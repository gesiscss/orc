# https://github.com/gesiscss/jhub_shibboleth_auth/tree/89e1a4b5ec49eafd55c583ef06d8012f88393dc6/docker/k8s_hub
FROM gesiscss/k8s-hub:v0.6-69797588

USER root
RUN mv /home/jovyan/.local/share/jupyter/hub/templates/page.html /home/jovyan/.local/share/jupyter/hub/templates/page_base.html
ADD templates/page.html /home/jovyan/.local/share/jupyter/hub/templates/page.html
#RUN mv /usr/local/share/jupyter/hub/templates/admin.html /usr/local/share/jupyter/hub/templates/admin_base.html
#ADD templates/admin.html /usr/local/share/jupyter/hub/templates/admin.html
# /home/jovyan/.local/share/jupyter/hub/templates
RUN mv /home/jovyan/.local/share/jupyter/hub/templates/admin.html /home/jovyan/.local/share/jupyter/hub/templates/admin_base.html
ADD templates/admin.html /home/jovyan/.local/share/jupyter/hub/templates/admin.html
RUN mv /home/jovyan/.local/share/jupyter/hub/templates/error.html /home/jovyan/.local/share/jupyter/hub/templates/error_base.html
ADD templates/error.html /home/jovyan/.local/share/jupyter/hub/templates/error.html
USER ${NB_USER}
