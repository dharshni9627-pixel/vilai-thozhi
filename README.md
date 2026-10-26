# விலைத் தோழி · VilaiThozhi

A **Tamil-first** web prototype that helps women's self-help group (SHG) members
estimate production cost, set a fair selling price and create product listings.

**Demo:** enter ingredient, packaging and labour costs → get a cost breakdown,
a suggested price range (min / suggested / max) and a Tamil + English product listing.

## Features
- Tamil / English interface toggle (Tamil by default)
- Cost breakdown with donut chart, cost per unit, profit-based price range
- Product listing from **photo + notes** (vision model, optional)
- Plain-language **cost explanation** in Tamil and English
- **Tamil → English** listing translation
- Save, print and delete listings (SQLite)
- Works fully **offline** with template text when no API key is set

## Tech stack
Flask · vanilla JavaScript · SQLite · optional Anthropic API (vision + language)

## Run locally
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # optionally add ANTHROPIC_API_KEY
flask --app app run --debug
```
Open http://127.0.0.1:5000

Run tests: `python -m unittest discover tests`

## Project structure
```
app.py                  Flask routes + SQLite
services/costing.py     Cost, price range, explanations (pure Python)
services/ai.py          Vision/LLM calls with offline fallback
templates/              base, home, calculator, products
static/css/style.css    Theme
static/js/i18n.js       Tamil/English strings
static/js/app.js        Calculator + saved products UI
static/img/             logo.svg, hero.svg
```

## API
| Method | Route | Purpose |
|---|---|---|
| POST | `/api/generate` | multipart: `data` (JSON) + optional `photo` → cost + listing |
| POST | `/api/translate` | Tamil title/description → English |
| POST | `/api/save` | Save a product |
| GET | `/api/products` | List saved products |
| DELETE | `/api/products/<id>` | Delete a product |

## Push to GitHub
```bash
git init
git add .
git commit -m "Initial prototype: VilaiThozhi"
git branch -M main
git remote add origin https://github.com/<your-username>/vilai-thozhi.git
git push -u origin main
```

## Notes / roadmap
- Prices use `cost per unit × (1 + profit %)`: minimum = profit − 15 points, maximum = profit + 20 points.
- Review AI-written text before publishing; the app never invents certifications or health claims.
- Ideas: voice input in Tamil, WhatsApp share, group-level accounts, GST/market-price comparison.
