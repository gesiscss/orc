## Volumes

### Secrets

#### `shibboleth-sp-tls-secret`

```bash
kubectl create secret tls shibboleth-sp-tls-secret \
    --key=path/to/shibboleth-sp-key.pem \
    --cert=path/to/shibboleth-sp-cert.pem \
    --namespace=<namespace>
```

#### `letsencrypt-manual-secret`

```bash
```

### Configmaps



## how to deploy

```bash
kubectl create --save-config -f nginx-shibboleth-app.yaml --namespace=<namespace>
```



