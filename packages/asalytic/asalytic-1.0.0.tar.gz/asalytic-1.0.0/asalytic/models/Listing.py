from typing import Optional
from pydantic import BaseModel
from enum import Enum

from asalytic.models.algorand import Application, AtomicTransfer
from asalytic.models.Teal import Teal

__all__ = ["Listing", "ListingType"]


class ListingType(str, Enum):
    application = "application"
    smart_signature = "smart_signature"


class Listing(BaseModel):
    asa_id: int
    asa_creator_address: Optional[str]
    collection_id: Optional[str]

    type: ListingType

    price: int
    seller: str
    time: Optional[int]
    block: Optional[int]

    platform: str

    creator_fee: Optional[float]
    marketplace_fee: Optional[float]
    referral_fee: Optional[float]

    delisting_block: Optional[int]
    delisting_time: Optional[int]

    app_id: Optional[int]

    smart_signature_bytes: Optional[str]
    smart_signature_address: Optional[str]
    smart_signature_tx_id: Optional[str]

    # Properties for Asalytic
    a_seller_amount: Optional[int]
    a_contract_amount: Optional[int]
    a_creator_amount: Optional[int]

    a_listing_wallet: Optional[str]
    a_creator_wallet: Optional[str]

    class Config:
        use_enum_values = True

    @staticmethod
    def init_from_application(application: Application):
        pass

    @staticmethod
    def init_from_teal(teal: Teal, atomic_transfer: AtomicTransfer):
        pass
