from pydantic import BaseModel


class AtomicTransferSignatureListing(BaseModel):
    platform: str
    time: int
    block: int
    address: str
    teal_tx_id: str
    group: str
