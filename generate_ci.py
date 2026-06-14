import os

services = [
    {"name": "auth-service", "has_mock": False},
    {"name": "product-service", "has_mock": False},
    {"name": "order-service", "has_mock": True},        
    {"name": "notification-service", "has_mock": True}, 
]
branch = "hybrid-helm-dev"

workflow_template = """name: CI {service_title}

on:
  push:
    branches: [ "**" ]
    paths:
      - 'src/{service_name}/**'
      - ".github/workflows/ci-{service_name}.yaml"

jobs:
  # ==========================================
  # JOB 1: CHẠY TRÊN CLOUD (UNIT TEST & BUILD IMAGE)
  # ==========================================
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    outputs:
      image_tag: ${{{{ github.sha }}}}

    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install Dependencies & Run Unit Tests
      run: |
        cd src/{service_name}
        pip install --no-cache-dir -r requirements.txt pytest {mock_package}
        pytest test_app.py

    - name: Log in to GHCR
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{{{ github.actor }}}}
        password: ${{{{ secrets.GITHUB_TOKEN }}}}

    - name: Downcase REPO name
      run: |
        echo "REPO_LOWER=${{GITHUB_REPOSITORY_LOWER,,}}" >> $GITHUB_ENV
      env:
        GITHUB_REPOSITORY_LOWER: ${{{{ github.repository }}}}

    - name: Build and Push Docker Image
      uses: docker/build-push-action@v5
      with:
        context: ./src/{service_name}
        push: true
        tags: ghcr.io/${{{{ env.REPO_LOWER }}}}/{service_name}:${{{{ github.sha }}}}

  # ==========================================
  # JOB 2: CHẠY TẠI K8S LOCAL QUA ARC (INTEGRATION TEST)
  # ==========================================
  integration-test:
    runs-on: arc-runner-set
    needs: build-and-push
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Downcase REPO name
      run: |
        echo "REPO_LOWER=${{GITHUB_REPOSITORY_LOWER,,}}" >> $GITHUB_ENV
      env:
        GITHUB_REPOSITORY_LOWER: ${{{{ github.repository }}}}

    - name: Setup Ephemeral Environment & Run Integration Test
      run: |
        # Đặt tên Namespace biệt lập tránh trùng lặp giữa các luồng Monorepo chạy song song
        NS="test-{service_name}-${{{{ github.run_id }}}}-${{{{ github.run_attempt }}}}"
        echo "Namespace tạm thời: $NS"
        
        # Tạo namespace độc lập
        kubectl create namespace $NS
        
        # Cài đặt hạ tầng Kafka/Zookeeper tạm thời phục vụ đợt test
        helm install kafka-test ./helm-charts/kafka-infra --namespace $NS
        
        # Đợi Kafka cluster sẵn sàng hoạt động
        kubectl rollout status deployment/kafka --namespace $NS --timeout=90s
        
        # Cài đặt toàn bộ ứng dụng Microservices (Inject cái Tag Image vừa build ở Job 1 vào)
        helm install app-test ./helm-charts/app-dev --namespace $NS \
          --set services.{service_name}.repository=ghcr.io/${{{{ env.REPO_LOWER }}}}/{service_name} \
          --set services.{service_name}.tag=${{{{ github.sha }}}} \
          --set services.notification-service.env[0].value="kafka-service.$NS.svc.cluster.local:9092" \
          --set services.order-service.env[0].value="kafka-service.$NS.svc.cluster.local:9092"

        # Đợi các pod microservices lên đều
        kubectl rollout status deployment/{service_name} --namespace $NS --timeout=60s

        # Tiến hành chạy file Integration Test thực tế hướng vào Endpoint của K8s Service nội bộ
        pip install pytest httpx
        pytest src/{service_name}/integration_test.py --ns=$NS
        
    # LUÔN LUÔN DỌN DẸP SẠCH SẼ KỂ CẢ TEST THÀNH CÔNG HAY THẤT BẠI
    - name: Purge Ephemeral Environment (Anti-Trash)
      if: always()
      run: |
        NS="test-{service_name}-${{{{ github.run_id }}}}-${{{{ github.run_attempt }}}}"
        echo "🧹 Đang dọn dẹp triệt để namespace: $NS"
        kubectl delete namespace $NS --ignore-not-found=true
        rm -rf ${{{{ github.workspace }}}}/*

  # ==========================================
  # JOB 3: QUAY LẠI CLOUD (SỬA TAG FILE MANIFEST CHÍNH THỨC)
  # ==========================================
  update-gitops-manifest:
    runs-on: ubuntu-latest
    needs: integration-test
    permissions:
      contents: write
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Downcase REPO name
      run: |
        echo "REPO_LOWER=${{GITHUB_REPOSITORY_LOWER,,}}" >> $GITHUB_ENV
      env:
        GITHUB_REPOSITORY_LOWER: ${{{{ github.repository }}}}

    - name: Update Image Tag in Helm values.yaml
      run: |
        yq -i '.services."{service_name}".repository = "ghcr.io/'"${{{{ env.REPO_LOWER }}}}"'/{service_name}"' helm-charts/app-dev/values.yaml
        yq -i '.services."{service_name}".tag = "${{{{ github.sha }}}}"' helm-charts/app-dev/values.yaml

    - name: Commit and Push Manifest Changes
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "github-actions[bot]"
        git add helm-charts/app-dev/values.yaml
        
        git commit -m "chore(gitops): update {service_name} helm tag to ${{{{ github.sha }}}} [skip ci]" || echo "No changes to commit"
        
        for i in {{1..5}}; do
          echo "Đang thử push lần $i..."
          git pull --rebase origin {branch_name}
          if git push origin {branch_name}; then
            echo "✅ Push cấu hình thành công, chờ ArgoCD đồng bộ!"
            exit 0
          fi
          echo "❌ Trùng lịch push với service khác, đang đợi rebase lại..."
          sleep $(((RANDOM % 5 + 2)))
        done
        exit 1
"""

output_dir = ".github/workflows"
os.makedirs(output_dir, exist_ok=True)

for svc in services:
    title = " ".join([word.capitalize() for word in svc["name"].split("-")])
    mock_package = "pytest-mock" if svc["has_mock"] else ""
    
    rendered_content = workflow_template.format(
        service_title=title,
        service_name=svc["name"],
        mock_package=mock_package,
        branch_name=branch
    )
    
    file_path = os.path.join(output_dir, f"ci-{svc['name']}.yaml")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(rendered_content)
        
    print(f"✅ Đã cập nhật file Hybrid CI chạy Helm: {file_path}")