## Test ArgoCD and Full CI/CD pipeline

```
kubectl create namespace testcd
```

```
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<GITHUB USERNAME> \
  --docker-password=<GITHUB TOKEN>\
  --docker-email=<EMAIL GITHUB> \
  -n testcd

```
### Download ArgoCD
```
kubectl apply -n argocd   --server-side   --force-conflicts   -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

```
### Cấu hình để truy cập ArgoCD
```
kubectl port-forward svc/argocd-server -n argocd 9000:443
```
### Truy cập ArgoCD
```
https://localhost:9000
```

### Test CD 

```
chmod +x ./commit.sh
./commit.sh

```
