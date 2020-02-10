## Run GESIS Hub locally

### Run only JupyterHub to test templates and static files

1. Create a virtual env and activate it

2. Install JupyterHub v1.1.0: https://jupyterhub.readthedocs.io/en/stable/quickstart.html

3. run JupyterHub with custom configuration: `jupyterhub -f jupyterhub_config.py`

4. Open http://localhost:8000

### Run GESIS Hub in minikube

First way (`Run only JupyterHub to test templates and static files`) should normally be enough for local 
development. If you still need it, you can run it with minikube as it is explained here. But be aware that 
`config.yaml` might be incomplete.

1. [Install minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/)

```bash
# to start minikube
minikube start

# to stop minikube
minikube stop
# if you get error "error: You must be logged in to the server (Unauthorized)", 
# # you can delete and re-start minikube cluster
minikube delete
rm -rf ~/.kube

# to start dashboard
minikube dashboard
# to get ip of minikube cluster
minikube ip
```

2. [Install and initialize helm](https://github.com/jupyterhub/binderhub/blob/master/CONTRIBUTING.md#one-time-installation)
```bash
curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash
helm init

helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update
```
Before starting your local deployment run:

`eval $(minikube docker-env)`

This command sets up docker to use the same Docker daemon as your minikube cluster does. 
This means images you build are directly available to the cluster. 
Note: when you no longer wish to use the minikube host, you can undo this change by running:

`eval $(minikube docker-env -u)`

3. 
```bash
git clone git@github.com:gesiscss/orc.git
cd orc
# update binderhub chart
helm dependency update gesishub/gesishub

# mount static folder to minikube cluster
# this directory will be mounted to hub pod in order to server static files
# normally in prod/staging deployment these static files are served by nginx
minikube mount load_balancer/static:/static_extra

# test config for local development
helm template gesishub/gesishub -f gesishub/local/config.yaml
# install it in minikube cluster
helm upgrade --install --namespace=jhub-dev-ns jhub-dev gesishub/gesishub --debug -f gesishub/local/config.yaml

# run this command to reach the application
minikube service --namespace=jhub-dev-ns proxy-public
```
