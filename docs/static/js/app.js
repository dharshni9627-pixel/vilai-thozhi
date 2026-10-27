(function () {
  "use strict";

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const rupee = n => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 });
  const COLORS = { ingredients: "#C2185B", packaging: "#FF9F1C", labour: "#00A896", other: "#3D2C8D" };

  let toastTimer;
  function toast(msg, kind) {
    const el = $("#toast");
    el.textContent = msg;
    el.className = "toast show" + (kind === "err" ? " err" : "");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (el.className = "toast"), 2800);
  }

  async function api(url, options) {
    const res = await fetch(url, options);
    let json = {};
    try { json = await res.json(); } catch (e) {}
    if (!res.ok) throw new Error(json.error || t("err_generic"));
    return json;
  }

  /* ================= Calculator ================= */
  function initCalculator() {
    const form = $("#calc-form");
    const rowsEl = $("#ing-rows");
    let state = null;

    function addRow(name = "", cost = "") {
      const row = document.createElement("div");
      row.className = "ing-row";
      row.innerHTML =
        `<input type="text" class="ing-name" maxlength="60" placeholder="${esc(t("ph_item"))}" value="${esc(name)}">` +
        `<input type="number" class="ing-cost" min="0" step="0.01" inputmode="decimal" placeholder="₹" value="${esc(cost)}">` +
        `<button type="button" class="icon-btn rm" aria-label="remove">✕</button>`;
      rowsEl.appendChild(row);
    }

    const num = sel => parseFloat($(sel).value) || 0;

    function collect() {
      return {
        name: $("#name").value.trim(),
        category: $("#category").value,
        units: parseInt($("#units").value, 10) || 0,
        margin: num("#margin"),
        ingredients: $$(".ing-row").map(r => ({
          name: $(".ing-name", r).value.trim(),
          cost: parseFloat($(".ing-cost", r).value) || 0
        })).filter(r => r.name || r.cost),
        packaging: num("#packaging"),
        labour: num("#labour"),
        other: num("#other"),
        notes: $("#notes").value.trim()
      };
    }

    function updateLive() {
      const d = collect();
      const total = d.ingredients.reduce((s, i) => s + i.cost, 0) + d.packaging + d.labour + d.other;
      $("#live-total").textContent = rupee(total);
    }

    function fillDemo() {
      $("#name").value = "மாங்காய் ஊறுகாய்";
      $("#category").value = "pickle";
      $("#units").value = 10;
      $("#margin").value = 30;
      $("#packaging").value = 40;
      $("#labour").value = 150;
      $("#other").value = 30;
      $("#notes").value = "வீட்டிலேயே அரைத்த மசாலா, நல்லெண்ணெய் சேர்த்த பாரம்பரிய சுவை. 3 மாதம் வரை கெடாது.";
      rowsEl.innerHTML = "";
      [["மாங்காய்", 120], ["நல்லெண்ணெய்", 60], ["மிளகாய்த்தூள் & மசாலா", 45], ["உப்பு", 10]].forEach(([n, c]) => addRow(n, c));
      updateLive();
    }

    async function onSubmit(e) {
      e.preventDefault();
      const data = collect();
      if (!data.name) return toast(t("err_name"), "err");
      const fd = new FormData();
      fd.append("data", JSON.stringify(data));
      const file = $("#photo").files[0];
      if (file) fd.append("photo", file);

      const btn = $("#btn-generate");
      btn.disabled = true;
      btn.textContent = "⏳ " + t("working");
      try {
        const json = await api("/api/generate", { method: "POST", body: fd });
        state = { ...json, name: data.name, category: data.category };
        renderResults();
        $("#results").scrollIntoView({ behavior: "smooth", block: "start" });
      } catch (err) {
        toast(err.message, "err");
      } finally {
        btn.disabled = false;
        btn.textContent = t("btn_generate");
      }
    }

    function donut(parts) {
      let acc = 0;
      const stops = parts.map(p => {
        const start = acc; acc += p.percent;
        return `${COLORS[p.key]} ${start}% ${Math.min(acc, 100)}%`;
      });
      return `conic-gradient(${stops.join(",")})`;
    }

    function renderResults() {
      const { cost, listing, image_url: img, ai_mode: mode, warning } = state;
      const lang = getLang();
      const parts = cost.breakdown.filter(b => b.amount > 0);
      const explanation = listing["explanation_" + lang] || listing.explanation_en || "";
      const el = $("#results");
      el.hidden = false;
      el.innerHTML = `
        <div class="result-head">
          <h2>${t("res_title")}</h2>
          <span class="badge ${mode === "llm" ? "badge-ai" : "badge-off"}">${mode === "llm" ? "✨ " + t("mode_ai") : "🧪 " + t("mode_offline")}</span>
        </div>
        <div class="stats">
          <div class="stat s1"><span>${t("r_total")}</span><b>${rupee(cost.total)}</b></div>
          <div class="stat s2"><span>${t("r_unit")}</span><b>${rupee(cost.per_unit)}</b></div>
          <div class="stat s3"><span>${t("r_min")}</span><b>${rupee(cost.price.low)}</b></div>
          <div class="stat s4"><span>${t("r_sug")}</span><b>${rupee(cost.price.suggested)}</b></div>
          <div class="stat s5"><span>${t("r_max")}</span><b>${rupee(cost.price.high)}</b></div>
        </div>
        <div class="grid-2">
          <section class="card">
            <h3>${t("r_break")}</h3>
            <div class="donut-wrap">
              <div class="donut" style="background:${donut(parts)}">
                <div class="donut-hole"><b>${rupee(cost.per_unit)}</b><small>${t("per_unit")}</small></div>
              </div>
              <ul class="legend">
                ${parts.map(p => `<li><span class="sw" style="background:${COLORS[p.key]}"></span>${t("c_" + p.key)} (${p.percent}%)<span class="amt">${rupee(p.amount)}</span></li>`).join("")}
              </ul>
            </div>
          </section>
          <section class="card">
            <h3>${t("r_explain")}</h3>
            <p class="explain">${esc(explanation)}</p>
            ${warning ? `<p class="warn">⚠️ ${esc(warning)}</p>` : ""}
          </section>
        </div>
        <section class="card">
          <h3>${t("r_listing")}</h3>
          <div class="listing-top">
            ${img ? `<img class="listing-img" src="${esc(img)}" alt="">` : `<div class="listing-img placeholder">🛍️</div>`}
            <div class="lang-cols">
              <div class="lang-col">
                <h4>${t("r_ta")}</h4>
                <label>${t("r_title")}</label><input id="title-ta" value="${esc(listing.title_ta)}">
                <label>${t("r_desc")}</label><textarea id="desc-ta" rows="7">${esc(listing.description_ta)}</textarea>
              </div>
              <div class="lang-col">
                <h4>${t("r_en")}</h4>
                <label>${t("r_title")}</label><input id="title-en" value="${esc(listing.title_en)}">
                <label>${t("r_desc")}</label><textarea id="desc-en" rows="7">${esc(listing.description_en)}</textarea>
              </div>
            </div>
          </div>
          <div class="tags">${(listing.tags || []).map(x => `<span class="tag">#${esc(x)}</span>`).join("")}</div>
          <div class="listing-actions">
            <button class="btn btn-soft" id="btn-translate">🌐 ${t("btn_translate")}</button>
            <button class="btn btn-ghost-dark" id="btn-copy">📋 ${t("btn_copy")}</button>
            <button class="btn btn-ghost-dark" id="btn-print">🖨️ ${t("btn_print")}</button>
            <button class="btn btn-primary" id="btn-save">💾 ${t("btn_save")}</button>
          </div>
        </section>`;

      [["title-ta", "title_ta"], ["desc-ta", "description_ta"], ["title-en", "title_en"], ["desc-en", "description_en"]]
        .forEach(([id, key]) => $("#" + id).addEventListener("input", e => { state.listing[key] = e.target.value; }));

      $("#btn-translate").addEventListener("click", translate);
      $("#btn-copy").addEventListener("click", copyListing);
      $("#btn-print").addEventListener("click", () => window.print());
      $("#btn-save").addEventListener("click", save);
    }

    async function translate(e) {
      const btn = e.currentTarget; btn.disabled = true;
      try {
        const j = await api("/api/translate", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: state.listing.title_ta, description: state.listing.description_ta })
        });
        state.listing.title_en = j.title;
        state.listing.description_en = j.description;
        renderResults();
        toast(t("translated"));
      } catch (err) { toast(err.message, "err"); btn.disabled = false; }
    }

    async function copyListing() {
      const l = state.listing;
      const text = `${l.title_ta}\n${l.description_ta}\n\n${l.title_en}\n${l.description_en}`;
      try { await navigator.clipboard.writeText(text); toast(t("copied")); }
      catch (e) {
        const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta);
        ta.select(); document.execCommand("copy"); ta.remove(); toast(t("copied"));
      }
    }

    async function save(e) {
      const btn = e.currentTarget; btn.disabled = true;
      try {
        await api("/api/save", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: state.name, category: state.category, cost: state.cost, listing: state.listing, image_url: state.image_url })
        });
        toast(t("saved"));
      } catch (err) { toast(err.message, "err"); }
      btn.disabled = false;
    }

    addRow(); addRow(); addRow();
    rowsEl.addEventListener("click", e => {
      const rm = e.target.closest(".rm");
      if (rm && $$(".ing-row").length > 1) { rm.parentElement.remove(); updateLive(); }
    });
    $("#btn-add").addEventListener("click", () => addRow());
    $("#btn-demo").addEventListener("click", fillDemo);
    form.addEventListener("input", updateLive);
    form.addEventListener("submit", onSubmit);
    document.addEventListener("langchange", () => {
      $$(".ing-name").forEach(i => (i.placeholder = t("ph_item")));
      if (state) renderResults();
    });
    if (location.hash === "#demo") fillDemo();
    updateLive();
  }

  /* ================= Saved products ================= */
  function initProducts() {
    const grid = $("#products-grid");
    let items = [];

    function render() {
      if (!items.length) {
        grid.innerHTML = `<div class="empty"><div class="big">🌸</div><p>${t("prod_empty")}</p><a class="btn btn-primary" href="calculator.html">${t("nav_calc")}</a></div>`;
        return;
      }
      const lang = getLang();
      grid.innerHTML = items.map(p => {
        const l = p.listing, c = p.cost;
        const title = lang === "ta" ? l.title_ta : (l.title_en || l.title_ta);
        const desc = lang === "ta" ? l.description_ta : (l.description_en || l.description_ta);
        return `<article class="p-card">
          ${p.image_url ? `<img src="${esc(p.image_url)}" alt="">` : `<div class="ph">🛍️</div>`}
          <div class="p-body">
            <span class="p-cat">${t("cat_" + p.category)}</span>
            <h3>${esc(title)}</h3>
            <div class="p-prices"><span class="big">${rupee(c.price.suggested)}</span><small>${rupee(c.price.low)} – ${rupee(c.price.high)} · ${t("r_unit")}: ${rupee(c.per_unit)}</small></div>
            <p class="p-desc">${esc(desc)}</p>
            <div class="p-actions">
              <button class="btn btn-ghost-dark btn-sm" onclick="window.print()">🖨️ ${t("btn_print")}</button>
              <button class="btn btn-danger btn-sm" data-del="${p.id}">🗑️ ${t("btn_delete")}</button>
            </div>
          </div>
        </article>`;
      }).join("");
    }

    grid.addEventListener("click", async e => {
      const b = e.target.closest("[data-del]");
      if (!b || !confirm(t("confirm_delete"))) return;
      try {
        await api("/api/products/" + b.dataset.del, { method: "DELETE" });
        items = items.filter(i => String(i.id) !== b.dataset.del);
        render(); toast(t("deleted"));
      } catch (err) { toast(err.message, "err"); }
    });

    document.addEventListener("langchange", render);
    api("/api/products").then(j => { items = j; render(); }).catch(err => toast(err.message, "err"));
  }

  if ($("#calc-form")) initCalculator();
  if ($("#products-grid")) initProducts();
  applyLang();
})();
