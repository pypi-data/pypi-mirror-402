from typing import Optional
from pydantic import BaseModel
from asalytic.models.ASASale import SaleType

__all__ = ["ASAListing"]


class ASAListing(BaseModel):
    asa_id: int
    collection_id: str

    price: int
    time: int
    seller: str

    platform: str
    listing_type: Optional[SaleType]
    slug: Optional[str]

    creator_fee: Optional[float]
    marketplace_fee: Optional[float]
    referral_fee: Optional[float]

    class Config:
        use_enum_values = True
