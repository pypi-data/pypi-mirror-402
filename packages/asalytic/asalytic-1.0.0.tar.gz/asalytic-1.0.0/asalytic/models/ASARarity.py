from pydantic import BaseModel


class ASARarity(BaseModel):
    asa_id: int
    collection_id: str
    rank: int
    total: int
    score: float
    scaled_score: float
