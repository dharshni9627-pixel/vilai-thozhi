# Sample data

`demo_products.json` is a list of sample products. Each item has:

- `input` – exactly what the calculator sends to `/api/generate` (Tamil name, category, units, profit %, ingredients, packaging, labour, other costs, notes)
- `expected` – the totals and prices the app must produce

| ID | Product | Units | Total cost (₹) | Per unit (₹) | Min / Suggested / Max (₹) |
|---|---|---|---|---|---|
| S1 | மாங்காய் ஊறுகாய் (mango pickle) | 10 | 455 | 45.50 | 55 / 60 / 70 |
| S2 | எலுமிச்சை ஊறுகாய் (lemon pickle) | 12 | 545 | 45.42 | 55 / 60 / 70 |
| S3 | கை முறுக்கு (murukku) | 20 | 780 | 39.00 | 50 / 55 / 65 |
| S4 | பனை ஓலைக் கூடை (palm-leaf basket) | 8 | 830 | 103.75 | 130 / 150 / 170 |
| S5 | மூலிகை சோப்பு (herbal soap) | 30 | 800 | 26.67 | 35 / 40 / 45 |

## Use it
- **Automated check:** `python -m unittest tests.test_samples`
- **Fill the app with these products:** `python sample_data/seed.py` (skips ones already saved)
- **Try one by hand:** copy values from `demo_products.json` into the calculator form
