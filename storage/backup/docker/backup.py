from os import environ, mkdir, listdir
from os.path import join, exists, expanduser
import json
import shutil
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

from kubernetes import client, config
from datetime import datetime, timedelta
from time import time
from subprocess import run, PIPE


def mkdir_p(dir_path):
    if not exists(dir_path):
        mkdir(dir_path)


def archive(backup_path, pv_dir_name, pvc_name):
    # format -> xztar: xz’ed tar-file (if the lzma module is available)
    # compress and save under the name of pvc
    filename = shutil.make_archive(
        join(backup_path, pvc_name), "xztar", join(environ["PV_FOLDER"], pv_dir_name)
    )
    return filename


def backup():
    start_time = time()

    # create backup directories
    year, month, day = str(datetime.now().date()).split("-")
    year_path = join(environ["BACKUP_FOLDER"], year)
    mkdir_p(year_path)
    month_path = join(year_path, month)
    mkdir_p(month_path)
    day_path = join(month_path, day)
    mkdir(day_path)

    # setup logging
    logger = logging.getLogger("backup")
    file_handler = logging.FileHandler(join(day_path, "backup.log"))
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    # file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)

    # dump all production databases
    # databases = ["gesishub", "gesisbinder", "gallery"]
    databases = ["gesisbinder", "gallery"]
    logger.info(f"## dumping databases: {', '.join(databases)}")
    mkdir(expanduser("~/.ssh"))
    command = "ssh-keyscan -H 194.95.75.9 > ~/.ssh/known_hosts"
    cp = run(command, shell=True, stdout=PIPE, stderr=PIPE)
    logger.info(f"#### command: {cp.args} -> {cp.returncode} - stdout: {cp.stdout}")
    if cp.stderr:
        logger.error(f"##### Backup error: for command {cp.args}: {cp.stderr}")
    for db in databases:
        dump_path = join(day_path, f"{db}.sql.gz")
        # take password from SSHPASS env variable
        command = (
            f"sshpass -e ssh iuser@194.95.75.9 "
            f'"pg_dump -Fp -h "localhost" -U "orc" -d "{db}"" '
            f"| gzip > {dump_path}"
        )
        cp = run(command, shell=True, stdout=PIPE, stderr=PIPE)
        logger.info(
            f"#### command for {db}: {cp.args} -> {cp.returncode} - stdout: {cp.stdout}"
        )
        if cp.stderr:
            logger.error(f"##### Backup error: for command {cp.args}: {cp.stderr}")
    done_db_time = time()
    logger.info(
        f"## Done: dumping databases: {timedelta(seconds=done_db_time-start_time)}\n\n"
    )

#     # Save config files of all production PVCs
#     logger.info("## Save config files of all production PVCs")
#     pvcs_backup_path = join(day_path, "pvcs")
#     mkdir_p(pvcs_backup_path)
#     pvc_template = """apiVersion: v1
# kind: PersistentVolumeClaim
# metadata:
#   annotations:
#     hub.jupyter.org/username: {username}
#   labels:
#     app: {app}
#     chart: {chart}
#     component: {component}
#     heritage: {heritage}
#     release: {release}
#   name: {name}
#   namespace: {namespace}
# spec:
#   accessModes:
#   - {access_mode}
#   resources:
#     requests:
#       storage: {storage}"""
#     # we have to map old pv names to new pv names through pvc names (pvc names stay same)
#     pv_dict = {}  # {pv_name: pvc_name}
#     pv_dict_rest = {}  # {pv_name: pvc_name}
#     config.load_incluster_config()
#     v1 = client.CoreV1Api()
#     pvcs = v1.list_persistent_volume_claim_for_all_namespaces(watch=False)
#     for pvc in pvcs.items:
#         # JupyterHub PVs
#         if pvc.metadata.namespace == "jhub-ns":
#             pv_dict[pvc.spec.volume_name] = pvc.metadata.name
#             d = {
#                 "username": pvc.metadata.annotations["hub.jupyter.org/username"],
#                 "app": pvc.metadata.labels["app"],
#                 "chart": pvc.metadata.labels["chart"],
#                 "component": pvc.metadata.labels["component"],
#                 "heritage": pvc.metadata.labels["heritage"],
#                 "release": pvc.metadata.labels["release"],
#                 "name": pvc.metadata.name,
#                 "namespace": pvc.metadata.namespace,
#                 "access_mode": pvc.spec.access_modes[0],
#                 "storage": pvc.spec.resources.requests["storage"],
#             }
#             with open(join(pvcs_backup_path, f"{pvc.metadata.name}.yaml"), "w") as f:
#                 f.write(pvc_template.format(**d))
#         # grafana PVs
#         # dont backup prometheus, it takes too long and causes mostly errors and
#         # actually we dont need it anymore for popular repos
#         elif pvc.metadata.namespace == "default" and ("grafana" in pvc.metadata.name):
#             # ('grafana' in pvc.metadata.name or 'prometheus' in pvc.metadata.name):
#             pv_dict_rest[pvc.spec.volume_name] = pvc.metadata.name
#         # efk-stack
#         # elif pvc.metadata.namespace == 'efk-stack-ns':
#         #     pv_dict_rest[pvc.spec.volume_name] = pvc.metadata.name
#     with open(f"{day_path}/pv_dict.json", "w") as fp:
#         json.dump(pv_dict, fp, indent=4)
#     with open(f"{day_path}/pv_dict_rest.json", "w") as fp:
#         json.dump(pv_dict_rest, fp, indent=4)
#     done_config_files = time()
#     logger.info(
#         f"## Done: Save config files of all production PVCs: "
#         f"{timedelta(seconds=done_config_files-done_db_time)}\n\n"
#     )

