import os

# Danh sách các microservices và thông tin cấu hình riêng biệt
services = [
    {"name": "auth-service", "placeholder": "auth-image-placeholder", "has_mock": False},
    {"name": "product-service", "placeholder": "product-image-placeholder", "has_mock": False},
    {"name": "order-service", "placeholder": "order-image-placeholder", "has_mock": True},  # Cần pytest-mock
    {"name": "notification-service", "placeholder": "notification-image-placeholder", "has_mock": False},
]

# Template chung cho tất cả các file CI Workflows
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

    # ĐÃ SỬA TẠI ĐÂY: Dùng biến môi trường chuẩn của Bash ($GITHUB_REPOSITORY_LOWER,,) thay vì biểu thức GitHub Actions
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
        
        # Chỉ commit nếu thực sự có sự thay đổi
        git commit -m "chore(gitops): update {service_name} tag to ${{{{ github.sha }}}} [skip ci]" || echo "No changes to commit"
        
        # CHIẾN THUẬT: Vòng lặp kéo code mới về (rebase) rồi push, thử lại tối đa 5 lần nếu bị tranh giành
        for i in {{1..5}}; do
          echo "Đang thử push lần $i..."
          git pull --rebase origin main
          if git push origin main; then
            echo "✅ Push cấu hình thành công!"
            exit 0
          fi
          echo "❌ Push thất bại do xung đột, đang đợi để thử lại..."
          sleep $((RANDOM % 5 + 2)) # Nghỉ ngẫu nhiên từ 2-7 giây để tránh các job đâm sầm vào nhau lần nữa
        done
        exit 1
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