from pydantic import BaseModel
from typing import List, Optional

__all__ = ["WalletConfiguration"]


class WalletConfiguration(BaseModel):
    wallet: str
    linked_wallets: List[str]
    favorite_asa_ids: List[int]
    favorite_listings_asa_ids: List[int]
    favorite_collection_ids: List[str]
    favorite_creator_ids: List[str]
    email: Optional[str]
    promo_used: bool
