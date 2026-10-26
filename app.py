import json
import os
import sqlite3
import uuid

from dotenv import load_dotenv
from flask import Flask, g, jsonify, render_template, request

load_dotenv()

from services import ai  # noqa: E402  (after load_dotenv)
from services.costing import calculate  # noqa: E402

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only")
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024  # 6 MB uploads

os.makedirs(app.instance_path, exist_ok=True)
DB_PATH = os.path.join(app.instance_path, "shg.db")
UPLOAD_DIR = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    units INTEGER,
    total_cost REAL,
    suggested_price REAL,
    image_url TEXT,
    data_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


with sqlite3.connect(DB_PATH) as _db:
    _db.executescript(SCHEMA)


# ---------- pages ----------
@app.route("/")
def home():
    return render_template("index.html", page="home")


@app.route("/calculator")
def calculator():
    return render_template("calculator.html", page="calc")


@app.route("/products")
def products_page():
    return render_template("products.html", page="products")


# ---------- API ----------
@app.errorhandler(413)
def too_large(_e):
    return jsonify(error="Photo is too large (max 6 MB)"), 413


@app.post("/api/generate")
def api_generate():
    try:
        payload = json.loads(request.form.get("data", "{}"))
        cost = calculate(payload)
    except (ValueError, json.JSONDecodeError) as exc:
        return jsonify(error=str(exc)), 400

    name = str(payload.get("name", "")).strip()[:120]
    if not name:
        return jsonify(error="Please enter the product name"), 400
    notes = str(payload.get("notes", "")).strip()[:1500]
    category = str(payload.get("category", "other"))[:30]

    image_bytes = media_type = image_url = None
    photo = request.files.get("photo")
    if photo and photo.filename:
        ext = ALLOWED.get(photo.mimetype)
        if not ext:
            return jsonify(error="Photo must be JPG, PNG or WEBP"), 400
        image_bytes, media_type = photo.read(), photo.mimetype
        fname = f"{uuid.uuid4().hex}.{ext}"
        with open(os.path.join(UPLOAD_DIR, fname), "wb") as fh:
            fh.write(image_bytes)
        image_url = f"/static/uploads/{fname}"

    listing, mode, warning = ai.generate_listing(name, category, notes, cost, image_bytes, media_type)
    return jsonify(cost=cost, listing=listing, image_url=image_url, ai_mode=mode, warning=warning)


@app.post("/api/translate")
def api_translate():
    body = request.get_json(silent=True) or {}
    title, desc = str(body.get("title", ""))[:200], str(body.get("description", ""))[:3000]
    if not (title or desc):
        return jsonify(error="Nothing to translate"), 400
    t_en, d_en, mode = ai.translate_listing(title, desc)
    return jsonify(title=t_en, description=d_en, mode=mode)


@app.post("/api/save")
def api_save():
    b = request.get_json(silent=True) or {}
    if not b.get("name") or "cost" not in b or "listing" not in b:
        return jsonify(error="Incomplete data"), 400
    image_url = b.get("image_url") or None
    if image_url and not str(image_url).startswith("/static/uploads/"):
        image_url = None
    db = get_db()
    cur = db.execute(
        "INSERT INTO products (name, category, units, total_cost, suggested_price, image_url, data_json)"
        " VALUES (?,?,?,?,?,?,?)",
        (
            str(b["name"])[:120], str(b.get("category", ""))[:30],
            b["cost"].get("units"), b["cost"].get("total"),
            b["cost"].get("price", {}).get("suggested"), image_url,
            json.dumps({"cost": b["cost"], "listing": b["listing"]}, ensure_ascii=False),
        ),
    )
    db.commit()
    return jsonify(id=cur.lastrowid)


@app.get("/api/products")
def api_products():
    rows = get_db().execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    out = []
    for r in rows:
        d = json.loads(r["data_json"])
        out.append({
            "id": r["id"], "name": r["name"], "category": r["category"],
            "image_url": r["image_url"], "created_at": r["created_at"],
            "cost": d["cost"], "listing": d["listing"],
        })
    return jsonify(out)


@app.delete("/api/products/<int:pid>")
def api_delete(pid):
    row = get_db().execute("SELECT image_url FROM products WHERE id=?", (pid,)).fetchone()
    if row and row["image_url"]:
        path = os.path.join(UPLOAD_DIR, os.path.basename(row["image_url"]))
        if os.path.isfile(path):
            os.remove(path)
    get_db().execute("DELETE FROM products WHERE id=?", (pid,))
    get_db().commit()
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