#     # backup PVs
#     logger.info("## Back up nfs shares separately: user folders and also grafana")
#     _pvs = listdir(environ["PV_FOLDER"])
#     pvs = []
#     # user PVs
#     pvs_backup_path = join(day_path, "pvs")
#     mkdir_p(pvs_backup_path)
#     for pv_dir_name in _pvs:
#         # filter out nfs files and PVs of staging
#         if pv_dir_name.startswith("pvc-") and pv_dir_name in pv_dict:
#             pvs.append([pvs_backup_path, pv_dir_name, pv_dict[pv_dir_name]])
#     # grafana PV
#     pvs_backup_path_rest = join(day_path, "pvs_rest")
#     mkdir_p(pvs_backup_path_rest)
#     for pv_dir_name in _pvs:
#         if pv_dir_name.startswith("pvc-") and pv_dir_name in pv_dict_rest:
#             pvs.append([pvs_backup_path_rest, pv_dir_name, pv_dict_rest[pv_dir_name]])
#     logger.info(f"### # pvs is {len(pvs)}")
#     max_workers = int(environ.get("MAX_WORKERS", 5))
#     try:
#         with ProcessPoolExecutor(max_workers=max_workers) as executor:
#             jobs = {}
#             pvs_left = len(pvs)
#             pvs_iter = iter(pvs)

#             success = 0
#             fail = 0
#             while pvs_left:
#                 for backup_path, pv_dir_name, pvc_name in pvs_iter:
#                     job = executor.submit(archive, backup_path, pv_dir_name, pvc_name)
#                     jobs[job] = pv_dir_name
#                     if len(jobs) == max_workers:  # limit # jobs with max_workers
#                         break

#                 for job in as_completed(jobs):
#                     pvs_left -= 1
#                     pv_dir_name = jobs[job]
#                     try:
#                         filename = job.result()
#                     except Exception:
#                         fail += 1
#                         logger.exception(pv_dir_name)
#                     else:
#                         success += 1
#                         logger.info(filename)

#                     del jobs[job]
#                     break  # to add a new job, if there is any
#     except Exception:
#         logger.exception("Backup error: nfs shares")
#     else:
#         logger.info(
#             f"## Done nfs shares ({success} PVs, failed {fail}): "
#             f"{timedelta(seconds=time()-done_config_files)}\n\n"
#         )

    # Rolling 21 day back up.
    delete_day = datetime.now().date() - timedelta(days=21)
    logger.info(f"## Rolling 21 day delete, deleting {delete_day.__str__()}")
    # Path follows YYYY/MM/DD format.
    delete_day_path = join(
        environ["BACKUP_FOLDER"],
        str(delete_day.year),
        "{:02d}".format(delete_day.month),
        "{:02d}".format(delete_day.day),
    )
    if exists(delete_day_path):
        shutil.rmtree(delete_day_path, ignore_errors=True)
        logger.info(f"### Deleted backup for {delete_day.__str__()}")

    logger.info(
        f"Backup was successful: duration: {timedelta(seconds=time()-start_time)}"
    )


if __name__ == "__main__":
    backup()
