#!/bin/bash

# Tạo cấu trúc thư mục cho Source Code Python
mkdir -p src/auth-service
mkdir -p src/product-service
mkdir -p src/order-service
mkdir -p src/notification-service

# Tạo cấu trúc thư mục cho Kubernetes & Kustomize
mkdir -p k8s/base/auth
mkdir -p k8s/base/product
mkdir -p k8s/base/order
mkdir -p k8s/base/notification
mkdir -p k8s/environments/dev

# Tạo thư mục cho GitHub Actions Workflows
mkdir -p .github/workflows

echo "=== Đã tạo xong toàn bộ cấu trúc thư mục Monorepo! ==="