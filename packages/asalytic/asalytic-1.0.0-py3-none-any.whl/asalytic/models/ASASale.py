from pydantic import BaseModel
from typing import Optional
from enum import Enum
from asalytic.models.algorand import AtomicTransfer

__all__ = ["SaleType", "PriceConversion", "ASASale"]


class SaleType(str, Enum):
    buy_now = 'buy_now'
    offer = 'offer'
    auction = 'auction'
    shuffle = 'shuffle'
    unknown = 'unknown'


class PriceConversion(BaseModel):
    usd: Optional[float]
    eth: Optional[float]
    btc: Optional[float]


class ASASale(BaseModel):
    seller: str
    buyer: str
    price: int
    platform_fee: int
    creator_fee: int
    seller_price: int
    time: int
    asa_id: int
    sale_platform: str
    sale_type: SaleType
    group_id: str
    block_number: int

    usd_price: Optional[float]
    eth_price: Optional[float]
    btc_price: Optional[float]

    collection_id: Optional[str]
    creator_address: Optional[str]

    a_listing_side: Optional[str]  # Asalytic Listing Side wallet
    a_buying_side: Optional[str]  # Asalytic Buying Side wallet

    @property
    def royalty_percent(self):
        return self.creator_fee / self.price * 100

    class Config:
        use_enum_values = True

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        pass
