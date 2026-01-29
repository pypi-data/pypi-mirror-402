from pydantic import BaseModel
from typing import Optional
from asalytic.models.algorand.AssetParams import AssetsParams


# https://developer.algorand.org/docs/rest-apis/indexer/#transactionassetconfig
class AssetConfigTransaction(BaseModel):
    asset_id: Optional[int]
    params: Optional[AssetsParams]

    @property
    def is_asset_creation(self):
        return self.asset_id == 0

    @property
    def is_asset_update(self):
        if self.is_asset_delete:
            return False

        return self.asset_id is not None and self.asset_id != 0 and self.params is not None

    # TODO: This is incorrect. Need help in order how to determine if a transaction is a deletion or destruction.
    # https://algoindexer.algoexplorerapi.io/v2/transactions?txid=5SL2CLZVYI7AC3QRG2BCYFAJSTAMKBBOD5666OGPNJPE6VDG6HQQ
    @property
    def is_asset_delete(self):

        # Documentation deletion.
        if self.params is None and self.asset_id is not None and self.asset_id != 0:
            return True

        return False

    @staticmethod
    def init_from_asset_config(asset_config: dict):

        try:
            params = asset_config.get('params', None)
            return AssetConfigTransaction(asset_id=asset_config.get('asset-id', None),
                                          params=AssetsParams.init_from_asset_params(
                                              asset_params=params) if params is not None else None)
        except:
            return None
