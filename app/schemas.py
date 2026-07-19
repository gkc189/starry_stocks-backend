from typing import Optional

from pydantic import BaseModel


class StrategyOut(BaseModel):
    id: str
    name: str
    available: bool


class UniverseOut(BaseModel):
    tickers: list[str]


class ScanRequest(BaseModel):
    tickers: Optional[list[str]] = None


class ScannedStockOut(BaseModel):
    ticker: str
    price: float


class ScoredOptionOut(BaseModel):
    ticker: str
    expiration: str
    dte: int
    strike: float
    bid: float
    iv: float
    open_interest: int
    score: float
    bucket: str


class SellPutsScanOut(BaseModel):
    scanned_stocks: list[ScannedStockOut]
    bucket_order: list[str]
    buckets: dict[str, list[ScoredOptionOut]]


class ScoredSpreadOut(BaseModel):
    score: float
    ticker: str
    short_strike: float
    long_strike: float
    width: float
    credit: float
    short_delta: float
    dte: Optional[int]
    iv_rank: Optional[float]
    credit_ratio: float
    return_on_risk: float


class PutCreditSpreadScanOut(BaseModel):
    scanned_stocks: list[ScannedStockOut]
    ranked_spreads: list[ScoredSpreadOut]


class ScoreComponentOut(BaseModel):
    key: str
    label: str
    weight: float
    weight_percent: float
    summary: Optional[str]
    weight_rationale: Optional[str]


class ExplainOut(BaseModel):
    strategy: str
    components: list[ScoreComponentOut]
