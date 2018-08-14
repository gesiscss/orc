# https://github.com/gesiscss/jhub_shibboleth_auth/tree/c820dbfbeb37253bf7c0068c515197a981b60fe1/docker/k8s_hub
FROM gesiscss/k8s-hub:ac54cf1-v1.3.0

USER root
COPY templates /srv/jhub_custom_templates
USER ${NB_USER}
