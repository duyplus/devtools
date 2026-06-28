import json
from io import BytesIO
import warnings
import zipfile

from PIL import Image, ImageOps, UnidentifiedImageError


class IconError(ValueError):
    def __init__(self, key):
        self.key = key
        self.params = {}
        super().__init__(key)


ICO_SIZES = {16, 24, 32, 48, 64, 128, 256}
MAX_IMAGE_PIXELS = 4_000_000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def generate_ico(image_bytes, sizes, bit_depth="32", keep_ratio=False):
    sizes = _clean_sizes(sizes)
    if bit_depth == "8" and 256 in sizes:
        raise IconError("icons.error.size_256_alpha")

    image = _open_image(image_bytes)
    base = _square_png(image, max(sizes), keep_ratio=keep_ratio)
    if bit_depth == "8":
        base = base.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
    elif bit_depth != "32":
        raise IconError("icons.error.bit_depth")

    output = BytesIO()
    base.save(output, format="ICO", sizes=[(size, size) for size in sizes])
    output.seek(0)
    return output


def _has_transparency(img):
    if img.mode == 'RGBA':
        alpha = img.split()[-1]
        return alpha.getbbox() is not None and min(alpha.getextrema()) < 255
    elif img.mode == 'P' and 'transparency' in img.info:
        return True
    return False


def _add_white_background(img):
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    background = Image.new('RGB', img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[-1])
    return background


def _resize_with_white_bg(img, size, keep_ratio):
    img_copy = img.copy()
    if keep_ratio:
        img_copy.thumbnail((size, size), Image.Resampling.LANCZOS)
        new_img = Image.new('RGB', (size, size), (255, 255, 255))
        x = (size - img_copy.width) // 2
        y = (size - img_copy.height) // 2
        new_img.paste(img_copy, (x, y))
        return new_img
    else:
        return img_copy.resize((size, size), Image.Resampling.LANCZOS)


def generate_favicon_pack(image_bytes, keep_ratio=False):
    img = _open_image(image_bytes)
    
    if _has_transparency(img):
        img = _add_white_background(img)
    else:
        if img.mode != "RGB":
            img = img.convert("RGB")
            
    base_img = _resize_with_white_bg(img, 1024, keep_ratio)
    output = BytesIO()

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        sizes = {
            # Web favicons
            "favicon-16x16.png": 16,
            "favicon-32x32.png": 32,
            "favicon-96x96.png": 96,
            
            # Android icons
            "android-icon-36x36.png": 36,
            "android-icon-48x48.png": 48,
            "android-icon-72x72.png": 72,
            "android-icon-96x96.png": 96,
            "android-icon-144x144.png": 144,
            "android-icon-192x192.png": 192,
            
            # Apple Touch icons
            "apple-icon-40x40.png": 40,
            "apple-icon-58x58.png": 58,
            "apple-icon-60x60.png": 60,
            "apple-icon-76x76.png": 76,
            "apple-icon-80x80.png": 80,
            "apple-icon-87x87.png": 87,
            "apple-icon-114x114.png": 114,
            "apple-icon-120x120.png": 120,
            "apple-icon-128x128.png": 128,
            "apple-icon-136x136.png": 136,
            "apple-icon-144x144.png": 144,
            "apple-icon-152x152.png": 152,
            "apple-icon-167x167.png": 167,
            "apple-icon-180x180.png": 180,
            "apple-icon-192x192.png": 192,
            "apple-icon-1024x1024.png": 1024,
            
            # Microsoft icons
            "ms-icon-70x70.png": 70,
            "ms-icon-144x144.png": 144,
            "ms-icon-150x150.png": 150,
            "ms-icon-310x310.png": 310
        }
        
        # 1. Generate main folder images
        for filename, size in sizes.items():
            resized = _resize_with_white_bg(base_img, size, keep_ratio)
            img_bytes_io = BytesIO()
            if size == 1024:
                resized_p = resized.convert('P', palette=Image.Palette.ADAPTIVE, colors=256)
                resized_p.save(img_bytes_io, format='PNG', optimize=True, compress_level=9)
            else:
                resized.save(img_bytes_io, format='PNG', optimize=True)
            archive.writestr(filename, img_bytes_io.getvalue())
            
        # 2. Generate favicon.ico (16x16)
        favicon_img = _resize_with_white_bg(base_img, 16, keep_ratio)
        favicon_ico = favicon_img.convert('RGBA')
        ico_io = BytesIO()
        favicon_ico.save(ico_io, format='ICO', sizes=[(16, 16)])
        archive.writestr("favicon.ico", ico_io.getvalue())
        
        # 3. Generate apple icons folder (icons/)
        apple_sizes = [48, 72, 96, 120, 144, 152, 167, 180, 192, 1024]
        for size in apple_sizes:
            resized = _resize_with_white_bg(base_img, size, keep_ratio)
            img_bytes_io = BytesIO()
            if size == 1024:
                resized_p = resized.convert('P', palette=Image.Palette.ADAPTIVE, colors=256)
                resized_p.save(img_bytes_io, format='PNG', optimize=True, compress_level=9)
            else:
                resized.save(img_bytes_io, format='PNG', optimize=True)
            archive.writestr(f"icons/{size}x{size}.png", img_bytes_io.getvalue())
            
        # 4. Generate manifest.json
        manifest = {
            "name": "Generated App",
            "icons": [
                {"src": "/android-icon-36x36.png", "sizes": "36x36", "type": "image/png", "density": "0.75"},
                {"src": "/android-icon-48x48.png", "sizes": "48x48", "type": "image/png", "density": "1.0"},
                {"src": "/android-icon-72x72.png", "sizes": "72x72", "type": "image/png", "density": "1.5"},
                {"src": "/android-icon-96x96.png", "sizes": "96x96", "type": "image/png", "density": "2.0"},
                {"src": "/android-icon-144x144.png", "sizes": "144x144", "type": "image/png", "density": "3.0"},
                {"src": "/android-icon-192x192.png", "sizes": "192x192", "type": "image/png", "density": "4.0"}
            ]
        }
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        
        # 5. Generate browserconfig.xml
        browserconfig = '''<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square70x70logo src="/ms-icon-70x70.png"/>
            <square150x150logo src="/ms-icon-150x150.png"/>
            <square310x310logo src="/ms-icon-310x310.png"/>
            <TileColor>#ffffff</TileColor>
        </tile>
    </msapplication>
</browserconfig>'''
        archive.writestr("browserconfig.xml", browserconfig)

    output.seek(0)
    return output


def _open_image(image_bytes):
    if not image_bytes:
        raise IconError("icons.error.empty")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(BytesIO(image_bytes))
            image.load()
    except (
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise IconError("icons.error.invalid")
    return image.convert("RGBA")


def _fit(image, size):
    return image.resize((size, size), Image.Resampling.LANCZOS)


def _square_png(image, size, keep_ratio):
    if not keep_ratio:
        return _fit(image, size)

    contained = ImageOps.contain(image, (size, size), method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    left = (size - contained.width) // 2
    top = (size - contained.height) // 2
    canvas.paste(contained, (left, top), contained)
    return canvas


def _png_bytes(image):
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _clean_sizes(sizes):
    cleaned = sorted({int(size) for size in sizes if int(size) in ICO_SIZES})
    if not cleaned:
        raise IconError("icons.error.size_required")
    return cleaned
