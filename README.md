# Open Research Computing (ORC)

For more information about iLCM project and ORC environment:

- https://www.gesis.org/en/research/external-funding-projects/overview-external-funding-projects/a-virtual-research-infrastructure-for-large-scale-qualitative-data/
- https://notebooks.gesis.org/about/
- http://gepris.dfg.de/gepris/projekt/324867496?language=en

## Technical Details

This ORC instance is deployed on kubernetes on bare metal machines with Ubuntu 16.04.
And kubernetes cluster is created with [kubeadm](https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/).
[Flannel](https://github.com/coreos/flannel/tree/v0.10.0) is used as pod network.
Docker version 17.03.2-ce is installed on servers.

All docker images of this project can be found in https://hub.docker.com/u/gesiscss/.

To monitor GESIS Notebooks: https://notebooks.gesis.org/grafana/

### [Nginx & Shibboleth](/nginx_shibboleth/)

Nginx is used as reverse proxy and load balancer.
It also handles [Shibboleth](https://www.shibboleth.net/) login and
SSL offloading/termination.

In this ORC instance ports 80 and 443 of `nginx-shibboleth` container are exposed to host machine.
All services in ORC cluster in k8s has type `NodePort` and run behind `nginx-shibboleth-service`.

[Dockerfile](/nginx_shibboleth/docker/Dockerfile) for `nginx-shibboleth` container
extends [this image](https://github.com/gesiscss/jhub_shibboleth_auth/tree/master/docker/shibboleth)
to be used in ORC instance.

[Nginx configuration files](/nginx_shibboleth/nginx)

[Shibboleth configuration files](/nginx_shibboleth/shibboleth/conf)

### [JupyterHub](/jupyterhub)

JupyterHub 0.9.4 runs under https://notebooks.gesis.org/jupyter/. 
Chart version [0.8-1400e35](https://github.com/jupyterhub/zero-to-jupyterhub-k8s/tree/1400e35).

[Dockerfile](/jupyterhub/docker/k8s_hub) of hub
extends [this image](https://github.com/gesiscss/jhub_shibboleth_auth/tree/master/docker/k8s_hub)
in order to use [jhub_shibboleth_auth](https://github.com/gesiscss/jhub_shibboleth_auth)
authenticator in ORC.

[Single user server image](/jupyterhub/docker/singleuser)

### [BinderHub](/binderhub)

BinderHub (with `jupyter/repo2docker:a161b09`) runs under https://notebooks.gesis.org/binder/. 
Chart version [0.1.0-47ed8cd](https://github.com/jupyterhub/binderhub/tree/47ed8cd)

Uses Docker Hub Registry (https://hub.docker.com/u/gesiscss/) to store built images.

### [NFS provisioner](/nfs_provisioner)

NFS provisioner (v2.2.0) is currently set as the default storage provider in k8s cluster.

### [ORC Site](/orc_site)

A micro app to serve ORC templates.