A micro app to serve ORC project templates.

## How to run locally

```
git clone git@github.com:gesiscss/orc.git
cd orc/orc_site

# create a virtual enviroment.

pip install -U -r requirements.txt

export FLASK_APP=app.py
export FLASK_DEBUG=1

flask run
```

## How to run on Docker

```bash
docker build -t orc-site:latest .
sudo docker run --name orc-site -it --rm -p 5000:5000 orc-site
# or
sudo docker run --name orc-site -d -p 5000:5000 orc-site
```

- https://github.com/docker/labs/tree/bd6bcaa1e25e75dc3611ea063b3d38c65e205141/beginner/flask-app
- https://runnable.com/docker/python/dockerize-your-flask-application
- https://github.com/honestbee/flask_app_k8s

## How to run on k8s

```bash
kubectl create --save-config -f deploy/orc-site-app-test.yaml --namespace=<namespace>
```

## Shibboleth embedded discovery service (EDS)

Shibboleth EDS documentation: https://wiki.shibboleth.net/confluence/display/EDS10/1.+Overview

This files are downloaded from: https://shibboleth.net/downloads/embedded-discovery-service/latest/