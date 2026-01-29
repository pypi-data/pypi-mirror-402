from enum import Enum
from typing import Optional

from asalytic.models import Listing, ListingType, Teal
from asalytic.models.algorand import AtomicTransfer, TransactionType

REFERRAL_FEE = 0

ASA_ID_LINE = 1
ROYALTY_LINE = 142
SELLER_AMOUNT_LINE = 154
MARKETPLACE_FEE_LINE = 166


class ALGOxNFTListing(Listing):
    platform = "ALGOxNFT"
    type = ListingType.smart_signature

    @staticmethod
    def init_from_3_transactions(teal: Teal, atomic_transfer: AtomicTransfer):

        transaction_order = [
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order.")

        teal_lines = teal.decompiled_teal.split('\n')

        asa_id = int(teal_lines[ASA_ID_LINE].split(' ')[-1])
        royalty_amount = int(teal_lines[ROYALTY_LINE].split(' ')[1])
        seller_amount = int(teal_lines[SELLER_AMOUNT_LINE].split(' ')[1])
        marketplace_amount = int(teal_lines[MARKETPLACE_FEE_LINE].split(' ')[1])

        price = royalty_amount + seller_amount + marketplace_amount

        if asa_id != atomic_transfer.transactions[2].asset_transfer_transaction.asset_id:
            raise NotImplementedError

        return ALGOxNFTListing(asa_id=asa_id,
                               asa_creator_address=None,
                               collection_id=None,
                               price=price,
                               seller=atomic_transfer.transactions[0].sender,
                               time=atomic_transfer.block_time,
                               block=atomic_transfer.block,
                               creator_fee=round(royalty_amount / price * 100, 2),
                               marketplace_fee=round(marketplace_amount / price * 100, 2),
                               referral_fee=REFERRAL_FEE,
                               delisting_time=None,
                               delisting_block=None,
                               app_id=None,
                               smart_signature_bytes=teal.teal_bytes,
                               smart_signature_address=teal.address,
                               smart_signature_tx_id=teal.tx_id)

    @staticmethod
    def init_from_teal(teal: Teal, atomic_transfer: AtomicTransfer):

        try:
            return ALGOxNFTListing.init_from_3_transactions(teal=teal, atomic_transfer=atomic_transfer)
        except:
            pass

        raise NotImplementedError
