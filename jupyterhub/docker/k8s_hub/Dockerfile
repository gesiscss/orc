# https://github.com/gesiscss/jhub_shibboleth_auth/tree/c96e23a2d9d065aa0cf959d6c0599db24646abdd/docker/k8s_hub
FROM gesiscss/k8s-hub:578b3a2-v1.2.0

USER root
COPY templates /srv/jhub_custom_templates
USER ${NB_USER}
