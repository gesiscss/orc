# https://github.com/gesiscss/jhub_shibboleth_auth/tree/2bb2e73ad41bad7ac7b07fb90628477f46f2bab9/docker/k8s_hub
FROM gesiscss/k8s-hub:5702f46-v1.4.0

USER root
COPY templates /srv/jhub_custom_templates
USER ${NB_USER}
