This is the default storage provider and it is 
based on chart https://github.com/helm/charts/tree/master/stable/nfs-server-provisioner
which is based on 
https://github.com/kubernetes-incubator/external-storage/tree/nfs-provisioner-v2.2.1-k8s1.12/nfs

It uses xfs quota to limit size of user directories, but by default it does not work fully and 
that's why we have `quota.py` 
(see https://github.com/kubernetes-incubator/external-storage/issues/855).

`backup` is a daily job to backup juypterhub, gesisbinder and gallery databases and 
user, grafana and prometheus persistent volumes.

`pv.yaml` is to create a `hostPath` type PV for nfs provisioner. There nfs creates its shares.
