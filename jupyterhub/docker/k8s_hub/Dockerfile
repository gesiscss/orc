# https://github.com/gesiscss/jhub_shibboleth_auth/tree/39457f1838dc6af9a36fcd95d95a2cffef952430/docker/k8s_hub
FROM gesiscss/k8s-hub:80a76ac-v1.4.0


USER root
COPY templates /srv/jhub_custom_templates
USER ${NB_USER}