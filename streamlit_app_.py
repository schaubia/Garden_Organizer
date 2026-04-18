"""
🌿 Garden Planner — Sofia Edition
Upload your plant list (CSV or XLSX), get live weather-aware care advice.
"""
import streamlit as st
import pandas as pd
import json
import io
import urllib.request
from datetime import date, datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🌿 Garden Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Jost:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Jost', sans-serif; background: #f5f2eb; }
h1,h2,h3 { font-family: 'Cormorant Garamond', serif !important; }
.stButton > button {
    background: #3d6b1e; color: white; border: none; border-radius: 6px;
    font-family: 'Jost', sans-serif; font-weight: 500;
}
.stButton > button:hover { background: #2c5015; }

/* Weather bar */
.wx-bar {
    background: linear-gradient(120deg, #1a3a0e 0%, #3d6b1e 60%, #6b8f4e 100%);
    color: white; border-radius: 14px; padding: 18px 28px;
    display: flex; gap: 32px; align-items: center; flex-wrap: wrap;
    margin-bottom: 24px;
}
.wx-item { text-align: center; }
.wx-val  { font-size: 1.6rem; font-weight: 600; font-family: 'Cormorant Garamond', serif; }
.wx-lbl  { font-size: 0.72rem; opacity: 0.75; letter-spacing: 0.08em; text-transform: uppercase; }
.wx-alert { background: rgba(255,255,255,0.15); border-radius: 8px; padding: 8px 14px;
            font-size: 0.85rem; border-left: 3px solid #f0c040; }

/* Task cards */
.task-card {
    background: white; border-radius: 10px; padding: 14px 18px;
    margin-bottom: 10px; border-left: 5px solid #6b8f4e;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.task-card.urgent { border-left-color: #c0392b; }
.task-card.soon   { border-left-color: #e67e22; }
.task-plant { font-family: 'Cormorant Garamond', serif; font-size: 1.1rem; font-weight: 600; color: #1a3a0e; }
.task-body  { font-size: 0.88rem; color: #444; margin-top: 5px; line-height: 1.5; }
.task-meta  { font-size: 0.78rem; color: #888; margin-top: 6px; }
.zone-pill  { background: #eaf2e0; color: #3d6b1e; border-radius: 20px;
              padding: 2px 10px; font-size: 0.72rem; font-weight: 500; display: inline-block; }

/* Warning cards */
.warn-card  {
    background: #fffbf0; border: 1px solid #f0c040; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 10px;
}
.warn-head  { font-weight: 600; color: #9a3b00; font-size: 0.95rem; }
.warn-body  { font-size: 0.85rem; color: #555; margin-top: 6px; line-height: 1.55; }
.remove-card {
    background: #fff2f0; border: 1px solid #e74c3c; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 10px;
}
.remove-head { font-weight: 700; color: #c0392b; font-size: 0.95rem; }

/* Section header */
.sec-hdr {
    font-family: 'Cormorant Garamond', serif; font-size: 1.35rem;
    color: #1a3a0e; border-bottom: 2px solid #d4e6c0;
    padding-bottom: 5px; margin: 20px 0 14px 0;
}

/* Upload area hint */
.col-hint {
    background: #eef7e6; border: 1px dashed #8ab56a; border-radius: 8px;
    padding: 12px 16px; font-size: 0.82rem; color: #3d6b1e; margin-bottom: 12px;
    font-family: monospace;
}

/* AI box */
.ai-box {
    background: #f0f7e8; border: 1px solid #b8d89a; border-radius: 10px;
    padding: 16px 20px; margin-top: 10px; font-size: 0.88rem; line-height: 1.65;
    white-space: pre-wrap;
}

.stSpinner { color: #3d6b1e !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
SOFIA_LAT, SOFIA_LON = 42.698, 23.322

WMO_CODES = {
    0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",
    45:"Foggy",48:"Icy fog",51:"Light drizzle",53:"Drizzle",55:"Heavy drizzle",
    61:"Slight rain",63:"Rain",65:"Heavy rain",71:"Slight snow",73:"Snow",75:"Heavy snow",
    80:"Rain showers",81:"Rain showers",82:"Violent showers",
    95:"Thunderstorm",96:"Thunderstorm+hail",99:"Thunderstorm+heavy hail"
}

REQUIRED_COLS = {"name", "zone"}

SUN_OPTIONS  = ["full_sun","partial_shade","full_shade"]
SOIL_OPTIONS = ["well_drained","moist","clay","sandy","rich"]
WIND_OPTIONS = ["sheltered","tolerant","exposed"]

SUN_LABELS  = {"full_sun":"☀️ Full Sun","partial_shade":"⛅ Partial Shade","full_shade":"🌑 Full Shade"}
SOIL_LABELS = {"well_drained":"🪨 Well Drained","moist":"💧 Moist","clay":"🟤 Clay","sandy":"🏖 Sandy","rich":"🌱 Rich"}
WIND_LABELS = {"sheltered":"🏠 Sheltered","tolerant":"💨 Tolerant","exposed":"🌬️ Exposed"}

# ── Weather fetch ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_weather():
    """Fetch 7-day forecast from Open-Meteo (free, no key needed)."""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={SOFIA_LAT}&longitude={SOFIA_LON}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        f"uv_index_max,weathercode,et0_fao_evapotranspiration"
        f"&current_weather=true&timezone=Europe%2FSofia&forecast_days=7"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "GardenPlanner/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def weather_summary(wx: dict) -> dict:
    """Parse raw Open-Meteo response into a flat summary dict."""
    if "error" in wx:
        return {"ok": False, "error": wx["error"]}
    try:
        cw   = wx["current_weather"]
        d    = wx["daily"]
        mins = d["temperature_2m_min"]
        maxs = d["temperature_2m_max"]
        rain = d["precipitation_sum"]
        uv   = d["uv_index_max"]
        codes= d["weathercode"]
        dates= d["time"]

        frost_days   = [dates[i] for i,t in enumerate(mins) if t <= 0]
        heavy_rain   = [dates[i] for i,r in enumerate(rain) if r >= 10]
        weekly_rain  = sum(rain)
        avg_max      = sum(maxs)/len(maxs)

        return {
            "ok": True,
            "temp_now": cw["temperature"],
            "desc_now": WMO_CODES.get(cw["weathercode"], "Unknown"),
            "temp_max_today": maxs[0],
            "temp_min_today": mins[0],
            "uv_today": uv[0],
            "rain_today": rain[0],
            "frost_days": frost_days,
            "heavy_rain_days": heavy_rain,
            "weekly_rain_mm": weekly_rain,
            "avg_max_week": avg_max,
            "soil_dry": weekly_rain < 5 and avg_max > 15,
            "frost_risk": len(frost_days) > 0,
            "dates": dates,
            "mins": mins,
            "maxs": maxs,
            "rain": rain,
            "uv": uv,
            "codes": codes,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── File parser ────────────────────────────────────────────────────────────────
def parse_upload(uploaded_file) -> tuple[pd.DataFrame | None, str]:
    """Parse CSV or XLSX upload. Returns (df, error_message)."""
    try:
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            return None, "Only .csv, .xlsx or .xls files are supported."
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        missing = REQUIRED_COLS - set(df.columns)
        if missing:
            return None, f"Missing required columns: {', '.join(missing)}"
        df = df.where(pd.notna(df), None)
        df["name"] = df["name"].astype(str).str.strip()
        df["zone"] = df["zone"].astype(str).str.strip()
        for col in ["sun","soil","wind","latin","notes","is_bulb"]:
            if col not in df.columns:
                df[col] = None
        df["is_bulb"] = df["is_bulb"].apply(
            lambda x: str(x).strip().lower() in ("yes","true","1","да") if x else False
        )
        return df, ""
    except Exception as e:
        return None, str(e)

# ── Claude API ─────────────────────────────────────────────────────────────────
def ask_claude(system_prompt: str, user_prompt: str) -> str:
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())["content"][0]["text"]

# ── Advice generator ───────────────────────────────────────────────────────────
def build_plant_prompt(row: pd.Series, wx: dict, today: date) -> str:
    season = (
        "Spring" if today.month in [3,4,5] else
        "Summer" if today.month in [6,7,8] else
        "Autumn" if today.month in [9,10,11] else "Winter"
    )
    wx_block = ""
    if wx.get("ok"):
        wx_block = (
            f"Current weather in Sofia: {wx['temp_now']}°C, {wx['desc_now']}. "
            f"Today max/min: {wx['temp_max_today']}/{wx['temp_min_today']}°C. "
            f"UV index: {wx['uv_today']}. Rain today: {wx['rain_today']}mm. "
            f"Weekly rain total: {wx['weekly_rain_mm']:.0f}mm. "
            f"Frost days this week: {wx['frost_days'] or 'none'}. "
            f"Soil likely {'DRY' if wx['soil_dry'] else 'adequately moist'}."
        )

    sun  = SUN_LABELS.get(str(row.get("sun") or ""), str(row.get("sun") or "not specified"))
    soil = SOIL_LABELS.get(str(row.get("soil") or ""), str(row.get("soil") or "not specified"))
    wind = WIND_LABELS.get(str(row.get("wind") or ""), str(row.get("wind") or "not specified"))
    return f"""Plant: {row['name']} ({row.get('latin') or 'no latin name'})
Zone/bed: {row['zone']}
Is bulb/corm/tuber: {'yes' if row.get('is_bulb') else 'no'}
Planted in conditions: sun={sun}, soil={soil}, wind={wind}
Notes: {row.get('notes') or 'none'}
Season: {season}, Date: {today.strftime('%d %B %Y')}
{wx_block}"""

SYSTEM_CARE = """You are an expert gardener specialising in Sofia, Bulgaria (continental climate: hot dry summers, cold winters, frosts Oct–Apr possible).
You give PRACTICAL, SPECIFIC, weather-aware organic gardening advice.

For each plant, provide a structured response in this EXACT format with these section headers:

PRUNING: When and how to prune, taking current season/weather into account. Specific months.
FEEDING: Which biological soil boosters to use (worm castings, compost tea, seaweed, nettle tea, Biobizz, etc.), when, and how often.
WATERING: How much and how often, adjusted for current weather conditions. Note if irrigation is needed NOW based on the weather data.
BULB_CARE: (Only if it's a bulb/corm/tuber) When to lift, how to store for winter, when to replant. Skip this section otherwise.
PLACEMENT: Assess if the sun/soil/wind conditions match the plant's needs. If placement is WRONG, say clearly: "⚠️ UNSUITABLE — [reason]" and recommend whether to REMOVE or REPLANT, and when is the safest time to do it.
ALTERNATIVES: (Only if placement is UNSUITABLE) List 3 plants that WOULD thrive in those exact conditions.

Keep each section to 2–4 sentences. Be specific with calendar months."""

# ── Session state ──────────────────────────────────────────────────────────────
if "plants_df" not in st.session_state:
    st.session_state.plants_df = None
if "advice_cache" not in st.session_state:
    st.session_state.advice_cache = {}
if "wx" not in st.session_state:
    st.session_state.wx = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 Garden Planner")
    st.caption("Sofia, Bulgaria — Continental climate")
    st.divider()

    tab_choice = st.radio(
        "Navigate",
        ["🌤️ Dashboard", "📋 Plant Advice", "📤 Upload Plants", "🤖 Ask AI"],
        label_visibility="collapsed"
    )
    st.divider()

    # ── Persistent sidebar uploader ───────────────────────────────────────────
    plant_count = len(st.session_state.plants_df) if st.session_state.plants_df is not None else 0
    if plant_count:
        st.success(f"✅ {plant_count} plants loaded")
        if st.button("↩️ Replace plant list", use_container_width=True):
            st.session_state.plants_df = None
            st.session_state.advice_cache = {}
            st.rerun()
    else:
        st.markdown("**📂 Load your plants:**")
        sidebar_upload = st.file_uploader(
            "CSV or XLSX",
            type=["csv", "xlsx", "xls"],
            key="sidebar_uploader",
            label_visibility="collapsed",
        )
        if sidebar_upload:
            parsed_df, error = parse_upload(sidebar_upload)
            if error:
                st.error(f"❌ {error}")
            else:
                st.session_state.plants_df = parsed_df
                st.session_state.advice_cache = {}
                st.rerun()
    st.divider()

    # Weather refresh
    if st.button("🔄 Refresh Weather", use_container_width=True):
        st.cache_data.clear()
        st.session_state.wx = None

    if st.session_state.wx is None:
        with st.spinner("Fetching Sofia weather..."):
            raw = fetch_weather()
            st.session_state.wx = weather_summary(raw)

    wx = st.session_state.wx
    if wx.get("ok"):
        st.markdown(f"**{wx['temp_now']}°C** · {wx['desc_now']}")
        st.caption(f"Min {wx['temp_min_today']}°C · Max {wx['temp_max_today']}°C · UV {wx['uv_today']}")
        if wx["frost_risk"]:
            st.warning(f"❄️ Frost expected: {', '.join(wx['frost_days'])}")
    else:
        st.warning("Weather unavailable offline — advice will still work.")

    st.divider()
    today = st.date_input("📅 Date", value=date.today())

df = st.session_state.plants_df
wx = st.session_state.wx or {"ok": False}

# ══════════════════════════════════════════════════════════════════════════════
# TAB: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if tab_choice == "🌤️ Dashboard":
    st.markdown("# 🌿 Garden Dashboard")

    # Weather bar
    if wx.get("ok"):
        frost_txt  = f"❄️ Frost in {len(wx['frost_days'])}d" if wx["frost_risk"] else "✅ No frost this week"
        water_txt  = "💧 Water needed" if wx["soil_dry"] else "🌧️ Soil OK"
        st.markdown(f"""
        <div class="wx-bar">
          <div class="wx-item"><div class="wx-val">{wx['temp_now']}°C</div><div class="wx-lbl">Now</div></div>
          <div class="wx-item"><div class="wx-val">{wx['temp_max_today']}° / {wx['temp_min_today']}°</div><div class="wx-lbl">Today max/min</div></div>
          <div class="wx-item"><div class="wx-val">{wx['uv_today']}</div><div class="wx-lbl">UV Index</div></div>
          <div class="wx-item"><div class="wx-val">{wx['rain_today']} mm</div><div class="wx-lbl">Rain today</div></div>
          <div class="wx-item"><div class="wx-val">{wx['weekly_rain_mm']:.0f} mm</div><div class="wx-lbl">7-day rain</div></div>
          <div class="wx-item"><div class="wx-val">{wx['desc_now']}</div><div class="wx-lbl">Conditions</div></div>
          <div class="wx-alert">{frost_txt} &nbsp;·&nbsp; {water_txt}</div>
        </div>
        """, unsafe_allow_html=True)

        # 7-day mini forecast
        st.markdown('<div class="sec-hdr">7-Day Forecast</div>', unsafe_allow_html=True)
        cols = st.columns(7)
        for i, col in enumerate(cols):
            d_label = datetime.strptime(wx["dates"][i], "%Y-%m-%d").strftime("%a %d")
            icon = "🌧️" if wx["rain"][i] > 5 else ("❄️" if wx["mins"][i] <= 0 else ("☀️" if wx["codes"][i] <= 2 else "⛅"))
            col.markdown(f"**{d_label}**")
            col.markdown(f"{icon} {wx['maxs'][i]:.0f}°/{wx['mins'][i]:.0f}°")
            if wx["rain"][i] > 0:
                col.caption(f"💧{wx['rain'][i]:.0f}mm")
    else:
        st.info("⚡ Weather data unavailable — check your internet connection and refresh.")

    st.divider()

    # Plant summary
    if df is None:
        st.markdown("### 📂 Start by uploading your plant list")
        st.caption("Upload a CSV or XLSX — only `name` and `zone` columns are required.")
        dash_upload = st.file_uploader(
            "Drop your file here", type=["csv","xlsx","xls"], key="dash_uploader"
        )
        if dash_upload:
            parsed_df, error = parse_upload(dash_upload)
            if error:
                st.error(f"❌ {error}")
            else:
                st.session_state.plants_df = parsed_df
                st.session_state.advice_cache = {}
                st.rerun()
        st.stop()
    else:
        n_zones  = df["zone"].nunique()
        n_bulbs  = df["is_bulb"].sum()
        st.markdown(f"**{len(df)} plants** across **{n_zones} zones** · {int(n_bulbs)} bulbs/corms")

        # Weather alerts relevant to garden
        if wx.get("ok"):
            st.markdown('<div class="sec-hdr">🔔 Weather-Based Alerts</div>', unsafe_allow_html=True)
            alerts = []
            if wx["frost_risk"]:
                bulbs_at_risk = df[df["is_bulb"] == True]["name"].tolist()
                if bulbs_at_risk:
                    alerts.append(f"❄️ **Frost expected** — protect or lift these bulbs: {', '.join(bulbs_at_risk)}")
                alerts.append("❄️ Do not prune anything frost-sensitive this week.")
            if wx["soil_dry"]:
                alerts.append("💧 **Soil is dry** — water deeply, preferably in early morning or evening.")
            if wx["uv_today"] >= 7:
                alerts.append("☀️ **High UV today** — avoid transplanting or dividing plants. Water early.")
            if any(r >= 10 for r in wx["rain"]):
                alerts.append("🌧️ Heavy rain forecast — skip feeding this week; nutrients will wash out.")
            if not alerts:
                alerts.append("✅ No urgent weather alerts — good week for routine garden tasks.")
            for a in alerts:
                st.markdown(f"- {a}")

        # Zone overview
        st.markdown('<div class="sec-hdr">🗂️ Zones at a Glance</div>', unsafe_allow_html=True)
        for zone in sorted(df["zone"].unique()):
            zone_df = df[df["zone"] == zone]
            plant_list = ", ".join(zone_df["name"].tolist())
            st.markdown(f"**{zone}** · {len(zone_df)} plant{'s' if len(zone_df)>1 else ''}: {plant_list}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB: PLANT ADVICE
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "📋 Plant Advice":
    st.markdown("# 📋 Plant Care Advice")

    if df is None:
        st.markdown("### 📂 Upload your plant list to get started")
        adv_upload = st.file_uploader(
            "Drop your CSV or XLSX here", type=["csv","xlsx","xls"], key="adv_uploader"
        )
        if adv_upload:
            parsed_df, error = parse_upload(adv_upload)
            if error:
                st.error(f"❌ {error}")
            else:
                st.session_state.plants_df = parsed_df
                st.session_state.advice_cache = {}
                st.rerun()
        st.stop()
    else:
        # Zone filter
        zones = ["All zones"] + sorted(df["zone"].unique().tolist())
        selected_zone = st.selectbox("Filter by zone", zones)
        filtered_df = df if selected_zone == "All zones" else df[df["zone"] == selected_zone]

        # Bulk generate button
        col_btn, col_info = st.columns([2, 3])
        generate_all = col_btn.button("🤖 Generate advice for all plants", use_container_width=True)
        col_info.caption(f"Generates AI advice for {len(filtered_df)} plant(s). Takes ~5–10s per plant.")

        if generate_all:
            progress = st.progress(0, text="Generating advice...")
            for i, (_, row) in enumerate(filtered_df.iterrows()):
                key = row["name"]
                if key not in st.session_state.advice_cache:
                    try:
                        prompt = build_plant_prompt(row, wx, today)
                        advice = ask_claude(SYSTEM_CARE, prompt)
                        st.session_state.advice_cache[key] = advice
                    except Exception as e:
                        st.session_state.advice_cache[key] = f"Error: {e}"
                progress.progress((i + 1) / len(filtered_df), text=f"Done: {row['name']}")
            progress.empty()
            st.success("✅ All advice generated!")

        st.divider()

        # Per-plant cards
        for _, row in filtered_df.iterrows():
            plant_name = row["name"]
            has_advice = plant_name in st.session_state.advice_cache

            with st.expander(
                f"{'✅' if has_advice else '○'} **{plant_name}** — {row['zone']}"
                + (" 🫙" if row.get("is_bulb") else ""),
                expanded=False
            ):
                # Condition badges
                sun_v  = str(row.get("sun")  or "")
                soil_v = str(row.get("soil") or "")
                wind_v = str(row.get("wind") or "")

                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Sun:** {SUN_LABELS.get(sun_v, sun_v or '—')}")
                c2.markdown(f"**Soil:** {SOIL_LABELS.get(soil_v, soil_v or '—')}")
                c3.markdown(f"**Wind:** {WIND_LABELS.get(wind_v, wind_v or '—')}")
                if row.get("latin"):
                    st.caption(f"*{row['latin']}*")
                if row.get("notes"):
                    st.caption(f"📝 {row['notes']}")

                # Generate button for individual plant
                if not has_advice:
                    if st.button(f"🤖 Get advice for {plant_name}", key=f"gen_{plant_name}"):
                        with st.spinner(f"Analysing {plant_name}..."):
                            try:
                                prompt = build_plant_prompt(row, wx, today)
                                advice = ask_claude(SYSTEM_CARE, prompt)
                                st.session_state.advice_cache[plant_name] = advice
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                else:
                    advice_text = st.session_state.advice_cache[plant_name]

                    # Parse sections for colour-coded display
                    sections = {
                        "PRUNING":    ("✂️ Pruning",    "#eaf2e0", "#2c5015"),
                        "FEEDING":    ("🌿 Feeding",    "#f0f7e8", "#1a5226"),
                        "WATERING":   ("💧 Watering",   "#e8f3fb", "#1a3a5c"),
                        "BULB_CARE":  ("🫙 Bulb Care",  "#fef9e8", "#5c4a00"),
                        "PLACEMENT":  ("📍 Placement",  "#fff8f0", "#7a3000"),
                        "ALTERNATIVES":("🌱 Alternatives","#f3eeff","#3a1a7a"),
                    }

                    parsed = {}
                    current = None
                    for line in advice_text.split("\n"):
                        matched = False
                        for key in sections:
                            if line.strip().startswith(key + ":"):
                                current = key
                                parsed[key] = line.split(":", 1)[1].strip() if ":" in line else ""
                                matched = True
                                break
                        if not matched and current and line.strip():
                            parsed[current] = parsed.get(current, "") + "\n" + line.strip()

                    if parsed:
                        for sec_key, (sec_title, bg, fg) in sections.items():
                            if sec_key in parsed and parsed[sec_key].strip():
                                text = parsed[sec_key].strip()
                                # Flag unsuitable placement
                                border = "2px solid #e74c3c" if "UNSUITABLE" in text and sec_key == "PLACEMENT" else "none"
                                st.markdown(f"""
                                <div style="background:{bg};border-radius:8px;padding:12px 16px;
                                            margin-bottom:8px;border:{border}">
                                  <div style="font-weight:600;color:{fg};margin-bottom:5px">{sec_title}</div>
                                  <div style="font-size:0.87rem;color:#333;line-height:1.6">{text}</div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        # Fallback: show raw text
                        st.markdown(f'<div class="ai-box">{advice_text}</div>', unsafe_allow_html=True)

                    if st.button("🔄 Regenerate", key=f"regen_{plant_name}"):
                        del st.session_state.advice_cache[plant_name]
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB: UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "📤 Upload Plants":
    st.markdown("# 📤 Upload Your Plant List")

    st.markdown("""
    <div class="col-hint">
    <b>Required columns:</b> name, zone<br>
    <b>Optional columns:</b> latin, sun, soil, wind, is_bulb, notes<br><br>
    <b>sun values:</b> full_sun | partial_shade | full_shade<br>
    <b>soil values:</b> well_drained | moist | clay | sandy | rich<br>
    <b>wind values:</b> sheltered | tolerant | exposed<br>
    <b>is_bulb:</b> yes / no (or true/false/1/0)
    </div>
    """, unsafe_allow_html=True)

    # Download template
    template_df = pd.DataFrame([
        {"name":"Lavender","latin":"Lavandula angustifolia","zone":"Terrace Pots",
         "sun":"full_sun","soil":"well_drained","wind":"tolerant","is_bulb":"no","notes":"Purple variety"},
        {"name":"Ranunculus","latin":"Ranunculus asiaticus","zone":"Front Bed",
         "sun":"full_sun","soil":"well_drained","wind":"sheltered","is_bulb":"yes","notes":"Pink mix"},
        {"name":"Hosta","latin":"Hosta sieboldiana","zone":"Back Corner",
         "sun":"full_shade","soil":"moist","wind":"sheltered","is_bulb":"no","notes":"Blue-green leaves"},
    ])
    csv_bytes = template_df.to_csv(index=False).encode()
    st.download_button(
        "⬇️ Download CSV template",
        data=csv_bytes,
        file_name="garden_plants_template.csv",
        mime="text/csv",
        use_container_width=False,
    )

    st.divider()

    uploaded = st.file_uploader(
        "Upload your plant file",
        type=["csv", "xlsx", "xls"],
        help="CSV or Excel file with your plant list"
    )

    if uploaded:
        parsed_df, error = parse_upload(uploaded)
        if error:
            st.error(f"❌ {error}")
        else:
            st.success(f"✅ Loaded **{len(parsed_df)} plants** from {uploaded.name}")
            st.dataframe(parsed_df, use_container_width=True, hide_index=True)

            # Validate sun/soil/wind values
            issues = []
            for col, valid in [("sun", SUN_OPTIONS), ("soil", SOIL_OPTIONS), ("wind", WIND_OPTIONS)]:
                if col in parsed_df.columns:
                    bad = parsed_df[parsed_df[col].notna() & ~parsed_df[col].isin(valid)][["name", col]]
                    if not bad.empty:
                        for _, r in bad.iterrows():
                            issues.append(f"Row '{r['name']}': unrecognised {col} value '{r[col]}' — will be treated as unspecified")
            if issues:
                st.warning("⚠️ Some values were not recognised:\n" + "\n".join(f"- {i}" for i in issues))

            if st.button("✅ Use this plant list", use_container_width=True, type="primary"):
                st.session_state.plants_df   = parsed_df
                st.session_state.advice_cache = {}
                st.success("Plant list loaded! Go to **Plant Advice** to generate care plans.")

    # Manual entry expander
    with st.expander("➕ Or add a single plant manually"):
        with st.form("manual_add"):
            r1, r2 = st.columns(2)
            m_name  = r1.text_input("Plant name *")
            m_latin = r2.text_input("Latin name")
            m_zone  = st.text_input("Zone / Bed *", placeholder="e.g. Front Bed, Terrace Pots")
            r3, r4, r5 = st.columns(3)
            m_sun   = r3.selectbox("Sun conditions",  [""] + SUN_OPTIONS,  format_func=lambda x: SUN_LABELS.get(x, x or "— not set —"))
            m_soil  = r4.selectbox("Soil conditions", [""] + SOIL_OPTIONS, format_func=lambda x: SOIL_LABELS.get(x, x or "— not set —"))
            m_wind  = r5.selectbox("Wind exposure",   [""] + WIND_OPTIONS, format_func=lambda x: WIND_LABELS.get(x, x or "— not set —"))
            m_bulb  = st.checkbox("🫙 Bulb / corm / tuber")
            m_notes = st.text_area("Notes", height=70)
            if st.form_submit_button("Add plant", use_container_width=True):
                if not m_name or not m_zone:
                    st.error("Name and zone are required.")
                else:
                    new_row = pd.DataFrame([{
                        "name": m_name.strip(), "latin": m_latin.strip(),
                        "zone": m_zone.strip(), "sun": m_sun or None,
                        "soil": m_soil or None, "wind": m_wind or None,
                        "is_bulb": m_bulb, "notes": m_notes.strip(),
                    }])
                    if st.session_state.plants_df is None:
                        st.session_state.plants_df = new_row
                    else:
                        st.session_state.plants_df = pd.concat(
                            [st.session_state.plants_df, new_row], ignore_index=True
                        )
                    st.success(f"✅ Added {m_name} to {m_zone}!")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB: ASK AI
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "🤖 Ask AI":
    st.markdown("# 🤖 Ask the Garden Advisor")
    st.caption("Ask anything — planting timing, companion plants, pest problems, organic feeds, winter protection…")

    plant_options = ["— general question —"]
    if df is not None:
        plant_options += df["name"].tolist()

    selected = st.selectbox("Context plant (optional)", plant_options)
    question = st.text_area(
        "Your question",
        height=110,
        placeholder=(
            "When should I lift my Ranunculus corms?\n"
            "What biological fertiliser works best for roses in Sofia?\n"
            "My lavender is yellowing — what's wrong?"
        ),
    )

    # Quick question chips
    st.markdown("**Quick questions:**")
    quick = [
        "What should I be doing in my garden this week?",
        "Which plants survive Sofia winters without protection?",
        "Best biological soil boosters for containers?",
        "When is the last safe date to plant bulbs?",
        "How to protect plants from late spring frost?",
    ]
    qcols = st.columns(3)
    for i, q in enumerate(quick):
        if qcols[i % 3].button(q, key=f"q{i}"):
            question = q

    if st.button("🤖 Ask", use_container_width=True) and question.strip():
        ctx = ""
        if selected != "— general question —" and df is not None:
            row = df[df["name"] == selected].iloc[0]
            ctx = build_plant_prompt(row, wx, today) + "\n\n"
        elif wx.get("ok"):
            ctx = (
                f"Garden in Sofia, Bulgaria. Today: {today.strftime('%d %B %Y')}. "
                f"Weather: {wx['temp_now']}°C, {wx['desc_now']}, "
                f"weekly rain {wx['weekly_rain_mm']:.0f}mm, "
                f"frost risk: {'yes' if wx['frost_risk'] else 'no'}.\n\n"
            )

        system = (
            "You are an expert organic gardener specialising in Sofia, Bulgaria (continental climate). "
            "Give practical, specific advice with exact calendar months. "
            "Recommend only biological/organic products. Keep answers under 250 words."
        )
        with st.spinner("Consulting the garden oracle…"):
            try:
                answer = ask_claude(system, ctx + question)
                st.markdown(f'<div class="ai-box">{answer}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not reach AI: {e}")
