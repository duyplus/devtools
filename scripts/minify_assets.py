from pathlib import Path

from rcssmin import cssmin
from rjsmin import jsmin


ROOT = Path(__file__).resolve().parents[1]
ASSETS = (
    (ROOT / "app/static/css/app.css", cssmin),
    (ROOT / "app/static/js/app.js", jsmin),
)

def minified_path(path):
    return path.with_name(f"{path.stem}.min{path.suffix}")

def main():
    for path, minify in ASSETS:
        source = path.read_text(encoding="utf-8")
        output = minify(source)
        target = minified_path(path)
        target.write_text(output, encoding="utf-8")
        print(f"{path.relative_to(ROOT)} -> {target.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
