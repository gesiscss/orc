from fabric import task


@task
def nginx(c, user, password, branch_name, ref='master', mode=''):
    c.user = user
    c.connect_kwargs.password = password

    nginx_folder = '~/ilcm/orc_nginx/load_balancer/'  # on base:worker
    c.run('echo "######## Updating code base"')
    with c.cd(nginx_folder):
        c.run('git fetch --all')
        c.run('git checkout {}'.format(ref))

    mode = mode.split('-')
    if "static" in mode:
        c.run('echo "######## Replacing static files"')
        branch_name = "prod" if branch_name == "master" else "staging"
        c.sudo("rm -rf /var/www/{}/static".format(branch_name), password=password)
        c.sudo("cp -R {}static /var/www/{}/".format(nginx_folder, branch_name), password=password)
    if "config" in mode:
        c.run('echo "######## Copying config files"')
        c.sudo("cp -R {}snippets/* /etc/nginx/snippets/".format(nginx_folder), password=password)
        c.sudo("cp {}sites-available/default /etc/nginx/sites-available/".format(nginx_folder), password=password)
        c.sudo("cp {}sites-available/gesis_mybinder /etc/nginx/sites-available/".format(nginx_folder), password=password)
        c.sudo("cp {}sites-available/orc /etc/nginx/sites-available/".format(nginx_folder), password=password)
        # add ORC_test/pbhub for notebooks-test.gesis.org
        c.run('echo "######## Testing config files"')
        c.sudo("nginx -t", password=password)
        c.run('echo "######## Reloading nginx"')
        c.sudo("systemctl reload nginx.service", password=password)
        c.sudo("systemctl status nginx.service", password=password)


