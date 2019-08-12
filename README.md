# Open Research Computing (ORC)

For more information about ORC project: https://notebooks.gesis.org/about/

## Technical Details

This ORC instance is deployed on kubernetes on bare metal machines with Ubuntu 18.04.
And kubernetes cluster (ORC cluster) is created with [kubeadm](https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/) 
(v1.14.1).
[Flannel](https://github.com/coreos/flannel/tree/v0.11.0) is used as pod network.
Docker version 18.06.2-ce is installed on servers.

All docker images of this project can be found in https://hub.docker.com/u/gesiscss/.

### [Load Balancer](/load_balancer)

Because we setup the kubernetes cluster on baremetal, we use the deployment approach 
["Using a self-provisioned edge"](https://kubernetes.github.io/ingress-nginx/deploy/baremetal/#using-a-self-provisioned-edge).

Nginx is used as reverse proxy server and load balancer. 
It also handles SSL offloading/termination and serves static files. 
It is outside of ORC cluster and a public entrypoint to the cluster. 
All services in the cluster has type `NodePort`.

### [Storage](/storage)

`NFS Server Provisioner` is the default storage provider in ORC cluster.

### [GESIS Hub](/gesishub)

JupyterHub 1.0.0 runs under https://notebooks.gesis.org/hub/. 

Single user server image: https://github.com/gesiscss/data_science_image

### [GESIS Binder](/gesisbinder)

BinderHub runs under https://notebooks.gesis.org/binder/. 

Uses Docker Hub Registry (https://hub.docker.com/u/gesiscss/) to store built images.

### [Gallery](/gallery)

Gallery of popular repos launched on [GESIS Binder](https://notebooks.gesis.org/binder/) 
and featured projects: https://notebooks.gesis.org/gallery/

### [ORC Site](/orc_site)

An app to serve ORC project base pages, such as home and about.


