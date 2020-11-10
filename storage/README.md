This is the default storage provider and it is 
based on chart https://github.com/helm/charts/tree/master/stable/nfs-server-provisioner
which is based on 
https://github.com/kubernetes-incubator/external-storage/tree/nfs-provisioner-v2.2.1-k8s1.12/nfs. 
It uses xfs quota to limit size of user directories 
(https://github.com/kubernetes-retired/external-storage/blob/nfs-provisioner-v2.2.1-k8s1.12/nfs/docs/deployment.md#arguments).

`backup` is a daily job to backup GESIS Hub, GESIS Binder and Gallery databases and 
user and grafana persistent volumes.

`pv.yaml` is to create a `hostPath` type PV for nfs provisioner. There nfs creates its shares.