@task
def deploy(c, user, password, staging=False, ref='master', mode=''):
    """fab -H <master_node_ip> deploy -p <master_node_password> -r <commit_number> -m <deploy_mode> -s
    http://docs.fabfile.org/en/2.4/
    :param c: fabric.Connection
    :param password: k8s master node password.
    :param staging: Deploy on staging or on production
    :param ref: Branch name or commit number to checkout and deploy.
    :param mode: Deploy mode.
    :return:
    """
    c.user = user
    c.connect_kwargs.password = password

    format_dict = {
        'env': 'staging' if staging else 'production',
        '_test': '_test' if staging else '',
        '-test': '-test' if staging else ''
    }
    remote_project_root = '~/ilcm/orc'  # on master
    with c.cd(remote_project_root):
        mode = mode.split('-')
        if 'fetch_co' in mode:
            c.run('git fetch --all')
            c.run('git checkout {}'.format(ref))
        if 'galleryapp' in mode or 'gallerytestapp' in mode or \
           'galleryconf' in mode or 'gallerytestconf' in mode:
            if 'galleryconf' in mode or 'gallerytestconf' in mode:
                c.run('kubectl create secret generic gallery-config '
                      '--from-file=gallery/_secret_config{_test}.py '
                      '--namespace=gallery{-test}-ns '
                      '-o yaml --dry-run | kubectl replace -f -'.format(**format_dict))
                c.run('kubectl delete deployment gallery{-test} '
                      '--namespace=gallery{-test}-ns'.format(**format_dict))
            c.run('kubectl apply -f gallery/config{_test}.yaml '
                  '--namespace=gallery{-test}-ns'.format(**format_dict))
        if 'galleryarchives' in mode and not staging:
            c.run('kubectl apply -f gallery/cron_job.yaml -n gallery-ns')
        if 'bhubns' in mode or 'bhubtestns' in mode:
            c.run('helm repo update')
            c.run('helm dependency update gesisbinder/gesisbinder')
            # if any static file or template file is changed, binder pod must be restarted in order to reflect changes
            # nginx servers static files for custom binder templates and when they are changed pod must be restarted to get a new static_version
            sha256sum_nginx = c.run('find load_balancer/static/images/ load_balancer/static/styles/ load_balancer/static/scripts/ -type f -exec sha256sum {} \; | sha256sum')
            sha256sum_bh = c.run('find gesishub/gesishub/files/etc/binderhub/templates/ -type f -exec sha256sum {} \; | sha256sum')
            sha256sum_bh = c.run('echo "{}" | sha256sum'.format(sha256sum_bh.stdout + sha256sum_nginx.stdout))
            command = 'helm upgrade bhub{-test} gesisbinder/gesisbinder ' \
                      '--namespace=bhub{-test}-ns ' \
                      '--cleanup-on-fail --debug ' \
                      '-f gesisbinder/config{_test}.yaml ' \
                      '-f gesisbinder/_secret{_test}.yaml'.format(**format_dict) + \
                      ' --set binderhub.podAnnotations.rollme=' + sha256sum_bh.stdout.split()[0]
            c.run('echo "######## {}"'.format(command))
            c.run(command)
        if 'bhubupgrade' in mode and not staging:
            c.run('kubectl apply -f gesisbinder/bot/_secret_cron_job.yaml -n bhub-ns')
            c.run('kubectl apply -f gesisbinder/bot/cron_job.yaml -n bhub-ns')
        if 'jhubns' in mode or 'jhubtestns' in mode:
            c.run('helm repo update')
            c.run('helm dependency update gesishub/gesishub')
            # if any configmap file or static file or template file is changed, hub pod must be restarted in order to reflect changes
            # nginx servers static files for custom binder templates and when they are changed pod must be restarted to get a new static_version
            sha256sum_nginx = c.run('find load_balancer/static/images/ load_balancer/static/styles/ load_balancer/static/scripts/ -type f -exec sha256sum {} \; | sha256sum')
            sha256sum_jh = c.run('find gesishub/gesishub/files/etc/jupyterhub/ -type f -exec sha256sum {} \; | sha256sum')
            sha256sum_jh = c.run('echo "{}" | sha256sum'.format(sha256sum_jh.stdout + sha256sum_nginx.stdout))
            # compared to gesis binder, here bhub also uses binder-extra-config-json configmap, not only templates
            # so restart the binder pod depending on the same condition as for hub pod
            sha256sum_jbh = c.run('find gesishub/gesishub/files/ -type f -exec sha256sum {} \; | sha256sum')
            sha256sum_jbh = c.run('echo "{}" | sha256sum'.format(sha256sum_jbh.stdout + sha256sum_nginx.stdout))
            command = 'helm upgrade jhub{-test} gesishub/gesishub ' \
                      '--namespace=jhub{-test}-ns ' \
                      '--cleanup-on-fail --debug ' \
                      '-f gesishub/config{_test}.yaml ' \
                      '-f gesishub/_secret{_test}.yaml'.format(**format_dict) + \
                      ' --set persistent_binderhub.binderhub.jupyterhub.hub.annotations.rollme=' + sha256sum_jh.stdout.split()[0] + \
                      ' --set persistent_binderhub.binderhub.podAnnotations.rollme=' + sha256sum_jbh.stdout.split()[0]
            c.run('echo "######## {}"'.format(command))
            c.run(command)
        if 'backupjob' in mode and not staging:
            c.run('kubectl apply -f storage/backup/_secret.yaml')
            c.run('kubectl apply -f storage/backup/rbac.yaml')
            c.run('kubectl apply -f storage/backup/cron_job.yaml')
        if 'prometheus' in mode and not staging:
            with open('monitoring/prometheus_config.yaml') as f:
                first_line = f.readline()
                chart_version = first_line.strip().split(" ")[-1]
            c.run('echo "######## prometheus chart version {}"'.format(chart_version))
            c.run('helm upgrade prometheus prometheus-community/prometheus --version='+chart_version+' '
                  '-f monitoring/prometheus_config.yaml '
                  '--cleanup-on-fail --debug')
        if 'grafana' in mode and not staging:
            with open('monitoring/grafana_config.yaml') as f:
                first_line = f.readline()
                chart_version = first_line.strip().split(" ")[-1]
            c.run('echo "######## grafana chart version {}"'.format(chart_version))
            c.run('helm upgrade grafana grafana/grafana --version='+chart_version+' '
                  '-f monitoring/grafana_config.yaml '
                  '-f monitoring/_secret_grafana.yaml '
                  '--cleanup-on-fail --debug')


@task
def test(c, user, password, staging=False, ref='master', mode=''):
    """
    fab -H '194.95.75.10' test -s
    http://docs.fabfile.org/en/2.4/
    """
    c.user = user
    c.connect_kwargs.password = password
    remote_project_root = '~/ilcm/orc'
    with c.cd(remote_project_root):
        c.run('pwd')
        c.run('ls -alh')
