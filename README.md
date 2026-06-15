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
### cấu hình truy cập argoCD qua ingress
```YAML
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS" # Bảo NGINX nói chuyện với ArgoCD bằng HTTPS
    # Nếu bạn dùng chứng chỉ tự ký của ArgoCD, NGINX có thể sẽ chặn vì không tin tưởng. 
    # Thêm dòng dưới để NGINX bỏ qua việc kiểm tra chứng chỉ của ArgoCD:
    nginx.ingress.kubernetes.io/proxy-ssl-verify: "off"
spec:
  ingressClassName: nginx
  rules:
  - host: argocd.local.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              name: https # Hoặc số port là 443
```
### Test CD 

```
chmod +x ./commit.sh
./commit.sh

```


```bash
# Tạo namespace cho ARC
kubectl create namespace arc-systems

# Thêm repo helm và cài đặt Controller
helm install arc \
    --namespace arc-systems \
    oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller
# Thay <YOUR_TOKEN_HERE> bằng GitHub PAT của bạn
kubectl create secret generic controller-manager \
    -n arc-systems \
    --from-literal=github_token=<YOUR_TOKEN_HERE>
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