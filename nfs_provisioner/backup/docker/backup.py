import os
import json
import shutil
import logging

from kubernetes import client, config
from datetime import datetime
from time import time
from subprocess import run, PIPE


def backup():
    start_time = time()

    # create backup directory
    year, month, day = str(datetime.now().date()).split('-')
    year_path = os.path.join(os.environ['BACKUP_FOLDER'], year)
    if not os.path.exists(year_path):
        os.mkdir(year_path)
    month_path = os.path.join(year_path, month)
    if not os.path.exists(month_path):
        os.mkdir(month_path)
    day_path = os.path.join(month_path, day)
    os.mkdir(day_path)

    # setup logging
    logger = logging.getLogger()  # root logger
    file_handler = logging.FileHandler(os.path.join(day_path, 'backup.log'))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    # file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    # dump all databases
    databases = ['jhub_db', 'bhub_db', 'jhub_test_db', 'bhub_test_db']
    logger.info('dumping databases: {}'.format(', '.join(databases)))
    os.mkdir(os.path.expanduser('~/.ssh'))
    command = 'ssh-keyscan -H 194.95.75.9 > ~/.ssh/known_hosts'
    cp = run(command, shell=True, stdout=PIPE, stderr=PIPE)
    logger.info('{} - {} - {} - {}'.format(cp.args, cp.returncode, cp.stdout, cp.stderr))
    for db in databases:
        dump_path = os.path.join(day_path, '{}.sql.gz'.format(db))
        # take password from SSHPASS env variable
        command = 'sshpass -e ssh iuser@194.95.75.9 "pg_dump -Fp -h "localhost" -U "jhub" -d "{}"" | gzip > {}'.\
                  format(db, dump_path)
        cp = run(command, shell=True, stdout=PIPE, stderr=PIPE)
        logger.info('{}:-> {} - {} - {} - {}'.format(db, cp.args, cp.returncode, cp.stdout, cp.stderr))
    logger.info('Done: dumping databases')

    # Save config files for all pvcs in jhub-ns
    logger.info('Save config files for all pvcs in jhub-ns')
    pvcs_backup_path = os.path.join(day_path, 'pvcs')
    if not os.path.exists(pvcs_backup_path):
        os.mkdir(pvcs_backup_path)
    pvc_template = """apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  annotations:
    hub.jupyter.org/username: {username}
  labels:
    app: {app}
    heritage: {heritage}
  name: {name}
  namespace: {namespace}
spec:
  accessModes:
  - {access_mode}
  resources:
    requests:
      storage: {storage}"""
    # we have to map old pv names to new pv names through pvc names (pvc names stay same)
    pv_dict = {}  # {pv_name: pvc_name}
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    pvcs = v1.list_persistent_volume_claim_for_all_namespaces(watch=False)
    for pvc in pvcs.items:
        # JupyterHub PVs
        if pvc.metadata.namespace == 'jhub-ns':
            pv_dict[pvc.spec.volume_name] = pvc.metadata.name
            d = {'username': pvc.metadata.annotations['hub.jupyter.org/username'],
                 'app': pvc.metadata.labels['app'],
                 'heritage': pvc.metadata.labels['heritage'],
                 'name': pvc.metadata.name,
                 'namespace': pvc.metadata.namespace,
                 'access_mode': pvc.spec.access_modes[0],
                 'storage': pvc.spec.resources.requests['storage']}
            with open('{}/{}.yaml'.format(pvcs_backup_path, pvc.metadata.name), 'w') as f:
                f.write(pvc_template.format(**d))
        # grafana and prometheus PVs
        elif pvc.metadata.namespace == 'default' and \
            ('grafana' in pvc.spec.volume_name or 'prometheus' in pvc.spec.volume_name):
            pv_dict[pvc.spec.volume_name] = pvc.metadata.name
    with open('{}/pvc_data.json'.format(day_path), 'w') as fp:
        json.dump(pv_dict, fp, indent=4)
    logger.info('Done: Save config files for all pvcs in jhub-ns')

    # back up each user folder separately and back up grafana and prometheus PVs
    logger.info('back up each user folder separately and back up grafana and prometheus PVs')
    pvs_backup_path = os.path.join(day_path, 'pvs')
    if not os.path.exists(pvs_backup_path):
        os.mkdir(pvs_backup_path)
    count = 0
    for pv_dir_name in os.listdir(os.environ['PV_FOLDER']):
        # filter out pvs of jhub-test-ns
        if pv_dir_name.startswith('pvc-') and pv_dir_name in pv_dict:
            # format -> xztar: xz’ed tar-file (if the lzma module is available)
            # compress and save under the name of pvc
            filename = shutil.make_archive(os.path.join(pvs_backup_path, pv_dict[pv_dir_name]),
                                           'xztar',
                                           os.path.join(os.environ['PV_FOLDER'], pv_dir_name))
            count += 1
            logger.info(filename)
    logger.info('Done: {} PVs'.format(count))

    # delete backup data older than 1 month 1 day
    logger.info('delete backup data older than 1 month 1 day')
    if day == '01':
        if month == '01' or month == '02':
            previous_year_path = os.path.join(os.environ['BACKUP_FOLDER'], str(int(year) - 1))
            previous_month_path = os.path.join(previous_year_path, '{}'.format(str(10+int(month))))
        else:
            previous_month_path = os.path.join(year_path, '{:02}'.format(int(month) - 2))
        if os.path.exists(previous_month_path):
            logger.info('deleting {}'.format(previous_month_path))
            shutil.rmtree(previous_month_path, ignore_errors=True)
    logger.info('Done: delete backup data older than 1 month 1 day')
    logger.info('Backup duration: {} seconds'.format(time()-start_time))


if __name__ == '__main__':
    backup()
