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
    image_prefix = os.getenv('IMAGE_CLEANER_PREFIX', 'gesiscss/orc-binder-')
    path_to_check = os.getenv('IMAGE_CLEANER_PATH', '/var/lib/docker')
    delay = float(os.getenv('IMAGE_CLEANER_DELAY', '5'))
    high_limit = float(os.getenv('IMAGE_CLEANER_HIGH', '80'))
    low_limit = float(os.getenv('IMAGE_CLEANER_LOW', '40'))

    # TODO delete an image if built with older version
    # response = requests.get("https://notebooks.gesis.org/binder/versions", timeout=1)
    # r2d_version = response.json()["builder"]

    client = docker.from_env()
    while True:
        start_time = time()

        prune_output = client.images.prune(filters={"dangling": True})
        logging.info(f"After prune: {prune_output}")

        available = get_available_disk_space(path_to_check)
        if available < high_limit:
            # cleaning is done when there is enough free disk space
            logging.info(f"There is enough free disk space ({available}%).")
            pass
        else:
            for days in range(days_limit, -1, -1):
                logging.info(f"Start deleting images not used in last {days} days. Free disk space: {available}%")

                # get launches on GESIS Binder in last x days
                from_dt = (datetime.now() - timedelta(days=days)).isoformat()
                url = f'https://notebooks.gesis.org/gallery/api/v1.0/launches/{from_dt}/'
                launches = []
                # because of pagination the api gives 100 results per page so for analysis you have to take data in all pages
                next_page = 1
                while next_page is not None:
                    api_url = url + str('?page=') + str(next_page)
                    r = requests.get(api_url)
                    response = r.json()
                    # check the limit of queries per second/minute,
                    message = response.get("message", "")
                    if message not in ["2 per 1 second", "100 per 1 minute"]:
                        launches.extend(response['launches'])
                        next_page = response['next_page']
                    else:
                        sleep(1)
                _launches = []
                for l in launches:
                    # get launches on GESIS only
                    if l["origin"] not in ["notebooks.gesis.org", "gesis.mybinder.org"]:
                        continue
                    if l["provider"] in ["Git", "GitLab"]:
                        spec = l["spec"].rsplit("/", 1)[0]
                        spec = unquote(spec)
                    elif l["provider"] in ["Zenodo", "Figshare"]:
                        spec = l["spec"]
                    else:
                        spec = l["spec"].rsplit("/", 1)[0]
                    if spec.endswith(".git"):
                        spec = spec.split(".git")[0]
                    _launches.append((spec, l["provider"].lower()))
                launches = _launches
                logging.info(f"Number of launches on GESIS: {len(launches)}")

                deleted = 0
                for image in client.images.list():
                    if not image.tags:
                        # TODO why does this exist?
                        continue
                    tag = image.tags[0]
                    if not tag.startswith(image_prefix):
                        continue

                    # image.labels["repo2docker.repo"] gives us repo url
                    # image.labels["repo2docker.version"] gives us repo2docker version
                    # image.labels["repo2docker.ref"] gives us resolved ref (image tag)
                    # delete dockerfile repos always, because they dont have r2d labels (unless maintainer adds them)
                    if "repo2docker.repo" not in image.labels or \
                        not bool([True for spec, provider in launches
                                  if spec in image.labels["repo2docker.repo"] and provider in image.labels["repo2docker.repo"]]):
                        logging.info(f"Deleting {tag} with labels: {image.labels}")
                        try:
                            client.images.remove(tag)
                            # client.images.remove(image=image.id, force=True)
                            # logging.info(f'Removed {name}')
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
                            if available > low_limit:
                                # cleaning is done when there is enough free disk space
                                logging.info(f"While deleting images not used in last {days} days, "
                                             f"reached to enough free disk space ({available}%). Stop deleting.")
                                break
                    else:
                        logging.info(f"Skipping {tag} with labels: {image.labels}")

                logging.info(f"Deleted {deleted} images. Free disk space after deleting {days} days: {available}%")
                # check available disk space before checking next day
                available = get_available_disk_space(path_to_check)
                if available > low_limit:
                    # cleaning is done when there is enough free disk space
                    logging.info(f"After deleting images not used in last {days} days, "
                                 f"there is enough free disk space ({available}%). Stop deleting.")
                    break
        logging.info(f"Duration: {timedelta(seconds=time()-start_time)}")
        sleep(interval)


if __name__ == '__main__':
    clean_images()
