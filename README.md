# starry_stocks-backend

FastAPI web service exposing the Starry Stocks options scanner over HTTP.
Uses the shared scanning/scoring engine from
[starry_stocks-common](../starry_stocks-common) - the same engine the
[starry_stocks](../starry_stocks) CLI uses.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: http://127.0.0.1:8000/docs

## Endpoints

- `GET /api/health` - liveness check
- `GET /api/strategies` - available strategies
- `GET /api/universe` - default ticker universe (from `app/configs/config.yaml`)
- `GET /api/strategies/{strategy_id}/explain` - scoring weight breakdown
- `POST /api/scan/sell-puts` - run the cash-secured put scan, body: `{"tickers": ["SPY", ...]}` (omit/`null` to use the default universe)
- `POST /api/scan/put-credit-spread` - run the put credit spread scan, same body shape
- `POST /api/scan/call-credit-spread` - returns `501` (not yet implemented, matches the CLI)

## Configuration

Default scoring/universe settings live in `app/configs/*.yaml` (copies of the
CLI's config files). Edit them to change the default ticker universe, DTE
buckets, or scoring weights. Per-request ticker overrides can be sent in the
`tickers` field of the scan request body without touching these files.

CORS is wide open (`allow_origins=["*"]`) since this is meant to be paired
with the [starry_stocks-webapp](../starry_stocks-webapp) static frontend
running on a different local port. Tighten this before deploying anywhere
public.
