# Monday.com BI Agent (Skylark Drones Assignment)

This project is a conversational business-intelligence agent that reads **Deals** and **Work Orders** from monday.com (read-only), normalizes messy fields, and answers founder-level queries with data caveats.

## What this prototype does

- Conversational interface (Streamlit chat)
- monday.com integration via GraphQL API (read-only)
- Data resilience:
  - Handles null/missing fields
  - Normalizes dates, numbers, and sector/status text
  - Surfaces data quality caveats in every response
- BI coverage:
  - Pipeline health
  - Revenue / billing / collections / receivables
  - Operational status summaries
  - Leadership update draft (optional requirement interpretation)

## Architecture

- `app.py` - Streamlit UI
- `src/monday_client.py` - monday.com GraphQL client + pagination
- `src/data_loader.py` - data source loader (`monday` default, `csv` fallback for local demo)
- `src/normalization.py` - schema harmonization and quality checks
- `src/metrics.py` - query intent heuristics + business metrics
- `src/agent.py` - query interpretation and response synthesis
- `docs/DECISION_LOG.md` - assumptions, tradeoffs, what to improve

## Setup

1. Create a virtual env and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Configure env vars:

```powershell
Copy-Item .env.example .env
```

Set:
- `MONDAY_API_TOKEN`
- `MONDAY_DEALS_BOARD_ID`
- `MONDAY_WORK_ORDERS_BOARD_ID`

Optional:
- `OPENAI_API_KEY` for stronger intent parsing
- `OPENAI_MODEL` (default: `gpt-4o-mini`)

3. Run app:

```powershell
streamlit run app.py
```

## monday.com configuration

Create/import two boards:
- Deals board (from `Deal_funnel_Data.csv`)
- Work Orders board (from `Work_Order_Tracker_Data.csv`)

Then set their board IDs in `.env`.

Notes:
- The app does **not** hardcode CSV values for normal operation.
- `csv` mode in sidebar is only a local fallback demo mode if monday credentials are not configured.

## Sample prompts

- `How's our pipeline looking for mining sector this quarter?`
- `Show revenue and collection efficiency for powerline this quarter.`
- `What operational risks do we have this month in renewables?`
- `Prepare a leadership update for this quarter.`

## Deployment (Hosted Prototype)

Fastest path: **Streamlit Community Cloud**

1. Push code to GitHub
2. Create app in Streamlit Cloud with `app.py`
3. Add secrets for monday API token/board IDs (and optional OpenAI key)
4. Share the public URL in submission form

Alternative: Render Web Service running `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

## Error handling behavior

- API failures are surfaced with clear message in UI
- Missing board IDs/token fails fast with actionable config hints
- Missing data is handled with null-safe aggregations and caveat reporting

## Assignment deliverables mapping

- Hosted Prototype: deploy this app
- Decision Log: see `docs/DECISION_LOG.md`
- Source Code ZIP: zip this repo with README and docs
