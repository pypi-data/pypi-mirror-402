from pydantic import BaseModel


class ATAppListing(BaseModel):
    platform: str
    time: int
    block: int
    app_id: int
