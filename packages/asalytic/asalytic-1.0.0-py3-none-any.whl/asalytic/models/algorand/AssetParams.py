from pydantic import BaseModel
from typing import Optional


# https://developer.algorand.org/docs/rest-apis/indexer/#assetparams
class AssetsParams(BaseModel):
    name: Optional[str]
    unit_name: Optional[str]

    total: int
    decimals: int

    creator: str
    clawback: Optional[str]
    freeze: Optional[str]
    manager: Optional[str]
    reserve: Optional[str]

    default_frozen: Optional[bool]

    url: Optional[str]

    @staticmethod
    def init_from_asset_params(asset_params: dict):
        try:
            return AssetsParams(name=asset_params.get('name', None),
                                unit_name=asset_params.get('unit-name', None),
                                total=asset_params.get('total', None),
                                decimals=asset_params.get('decimals', None),
                                creator=asset_params.get('creator', None),
                                clawback=asset_params.get('clawback', None),
                                freeze=asset_params.get('freeze', None),
                                manager=asset_params.get('manager', None),
                                reserve=asset_params.get('reserve', None),
                                default_frozen=asset_params.get('default-frozen', None),
                                url=asset_params.get('url', None))
        except:
            return None
