# Test Cases

Automated tests: `python -m unittest discover tests` (26 tests). Sample inputs live in
[`sample_data/demo_products.json`](../sample_data/demo_products.json).

## A. Costing logic (`tests/test_costing.py`)
| ID | Case | Input | Expected |
|---|---|---|---|
| TC01 | Demo totals | Mango pickle, 10 units, 30% | Total ₹455, per unit ₹45.50, prices 55 / 60 / 70 |
| TC02 | Price order | Demo | minimum ≤ suggested ≤ maximum; suggested > cost per unit |
| TC03 | Breakdown | Demo | 4 categories; percentages sum to about 100 |
| TC04 | Rounding | 7.2, 19.01, 20, 20.01, 145.25 | 8, 20, 20, 25, 150 |
| TC05 | Default profit | No `margin` | Margin = 30 |
| TC06 | Margin floor | Profit 10% | Minimum price still above cost |
| TC07 | One unit | units = 1, packaging 10 | per unit ₹10 |
| TC08 | Unnamed ingredient | name empty, cost 50 | Kept as "-", total 50 |
| TC09 | No costs | units only | Error |
| TC10 | Negative cost | packaging = -3 | Error |
| TC11 | Zero units | units = 0 | Error |
| TC12 | Non-numeric | packaging = "abc" | Error |
| TC13 | Explanations | Demo | Tamil and English text contain the total |

## B. Sample data (`tests/test_samples.py`)
| ID | Case | Expected |
|---|---|---|
| TC20 | Sample file has at least 5 products | Pass |
| TC21 | Every sample matches expected total, per unit, min / suggested / max | Pass (see table in `sample_data/README.md`) |
| TC22 | Every sample name is in Tamil script | Pass |

## C. API (`tests/test_api.py`)
| ID | Case | Expected |
|---|---|---|
| TC30 | GET `/`, `/calculator`, `/products` | 200 |
| TC31 | POST `/api/generate` with demo, no key | 200, `ai_mode` = offline, suggested price 60, Tamil title kept |
| TC32 | Generate with blank name | 400 |
| TC33 | Generate with no costs or negative cost | 400 |
| TC34 | Generate with PNG photo | 200, `image_url` under `/static/uploads/`, file exists |
| TC35 | Generate with `.txt` photo | 400 |
| TC36 | Save, list, delete round trip | Appears in list, then gone after delete |
| TC37 | Save with missing fields | 400 |
| TC38 | Save with external `image_url` | Stored as null |
| TC39 | Translate offline; translate empty body | Offline mode with "mango" in title; 400 for empty |

## D. Manual checks
| ID | Case | Steps | Expected |
|---|---|---|---|
| M01 | Language toggle | Click EN, then தமிழ் | All labels switch; choice remembered after reload |
| M02 | Demo fill | Calculator → "மாதிரித் தரவை நிரப்பு" | Form fills; live total shows ₹455 |
| M03 | Tamil rendering | Open home page | Tamil text clear, no boxes or broken letters |
| M04 | Chart | Generate demo | Donut chart with 4 coloured legend rows |
| M05 | Photo | Upload JPG, generate | Photo shown beside the listing |
| M06 | Edit and translate | Edit Tamil text, click translate | English fields update; toast shown |
| M07 | Save and view | Click save, open My Products | Card with price, photo and description |
| M08 | Delete | Click delete, confirm | Card removed |
| M09 | Print | Click print | Print preview shows listing only, without form or header |
| M10 | Mobile | Open on phone width (about 380 px) | No sideways scrolling; buttons easy to tap |
| M11 | AI mode | Add API key, restart, generate | Badge shows "AI உதவியுடன்"; richer Tamil/English text |
| M12 | AI failure | Use an invalid key | Warning shown; offline listing still returned |
