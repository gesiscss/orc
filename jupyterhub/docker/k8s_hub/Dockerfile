# https://github.com/gesiscss/jhub_shibboleth_auth/tree/78fbca3a5319faf5e8c1787794117dd30e3bf1c8/docker/k8s_hub
FROM gesiscss/k8s-hub:ae44b17-v1.4.0

USER root
COPY templates /srv/jhub_custom_templates
USER ${NB_USER}

RUN pip3 install https://github.com/jupyterhub/kubespawner/archive/481ec0926960927300c7355c48bd03230ee857f0.tar.gz
