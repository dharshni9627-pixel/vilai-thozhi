"""Pure costing and pricing logic (no Flask) so it is easy to test."""
import math

LABELS = {
    "ingredients": {"ta": "மூலப்பொருட்கள்", "en": "Ingredients"},
    "packaging": {"ta": "பேக்கிங்", "en": "Packaging"},
    "labour": {"ta": "உழைப்பு", "en": "Labour"},
    "other": {"ta": "மற்ற செலவுகள்", "en": "Other costs"},
}


def _num(value, field):
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid number in {field}")
    if math.isnan(n) or math.isinf(n) or n < 0:
        raise ValueError(f"{field} must be zero or more")
    return n


def round_price(value):
    """Shop-friendly prices: whole rupees under 20, multiples of 5 above."""
    if value < 20:
        return int(math.ceil(value))
    return int(5 * math.ceil(value / 5))


def calculate(data):
    ingredients = []
    for row in data.get("ingredients", []) or []:
        name = str(row.get("name", "")).strip()[:60]
        cost = _num(row.get("cost"), "ingredient cost")
        if name or cost:
            ingredients.append({"name": name or "-", "cost": round(cost, 2)})

    amounts = {
        "ingredients": sum(i["cost"] for i in ingredients),
        "packaging": _num(data.get("packaging"), "packaging"),
        "labour": _num(data.get("labour"), "labour"),
        "other": _num(data.get("other"), "other costs"),
    }
    total = sum(amounts.values())
    if total <= 0:
        raise ValueError("Please enter at least one cost")

    units = int(_num(data.get("units"), "units"))
    if units < 1:
        raise ValueError("Units per batch must be at least 1")

    margin = _num(data.get("margin") if data.get("margin") not in (None, "") else 30, "profit %")
    margin = min(margin, 300)
    low_margin = max(5, margin - 15)
    high_margin = margin + 20

    per_unit = total / units
    low = round_price(per_unit * (1 + low_margin / 100))
    suggested = round_price(per_unit * (1 + margin / 100))
    high = round_price(per_unit * (1 + high_margin / 100))
    profit = suggested - per_unit

    breakdown = [
        {
            "key": k,
            "label_ta": LABELS[k]["ta"],
            "label_en": LABELS[k]["en"],
            "amount": round(v, 2),
            "percent": round(v / total * 100, 1),
        }
        for k, v in amounts.items()
    ]

    return {
        "ingredients": ingredients,
        "units": units,
        "total": round(total, 2),
        "per_unit": round(per_unit, 2),
        "margin": margin,
        "price": {"low": low, "suggested": suggested, "high": high},
        "profit_per_unit": round(profit, 2),
        "profit_percent": round(profit / per_unit * 100, 1),
        "breakdown": breakdown,
    }


def explain(r):
    """Plain-language explanation in Tamil and English (works offline)."""
    top = max(r["breakdown"], key=lambda b: b["amount"])
    p = r["price"]
    en = (
        f"Making {r['units']} units costs Rs.{r['total']:g}, which is Rs.{r['per_unit']:g} per unit. "
        f"The biggest cost is {top['label_en'].lower()} ({top['percent']:g}%). "
        f"Selling at Rs.{p['suggested']} gives about Rs.{r['profit_per_unit']:g} profit per unit. "
        f"Try not to sell below Rs.{p['low']}, because small unexpected costs can remove your profit."
    )
    ta = (
        f"{r['units']} எண்ணிக்கை தயாரிக்க மொத்த செலவு ₹{r['total']:g}; ஒரு எண்ணிக்கைக்கு ₹{r['per_unit']:g}. "
        f"அதிகச் செலவு: {top['label_ta']} ({top['percent']:g}%). "
        f"₹{p['suggested']} விலைக்கு விற்றால் ஒரு எண்ணிக்கைக்குச் சுமார் ₹{r['profit_per_unit']:g} லாபம் கிடைக்கும். "
        f"₹{p['low']}-க்குக் கீழ் விற்க வேண்டாம்; எதிர்பாராத சிறு செலவுகளால் லாபம் போய்விடும்."
    )
    return {"ta": ta, "en": en}
