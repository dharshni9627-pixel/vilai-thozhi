"""AI helpers. Uses the Anthropic API when ANTHROPIC_API_KEY is set,
otherwise falls back to simple offline templates so the demo always works."""
import base64
import json
import os
import re

from .costing import explain

TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")

GLOSSARY = {
    "மாங்காய்": "mango", "எலுமிச்சை": "lemon", "ஊறுகாய்": "pickle", "முறுக்கு": "murukku",
    "அதிரசம்": "adhirasam", "சோப்பு": "soap", "மசாலா": "masala", "பொடி": "powder",
    "கூடை": "basket", "பை": "bag", "தேங்காய்": "coconut", "நல்லெண்ணெய்": "sesame oil",
    "எண்ணெய்": "oil", "நெய்": "ghee", "வடகம்": "vadagam", "அப்பளம்": "appalam",
    "துணி": "cloth", "மெழுகுவர்த்தி": "candle", "சேலை": "saree", "சிறுதானிய": "millet",
    "கடலை": "groundnut", "மிட்டாய்": "sweet", "இஞ்சி": "ginger", "தேன்": "honey",
    "மஞ்சள்": "turmeric", "மிளகாய்": "chilli", "கைவினை": "handmade", "வீட்டில்": "homemade",
}


def llm_available():
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _gloss(text):
    for ta, en in sorted(GLOSSARY.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(ta, en)
    return text.strip()


def _parse_json(text):
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON in model reply")
    return json.loads(text[start : end + 1])


def _call_llm(content, max_tokens=1500):
    import anthropic  # imported lazily so the app runs without the package

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


def _offline_listing(name, notes, cost):
    title_en = _gloss(name) or name
    exp = explain(cost)
    price = cost["price"]["suggested"]
    ta = (
        f"{name} — எங்கள் சுய உதவிக்குழு பெண்களால் தூய்மையாகவும் அன்புடனும் தயாரிக்கப்பட்டது. "
        f"{notes}\n\nவிலை: ₹{price} (ஒரு எண்ணிக்கைக்கு). ஆர்டர் செய்ய எங்களைத் தொடர்பு கொள்ளுங்கள்."
    ).strip()
    notes_en = _gloss(notes)
    en = f"{title_en} - made with care by the women of our self-help group, using quality ingredients."
    if notes_en and not TAMIL_RE.search(notes_en):
        en += f" {notes_en}"
    en += f"\n\nPrice: Rs.{price} per unit. Contact us to order."
    return {
        "title_ta": name, "title_en": title_en,
        "description_ta": ta, "description_en": en,
        "tags": ["homemade", "women-made", "self-help group"],
        "explanation_ta": exp["ta"], "explanation_en": exp["en"],
    }


def generate_listing(name, category, notes, cost, image_bytes=None, media_type=None):
    """Returns (listing_dict, mode, warning). mode is 'llm' or 'offline'."""
    offline = _offline_listing(name, notes, cost)
    if not llm_available():
        return offline, "offline", None

    top = max(cost["breakdown"], key=lambda b: b["amount"])
    items = ", ".join(i["name"] for i in cost["ingredients"] if i["name"] != "-") or "not given"
    prompt = f"""You help women's self-help groups in Tamil Nadu sell homemade products.
Product name: {name}
Category: {category}
Ingredients listed: {items}
Maker's notes (may be Tamil): {notes or 'none'}
Costing: {cost['units']} units per batch, cost per unit Rs.{cost['per_unit']}, suggested price Rs.{cost['price']['suggested']} (range Rs.{cost['price']['low']}-{cost['price']['high']}), biggest cost: {top['label_en']} ({top['percent']}%).
{'A photo of the product is attached: mention only what is visible (colour, texture, packaging).' if image_bytes else ''}

Return ONLY a JSON object with keys:
title_ta, title_en, description_ta, description_en, tags (array of 3-6 short English words), explanation_ta, explanation_en.
Rules: use simple, friendly Tamil a village shopkeeper understands; each description 50-80 words; do not invent certifications, health claims or ingredients not given; do not put prices in the description; explanation is 2-3 short sentences on where the money goes and why this price range is suggested."""

    content = []
    if image_bytes:
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": media_type,
            "data": base64.b64encode(image_bytes).decode()}})
    content.append({"type": "text", "text": prompt})

    try:
        data = _parse_json(_call_llm(content))
        merged = {**offline, **{k: v for k, v in data.items() if v}}
        merged["tags"] = [str(t) for t in merged.get("tags", [])][:6]
        return merged, "llm", None
    except Exception as exc:  # network, key, parse errors -> keep the demo working
        return offline, "offline", f"AI unavailable, showing template text ({type(exc).__name__})"


def translate_listing(title_ta, description_ta):
    """Tamil -> English. Returns (title_en, description_en, mode)."""
    if llm_available():
        prompt = (
            "Translate this Tamil product listing into natural, warm English for an online shop. "
            "Keep meaning exact; do not add claims. Return ONLY JSON with keys title_en and description_en.\n\n"
            f"TITLE: {title_ta}\nDESCRIPTION: {description_ta}"
        )
        try:
            data = _parse_json(_call_llm(prompt, 1000))
            return data["title_en"], data["description_en"], "llm"
        except Exception:
            pass
    return _gloss(title_ta), _gloss(description_ta), "offline"
