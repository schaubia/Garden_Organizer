# 🌿 Garden Planner — Sofia Edition

A Streamlit web application for managing your garden plants with live weather-aware care schedules, sun placement advice, and AI-powered deep-dive analysis. Built for the **continental climate of Sofia, Bulgaria** (hot dry summers, cold winters, frost October–April).

---

## Features

- **Live weather** — 7-day forecast for Sofia from Open-Meteo (free, no API key needed); drives alerts for frost, dry soil, high UV, and heavy rain
- **Single upload point** — one file uploader in the sidebar; drop in a CSV or XLSX and the whole app populates instantly
- **Care data auto-fill** — pruning, feeding, and watering schedules are looked up automatically from a built-in database of 70+ species using the `latin` column; no manual entry needed
- **Sun position setup** — one click per plant to record where it actually grows (full sun / partial shade / full shade); mismatches flagged immediately
- **Side-by-side monthly task tables** — tasks for the current month are displayed in separate colour-coded columns by activity type (✂️ Pruning, 🌿 Feeding, 💧 Watering, 🫙 Bulb care) so you can scan at a glance
- **Four care schedule views** — by month, by plant, bulbs only, or mismatches only
- **Placement warnings** — plants in the wrong light conditions are flagged with a clear explanation and a pointer to the AI tab
- **AI Deep Dive** — Claude-powered detailed advice per plant: weather-adjusted timing, biological fertiliser recommendations, replanting/removal decisions, and alternative species for misplaced plants
- **Bulb management** — dedicated bulb view with per-species care cards and detailed winter storage instructions

---

## Project structure

```
garden_planner/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── my_plants_template.csv    # Example CSV template
└── README.md                 # This file
```

---

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Steps

