from pydantic import BaseModel


class AtomicTransferDelisting(BaseModel):
    platform: str
    time: int
    block: int
    app_id: int
