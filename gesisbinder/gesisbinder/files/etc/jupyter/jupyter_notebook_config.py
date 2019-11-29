import notebook
import os

from distutils.version import LooseVersion as V


c.NotebookApp.extra_template_paths.append('/etc/jupyter/templates')


# For old notebook versions we have to explicitly enable the translation
# extension
if V(notebook.__version__) < V('5.1.0'):
    c.NotebookApp.jinja_environment_options = {'extensions': ['jinja2.ext.i18n']}


def make_federation_url(url):
    federation_host = 'https://mybinder.org'
    if not url:
        return ''
    url_parts = url.split('/v2/', 1)
    return federation_host + '/v2/' + url_parts[-1]


binder_launch_host = os.environ.get('BINDER_LAUNCH_HOST', '')
binder_request = os.environ.get('BINDER_REQUEST', '')
binder_persistent_request = os.environ.get('BINDER_PERSISTENT_REQUEST', '')

c.NotebookApp.jinja_template_vars.update({
    'binder_url': make_federation_url(binder_launch_host+binder_request),
    'persistent_binder_url': make_federation_url(binder_launch_host+binder_persistent_request),
    'repo_url': os.environ.get('BINDER_REPO_URL', ''),
    'ref_url': os.environ.get('BINDER_REF_URL', ''),
})
