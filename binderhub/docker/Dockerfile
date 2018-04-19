#https://hub.docker.com/r/jupyterhub/k8s-binderhub/tags/
#sudo docker build -t binder-fork -f helm-chart/images/binderhub/Dockerfile .
FROM jupyterhub/k8s-binderhub:4075ab8

ADD templates/page.html /usr/local/lib/python3.6/site-packages/binderhub/templates/page.html

RUN mv /usr/local/lib/python3.6/site-packages/binderhub/templates/index.html /usr/local/lib/python3.6/site-packages/binderhub/templates/index_base.html
ADD templates/index.html /usr/local/lib/python3.6/site-packages/binderhub/templates/index.html

ADD templates/error.html /usr/local/lib/python3.6/site-packages/binderhub/templates/error.html

ADD templates/loading.html /usr/local/lib/python3.6/site-packages/binderhub/templates/loading.html
