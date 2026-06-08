import os

# Danh sách các microservices và thông tin cấu hình riêng biệt
services = [
    {"name": "auth-service", "placeholder": "auth-image-placeholder", "has_mock": False},
    {"name": "product-service", "placeholder": "product-image-placeholder", "has_mock": False},
    {"name": "order-service", "placeholder": "order-image-placeholder", "has_mock": True},  # Cần pytest-mock
    {"name": "notification-service", "placeholder": "notification-image-placeholder", "has_mock": False},
]

# Template chung cho tất cả các file CI Workflows
# Mẹo: Đã nhân đôi {{ thành {{{{ cho các biến GitHub Actions để Python không can thiệp
workflow_template = """name: CI {service_title}

on:
  push:
    branches:
      - main
    paths:
      - 'src/{service_name}/**'

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

    # SỬA LẠI DÒNG NÀY: Đã bọc block env và nhân bốn ngoặc nhọn cho Python format
    - name: Downcase REPO name
      run: |
        REPO="${{{{ github.repository }}}}"
        echo "REPO_LOWER=${{{{REPO,,}}}}" >> $GITHUB_ENV
      env:
        GITHUB_REPOSITORY_LOWER: ${{{{ github.repository }}}}

    - name: Build and Push Docker Image
      uses: docker/build-push-action@v5
      with:
        context: ./src/{service_name}
        push: true
        tags: ghcr.io/${{{{ env.REPO_LOWER }}}}/{service_name}:${{{{ github.sha }}}}
    # Test
    - name: Setup Kustomize
      uses: imranismail/setup-kustomize@v2

    - name: Update Image Tag in Kustomize
      run: |
        cd k8s/environments/dev
        kustomize edit set image {image_placeholder}=ghcr.io/${{{{ env.REPO_LOWER }}}}/{service_name}:${{{{ github.sha }}}}

    - name: Commit and Push Manifest Changes
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "github-actions[bot]"
        git add k8s/environments/dev/kustomization.yaml
        git commit -m "chore(gitops): update {service_name} tag to ${{{{ github.sha }}}} [skip ci]" || echo "No changes to commit"
        git push
"""

# Thư mục đích để lưu file YAML
output_dir = ".github/workflows"
os.makedirs(output_dir, exist_ok=True)

# Tiến hành sinh file tự động
for svc in services:
    # Định dạng tên hiển thị (Ví dụ: auth-service -> Auth Service)
    title = " ".join([word.capitalize() for word in svc["name"].split("-")])
    
    # Kiểm tra xem service này có cần cài thêm pytest-mock để test không
    mock_package = "pytest-mock" if svc["has_mock"] else ""
    
    # Render nội dung từ template
    rendered_content = workflow_template.format(
        service_title=title,
        service_name=svc["name"],
        image_placeholder=svc["placeholder"],
        mock_package=mock_package
    )
    
    # Đường dẫn file đầu ra
    file_path = os.path.join(output_dir, f"ci-{svc['name']}.yaml")
    
    # Ghi file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(rendered_content)
        
    print(f"✅ Đã sinh file cấu hình thành công: {file_path}")

print("\n=== Hoàn thành! Toàn bộ 4 file CI đã nằm trong thư mục .github/workflows ===")