Files (`rbac.yaml`, `psp.yaml`, `deployment.yaml` and `class.yaml`) are based on 
[NFS provisioner (v2.2.1)](https://github.com/kubernetes-incubator/external-storage/tree/nfs-provisioner-v2.2.1-k8s1.12/nfs) repo.

`nfs-provisioner` pod is assigned to a specific node where storage (`/srv/nfs-provisioner`) and
backup (`/backup/nfs-backup`) disks are mounted.