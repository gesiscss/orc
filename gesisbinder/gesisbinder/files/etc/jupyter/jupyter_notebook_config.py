import os
c.NotebookApp.extra_template_paths.append('/etc/jupyter/templates')

federation_host = 'https://mybinder.org'
current_host = 'https://notebooks.gesis.org/binder'
c.NotebookApp.jinja_template_vars.update({
    'binder_url': os.environ.get('BINDER_URL', federation_host).replace(current_host, federation_host),
    'persistent_binder_url': os.environ.get('PERSISTENT_BINDER_URL', '').replace(current_host, federation_host),
    'repo_url': os.environ.get('REPO_URL', ''),
    'ref_url': os.environ.get('REF_URL', ''),
})
