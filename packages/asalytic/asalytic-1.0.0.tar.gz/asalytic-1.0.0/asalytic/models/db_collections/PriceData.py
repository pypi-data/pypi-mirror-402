from pydantic import BaseModel


class PriceData(BaseModel):
    date: str
    usd: float
    btc: float
    eth: float
