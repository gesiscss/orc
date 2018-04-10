import os
import json
import subprocess
import shutil
import logging

from kubernetes import client, config
from datetime import datetime
from time import time


def main():
    start = time()

    # create backup directory
    year, month, day = str(datetime.now().date()).split('-')
    year_path = os.path.join(os.environ['BACKUP_FOLDER'], year)
    if not os.path.exists(year_path):
        os.mkdir(year_path)
    month_path = os.path.join(year_path, month)
    if not os.path.exists(month_path):
        os.mkdir(month_path)
    day_path = os.path.join(month_path, day)
    if not os.path.exists(day_path):
        os.mkdir(day_path)

    logger = logging.getLogger()
    file_handler = logging.FileHandler(os.path.join(day_path, 'backup.log'))
    # file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    # dump all databases
    logger.info('dump all databases')
    databases = ['jhub_db', 'jhub_test_db', 'bhub_db', 'bhub_test_db']
    os.mkdir(os.path.expanduser('~/.ssh'))
    command = 'ssh-keyscan -H 194.95.75.9 > ~/.ssh/known_hosts'
    cp = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    logger.info('{} - {} - {} - {}'.format(cp.returncode, cp.stdout, cp.stderr, cp.args))
    for db in databases:
        dump_path = os.path.join(day_path, '{}.sql.gz'.format(db))
        # take password from SSHPASS env variable
        command = 'sshpass -e ssh iuser@194.95.75.9 "pg_dump -Fp -h "localhost" -U "jhub" -d "{}"" | gzip > {}'.\
                  format(db, dump_path)
        cp = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
        logger.info('{} - {} - {} - {} - {}'.format(db, cp.returncode, cp.stdout, cp.stderr, cp.args))
    logger.info('Done: dump all databases')

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
    pvc_map = {}  # {pvc_name: pv_name}
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    pvcs = v1.list_persistent_volume_claim_for_all_namespaces(watch=False)
    for pvc in pvcs.items:
        if pvc.metadata.namespace == 'jhub-ns':
            pvc_map[pvc.metadata.name] = pvc.spec.volume_name
            d = {'username': pvc.metadata.annotations['hub.jupyter.org/username'],
                 'app': pvc.metadata.labels['app'],
                 'heritage': pvc.metadata.labels['heritage'],
                 'name': pvc.metadata.name,
                 'namespace': pvc.metadata.namespace,
                 'access_mode': pvc.spec.access_modes[0],
                 'storage': pvc.spec.resources.requests['storage']}
            with open('{}/{}.yaml'.format(pvcs_backup_path, pvc.metadata.name), 'w') as f:
                f.write(pvc_template.format(**d))
    with open('{}/pvc_data.json'.format(day_path), 'w') as fp:
        json.dump(pvc_map, fp)
    logger.info('Done: Save config files for all pvcs in jhub-ns')

    # back up each user folder separately
    logger.info('back up each user folder separately')
    pvs_backup_path = os.path.join(day_path, 'pvs')
    if not os.path.exists(pvs_backup_path):
        os.mkdir(pvs_backup_path)
    pv_names = set(pvc_map.values())
    for pv_dir in os.listdir(os.environ['PV_FOLDER']):
        # filter out pvs of jhub-test-ns
        if pv_dir.startswith('pvc-') and pv_dir in pv_names:
            # format -> xztar: xz’ed tar-file (if the lzma module is available)
            filename = shutil.make_archive(os.path.join(pvs_backup_path, pv_dir),
                                           'xztar',
                                           os.path.join(os.environ['PV_FOLDER'], pv_dir))
            logger.info(filename)
    logger.info('Done: back up each user folder separately')

    # delete backup data older than 1 month 1 day
    logger.info('delete backup data older than 1 month 1 day')
    if day == '01':
        if month == '01' or month == '02':
            previous_year_path = os.path.join(os.environ['BACKUP_FOLDER'], str(int(year) - 1))
            previous_month_path = os.path.join(previous_year_path, '{}'.format(str(10+int(month))))
        else:
            previous_month_path = os.path.join(year_path, '{:02}'.format(int(month) - 1))
        if os.path.exists(previous_month_path):
            logger.info('deleting {}'.format(previous_month_path))
            os.rmdir(previous_month_path)
    logger.info('Done: delete backup data older than 1 month 1 day')
    logger.info('backup time: {} seconds'.format(time()-start))


if __name__ == '__main__':
    main()
