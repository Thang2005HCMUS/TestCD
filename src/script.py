import os

# File output
OUTPUT_FILE = "content.txt"

# Lấy thư mục hiện tại
root_dir = os.getcwd()

# Các file cần bỏ qua
exclude_files = {OUTPUT_FILE}

# Hàm đọc file text an toàn
def read_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                return f.read()
        except:
            return "[Không thể đọc nội dung file]"
    except Exception as e:
        return f"[Lỗi khi đọc file: {e}]"

# Ghi toàn bộ nội dung vào content.txt
with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
    for foldername, subfolders, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename in exclude_files:
                continue

            full_path = os.path.join(foldername, filename)

            # Đường dẫn tương đối
            relative_path = os.path.relpath(full_path, root_dir)

            # Đọc nội dung file
            content = read_file(full_path)

            # Ghi ra file
            output.write(f"======{relative_path} content ======:\n")
            output.write(content)
            output.write("\n\n")
print()
print(f"Đã ghi xong vào {OUTPUT_FILE}")