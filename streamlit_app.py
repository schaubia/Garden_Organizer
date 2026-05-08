"""🌿 Garden Planner — works for any location worldwide"""
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
.stButton > button[kind="secondary"] { background:#e8e4dc;color:#2c3e1a; }
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
.care-card { border-radius:10px;padding:13px 16px;margin-bottom:6px; }
.care-title { font-weight:600;font-size:0.85rem;margin-bottom:4px; }
.care-body { font-size:0.84rem;color:#333;line-height:1.58; }
.task-now { background:#fff3cd;border-left:4px solid #e6a817;border-radius:8px;padding:10px 14px;margin-bottom:7px; }
.task-now-name { font-weight:600;color:#1a3a0e;font-size:0.9rem; }
.task-now-body { font-size:0.83rem;color:#555;margin-top:3px; }
.plant-header { font-family:'Cormorant Garamond',serif;font-size:1.05rem;font-weight:600;color:#1a3a0e; }
.ai-box { background:#f0f7e8;border:1px solid #b8d89a;border-radius:10px;padding:16px 20px;margin-top:10px;font-size:0.88rem;line-height:1.65;white-space:pre-wrap; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
WMO = {0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",45:"Foggy",
       51:"Light drizzle",53:"Drizzle",61:"Slight rain",63:"Rain",65:"Heavy rain",
       71:"Slight snow",73:"Snow",80:"Rain showers",82:"Violent showers",95:"Thunderstorm"}
SUN_OPTIONS  = {"full_sun":"☀️ Full sun","partial_shade":"⛅ Partial shade","full_shade":"🌑 Full shade"}
SOIL_OPTIONS = {"well_drained":"🪨 Well drained","moist":"💧 Moist","clay":"🟤 Clay","sandy":"🏖 Sandy","rich":"🌱 Rich"}
SUN_NORM = {"full_sun":"full_sun","full sun":"full_sun","partial_shade":"partial_shade",
            "partial sun":"partial_shade","partial shade":"partial_shade",
            "half shade":"partial_shade","half_shade":"partial_shade",
            "full_shade":"full_shade","full shade":"full_shade","shade":"full_shade"}
MONTH_NAMES = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
               7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

# ── Care database ──────────────────────────────────────────────────────────────
CARE_DB = {
    "Juglans":    {"pruning":"Late winter (Feb–Mar): remove dead/crossing branches. Avoid cutting in spring — bleeds sap.","feeding":"Apr: compost mulch around base. Jun: liquid seaweed once.","watering":"Deep water weekly in dry summers. Drought-tolerant once established.","pruning_months":"2,3","feeding_months":"4,6","water_freq":"weekly_summer"},
    "Cornus":     {"pruning":"Mar: cut coloured-stem varieties hard to ground for bright new growth.","feeding":"Apr: worm castings around base. Jun: compost tea.","watering":"Moderate. Water in dry spells, especially first 2 years.","pruning_months":"3","feeding_months":"4,6","water_freq":"moderate"},
    "Mespilus":   {"pruning":"Feb–Mar: thin canopy, remove inward growth.","feeding":"Apr: balanced compost. No high-nitrogen.","watering":"Drought-tolerant when established. Water young trees weekly.","pruning_months":"2,3","feeding_months":"4","water_freq":"low"},
    "Ginkgo":     {"pruning":"Nov–Feb: remove dead wood only. Minimal pruning needed.","feeding":"Apr: slow-release organic fertiliser once a year.","watering":"Drought-tolerant. Water weekly first season only.","pruning_months":"11,12,1,2","feeding_months":"4","water_freq":"low"},
    "Cydonia":    {"pruning":"Feb–Mar: open up centre for airflow and light.","feeding":"Mar: compost mulch. May: liquid seaweed.","watering":"Water well during fruit development (Jun–Aug).","pruning_months":"2,3","feeding_months":"3,5","water_freq":"moderate"},
    "Crataegus":  {"pruning":"Feb–Mar or after flowering (Jun): shape and thin.","feeding":"Apr: light compost mulch.","watering":"Very drought-tolerant. Water only in extreme heat.","pruning_months":"2,3,6","feeding_months":"4","water_freq":"low"},
    "Cotoneaster":{"pruning":"Mar or Aug: light trim for shape.","feeding":"Apr: compost mulch once.","watering":"Drought-tolerant. Water young plants in dry spells.","pruning_months":"3,8","feeding_months":"4","water_freq":"low"},
    "Chamaecyparis":{"pruning":"Apr–May: light shaping only, never cut into old brown wood.","feeding":"Apr: slow-release conifer fertiliser.","watering":"Regular water in first year. Drought-tolerant after.","pruning_months":"4,5","feeding_months":"4","water_freq":"low"},
    "Corylus":    {"pruning":"Feb–Mar: remove oldest stems at base every 3 years for rejuvenation.","feeding":"Mar: compost mulch. May: seaweed foliar spray.","watering":"Moderate. Water in dry spells.","pruning_months":"2,3","feeding_months":"3,5","water_freq":"moderate"},
    "Rhamnus":    {"pruning":"Mar: light shaping. Tolerates hard pruning.","feeding":"Apr: compost mulch.","watering":"Very drought-tolerant once established.","pruning_months":"3","feeding_months":"4","water_freq":"low"},
    "Salvia":     {"pruning":"Mar–Apr: cut back by 1/3 after winter. Deadhead through summer.","feeding":"Apr: worm castings. Avoid high nitrogen — reduces aroma.","watering":"Drought-tolerant. Water deeply once a week in summer.","pruning_months":"3,4","feeding_months":"4","water_freq":"weekly_summer"},
    "Thymus":     {"pruning":"Apr–May: light trim after flowering to keep compact. Never cut old wood.","feeding":"Apr: light compost. Very low feeder.","watering":"Very drought-tolerant. Overwatering is the main killer.","pruning_months":"4,5","feeding_months":"4","water_freq":"very_low"},
    "Melissa":    {"pruning":"Jun: cut to ground after first flowering — promotes fresh flush. Cut again in Aug.","feeding":"Apr: compost mulch. May: diluted nettle tea.","watering":"Moderate. Keep moist but not waterlogged.","pruning_months":"6,8","feeding_months":"4,5","water_freq":"moderate"},
    "Mentha":     {"pruning":"Jun and Aug: cut hard to ground to prevent flowering and keep bushy.","feeding":"May: nettle tea or compost tea monthly.","watering":"Keep consistently moist. Dries out fast in containers.","pruning_months":"6,8","feeding_months":"5,6,7,8","water_freq":"high"},
    "Parthenocissus":{"pruning":"Mar: cut back hard from gutters/windows. Shape in Aug if needed.","feeding":"Apr: compost mulch at base. Jun: liquid seaweed.","watering":"Moderate. Self-sufficient once established.","pruning_months":"3,8","feeding_months":"4,6","water_freq":"low"},
    "Lonicera":   {"pruning":"Mar: remove 1/3 oldest stems. Tidy after flowering (Jun).","feeding":"Apr: compost mulch. Jun: balanced liquid feed.","watering":"Moderate. Keep moist in summer.","pruning_months":"3,6","feeding_months":"4,6","water_freq":"moderate"},
    "Hedera":     {"pruning":"Mar–Apr: cut back hard if overgrown. Light trim any time.","feeding":"Apr: balanced compost. Tolerates poor soil.","watering":"Drought-tolerant once established. Water young plants regularly.","pruning_months":"3,4","feeding_months":"4","water_freq":"low"},
    "Campsis":    {"pruning":"Feb–Mar: cut all side shoots back to 2–3 buds. Essential for flowering.","feeding":"Apr: high-potassium feed (seaweed). Avoid nitrogen — causes leafy growth, fewer flowers.","watering":"Drought-tolerant. Water weekly in extreme heat only.","pruning_months":"2,3","feeding_months":"4,5","water_freq":"low"},
    "Clematis":   {"pruning":"Feb–Mar (Group 3): cut hard to 30cm from ground. Check your variety group.","feeding":"Mar: worm castings. Apr–Jul: liquid seaweed every 2 weeks.","watering":"Keep roots cool and moist. Mulch heavily. Water 2× week in summer.","pruning_months":"2,3","feeding_months":"3,4,5,6,7","water_freq":"moderate"},
    "Jasminum":   {"pruning":"After flowering (Aug–Sep): thin out oldest stems by 1/3.","feeding":"Apr: balanced compost. Jun: liquid seaweed.","watering":"Moderate. Drought-tolerant when established.","pruning_months":"8,9","feeding_months":"4,6","water_freq":"moderate"},
    "Viburnum":   {"pruning":"After flowering (Jun–Jul): light shaping only.","feeding":"Apr: compost mulch. Jun: liquid seaweed.","watering":"Moderate. Water in dry spells, especially in flower.","pruning_months":"6,7","feeding_months":"4,6","water_freq":"moderate"},
    "Pyracantha": {"pruning":"Apr: trim new growth back to 2–3 leaves. Aug: repeat light trim.","feeding":"Mar: compost mulch. Avoid high nitrogen — reduces berries.","watering":"Moderate once established. Water young plants weekly.","pruning_months":"4,8","feeding_months":"3","water_freq":"moderate"},
    "Mahonia":    {"pruning":"After flowering (Apr–May): remove oldest stems at base every 2–3 years.","feeding":"Mar: compost mulch. Very unfussy feeder.","watering":"Drought-tolerant. Water during establishment.","pruning_months":"4,5","feeding_months":"3","water_freq":"low"},
    "Euonymus":   {"pruning":"Mar–Apr: shape as needed. Tolerates hard pruning.","feeding":"Apr: balanced compost mulch.","watering":"Moderate. Drought-tolerant when established.","pruning_months":"3,4","feeding_months":"4","water_freq":"low"},
    "Rosa":       {"pruning":"Mar: main prune — cut to outward-facing bud, remove dead wood. Deadhead Jun–Sep.","feeding":"Mar: worm castings. May & Jul: high-potassium seaweed feed. Stop feeding Jul.","watering":"Deep water twice weekly in summer. Avoid wetting foliage.","pruning_months":"3,6,7,8,9","feeding_months":"3,5,7","water_freq":"twice_weekly_summer"},
    "Ligustrum":  {"pruning":"May–Jun and Aug: clip 2× a year. Hard renovate in Mar if overgrown.","feeding":"Apr: balanced compost mulch.","watering":"Drought-tolerant once established.","pruning_months":"3,5,6,8","feeding_months":"4","water_freq":"low"},
    "Berberis":   {"pruning":"After flowering (Jun): remove oldest stems. Wear gloves — thorns.","feeding":"Apr: compost mulch.","watering":"Very drought-tolerant.","pruning_months":"6","feeding_months":"4","water_freq":"low"},
    "Callicarpa": {"pruning":"Mar: cut hard to 30–40cm — promotes fruiting wood.","feeding":"Apr: worm castings. Jun: seaweed.","watering":"Moderate. Keep moist in summer for best berry set.","pruning_months":"3","feeding_months":"4,6","water_freq":"moderate"},
    "Weigela":    {"pruning":"After flowering (Jun–Jul): remove 1/3 oldest stems at base.","feeding":"Apr: compost mulch. Jun: liquid seaweed.","watering":"Moderate. Water during dry spells.","pruning_months":"6,7","feeding_months":"4,6","water_freq":"moderate"},
    "Spiraea":    {"pruning":"Mar: cut hard to ground. After flowering (Jul): deadhead.","feeding":"Apr: balanced compost.","watering":"Moderate.","pruning_months":"3,7","feeding_months":"4","water_freq":"moderate"},
    "Deutzia":    {"pruning":"After flowering (Jun–Jul): cut flowered stems back to strong new growth.","feeding":"Apr: compost mulch. Jun: seaweed.","watering":"Moderate. Keep moist in flower.","pruning_months":"6,7","feeding_months":"4,6","water_freq":"moderate"},
    "Hibiscus":   {"pruning":"Apr: cut back frost-damaged tips. Light shape only.","feeding":"May: high-potassium feed. Jun–Aug: seaweed monthly.","watering":"Regular watering May–Sep. Reduce in autumn.","pruning_months":"4","feeding_months":"5,6,7,8","water_freq":"regular_summer"},
    "Pinus":      {"pruning":"May–Jun: pinch back candles by 1/2 to control size. No hard pruning.","feeding":"Apr: slow-release conifer food once.","watering":"Drought-tolerant. Water young plants only.","pruning_months":"5,6","feeding_months":"4","water_freq":"low"},
    "Juniperus":  {"pruning":"Apr–May: light shaping only. Never cut into old brown wood.","feeding":"Apr: slow-release granular fertiliser.","watering":"Drought-tolerant.","pruning_months":"4,5","feeding_months":"4","water_freq":"low"},
    "Echinacea":  {"pruning":"Mar: cut old stems to ground. Leave seed heads over winter for birds.","feeding":"Apr: worm castings. Jun: compost tea.","watering":"Drought-tolerant once established. Water weekly first season.","pruning_months":"3","feeding_months":"4,6","water_freq":"low"},
    "Rudbeckia":  {"pruning":"Mar: cut to ground. Can leave for winter wildlife.","feeding":"Apr: balanced compost. Jun: seaweed foliar.","watering":"Moderate. Water in dry spells.","pruning_months":"3","feeding_months":"4,6","water_freq":"moderate"},
    "Lupinus":    {"pruning":"After flowering (Jun): deadhead to encourage second flush. Cut to ground in Oct.","feeding":"Apr: low-nitrogen — lupins fix their own nitrogen.","watering":"Moderate. Dislikes waterlogging.","pruning_months":"6,10","feeding_months":"4","water_freq":"moderate"},
    "Paeonia":    {"pruning":"Oct–Nov: cut stems to 10cm after frost. Do not cut in spring — harms flowering.","feeding":"Mar: worm castings. May: seaweed after flowering.","watering":"Deep weekly watering in May–Jun. Drought-tolerant after.","pruning_months":"10,11","feeding_months":"3,5","water_freq":"weekly_flowering"},
    "Hydrangea":  {"pruning":"Mar: remove old flowerheads to first pair of fat buds. Don't prune in autumn.","feeding":"Apr: high-potassium feed. Jun: liquid seaweed.","watering":"Keep consistently moist. Water daily in summer heat.","pruning_months":"3","feeding_months":"4,6","water_freq":"daily_summer"},
    "Stachys":    {"pruning":"Mar: remove winter-damaged leaves. Deadhead flower spikes in Jul if unwanted.","feeding":"Apr: light compost. Very low feeder.","watering":"Drought-tolerant. Overwatering causes rot.","pruning_months":"3,7","feeding_months":"4","water_freq":"very_low"},
    "Hosta":      {"pruning":"Oct–Nov: cut all foliage to ground after frost. Mar: remove slug-damaged leaves.","feeding":"Apr: slow-release balanced feed or worm castings.","watering":"Keep consistently moist. Water 3× week in summer.","pruning_months":"3,10,11","feeding_months":"4","water_freq":"high_summer"},
    "Convallaria":{"pruning":"Oct: cut back yellowed foliage after it dies down naturally.","feeding":"Mar: thin layer of leaf mould or compost. Very low feeder.","watering":"Keep moist. Water weekly in dry weather.","pruning_months":"10","feeding_months":"3","water_freq":"moderate"},
    "Bergenia":   {"pruning":"Mar: remove winter-damaged or tatty old leaves. Deadhead after flowering.","feeding":"Apr: light compost mulch once.","watering":"Low once established. Water young plants regularly.","pruning_months":"3","feeding_months":"4","water_freq":"low"},
    "Sempervivum":{"pruning":"Remove dead rosettes after flowering. No other pruning.","feeding":"Apr: very light grit/sand top-dressing. Minimal feeding — rich soil causes rot.","watering":"Extremely drought-tolerant. Water only in severe drought.","pruning_months":"6,7","feeding_months":"4","water_freq":"very_low"},
    "Vinca":      {"pruning":"Mar–Apr: cut hard to ground to rejuvenate. Can be aggressive spreader.","feeding":"Apr: light compost mulch.","watering":"Low once established.","pruning_months":"3,4","feeding_months":"4","water_freq":"low"},
    "Festuca":    {"pruning":"Mar: comb out dead grass with fingers. Every 3 years: divide clumps.","feeding":"Apr: light slow-release granular. Avoid rich compost.","watering":"Drought-tolerant. Water monthly in extreme heat only.","pruning_months":"3","feeding_months":"4","water_freq":"very_low"},
    "Phlox":      {"pruning":"Oct: cut to ground. Divide clumps every 3 years in Mar.","feeding":"Apr: worm castings. Jun: seaweed foliar spray.","watering":"Keep moist in summer. Water 2–3× week in heat.","pruning_months":"10","feeding_months":"4,6","water_freq":"moderate"},
    "Allium":     {"pruning":"Allow foliage to die back fully (6 weeks after flowering) before removing.","feeding":"Mar: worm castings at planting or top-dress established clumps.","watering":"Water after planting. Drought-tolerant once established.","pruning_months":"6,7","feeding_months":"3","water_freq":"low"},
    "Dahlia":     {"pruning":"Deadhead regularly Jun–Oct. Cut to ground after first frost (Oct–Nov).","feeding":"Jun: high-potassium feed (seaweed or tomato feed) every 2 weeks until Sep.","watering":"Water deeply 2× week in summer. Keep evenly moist.","pruning_months":"6,7,8,9,10","feeding_months":"6,7,8,9","water_freq":"twice_weekly_summer"},
    "Gladiolus":  {"pruning":"After flowering: cut stem leaving 4 leaves. Remove foliage after yellowing.","feeding":"Jun: seaweed or balanced liquid feed when 30cm tall.","watering":"Water well from planting until flowering. Reduce after.","pruning_months":"8,9","feeding_months":"6,7","water_freq":"moderate"},
    "Tulipa":     {"pruning":"After flowering: deadhead but allow foliage to die back naturally (6 weeks).","feeding":"Mar: balanced granular. After flowering: liquid seaweed.","watering":"Water after planting. Minimal in summer — bulbs need to bake dry.","pruning_months":"5,6","feeding_months":"3,5","water_freq":"low_summer"},
    "Hyacinthus": {"pruning":"After flowering: deadhead. Allow foliage to die back. Lift and dry Jun–Jul.","feeding":"Mar: balanced fertiliser as shoots emerge.","watering":"Water during growth. Dry out completely in summer.","pruning_months":"4,5","feeding_months":"3","water_freq":"low_summer"},
    "Ranunculus": {"pruning":"After flowering: allow foliage to yellow, then remove. Lift corms Jun.","feeding":"Mar–Apr: liquid seaweed every 2 weeks during active growth.","watering":"Water regularly during growth (Mar–Jun). Stop completely when dormant.","pruning_months":"5,6","feeding_months":"3,4,5","water_freq":"regular_growing"},
    "Muscari":    {"pruning":"After flowering (Apr–May): allow leaves to die back naturally.","feeding":"Sep–Oct at planting: bone meal in hole.","watering":"Minimal. Water only after planting.","pruning_months":"5,6","feeding_months":"9,10","water_freq":"very_low"},
    "Scilla":     {"pruning":"After flowering: allow foliage to die back naturally.","feeding":"Sep: bone meal at planting.","watering":"Minimal. Self-sufficient.","pruning_months":"4,5","feeding_months":"9","water_freq":"very_low"},
    "Iris":       {"pruning":"After flowering (Jun–Jul): cut flower stems. Tidy fans in Sep. Divide every 3–4 years.","feeding":"Mar: low-nitrogen fertiliser. May: high-potassium after flowering.","watering":"Moderate during growth. Dry in summer — rhizomes need sun to bake.","pruning_months":"6,7,9","feeding_months":"3,5","water_freq":"low_summer"},
    "Aubrieta":   {"pruning":"After flowering (May): cut hard back by 2/3 to keep compact.","feeding":"Mar: light balanced fertiliser.","watering":"Drought-tolerant. Water lightly in extreme heat.","pruning_months":"5","feeding_months":"3","water_freq":"very_low"},
    "Iberis":     {"pruning":"After flowering (May–Jun): cut back by 1/3 to maintain shape.","feeding":"Mar: light compost.","watering":"Low. Drought-tolerant once established.","pruning_months":"5,6","feeding_months":"3","water_freq":"very_low"},
    "Cerastium":  {"pruning":"After flowering (Jun): cut back hard to prevent spreading.","feeding":"Apr: very light compost. Thrives in poor soil.","watering":"Very drought-tolerant.","pruning_months":"6","feeding_months":"4","water_freq":"very_low"},
    "Leontopodium":{"pruning":"Mar: remove dead stems. Minimal.","feeding":"Apr: very light compost or rock dust. Poor soil preferred.","watering":"Very drought-tolerant. Hates wet feet.","pruning_months":"3","feeding_months":"4","water_freq":"very_low"},
    "Santolina":  {"pruning":"Mar–Apr: cut back by half. After flowering (Aug): deadhead.","feeding":"Apr: light compost. Avoid rich feeding.","watering":"Very drought-tolerant.","pruning_months":"3,4,8","feeding_months":"4","water_freq":"very_low"},
    "Calluna":    {"pruning":"Mar: trim lightly after flowering. Avoid cutting into old wood.","feeding":"Apr: ericaceous fertiliser (acid-loving). No lime.","watering":"Keep moist but well-drained. Dislikes drought.","pruning_months":"3","feeding_months":"4","water_freq":"moderate"},
    "Aeonium":    {"pruning":"Remove dead rosettes. Minimal.","feeding":"Apr: light succulent fertiliser.","watering":"Water spring–autumn. Dry rest in summer. Frost-tender — protect below 5°C.","pruning_months":"","feeding_months":"4","water_freq":"low"},
    "Callocephalus":{"pruning":"Mar–Apr: light trim to shape.","feeding":"Apr: light compost.","watering":"Low.","pruning_months":"3,4","feeding_months":"4","water_freq":"low"},
    "Calendula":  {"pruning":"Deadhead continuously (Jun–Oct) to extend flowering. Self-seeds freely.","feeding":"Apr at sowing: light compost. Monthly liquid seaweed.","watering":"Moderate. Water regularly to extend flowering season.","pruning_months":"6,7,8,9,10","feeding_months":"4,5,6,7,8,9","water_freq":"moderate"},
    "Eschscholzia":{"pruning":"Deadhead to prevent excessive self-seeding, or allow to naturalise.","feeding":"Thrives in poor soil — no feeding needed.","watering":"Very drought-tolerant. Water only at sowing.","pruning_months":"6,7,8","feeding_months":"","water_freq":"very_low"},
    "Bellis":     {"pruning":"Deadhead regularly (Mar–Jun) to prolong flowering.","feeding":"Mar: light balanced compost.","watering":"Keep moist during flowering.","pruning_months":"3,4,5,6","feeding_months":"3","water_freq":"moderate"},
    "Antirrhinum":{"pruning":"Pinch tips at 10cm for bushier plants. Deadhead through summer.","feeding":"May: balanced liquid feed every 2 weeks.","watering":"Keep moist. Dislikes drought.","pruning_months":"5,6,7,8,9","feeding_months":"5,6,7,8","water_freq":"moderate"},
    "Actinidia":  {"pruning":"Feb–Mar: cut side shoots to 2–3 buds. Summer: remove excess growth.","feeding":"Mar: worm castings. May: seaweed.","watering":"Moderate–high. Water 2× week in summer for fruit.","pruning_months":"2,3,7","feeding_months":"3,5","water_freq":"moderate"},
    "Prunus":     {"pruning":"Mar–Apr: trim after flowering. Hard prune if overgrown — tolerates it well.","feeding":"Apr: compost mulch. Jun: balanced liquid feed.","watering":"Moderate. Water young plants regularly. Drought-tolerant once established.","pruning_months":"3,4","feeding_months":"4,6","water_freq":"moderate"},
}
DEFAULT_CARE = {"pruning":"Mar: general tidy — remove dead/damaged stems.","feeding":"Apr: worm castings or compost mulch. Jun: liquid seaweed.","watering":"Water moderately during dry periods, especially summer.","pruning_months":"3","feeding_months":"4,6","water_freq":"moderate"}

def lookup_care(latin):
    if not latin or str(latin).lower() in ("nan","none",""):
        return DEFAULT_CARE
    for genus, care in CARE_DB.items():
        if genus.lower() in str(latin).lower():
            return care
    return DEFAULT_CARE

def months_list(months_str):
    if not months_str or str(months_str).lower() in ("nan","none",""):
        return []
    try:
        return [int(m.strip()) for m in str(months_str).split(",") if m.strip()]
    except:
        return []

def tasks_this_month(df, month):
    """Return list of (name, task_type, description) due this month."""
    tasks = []
    for _, row in df.iterrows():
        name = row["name"]
        care = lookup_care(row.get("latin"))
        if month in months_list(row.get("pruning_months") or care["pruning_months"]):
            tasks.append((name, "✂️ Pruning", row.get("pruning") or care["pruning"]))
        if month in months_list(row.get("feeding_months") or care["feeding_months"]):
            tasks.append((name, "🌿 Feeding", row.get("feeding") or care["feeding"]))
        if row.get("is_bulb") and month in [10, 11]:
            tasks.append((name, "🫙 Bulb care", f"Check if {name} bulbs need lifting before first frost."))
        if row.get("is_bulb") and month in [3, 4]:
            tasks.append((name, "🌱 Bulb planting", f"Check if {name} bulbs/corms are ready to plant out."))
    return tasks

# ── Weather ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def geocode_location(city_name: str):
    """Geocode a city name using Open-Meteo geocoding API."""
    import urllib.parse
    url = (f"https://geocoding-api.open-meteo.com/v1/search"
           f"?name={urllib.parse.quote(city_name)}&count=1&language=en&format=json")
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"GardenPlanner/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        if not data.get("results"):
            return {"error": f"Location '{city_name}' not found."}
        r = data["results"][0]
        return {
            "name":     r["name"],
            "country":  r.get("country", ""),
            "region":   r.get("admin1", ""),
            "lat":      r["latitude"],
            "lon":      r["longitude"],
            "timezone": r.get("timezone", "UTC"),
            "elevation":r.get("elevation", 0),
        }
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600)
def fetch_weather(lat: float, lon: float, timezone: str):
    import urllib.parse
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,uv_index_max,weathercode"
           f"&current_weather=true&timezone={urllib.parse.quote(timezone)}&forecast_days=7")
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"GardenPlanner/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def detect_climate(lat: float, avg_min_winter: float, avg_max_summer: float) -> str:
    """Infer a broad climate description from coordinates and seasonal temps."""
    if lat > 60:
        return "subarctic/nordic (long cold winters, short cool summers)"
    if avg_min_winter <= -5 and avg_max_summer >= 28:
        return "continental (cold winters with frost, hot dry summers)"
    if avg_min_winter <= 0 and avg_max_summer >= 22:
        return "temperate continental (cold winters, warm summers)"
    if avg_min_winter > 8 and avg_max_summer > 28:
        return "mediterranean (mild wet winters, hot dry summers)"
    if avg_min_winter > 10 and avg_max_summer > 32:
        return "subtropical/warm (mild winters, very hot summers)"
    if avg_min_winter < -15:
        return "cold continental (very cold winters, warm short summers)"
    return "temperate oceanic (mild winters, cool summers, year-round rain)"

def parse_weather(raw):
    if "error" in raw: return {"ok":False}
    try:
        cw=raw["current_weather"]; d=raw["daily"]
        mins=d["temperature_2m_min"]; maxs=d["temperature_2m_max"]
        rain=d["precipitation_sum"]; uv=d["uv_index_max"]
        codes=d["weathercode"]; dates=d["time"]
        return {"ok":True,"temp_now":cw["temperature"],"desc_now":WMO.get(cw["weathercode"],"Unknown"),
                "temp_max":maxs[0],"temp_min":mins[0],"uv":uv[0],"rain_today":rain[0],
                "weekly_rain":sum(rain),"frost_risk":any(t<=0 for t in mins),
                "frost_days":[dates[i] for i,t in enumerate(mins) if t<=0],
                "soil_dry":sum(rain)<5 and sum(maxs)/len(maxs)>15,
                "heavy_rain":any(r>=10 for r in rain),
                "dates":dates,"mins":mins,"maxs":maxs,"rain":rain,"uv_all":uv,"codes":codes}
    except: return {"ok":False}

# ── File parser ────────────────────────────────────────────────────────────────
def parse_upload(f):
    try:
        nm = f.name.lower()
        df = pd.read_csv(f) if nm.endswith(".csv") else pd.read_excel(f)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        df = df.where(pd.notna(df), None)
        sun_vals_set = set(SUN_NORM.keys())
        if "sun_needed" in df.columns: sun_col = "sun_needed"
        elif "zone" in df.columns and df["zone"].dropna().astype(str).str.lower().str.strip().isin(sun_vals_set).mean() > 0.4: sun_col = "zone"
        elif "sun" in df.columns: sun_col = "sun"
        else: return None, "Need a column with light requirements (sun_needed, sun, or zone with sun values)."
        df["sun_needed"] = df[sun_col].astype(str).str.strip().str.lower().map(SUN_NORM)
        for drop_col in ["zone","sun"]:
            if drop_col in df.columns and drop_col != sun_col: df = df.drop(columns=[drop_col])
        if sun_col in df.columns and sun_col != "sun_needed": df = df.drop(columns=[sun_col])
        if "actual_sun" not in df.columns: df["actual_sun"] = None
        if "name" not in df.columns: return None, "Missing required 'name' column."
        df["name"] = df["name"].astype(str).str.strip()
        for col in ["latin","soil","wind","notes","pruning","feeding","watering",
                    "pruning_months","feeding_months","water_freq"]:
            if col not in df.columns: df[col] = None
        df["is_bulb"] = df.get("is_bulb", pd.Series([False]*len(df))).apply(
            lambda x: str(x).strip().lower() in ("yes","true","1","да") if x else False)
        # Fill missing care data from DB
        for i, row in df.iterrows():
            if not row.get("pruning"):
                care = lookup_care(row.get("latin"))
                df.at[i,"pruning"]        = care["pruning"]
                df.at[i,"feeding"]        = care["feeding"]
                df.at[i,"watering"]       = care["watering"]
                df.at[i,"pruning_months"] = care["pruning_months"]
                df.at[i,"feeding_months"] = care["feeding_months"]
                df.at[i,"water_freq"]     = care["water_freq"]
        return df, ""
    except Exception as e:
        return None, str(e)

def sun_mismatch(needed, actual):
    order = ["full_shade","partial_shade","full_sun"]
    if not needed or not actual or needed not in order or actual not in order: return None
    diff = order.index(actual) - order.index(needed)
    if diff >= 1: return "over"
    if diff <= -1: return "under"
    return None

# ── Claude API removed ───────────────────────────────────────────────────────



def render_tasks_by_type(tasks, month_name=""):
    """Render tasks grouped by type in side-by-side coloured tables."""
    from collections import defaultdict
    grouped = defaultdict(list)
    for name, task_type, desc in tasks:
        grouped[task_type].append((name, desc))

    TYPE_STYLE = {
        "✂️ Pruning":       ("#eaf2e0", "#2c5015"),
        "🌿 Feeding":       ("#f0f7e8", "#1a5226"),
        "💧 Watering":      ("#e8f3fb", "#1a3a5c"),
        "🫙 Bulb care":     ("#fef9e8", "#5c4a00"),
        "🌱 Bulb planting": ("#f3eeff", "#3a1a7a"),
    }

    # Only render types that have tasks
    active_types = [t for t in TYPE_STYLE if t in grouped]
    if not active_types:
        st.success(f"✅ No scheduled tasks{' for ' + month_name if month_name else ''}.")
        return

    cols = st.columns(len(active_types))
    for col, task_type in zip(cols, active_types):
        bg, fg = TYPE_STYLE[task_type]
        rows_html = "".join(
            f'''<tr>
              <td style="padding:7px 10px;border-bottom:1px solid {bg};font-weight:600;
                         color:#1a3a0e;font-size:0.85rem;vertical-align:top;width:35%">{name}</td>
              <td style="padding:7px 10px;border-bottom:1px solid {bg};color:#444;
                         font-size:0.82rem;line-height:1.5;vertical-align:top">{desc}</td>
            </tr>'''
            for name, desc in grouped[task_type]
        )
        col.markdown(f'''
        <div style="background:{bg};border-radius:10px;overflow:hidden;height:100%">
          <div style="background:{fg};color:white;padding:10px 14px;font-weight:600;
                      font-size:0.95rem;font-family:Cormorant Garamond,serif;letter-spacing:0.02em">
            {task_type} <span style="opacity:0.75;font-size:0.8rem;font-weight:400">
              ({len(grouped[task_type])} plant{"s" if len(grouped[task_type])>1 else ""})</span>
          </div>
          <table style="width:100%;border-collapse:collapse">{rows_html}</table>
        </div>''', unsafe_allow_html=True)

def require_plants():
    if st.session_state.plants_df is None:
        st.info("📂 Upload your plant list using the uploader in the **sidebar on the left**.")
        st.stop()

# ── Session state initialisation ──────────────────────────────────────────────
for k, v in [
    ("plants_df",    None),
    ("wx",           None),
    ("location",     {"name":"Sofia","country":"Bulgaria","region":"Sofia-Capital",
                      "lat":42.698,"lon":23.322,"timezone":"Europe/Sofia","elevation":550}),
    ("climate_desc", "continental (cold winters with frost, hot dry summers)"),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 Garden Planner")
    loc = st.session_state.location
    st.caption(f"{loc['name']}, {loc['country']}")
    st.divider()

    tab_choice = st.radio("Navigate",
        ["🌤️ Dashboard","☀️ Sun Setup","📋 Care Schedule","⬇️ CSV Template"],
        label_visibility="collapsed")
    st.divider()

    # ── Plant list status ─────────────────────────────────────────────────────
    plant_count = len(st.session_state.plants_df) if st.session_state.plants_df is not None else 0
    if plant_count:
        n_set = int((st.session_state.plants_df["actual_sun"].notna() &
                     (st.session_state.plants_df["actual_sun"] != "")).sum())
        st.success(f"✅ {plant_count} plants loaded")
        st.caption(f"☀️ {n_set}/{plant_count} sun positions set")
        if st.button("↩️ Replace plant list", use_container_width=True):
            st.session_state.plants_df = None
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
                st.rerun()
    st.divider()

    # ── Location search ───────────────────────────────────────────────────────
    with st.expander("📍 Change location"):
        city_input = st.text_input("City name", placeholder="e.g. London, Paris, Plovdiv…",
                                   key="city_input")
        if st.button("🔍 Search", use_container_width=True) and city_input:
            with st.spinner(f"Searching for {city_input}…"):
                geo = geocode_location(city_input)
                if "error" in geo:
                    st.error(geo["error"])
                else:
                    st.session_state.location = geo
                    st.session_state.wx = None
                    st.rerun()

    # ── Weather ───────────────────────────────────────────────────────────────
    if st.button("🔄 Refresh Weather", use_container_width=True):
        st.cache_data.clear()
        st.session_state.wx = None

    loc = st.session_state.location
    if st.session_state.wx is None:
        with st.spinner(f"Fetching weather for {loc['name']}…"):
            raw = fetch_weather(loc["lat"], loc["lon"], loc["timezone"])
            st.session_state.wx = parse_weather(raw)
            wx_data = st.session_state.wx
            if wx_data.get("ok"):
                avg_min = min(wx_data["mins"])
                avg_max = max(wx_data["maxs"])
                st.session_state.climate_desc = detect_climate(loc["lat"], avg_min, avg_max)

    wx = st.session_state.wx
    if wx.get("ok"):
        st.markdown(f"**{wx['temp_now']}°C** · {wx['desc_now']}")
        st.caption(f"↑{wx['temp_max']}° ↓{wx['temp_min']}° · UV {wx['uv']} · 🌧️ {wx['rain_today']}mm")
        if wx["frost_risk"]:
            st.warning(f"❄️ Frost: {', '.join(wx['frost_days'])}")
    else:
        st.caption("Weather unavailable")
    st.divider()
    today = st.date_input("📅 Date", value=date.today())

df = st.session_state.plants_df
wx = st.session_state.wx or {"ok": False}

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if tab_choice == "🌤️ Dashboard":
    st.markdown("# 🌿 Garden Dashboard")
    loc = st.session_state.location
    if wx.get("ok"):
        st.markdown(f"""<div class="wx-bar">
          <div class="wx-item"><div class="wx-val">{wx['temp_now']}°C</div><div class="wx-lbl">Now · {loc['name']}</div></div>
          <div class="wx-item"><div class="wx-val">{wx['temp_max']}° / {wx['temp_min']}°</div><div class="wx-lbl">Today</div></div>
          <div class="wx-item"><div class="wx-val">{wx['uv']}</div><div class="wx-lbl">UV Index</div></div>
          <div class="wx-item"><div class="wx-val">{wx['rain_today']} mm</div><div class="wx-lbl">Rain today</div></div>
          <div class="wx-item"><div class="wx-val">{wx['weekly_rain']:.0f} mm</div><div class="wx-lbl">7-day rain</div></div>
          <div class="wx-item"><div class="wx-val">{wx['desc_now']}</div><div class="wx-lbl">Conditions</div></div>
          <div class="wx-alert">{"❄️ Frost "+', '.join(wx['frost_days']) if wx['frost_risk'] else '✅ No frost'} &nbsp;·&nbsp; {"💧 Water needed" if wx['soil_dry'] else "🌧️ Soil OK"}</div>
        </div>""", unsafe_allow_html=True)
        cols = st.columns(7)
        for i,col in enumerate(cols):
            dl = datetime.strptime(wx["dates"][i],"%Y-%m-%d").strftime("%a %d")
            icon = "❄️" if wx["mins"][i]<=0 else ("🌧️" if wx["rain"][i]>5 else ("☀️" if wx["codes"][i]<=2 else "⛅"))
            col.markdown(f"**{dl}**"); col.markdown(f"{icon} {wx['maxs'][i]:.0f}°/{wx['mins'][i]:.0f}°")
            if wx["rain"][i]>0: col.caption(f"💧{wx['rain'][i]:.0f}mm")
    else: st.info("Weather unavailable — check connection and refresh.")
    st.divider()
    require_plants()

    n_set = int((df["actual_sun"].notna() & (df["actual_sun"] != "")).sum())
    mismatches = [(row, sun_mismatch(row.get("sun_needed"), row.get("actual_sun")))
                  for _, row in df.iterrows() if sun_mismatch(row.get("sun_needed"), row.get("actual_sun"))]
    this_month_tasks = tasks_this_month(df, today.month)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🌱 Plants", len(df))
    c2.metric("☀️ Sun positions set", f"{n_set}/{len(df)}")
    c3.metric("⚠️ Mismatches", len(mismatches))
    c4.metric(f"📅 Tasks this month", len(this_month_tasks))

    # This month's tasks
    st.markdown(f'<div class="sec-hdr">📅 Tasks for {MONTH_NAMES[today.month]}</div>', unsafe_allow_html=True)
    render_tasks_by_type(this_month_tasks, MONTH_NAMES[today.month])

    col_l, col_r = st.columns(2)
    with col_l:
        if mismatches:
            st.markdown('<div class="sec-hdr">⚠️ Placement Mismatches</div>', unsafe_allow_html=True)
            for row, mtype in mismatches:
                needed = SUN_OPTIONS.get(str(row.get("sun_needed") or ""),"?")
                actual = SUN_OPTIONS.get(str(row.get("actual_sun") or ""),"?")
                msg = f"Gets <b>{actual}</b> but needs <b>{needed}</b> — {'too much sun.' if mtype=='over' else 'too little sun.'}"
                st.markdown(f"""<div class="mismatch-card {'severe' if mtype=='over' else ''}">
                  <div class="mismatch-name">{row['name']}</div>
                  <div class="mismatch-body">{msg}</div></div>""", unsafe_allow_html=True)
    with col_r:
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
    st.caption("For each plant, set how much sun it actually receives in your garden. Click an active button again to clear it.")
    require_plants()
    st.markdown('<div class="sec-hdr">Bulk assign</div>', unsafe_allow_html=True)
    bc1,bc2,bc3,bc4,bc5 = st.columns([2.5,1.2,1.5,1.3,1])
    bulk_q = bc1.text_input("Filter (empty = all)", placeholder="e.g. роза…", label_visibility="collapsed")
    mask = (st.session_state.plants_df["name"].str.contains(bulk_q,case=False,na=False) if bulk_q else pd.Series([True]*len(st.session_state.plants_df)))
    if bc2.button("☀️ All → Full sun"):    st.session_state.plants_df.loc[mask,"actual_sun"]="full_sun";    st.rerun()
    if bc3.button("⛅ All → Part. shade"): st.session_state.plants_df.loc[mask,"actual_sun"]="partial_shade"; st.rerun()
    if bc4.button("🌑 All → Full shade"):  st.session_state.plants_df.loc[mask,"actual_sun"]="full_shade";  st.rerun()
    if bc5.button("✕ Clear all"):          st.session_state.plants_df.loc[mask,"actual_sun"]=None;          st.rerun()
    st.divider()

    # Column headers
    hc1,hc2,hc3,hc4,hc5,hc6 = st.columns([3,2,2,1.2,1.5,1.3])
    hc1.markdown("<span style='font-size:0.78rem;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.05em'>Plant</span>", unsafe_allow_html=True)
    hc2.markdown("<span style='font-size:0.78rem;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.05em'>Needs (from file)</span>", unsafe_allow_html=True)
    hc3.markdown("<span style='font-size:0.78rem;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.05em'>Currently set</span>", unsafe_allow_html=True)
    hc4.markdown("<span style='font-size:0.78rem;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.05em'></span>", unsafe_allow_html=True)

    show_f = st.radio("Show",["All plants","⚠️ Mismatches only","○ Not set yet"],horizontal=True)

    for i, row in st.session_state.plants_df.iterrows():
        actual = row.get("actual_sun") or ""
        needed = row.get("sun_needed") or ""
        mtype  = sun_mismatch(needed, actual)
        if show_f=="⚠️ Mismatches only" and not mtype: continue
        if show_f=="○ Not set yet" and actual: continue

        status = "○" if not actual else ("⚠️" if mtype else "✅")
        color  = "#aaa" if not actual else ("#c0392b" if mtype=="over" else ("#e67e22" if mtype=="under" else "#2c7a1e"))

        # Currently set display
        if actual:
            actual_label = SUN_OPTIONS.get(actual, actual)
            actual_color = "#c0392b" if mtype=="over" else ("#e67e22" if mtype=="under" else "#2c7a1e")
            actual_html  = f"<span style='color:{actual_color};font-weight:600;font-size:0.85rem'>{actual_label}</span>"
        else:
            actual_html = "<span style='color:#bbb;font-size:0.82rem'>— not set —</span>"

        cn, cneeded, cactual, cb1, cb2, cb3 = st.columns([3, 2, 2, 1.2, 1.5, 1.3])

        cn.markdown(
            f"<span style='color:{color};font-weight:600'>{status} {row['name']}</span>"
            f"<br><span style='font-size:0.75rem;color:#888'>{row.get('latin','')}</span>",
            unsafe_allow_html=True
        )
        cneeded.markdown(
            f"<span style='font-size:0.82rem;color:#555'>{SUN_OPTIONS.get(needed, needed or '—')}</span>",
            unsafe_allow_html=True
        )
        cactual.markdown(actual_html, unsafe_allow_html=True)

        # Buttons: clicking an already-active one clears the value
        t = lambda v: "primary" if actual == v else "secondary"
        if cb1.button("☀️ Full sun",    key=f"fs_{i}",  type=t("full_sun")):
            st.session_state.plants_df.at[i,"actual_sun"] = None if actual=="full_sun" else "full_sun"
            st.rerun()
        if cb2.button("⛅ Part. shade", key=f"ps_{i}",  type=t("partial_shade")):
            st.session_state.plants_df.at[i,"actual_sun"] = None if actual=="partial_shade" else "partial_shade"
            st.rerun()
        if cb3.button("🌑 Full shade",  key=f"fsh_{i}", type=t("full_shade")):
            st.session_state.plants_df.at[i,"actual_sun"] = None if actual=="full_shade" else "full_shade"
            st.rerun()

    st.divider()
    n_set = int((st.session_state.plants_df["actual_sun"].notna() & (st.session_state.plants_df["actual_sun"] != "")).sum())
    st.caption(f"☀️ {n_set}/{len(df)} plants have sun position set.")

# ══════════════════════════════════════════════════════════════════════════════
# CARE SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "📋 Care Schedule":
    st.markdown("# 📋 Care Schedule")
    require_plants()

    view = st.radio("View", ["📅 By month","🌿 By plant","🫙 Bulbs only","⚠️ Mismatches only"], horizontal=True)
    st.divider()

    CARE_COLORS = {
        "pruning":  ("#eaf2e0","#2c5015","✂️ Pruning"),
        "feeding":  ("#f0f7e8","#1a5226","🌿 Feeding"),
        "watering": ("#e8f3fb","#1a3a5c","💧 Watering"),
    }

    if view == "📅 By month":
        month_sel = st.selectbox("Month", list(MONTH_NAMES.values()),
                                 index=today.month - 1,
                                 format_func=lambda x: x)
        month_num = list(MONTH_NAMES.values()).index(month_sel) + 1
        month_tasks = tasks_this_month(df, month_num)
        if month_tasks:
            st.caption(f"**{len(month_tasks)} tasks** scheduled for {month_sel}")
        render_tasks_by_type(month_tasks, month_sel)

    elif view == "🌿 By plant":
        search = st.text_input("🔍 Search plant", placeholder="Type name…")
        show_df = df[df["name"].str.contains(search, case=False, na=False)] if search else df
        for _, row in show_df.iterrows():
            name   = row["name"]
            needed = SUN_OPTIONS.get(str(row.get("sun_needed") or ""),"?")
            actual = SUN_OPTIONS.get(str(row.get("actual_sun") or ""),"— not set —")
            mtype  = sun_mismatch(row.get("sun_needed"), row.get("actual_sun"))
            warn   = "⚠️ " if mtype else ("✅ " if row.get("actual_sun") else "○ ")
            with st.expander(f"{warn}**{name}**{'  🫙' if row.get('is_bulb') else ''} · {SUN_OPTIONS.get(str(row.get('sun_needed') or ''),'?')}"):
                if row.get("latin"): st.caption(f"*{row['latin']}*")
                # Care cards — always visible, no button needed
                for care_key, (bg, fg, title) in CARE_COLORS.items():
                    text = row.get(care_key) or lookup_care(row.get("latin"))[care_key]
                    # Highlight months active this month
                    month_key = care_key + "_months"
                    months_active = months_list(row.get(month_key) or lookup_care(row.get("latin")).get(month_key,""))
                    badge = f" <span style='background:#3d6b1e;color:white;border-radius:10px;padding:1px 8px;font-size:0.72rem;'>📅 Due this month</span>" if today.month in months_active else ""
                    st.markdown(f"""<div class="care-card" style="background:{bg}">
                      <div class="care-title" style="color:{fg}">{title}{badge}</div>
                      <div class="care-body">{text}</div>
                    </div>""", unsafe_allow_html=True)
                # Bulb care
                if row.get("is_bulb"):
                    care = lookup_care(row.get("latin"))
                    # Show bulb-specific info from the care DB description
                    st.markdown(f"""<div class="care-card" style="background:#fef9e8">
                      <div class="care-title" style="color:#5c4a00">🫙 Bulb / Corm Care</div>
                      <div class="care-body">Lift after foliage yellows (typically Jun–Jul for spring-flowering, Oct–Nov for summer-flowering). Store dry in paper bags in a cool dark frost-free place. Replant at correct depth in appropriate season.</div>
                    </div>""", unsafe_allow_html=True)
                # Placement warning
                if mtype:
                    needed_lbl = SUN_OPTIONS.get(str(row.get("sun_needed") or ""),"?")
                    actual_lbl = SUN_OPTIONS.get(str(row.get("actual_sun") or ""),"?")
                    msg = (f"Gets <b>{actual_lbl}</b> but needs <b>{needed_lbl}</b> — "
                           f"{'too much sun — may scorch or dry out.' if mtype=='over' else 'too little sun — may not flower or grow properly.'} "
                           f"See the Care Schedule → By plant view for detailed care instructions.")
                    st.markdown(f"""<div class="care-card" style="background:#fdecea;border:1.5px solid #c0392b">
                      <div class="care-title" style="color:#c0392b">⚠️ Placement Problem</div>
                      <div class="care-body">{msg}</div>
                    </div>""", unsafe_allow_html=True)
                elif row.get("actual_sun"):
                    st.markdown(f"""<div class="care-card" style="background:#eaf7ea">
                      <div class="care-title" style="color:#1a6b1a">✅ Placement OK</div>
                      <div class="care-body">Sun conditions match what this plant needs.</div>
                    </div>""", unsafe_allow_html=True)

    elif view == "🫙 Bulbs only":
        bulb_df = df[df["is_bulb"]==True]
        if bulb_df.empty:
            st.info("No bulbs/corms in your plant list.")
        else:
            st.caption(f"**{len(bulb_df)} bulbs/corms** in your garden")
            for _, row in bulb_df.iterrows():
                with st.expander(f"🫙 **{row['name']}** — {row.get('latin','')}"):
                    for care_key, (bg, fg, title) in CARE_COLORS.items():
                        text = row.get(care_key) or lookup_care(row.get("latin"))[care_key]
                        months_active = months_list(row.get(care_key+"_months") or lookup_care(row.get("latin")).get(care_key+"_months",""))
                        badge = f" <span style='background:#3d6b1e;color:white;border-radius:10px;padding:1px 8px;font-size:0.72rem;'>📅 Due this month</span>" if today.month in months_active else ""
                        st.markdown(f"""<div class="care-card" style="background:{bg}">
                          <div class="care-title" style="color:{fg}">{title}{badge}</div>
                          <div class="care-body">{text}</div>
                        </div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="care-card" style="background:#fef9e8">
                      <div class="care-title" style="color:#5c4a00">🫙 Winter Storage</div>
                      <div class="care-body">After foliage yellows naturally: lift carefully, dry for 1–2 weeks in shade, dust with sulphur powder, store in paper bags (never plastic) in a cool (5–10°C), dark, frost-free location. Label clearly. Check monthly for rot.</div>
                    </div>""", unsafe_allow_html=True)

    else:  # Mismatches only
        mismatch_df = df[df.apply(lambda r: sun_mismatch(r.get("sun_needed"), r.get("actual_sun")) is not None, axis=1)]
        if mismatch_df.empty:
            st.success("✅ All plants with sun positions set are correctly placed!")
        else:
            st.caption(f"**{len(mismatch_df)} plants** with placement issues")
            for _, row in mismatch_df.iterrows():
                mtype  = sun_mismatch(row.get("sun_needed"), row.get("actual_sun"))
                needed = SUN_OPTIONS.get(str(row.get("sun_needed") or ""),"?")
                actual = SUN_OPTIONS.get(str(row.get("actual_sun") or ""),"?")
                with st.expander(f"⚠️ **{row['name']}** — needs {needed}, gets {actual}"):
                    if row.get("latin"): st.caption(f"*{row['latin']}*")
                    st.markdown(f"""<div class="care-card" style="background:#fdecea;border:1.5px solid #c0392b">
                      <div class="care-title" style="color:#c0392b">⚠️ Placement Problem</div>
                      <div class="care-body">Needs <b>{needed}</b> but currently gets <b>{actual}</b> — {"too much sun: may scorch, dry out, or fail to thrive." if mtype=="over" else "too little sun: likely poor flowering, weak growth, possible fungal issues."}<br><br>See the full care cards in <b>📋 Care Schedule → By plant</b> for detailed instructions.</div>
                    </div>""", unsafe_allow_html=True)
                    for care_key,(bg,fg,title) in CARE_COLORS.items():
                        text = row.get(care_key) or lookup_care(row.get("latin"))[care_key]
                        st.markdown(f"""<div class="care-card" style="background:{bg}">
                          <div class="care-title" style="color:{fg}">{title}</div>
                          <div class="care-body">{text}</div>
                        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# AI DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "⬇️ CSV Template":
    st.markdown("# ⬇️ Download CSV Template")
    st.caption("Use this template to prepare your plant list, then upload it via the sidebar.")
    st.divider()

    st.markdown("**Required columns:** `name`, `sun_needed`")
    st.markdown("**Optional:** `latin`, `actual_sun`, `soil`, `is_bulb`, `notes`, `pruning`, `feeding`, `watering`")
    st.caption("If `pruning`, `feeding`, `watering` are missing, care data is auto-filled from the built-in plant database using the `latin` column.")

    tpl = pd.DataFrame([
        {"name":"Лавандула","latin":"Lavandula angustifolia","sun_needed":"full_sun","actual_sun":"","soil":"well_drained","is_bulb":"no","notes":""},
        {"name":"Хоста","latin":"Hosta spp.","sun_needed":"partial_shade","actual_sun":"","soil":"moist","is_bulb":"no","notes":""},
        {"name":"Далия","latin":"Dahlia spp.","sun_needed":"full_sun","actual_sun":"","soil":"well_drained","is_bulb":"yes","notes":""},
    ])
    st.dataframe(tpl, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download CSV template", tpl.to_csv(index=False).encode(),
                       "garden_template.csv", "text/csv", use_container_width=True)
    st.divider()
    st.info("📂 To load your plant list, use the uploader in the **sidebar on the left**.")
