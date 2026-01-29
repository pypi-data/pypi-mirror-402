from pydantic import BaseModel
from typing import Optional


# https://developer.algorand.org/docs/rest-apis/indexer/#transactionassettransfer
class AssetTransferTransaction(BaseModel):
    asset_id: int

    amount: int

    receiver: str

    close_amount: Optional[int]
    close_to: Optional[str]

    sender: Optional[str]

    @property
    def asset_transferred(self):
        return self.amount > 0 or self.close_amount > 0

    @property
    def asset_opt_in(self):
        return self.amount == 0 and self.close_amount == 0

    @staticmethod
    def init_from_asset_transfer(asset_transfer: dict):
        try:
            return AssetTransferTransaction(asset_id=asset_transfer.get('asset-id', None),
                                            amount=asset_transfer.get('amount', None),
                                            receiver=asset_transfer.get('receiver', None),
                                            close_amount=asset_transfer.get('close-amount', None),
                                            close_to=asset_transfer.get('close-to', None),
                                            sender=asset_transfer.get('sender', None))
        except:
            return None
