from pydantic import BaseModel

__all__ = ["ASAOwner"]


class ASAOwner(BaseModel):
    owner: str
    asa_id: int
    balance: int = 1
