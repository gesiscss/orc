# https://github.com/gesiscss/jhub_shibboleth_auth/tree/28385b629495de7e57fee22fc2e171c8bb63af73/docker/k8s_hub
FROM gesiscss/k8s-hub:db9569c-v1.4.0

USER root
COPY templates /srv/jhub_custom_templates
USER ${NB_USER}
