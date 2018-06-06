#!/bin/sh

# replace letsencrypt ssl certs
sudo kubectl create secret tls letsencrypt-secret \
    --key=/etc/letsencrypt/live/notebooks-test.gesis.org/privkey.pem \
    --cert=/etc/letsencrypt/live/notebooks-test.gesis.org/fullchain.pem \
    --namespace=orc-test-ns \
    -o yaml --dry-run | kubectl replace -f -
sudo kubectl create secret tls letsencrypt-secret \
    --key=/etc/letsencrypt/live/notebooks.gesis.org/privkey.pem \
    --cert=/etc/letsencrypt/live/notebooks.gesis.org/fullchain.pem \
    --namespace=orc-ns \
    -o yaml --dry-run | kubectl replace -f -

PROJECT_PATH="/home/iuser/ilcm/"
cd "$PROJECT_PATH"
# update deployments
# kubectl replace --force -> does not recreate pods if secret/configmap is updated
kubectl delete deployment nginx-shibboleth-test-deployment --namespace=orc-test-ns
kubectl delete deployment nginx-shibboleth-deployment --namespace=orc-ns
kubectl apply -f orc/nginx_shibboleth/nginx-shibboleth-app-test.yaml --namespace=orc-test-ns
kubectl apply -f orc/nginx_shibboleth/nginx-shibboleth-app.yaml --namespace=orc-ns
