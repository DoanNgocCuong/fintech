# Gen57Metrics Dashboard

UI + API package to explore the 57 base indicators per stock. The implementation mirrors the conventions in `BaoCaoTaiChinh/web` but focuses on the Gen57Metrics calculator.

## Features

- FastAPI backend (`app.py`) that exposes:
  - `/api/indicators` – metadata straight from `57BaseIndicators.json`
  - `/api/stocks` & `/api/periods` – available tickers and reporting periods from PostgreSQL
  - `/api/indicator-values` – on-demand calculations using `IndicatorCalculator`
  - `/api/dashboard/bootstrap` – single call to hydrate the frontend
- Static frontend (`index.html`, `css/style.css`, `js/app.js`) with:
  - Stock/year/quarter selectors
  - Group + free-text filtering
  - Summary stats (successful/failed indicators)
  - Responsive data table showing definition, formulas, usage flags, weights, and live values

## Getting started

```bash
cd Gen57Metrics/web
pip install -r requirements.txt
uvicorn app:app --reload --port 30100
```

Then serve the static files (e.g. `python -m http.server 8081`) and open `http://localhost:8081/index.html`. The frontend auto-detects the API base when everything runs locally.

## Configuration

- Database credentials are reused from `Gen57Metrics/utils_database_manager.py`.
- The API defaults to `balance_sheet_raw` for the stock list, but you can pass `source=income_p2`, `source=cashflow`, etc.
- Frontend value formatting uses `vi-VN` locale and highlights failures with the summary cards.

## Testing

1. Start the API (`uvicorn app:app --reload`).
2. Load the UI and pick any ticker that exists in your DB.
3. Verify successful indicator counts and check browser devtools for API responses.
4. Optional: call `/api/indicator-values` via curl/Postman for automation.

## Next steps

- Add CSV/Excel export from the UI.
- Surface dependency graphs per indicator.
- Add authentication if the API is exposed publicly.

