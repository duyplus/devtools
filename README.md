# Devtools

Ứng dụng Flask gom các công cụ nhỏ dùng hằng ngày: xử lý text, ảnh, mã nguồn, tính toán và tạo mật khẩu. Giao diện hỗ trợ dark/light mode, tiếng Việt/tiếng Anh, chạy được local, Fly.io và cPanel Passenger.

## Tính năng

- **Icon Converter**: tạo favicon pack dạng ZIP hoặc chuyển ảnh sang `.ico`.
- **Delimiter Converter**: đổi danh sách giữa xuống dòng, dấu phẩy, chấm phẩy, pipe, khoảng trắng hoặc dấu tùy chỉnh.
- **Percentage Calculator**: tính phần trăm, tỷ lệ, tăng/giảm và tìm tổng từ một phần.
- **Base64 Encoder/Decoder**: mã hóa và giải mã văn bản UTF-8 bằng Base64.
- **JS Obfuscator/Deobfuscator**: làm rối JavaScript và giải mã các wrapper được hỗ trợ.
- **Password Generator**: tạo mật khẩu ngẫu nhiên an toàn, tùy chỉnh độ dài, số lượng và loại ký tự.

## Công nghệ

- Python 3.12
- Flask
- Pillow
- Gunicorn
- Jinja templates
- CSS/JavaScript thuần

## Cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Chạy local

```powershell
flask --app wsgi --debug run
```

Mở:

```text
http://127.0.0.1:5000
```

Chạy không debug:

```powershell
flask --app wsgi run
```

## Kiểm tra

```powershell
python -m unittest
```

## Chạy production local

```powershell
gunicorn wsgi:app --bind 127.0.0.1:8080
```

Trên Windows, Gunicorn thường không chạy native tốt. Dùng lệnh Flask local ở trên hoặc chạy Gunicorn trong Linux/WSL/container.

## Docker

```powershell
docker build -t devtools .
docker run --rm -p 8080:8080 devtools
```

Mở:

```text
http://127.0.0.1:8080
```

## Deploy Fly.io

Repo có sẵn `fly.toml`, `Procfile`, `wsgi.py` và `requirements.txt`.

```powershell
fly deploy
```

Health check:

```text
/healthz
```

## Deploy cPanel

1. Vào **Setup Python App**.
2. Chọn Python theo `runtime.txt`.
3. Cài dependency từ `requirements.txt`.
4. Trỏ Passenger tới `passenger_wsgi.py`.
5. Restart app sau khi upload code mới.

## Cấu trúc

```text
app/
  controllers/       Flask routes/controllers
  services/          Logic xử lý chính
  static/            CSS, JavaScript, image assets
  templates/         Jinja templates
  tools/registry.py  Danh sách tool hiển thị trên dashboard/menu
tests/               Unit tests và route tests
wsgi.py              Entry point cho Flask/Gunicorn
passenger_wsgi.py    Entry point cho cPanel Passenger
Dockerfile           Docker image
fly.toml             Cấu hình Fly.io
Procfile             Web process command
```

## Thêm tool mới

1. Tạo service trong `app/services/` nếu tool có logic riêng.
2. Tạo controller trong `app/controllers/`.
3. Tạo template trong `app/templates/tools/`.
4. Đăng ký tool trong `app/tools/registry.py`.
5. Thêm test trong `tests/`.

Dashboard và sidebar tự đọc danh sách tool từ registry.

## Ghi chú

- Không dùng database.
- Upload được xử lý trong request, không lưu lâu dài.
- Giới hạn upload hiện tại: `8 MB`.
- Password Generator dùng Web Crypto trên trình duyệt và `secrets` ở server fallback.
