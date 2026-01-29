from pydantic import BaseModel

__all__ = ["Teal"]


class Teal(BaseModel):
    tx_id: str
    address: str
    teal_bytes: str
    decompiled_teal: str
