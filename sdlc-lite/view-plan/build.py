"""Build index.html from template.html by inlining images from crops/.

Run from the page's folder: python3 build.py
Writes index.html (the page to publish) and preview.html (the same page in a
full document, for looking at it through a local server). Stops if a
{{img:<name>}} has no file in crops/ or a [[...]] placeholder is left.
"""
import base64
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
SKELETON = (
    '<!doctype html><html><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
    "<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>"
    "</head><body>@@PAGE@@</body></html>"
)


def image(match):
    name = match.group(1)
    for ext, mime in MIME.items():
        path = ROOT / "crops" / (name + ext)
        if path.exists():
            return "data:%s;base64,%s" % (mime, base64.b64encode(path.read_bytes()).decode())
    raise SystemExit("missing image: crops/%s.(jpg|png|webp)" % name)


def main():
    html = (ROOT / "template.html").read_text(encoding="utf-8")
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    left = sorted(set(re.findall(r"\[\[[^\]]*\]\]", html)))
    if left:
        raise SystemExit("placeholders left: " + ", ".join(left[:8]))
    html = re.sub(r"\{\{img:([^}]*)\}\}", image, html)
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    (ROOT / "preview.html").write_text(SKELETON.replace("@@PAGE@@", html), encoding="utf-8")
    print("built index.html: %d bytes, %d drawings" % (len(html), html.count("<svg")))


if __name__ == "__main__":
    main()
