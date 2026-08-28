# PS 26001 — NER Landslide Early Warning Dashboard (Phase 1)

SIH 2026 prototype for "AI-Based Early Warning and Landslide Risk Monitoring
System in NER" — your **main** submission (PS 26017 is the backup).

## What's in Phase 1
- `generate_data.py` — 300 synthetic monitoring points spread across all 8
  North Eastern states, with a realistic underlying landslide-risk pattern
  (slope, soil moisture, rainfall, vegetation loss, history).
- `train_model.py` — Random Forest classifier predicting high-risk-alert
  probability per location, with feature importances for explainability.
- `dashboard.py` — Streamlit app with:
  - a live risk **map** of NER (color-coded by risk level, sized by
    nearby population)
  - risk-sorted location table
  - "what's driving risk" chart
  - a simulated live alert feed
  - a citizen/field-officer ground-report form (with photo upload)
  - a per-location detail + recommended-action view

Everything has already been run once and verified working — `data/` and
`model/` are included, so the dashboard opens with real results immediately.

## Setup
```bash
pip install -r requirements.txt
```

## Run
Optional — regenerate data or retrain (already done once):
```bash
python generate_data.py
python train_model.py
```

Launch the dashboard:
```bash
streamlit run dashboard.py
```
Opens at http://localhost:8501

## Not built yet (next steps, in priority order)
1. **Automated alerts** — the feed is simulated on load; a real version
   would push notifications (SMS/email/webhook) when a location crosses
   the high-risk threshold.
2. **Real data sources** — swap synthetic values for actual IMD rainfall
   and ISRO/Bhuvan satellite + landslide-inventory data once you've
   registered for portal access (both need free accounts, not instant).
3. **Offline sync** — the official brief calls this out specifically;
   worth mentioning even if not fully built, since 2026 judges give
   bonus points for offline/on-device capability.
4. **Persistence** — citizen reports currently only last for the browser
   session; a real deployment needs a database.

Say "next" and I'll build whichever of these you want the same way —
coded, run, and verified before you see it.