```bash
# Clone or download the project folder
cd garden_planner

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Deploying to Streamlit Community Cloud

1. Push the `garden_planner/` folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set the main file path to `app.py`
4. Add your Anthropic API key as a secret:
   - In the Streamlit Cloud dashboard → **Settings → Secrets**
   - Add: `ANTHROPIC_API_KEY = "sk-ant-..."`
5. Deploy — weather fetching requires no additional keys

---

## Your plant CSV file

The app accepts CSV or XLSX. Upload using the **sidebar uploader** — this is the only upload point in the app.

### Columns

| Column | Required | Description |
|--------|----------|-------------|
| `name` | ✅ | Plant name (Bulgarian or English) |
| `sun_needed` | ✅ | Light requirement: `full_sun`, `partial_shade`, `half shade`, or `shade` |
| `latin` | recommended | Latin name — used to match species in the built-in care database |
| `actual_sun` | optional | Where the plant actually grows; can also be set in the app via ☀️ Sun Setup |
| `soil` | optional | `well_drained`, `moist`, `clay`, `sandy`, or `rich` |
| `is_bulb` | optional | `yes` or `no` |
| `notes` | optional | Free text notes |
| `pruning` | optional | Custom pruning text — overrides the built-in database for this plant |
| `feeding` | optional | Custom feeding text — overrides the built-in database |
| `watering` | optional | Custom watering text — overrides the built-in database |
| `pruning_months` | optional | Comma-separated month numbers, e.g. `3,9` for March and September |
| `feeding_months` | optional | Comma-separated month numbers |

> **Tip:** The `zone` and `sun` columns are also accepted as aliases for `sun_needed` when they contain sun values such as `full_sun`, `half shade`, or `shade`. This means your existing catalogue files upload without any renaming.

A ready-to-use template is included: `my_plants_template.csv`.

---

## How to use

### 1. Load your plants
Drop your CSV or XLSX into the **sidebar uploader**. The app reads the file, auto-fills any missing care data from the built-in species database, and makes the plant list available across all tabs. You will see a green confirmation badge in the sidebar once the file is loaded. To swap files, click **↩️ Replace plant list**.

### 2. Set sun positions (☀️ Sun Setup)
For each plant, click one of three buttons — **☀️ Full sun**, **⛅ Partial shade**, or **🌑 Full shade** — to record where it actually grows in your garden. A bulk-assign row at the top lets you set many plants at once by typing a name filter. The currently active button is highlighted. Plants are shown with a status icon: ○ not set, ✅ correctly placed, ⚠️ mismatch.

### 3. Check the dashboard (🌤️ Dashboard)
The dashboard shows the live 7-day forecast, a summary of key metrics, weather-based alerts specific to your plant list (e.g. which bulbs to protect if frost is forecast), and this month's tasks displayed as **side-by-side tables** — one column per activity type so pruning, feeding, and bulb care are easy to separate at a glance.

### 4. Browse the care schedule (📋 Care Schedule)
Four views to choose from:

- **📅 By month** — select any month and see all tasks across your whole garden, displayed in side-by-side colour-coded tables grouped by activity type (✂️ Pruning, 🌿 Feeding, 💧 Watering, 🫙 Bulb care, 🌱 Bulb planting). Only activity types that have tasks in that month are shown.
- **🌿 By plant** — expand any plant to see its three care cards (pruning, feeding, watering) always visible without any extra clicks. Cards due this month show a green **📅 Due this month** badge. Placement warnings appear inline.
- **🫙 Bulbs only** — all bulbs and corms with their care cards plus a detailed general winter storage guide.
- **⚠️ Mismatches only** — plants in the wrong light conditions, each with care cards and a prompt to use the AI tab for replanting advice.

### 5. Get AI advice (🤖 AI Deep Dive)
Select a plant from the dropdown, optionally type a specific question or tap one of the quick-question buttons, and get detailed advice adjusted for the current Sofia weather. Especially useful for misplaced plants — the AI explains whether to replant or remove, the best month to act, and which alternative plants would thrive in that spot instead.

---

## Built-in care database

The app includes species-level care data for 70+ plants common in Bulgarian gardens, covering exact pruning months, biological fertiliser recommendations, and watering frequency:

- **Trees and large shrubs** — Walnut, Hazel, Medlar, Ginkgo, Hawthorn, Cotoneaster, Chamaecyparis, Quince, Cornel, Cherry Laurel
- **Aromatic herbs** — Salvia, Thyme, Lemon balm, Mint
- **Climbers** — Virginia creeper, Campsis, Clematis, Ivy, Lonicera, Jasmine
- **Flowering shrubs** — Rose, Pyracantha, Mahonia, Weigela, Deutzia, Spiraea, Callicarpa, Barberry, Privet, Hibiscus, Vinca
- **Perennials** — Hosta, Echinacea, Rudbeckia, Paeonia, Hydrangea, Phlox, Stachys, Bergenia, Convallaria, Sempervivum, Lupinus
- **Bulbs and corms** — Dahlia, Tulip, Iris, Hyacinth, Ranunculus, Allium, Muscari, Scilla, Gladiolus
- **Ground covers and alpines** — Aubrieta, Iberis, Cerastium, Edelweiss, Santolina, Festuca, Calluna, Aeonium
- **Annuals** — Calendula, California poppy, Bellis, Antirrhinum

If a plant is not found in the database, a generic care schedule is used as fallback and a note is shown.

---

## Weather data

Weather is fetched from [Open-Meteo](https://open-meteo.com/) — a free, open-source weather API requiring no API key. Data is cached for 1 hour to avoid unnecessary requests. If the API is unreachable (e.g. offline), the rest of the app continues to work normally; weather-based alerts are simply not shown. Use the **🔄 Refresh Weather** button in the sidebar to force a fresh fetch.

---

## AI features

The **🤖 AI Deep Dive** tab uses the **Claude Sonnet** model via the Anthropic API. This requires an API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Set this as an environment variable when running locally, or as a Streamlit secret when deploying to Streamlit Cloud (Settings → Secrets). All other tabs — care schedules, weather, sun setup, placement detection — work fully without the key.

---

## Dependencies

```
streamlit>=1.32.0
pandas>=2.0.0
openpyxl>=3.1.0
```

No other packages are needed. Weather fetching and AI calls both use Python's built-in `urllib`.

---

## Notes on the Sofia climate

Care schedule timing throughout the app is calibrated for Sofia's continental climate:

- **Last frost** — typically mid-April; late frosts possible until end of April
- **First autumn frost** — typically mid-October
- **Summer** — hot and dry; July–August temperatures regularly exceed 35°C
- **Winter** — cold, −10°C to −15°C possible; most perennials benefit from mulching

All AI advice is prompted with these climate constraints and recommends only biological and organic products.
