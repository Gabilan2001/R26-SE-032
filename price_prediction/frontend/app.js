/**
 * Tomato Price Advisor — farmer-friendly UI (no technical details shown).
 */

function $(id) {
  return document.getElementById(id);
}

function escapeHtml(str) {
  if (str == null) return "";
  const d = document.createElement("div");
  d.textContent = String(str);
  return d.innerHTML;
}

let toastTimer;

function showToast(message, isError) {
  const el = $("toast");
  if (!el) return;
  el.textContent = message;
  el.hidden = false;
  el.classList.toggle("error", !!isError);
  el.classList.add("is-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.classList.remove("is-visible");
    setTimeout(() => {
      el.hidden = true;
    }, 280);
  }, 4500);
}

function friendlyError(kind) {
  const map = {
    weather: "Sorry, we could not load the weather. Please try again in a moment.",
    news: "Sorry, we could not load market news. Please try again.",
    predict: "Sorry, we could not finish your price forecast. Please try again.",
  };
  return map[kind] || "Something went wrong. Please try again.";
}

async function apiJson(path, options = {}) {
  const res = await fetch(path, {
    headers: { Accept: "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let body;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = null;
  }
  if (!res.ok) {
    const err = new Error(friendlyError("predict"));
    err.kind = "http";
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

/** Resolved market name for APIs (same string backend uses for locations). */
function resolvedMarket() {
  const sel = $("market-select");
  if (!sel || !sel.value) return "";
  if (sel.value === "__other__") {
    return (($("other-market") && $("other-market").value) || "").trim();
  }
  return sel.value.trim();
}

/** Display label for header/cards (e.g. Colombo (Pettah)). */
function displayMarketLabel(apiName) {
  if (!apiName) return "";
  if (apiName === "Colombo") return "Colombo (Pettah)";
  return apiName;
}

function weatherLoadingHtml(placeLabel) {
  const p = escapeHtml(placeLabel);
  return `
    <div class="loading-panel loading-panel--weather" role="status" aria-live="polite">
      <div class="loading-spinner-lg" aria-hidden="true"></div>
      <p class="loading-title">Getting weather…</p>
      <p class="loading-sub">Fetching the forecast for <strong>${p}</strong>. This usually takes a few seconds.</p>
      <div class="skeleton-block" aria-hidden="true">
        <div class="skeleton-line"></div>
        <div class="skeleton-line skeleton-line--mid"></div>
        <div class="skeleton-line skeleton-line--short"></div>
      </div>
    </div>
  `;
}

function newsLoadingHtml(placeLabel) {
  const p = escapeHtml(placeLabel);
  return `
    <div class="loading-panel loading-panel--news" role="status" aria-live="polite">
      <div class="loading-spinner-lg loading-spinner-lg--amber" aria-hidden="true"></div>
      <p class="loading-title">Loading market news…</p>
      <p class="loading-sub">Scanning recent headlines for <strong>${p}</strong>. Please wait…</p>
      <div class="skeleton-block" aria-hidden="true">
        <div class="skeleton-line"></div>
        <div class="skeleton-line skeleton-line--short"></div>
      </div>
    </div>
  `;
}

const WEATHER_IMPACT = {
  heavy_rain: "⚠️ Heavy rain may reduce supply — prices may rise",
  moderate_rain: "🌧️ Some rain expected, slight supply impact",
  light_rain: "🌦️ Light rain only, minimal impact",
  dry: "☀️ Dry conditions, normal supply expected",
  drought_risk: "⚠️ Dry spell may affect future crop supply",
  unknown: "Weather details are limited right now; we still use the latest data we have.",
};

const NEWS_MOOD = {
  very_negative: "⚠️ Bad news for supply — prices may rise",
  negative: "📉 Some negative signals — prices may increase slightly",
  neutral: "📊 Normal market conditions",
  positive: "✅ Good news for market — prices may stay steadier",
  very_positive: "🎉 Great market conditions — can be a good time to sell",
};

const NEWS_MEANS = {
  very_negative: "Prices may be unpredictable this week. Consider selling soon if your tomatoes are ready.",
  negative: "Keep an eye on buyers and transport; pressure may build on prices.",
  neutral: "No strong red flags in the headlines we saw. Use the price forecast as your main guide.",
  positive: "Headlines look supportive. You may have a bit more room on timing.",
  very_positive: "News tone is encouraging. Still check the day-by-day prices below.",
};

/** Plain wording for “why” section (no emoji). */
const NEWS_SENTIMENT_PLAIN = {
  very_negative: "worrying signals",
  negative: "some caution in the news",
  neutral: "a calm tone in the news",
  positive: "supportive signals",
  very_positive: "very supportive signals",
};

function rainfallLine(daily) {
  if (!Array.isArray(daily) || daily.length === 0) return "Rainfall: not available for this week.";
  const total = daily.reduce((a, b) => a + Number(b || 0), 0);
  const mx = Math.max(...daily.map((x) => Number(x || 0)));
  if (mx > 50) return `🌧️ Rainfall: heavy (peak day up to ${mx.toFixed(1)} mm)`;
  if (mx > 20) return `🌧️ Rainfall: moderate (peak day up to ${mx.toFixed(1)} mm)`;
  if (mx > 5) return `🌦️ Rainfall: light (peak day up to ${mx.toFixed(1)} mm)`;
  if (total < 1) return `🌧️ Rainfall: low (${total.toFixed(1)} mm over the week)`;
  return `🌧️ Rainfall: low (${total.toFixed(1)} mm over the week)`;
}

function conditionsLabel(signal) {
  const s = (signal || "").toLowerCase();
  if (s === "dry") return "Dry";
  if (s === "light_rain") return "Light rain at times";
  if (s === "moderate_rain") return "Wet periods";
  if (s === "heavy_rain") return "Very wet";
  if (s === "drought_risk") return "Very dry";
  return "Mixed";
}

function renderWeatherCard(data, displayArea) {
  const title = $("weather-title");
  const body = $("weather-body");
  if (!title || !body) return;
  const area = data.area_used_for_forecast || displayArea || "your area";
  title.textContent = `☀️ Weather near ${area}`;
  const temp = Number(data.expected_temperature_celsius);
  const tempStr = Number.isFinite(temp) ? `${temp.toFixed(1)}°C` : "—";
  const impact = WEATHER_IMPACT[data.weather_signal] || WEATHER_IMPACT.unknown;
  const rainLine = rainfallLine(data.daily_rainfall);
  const cond = conditionsLabel(data.weather_signal);
  body.innerHTML = `
    <div class="weather-stats">
      <div class="stat-tile">
        <span class="stat-label">Temperature</span>
        <span class="stat-value">${escapeHtml(tempStr)}</span>
      </div>
      <div class="stat-tile stat-tile-wide">
        <span class="stat-label">Rainfall</span>
        <span class="stat-value stat-value-sm">${escapeHtml(rainLine)}</span>
      </div>
      <div class="stat-tile">
        <span class="stat-label">Conditions</span>
        <span class="stat-value">${escapeHtml(cond)}</span>
      </div>
    </div>
    <div class="weather-impact">
      <p class="impact-heading">Impact on tomato supply</p>
      <p class="impact-body">${escapeHtml(impact)}</p>
    </div>
  `;
}

function sentimentKey(raw) {
  const k = String(raw || "neutral").toLowerCase().replace(/\s+/g, "_");
  if (NEWS_MOOD[k]) return k;
  return "neutral";
}

function renderNewsCard(data) {
  const body = $("news-body");
  if (!body) return;
  const sent = sentimentKey(data.news_sentiment);
  const mood = NEWS_MOOD[sent] || NEWS_MOOD.neutral;
  const means = NEWS_MEANS[sent] || NEWS_MEANS.neutral;
  const heads = (data.relevant_headlines || []).slice(0, 5);
  const list =
    heads.length > 0
      ? `<ul class="headline-list">${heads.map((h) => `<li>${escapeHtml(h)}</li>`).join("")}</ul>`
      : "<p>No short headlines matched this time — the market still looks calm in the news we checked.</p>";
  body.innerHTML = `
    <p class="mood-line">Overall mood: ${escapeHtml(mood)}</p>
    <p><strong>Latest headlines:</strong></p>
    ${list}
    <p class="meaning-line"><strong>What this means for you:</strong><br />${escapeHtml(means)}</p>
  `;
}

function parsePriceList(arr) {
  if (!Array.isArray(arr)) return [];
  return arr.map((x) => Number.parseFloat(String(x))).filter((n) => Number.isFinite(n));
}

function dayLabel(i) {
  if (i === 0) return "Tomorrow";
  return `Day ${i + 1}`;
}

/** YYYY-MM-DD → readable label (avoid UTC shift). */
function formatSellingDate(iso) {
  if (!iso || typeof iso !== "string") return "";
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso.trim());
  if (!m) return iso;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-LK", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function refreshTargetDateBounds() {
  const inp = $("target-date");
  if (!inp) return;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const min = new Date(today);
  min.setDate(min.getDate() + 1);
  const max = new Date(today);
  max.setDate(max.getDate() + 16);
  inp.min = min.toISOString().slice(0, 10);
  inp.max = max.toISOString().slice(0, 10);
  if (inp.value && (inp.value < inp.min || inp.value > inp.max)) {
    inp.value = "";
  }
}

/** Index in predicted series closest to focal headline price. */
function focalRowIndex(pred, focalPrice) {
  if (!pred.length || !Number.isFinite(focalPrice)) return -1;
  let best = 0;
  let bestDiff = Infinity;
  pred.forEach((p, i) => {
    const diff = Math.abs(p - focalPrice);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = i;
    }
  });
  return best;
}

function trendBaselineToFocal(baseline, focal) {
  if (!Number.isFinite(focal)) {
    return { label: "➡️ Prices steady", className: "trend-flat", key: "stable" };
  }
  if (baseline == null || !Number.isFinite(baseline) || Math.abs(baseline) < 1e-6) {
    return { label: "➡️ Prices steady", className: "trend-flat", key: "stable" };
  }
  const ch = (focal - baseline) / baseline;
  if (ch > 0.02) return { label: "📈 Prices rising", className: "trend-up", key: "up" };
  if (ch < -0.02) return { label: "📉 Prices falling", className: "trend-down", key: "down" };
  return { label: "➡️ Prices steady", className: "trend-flat", key: "stable" };
}

function friendlyTargetNote(raw) {
  if (!raw || typeof raw !== "string") return "";
  if (raw.includes("capped at")) {
    return "That date is further than 16 days ahead. We show prices for the next 16 days and use the last day for the amount on your date.";
  }
  return raw;
}

function pctChange(prev, cur) {
  if (!Number.isFinite(prev) || prev === 0 || !Number.isFinite(cur)) return null;
  return ((cur - prev) / prev) * 100;
}

/** Trend vs last known price (or first forecast day if no history). */
function trendFromForecast(baseline, prices) {
  if (!prices.length) return { label: "➡️ Prices steady", className: "trend-flat", key: "stable" };
  const last = prices[prices.length - 1];
  const start = baseline != null && Number.isFinite(baseline) ? baseline : prices[0];
  const denom = Math.abs(start) || 1;
  const ch = (last - start) / denom;
  if (ch > 0.02) return { label: "📈 Prices rising", className: "trend-up", key: "up" };
  if (ch < -0.02) return { label: "📉 Prices falling", className: "trend-down", key: "down" };
  return { label: "➡️ Prices steady", className: "trend-flat", key: "stable" };
}

function adviceCopy(data) {
  const fr = data.farmer_recommendation || {};
  const action = String(fr.action || "").toUpperCase();
  const risk = String(fr.market_risk || "").toUpperCase();
  const unc = String(data.news_uncertainty || "").toLowerCase();

  const holdish =
    action === "WAIT" &&
    (risk === "HIGH" || unc === "elevated" || unc === "very_high");

  if (action === "SELL_NOW") {
    return {
      title: "✅ SELL NOW",
      text: "Prices are expected to soften over the days ahead. Best to sell as soon as you can get a fair buyer.",
    };
  }
  if (holdish) {
    return {
      title: "🤔 HOLD",
      text: "The market looks uncertain. Watch prices for two or three more days before you decide.",
    };
  }
  if (action === "WAIT") {
    return {
      title: "⏳ WAIT",
      text: "Prices may improve a little if you can keep quality for a few more days. Only wait if storage is safe.",
    };
  }
  return {
    title: "💡 OUR ADVICE",
    text: fr.sell_timing_hint || "Use the day-by-day table and your own judgement.",
  };
}

function buildWhySection(data, displayArea) {
  const area = displayArea || data.location || "your area";
  const ws = data.weather_signal || "";
  const weatherSentence =
    ws === "dry"
      ? `Dry conditions near ${area}. Normal tomato supply is more likely this week.`
      : ws === "light_rain"
        ? `Light rain near ${area}. Only a small effect on harvest and transport is expected.`
        : ws === "moderate_rain"
          ? `Some wet weather near ${area}. Transport and picking may slow slightly.`
          : ws === "heavy_rain"
            ? `Heavy rain near ${area}. Harvest delays can tighten supply.`
            : ws === "drought_risk"
              ? `A long dry spell near ${area}. Future supply may get tighter if it continues.`
              : `We combined the latest weather picture for ${area} with your price outlook.`;

  const news = data.news_market_analysis || {};
  const nSent = sentimentKey(news.news_sentiment);
  const nPlain = NEWS_SENTIMENT_PLAIN[nSent] || "mixed signals";
  const art = Number(news.articles_analyzed) || 0;
  const newsPara =
    art > 0
      ? `Market news shows ${nPlain}. We read ${art} recent article${art === 1 ? "" : "s"} about Sri Lanka food and farming.`
      : "Market news was quiet in the articles we checked, so prices lean more on weather and recent selling levels.";

  const past = parsePriceList(data.past_prices_used);
  const pred = parsePriceList(data.predicted_prices);
  const lastObs = past.length ? past[past.length - 1] : null;
  const focal = Number(data.predicted_price);
  let trendPara = "Recent selling levels and the week-ahead outlook were compared to give you this table.";
  if (lastObs != null && Number.isFinite(focal)) {
    if (focal < lastObs * 0.97) {
      trendPara =
        "Recent prices have been relatively strong. Our analysis expects them to ease as more tomatoes reach the markets.";
    } else if (focal > lastObs * 1.03) {
      trendPara =
        "Recent prices have been on the lower side. Our analysis sees room for buyers to pay a bit more in the coming days.";
    } else {
      trendPara = "Recent prices and the week ahead look close together — no sharp jump or drop stands out.";
    }
  }

  return `
    <div class="why-block">
      <h4>Why is this the forecast?</h4>
      <div class="why-item">
        <p class="why-label">Weather</p>
        <p class="why-p">${escapeHtml(weatherSentence)}</p>
      </div>
      <div class="why-item">
        <p class="why-label">Market news</p>
        <p class="why-p">${escapeHtml(newsPara)}</p>
      </div>
      <div class="why-item">
        <p class="why-label">Price trend</p>
        <p class="why-p">${escapeHtml(trendPara)}</p>
      </div>
      <div class="remember-box">
        Remember: this is a forecast, not a guarantee. Prices can change because of sudden rain, transport strikes, or import news.
      </div>
    </div>
  `;
}

function confidenceLabel(score) {
  const s = Number(score);
  if (!Number.isFinite(s)) return "We are moderately sure about this outlook.";
  if (s >= 0.75) return "HIGH confidence in this forecast";
  if (s >= 0.5) return "MEDIUM confidence — keep checking local buyers";
  return "LOWER confidence — use this as one signal among many";
}

function renderForecast(data) {
  const wrap = $("forecast-result");
  if (!wrap) return;
  const displayArea = displayMarketLabel(data.location || resolvedMarket());
  const pred = parsePriceList(data.predicted_prices);
  const past = parsePriceList(data.past_prices_used);
  const baseline = past.length ? past[past.length - 1] : null;
  const currentApprox =
    baseline != null ? Math.round(baseline) : pred.length ? Math.round(pred[0]) : "—";

  const hasTarget = Boolean(data.target_date && String(data.target_date).trim());
  const focalPrice = Number(data.predicted_price);
  const focalRounded = Number.isFinite(focalPrice) ? Math.round(focalPrice) : "—";
  const focalIdx = hasTarget && Number.isFinite(focalPrice) ? focalRowIndex(pred, focalPrice) : -1;

  const day7 = pred.length >= 7 ? Math.round(pred[6]) : pred.length ? Math.round(pred[pred.length - 1]) : "—";
  const trend = hasTarget
    ? trendBaselineToFocal(baseline, focalPrice)
    : trendFromForecast(baseline, pred);

  const advice = adviceCopy(data);
  const conf = Number(data.confidence_score);
  const pct = Number.isFinite(conf) ? Math.round(Math.min(1, Math.max(0, conf)) * 100) : 50;

  const midLabel = hasTarget ? "On your date" : "About day 7";
  const midValue = hasTarget
    ? `${escapeHtml(formatSellingDate(String(data.target_date)))} — About ${escapeHtml(String(focalRounded))} <span class="unit">LKR/kg</span>`
    : `About ${escapeHtml(String(day7))} <span class="unit">LKR/kg</span>`;

  const trendLabel = hasTarget ? "To your date" : "Week trend";

  const noteFriendly = friendlyTargetNote(data.target_date_note);
  const noteBlock = noteFriendly
    ? `<div class="msg-note" role="status">${escapeHtml(noteFriendly)}</div>`
    : "";

  const rows = [];
  const nRows = pred.length;
  for (let i = 0; i < nRows; i++) {
    const prev = i === 0 ? baseline : pred[i - 1];
    const cur = pred[i];
    const p = pctChange(prev, cur);
    let cls = "trend-flat";
    let icon = "➡️";
    let pctStr = "—";
    if (prev != null && p != null && Number.isFinite(p)) {
      if (p > 0.5) {
        cls = "trend-up";
        icon = "📈";
      } else if (p < -0.5) {
        cls = "trend-down";
        icon = "📉";
      }
      pctStr = `${p >= 0 ? "+" : ""}${p.toFixed(1)}%`;
    }
    const rowHighlight = hasTarget && i === focalIdx ? " day-row-target" : "";
    rows.push(`
      <tr class="${rowHighlight.trim()}">
        <td>${escapeHtml(dayLabel(i))}</td>
        <td><strong>${Math.round(cur)} LKR</strong></td>
        <td class="${cls}">${icon} ${escapeHtml(pctStr)}</td>
      </tr>
    `);
  }

  const tableTitle = hasTarget ? "Day-by-day to your date" : "Day-by-day outlook (7 days)";

  wrap.hidden = false;
  wrap.innerHTML = `
    <div class="forecast-panel">
      <div class="forecast-panel-top">
        <h3>Tomato price forecast</h3>
        <p class="forecast-sub">${escapeHtml(displayArea)} market</p>
        ${
          hasTarget
            ? `<p class="forecast-date-line">Selling date: <strong>${escapeHtml(
                formatSellingDate(String(data.target_date))
              )}</strong></p>`
            : ""
        }
      </div>
      ${noteBlock}
      <div class="forecast-metrics metric-grid">
        <div class="metric-tile">
          <span class="metric-tile-label">Latest level</span>
          <span class="metric-tile-value">About ${escapeHtml(String(currentApprox))} <span class="unit">LKR/kg</span></span>
        </div>
        <div class="metric-tile">
          <span class="metric-tile-label">${escapeHtml(midLabel)}</span>
          <span class="metric-tile-value">${midValue}</span>
        </div>
        <div class="metric-tile metric-tile-highlight">
          <span class="metric-tile-label">${escapeHtml(trendLabel)}</span>
          <span class="metric-tile-value ${trend.className}">${escapeHtml(trend.label)}</span>
        </div>
      </div>
      <div class="forecast-divider"></div>
      <div class="day-table-wrap">
        <p class="day-table-title">${escapeHtml(tableTitle)}</p>
        <table class="day-table" aria-label="Day by day prices">
          <thead><tr><th>Day</th><th>Price (LKR)</th><th>Change</th></tr></thead>
          <tbody>${rows.join("")}</tbody>
        </table>
      </div>
      <div class="forecast-divider"></div>
      <div class="advice-block">
        <h4>Our advice</h4>
        <p class="advice-title">${escapeHtml(advice.title)}</p>
        <p class="advice-text">${escapeHtml(advice.text)}</p>
      </div>
      <div class="forecast-divider"></div>
      <div class="confidence-block">
        <p class="conf-heading">How sure we are</p>
        <div class="bar-track" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100">
          <div class="bar-fill" style="width:${pct}%"></div>
        </div>
        <p class="conf-label">${pct}% — ${escapeHtml(confidenceLabel(conf))}</p>
      </div>
      <div class="forecast-divider"></div>
      ${buildWhySection(data, displayArea)}
    </div>
  `;
}

let loadSeq = 0;

async function onMarketChanged() {
  const seq = ++loadSeq;
  const m = resolvedMarket();
  const sel = $("market-select");

  $("weather-error").hidden = true;
  $("news-error").hidden = true;
  $("forecast-error").hidden = true;

  if (!m || (sel && sel.value === "__other__" && !m)) {
    $("weather-section").classList.remove("card-is-loading");
    $("news-section").classList.remove("card-is-loading");
    $("weather-section").hidden = true;
    $("news-section").hidden = true;
    $("btn-forecast").disabled = true;
    $("other-market-wrap").hidden = !sel || sel.value !== "__other__";
    return;
  }

  $("other-market-wrap").hidden = sel.value !== "__other__";
  $("weather-section").hidden = false;
  $("news-section").hidden = false;
  $("btn-forecast").disabled = false;

  const label = displayMarketLabel(m);
  $("weather-title").textContent = `Weather for ${label}`;
  $("weather-section").classList.add("card-is-loading");
  $("news-section").classList.add("card-is-loading");
  $("weather-body").innerHTML = weatherLoadingHtml(label);
  $("news-body").innerHTML = newsLoadingHtml(label);
  $("weather-error").hidden = true;
  $("news-error").hidden = true;

  const locEnc = encodeURIComponent(m);

  const weatherP = fetch(`/weather/?location=${locEnc}`, { headers: { Accept: "application/json" } })
    .then((r) => r.json().then((j) => ({ ok: r.ok, j })))
    .catch(() => ({ ok: false, j: null }));

  const newsP = fetch(`/news/market-analysis?location=${locEnc}`, { headers: { Accept: "application/json" } })
    .then((r) => r.json().then((j) => ({ ok: r.ok, j })))
    .catch(() => ({ ok: false, j: null }));

  const [wRes, nRes] = await Promise.all([weatherP, newsP]);
  if (seq !== loadSeq) return;

  $("weather-section").classList.remove("card-is-loading");
  $("news-section").classList.remove("card-is-loading");

  if (wRes.ok && wRes.j) {
    renderWeatherCard(wRes.j, label);
    $("weather-error").hidden = true;
  } else {
    $("weather-body").innerHTML = "";
    $("weather-error").textContent = friendlyError("weather");
    $("weather-error").hidden = false;
  }

  if (nRes.ok && nRes.j) {
    renderNewsCard(nRes.j);
    $("news-error").hidden = true;
  } else {
    $("news-body").innerHTML = "";
    $("news-error").textContent = friendlyError("news");
    $("news-error").hidden = false;
  }
}

function forecastMode() {
  const el = document.querySelector('input[name="forecast-mode"]:checked');
  return el ? el.value : "week";
}

async function runForecast() {
  const m = resolvedMarket();
  if (!m) {
    showToast("Please choose where you are selling first.", true);
    return;
  }

  const mode = forecastMode();
  refreshTargetDateBounds();
  if (mode === "date") {
    const td = ($("target-date") && $("target-date").value) || "";
    if (!td.trim()) {
      showToast("Please choose your selling date.", true);
      $("target-date-wrap").hidden = false;
      return;
    }
  }

  $("forecast-error").hidden = true;
  $("forecast-loading").hidden = false;
  $("btn-forecast").disabled = true;
  $("btn-forecast").classList.add("btn-is-busy");
  $("forecast-result").hidden = true;
  $("forecast-result").innerHTML = "";

  const payload = {
    location: m,
    currency: "LKR/kg",
    window_size: 10,
  };
  if (mode === "date") {
    payload.target_date = ($("target-date") && $("target-date").value) || "";
  } else {
    payload.forecast_horizon_days = 7;
  }

  try {
    const body = await apiJson("/predict/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderForecast(body);
    syncCardsFromPredict(body);
    showToast("Your forecast is ready.");
    $("forecast-result").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch {
    $("forecast-error").textContent = friendlyError("predict");
    $("forecast-error").hidden = false;
    showToast(friendlyError("predict"), true);
  } finally {
    $("forecast-loading").hidden = true;
    $("btn-forecast").disabled = false;
    $("btn-forecast").classList.remove("btn-is-busy");
  }
}

/** After predict, refresh weather card from full prediction context when possible. */
function syncCardsFromPredict(body) {
  const m = body.location || resolvedMarket();
  const label = displayMarketLabel(m);
  fetch(`/weather/?location=${encodeURIComponent(m)}`, { headers: { Accept: "application/json" } })
    .then((r) => (r.ok ? r.json() : null))
    .then((w) => {
      if (w) renderWeatherCard(w, label);
    })
    .catch(() => {});
  if (body.news_market_analysis) renderNewsCard(body.news_market_analysis);
}

function init() {
  $("market-select").addEventListener("change", onMarketChanged);
  $("other-market").addEventListener(
    "input",
    debounce(() => {
      if ($("market-select").value === "__other__") onMarketChanged();
    }, 400)
  );
  $("btn-forecast").addEventListener("click", runForecast);

  document.querySelectorAll('input[name="forecast-mode"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      const dateMode = forecastMode() === "date";
      const wrap = $("target-date-wrap");
      if (wrap) wrap.hidden = !dateMode;
      if (dateMode) refreshTargetDateBounds();
    });
  });
  refreshTargetDateBounds();
}

function debounce(fn, ms) {
  let t;
  return function debounced(...args) {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), ms);
  };
}

init();
