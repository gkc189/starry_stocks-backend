from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starry_stocks_common.engine import (
    STRATEGIES,
    build_scoring_explanation,
    get_security_types,
    run_put_credit_spread_scan,
    run_sell_puts_scan,
    validate_dte_buckets,
)
from starry_stocks_common.market_data import suggest_index_ticker

from app.config import (
    STRATEGY_CONFIG_FILENAMES,
    get_dte_buckets,
    get_put_credit_spread_configs,
    get_put_credit_spread_max_dte,
    get_sell_puts_config,
    get_strategy_universe,
    set_dte_buckets,
    set_put_credit_spread_max_dte,
    set_strategy_universe,
)
from app.schemas import (
    DteBucketsOut,
    ExplainOut,
    MaxDteOut,
    PutCreditSpreadScanOut,
    SecurityTypesOut,
    SecurityTypesRequest,
    SellPutsScanOut,
    StrategyOut,
    StrategyUniverseOut,
    UpdateDteBucketsRequest,
    UpdateMaxDteRequest,
    UpdateStrategyUniverseRequest,
)

app = FastAPI(title='Starry Stocks Scanner API')

# Permissive CORS for local development: the webapp is a static page served
# from a different origin/port than this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

_STRATEGY_IDS = {strategy.id for strategy in STRATEGIES}


@app.get('/api/health')
def health():
    return {'status': 'ok'}


@app.get('/api/strategies', response_model=list[StrategyOut])
def list_strategies():
    return [asdict(strategy) for strategy in STRATEGIES]


def _universe_out(strategy_id: str, tickers: list[str]) -> dict:
    types = get_security_types(tickers)
    return {
        'strategy': strategy_id,
        'securities': [{'ticker': ticker, 'type': types.get(ticker)} for ticker in tickers],
    }


def _require_strategy_universe_support(strategy_id: str) -> None:
    if strategy_id in STRATEGY_CONFIG_FILENAMES:
        return
    if strategy_id in _STRATEGY_IDS:
        raise HTTPException(status_code=501, detail=f"No search-set config for strategy: {strategy_id}")
    raise HTTPException(status_code=404, detail=f"Unknown strategy: {strategy_id}")


@app.get('/api/strategies/{strategy_id}/universe', response_model=StrategyUniverseOut)
def strategy_universe(strategy_id: str):
    _require_strategy_universe_support(strategy_id)
    return _universe_out(strategy_id, get_strategy_universe(strategy_id))


@app.put('/api/strategies/{strategy_id}/universe', response_model=StrategyUniverseOut)
def update_strategy_universe(strategy_id: str, payload: UpdateStrategyUniverseRequest):
    _require_strategy_universe_support(strategy_id)
    tickers = set_strategy_universe(strategy_id, payload.tickers)
    return _universe_out(strategy_id, tickers)


@app.get('/api/strategies/sell-puts/dte-buckets', response_model=DteBucketsOut)
def dte_buckets():
    return {'buckets': get_dte_buckets()}


@app.put('/api/strategies/sell-puts/dte-buckets', response_model=DteBucketsOut)
def update_dte_buckets(payload: UpdateDteBucketsRequest):
    try:
        validate_dte_buckets(payload.buckets)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {'buckets': set_dte_buckets(payload.buckets)}


@app.get('/api/strategies/put-credit-spread/max-dte', response_model=MaxDteOut)
def put_credit_spread_max_dte():
    return {'max_dte': get_put_credit_spread_max_dte()}


@app.put('/api/strategies/put-credit-spread/max-dte', response_model=MaxDteOut)
def update_put_credit_spread_max_dte(payload: UpdateMaxDteRequest):
    if payload.max_dte < 1:
        raise HTTPException(status_code=400, detail='max_dte must be >= 1.')

    return {'max_dte': set_put_credit_spread_max_dte(payload.max_dte)}


@app.post('/api/securities/types', response_model=SecurityTypesOut)
def security_types(payload: SecurityTypesRequest):
    suggested_aliases = {
        ticker: alias
        for ticker in payload.tickers
        if (alias := suggest_index_ticker(ticker)) is not None
    }
    return {'types': get_security_types(payload.tickers), 'suggested_aliases': suggested_aliases}


@app.get('/api/strategies/{strategy_id}/explain', response_model=ExplainOut)
def explain_strategy(strategy_id: str):
    if strategy_id not in _STRATEGY_IDS:
        raise HTTPException(status_code=404, detail=f"Unknown strategy: {strategy_id}")

    if strategy_id == 'sell-puts':
        config = get_sell_puts_config()
    elif strategy_id == 'put-credit-spread':
        config, _ = get_put_credit_spread_configs()
    else:
        return {'strategy': strategy_id, 'components': []}

    components = build_scoring_explanation(config, strategy_id)
    return {'strategy': strategy_id, 'components': [asdict(c) for c in components]}


@app.post('/api/scan/sell-puts', response_model=SellPutsScanOut)
def scan_sell_puts():
    config = get_sell_puts_config()
    result = run_sell_puts_scan(config)
    return asdict(result)


@app.post('/api/scan/put-credit-spread', response_model=PutCreditSpreadScanOut)
def scan_put_credit_spread():
    config, put_spreads_config = get_put_credit_spread_configs()
    result = run_put_credit_spread_scan(config, put_spreads_config)
    return asdict(result)


@app.post('/api/scan/call-credit-spread')
def scan_call_credit_spread():
    raise HTTPException(status_code=501, detail='Call credit spread strategy is not yet implemented.')
