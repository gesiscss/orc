# Open Research Computing (ORC)

For more information about ORC project: https://notebooks.gesis.org/about/

Feel free to open an issue in this repository if there are any questions or contact us at [notebooks@gesis.org](mailto:notebooks@gesis.org).

## Technical Details

This ORC instance is deployed on kubernetes on bare metal machines with Ubuntu 18.04.
And kubernetes cluster (ORC cluster) is created with [kubeadm](https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/)
(v1.18.3).
[calico](https://github.com/projectcalico/calico/tree/v3.14.1) is used as network provider.
Docker version 19.03.8 is installed on servers.

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

[Persistent BinderHub](https://github.com/gesiscss/persistent_binderhub) runs under https://notebooks.gesis.org/hub/.

Uses Docker Hub Registry (https://hub.docker.com/u/gesiscss/) to store built images. 

### [GESIS Binder](/gesisbinder)

BinderHub runs under https://notebooks.gesis.org/binder/.

GESIS Hub and Binder uses same docker images (they uses same repo2docker version).

### [Gallery](/gallery)

Gallery of popular repos launched on [GESIS Binder](https://notebooks.gesis.org/binder/)
and featured projects: https://notebooks.gesis.org/gallery/
