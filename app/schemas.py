from typing import Optional

from pydantic import BaseModel, Field, model_validator


class StrategyOut(BaseModel):
    id: str
    name: str
    available: bool


class SecurityOut(BaseModel):
    ticker: str
    type: Optional[str] = None


class StrategyUniverseOut(BaseModel):
    strategy: str
    securities: list[SecurityOut]


class UpdateStrategyUniverseRequest(BaseModel):
    tickers: list[str]


class DteBucketsOut(BaseModel):
    buckets: list[list[int]]


class UpdateDteBucketsRequest(BaseModel):
    buckets: list[list[int]]


class StrategyConfigsOut(BaseModel):
    strategy: str
    configs: list[str]
    selected: str


class CreateStrategyConfigRequest(BaseModel):
    name: str


class SelectStrategyConfigRequest(BaseModel):
    name: str


class DeltaRange(BaseModel):
    min: float = Field(ge=0.0, le=1.0)
    max: float = Field(ge=0.0, le=1.0)

    @model_validator(mode='after')
    def check_range(self):
        if self.min > self.max:
            raise ValueError('delta range min must be <= max.')
        return self


class StrategyFiltersOut(BaseModel):
    strategy: str
    use_scoring: bool
    delta_range: DeltaRange
    risk_reward_min: float


class UpdateStrategyFiltersRequest(BaseModel):
    use_scoring: bool
    delta_range: DeltaRange
    risk_reward_min: float = Field(ge=0.01, le=1.0)


class SecurityTypesRequest(BaseModel):
    tickers: list[str]


class SecurityTypesOut(BaseModel):
    types: dict[str, Optional[str]]
    suggested_aliases: dict[str, str] = Field(default_factory=dict)


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
    delta: float
    risk_reward: float
    score: Optional[float]
    bucket: str


class SellPutsScanOut(BaseModel):
    scanned_stocks: list[ScannedStockOut]
    bucket_order: list[str]
    buckets: dict[str, list[ScoredOptionOut]]


class ScoredSpreadOut(BaseModel):
    score: Optional[float]
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
