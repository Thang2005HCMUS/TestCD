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


```bash

helm upgrade arc-runner-set \
    --namespace arc-systems \
    --set githubConfigUrl="https://github.com/Thang2005HCMUS/TestCD" \
    --set githubConfigSecret=controller-manager \
    --set maxRunners=4 \
    --set minRunners=1 \
    --set template.spec.containers[0].name=runner \
    --set template.spec.containers[0].image=ghcr.io/actions/actions-runner:latest \
    --set template.spec.containers[0].volumeMounts[0].name=tool-cache \
    --set template.spec.containers[0].volumeMounts[0].mountPath=/home/runner/_work/_tool \
    --set template.spec.volumes[0].name=tool-cache \
    --set template.spec.volumes[0].emptyDir=\{\} \
    oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
```
```bash
helm install arc-runner-set --namespace arc-systems -f runner-values.yaml oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
```