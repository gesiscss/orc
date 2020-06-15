"""
Most parts are taken from binderhub's image-cleaner
(https://github.com/jupyterhub/binderhub/tree/master/helm-chart/images/image-cleaner)
"""
from datetime import datetime, timedelta
from urllib.parse import unquote
from time import time, sleep

import shutil
import requests
import docker
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def get_available_disk_space(path_to_check):
    disk_usage = shutil.disk_usage(path_to_check)
    available = (disk_usage.free * 100) / disk_usage.total
    return available


def clean_images():
    days_limit = int(os.getenv('IMAGE_CLEANER_DAYS', '7'))
    interval = float(os.getenv('IMAGE_CLEANER_INTERVAL', '1800'))
    image_prefix = os.getenv('IMAGE_CLEANER_PREFIX', 'gesiscss/binder-')
    path_to_check = os.getenv('IMAGE_CLEANER_PATH', '/var/lib/docker')
    delay = float(os.getenv('IMAGE_CLEANER_DELAY', '5'))
    high_limit = float(os.getenv('IMAGE_CLEANER_HIGH', '80'))
    low_limit = float(os.getenv('IMAGE_CLEANER_LOW', '40'))

    # TODO delete an image if built with older version
    # response = requests.get("https://notebooks.gesis.org/binder/versions", timeout=1)
    # r2d_version = response.json()["builder"]

    logging.info(f"Cleaning images on {path_to_check}")
    while True:
        available = get_available_disk_space(path_to_check)
        if available > (100 - high_limit):
            logging.info(f"There is enough free disk space ({available}%).")
        else:
            start_time = time()
            # start cleaning when high_limit% of disk is used
            for days in range(days_limit, -1, -1):
                logging.info(f"Starting to remove images which are not used in last {days} days. current available disk space: {available}%")

                # get launches on GESIS Binder in last x days
                from_dt = (datetime.now() - timedelta(days=days)).isoformat()
                url = f'https://notebooks.gesis.org/gallery/api/v1.0/launches/{from_dt}/'
                launches = []
                # get launches only on GESIS
                origins = ["notebooks.gesis.org", "gesis.mybinder.org"]
                for origin in origins:
                    # because of pagination the api gives 500 results per page
                    # so for analysis you have to take data in all pages
                    next_page = 1
                    api_request_retry = 1
                    while next_page is not None:
                        payload = {'page': str(next_page), 'origin': origin}
                        r = requests.get(url, params=payload)
                        response = r.json()
                        if r.status_code == 429:
                            # check the limit of queries per second/minute
                            logging.info(f'Gallery API: status code 429: {response["messsage"]}')
                            sleep(1)
                        elif r.status_code == 200:
                            launches.extend(response['launches'])
                            next_page = response['next_page']
                            api_request_retry = 1
                        elif api_request_retry <= 3:
                            message = response.get("message", "")
                            logging.warning(f"Gallery API: not responding (page {next_page}, attempt {api_request_retry}): {r.status_code}: {message}")
                            sleep(api_request_retry)
                            api_request_retry += 1
                        else:
                            message = response.get("message", "")
                            logging.error(f"Gallery API: failed to get launches (page {next_page}): {r.status_code}: {message}")
                            break

                _launches = []
                for l in launches:
                    if l["provider"] in ['GitHub', 'Gist']:
                        namespace = l["spec"].rsplit("/", 1)[0]
                    elif l["provider"] in ["Git", "GitLab"]:
                        # for Git, quoted_namespace is actually the repo url
                        quoted_namespace = l["spec"].rsplit("/", 1)[0]
                        namespace = unquote(quoted_namespace)
                    else:
                        # FIXME
                        namespace = l["spec"]
                    if namespace.endswith(".git"):
                        namespace = namespace[:-(len(".git"))]
                    _launches.append((namespace, l["provider"].lower()))
                launches = _launches
                # logging.info(f"Number of launches on GESIS in last {days} days: {len(launches)}")

                deleted = 0
                client = docker.from_env()
                images = client.images.list()
                # sort images according to size in descending order
                images.sort(key=lambda i: i.attrs['Size'], reverse=True)
                for image in images:
                    if image.tags:
                        # ex tag: 'gesiscss/binder-serhatcevikel-2dbdm-5f2019-e7b363:a5c8f288aecebb097d8d525138c2b7b031fd0f3d'
                        tag = image.tags[0]
                        if not tag.startswith(image_prefix):
                            # delete images only which are built by binder
                            # NOTE: GESIS Hub and Binder have same image prefix
                            continue
                    else:
                        # ignore untagged images for now, prune will delete them if they are not used
                        continue

                    logging.info(f"Image {tag} with labels: {image.labels}")
                    # image.labels["repo2docker.repo"] gives us repo url
                    # image.labels["repo2docker.version"] gives us repo2docker version
                    # image.labels["repo2docker.ref"] gives us resolved ref (image tag)
                    recently_used = bool([True for namespace, provider in launches
                                          if namespace and
                                          namespace in image.labels["repo2docker.repo"] and
                                          provider in image.labels["repo2docker.repo"]])
                    # delete dockerfile repos always, because they dont have r2d labels (unless maintainer adds them)
                    if "repo2docker.repo" not in image.labels or not recently_used:
                        try:
                            # if days == 0:
                            #     # force delete
                            #     client.images.remove(tag, force=True)
                            # dont force, dont delete an image which is currently used in a container
                            client.images.remove(tag)
                            # client.images.remove(image=image.id, force=True)
                            logging.info(f'Removed {tag}')
                            # Delay between deletions.
                            # A sleep here avoids monopolizing the Docker API with deletions.
                            sleep(delay)
                        except docker.errors.APIError as e:
                            if e.status_code == 409:
                                # This means the image can not be removed right now
                                logging.info(f'Failed to remove {tag}, skipping this image')
                                logging.info(str(e))
                            elif e.status_code == 404:
                                logging.info(f'{tag} not found, probably already deleted')
                            else:
                                raise
                        except requests.exceptions.ReadTimeout:
                            logging.warning(f'Timeout removing {tag}')
                            # Delay longer after a timeout, which indicates that Docker is overworked
                            sleep(max(delay, 30))
                        else:
                            deleted += 1
                            available = get_available_disk_space(path_to_check)
                            if available >= (100 - low_limit):
                                # cleaning is done when there is enough free disk space
                                logging.info(f"{days} days: while removing images, "
                                             f"reached to enough free disk space ({available}%). "
                                             f"Stop cleaning.")
                                break
                    else:
                        logging.info(f"Skipping {tag}: used in last {days} days")

                # prune dangling (unused and untagged) images after deleting for each day
                client.images.prune(filters={"dangling": True})
                logging.info(f"{days} days: removed {deleted} images: available disk space: {available}%")
                # check available disk space before checking next day
                available = get_available_disk_space(path_to_check)
                if available >= (100 - low_limit):
                    # cleaning is done when there is enough free disk space
                    logging.info(f"{days} days: after removing images, "
                                 f"there is enough free disk space ({available}%). "
                                 f"Stop cleaning.")
                    break
            logging.info(f"Duration: {timedelta(seconds=time()-start_time)}")
        sleep(interval)


if __name__ == '__main__':
    clean_images()
