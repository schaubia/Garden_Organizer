"""
🌿 Garden Planner — Sofia Edition
Upload your plant list, set where each plant actually grows (sun/shade),
get weather-aware care advice and placement warnings.
"""
import streamlit as st
import pandas as pd
import json
import urllib.request
from datetime import date, datetime

st.set_page_config(page_title="🌿 Garden Planner", page_icon="🌿",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Jost:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'Jost', sans-serif; background: #f5f2eb; }
h1,h2,h3 { font-family: 'Cormorant Garamond', serif !important; }
.stButton > button { background:#3d6b1e;color:white;border:none;border-radius:6px;font-family:'Jost',sans-serif;font-weight:500; }
.stButton > button:hover { background:#2c5015; }
.wx-bar { background:linear-gradient(120deg,#1a3a0e 0%,#3d6b1e 60%,#6b8f4e 100%);color:white;border-radius:14px;padding:18px 28px;display:flex;gap:32px;align-items:center;flex-wrap:wrap;margin-bottom:24px; }
.wx-item { text-align:center; }
.wx-val { font-size:1.6rem;font-weight:600;font-family:'Cormorant Garamond',serif; }
.wx-lbl { font-size:0.72rem;opacity:0.75;letter-spacing:0.08em;text-transform:uppercase; }
.wx-alert { background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;font-size:0.85rem;border-left:3px solid #f0c040; }
.mismatch-card { background:#fff4e6;border-left:5px solid #e67e22;border-radius:8px;padding:12px 16px;margin-bottom:8px; }
.mismatch-card.severe { background:#fdecea;border-left-color:#c0392b; }
.mismatch-name { font-family:'Cormorant Garamond',serif;font-size:1.05rem;font-weight:700;color:#1a3a0e; }
.mismatch-body { font-size:0.85rem;color:#555;margin-top:4px;line-height:1.5; }
.sec-hdr { font-family:'Cormorant Garamond',serif;font-size:1.35rem;color:#1a3a0e;border-bottom:2px solid #d4e6c0;padding-bottom:5px;margin:20px 0 14px 0; }
.ai-box { background:#f0f7e8;border:1px solid #b8d89a;border-radius:10px;padding:16px 20px;margin-top:10px;font-size:0.88rem;line-height:1.65;white-space:pre-wrap; }
.adv-section { border-radius:8px;padding:12px 16px;margin-bottom:8px; }
.adv-title { font-weight:600;margin-bottom:5px;font-size:0.9rem; }
.adv-body { font-size:0.87rem;color:#333;line-height:1.6; }
</style>
""", unsafe_allow_html=True)

SOFIA_LAT, SOFIA_LON = 42.698, 23.322
WMO_CODES = {0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",45:"Foggy",
             51:"Light drizzle",53:"Drizzle",55:"Heavy drizzle",61:"Slight rain",63:"Rain",
             65:"Heavy rain",71:"Slight snow",73:"Snow",75:"Heavy snow",80:"Rain showers",
             81:"Rain showers",82:"Violent showers",95:"Thunderstorm",96:"Thunderstorm+hail"}

SUN_OPTIONS = {"full_sun":"☀️ Full sun","partial_shade":"⛅ Partial shade","full_shade":"🌑 Full shade"}
SOIL_OPTIONS = {"well_drained":"🪨 Well drained","moist":"💧 Moist","clay":"🟤 Clay","sandy":"🏖 Sandy","rich":"🌱 Rich"}

SUN_NORM = {"full_sun":"full_sun","full sun":"full_sun","partial_shade":"partial_shade",
            "partial sun":"partial_shade","partial shade":"partial_shade",
            "half shade":"partial_shade","half_shade":"partial_shade",
            "full_shade":"full_shade","full shade":"full_shade","shade":"full_shade"}

@st.cache_data(ttl=3600)
def fetch_weather():
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={SOFIA_LAT}&longitude={SOFIA_LON}"
           f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,uv_index_max,weathercode"
           f"&current_weather=true&timezone=Europe%2FSofia&forecast_days=7")
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"GardenPlanner/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def parse_weather(raw):
    if "error" in raw:
        return {"ok": False}
    try:
        cw=raw["current_weather"]; d=raw["daily"]
        mins=d["temperature_2m_min"]; maxs=d["temperature_2m_max"]
        rain=d["precipitation_sum"]; uv=d["uv_index_max"]
        codes=d["weathercode"]; dates=d["time"]
        return {"ok":True,"temp_now":cw["temperature"],"desc_now":WMO_CODES.get(cw["weathercode"],"Unknown"),
                "temp_max":maxs[0],"temp_min":mins[0],"uv":uv[0],"rain_today":rain[0],
                "weekly_rain":sum(rain),"frost_risk":any(t<=0 for t in mins),
                "frost_days":[dates[i] for i,t in enumerate(mins) if t<=0],
                "soil_dry":sum(rain)<5 and sum(maxs)/len(maxs)>15,
                "heavy_rain":any(r>=10 for r in rain),
                "dates":dates,"mins":mins,"maxs":maxs,"rain":rain,"uv_all":uv,"codes":codes}
    except:
        return {"ok": False}

def parse_upload(f):
    try:
        nm = f.name.lower()
        df = pd.read_csv(f) if nm.endswith(".csv") else pd.read_excel(f)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        df = df.where(pd.notna(df), None)

        # Detect which column holds light requirements
        sun_vals_set = set(SUN_NORM.keys())
        if "sun_needed" in df.columns:
            sun_col = "sun_needed"
        elif "zone" in df.columns and df["zone"].dropna().astype(str).str.lower().str.strip().isin(sun_vals_set).mean() > 0.4:
            sun_col = "zone"
        elif "sun" in df.columns:
            sun_col = "sun"
        else:
            return None, "Need a column with light requirements (sun_needed, sun, or zone with sun values)."

        df["sun_needed"] = df[sun_col].astype(str).str.strip().str.lower().map(SUN_NORM)
        if sun_col != "sun_needed" and sun_col in df.columns:
            df = df.drop(columns=[sun_col])
        if "zone" in df.columns and sun_col != "zone":
            df = df.drop(columns=["zone"])
        if "sun" in df.columns and sun_col != "sun":
            df = df.drop(columns=["sun"])

        if "actual_sun" not in df.columns:
            df["actual_sun"] = None
        if "name" not in df.columns:
            return None, "Missing required 'name' column."

        df["name"] = df["name"].astype(str).str.strip()
        for col in ["latin","soil","wind","notes"]:
            if col not in df.columns:
                df[col] = None
        df["is_bulb"] = df.get("is_bulb", pd.Series([False]*len(df))).apply(
            lambda x: str(x).strip().lower() in ("yes","true","1","да") if x else False)
        return df, ""
    except Exception as e:
        return None, str(e)

def sun_mismatch(needed, actual):
    order = ["full_shade","partial_shade","full_sun"]
    if not needed or not actual or needed not in order or actual not in order:
        return None
    diff = order.index(actual) - order.index(needed)
    if diff >= 1: return "over"
    if diff <= -1: return "under"
    return None

def ask_claude(system, user):
    payload = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":1000,
                          "system":system,"messages":[{"role":"user","content":user}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload,
          headers={"Content-Type":"application/json","anthropic-version":"2023-06-01"},method="POST")
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())["content"][0]["text"]

def build_prompt(row, wx, today):
    season = ("Spring" if today.month in [3,4,5] else "Summer" if today.month in [6,7,8]
              else "Autumn" if today.month in [9,10,11] else "Winter")
    wx_block = ""
    if wx.get("ok"):
        wx_block = (f"Weather Sofia: {wx['temp_now']}°C, {wx['desc_now']}. "
                    f"Today {wx['temp_max']}°/{wx['temp_min']}°C, UV {wx['uv']}, "
                    f"rain {wx['rain_today']}mm today / {wx['weekly_rain']:.0f}mm this week. "
                    f"Frost days: {wx['frost_days'] or 'none'}. "
                    f"Soil: {'DRY — water needed' if wx['soil_dry'] else 'adequately moist'}.")
    needed = SUN_OPTIONS.get(str(row.get("sun_needed") or ""), "unknown")
    actual = SUN_OPTIONS.get(str(row.get("actual_sun") or ""), "not set")
    soil   = SOIL_OPTIONS.get(str(row.get("soil") or ""), str(row.get("soil") or "not specified"))
    mtype  = sun_mismatch(row.get("sun_needed"), row.get("actual_sun"))
    placement = (f"⚠️ PLACEMENT PROBLEM: needs {needed} but gets {actual} — {'too much sun' if mtype=='over' else 'too little sun'}."
                 if mtype else ("✅ Sun conditions match." if row.get("actual_sun") else "Sun position not set."))
    return (f"Plant: {row['name']} ({row.get('latin') or ''})\n"
            f"Needs: {needed} | Gets: {actual}\nSoil: {soil} | Bulb: {'yes' if row.get('is_bulb') else 'no'}\n"
            f"Notes: {row.get('notes') or 'none'}\n{placement}\nSeason: {season}, {today.strftime('%d %B %Y')}\n{wx_block}")

SYSTEM_CARE = """Expert organic gardener, Sofia Bulgaria (continental climate: hot dry summers, cold winters, frosts Oct–Apr).
PRACTICAL, SPECIFIC, weather-aware advice. Exact calendar months. Biological/organic products only.

Respond in this EXACT structure (use these exact headers):

PRUNING: When and how. Specific months. Weather timing notes.
FEEDING: Biological products (worm castings, compost tea, seaweed, nettle tea, Biobizz…), when, how often.
WATERING: How much and how often. Note if needed NOW based on weather.
BULB_CARE: (only for bulbs/corms/tubers) When to lift, how to store, when to replant. Omit for non-bulbs.
PLACEMENT: If sun matches — confirm briefly. If WRONG — say "⚠️ UNSUITABLE", explain, say REPLANT or REMOVE and best month.
ALTERNATIVES: (only if UNSUITABLE) 3 specific plants that thrive in the actual conditions.

2–4 sentences per section."""

for key, default in [("plants_df",None),("advice_cache",{}),("wx",None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 Garden Planner")
    st.caption("Sofia, Bulgaria")
    st.divider()
    tab_choice = st.radio("Navigate",
        ["🌤️ Dashboard","☀️ Sun Setup","📋 Plant Advice","📤 Upload","🤖 Ask AI"],
        label_visibility="collapsed")
    st.divider()

    plant_count = len(st.session_state.plants_df) if st.session_state.plants_df is not None else 0
    if plant_count:
        n_set = int((st.session_state.plants_df["actual_sun"].notna() &
                     (st.session_state.plants_df["actual_sun"] != "")).sum())
        st.success(f"✅ {plant_count} plants loaded")
        st.caption(f"☀️ {n_set}/{plant_count} sun positions set")
        if st.button("↩️ Replace plant list", use_container_width=True):
            st.session_state.plants_df = None
            st.session_state.advice_cache = {}
            st.rerun()
    else:
        st.markdown("**📂 Load your plants:**")
        sb_file = st.file_uploader("CSV or XLSX", type=["csv","xlsx","xls"],
                                   key="sidebar_uploader", label_visibility="collapsed")
        if sb_file:
            parsed, err = parse_upload(sb_file)
            if err: st.error(f"❌ {err}")
            else:
                st.session_state.plants_df = parsed
                st.session_state.advice_cache = {}
                st.rerun()
    st.divider()

    if st.button("🔄 Refresh Weather", use_container_width=True):
        st.cache_data.clear(); st.session_state.wx = None
    if st.session_state.wx is None:
        with st.spinner("Fetching Sofia weather…"):
            st.session_state.wx = parse_weather(fetch_weather())
    wx = st.session_state.wx
    if wx.get("ok"):
        st.markdown(f"**{wx['temp_now']}°C** · {wx['desc_now']}")
        st.caption(f"↑{wx['temp_max']}° ↓{wx['temp_min']}° · UV {wx['uv']} · 🌧️ {wx['rain_today']}mm")
        if wx["frost_risk"]: st.warning(f"❄️ Frost: {', '.join(wx['frost_days'])}")
    else:
        st.caption("Weather unavailable")
    st.divider()
    today = st.date_input("📅 Date", value=date.today())

df = st.session_state.plants_df
wx = st.session_state.wx or {"ok": False}

def require_plants(key):
    if st.session_state.plants_df is None:
        st.markdown("### 📂 Upload your plant list to get started")
        up = st.file_uploader("CSV or XLSX", type=["csv","xlsx","xls"], key=key)
        if up:
            parsed, err = parse_upload(up)
            if err: st.error(f"❌ {err}")
            else:
                st.session_state.plants_df = parsed
                st.session_state.advice_cache = {}
                st.rerun()
        st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if tab_choice == "🌤️ Dashboard":
    st.markdown("# 🌿 Garden Dashboard")
    if wx.get("ok"):
        frost_txt = f"❄️ Frost in {len(wx['frost_days'])}d" if wx["frost_risk"] else "✅ No frost this week"
        water_txt = "💧 Water needed" if wx["soil_dry"] else "🌧️ Soil OK"
        st.markdown(f"""<div class="wx-bar">
          <div class="wx-item"><div class="wx-val">{wx['temp_now']}°C</div><div class="wx-lbl">Now</div></div>
          <div class="wx-item"><div class="wx-val">{wx['temp_max']}° / {wx['temp_min']}°</div><div class="wx-lbl">Today max/min</div></div>
          <div class="wx-item"><div class="wx-val">{wx['uv']}</div><div class="wx-lbl">UV Index</div></div>
          <div class="wx-item"><div class="wx-val">{wx['rain_today']} mm</div><div class="wx-lbl">Rain today</div></div>
          <div class="wx-item"><div class="wx-val">{wx['weekly_rain']:.0f} mm</div><div class="wx-lbl">7-day rain</div></div>
          <div class="wx-item"><div class="wx-val">{wx['desc_now']}</div><div class="wx-lbl">Conditions</div></div>
          <div class="wx-alert">{frost_txt} &nbsp;·&nbsp; {water_txt}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div class="sec-hdr">7-Day Forecast</div>', unsafe_allow_html=True)
        fcols = st.columns(7)
        for i, col in enumerate(fcols):
            dl = datetime.strptime(wx["dates"][i],"%Y-%m-%d").strftime("%a %d")
            icon = "❄️" if wx["mins"][i]<=0 else ("🌧️" if wx["rain"][i]>5 else ("☀️" if wx["codes"][i]<=2 else "⛅"))
            col.markdown(f"**{dl}**")
            col.markdown(f"{icon} {wx['maxs'][i]:.0f}°/{wx['mins'][i]:.0f}°")
            if wx["rain"][i]>0: col.caption(f"💧{wx['rain'][i]:.0f}mm")
    else:
        st.info("Weather unavailable — check connection and refresh.")
    st.divider()
    require_plants("dash_uploader")

    n_set = int((df["actual_sun"].notna() & (df["actual_sun"] != "")).sum())
    mismatches = [(row, sun_mismatch(row.get("sun_needed"), row.get("actual_sun")))
                  for _, row in df.iterrows()
                  if sun_mismatch(row.get("sun_needed"), row.get("actual_sun"))]
    c1,c2,c3 = st.columns(3)
    c1.metric("🌱 Plants", len(df))
    c2.metric("☀️ Sun positions set", f"{n_set} / {len(df)}")
    c3.metric("⚠️ Mismatches", len(mismatches))

    if n_set < len(df):
        remaining = len(df) - n_set
        st.warning(f"☀️ {remaining} plant{'s' if remaining>1 else ''} still need a sun position — go to **☀️ Sun Setup**.")

    if mismatches:
        st.markdown('<div class="sec-hdr">⚠️ Placement Mismatches</div>', unsafe_allow_html=True)
        for row, mtype in mismatches:
            needed = SUN_OPTIONS.get(str(row.get("sun_needed") or ""), "?")
            actual = SUN_OPTIONS.get(str(row.get("actual_sun") or ""), "?")
            msg = (f"Gets <b>{actual}</b> but needs <b>{needed}</b> — "
                   f"{'too much sun, may scorch.' if mtype=='over' else 'too little sun, may not flower or grow well.'}")
            st.markdown(f"""<div class="mismatch-card {'severe' if mtype=='over' else ''}">
              <div class="mismatch-name">{row['name']} <span style="font-size:0.8rem;font-weight:400;color:#666">— {row.get('latin','')}</span></div>
              <div class="mismatch-body">{msg}</div></div>""", unsafe_allow_html=True)

    if wx.get("ok"):
        st.markdown('<div class="sec-hdr">🔔 Weather Alerts</div>', unsafe_allow_html=True)
        alerts = []
        if wx["frost_risk"]:
            bulbs = df[df["is_bulb"]==True]["name"].tolist()
            if bulbs: alerts.append(f"❄️ **Frost expected** — protect or lift: {', '.join(bulbs)}")
            alerts.append("❄️ Avoid pruning frost-sensitive plants this week.")
        if wx["soil_dry"]: alerts.append("💧 **Soil is dry** — water deeply, morning or evening.")
        if wx["uv"] >= 7: alerts.append("☀️ **High UV** — avoid transplanting. Water early.")
        if wx["heavy_rain"]: alerts.append("🌧️ Heavy rain forecast — skip feeding this week.")
        if not alerts: alerts.append("✅ No urgent alerts — good week for routine tasks.")
        for a in alerts: st.markdown(f"- {a}")

# ══════════════════════════════════════════════════════════════════════════════
# SUN SETUP
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "☀️ Sun Setup":
    st.markdown("# ☀️ Sun Position Setup")
    st.caption("For each plant, set how much sun it actually receives where it's planted in your garden.")
    require_plants("sun_uploader")

    st.markdown('<div class="sec-hdr">Bulk assign</div>', unsafe_allow_html=True)
    bc1,bc2,bc3,bc4 = st.columns([2.5,1.2,1.5,1.3])
    bulk_q = bc1.text_input("Filter by name (leave empty = all)", placeholder="e.g. роза, лук…", label_visibility="collapsed")
    mask = (st.session_state.plants_df["name"].str.contains(bulk_q, case=False, na=False)
            if bulk_q else pd.Series([True]*len(st.session_state.plants_df)))
    if bc2.button("☀️ All → Full sun"):
        st.session_state.plants_df.loc[mask,"actual_sun"] = "full_sun"; st.rerun()
    if bc3.button("⛅ All → Partial shade"):
        st.session_state.plants_df.loc[mask,"actual_sun"] = "partial_shade"; st.rerun()
    if bc4.button("🌑 All → Full shade"):
        st.session_state.plants_df.loc[mask,"actual_sun"] = "full_shade"; st.rerun()
    st.divider()

    show_f = st.radio("Show", ["All plants","⚠️ Mismatches only","○ Not set yet"], horizontal=True)

    for i, row in st.session_state.plants_df.iterrows():
        actual = row.get("actual_sun") or ""
        needed = row.get("sun_needed") or ""
        mtype  = sun_mismatch(needed, actual)
        if show_f == "⚠️ Mismatches only" and not mtype: continue
        if show_f == "○ Not set yet" and actual: continue

        status = "○" if not actual else ("⚠️" if mtype else "✅")
        color  = "#aaa" if not actual else ("#c0392b" if mtype=="over" else ("#e67e22" if mtype=="under" else "#2c7a1e"))

        cn, cneeded, cb1, cb2, cb3 = st.columns([3,2,1.2,1.5,1.3])
        cn.markdown(f"<span style='color:{color};font-weight:600'>{status} {row['name']}</span>"
                    f"<br><span style='font-size:0.75rem;color:#888'>{row.get('latin','')}</span>",
                    unsafe_allow_html=True)
        cneeded.markdown(f"<span style='font-size:0.82rem;color:#555'>Needs: {SUN_OPTIONS.get(needed, needed or '—')}</span>",
                         unsafe_allow_html=True)
        t = lambda v: "primary" if actual==v else "secondary"
        if cb1.button("☀️ Full sun",    key=f"fs_{i}",  type=t("full_sun")):
            st.session_state.plants_df.at[i,"actual_sun"]="full_sun"; st.rerun()
        if cb2.button("⛅ Part. shade", key=f"ps_{i}",  type=t("partial_shade")):
            st.session_state.plants_df.at[i,"actual_sun"]="partial_shade"; st.rerun()
        if cb3.button("🌑 Full shade",  key=f"fsh_{i}", type=t("full_shade")):
            st.session_state.plants_df.at[i,"actual_sun"]="full_shade"; st.rerun()

    st.divider()
    n_set = int((st.session_state.plants_df["actual_sun"].notna() &
                 (st.session_state.plants_df["actual_sun"] != "")).sum())
    st.caption(f"☀️ {n_set} / {len(df)} plants have sun position set.")

# ══════════════════════════════════════════════════════════════════════════════
# PLANT ADVICE
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "📋 Plant Advice":
    st.markdown("# 📋 Plant Care Advice")
    require_plants("adv_uploader")

    filt = st.radio("Show", ["All","⚠️ Mismatches only","🫙 Bulbs only"], horizontal=True)
    filtered = df.copy()
    if filt == "⚠️ Mismatches only":
        filtered = filtered[filtered.apply(lambda r: sun_mismatch(r.get("sun_needed"),r.get("actual_sun")) is not None, axis=1)]
    elif filt == "🫙 Bulbs only":
        filtered = filtered[filtered["is_bulb"]==True]

    cb, ci = st.columns([2,3])
    if cb.button("🤖 Generate advice for all shown plants", use_container_width=True):
        bar = st.progress(0, text="Generating…")
        for i,(_, row) in enumerate(filtered.iterrows()):
            k = row["name"]
            if k not in st.session_state.advice_cache:
                try: st.session_state.advice_cache[k] = ask_claude(SYSTEM_CARE, build_prompt(row,wx,today))
                except Exception as e: st.session_state.advice_cache[k] = f"Error: {e}"
            bar.progress((i+1)/len(filtered), text=f"Done: {row['name']}")
        bar.empty(); st.success("✅ All advice generated!")
    ci.caption(f"{len(filtered)} plants · ~5–10s each")
    st.divider()

    SEC = {"PRUNING":("✂️ Pruning","#eaf2e0","#2c5015"),
           "FEEDING":("🌿 Feeding","#f0f7e8","#1a5226"),
           "WATERING":("💧 Watering","#e8f3fb","#1a3a5c"),
           "BULB_CARE":("🫙 Bulb Care","#fef9e8","#5c4a00"),
           "PLACEMENT":("📍 Placement","#fff8f0","#7a3000"),
           "ALTERNATIVES":("🌱 Alternatives","#f3eeff","#3a1a7a")}

    for _, row in filtered.iterrows():
        name   = row["name"]
        needed = SUN_OPTIONS.get(str(row.get("sun_needed") or ""),"?")
        actual = SUN_OPTIONS.get(str(row.get("actual_sun") or ""),"— not set —")
        mtype  = sun_mismatch(row.get("sun_needed"),row.get("actual_sun"))
        warn   = "⚠️ " if mtype else ("✅ " if row.get("actual_sun") else "○ ")
        with st.expander(f"{warn}**{name}**{'  🫙' if row.get('is_bulb') else ''} · needs {needed} · gets {actual}"):
            if row.get("latin"): st.caption(f"*{row['latin']}*")
            if row.get("notes"): st.caption(f"📝 {row['notes']}")
            if name not in st.session_state.advice_cache:
                if st.button(f"🤖 Get advice", key=f"gen_{name}"):
                    with st.spinner(f"Analysing {name}…"):
                        try:
                            st.session_state.advice_cache[name] = ask_claude(SYSTEM_CARE, build_prompt(row,wx,today))
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
            else:
                text = st.session_state.advice_cache[name]
                parsed = {}; current = None
                for line in text.split("\n"):
                    for sec in SEC:
                        if line.strip().startswith(sec+":"):
                            current=sec; parsed[sec]=line.split(":",1)[1].strip(); break
                    else:
                        if current and line.strip():
                            parsed[current] = parsed.get(current,"") + "\n" + line.strip()
                if parsed:
                    for sec,(title,bg,fg) in SEC.items():
                        if sec in parsed and parsed[sec].strip():
                            border = "2px solid #c0392b" if "UNSUITABLE" in parsed[sec] and sec=="PLACEMENT" else "none"
                            st.markdown(f"""<div class="adv-section" style="background:{bg};border:{border}">
                              <div class="adv-title" style="color:{fg}">{title}</div>
                              <div class="adv-body">{parsed[sec].strip()}</div></div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="ai-box">{text}</div>', unsafe_allow_html=True)
                if st.button("🔄 Regenerate", key=f"regen_{name}"):
                    del st.session_state.advice_cache[name]; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD TAB
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "📤 Upload":
    st.markdown("# 📤 Upload Plant List")
    st.markdown("""Your file needs at minimum:
- **`name`** — plant name
- **`sun_needed`** (or `sun` or `zone`) — light requirement: `full_sun` / `partial_shade` / `half shade` / `shade`

Optional: `latin`, `actual_sun`, `soil`, `wind`, `is_bulb` (yes/no), `notes`""")

    tpl = pd.DataFrame([
        {"name":"Лавандула","latin":"Lavandula angustifolia","sun_needed":"full_sun","actual_sun":"","soil":"well_drained","is_bulb":"no","notes":""},
        {"name":"Хоста","latin":"Hosta spp.","sun_needed":"partial_shade","actual_sun":"","soil":"moist","is_bulb":"no","notes":""},
        {"name":"Момина сълза","latin":"Convallaria majalis","sun_needed":"full_shade","actual_sun":"","soil":"moist","is_bulb":"no","notes":""},
    ])
    st.download_button("⬇️ Download CSV template", tpl.to_csv(index=False).encode(), "garden_template.csv","text/csv")
    st.divider()

    up = st.file_uploader("Upload your file", type=["csv","xlsx","xls"], key="upload_tab")
    if up:
        parsed,err = parse_upload(up)
        if err: st.error(f"❌ {err}")
        else:
            st.success(f"✅ {len(parsed)} plants found")
            st.dataframe(parsed[["name","latin","sun_needed","actual_sun","soil","is_bulb"]],
                         use_container_width=True, hide_index=True)
            if st.button("✅ Use this list", type="primary", use_container_width=True):
                st.session_state.plants_df = parsed
                st.session_state.advice_cache = {}
                st.success("Loaded! Go to **☀️ Sun Setup** to set where each plant grows.")

    with st.expander("➕ Add a single plant manually"):
        with st.form("manual_form"):
            c1,c2 = st.columns(2)
            m_name=c1.text_input("Plant name *"); m_latin=c2.text_input("Latin name")
            c3,c4 = st.columns(2)
            m_need  = c3.selectbox("Needs (sun requirement)", list(SUN_OPTIONS.keys()), format_func=lambda x:SUN_OPTIONS[x])
            m_actual= c4.selectbox("Actually gets", [""]+list(SUN_OPTIONS.keys()), format_func=lambda x:SUN_OPTIONS.get(x,"— not set —"))
            m_soil  = st.selectbox("Soil", list(SOIL_OPTIONS.keys()), format_func=lambda x:SOIL_OPTIONS[x])
            m_bulb  = st.checkbox("🫙 Bulb / corm / tuber")
            m_notes = st.text_area("Notes", height=60)
            if st.form_submit_button("Add plant"):
                if not m_name: st.error("Name is required.")
                else:
                    new_row = pd.DataFrame([{"name":m_name.strip(),"latin":m_latin.strip(),
                        "sun_needed":m_need,"actual_sun":m_actual or None,"soil":m_soil,
                        "wind":"tolerant","is_bulb":m_bulb,"notes":m_notes.strip()}])
                    if st.session_state.plants_df is None: st.session_state.plants_df = new_row
                    else: st.session_state.plants_df = pd.concat([st.session_state.plants_df, new_row], ignore_index=True)
                    st.success(f"✅ Added {m_name}!"); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ASK AI
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "🤖 Ask AI":
    st.markdown("# 🤖 Ask the Garden Advisor")
    st.caption("Sofia climate · organic methods · specific timing")
    opts = ["— general question —"] + (df["name"].tolist() if df is not None else [])
    selected = st.selectbox("Context plant (optional)", opts)
    question = st.text_area("Your question", height=100,
        placeholder="When to lift Ranunculus corms?\nBest biological feed for roses?\nMy lavender is yellowing — why?")
    quick = ["What should I do in my garden this week?",
             "Which plants survive Sofia winters without protection?",
             "Best organic soil boosters for containers?",
             "How to protect bulbs from late frost?"]
    qcols = st.columns(2)
    for i,q in enumerate(quick):
        if qcols[i%2].button(q, key=f"qq{i}"): question=q
    if st.button("🤖 Ask", use_container_width=True) and question.strip():
        ctx = ""
        if selected != "— general question —" and df is not None:
            ctx = build_prompt(df[df["name"]==selected].iloc[0], wx, today) + "\n\n"
        elif wx.get("ok"):
            ctx = (f"Sofia garden. {today.strftime('%d %B %Y')}. "
                   f"{wx['temp_now']}°C, {wx['desc_now']}, rain {wx['weekly_rain']:.0f}mm/week, "
                   f"frost: {'yes' if wx['frost_risk'] else 'no'}.\n\n")
        system = "Expert organic gardener, Sofia Bulgaria continental climate. Practical, exact months, biological products only. Under 250 words."
        with st.spinner("Thinking…"):
            try: st.markdown(f'<div class="ai-box">{ask_claude(system, ctx+question)}</div>', unsafe_allow_html=True)
            except Exception as e: st.error(f"Error: {e}")
