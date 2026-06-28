# DevTools

DevTools là ứng dụng Flask gom các công cụ nhỏ để xử lý văn bản, mã nguồn, hình ảnh, QR, phần trăm và mật khẩu. Ứng dụng không dùng database, có thể chạy local, Docker, Fly.io hoặc cPanel Passenger.

## Công cụ

- Icon Converter: tạo icon pack hoặc chuyển ảnh sang `.ico`.
- Delimiter Converter: đổi danh sách giữa xuống dòng, dấu phẩy, chấm phẩy, pipe, khoảng trắng hoặc dấu tùy chỉnh.
- Text Diff: so sánh hai khối văn bản, xem thay đổi và merge từng hunk.
- Percentage Calculator: tính phần trăm, tỷ lệ, tăng/giảm và suy ngược tổng.
- Base64 Converter: encode/decode văn bản UTF-8 bằng Base64.
- JS De/Obfuscator: làm rối JavaScript và giải các wrapper được hỗ trợ.
- Password Generator: tạo mật khẩu ngẫu nhiên an toàn theo độ dài, số lượng và nhóm ký tự.
- QR Generator: tạo QR cho URL, text, email, điện thoại, SMS, WiFi, danh thiếp, vị trí và sự kiện; hỗ trợ màu, kích thước, logo và frame text.

## Công nghệ

- Python 3.12+
- Flask
- Pillow
- qrcode
- Gunicorn
- Jinja templates
- CSS thuần
- JavaScript, jQuery 3, Lucide icons
- `unittest`

## Cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Chạy local

```powershell
python -m flask --app wsgi:app --debug run
```

Mở:

```text
http://127.0.0.1:5000
```

Local development dùng asset dễ đọc:

- `app/static/css/app.css`
- `app/static/js/app.js`

## Kiểm tra

```powershell
python -m unittest -q
python -m compileall -q app tests scripts
```

## Minify asset

Tạo CSS và JS minified:

```powershell
python scripts\minify_assets.py
```

File tạo ra:

- `app/static/css/app.min.css`
- `app/static/js/app.min.js`

Các file này bị ignore bởi git. Production chỉ dùng chúng khi bật `MINIFY_ASSETS=1`.

Test chế độ production minify ở local:

```powershell
$env:MINIFY_ASSETS="1"
$env:MINIFY_HTML="1"
python -m flask --app wsgi:app run
```

`MINIFY_HTML=1` xóa HTML comment và khoảng trắng giữa các tag sau khi Flask render trang.

## Production

Env vars cần bật để dùng output minified:

```text
MINIFY_ASSETS=1
MINIFY_HTML=1
```

Nên cấu hình secret:

```text
SECRET_KEY=<giá trị random mạnh>
```

Chạy bằng Gunicorn trên Linux/WSL/container:

```powershell
gunicorn wsgi:app --bind 0.0.0.0:8080
```

Khi phát triển local trên Windows, dùng lệnh Flask dev ở trên thay vì Gunicorn.

## Docker

```powershell
docker build -t devtools .
docker run --rm -p 8080:8080 devtools
```

Mở:

```text
http://127.0.0.1:8080
```

Docker build sẽ chạy `python scripts/minify_assets.py` và bật env minify.

## Fly.io

Repo có sẵn `fly.toml`.

```powershell
fly deploy
```

Health check:

```text
/healthz
```

## cPanel Passenger

1. Tạo Python app trong cPanel.
2. Dùng phiên bản Python theo `runtime.txt`.
3. Cài dependency từ `requirements.txt`.
4. Trỏ Passenger tới `passenger_wsgi.py`.
5. Chạy `python scripts/minify_assets.py` trong lúc upload/deploy nếu muốn dùng static asset minified.
6. Set `MINIFY_ASSETS=1`, `MINIFY_HTML=1` và `SECRET_KEY`.
7. Restart app.

## Cấu trúc dự án

```text
app/
  controllers/       Flask routes/controllers
  services/          Logic xử lý của từng tool
  static/            CSS, JavaScript, fonts, images
  templates/         Jinja templates
  tools/registry.py  Registry tool cho dashboard/sidebar
scripts/
  minify_assets.py   Build step minify CSS/JS
tests/               Route tests và service tests
wsgi.py              Entry point Flask/Gunicorn
passenger_wsgi.py    Entry point cPanel Passenger
Dockerfile           Docker image
fly.toml             Cấu hình Fly.io
Procfile             Web process command
runtime.txt          Gợi ý Python runtime
```

## Đa ngôn ngữ

Ngôn ngữ hỗ trợ: `vi`, `en`.

- Text server/template nằm trong `app/i18n.py`.
- Template dùng `t("key")`.
- Service raise error key; controller gọi `translate_error(...)`.
- JavaScript đọc translated messages từ `#devtools-i18n` trong `base.html`.

## Thêm tool mới

1. Thêm service logic trong `app/services/` nếu cần.
2. Thêm controller trong `app/controllers/`.
3. Thêm template trong `app/templates/tools/`.
4. Đăng ký tool trong `app/tools/registry.py`.
5. Thêm route/service tests trong `tests/`.

Dashboard và sidebar đọc danh sách tool từ registry.

## Ghi chú

- Không dùng database.
- Giới hạn upload: 8 MB.
- File upload được xử lý trong request memory, không lưu lâu dài.
- Các tool xử lý ảnh sẽ reject ảnh quá lớn/decompression bomb.
- Theme sáng/tối lưu bằng `localStorage`.
- QR frame text dùng font Quicksand từ `app/static/fonts/` khi có sẵn.
