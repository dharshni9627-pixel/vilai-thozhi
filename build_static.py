"""Builds a static demo for GitHub Pages into ./docs (no Flask server needed).
Run:  python build_static.py   then push the docs/ folder."""
import os
import shutil

from app import app

OUT = "docs"
PAGES = {"/": "index.html", "/calculator": "calculator.html", "/products": "products.html"}

shutil.rmtree(OUT, ignore_errors=True)
shutil.copytree("static", f"{OUT}/static", ignore=shutil.ignore_patterns("uploads"))
shutil.copy("static_demo/local-api.js", f"{OUT}/static/js/local-api.js")

# Links inside app.js that must work without a server
js_path = f"{OUT}/static/js/app.js"
with open(js_path, encoding="utf-8") as fh:
    js = fh.read().replace('href="/calculator"', 'href="calculator.html"')
with open(js_path, "w", encoding="utf-8") as fh:
    fh.write(js)

client = app.test_client()
for route, fname in PAGES.items():
    html = client.get(route).get_data(as_text=True)
    html = html.replace('href="/static/', 'href="static/').replace('src="/static/', 'src="static/')
    html = html.replace('href="/calculator#demo"', 'href="calculator.html#demo"')
    for r, f in PAGES.items():
        html = html.replace(f'href="{r}"', f'href="{f}"')
    html = html.replace(
        '<script src="static/js/i18n.js">',
        '<script src="static/js/local-api.js"></script>\n  <script src="static/js/i18n.js">',
    )
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as fh:
        fh.write(html)

open(os.path.join(OUT, ".nojekyll"), "w").close()
print("Static demo written to ./docs")
