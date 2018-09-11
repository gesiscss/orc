from fabric.api import cd, env, run, task


PROJECT_NAME = 'orc'


# @task
# def staging():
#     env.hosts = ['iuser@notebooks-test.gesis.org']
#     env.environment = 'staging'
#
#
# @task
# def production():
#     env.hosts = ['iuser@notebooks.gesis.org']
#     env.environment = 'production'


@task
def k8s_master():
    env.hosts = ['iuser@194.95.75.8']
    env.environment = 'k8s_master'


# def pip(cmd):
#     return run('~/anaconda3/envs/orc3/bin/pip {}'.format(cmd))


@task
def deploy(branch='master', mode='', is_staging=False):
    """
    http://docs.fabfile.org/en/1.14/tutorial.html#conclusion
    fab production deploy
    fab production deploy:branch=dev,mode=fetch_co-bhubns
    fab production deploy:branch=commit_nr,mode=fetch_co-bhubtestns,is_staging=True

    :param branch: Branch name or commit number to checkout and deploy.
    :param mode: To update everything, use fetch_co-jhub-bhub-nginx.
    :param is_staging: If (only) updating k8s test namespaces for staging in master node.
    """
    format_dict = {
        'env': 'staging' if is_staging else 'production',
        '_test': '_test' if is_staging else '',
        '-test': '-test' if is_staging else ''
    }
    remote_project_root = '~/ilcm/orc_staging' if is_staging else '~/ilcm/orc'
    with cd(remote_project_root):
        mode = mode.split('-')
        if 'fetch_co' in mode:
            run('git fetch --all')
            run('git checkout {}'.format(branch))
        if 'nginxshibbolethapp' in mode or 'nginxshibbolethtestapp' in mode or \
           'nginxshibbolethconf' in mode or 'nginxshibbolethtestconf' in mode:
            print('####### kubectl update nginxshibboleth{-test} app'.format(**format_dict))
            if 'nginxshibbolethconf' in mode or 'nginxshibbolethtestconf' in mode:
                print('####### kubectl update nginxshibboleth{-test} conf'.format(**format_dict))
                run('kubectl create configmap shibboleth-configmap '
                    '--from-file=nginx_shibboleth/shibboleth/conf/{env}/shibboleth2.xml '
                    '--from-file=nginx_shibboleth/shibboleth/conf/attribute-map.xml '
                    '--from-file=nginx_shibboleth/shibboleth/conf/{env}/attrChecker.html '
                    '--from-file=nginx_shibboleth/shibboleth/conf/{env}/metadata.xml '
                    '--namespace=orc{-test}-ns '
                    '-o yaml --dry-run | kubectl replace -f -'.format(**format_dict))
                run('kubectl create configmap nginx-configmap '
                    '--from-file=nginx_shibboleth/nginx/k8s{_test}.conf '
                    '--namespace=orc{-test}-ns '
                    '-o yaml --dry-run | kubectl replace -f -'.format(**format_dict))
                run('kubectl delete deployment nginx-shibboleth{-test}-deployment '
                    '--namespace=orc{-test}-ns'.format(**format_dict))
            run('kubectl apply -f nginx_shibboleth/nginx-shibboleth-app{-test}.yaml '
                '--namespace=orc{-test}-ns'.format(**format_dict))
            print('####### kubectl update nginxshibboleth{-test} app - done'.format(**format_dict))
        if 'orcsite' in mode or 'orctestsite' in mode:
            print('####### kubectl upgrade orc{-test} site'.format(**format_dict))
            run('kubectl apply -f orc_site/deploy/orc-site-app{-test}.yaml '
                '--namespace=orc{-test}-ns'.format(**format_dict))
            print('####### kubectl upgrade orc{-test} site - done'.format(**format_dict))
        # take secret files from ~/ilcm/orc, because they are manually updated
        if 'jhubns' in mode or 'jhubtestns' in mode:
            print('####### helm upgrade jhub{-test} ns'.format(**format_dict))
            run('helm repo update')
            run('helm upgrade jhub{-test} jupyterhub/jupyterhub --version=0.7.0 --wait --force --install --namespace=jhub{-test}-ns '
                '-f jupyterhub/config{_test}.yaml '
                '-f ~/ilcm/orc/jupyterhub/secret{_test}.yaml --debug --timeout=360000'.
                format(**format_dict))
            print('####### helm upgrade jhub{-test} ns - done'.format(**format_dict))
        if 'bhubns' in mode or 'bhubtestns' in mode:
            print('####### helm upgrade bhub{-test} ns'.format(**format_dict))
            run('helm repo update')
            # run('helm upgrade bhub{-test} ~/ilcm/binderhub-0.1.0-e113dbb/binderhub --wait '
            run('helm upgrade bhub{-test} jupyterhub/binderhub --version=0.1.0-6e8f9dc --wait --force --install --namespace=bhub{-test}-ns '
                '-f ~/ilcm/orc/binderhub/secret{_test}.yaml '
                '-f binderhub/config{_test}.yaml --debug --timeout=360000'.
                format(**format_dict))
            print('####### helm upgrade bhub{-test} ns - done'.format(**format_dict))
