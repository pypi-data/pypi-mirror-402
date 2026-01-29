from asalytic.models import Listing, ListingType, Teal
from asalytic.models.algorand import AtomicTransfer, TransactionType

REFERRAL_FEE = 50

ASA_ID_LINE = 1
ROYALTY_LINE = 142
SELLER_AMOUNT_LINE = 154
MARKETPLACE_FEE_LINE = 166


class AsalyticListing(Listing):
    platform = "Asalytic"
    type = ListingType.smart_signature

    @staticmethod
    def init_from_4_transactions(teal: Teal, atomic_transfer: AtomicTransfer):

        transaction_order = [
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order.")

        teal_lines = teal.decompiled_teal.split('\n')

        asa_id = int(teal_lines[153].split("//")[-1].replace(" ", ""))

        royalty_amount = int(teal_lines[133].split(' ')[1])
        seller_amount = int(teal_lines[77].split(' ')[1])
        contract_fee = int(teal_lines[113].split("//")[-1].replace(" ", ""))

        seller_wallet = teal_lines[74].split("bytec_0 // addr")[-1].replace(" ", "")
        listing_side_wallet = teal_lines[93].split("// addr")[-1].replace(" ", "")
        creator_wallet = teal_lines[129].split("// addr")[-1].replace(" ", "")

        price = royalty_amount + seller_amount + contract_fee + contract_fee

        if asa_id != atomic_transfer.transactions[1].asset_transfer_transaction.asset_id:
            raise NotImplementedError

        if asa_id != atomic_transfer.transactions[2].asset_transfer_transaction.asset_id:
            raise NotImplementedError

        if asa_id != atomic_transfer.transactions[3].asset_transfer_transaction.asset_id:
            raise NotImplementedError

        if seller_wallet != atomic_transfer.transactions[3].sender:
            raise NotImplementedError

        return AsalyticListing(asa_id=asa_id,
                               asa_creator_address=None,
                               collection_id=None,
                               price=price,
                               seller=seller_wallet,
                               time=atomic_transfer.block_time,
                               block=atomic_transfer.block,
                               creator_fee=round(royalty_amount / price * 100, 2),
                               marketplace_fee=round(2 * contract_fee / price * 100, 2),
                               referral_fee=REFERRAL_FEE,
                               delisting_time=None,
                               delisting_block=None,
                               app_id=None,
                               smart_signature_bytes=teal.teal_bytes,
                               smart_signature_address=teal.address,
                               smart_signature_tx_id=teal.tx_id,
                               a_seller_amount=seller_amount,
                               a_contract_amount=contract_fee,
                               a_creator_amount=royalty_amount,
                               a_seller_wallet=seller_wallet,
                               a_listing_wallet=listing_side_wallet,
                               a_creator_wallet=creator_wallet
                               )

    @staticmethod
    def init_from_teal(teal: Teal, atomic_transfer: AtomicTransfer):

        try:
            return AsalyticListing.init_from_4_transactions(teal=teal, atomic_transfer=atomic_transfer)
        except:
            pass

        raise NotImplementedError
