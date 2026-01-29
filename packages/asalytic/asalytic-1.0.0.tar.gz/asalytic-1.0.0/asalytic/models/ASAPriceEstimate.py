from pydantic import BaseModel
from typing import Optional


class ASAPriceEstimate(BaseModel):
    asa_id: int
    collection_id: str
    collection_floor: Optional[float]
    price_estimate: Optional[float]
    trait_estimate: Optional[float]
