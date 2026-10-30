# Kubernetes deployment contract

The base manifests deploy one hardened API replica. Before applying them:

1. publish the application image and replace the image reference in
   `base/deployment.yaml` with an immutable digest;
2. populate the `predmaint-models` volume with `champion.json` and its referenced
   release model through the platform's model-delivery job or storage CSI driver;
3. create the API-key secret:

```sh
kubectl create namespace predictive-maintenance --dry-run=client -o yaml | kubectl apply -f -
kubectl -n predictive-maintenance create secret generic predmaint-api-secrets \
  --from-literal=api-key='<strong-random-secret>'
kubectl apply -k deploy/kubernetes/base
```

The pod runs as UID/GID 10001 with a read-only root filesystem, no Linux
capabilities, no privilege escalation, no service-account token, explicit CPU and
memory limits, and separate read-only model and writable prediction volumes.

The replica count and deployment strategy are intentionally fixed to one and
`Recreate`. SQLite cannot safely provide shared multi-pod persistence. Horizontal
scaling requires moving prediction events to PostgreSQL, a queue, or another
external service before changing this contract.
