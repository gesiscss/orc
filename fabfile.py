from fabric import task


@task
def deploy(c, password, staging=False, ref='master', mode=''):
    """fab -H <master_node_ip> deploy -p <master_node_password> -r <commit_number> -m <deploy_mode> -s
    http://docs.fabfile.org/en/2.4/
    :param c: fabric.Connection
    :param password: k8s master node password.
    :param staging: Deploy on staging or on production
    :param ref: Branch name or commit number to checkout and deploy.
    :param mode: Deploy mode. To update all apps, use fetch_co-jhub-bhub-nginx.
    :return:
    """
    c.user = 'iuser'
    c.connect_kwargs.password = password

    format_dict = {
        'env': 'staging' if staging else 'production',
        '_test': '_test' if staging else '',
        '-test': '-test' if staging else ''
    }
    remote_project_root = '~/ilcm/orc_staging' if staging else '~/ilcm/orc'
    with c.cd(remote_project_root):
        mode = mode.split('-')
        if 'fetch_co' in mode:
            c.run('git fetch --all')
            c.run('git checkout {}'.format(ref))
        if 'nginxshibbolethapp' in mode or 'nginxshibbolethtestapp' in mode or \
           'nginxshibbolethconf' in mode or 'nginxshibbolethtestconf' in mode:
            if 'nginxshibbolethconf' in mode or 'nginxshibbolethtestconf' in mode:
                c.run('kubectl create secret tls shibboleth-sp-tls-secret '
                      '--key=nginx_shibboleth/shibboleth/conf/{env}/_secret_sp_key.pem '
                      '--cert=nginx_shibboleth/shibboleth/conf/{env}/_secret_sp_cert.pem '
                      '--namespace=orc{-test}-ns '
                      '-o yaml --dry-run | kubectl replace -f -'.format(**format_dict))
                c.run('kubectl create configmap shibboleth-configmap '
                      '--from-file=nginx_shibboleth/shibboleth/conf/{env}/shibboleth2.xml '
                      '--from-file=nginx_shibboleth/shibboleth/conf/attribute-map.xml '
                      '--from-file=nginx_shibboleth/shibboleth/conf/{env}/attrChecker.html '
                      '--from-file=nginx_shibboleth/shibboleth/conf/{env}/metadata.xml '
                      '--namespace=orc{-test}-ns '
                      '-o yaml --dry-run | kubectl replace -f -'.format(**format_dict))
                c.run('kubectl create configmap nginx-configmap '
                      '--from-file=nginx_shibboleth/nginx/k8s{_test}.conf '
                      '--namespace=orc{-test}-ns '
                      '-o yaml --dry-run | kubectl replace -f -'.format(**format_dict))
                c.run('kubectl delete deployment nginx-shibboleth{-test}-deployment '
                      '--namespace=orc{-test}-ns'.format(**format_dict))
                # TODO wait until all pods are removed
            c.run('kubectl apply -f nginx_shibboleth/nginx-shibboleth-app{-test}.yaml '
                  '--namespace=orc{-test}-ns'.format(**format_dict))
        if 'orcsite' in mode or 'orctestsite' in mode:
            c.run('kubectl apply -f orc_site/deploy/orc-site-app{-test}.yaml '
                  '--namespace=orc{-test}-ns'.format(**format_dict))
        if 'jhubns' in mode or 'jhubtestns' in mode:
            c.run('helm repo update')
            c.run('helm upgrade jhub{-test} jupyterhub/jupyterhub --version=0.8-151be76 '
                  '--install --namespace=jhub{-test}-ns '
                  '-f jupyterhub/config{_test}.yaml '
                  '-f jupyterhub/_secret{_test}.yaml '
                  '--wait --force --debug --timeout=1800'.format(**format_dict))
        if 'bhubns' in mode or 'bhubtestns' in mode:
            c.run('helm repo update')
            c.run('helm upgrade bhub{-test} jupyterhub/binderhub --version=0.2.0-2b368e4 '
                  '--install --namespace=bhub{-test}-ns '
                  '-f binderhub/_secret{_test}.yaml '
                  '-f binderhub/config{_test}.yaml '
                  '--wait --force --debug --timeout=1800'.format(**format_dict))


@task
def test(c, password, staging=False, ref='master', mode=''):
    """
    fab -H '194.95.75.8' test -s
    http://docs.fabfile.org/en/2.4/
    """
    c.user = 'iuser'
    c.connect_kwargs.password = password
    remote_project_root = '~/ilcm/orc_staging' if staging else '~/ilcm/orc'
    with c.cd(remote_project_root):
        c.run('pwd')
        c.run('ls -alh')
