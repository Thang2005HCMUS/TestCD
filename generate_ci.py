import os

# Danh sách các microservices và thông tin cấu hình riêng biệt
services = [
    {"name": "auth-service", "has_mock": False},
    {"name": "product-service", "has_mock": False},
    {"name": "order-service", "has_mock": True},  # Cần pytest-mock
    {"name": "notification-service", "has_mock": False},
]
branch = "helm-dev"

# Template chung cho tất cả các file CI Workflows (Dùng Helm)
workflow_template = """name: CI {service_title}

on:
  push:
    branches: [ "**" ]
    paths:
      - 'src/{service_name}/**'
      - ".github/workflows/ci-{service_name}.yaml"

jobs:
  test-build-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write

    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install Dependencies & Run Tests
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

    # THAY ĐỔI Ở ĐÂY: Dùng yq để cập nhật values.yaml của Helm thay vì Kustomize
    - name: Update Image Tag in Helm values.yaml
      run: |
        yq -i '.services."{service_name}".repository = "ghcr.io/'"${{{{ env.REPO_LOWER }}}}"'/{service_name}"' helm-charts/app-dev/values.yaml
        yq -i '.services."{service_name}".tag = "${{{{ github.sha }}}}"' helm-charts/app-dev/values.yaml

    - name: Commit and Push Manifest Changes
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "github-actions[bot]"
        git add helm-charts/app-dev/values.yaml
        
        # Chỉ commit nếu thực sự có sự thay đổi
        git commit -m "chore(gitops): update {service_name} helm tag to ${{{{ github.sha }}}} [skip ci]" || echo "No changes to commit"
        
        # CHIẾN THUẬT: Vòng lặp kéo code mới về (rebase) rồi push, thử lại tối đa 5 lần
        for i in {{1..5}}; do
          echo "Đang thử push lần $i..."
          git pull --rebase origin {branch_name}
          if git push origin {branch_name}; then
            echo "✅ Push cấu hình thành công!"
            exit 0
          fi
          echo "❌ Push thất bại do xung đột, đang đợi để thử lại..."
          sleep $((RANDOM % 5 + 2))
        done
        exit 1
"""

# Thư mục đích để lưu file YAML
output_dir = ".github/workflows"
os.makedirs(output_dir, exist_ok=True)

# Tiến hành sinh file tự động
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
        
    print(f"✅ Đã cập nhật file CI chạy Helm: {file_path}")

print("\n=== Hoàn thành! Đã chuyển đổi toàn bộ Workflow sang cơ chế Helm ===")