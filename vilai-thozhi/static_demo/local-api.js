/* Static demo backend for GitHub Pages.
   Replaces the Flask /api/* routes with in-browser logic + localStorage.
   Offline mode only (no AI): template listings and a small Tamil glossary. */
(function () {
  "use strict";
  const realFetch = window.fetch.bind(window);
  const KEY = "vilai_products_v1";
  const TAMIL = /[\u0B80-\u0BFF]/;

  const LABELS = {
    ingredients: { ta: "மூலப்பொருட்கள்", en: "Ingredients" },
    packaging: { ta: "பேக்கிங்", en: "Packaging" },
    labour: { ta: "உழைப்பு", en: "Labour" },
    other: { ta: "மற்ற செலவுகள்", en: "Other costs" }
  };
  const GLOSSARY = {
    "மாங்காய்": "mango", "எலுமிச்சை": "lemon", "ஊறுகாய்": "pickle", "முறுக்கு": "murukku",
    "அதிரசம்": "adhirasam", "சோப்பு": "soap", "மசாலா": "masala", "பொடி": "powder",
    "கூடை": "basket", "பை": "bag", "தேங்காய்": "coconut", "நல்லெண்ணெய்": "sesame oil",
    "எண்ணெய்": "oil", "நெய்": "ghee", "வடகம்": "vadagam", "அப்பளம்": "appalam",
    "துணி": "cloth", "மெழுகுவர்த்தி": "candle", "சேலை": "saree", "சிறுதானிய": "millet",
    "கடலை": "groundnut", "மிட்டாய்": "sweet", "இஞ்சி": "ginger", "தேன்": "honey",
    "மஞ்சள்": "turmeric", "மிளகாய்": "chilli", "கைவினை": "handmade", "வீட்டில்": "homemade"
  };

  const g = n => String(parseFloat(Number(n).toPrecision(6)));
  const r2 = n => Math.round(n * 100) / 100;
  const json = (body, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

  function num(v, field) {
    const n = parseFloat(v || 0);
    if (!isFinite(n) || n < 0) throw new Error("Invalid value in " + field);
    return n;
  }
  function roundPrice(v) { return v < 20 ? Math.ceil(v) : 5 * Math.ceil(v / 5); }

  function calculate(d) {
    const ingredients = [];
    (d.ingredients || []).forEach(row => {
      const name = String(row.name || "").trim().slice(0, 60);
      const cost = num(row.cost, "ingredient cost");
      if (name || cost) ingredients.push({ name: name || "-", cost: r2(cost) });
    });
    const amounts = {
      ingredients: ingredients.reduce((s, i) => s + i.cost, 0),
      packaging: num(d.packaging, "packaging"),
      labour: num(d.labour, "labour"),
      other: num(d.other, "other costs")
    };
    const total = Object.values(amounts).reduce((a, b) => a + b, 0);
    if (total <= 0) throw new Error("Please enter at least one cost");
    const units = Math.floor(num(d.units, "units"));
    if (units < 1) throw new Error("Units per batch must be at least 1");
    let margin = (d.margin === null || d.margin === undefined || d.margin === "") ? 30 : num(d.margin, "profit %");
    margin = Math.min(margin, 300);
    const perUnit = total / units;
    const low = roundPrice(perUnit * (1 + Math.max(5, margin - 15) / 100));
    const suggested = roundPrice(perUnit * (1 + margin / 100));
    const high = roundPrice(perUnit * (1 + (margin + 20) / 100));
    const profit = suggested - perUnit;
    return {
      ingredients, units, total: r2(total), per_unit: r2(perUnit), margin,
      price: { low, suggested, high },
      profit_per_unit: r2(profit), profit_percent: Math.round(profit / perUnit * 1000) / 10,
      breakdown: Object.keys(amounts).map(k => ({
        key: k, label_ta: LABELS[k].ta, label_en: LABELS[k].en,
        amount: r2(amounts[k]), percent: Math.round(amounts[k] / total * 1000) / 10
      }))
    };
  }

  function explain(r) {
    const top = r.breakdown.reduce((a, b) => (b.amount > a.amount ? b : a));
    const p = r.price;
    return {
      en: `Making ${r.units} units costs Rs.${g(r.total)}, which is Rs.${g(r.per_unit)} per unit. ` +
          `The biggest cost is ${top.label_en.toLowerCase()} (${g(top.percent)}%). ` +
          `Selling at Rs.${p.suggested} gives about Rs.${g(r.profit_per_unit)} profit per unit. ` +
          `Try not to sell below Rs.${p.low}, because small unexpected costs can remove your profit.`,
      ta: `${r.units} எண்ணிக்கை தயாரிக்க மொத்த செலவு ₹${g(r.total)}; ஒரு எண்ணிக்கைக்கு ₹${g(r.per_unit)}. ` +
          `அதிகச் செலவு: ${top.label_ta} (${g(top.percent)}%). ` +
          `₹${p.suggested} விலைக்கு விற்றால் ஒரு எண்ணிக்கைக்குச் சுமார் ₹${g(r.profit_per_unit)} லாபம் கிடைக்கும். ` +
          `₹${p.low}-க்குக் கீழ் விற்க வேண்டாம்; எதிர்பாராத சிறு செலவுகளால் லாபம் போய்விடும்.`
    };
  }

  function gloss(text) {
    Object.keys(GLOSSARY).sort((a, b) => b.length - a.length)
      .forEach(ta => { text = text.split(ta).join(GLOSSARY[ta]); });
    return text.trim();
  }

  function offlineListing(name, notes, cost) {
    const titleEn = gloss(name) || name;
    const exp = explain(cost);
    const price = cost.price.suggested;
    const ta = `${name} — எங்கள் சுய உதவிக்குழு பெண்களால் தூய்மையாகவும் அன்புடனும் தயாரிக்கப்பட்டது. ` +
      `${notes}\n\nவிலை: ₹${price} (ஒரு எண்ணிக்கைக்கு). ஆர்டர் செய்ய எங்களைத் தொடர்பு கொள்ளுங்கள்.`;
    const notesEn = gloss(notes);
    let en = `${titleEn} - made with care by the women of our self-help group, using quality ingredients.`;
    if (notesEn && !TAMIL.test(notesEn)) en += " " + notesEn;
    en += `\n\nPrice: Rs.${price} per unit. Contact us to order.`;
    return {
      title_ta: name, title_en: titleEn, description_ta: ta.trim(), description_en: en,
      tags: ["homemade", "women-made", "self-help group"],
      explanation_ta: exp.ta, explanation_en: exp.en
    };
  }

  function readPhoto(file) {
    return new Promise((resolve, reject) => {
      if (!/^image\/(jpeg|png|webp)$/.test(file.type)) return reject(new Error("Photo must be JPG, PNG or WEBP"));
      if (file.size > 6 * 1024 * 1024) return reject(new Error("Photo is too large (max 6 MB)"));
      const fr = new FileReader();
      fr.onerror = () => reject(new Error("Could not read the photo"));
      fr.onload = () => {
        const img = new Image();
        img.onerror = () => reject(new Error("Could not read the photo"));
        img.onload = () => {
          const s = Math.min(1, 480 / Math.max(img.width, img.height));
          const c = document.createElement("canvas");
          c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
          c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
          resolve(c.toDataURL("image/jpeg", 0.8));
        };
        img.src = fr.result;
      };
      fr.readAsDataURL(file);
    });
  }

  const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { return []; } };
  const store = items => localStorage.setItem(KEY, JSON.stringify(items));

  window.fetch = async function (url, opts) {
    opts = opts || {};
    const u = String(url);
    if (!u.startsWith("/api/")) return realFetch(url, opts);
    const method = (opts.method || "GET").toUpperCase();
    try {
      if (u === "/api/generate" && method === "POST") {
        const payload = JSON.parse(opts.body.get("data") || "{}");
        const cost = calculate(payload);
        const name = String(payload.name || "").trim().slice(0, 120);
        if (!name) return json({ error: "Please enter the product name" }, 400);
        const notes = String(payload.notes || "").trim().slice(0, 1500);
        const photo = opts.body.get("photo");
        const image_url = photo && photo.size ? await readPhoto(photo) : null;
        return json({ cost, listing: offlineListing(name, notes, cost), image_url, ai_mode: "offline", warning: null });
      }
      if (u === "/api/translate" && method === "POST") {
        const b = JSON.parse(opts.body || "{}");
        return json({ title: gloss(b.title || ""), description: gloss(b.description || ""), mode: "offline" });
      }
      if (u === "/api/save" && method === "POST") {
        const b = JSON.parse(opts.body || "{}");
        if (!b.name || !b.cost || !b.listing) return json({ error: "Incomplete data" }, 400);
        const items = load();
        const id = items.reduce((m, i) => Math.max(m, i.id), 0) + 1;
        items.push({ id, name: b.name, category: b.category, image_url: b.image_url || null,
                     created_at: new Date().toISOString(), cost: b.cost, listing: b.listing });
        try { store(items); } catch (e) { return json({ error: "Browser storage is full. Delete some saved products." }, 500); }
        return json({ id });
      }
      if (u === "/api/products" && method === "GET") return json(load().sort((a, b) => b.id - a.id));
      const del = u.match(/^\/api\/products\/(\d+)$/);
      if (del && method === "DELETE") {
        store(load().filter(i => i.id !== Number(del[1])));
        return json({ ok: true });
      }
      return json({ error: "Not found" }, 404);
    } catch (err) {
      return json({ error: err.message }, 400);
    }
  };
})();
