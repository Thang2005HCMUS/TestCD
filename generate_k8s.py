import os

# Cấu hình chi tiết cho từng dịch vụ
services_config = {
    "auth-service": {
        "image_placeholder": "auth-image-placeholder",
        "port": 8000,
        "env": []
    },
    "product-service": {
        "image_placeholder": "product-image-placeholder",
        "port": 8000,
        "env": []
    },
    "order-service": {
        "image_placeholder": "order-image-placeholder",
        "port": 8000,
        "env": [
            {"name": "PRODUCT_SERVICE_URL", "value": "http://product-service:8000"},
            {"name": "NOTIFICATION_SERVICE_URL", "value": "http://notification-service:8000"}
        ]
    },
    "notification-service": {
        "image_placeholder": "notification-image-placeholder",
        "port": 8000,
        "env": []
    }
}

# 1. Template cho Deployment
deployment_template = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service_name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {service_name}
  template:
    metadata:
      labels:
        app: {service_name}
    spec:
      containers:
      - name: {service_name}
        image: {image_placeholder}
        ports:
        - containerPort: {port}
{env_section}"""

# 2. Template cho Service
service_template = """apiVersion: v1
kind: Service
metadata:
  name: {service_name}
spec:
  ports:
  - port: {port}
    targetPort: {port}
  selector:
    app: {service_name}
"""

# 3. Template cho Kustomization
kustomization_template = """resources:
  - deployment.yaml
  - service.yaml
"""

# Thư mục gốc chứa các file base của K8s
base_dir = "k8s/base"

print("=== BẮT ĐẦU SINH FILE K8S MANIFESTS GỐC ===")

for svc_name, config in services_config.items():
    # Tạo thư mục đích cho từng service (ví dụ: k8s/base/auth-service)
    # Lưu ý: file kustomization.yaml ở môi trường dev đang trỏ tới ../../base/auth, product... 
    # Nên chúng ta sẽ đặt tên thư mục ngắn gọn theo đúng thiết kế trước đó: auth, product, order, notification
    short_name = svc_name.split("-")[0]
    svc_dir = os.path.join(base_dir, short_name)
    os.makedirs(svc_dir, exist_ok=True)
    
    # Xử lý phần biến môi trường (Environment Variables) nếu có
    env_section = ""
    if config["env"]:
        env_section = "        env:\n"
        for item in config["env"]:
            env_section += f"        - name: {item['name']}\n"
            env_section += f"          value: \"{item['value']}\"\n"
    
    # Render nội dung Deployment và ghi file
    dep_content = deployment_template.format(
        service_name=svc_name,
        image_placeholder=config["image_placeholder"],
        port=config["port"],
        env_section=env_section.rstrip()
    )
    with open(os.path.join(svc_dir, "deployment.yaml"), "w", encoding="utf-8") as f:
        f.write(dep_content)
        
    # Render nội dung Service và ghi file
    svc_content = service_template.format(
        service_name=svc_name,
        port=config["port"]
    )
    with open(os.path.join(svc_dir, "service.yaml"), "w", encoding="utf-8") as f:
        f.write(svc_content)
        
    # Ghi file kustomization.yaml
    with open(os.path.join(svc_dir, "kustomization.yaml"), "w", encoding="utf-8") as f:
        f.write(kustomization_template)
        
    print(f"✅ Đã tạo cấu hình K8s thành công cho: {svc_name} -> {svc_dir}/")

print("\n=== HOÀN THÀNH! Đã lấp đầy thư mục k8s/base sẵn sàng cho ArgoCD ===")