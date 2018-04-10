# https://github.com/gesiscss/jhub_shibboleth_auth/tree/master/docker/shibboleth
FROM gesiscss/nginx-shibboleth:8540088

RUN apt-get update && \
    apt-get install -yq --no-install-recommends \
    vim \
    wget \
    htop \
    less && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN cd /etc/shibboleth && \
    wget --quiet --no-check-certificate https://www.aai.dfn.de/fileadmin/metadata/dfn-aai.g2.pem

RUN sed -i 's/worker_processes  1;/worker_processes  auto;/g' /etc/nginx/nginx.conf

EXPOSE 80
