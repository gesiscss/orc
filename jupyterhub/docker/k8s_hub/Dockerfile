# https://github.com/gesiscss/jhub_shibboleth_auth/tree/c8ac23392784532a2c187ed5bd99e8fd8be324cb/docker/k8s_hub
FROM gesiscss/k8s-hub:2ff9218-v1.2.0

USER root
COPY templates /srv/jhub_custom_templates
USER ${NB_USER}
