import streamlit as st
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🌿 Garden Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

PLANTS_FILE = Path(__file__).parent / "plants.json"

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

h1, h2, h3 { font-family: 'Playfair Display', serif !important; }

.main { background-color: #f9f6f0; }

/* Task cards */
.task-card {
    background: white;
    border-left: 5px solid #6b8f4e;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
.task-card.urgent { border-left-color: #c0392b; }
.task-card.soon   { border-left-color: #e67e22; }
.task-card.info   { border-left-color: #2980b9; }

.task-plant  { font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 600; color: #2c3e1a; }
.task-action { font-size: 0.9rem; color: #555; margin-top: 3px; }
.task-date   { font-size: 0.8rem; color: #888; margin-top: 4px; }
.task-zone   { display:inline-block; background:#eaf2e0; color:#4a6e2a;
               border-radius:20px; padding:2px 10px; font-size:0.75rem; margin-top:6px; }

/* Warning cards */
.warn-card {
    background: #fff8f0;
    border: 1px solid #f0a500;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.warn-title { font-weight: 600; color: #c0392b; font-size: 1rem; }
.warn-advice { font-size: 0.88rem; color: #555; margin-top: 5px; }

/* Plant row */
.plant-row {
    background: white;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    display: flex;
    align-items: center;
    gap: 12px;
}

/* Metric pills */
.pill {
    display: inline-block;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 500;
}
.pill-green  { background:#eaf2e0; color:#3d6b1e; }
.pill-yellow { background:#fef9e0; color:#9a6b00; }
.pill-red    { background:#fdecea; color:#a02020; }
.pill-blue   { background:#e8f3fb; color:#1a5276; }

/* Section header */
.section-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    color: #2c3e1a;
    border-bottom: 2px solid #d4e6c0;
    padding-bottom: 6px;
    margin-bottom: 16px;
}

/* Today banner */
.today-banner {
    background: linear-gradient(135deg, #3d6b1e 0%, #6b8f4e 100%);
    color: white;
    border-radius: 12px;
    padding: 18px 24px;
    margin-bottom: 24px;
}
.today-banner h2 { color: white !important; margin: 0; }
.today-banner p  { color: rgba(255,255,255,0.85); margin: 4px 0 0 0; font-size: 0.9rem; }

/* AI response box */
.ai-box {
    background: #f0f7e8;
    border: 1px solid #b8d89a;
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 12px;
    font-size: 0.9rem;
    line-height: 1.6;
    white-space: pre-wrap;
}
</style>
""", unsafe_allow_html=True)

# ── Data helpers ──────────────────────────────────────────────────────────────

SUN_LABELS    = {"full_sun": "☀️ Full Sun", "partial_shade": "⛅ Partial Shade", "full_shade": "🌑 Full Shade"}
SOIL_LABELS   = {"well_drained": "🪨 Well Drained", "moist": "💧 Moist", "clay": "🟤 Clay", "sandy": "🏖 Sandy", "rich": "🌱 Rich"}
WIND_LABELS   = {"sheltered": "🏠 Sheltered", "tolerant": "💨 Tolerant", "exposed": "🌬️ Exposed"}

SUN_OPTIONS   = list(SUN_LABELS.keys())
SOIL_OPTIONS  = list(SOIL_LABELS.keys())
WIND_OPTIONS  = list(WIND_LABELS.keys())

def load_plants():
    if PLANTS_FILE.exists():
        with open(PLANTS_FILE) as f:
            return json.load(f)
    return []

def save_plants(plants):
    with open(PLANTS_FILE, "w", encoding="utf-8") as f:
        json.dump(plants, f, ensure_ascii=False, indent=2)

def next_id(plants):
    return max((p["id"] for p in plants), default=0) + 1

# ── Care schedule logic ───────────────────────────────────────────────────────

def get_care_tasks(plant: dict, today: date) -> list[dict]:
    """Generate rule-based care tasks for the next 90 days."""
    tasks = []
    month = today.month
    name = plant["name"]
    zone = plant["zone"]
    is_bulb = plant.get("is_bulb", False)

    def add(action, target_month, target_day=15, category="general", urgency="soon"):
        target = date(today.year, target_month, min(target_day, 28))
        if target < today:
            target = date(today.year + 1, target_month, min(target_day, 28))
        days_away = (target - today).days
        if 0 <= days_away <= 90:
            tasks.append({
                "plant": name, "zone": zone, "action": action,
                "date": target, "days_away": days_away,
                "category": category,
                "urgency": "urgent" if days_away <= 7 else ("soon" if days_away <= 21 else "info")
            })

    # Pruning
    if any(x in name.lower() for x in ["rose", "lavender", "shrub", "buddleia"]):
        add("✂️ Prune back hard — late winter cut to encourage new growth", 3, 10, "pruning")
        add("✂️ Deadhead spent flowers to extend blooming", 7, 1, "pruning")
    elif any(x in name.lower() for x in ["hosta", "fern", "perennial"]):
        add("✂️ Cut back old foliage to ground level before new growth emerges", 3, 1, "pruning")
    else:
        add("✂️ Light tidy-up — remove dead stems and spent growth", 3, 15, "pruning")

    # Feeding
    add("🌿 Feed with worm castings or compost tea — spring root booster", 4, 1, "feeding")
    add("🌿 Apply slow-release biological fertiliser (e.g. Biobizz Grow)", 5, 15, "feeding")
    add("🌿 Mid-summer feed — liquid seaweed or nettle tea", 7, 1, "feeding")

    # Bulb-specific tasks
    if is_bulb:
        if any(x in name.lower() for x in ["dahlia", "canna", "gladiolus", "begonia"]):
            add("🫙 Lift bulbs after first frost — dry, dust with sulphur, store in cool dark place", 10, 20, "bulb", "urgent")
            add("🌱 Re-plant tubers once soil warms above 10°C", 4, 15, "bulb")
        elif any(x in name.lower() for x in ["ranunculus"]):
            add("🫙 Lift corms after foliage yellows — store dry in paper bag in cool dark spot", 6, 10, "bulb")
            add("🌱 Pre-soak corms 4h in water, then plant 5cm deep with claws down", 10, 1, "bulb")
        elif any(x in name.lower() for x in ["tulip", "daffodil", "narcissus", "allium"]):
            add("🍂 Allow foliage to die back naturally — do not cut for 6 weeks after flowering", 5, 15, "bulb")
            add("🌱 Plant new bulbs at 3× their own depth", 10, 10, "bulb")
            add("🫙 Optionally lift and dry bulbs for summer storage in shaded ventilated spot", 7, 1, "bulb")

    # Watering reminder at season start
    if month <= 4:
        add("💧 Start regular watering schedule as temperatures rise", 4, 10, "watering")

    return sorted(tasks, key=lambda t: t["date"])


def check_placement(plant: dict) -> list[dict]:
    """Compare plant needs vs actual garden conditions and return warnings + advice."""
    warnings = []
    name = plant["name"]

    needed_sun  = plant.get("sun", "")
    actual_sun  = plant.get("actual_sun", "")
    needed_soil = plant.get("soil", "")
    actual_soil = plant.get("actual_soil", "")
    needed_wind = plant.get("wind_exposure", "")
    actual_wind = plant.get("actual_wind", "")

    # Sun mismatch
    sun_order = ["full_shade", "partial_shade", "full_sun"]
    if needed_sun in sun_order and actual_sun in sun_order:
        diff = sun_order.index(actual_sun) - sun_order.index(needed_sun)
        if diff >= 1:
            warnings.append({
                "issue": f"☀️ Too much sun for {name}",
                "detail": f"Needs {SUN_LABELS[needed_sun]} but planted in {SUN_LABELS[actual_sun]}.",
                "advice": "Move to a north-facing bed, under a pergola, or near a taller plant that provides afternoon shade. Best time to transplant: early spring (March–April) or early autumn (September).",
            })
        elif diff <= -1:
            warnings.append({
                "issue": f"🌑 Too little sun for {name}",
                "detail": f"Needs {SUN_LABELS[needed_sun]} but planted in {SUN_LABELS[actual_sun]}.",
                "advice": "Relocate to a south- or west-facing spot that gets 6+ hours of direct light. Transplant in early spring before active growth starts.",
            })

    # Wind mismatch
    wind_order = ["sheltered", "tolerant", "exposed"]
    if needed_wind in wind_order and actual_wind in wind_order:
        diff = wind_order.index(actual_wind) - wind_order.index(needed_wind)
        if diff >= 1:
            warnings.append({
                "issue": f"🌬️ Too exposed to wind for {name}",
                "detail": f"Prefers {WIND_LABELS[needed_wind]} but is in a {WIND_LABELS[actual_wind]} spot.",
                "advice": "Install a windbreak (willow hurdle, dense hedge, or trellis) or move behind an existing shelter. Transplant in calm, overcast weather in spring.",
            })

    # Soil mismatch
    if needed_soil and actual_soil and needed_soil != actual_soil:
        if needed_soil == "well_drained" and actual_soil in ("moist", "clay"):
            warnings.append({
                "issue": f"💧 Soil too wet for {name}",
                "detail": f"Needs {SOIL_LABELS[needed_soil]} but soil is {SOIL_LABELS.get(actual_soil, actual_soil)}.",
                "advice": "Amend bed with 30% horticultural grit + perlite, or raise the bed by 20 cm. For pots, use a free-draining terracotta mix. Best done in autumn.",
            })
        elif needed_soil in ("moist", "rich") and actual_soil in ("well_drained", "sandy"):
            warnings.append({
                "issue": f"🏜️ Soil too dry/poor for {name}",
                "detail": f"Needs {SOIL_LABELS[needed_soil]} but soil is {SOIL_LABELS.get(actual_soil, actual_soil)}.",
                "advice": "Work in generous amounts of compost and leaf mould to improve water retention. Mulch heavily each spring with 5 cm of bark or compost.",
            })

    return warnings

# ── AI helper ─────────────────────────────────────────────────────────────────

def ask_claude(prompt: str) -> str:
    """Call Claude API for plant-specific advice."""
    import urllib.request
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())
    return data["content"][0]["text"]

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🌿 Garden Planner")
    st.markdown("*Sofia, Bulgaria — Continental climate*")
    st.divider()
    tab_choice = st.radio("Navigate", ["📋 Dashboard", "🪴 My Plants", "➕ Add Plant", "🤖 AI Advisor"], label_visibility="collapsed")
    st.divider()
    today = st.date_input("📅 Today's date", value=date.today())
    st.caption(f"Season: {'🌱 Spring' if today.month in [3,4,5] else '☀️ Summer' if today.month in [6,7,8] else '🍂 Autumn' if today.month in [9,10,11] else '❄️ Winter'}")

plants = load_plants()

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
if tab_choice == "📋 Dashboard":
    st.markdown(f"""
    <div class="today-banner">
      <h2>🌿 Garden Dashboard</h2>
      <p>{today.strftime('%A, %d %B %Y')} · {len(plants)} plants across {len(set(p['zone'] for p in plants))} zones</p>
    </div>
    """, unsafe_allow_html=True)

    if not plants:
        st.info("No plants yet — add some in the **➕ Add Plant** tab!")
    else:
        # Collect all tasks
        all_tasks = []
        for p in plants:
            all_tasks.extend(get_care_tasks(p, today))
        all_tasks.sort(key=lambda t: t["date"])

        # Collect all warnings
        all_warnings = []
        for p in plants:
            for w in check_placement(p):
                w["plant"] = p["name"]
                w["zone"] = p["zone"]
                all_warnings.append(w)

        col1, col2, col3, col4 = st.columns(4)
        urgent = [t for t in all_tasks if t["urgency"] == "urgent"]
        soon   = [t for t in all_tasks if t["urgency"] == "soon"]
        col1.metric("🔴 Urgent (≤7 days)",  len(urgent))
        col2.metric("🟠 Soon (≤21 days)",   len(soon))
        col3.metric("⚠️ Placement issues",  len(all_warnings))
        col4.metric("🌱 Total tasks (90d)", len(all_tasks))

        st.divider()

        # Tasks
        col_tasks, col_warn = st.columns([3, 2])

        with col_tasks:
            st.markdown('<div class="section-header">📅 Upcoming Care Tasks</div>', unsafe_allow_html=True)
            filter_cat = st.multiselect(
                "Filter by category",
                ["pruning", "feeding", "bulb", "watering", "general"],
                default=["pruning", "feeding", "bulb", "watering", "general"],
                key="cat_filter"
            )
            shown = [t for t in all_tasks if t["category"] in filter_cat]
            if not shown:
                st.info("No tasks in selected categories for the next 90 days.")
            for t in shown[:20]:
                days_txt = "Today!" if t["days_away"] == 0 else (f"In {t['days_away']} day{'s' if t['days_away']>1 else ''}")
                st.markdown(f"""
                <div class="task-card {t['urgency']}">
                  <div class="task-plant">{t['plant']}</div>
                  <div class="task-action">{t['action']}</div>
                  <div class="task-date">📅 {t['date'].strftime('%d %b %Y')} &nbsp;·&nbsp; {days_txt}</div>
                  <span class="task-zone">{t['zone']}</span>
                </div>
                """, unsafe_allow_html=True)

        with col_warn:
            st.markdown('<div class="section-header">⚠️ Placement Warnings</div>', unsafe_allow_html=True)
            if not all_warnings:
                st.success("✅ All plants are well-placed!")
            for w in all_warnings:
                st.markdown(f"""
                <div class="warn-card">
                  <div class="warn-title">{w['issue']}</div>
                  <div class="warn-advice"><b>{w['plant']}</b> · <i>{w['zone']}</i><br>{w['detail']}<br><br>💡 {w['advice']}</div>
                </div>
                """, unsafe_allow_html=True)

# ── MY PLANTS ──────────────────────────────────────────────────────────────────
elif tab_choice == "🪴 My Plants":
    st.markdown("## 🪴 My Plants")

    if not plants:
        st.info("No plants yet — add some in the **➕ Add Plant** tab!")
    else:
        zones = sorted(set(p["zone"] for p in plants))
        selected_zone = st.selectbox("Filter by zone", ["All zones"] + zones)
        filtered = plants if selected_zone == "All zones" else [p for p in plants if p["zone"] == selected_zone]

        for p in filtered:
            warnings = check_placement(p)
            warn_badge = f"⚠️ {len(warnings)} issue{'s' if len(warnings)>1 else ''}" if warnings else "✅ Well placed"
            bulb_badge = "🫙 Bulb" if p.get("is_bulb") else ""

            with st.expander(f"**{p['name']}** — {p['zone']}  &nbsp; {warn_badge}  {bulb_badge}"):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Needs:** {SUN_LABELS.get(p.get('sun',''), p.get('sun',''))}")
                c2.markdown(f"**Actual:** {SUN_LABELS.get(p.get('actual_sun',''), p.get('actual_sun',''))}")
                c3.markdown(f"**Soil:** {SOIL_LABELS.get(p.get('soil',''), p.get('soil',''))}")
                c1.markdown(f"**Wind needs:** {WIND_LABELS.get(p.get('wind_exposure',''), p.get('wind_exposure',''))}")
                c2.markdown(f"**Wind actual:** {WIND_LABELS.get(p.get('actual_wind',''), p.get('actual_wind',''))}")
                c3.markdown(f"**Planted:** {p.get('planted_date','—')}")
                if p.get("notes"):
                    st.caption(f"📝 {p['notes']}")

                if warnings:
                    for w in warnings:
                        st.warning(f"**{w['issue']}** — {w['detail']}\n\n💡 {w['advice']}")

                # Tasks for this plant
                tasks = get_care_tasks(p, today)
                if tasks:
                    st.markdown("**Upcoming tasks (next 90 days):**")
                    for t in tasks[:5]:
                        st.markdown(f"- {t['action']} · *{t['date'].strftime('%d %b')}*")

                # Edit & Delete
                col_edit, col_del = st.columns([1, 1])
                if col_del.button("🗑️ Delete", key=f"del_{p['id']}"):
                    plants = [x for x in plants if x["id"] != p["id"]]
                    save_plants(plants)
                    st.rerun()

# ── ADD PLANT ──────────────────────────────────────────────────────────────────
elif tab_choice == "➕ Add Plant":
    st.markdown("## ➕ Add a New Plant")

    with st.form("add_plant_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name         = c1.text_input("Plant name *", placeholder="e.g. Lavender")
        latin        = c2.text_input("Latin name", placeholder="e.g. Lavandula angustifolia")
        zone         = st.text_input("Zone / Bed name *", placeholder="e.g. Front Bed, Terrace Pots, Shaded Corner")
        is_bulb      = st.checkbox("🫙 This is a bulb / corm / tuber")
        planted_date = st.date_input("Date planted", value=date.today())
        notes        = st.text_area("Notes", placeholder="Colour, variety, source...")

        st.markdown("**Plant requirements (what it needs):**")
        r1, r2, r3 = st.columns(3)
        sun_need  = r1.selectbox("Sun",  SUN_OPTIONS,  format_func=lambda x: SUN_LABELS[x],  key="sun_need")
        soil_need = r2.selectbox("Soil", SOIL_OPTIONS, format_func=lambda x: SOIL_LABELS[x], key="soil_need")
        wind_need = r3.selectbox("Wind", WIND_OPTIONS, format_func=lambda x: WIND_LABELS[x], key="wind_need")

        st.markdown("**Actual conditions where it's planted:**")
        a1, a2, a3 = st.columns(3)
        actual_sun  = a1.selectbox("Actual sun",  SUN_OPTIONS,  format_func=lambda x: SUN_LABELS[x],  key="actual_sun")
        actual_soil = a2.selectbox("Actual soil", SOIL_OPTIONS, format_func=lambda x: SOIL_LABELS[x], key="actual_soil")
        actual_wind = a3.selectbox("Actual wind", WIND_OPTIONS, format_func=lambda x: WIND_LABELS[x], key="actual_wind")

        submitted = st.form_submit_button("🌱 Add Plant", use_container_width=True)
        if submitted:
            if not name or not zone:
                st.error("Plant name and zone are required.")
            else:
                new_plant = {
                    "id": next_id(plants),
                    "name": name.strip(),
                    "latin": latin.strip(),
                    "zone": zone.strip(),
                    "sun": sun_need,
                    "soil": soil_need,
                    "wind_exposure": wind_need,
                    "is_bulb": is_bulb,
                    "planted_date": str(planted_date),
                    "notes": notes.strip(),
                    "actual_sun": actual_sun,
                    "actual_soil": actual_soil,
                    "actual_wind": actual_wind,
                }
                plants.append(new_plant)
                save_plants(plants)
                st.success(f"✅ **{name}** added to **{zone}**!")
                warnings = check_placement(new_plant)
                if warnings:
                    for w in warnings:
                        st.warning(f"⚠️ {w['issue']}: {w['advice']}")

# ── AI ADVISOR ────────────────────────────────────────────────────────────────
elif tab_choice == "🤖 AI Advisor":
    st.markdown("## 🤖 AI Plant Advisor")
    st.caption("Ask anything about your plants — care, timing, problems, pairings.")

    if not plants:
        st.info("Add some plants first so the advisor can give personalised advice.")
    else:
        plant_names = [p["name"] for p in plants]
        selected_plant_name = st.selectbox("Ask about a specific plant (or ask general)", ["— general question —"] + plant_names)

        if selected_plant_name != "— general question —":
            plant_ctx = next((p for p in plants if p["name"] == selected_plant_name), None)
            ctx_str = (
                f"Plant: {plant_ctx['name']} ({plant_ctx.get('latin','')})\n"
                f"Zone: {plant_ctx['zone']}\n"
                f"Needs: {plant_ctx['sun']} sun, {plant_ctx['soil']} soil, {plant_ctx['wind_exposure']} wind\n"
                f"Planted in: {plant_ctx['sun']} sun, {plant_ctx['soil']} soil, {plant_ctx['wind_exposure']} wind\n"
                f"Is bulb: {plant_ctx.get('is_bulb', False)}\n"
                f"Notes: {plant_ctx.get('notes','')}\n"
            )
        else:
            ctx_str = f"Garden in Sofia, Bulgaria. Plants: {', '.join(plant_names)}."

        question = st.text_area(
            "Your question",
            placeholder="When should I lift the Ranunculus corms? What biological feed works best for Lavender? Can I plant Hostas next to Tulips?",
            height=100,
        )

        quick_qs = [
            "When is the best time to divide this plant?",
            "What biological soil boosters work best?",
            "How do I save the bulbs for winter?",
            "What companion plants would work well nearby?",
        ]
        st.markdown("**Quick questions:**")
        cols = st.columns(len(quick_qs))
        for i, qq in enumerate(quick_qs):
            if cols[i].button(qq, key=f"qq_{i}"):
                question = qq

        if st.button("🤖 Ask Claude", use_container_width=True) and question:
            system = (
                "You are an expert gardener specialising in Bulgarian continental climate gardens (Sofia region). "
                "You give practical, specific, organic/biological gardening advice. "
                "Keep answers concise — 150 words max. Use bullet points where helpful. "
                "Always mention the best calendar month for any action."
            )
            full_prompt = f"Context:\n{ctx_str}\n\nQuestion: {question}"
            with st.spinner("Consulting the garden oracle..."):
                try:
                    answer = ask_claude(f"{system}\n\n{full_prompt}")
                    st.markdown(f'<div class="ai-box">{answer}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not reach AI: {e}")
