from pydantic import BaseModel

from asalytic.models.algorand import AtomicTransfer


class SignatureDelisting(BaseModel):
    address: str
    asa_id: int

    @staticmethod
    def init_delisting(atomic_transfer: AtomicTransfer):
        pass
