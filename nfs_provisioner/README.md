NFS provisioner (v1.0.9) files (`rbac.yaml`, `deployment.yaml` and `class.yaml`) are based on
https://github.com/kubernetes-incubator/external-storage/tree/nfs-provisioner-v1.0.9/nfs.

`nfs-provisioner` pod is assigned to a specific node where storage (`/srv/nfs-provisioner`) and
backup (`/backup/nfs-backup`) disks are mounted.