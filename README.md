# 🌿 Garden Planner — Sofia Edition

A Streamlit web application for managing your garden plants with weather-aware care schedules, placement advice, and AI-powered deep-dive analysis. Built for the **continental climate of Sofia, Bulgaria** (hot dry summers, cold winters, frost October–April).

---

## Features

- **Live weather** — fetches a 7-day forecast for Sofia from Open-Meteo (free, no API key needed) and uses it to trigger alerts: frost warnings, soil-dry notifications, high UV, heavy rain
- **Plant list import** — upload your plants as CSV or XLSX; care data is auto-filled from a built-in database of 70+ species
- **Sun position setup** — set where each plant actually grows (full sun / partial shade / full shade) with one click per plant; mismatches detected automatically
- **Care schedule** — pruning, feeding, and watering instructions visible immediately for every plant, no AI call needed; browse by month, by plant, bulbs only, or mismatches only
- **Placement warnings** — flags plants in the wrong light conditions with a clear explanation and a link to AI advice
- **AI Deep Dive** — Claude-powered detailed advice for individual plants: weather-adjusted timing, biological fertiliser recommendations, replanting/removal decisions for misplaced plants, alternative species suggestions
- **Bulb management** — dedicated bulb view with winter storage instructions and seasonal planting reminders

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
5. Deploy — weather fetching works without any additional keys

---

## Your plant CSV file

The app accepts CSV or XLSX. The minimum required columns are:

| Column | Required | Description |
|--------|----------|-------------|
| `name` | ✅ | Plant name (Bulgarian or English) |
| `sun_needed` | ✅ | Light requirement: `full_sun`, `partial_shade`, `half shade`, or `shade` |
| `latin` | optional | Latin name — used to auto-fill care data from the built-in database |
| `actual_sun` | optional | Can be set in the app via the ☀️ Sun Setup tab |
| `soil` | optional | `well_drained`, `moist`, `clay`, `sandy`, or `rich` |
| `is_bulb` | optional | `yes` or `no` |
| `notes` | optional | Free text notes |
| `pruning` | optional | Custom pruning instructions (overrides built-in DB) |
| `feeding` | optional | Custom feeding instructions (overrides built-in DB) |
| `watering` | optional | Custom watering instructions (overrides built-in DB) |
| `pruning_months` | optional | Comma-separated month numbers, e.g. `3,9` for March and September |
| `feeding_months` | optional | Comma-separated month numbers |

> **Tip:** The `zone` column is also accepted as an alias for `sun_needed` if it contains sun values (e.g. `full_sun`, `half shade`).

A template CSV is included: `my_plants_template.csv`.

---

## How to use

### 1. Load your plants
Drop your CSV or XLSX into the uploader in the sidebar or the **📤 Upload** tab. Care data (pruning, feeding, watering) is auto-filled from the built-in database using the `latin` column to match species.

### 2. Set sun positions (☀️ Sun Setup)
For each plant, click one button — **☀️ Full sun**, **⛅ Partial shade**, or **🌑 Full shade** — to record where it actually grows in your garden. Use the bulk-assign row at the top to set many plants at once. The app immediately flags any plant whose actual conditions don't match its requirements.

### 3. Browse the care schedule (📋 Care Schedule)
Four views:
- **📅 By month** — all tasks due in a selected month across your whole garden
- **🌿 By plant** — expand any plant to see its pruning, feeding, and watering cards; tasks due this month are highlighted with a badge
- **🫙 Bulbs only** — all bulbs/corms with care cards and winter storage instructions
- **⚠️ Mismatches only** — plants in the wrong light conditions

### 4. Get AI advice for a specific plant (🤖 AI Deep Dive)
Select any plant from the dropdown, ask a specific question or choose a quick question, and receive detailed advice adjusted for the current weather in Sofia. Especially useful for misplaced plants — the AI will tell you whether to replant or remove, which month is safest to do it, and what to grow in that spot instead.

---

## Built-in care database

The app includes species-level care data for 70+ plants common in Bulgarian gardens:

- Trees and large shrubs: Walnut, Hazel, Medlar, Ginkgo, Hawthorn, Cotoneaster, Chamaecyparis, Quince, Cornel
- Aromatic herbs: Lavender, Thyme, Rosemary, Salvia, Mint, Lemon balm
- Climbers: Virginia creeper, Campsis, Clematis, Ivy, Lonicera, Jasmine
- Flowering shrubs: Rose, Pyracantha, Mahonia, Weigela, Deutzia, Callicarpa, Barberry, Privet, Berberis
- Perennials: Hosta, Echinacea, Rudbeckia, Paeonia, Hydrangea, Phlox, Stachys, Bergenia, Convallaria, Sempervivum
- Bulbs and corms: Dahlia, Tulip, Iris, Hyacinth, Ranunculus, Allium, Muscari, Scilla, Gladiolus
- Ground covers and alpines: Aubrieta, Iberis, Cerastium, Edelweiss, Santolina, Festuca, Calluna, Vinca
- Annuals: Calendula, California poppy, Bellis, Antirrhinum

If a plant is not in the database, a sensible generic care schedule is used as fallback.

---

## Weather data

Weather is fetched from [Open-Meteo](https://open-meteo.com/) — a free, open-source weather API with no API key requirement. Data is cached for 1 hour. If you are offline or the API is unreachable, the app continues to work without weather data; the weather-based alerts and watering advice simply won't be shown.

---

## AI features

The AI Deep Dive tab uses the **Claude Sonnet** model via the Anthropic API. This requires an API key set as an environment variable or Streamlit secret:

```
ANTHROPIC_API_KEY=sk-ant-...
```

When running locally without a key, the rest of the app (care schedules, weather, placement detection) works fully — only the AI tab will return an error.

---

## Dependencies

```
streamlit>=1.32.0
pandas>=2.0.0
openpyxl>=3.1.0
```

No other dependencies are required. Weather and AI calls use Python's built-in `urllib`.

---

## Notes on the Sofia climate

The care schedule timing is calibrated for Sofia's continental climate:

- **Last frost:** typically mid-April, but late frosts possible until end of April
- **First autumn frost:** typically mid-October
- **Summer:** hot and dry, July–August temperatures regularly exceed 35°C
- **Winter:** cold, −10°C to −15°C possible; most perennials need mulching

Advice from the AI is prompted with these conditions and uses only biological/organic products throughout.
