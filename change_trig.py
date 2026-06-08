import os

# Danh sách các thư mục cần tạo/cập nhật file
target_folders = [
    "src/auth-service"  ,"src/notification-service"  ,"src/order-service" , "src/product-service"
]

file_name = "change_trig.txt"

for folder in target_folders:
    # Kiểm tra xem thư mục có tồn tại không
    if os.path.exists(folder):
        file_path = os.path.join(folder, file_name)
        
        # Kiểm tra nếu file đã tồn tại
        if os.path.exists(file_path):
            # Đọc giá trị hiện tại và cộng thêm 1
            with open(file_path, "r") as f:
                try:
                    current_value = int(f.read().strip())
                except ValueError:
                    current_value = 0
            new_value = current_value + 1
        else:
            # Tạo mới với giá trị 0
            new_value = 0
            
        # Ghi giá trị vào file
        with open(file_path, "w") as f:
            f.write(str(new_value))
        
        print(f"Đã cập nhật {file_path} với giá trị: {new_value}")
    else:
        print(f"Thư mục {folder} không tồn tại, bỏ qua.")