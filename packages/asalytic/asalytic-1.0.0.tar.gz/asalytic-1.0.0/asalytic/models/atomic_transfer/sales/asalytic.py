from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType
from asalytic.models.atomic_transfer.sales.constants import ASALYTIC_VALID_FACTORY_APP_IDS
import json
import base64

__all__ = ["AsalyticSale"]

ALGOxNFT_BANK_ADDRESS = 'XNFT36FUCFRR6CK675FW4BEBCCCOJ4HOSMGCN6J2W6ZMB34KM2ENTNQCP4'


class AsalyticSale(ASASale):
    sale_platform = "Asalytic"

    @staticmethod
    def init_from_6_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/A81GNsBe%2FeuM3EYCt%2B7WoOSDcrjb8%2FzejDvX93qyoPU%3D
        A81GNsBe/euM3EYCt+7WoOSDcrjb8/zejDvX93qyoPU=
        22846451
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        price = 0
        for t in atomic_transfer.payment_transactions:
            price += t.payment_transaction.amount

        # Bank Address for ALGOxNFT.
        if atomic_transfer.payment_transactions[2].payment_transaction.receiver != ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        txn_note = atomic_transfer.payment_transactions[2].note

        if txn_note is None:
            raise NotImplementedError

        if txn_note is not None:
            platform_note = json.loads(base64.b64decode(txn_note).decode('utf-8'))
            platform_name = platform_note.get('platform', None)
            if platform_name is not None:
                if platform_name != "Asalytic":
                    raise NotImplementedError

        return AsalyticSale(seller=atomic_transfer.transactions[3].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[1].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[4].payment_transaction.amount,
                            creator_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[3].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_7_transactions(atomic_transfer: AtomicTransfer):
        """
        aw1xP2aEnn7Xvw+gEhHtkfEkTv/3QOEgR3hcqT5A3B0=
        38346683
        """
        inner_transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        valid_sender_address = True

        if atomic_transfer.transactions[0].sender != atomic_transfer.transactions[1].sender:
            valid_sender_address = False

        if atomic_transfer.transactions[0].sender != atomic_transfer.transactions[2].sender:
            valid_sender_address = False

        if atomic_transfer.transactions[0].sender != atomic_transfer.transactions[3].sender:
            valid_sender_address = False

        if atomic_transfer.transactions[0].sender != atomic_transfer.transactions[4].sender:
            valid_sender_address = False

        if atomic_transfer.transactions[5].asset_transfer_transaction.receiver != atomic_transfer.transactions[
            0].sender:
            valid_sender_address = False

        if atomic_transfer.transactions[5].sender != atomic_transfer.transactions[6].sender:
            valid_sender_address = False

        if not valid_sender_address:
            raise NotImplementedError

        if atomic_transfer.transactions[1].payment_amount != atomic_transfer.transactions[2].payment_amount:
            raise NotImplementedError

        price = 0
        price += atomic_transfer.transactions[0].payment_amount
        price += atomic_transfer.transactions[1].payment_amount
        price += atomic_transfer.transactions[2].payment_amount
        price += atomic_transfer.transactions[3].payment_amount

        platform_fee = 0
        platform_fee += atomic_transfer.transactions[1].payment_amount
        platform_fee += atomic_transfer.transactions[2].payment_amount

        return AsalyticSale(seller=atomic_transfer.transactions[0].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[0].sender,
                            price=price,
                            platform_fee=platform_fee,
                            creator_fee=atomic_transfer.transactions[3].payment_amount,
                            seller_price=atomic_transfer.transactions[0].payment_amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_12_transactions(atomic_transfer: AtomicTransfer):
        """
        KVIKUcE0KrTZGZLuKm5wdK0zbKCIASr7JH2XAPuraLk=
        39159553
        """
        inner_transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        if atomic_transfer.all_transactions[
            2].application_transaction.application_id not in ASALYTIC_VALID_FACTORY_APP_IDS:
            raise NotImplementedError("Invalid app ID")

        all_txns = atomic_transfer.all_transactions

        return AsalyticSale(seller=all_txns[9].payment_transaction.receiver,
                            buyer=all_txns[1].sender,
                            price=all_txns[1].payment_amount,
                            platform_fee=all_txns[7].payment_amount + all_txns[8].payment_amount,
                            creator_fee=all_txns[6].payment_amount,
                            seller_price=all_txns[9].payment_close_amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block,
                            a_listing_side=all_txns[7].payment_transaction.receiver,
                            a_buying_side=all_txns[8].payment_transaction.receiver)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError("Invalid number of transferred ASAs.")

        if atomic_transfer.highest_payment_amount is not None and atomic_transfer.highest_payment_amount < 1000000:
            raise NotImplementedError("Highest sale below 1A")

        try:
            buy = AsalyticSale.init_from_6_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = AsalyticSale.init_from_7_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = AsalyticSale.init_from_12_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
