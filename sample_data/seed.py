"""Loads the sample products into the local SQLite DB so 'My Products' is not empty.
Run from the project root:  python sample_data/seed.py"""
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import app as shg  # noqa: E402  (creates the DB and table if missing)
from services import ai  # noqa: E402
from services.costing import calculate  # noqa: E402

with open(os.path.join(ROOT, "sample_data", "demo_products.json"), encoding="utf-8") as fh:
    samples = json.load(fh)

added = 0
with sqlite3.connect(shg.DB_PATH) as db:
    existing = {row[0] for row in db.execute("SELECT name FROM products")}
    for s in samples:
        inp = s["input"]
        if inp["name"] in existing:
            continue
        cost = calculate(inp)
        listing, _mode, _warn = ai.generate_listing(inp["name"], inp["category"], inp.get("notes", ""), cost)
        db.execute(
            "INSERT INTO products (name, category, units, total_cost, suggested_price, image_url, data_json)"
            " VALUES (?,?,?,?,?,?,?)",
            (inp["name"], inp["category"], cost["units"], cost["total"], cost["price"]["suggested"], None,
             json.dumps({"cost": cost, "listing": listing}, ensure_ascii=False)),
        )
        added += 1
print(f"Added {added} sample product(s) to {shg.DB_PATH}")
