/**
 * Tomato Price Advisor — farmer-friendly UI logic.
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

/** Resolved market name for APIs. */
function resolvedMarket() {
  const sel = $("market-select");
  if (!sel || !sel.value) return "";
  if (sel.value === "__other__") {
    return (($("other-market") && $("other-market").value) || "").trim();
  }
  return sel.value.trim();
}

/** Display label for header/cards. */
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
      <p class="loading-title">Loading weather data…</p>
      <p class="loading-sub">Analyzing regional weather signals across Anuradhapura, Badulla, Dambulla, and Nuwara Eliya (${p})…</p>
    </div>
  `;
}


function newsLoadingHtml() {
  return `
    <div class="loading-panel loading-panel--news" role="status" aria-live="polite">
      <div class="loading-spinner-lg loading-spinner-lg--amber" aria-hidden="true"></div>
      <p class="loading-title">Loading market intelligence…</p>
    </div>
  `;
}

const WEATHER_IMPACT = {
  heavy_rain: "⚠️ Heavy rain in growing regions may reduce supply — prices may rise",
  moderate_rain: "🌧️ Rainfall in growing regions may slightly affect harvest supply",
  light_rain: "🌦️ Light rain in growing regions; minimal harvest disruption expected",
  dry: "☀️ Dry conditions in growing regions; normal harvest supply expected",
  drought_risk: "⚠️ Prolonged dry spell in growing regions may tighten future crop supply",
  unknown: "Weather monitoring active.",
};

const NEWS_MOOD = {
  very_negative: "⚠️ Bad news for supply — prices may rise",
  negative: "📉 Negative market signals detected",
  neutral: "📊 Normal market conditions",
  positive: "✅ Supportive market signals",
  very_positive: "🎉 Encouraging market conditions",
};

function rainfallLine(daily) {
  if (!Array.isArray(daily) || daily.length === 0) return "Rainfall: N/A";
  const mx = Math.max(...daily.map((x) => Number(x || 0)));
  if (mx > 50) return `🌧️ Heavy rain (up to ${mx.toFixed(1)} mm)`;
  if (mx > 20) return `🌧️ Moderate rain (up to ${mx.toFixed(1)} mm)`;
  if (mx > 5) return `🌦️ Light rain (up to ${mx.toFixed(1)} mm)`;
  return `☀️ Low/Dry (${mx.toFixed(1)} mm)`;
}

/** Render Multi-Station Regional Weather Impact Card into Left Sidebar #weather-body. */
function renderWeatherCard(regImpact) {
  const body = $("weather-body");
  if (!body || !regImpact) return;

  const html = buildRegionalWeatherCard(regImpact);
  if (html) {
    body.innerHTML = html;
  }
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
  const heads = (data.relevant_headlines || []).slice(0, 5);
  const list =
    heads.length > 0
      ? `<ul class="headline-list">${heads.map((h) => `<li>${escapeHtml(h)}</li>`).join("")}</ul>`
      : "<p class='text-muted-sm'>No major supply alerts reported in recent news monitoring.</p>";

  body.innerHTML = `
    <div class="news-compact-row">
      <span class="news-mood-badge">${escapeHtml(mood)}</span>
    </div>
    <details class="news-headlines-details" style="margin-top: 0.5rem;">
      <summary class="toggle-link">Show Headlines (${heads.length})</summary>
      <div class="headline-wrap-inner" style="margin-top: 0.4rem;">
        ${list}
      </div>
    </details>
  `;
}

function parsePriceList(arr) {
  if (!Array.isArray(arr)) return [];
  return arr.map((x) => Number.parseFloat(String(x))).filter((n) => Number.isFinite(n));
}

function dayLabel(i, forecastDates) {
  const dateStr = Array.isArray(forecastDates) && forecastDates[i] ? forecastDates[i] : "";
  const num = i + 1;
  if (dateStr) {
    return `Day ${num} <span style="font-size: 0.85em; color: var(--text-muted); font-weight: normal;">(${escapeHtml(dateStr)})</span>`;
  }
  return i === 0 ? "Tomorrow" : `Day ${num}`;
}

function pctChange(prev, cur) {
  if (!Number.isFinite(prev) || prev === 0 || !Number.isFinite(cur)) return null;
  return ((cur - prev) / prev) * 100;
}

/** Farmer-facing simple copy in English with plain Sinhala subtitle. */
function adviceCopy(data) {
  const code = String(data.action_code || "").toUpperCase();
  const peakDay = data.peak_day || data.optimal_sell_day || 1;
  const peakPrice = data.peak_price_lkr || data.optimal_sell_price_lkr || data.day1_forecast_lkr;
  const termPrice = data.day14_forecast_lkr;
  const trend = String(data.trend || "").toUpperCase();

  // RULE 1: Anomaly
  if (code === "MONITOR" || (!code && String(data.recommendation || "").toUpperCase().includes("MONITOR"))) {
    return {
      title: "⚠️ MONITOR — Market Anomaly Detected",
      textEn: "Current market prices are behaving unpredictably right now. Keep a close eye on daily physical market offers before committing to a large sale.",
      textSi: "වෙළඳපොළ මිල ගණන් දැනට අවිනිශ්චිත තත්ත්වයක පවතී. විශාල වශයෙන් අලෙවි කිරීමට පෙර දිනපතා වෙළඳපොළ තොරතුරු පරීක්ෂා කරන්න.",
      bannerClass: "banner-monitor",
    };
  }

  // RULE 2 & 3: SELL NOW (Early Peak or Continuous Decline)
  if (code === "SELL_NOW" || (!code && String(data.recommendation || "").toUpperCase().startsWith("SELL NOW") && !String(data.recommendation || "").toUpperCase().includes("HOLD"))) {
    if (peakDay <= 2 && (trend === "DECLINING" || (data.terminal_change_pct != null && data.terminal_change_pct < 0))) {
      return {
        title: `⚡ SELL NOW — Peak Price in Next ${peakDay === 1 ? "1–2 Days" : "Day " + peakDay}`,
        textEn: `Prices are projected to peak near ${Math.round(peakPrice)} LKR/kg around Day ${peakDay} and soften thereafter (reaching ~${Math.round(termPrice)} LKR/kg by Day 14). Selling immediately or near this early peak is recommended.`,
        textSi: `ඉදිරි දින 1–2 තුළ තක්කාලි මිල උපරිම මට්ටමට (~රු. ${Math.round(peakPrice)}) ළඟා වී ඉන්පසු පහත වැටෙනු ඇතැයි අපේක්ෂා කෙරේ. වැඩි ලාභයක් ලබා ගැනීමට වහාම අලෙවි කිරීම සුදුසුය.`,
        bannerClass: "banner-sell",
      };
    }
    return {
      title: "🚨 SELL NOW — Prices Softening",
      textEn: `Prices are projected to decline across the coming days (down to ~${Math.round(termPrice)} LKR/kg). Selling immediately is recommended to protect your earnings before prices drop further.`,
      textSi: "ඉදිරි දින කිහිපය තුළ තක්කාලි මිල පහළ යාමට ඉඩ ඇත. මිල තවත් අඩුවීමට පෙර වහාම අලෙවි කිරීම සුදුසුය.",
      bannerClass: "banner-sell",
    };
  }

  // RULE 4 & 5: HOLD (Mid-term peak or late rise)
  if (code === "HOLD" || (!code && String(data.recommendation || "").toUpperCase() === "HOLD")) {
    if (peakDay <= 5) {
      return {
        title: `📈 HOLD — Optimal Selling Window Around Day ${peakDay}`,
        textEn: `Prices are projected to rise toward a peak of ~${Math.round(peakPrice)} LKR/kg around Day ${peakDay}. Timing sales near this window is recommended if harvested tomatoes can be safely managed without spoilage (3–5 day shelf life).`,
        textSi: `ඉදිරි දින ${peakDay} තුළ තක්කාලි මිල ඉහළ ගොස් උපරිම මට්ටමට (~රු. ${Math.round(peakPrice)}) ළඟා වනු ඇතැයි අපේක්ෂා කෙරේ. වැඩි ලාභයක් ලබා ගැනීම සඳහා අලෙවිය දින කිහිපයක් ප්‍රමාද කිරීම සුදුසුය.`,
        bannerClass: "banner-hold",
      };
    }
    return {
      title: `📈 HOLD — Higher Prices Projected Around Day ${peakDay}`,
      textEn: `Higher market prices (up to ~${Math.round(peakPrice)} LKR/kg) are projected later around Day ${peakDay}. Plan staggered field harvesting rather than holding already-harvested crop in ambient storage for extended periods.`,
      textSi: `ඉදිරි දින ${peakDay} පමණ වන විට ඉහළ මිලක් (~රු. ${Math.round(peakPrice)}) අපේක්ෂා කෙරේ. තක්කාලි කල්තබා ගත නොහැකි බැවින් අස්වනු නෙළීම සැලසුම් සහගතව සිදු කරන්න.`,
      bannerClass: "banner-hold",
    };
  }

  // RULE 6: STABLE (Default)
  return {
    title: "➡️ STABLE — Sell at Convenience",
    textEn: "Prices are projected to remain relatively steady within normal daily market fluctuations. You can sell at your convenience according to harvest readiness.",
    textSi: "තක්කාලි මිල සාමාන්‍ය මට්ටමේ ස්ථාවරව පවතිනු ඇතැයි අපේක්ෂා කෙරේ. අස්වැන්නේ තත්ත්වය අනුව ඔබට පහසු පරිදි අලෙවි කළ හැක.",
    bannerClass: "banner-stable",
  };
}


/** Render Collapsible Technical Details for Researchers / Supervisors. */
function buildTechnicalDetails(data, displayArea) {
  const area = displayArea || data.series || data.location || "your area";
  const reasoningText = data.reasoning || "";
  const d14Rain = data.d14_cum_rain_mm != null ? data.d14_cum_rain_mm.toFixed(1) : "—";
  const weatherLevel = (data.weather_flag_level || "none").toUpperCase();
  const newsLevel = (data.news_flag_level || "none").toUpperCase();
  const isAnomaly = data.is_anomaly ? "YES (Market shock detected)" : "NO (Normal market behavior)";

  const lstmShare = data.driver_share_lstm_pct != null ? data.driver_share_lstm_pct.toFixed(0) : "100";
  const weatherShare = data.driver_share_weather_pct != null ? data.driver_share_weather_pct.toFixed(0) : "0";

  const shapData = data.shap_explanation;
  let shapHtml = "";
  if (shapData && shapData.summary_sentence) {
    const rankedList = Array.isArray(shapData.ranked_timesteps) ? shapData.ranked_timesteps.slice(0, 5) : [];
    const maxVal = Math.max(...rankedList.map(t => Math.abs(t.shap_contribution_lkr)), 0.01);

    const itemsHtml = rankedList.map(t => {
      const val = t.shap_contribution_lkr;
      const isPos = val >= 0;
      const sign = isPos ? "+" : "";
      const color = isPos ? "#10b981" : "#ef4444";
      const pctWidth = Math.min(Math.round((Math.abs(val) / maxVal) * 100), 100);
      const fillClass = isPos ? "shap-bar-fill-pos" : "shap-bar-fill-neg";

      return `
        <div class="shap-bar-item">
          <div class="shap-bar-head">
            <span><strong>${escapeHtml(t.timestep_label)}</strong> (${t.observed_price_lkr.toFixed(2)} LKR/kg)</span>
            <span style="color: ${color}; font-weight: 700;">${sign}${val.toFixed(2)} LKR</span>
          </div>
          <div class="shap-bar-track">
            <div class="${fillClass}" style="width: ${pctWidth}%;"></div>
          </div>
        </div>
      `;
    }).join("");

    shapHtml = `
      <div class="shap-card">
        <p class="shap-title">🔍 LSTM SHAP Timestep Attributions</p>
        <p class="shap-summary"><strong>${escapeHtml(shapData.summary_sentence)}</strong></p>
        <div class="shap-bars-container">
          ${itemsHtml}
        </div>
      </div>
    `;
  }

  const conf = data.is_anomaly ? 0.50 : 0.90;
  const pct = Math.round(conf * 100);

  return `
    <details class="tech-details-card" style="margin-top: 1.2rem;">
      <summary class="tech-summary">⚙️ Technical Details (For Researchers & Supervisors)</summary>
      <div class="tech-details-body" style="padding-top: 1rem;">
        <div class="why-item">
          <p class="why-label">Decision Reasoning Engine Text</p>
          <p class="why-p"><strong>${escapeHtml(reasoningText)}</strong></p>
        </div>
        ${shapHtml}
        <div class="why-item">
          <p class="why-label">Forecast Driver Deconstruction</p>
          <p class="why-p">Base LSTM Price Momentum: <strong>${lstmShare}%</strong> | Weather Calibration: <strong>${weatherShare}%</strong></p>
        </div>
        <div class="why-item">
          <p class="why-label">14-Day Lagged Weather Signal ($\Delta mm$ Anuradhapura)</p>
          <p class="why-p">Flag Level: <strong>${escapeHtml(weatherLevel)}</strong> (${d14Rain} mm cumulative rain change)</p>
        </div>
        <div class="why-item">
          <p class="why-label">Price Residual Anomaly Check (IsolationForest)</p>
          <p class="why-p">Anomaly Flag: <strong>${escapeHtml(isAnomaly)}</strong> (Score: ${data.anomaly_score != null ? data.anomaly_score.toFixed(4) : "—"})</p>
        </div>
        <div class="why-item">
          <p class="why-label">Heuristic Model Confidence Score</p>
          <p class="why-p">Confidence Rating: <strong>${pct}%</strong> (Heuristic flag based on residual bounds)</p>
        </div>
      </div>
    </details>
  `;
}

/** Render Multi-Station Regional Weather Risk Section for Farmers. */
function buildRegionalWeatherCard(regImpact) {
  if (!regImpact || !regImpact.growing_region_weather) return "";
  const gw = regImpact.growing_region_weather;
  const regions = gw.regions || {};
  const season = regImpact.season || "Yala";
  const overallRisk = regImpact.overall_weather_risk || "LOW";
  const primaryRegion = regImpact.primary_region || "Badulla";
  const explanation = regImpact.explanation || "";

  const riskBadgeClass = overallRisk === "SEVERE" ? "badge-danger" : (overallRisk === "MODERATE" ? "badge-warning" : "badge-success");

  let stationCardsHtml = "";
  for (const [stName, stData] of Object.entries(regions)) {
    const rLvl = stData.risk_level || "LOW";
    const stBadgeClass = rLvl === "SEVERE" ? "badge-danger" : (rLvl === "MODERATE" ? "badge-warning" : "badge-success");
    const rain21 = stData.rain_21d_cum_mm != null ? stData.rain_21d_cum_mm.toFixed(1) : "—";
    const zScore = stData.rain_21d_z != null ? (stData.rain_21d_z >= 0 ? "+" : "") + stData.rain_21d_z.toFixed(1) + "σ" : "—";
    const temp3d = stData.temp_3d_avg_c != null ? stData.temp_3d_avg_c.toFixed(1) : "—";
    const weightPct = Math.round((stData.seasonal_weight || 0.25) * 100);

    stationCardsHtml += `
      <div style="background: var(--bg-card, #f8fafc); border: 1px solid var(--border-soft, #e2e8f0); border-radius: 8px; padding: 0.65rem; flex: 1 1 45%; min-width: 130px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem;">
          <strong style="font-size: 0.9rem;">📍 ${escapeHtml(stName)}</strong>
          <span class="badge ${stBadgeClass}" style="font-size: 0.7rem; padding: 1px 5px;">${escapeHtml(rLvl)}</span>
        </div>
        <div style="font-size: 0.82rem; color: var(--text-muted, #64748b);">
          <div>21d Rain: <strong>${rain21} mm</strong> (${zScore})</div>
          <div>3d Temp: <strong>${temp3d} °C</strong> | Weight: <strong>${weightPct}%</strong></div>
        </div>
      </div>
    `;
  }

  const storage = regImpact.market_storage_impact || {};
  const storageLoc = storage.market_location || "";
  const storageTemp = storage.ambient_temp_3d_avg_c != null ? storage.ambient_temp_3d_avg_c.toFixed(1) : "—";
  const storageSpoilage = storage.spoilage_risk_level || "LOW";
  const storageUrgency = storage.selling_urgency || "NORMAL";
  const storageBadgeClass = storageSpoilage === "HIGH" ? "badge-danger" : (storageSpoilage === "MEDIUM" ? "badge-warning" : "badge-success");

  let storageHtml = "";
  if (storageLoc) {
    storageHtml = `
      <div style="margin-top: 0.65rem; padding-top: 0.65rem; border-top: 1px dashed var(--border-soft, #e2e8f0);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
          <strong style="font-size: 0.88rem; color: var(--text-heading, #0f172a);">🏪 Market Storage Impact (${escapeHtml(storageLoc)})</strong>
          <span class="badge ${storageBadgeClass}" style="font-size: 0.7rem; padding: 1px 5px;">Spoilage: ${escapeHtml(storageSpoilage)}</span>
        </div>
        <p style="font-size: 0.82rem; color: var(--text-muted, #64748b); margin: 0;">
          3-Day Ambient Temp: <strong>${storageTemp} °C</strong> | Selling Urgency: <strong>${escapeHtml(storageUrgency)}</strong>
        </p>
      </div>
    `;
  }

  return `
    <div class="card card-pad" style="margin-bottom: 1rem; background: var(--bg-surface, #ffffff); border: 1px solid var(--border-soft, #e2e8f0); border-radius: 12px; padding: 0.9rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-soft, #e2e8f0); padding-bottom: 0.4rem; margin-bottom: 0.65rem;">
        <h3 style="margin: 0; font-size: 0.98rem; color: var(--text-heading, #0f172a);">
          🌱 Sri Lankan Tomato Supply Weather Impact
        </h3>
        <span class="badge ${riskBadgeClass}" style="font-size: 0.78rem;">Season: ${escapeHtml(season)} | Risk: ${escapeHtml(overallRisk)}</span>
      </div>
      <p style="font-size: 0.84rem; color: var(--text-body, #334155); margin-bottom: 0.65rem;">
        Primary Signal: <strong>${escapeHtml(primaryRegion)} 21-Day Rainfall Anomaly</strong>
      </p>
      <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.65rem;">
        ${stationCardsHtml}
      </div>
      ${storageHtml}
      <div style="margin-top: 0.65rem; background: rgba(16, 185, 129, 0.08); border-left: 3px solid #10b981; padding: 0.5rem 0.7rem; border-radius: 4px; font-size: 0.82rem; color: var(--text-body, #334155);">
        <strong>Research Analysis:</strong> ${escapeHtml(explanation)}
      </div>
    </div>
  `;
}


function renderForecast(data) {
  const wrap = $("forecast-result");
  if (!wrap) return;
  wrap.hidden = false;

  if (data.regional_weather_impact) {
    renderWeatherCard(data.regional_weather_impact);
  }


  const displayArea = displayMarketLabel(data.series || data.location || resolvedMarket());


  const pred = Array.isArray(data.weather_adjusted_forecast) && data.weather_adjusted_forecast.length
    ? data.weather_adjusted_forecast
    : parsePriceList(data.predicted_prices);

  const baseline = data.current_price_lkr != null ? data.current_price_lkr : (pred.length ? pred[0] : null);
  const currentApprox = baseline != null ? Math.round(baseline) : "—";

  const focalPrice = Number(data.day1_forecast_lkr || data.predicted_price || (pred.length ? pred[0] : 0));
  const focalRounded = Number.isFinite(focalPrice) ? Math.round(focalPrice) : "—";

  const day14 = data.day14_forecast_lkr != null ? Math.round(data.day14_forecast_lkr) : (pred.length ? Math.round(pred[pred.length - 1]) : "—");
  
  // Calculate 14-day trend arrow & % change
  const totalChgPct = baseline != null && baseline > 0 ? ((day14 - baseline) / baseline) * 100 : 0;
  let trendArrow = "➡️";
  let trendClass = "trend-flat";
  if (totalChgPct > 2.0) {
    trendArrow = "📈";
    trendClass = "trend-up";
  } else if (totalChgPct < -2.0) {
    trendArrow = "📉";
    trendClass = "trend-down";
  }
  const totalChgStr = `${totalChgPct >= 0 ? "+" : ""}${totalChgPct.toFixed(1)}%`;

  const advice = adviceCopy(data);

  // Build Day-by-Day Table Rows (Full 14 Days)
  const nRows = pred.length;
  const fullRows = [];
  const milestoneRows = [];
  const milestoneIndices = [0, 2, 6, nRows - 1].filter(idx => idx >= 0 && idx < nRows);

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

    const rowHtml = `
      <tr>
        <td>${dayLabel(i, data.forecast_dates)}</td>
        <td><strong>${Math.round(cur)} LKR</strong></td>
        <td class="${cls}">${icon} ${escapeHtml(pctStr)}</td>
      </tr>
    `;

    fullRows.push(rowHtml);
    if (milestoneIndices.includes(i)) {
      milestoneRows.push(rowHtml);
    }
  }

  const tableTitle = data.forecast_period_label
    ? `14-Day Forecast (${data.forecast_period_label})`
    : "14-Day Forecast";

  wrap.hidden = false;
  wrap.innerHTML = `
    <div class="forecast-panel">
      <!-- Prominent Color-Coded Recommendation Banner -->
      <div class="rec-banner ${advice.bannerClass}">
        <h3 class="rec-title">${escapeHtml(advice.title)}</h3>
        <p class="rec-body-en">${escapeHtml(advice.textEn)}</p>
        <p class="rec-body-si">${escapeHtml(advice.textSi)}</p>
      </div>

      <!-- 3-Tile Metrics Row -->
      <div class="forecast-metrics metric-grid">
        <div class="metric-tile">
          <span class="metric-tile-label">Current Observed Price</span>
          <span class="metric-tile-value">${escapeHtml(String(currentApprox))} <span class="unit">LKR/kg</span></span>
          <span class="metric-tile-sub">As of ${escapeHtml(data.data_as_of_date || "—")}</span>
        </div>
        <div class="metric-tile">
          <span class="metric-tile-label">Tomorrow's Forecast</span>
          <span class="metric-tile-value">${escapeHtml(String(focalRounded))} <span class="unit">LKR/kg</span></span>
          <span class="metric-tile-sub">${escapeHtml(data.forecast_start_date || "Day 1")}</span>
        </div>
        <div class="metric-tile metric-tile-highlight">
          <span class="metric-tile-label">14-Day Forecast</span>
          <span class="metric-tile-value">${escapeHtml(String(day14))} <span class="unit">LKR/kg</span> <span class="${trendClass}" style="font-size: 0.9em;">${trendArrow} (${totalChgStr})</span></span>
          <span class="metric-tile-sub">${escapeHtml(data.forecast_end_date || "Day 14")}</span>
        </div>
      </div>

      <!-- Compact Milestone Forecast Table with Toggle -->
      <div class="day-table-wrap">
        <div class="table-header-flex">
          <p class="day-table-title">${escapeHtml(tableTitle)}</p>
          <button type="button" id="btn-toggle-days" class="btn-toggle-sm">
            Show All 14 Days
          </button>
        </div>
        <table class="day-table" aria-label="Forecasted prices">
          <thead><tr><th>Forecast Day</th><th>Expected Price (LKR)</th><th>Daily Trend</th></tr></thead>
          <tbody id="forecast-table-body">${milestoneRows.join("")}</tbody>
        </table>
      </div>

      <p class="dataset-coverage-note">Model trained on historical price data from ${escapeHtml(data.dataset_coverage || "Aug 2016 to Aug 2026")}.</p>

      <!-- Collapsible Technical Details for Researchers -->
      ${buildTechnicalDetails(data, displayArea)}


    </div>
  `;

  // Attach Table Toggle Listener
  const toggleBtn = $("btn-toggle-days");
  if (toggleBtn) {
    let showingAll = false;
    toggleBtn.addEventListener("click", () => {
      showingAll = !showingAll;
      const tbody = $("forecast-table-body");
      if (tbody) {
        tbody.innerHTML = showingAll ? fullRows.join("") : milestoneRows.join("");
      }
      toggleBtn.textContent = showingAll ? "Show Key Milestones Only" : "Show All 14 Days";
    });
  }
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
  $("weather-body").innerHTML = weatherLoadingHtml(label);
  $("news-body").innerHTML = newsLoadingHtml();

  const locEnc = encodeURIComponent(m);

  // Fetch Multi-Station Regional Weather Impact & News Signals for selected market
  const marketParts = m.split("-");
  const mkt = marketParts[0].trim();
  const tp = marketParts.length > 1 ? marketParts[1].trim() : "Retail";

  const predictP = apiJson("/predict/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      market: mkt,
      type: tp,
      forecast_horizon_days: 14,
    }),
  }).catch(() => null);


  const newsP = fetch(`/news/market-analysis?location=${locEnc}`, { headers: { Accept: "application/json" } })
    .then((r) => (r.ok ? r.json() : null))
    .catch(() => null);

  const [pData, nData] = await Promise.all([predictP, newsP]);
  if (seq !== loadSeq) return;

  if (pData && pData.regional_weather_impact) {
    renderWeatherCard(pData.regional_weather_impact);
    $("weather-error").hidden = true;
  } else {
    $("weather-body").innerHTML = "";
    $("weather-error").textContent = friendlyError("weather");
    $("weather-error").hidden = false;
  }


  if (nData) {
    renderNewsCard(nData);
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

function selectedTargetDateIso() {
  return (($("target-date") && $("target-date").value) || "").trim();
}

function refreshTargetDateBounds() {
  const inp = $("target-date");
  if (!inp) return;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const min = new Date(today);
  min.setDate(min.getDate() + 1);
  const max = new Date(today);
  max.setDate(max.getDate() + 365); // Allow target date up to 1 year ahead
  inp.min = min.toISOString().slice(0, 10);
  inp.max = max.toISOString().slice(0, 10);
}

function renderSeasonalForecast(data, targetDateStr) {
  const wrap = $("forecast-result");
  if (!wrap) return;
  wrap.hidden = false;

  const nom = data.planning_estimates_nominal || {};
  const real = data.real_price_estimates_constant_lkr || {};
  const conf = (data.confidence_rating || "MODERATE").toUpperCase();
  const confBadgeStyle = conf === "HIGH" ? "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4);" : conf === "MODERATE" ? "background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4);" : "background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4);";
  const confLabel = conf === "HIGH" ? "🟢 HIGH CONFIDENCE" : conf === "MODERATE" ? "🟡 MODERATE CONFIDENCE" : "🔴 LOW CONFIDENCE (HIGH VOLATILITY)";

  const wObj = data.weather || {};
  const isSeas5 = wObj.source === "ECMWF SEAS5";
  const weatherLabel = data.weather_outlook_label || (isSeas5 ? `${wObj.regional_outlook} (ECMWF SEAS5)` : "Near-Normal Rainfall (Historical Baseline)");
  const weatherBadgeIcon = weatherLabel.includes("Above") ? "🌧️ " : weatherLabel.includes("Below") ? "☀️ " : "🌤️ ";

  let weatherSectionHtml = "";
  if (isSeas5 && wObj.ensemble_probability) {
    const ep = wObj.ensemble_probability;
    weatherSectionHtml = `
      <div class="seasonal-weather-card" style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 1.25rem; margin: 1.25rem 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap;">
          <h4 style="margin: 0; font-size: 1.05em; color: #60a5fa;">📊 ${escapeHtml(data.target_month_name)} ${escapeHtml(data.target_year)} Seasonal Climate Outlook</h4>
          <span style="font-size: 0.8em; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 0.2rem 0.6rem; border-radius: 12px;">Source: ECMWF SEAS5 (50-member ensemble)</span>
        </div>
        <p style="font-size: 0.9em; margin-bottom: 0.75rem;">Regional Outlook: <strong>${escapeHtml(wObj.regional_outlook)}</strong> across tomato growing hub</p>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; text-align: center; margin-bottom: 0.75rem;">
          <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 0.5rem; border-radius: 6px;">
            <span style="font-size: 0.75em; color: #6ee7b7; display: block;">Above Normal</span>
            <strong style="font-size: 1.2em; color: #34d399;">${ep.above_normal}%</strong>
          </div>
          <div style="background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.25); padding: 0.5rem; border-radius: 6px;">
            <span style="font-size: 0.75em; color: #93c5fd; display: block;">Near Normal</span>
            <strong style="font-size: 1.2em; color: #60a5fa;">${ep.near_normal}%</strong>
          </div>
          <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.25); padding: 0.5rem; border-radius: 6px;">
            <span style="font-size: 0.75em; color: #fca5a5; display: block;">Below Normal</span>
            <strong style="font-size: 1.2em; color: #f87171;">${ep.below_normal}%</strong>
          </div>
        </div>
        <p style="font-size: 0.78em; color: #94a3b8; margin: 0; font-style: italic;">
          ℹ️ This is a monthly seasonal ensemble outlook indicating regional probabilities, not a specific daily weather forecast. Weather data: Open-Meteo / ECMWF SEAS5
        </p>
      </div>
    `;
  } else {
    weatherSectionHtml = `
      <div class="seasonal-weather-card" style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 1rem; margin: 1.25rem 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
          <h4 style="margin: 0; font-size: 0.95em; color: #cbd5e1;">📅 Historical ${escapeHtml(data.target_month_name)} Climate Baseline</h4>
          <span style="font-size: 0.75em; color: #94a3b8;">Source: Sri Lankan Agromet CSV (2016–2026)</span>
        </div>
        <p style="font-size: 0.85em; color: #94a3b8; margin: 0;">
          Based on 10-year historical weather patterns for ${escapeHtml(data.target_month_name)}. SEAS5 forecast data is not available for this target horizon.
        </p>
      </div>
    `;
  }

  wrap.innerHTML = `
    <div class="forecast-result-card seasonal-mode-card" style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); padding: 1.5rem; border-radius: 16px;">
      <div class="seasonal-header" style="margin-bottom: 1rem;">
        <h3 style="font-size: 1.25em; margin-bottom: 0.25rem;">📅 Seasonal Price Outlook — based on ${escapeHtml(data.historical_seasons_count || "10")} years of CPI-adjusted price patterns</h3>
        <p style="color: var(--text-muted); font-size: 0.95em; margin: 0;">Target Horizon: <strong>${escapeHtml(data.target_month_name)} ${escapeHtml(data.target_year)}</strong> (${escapeHtml(displayMarketLabel(data.series))})</p>
      </div>

      <div class="seasonal-badges-row" style="display: flex; gap: 0.6rem; margin: 1rem 0; flex-wrap: wrap;">
        <span style="padding: 0.4rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.85em; ${confBadgeStyle}">
          ${escapeHtml(confLabel)} (${data.historical_interval_coverage_pct}% Historical Interval Coverage)
        </span>
        <span style="padding: 0.4rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.85em; background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4);">
          ${weatherBadgeIcon}${escapeHtml(weatherLabel)}
        </span>
        <span style="padding: 0.4rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.85em; background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4);">
          🏷️ CPI Inflation Normalized
        </span>
      </div>

      <!-- Horizontal Price Range Bar (25th Core Low -> Median -> 75th Core High) -->
      <div class="price-range-bar-container" style="background: rgba(255,255,255,0.03); padding: 1.25rem; border-radius: 12px; margin: 1.25rem 0; border: 1px solid rgba(255,255,255,0.05);">
        <p style="margin-bottom: 0.75rem; font-weight: 600; font-size: 0.95em;" title="Projected assuming ~4% annual inflation from August 2026 baseline">Expected Core Planning Range (nominal LKR, ~4% inflation assumed):</p>
        <div class="range-values-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); text-align: center; gap: 0.75rem;">
          <div class="range-box range-low" style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.25); padding: 0.75rem; border-radius: 8px;">
            <span style="font-size: 0.75em; color: #fca5a5; display: block; margin-bottom: 0.2rem;">Core Low (25th Pctl)</span>
            <strong style="font-size: 1.3em; color: #f87171;">${nom.core_p25 || "—"} LKR</strong>
          </div>
          <div class="range-box range-median" style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); padding: 0.75rem; border-radius: 8px;">
            <span style="font-size: 0.75em; color: #93c5fd; display: block; margin-bottom: 0.2rem;">Expected Median (50th)</span>
            <strong style="font-size: 1.4em; color: #60a5fa;">${nom.median_p50 || "—"} LKR</strong>
          </div>
          <div class="range-box range-high" style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 0.75rem; border-radius: 8px;">
            <span style="font-size: 0.75em; color: #6ee7b7; display: block; margin-bottom: 0.2rem;">Core High (75th Pctl)</span>
            <strong style="font-size: 1.3em; color: #34d399;">${nom.core_p75 || "—"} LKR</strong>
          </div>
        </div>
        <p style="font-size: 0.85em; color: var(--text-muted); text-align: center; margin-top: 0.85rem; margin-bottom: 0.35rem;">
          Wider Risk Range (10th–90th percentile): <strong>${nom.low_p10} – ${nom.high_p90} LKR/kg</strong> | Constant Real Benchmark: <strong>${real.median_p50} LKR/kg</strong>
        </p>
        <p class="seasonal-inflation-note" style="font-size: 0.78em; color: #94a3b8; text-align: center; margin: 0.35rem 0 0 0; font-style: italic;">
          Nominal prices projected assuming ~4% annual inflation from August 2026 baseline. Actual inflation may differ.
        </p>
      </div>

      ${weatherSectionHtml}

      <div class="seasonal-recommendation-box" style="background: rgba(16, 185, 129, 0.08); border-left: 4px solid var(--accent-green); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <p style="margin: 0; line-height: 1.5; font-size: 0.95em;">💡 <strong>Planning Guidance:</strong> ${escapeHtml(data.planning_recommendation)}</p>
      </div>

      <p class="seasonal-disclaimer" style="font-size: 0.8em; color: var(--text-muted); font-style: italic; margin-top: 1rem; margin-bottom: 0;">
        This is a planning estimate, not a precise forecast. Actual prices may differ due to weather, supply, and market conditions.
      </p>
    </div>
  `;

}


async function runForecast() {
  const m = resolvedMarket();
  if (!m) {
    showToast("Please choose your market location first.", true);
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

    // Check if target date is > 14 days away from today
    const targetDt = new Date(td);
    const todayDt = new Date();
    todayDt.setHours(0, 0, 0, 0);
    const diffDays = Math.ceil((targetDt - todayDt) / (1000 * 60 * 60 * 24));

    if (diffDays > 14) {
      // Activate Seasonal Planning Mode automatically
      const mkt = m.includes("-") ? m.split("-")[0].trim() : m;
      const tp = m.includes("-") ? m.split("-")[1].trim() : "Retail";
      const targetMonth = targetDt.getMonth() + 1;
      const targetYear = targetDt.getFullYear();

      $("forecast-error").hidden = true;
      $("forecast-loading").hidden = false;
      $("btn-forecast").disabled = true;
      $("btn-forecast").classList.add("btn-is-busy");
      $("forecast-result").hidden = true;
      $("forecast-result").innerHTML = "";

      try {
        const sData = await apiJson(`/seasonal-forecast/?market=${encodeURIComponent(mkt)}&type=${encodeURIComponent(tp)}&target_month=${targetMonth}&target_year=${targetYear}`);
        renderSeasonalForecast(sData, td);
        showToast("Your Seasonal Price Outlook is ready.");
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
    market: m.includes("-") ? m.split("-")[0] : m,
    type: m.includes("-") ? m.split("-")[1] : "Retail",
    currency: "LKR/kg",
    forecast_horizon_days: 14,
  };
  if (mode === "date") {
    payload.target_date = ($("target-date") && $("target-date").value) || "";
  }

  try {
    const body = await apiJson("/predict/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderForecast(body);
    showToast("Your AI selling recommendation is ready.");
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


function init() {
  $("market-select").addEventListener("change", onMarketChanged);
  if ($("other-market")) {
    $("other-market").addEventListener(
      "input",
      debounce(() => {
        if ($("market-select").value === "__other__") onMarketChanged();
      }, 400)
    );
  }
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

  // Initial load
  onMarketChanged();
}

function debounce(fn, ms) {
  let t;
  return function debounced(...args) {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), ms);
  };
}

init();
