import os
# c.NotebookApp.quit_button = False
# c.NotebookApp.extra_template_paths = ['/etc/jupyter/custom_notebook_templates']
c.NotebookApp.jinja_template_vars = {'is_staging': os.environ.get('IS_STAGING') == "true",
                                     'is_production': os.environ.get('IS_PRODUCTION') == "true"}
