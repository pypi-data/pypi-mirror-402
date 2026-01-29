from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType
import json
import base64

__all__ = ["EXASale"]

EXA_BANK_ADDRESS = 'HCHP4KJ3I3CXQZATZWYHUJUTOKQ4YJRRIV2Y45FTEVGVL5OJQ3L35VFDZQ'


class EXASale(ASASale):
    sale_platform = "EXA Market"

    @staticmethod
    def init_from_6_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/GNGbPhtz0PPvkOEDvcb2qHP2QF5LBtTH%2FIDuXRtz07c%3D
        GNGbPhtz0PPvkOEDvcb2qHP2QF5LBtTH/IDuXRtz07c=
        24613016
        """
        inner_transaction_order = [
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        price = atomic_transfer.payment_transactions[0].payment_amount + \
                atomic_transfer.payment_transactions[1].payment_amount

        # Bank Address for EXA.
        if atomic_transfer.payment_transactions[0].payment_transaction.receiver != EXA_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        return EXASale(seller=atomic_transfer.transactions[1].inner_txns[1].payment_transaction.receiver,
                       buyer=atomic_transfer.transactions[1].inner_txns[2].asset_transfer_transaction.receiver,
                       price=price,
                       platform_fee=atomic_transfer.transactions[1].inner_txns[0].payment_transaction.amount,
                       creator_fee=0,
                       seller_price=atomic_transfer.transactions[1].inner_txns[1].payment_transaction.amount,
                       time=atomic_transfer.block_time,
                       asa_id=atomic_transfer.asa_id,
                       sale_type=SaleType.buy_now,
                       group_id=atomic_transfer.group_id,
                       block_number=atomic_transfer.block)

    @staticmethod
    def init_from_7_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/ak8%2BJ%2F6tAHbFmD3SrwjRIu7LYG3CSZDS2F8ntAnTTko%3D
        ak8+J/6tAHbFmD3SrwjRIu7LYG3CSZDS2F8ntAnTTko=
        24723280
        """
        inner_transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        price = atomic_transfer.payment_transactions[0].payment_amount + \
                atomic_transfer.payment_transactions[1].payment_amount

        # Bank Address for EXA.
        if atomic_transfer.payment_transactions[0].payment_transaction.receiver != EXA_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        return EXASale(seller=atomic_transfer.transactions[2].inner_txns[2].payment_transaction.receiver,
                       buyer=atomic_transfer.transactions[2].inner_txns[0].asset_transfer_transaction.receiver,
                       price=price,
                       platform_fee=atomic_transfer.transactions[2].inner_txns[1].payment_transaction.amount,
                       creator_fee=0,
                       seller_price=atomic_transfer.transactions[2].inner_txns[2].payment_transaction.amount,
                       time=atomic_transfer.block_time,
                       asa_id=atomic_transfer.asa_id,
                       sale_type=SaleType.offer,
                       group_id=atomic_transfer.group_id,
                       block_number=atomic_transfer.block)

    @staticmethod
    def init_from_7_transactions_auction(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/MUaibkwqcg6YkLdF9QSLGEZwafjJ67KM33OsRznXKSo%3D
        MUaibkwqcg6YkLdF9QSLGEZwafjJ67KM33OsRznXKSo=
        24769154
        """
        inner_transaction_order = [
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        price = atomic_transfer.payment_transactions[0].payment_amount + \
                atomic_transfer.payment_transactions[1].payment_amount + \
                atomic_transfer.payment_transactions[2].payment_amount

        # Bank Address for EXA.
        if atomic_transfer.payment_transactions[1].payment_transaction.receiver != EXA_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        return EXASale(seller=atomic_transfer.transactions[1].inner_txns[1].payment_transaction.receiver,
                       buyer=atomic_transfer.transactions[1].inner_txns[2].asset_transfer_transaction.receiver,
                       price=price,
                       platform_fee=atomic_transfer.transactions[1].inner_txns[0].payment_transaction.amount,
                       creator_fee=atomic_transfer.transactions[0].inner_txns[0].payment_transaction.amount,
                       seller_price=atomic_transfer.transactions[1].inner_txns[1].payment_transaction.amount,
                       time=atomic_transfer.block_time,
                       asa_id=atomic_transfer.asa_id,
                       sale_type=SaleType.auction,
                       group_id=atomic_transfer.group_id,
                       block_number=atomic_transfer.block)

    @staticmethod
    def init_from_8_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/lKoxrjF7qeyCtohTqg8VJlexAeAKEu8w%2FXgxh1DPFzM%3D
        lKoxrjF7qeyCtohTqg8VJlexAeAKEu8w/Xgxh1DPFzM=
        24336858
        """
        inner_transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        price = atomic_transfer.payment_transactions[0].payment_amount

        # Bank Address for EXA.
        if atomic_transfer.payment_transactions[1].payment_transaction.receiver != EXA_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        purchase_platform = "EXA Market"

        # TODO: This is not the right place for this.
        try:
            txn_note = atomic_transfer.payment_transactions[0].note

            if txn_note is not None:
                platform_note = json.loads(base64.b64decode(txn_note).decode('utf-8'))
                platform_name = platform_note.get('platform', None)
                if platform_name == "asalytic":
                    purchase_platform = "Asalytic"
        except:
            pass

        return EXASale(seller=atomic_transfer.transactions[3].inner_txns[1].payment_transaction.receiver,
                       buyer=atomic_transfer.transactions[3].inner_txns[2].asset_transfer_transaction.receiver,
                       price=price,
                       platform_fee=atomic_transfer.transactions[3].inner_txns[0].payment_transaction.amount,
                       creator_fee=0,
                       seller_price=atomic_transfer.transactions[3].inner_txns[1].payment_transaction.amount,
                       time=atomic_transfer.block_time,
                       asa_id=atomic_transfer.asa_id,
                       sale_type=SaleType.buy_now,
                       group_id=atomic_transfer.group_id,
                       block_number=atomic_transfer.block,
                       sale_platform=purchase_platform)

    @staticmethod
    def init_from_9_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/3rI6HLv0IhGBCQK0pk0gVbmgNB57nZ6fz4bdHkC19L8%3D
        3rI6HLv0IhGBCQK0pk0gVbmgNB57nZ6fz4bdHkC19L8=
        24722397
        """
        inner_transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        price = atomic_transfer.payment_transactions[0].payment_amount

        # Bank Address for EXA.
        if atomic_transfer.payment_transactions[1].payment_transaction.receiver != EXA_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        purchase_platform = "EXA Market"

        try:
            txn_note = atomic_transfer.payment_transactions[0].note

            if txn_note is not None:
                platform_note = json.loads(base64.b64decode(txn_note).decode('utf-8'))
                platform_name = platform_note.get('platform', None)
                if platform_name == "asalytic":
                    purchase_platform = "Asalytic"
        except:
            pass

        return EXASale(seller=atomic_transfer.transactions[4].inner_txns[1].payment_transaction.receiver,
                       buyer=atomic_transfer.transactions[4].inner_txns[2].asset_transfer_transaction.receiver,
                       price=price,
                       platform_fee=atomic_transfer.transactions[4].inner_txns[0].payment_transaction.amount,
                       creator_fee=0,
                       seller_price=atomic_transfer.transactions[4].inner_txns[1].payment_transaction.amount,
                       time=atomic_transfer.block_time,
                       asa_id=atomic_transfer.asa_id,
                       sale_type=SaleType.buy_now,
                       group_id=atomic_transfer.group_id,
                       block_number=atomic_transfer.block,
                       sale_platform=purchase_platform)

    @staticmethod
    def init_from_10_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/GNZOmFdhHcmgOHlMPua%2FZzmqkBMuBQ8a6qb08wBxzgQ%3D
        GNZOmFdhHcmgOHlMPua/ZzmqkBMuBQ8a6qb08wBxzgQ=
        24278375
        """
        inner_transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        price = atomic_transfer.payment_transactions[0].payment_amount

        # Bank Address for EXA.
        if atomic_transfer.payment_transactions[2].payment_transaction.receiver != EXA_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        purchase_platform = "EXA Market"

        try:
            txn_note = atomic_transfer.payment_transactions[0].note

            if txn_note is not None:
                platform_note = json.loads(base64.b64decode(txn_note).decode('utf-8'))
                platform_name = platform_note.get('platform', None)
                if platform_name == "asalytic":
                    purchase_platform = "Asalytic"
        except:
            pass

        return EXASale(seller=atomic_transfer.transactions[4].inner_txns[1].payment_transaction.receiver,
                       buyer=atomic_transfer.transactions[4].inner_txns[2].asset_transfer_transaction.receiver,
                       price=price,
                       platform_fee=atomic_transfer.transactions[4].inner_txns[0].payment_transaction.amount,
                       creator_fee=atomic_transfer.transactions[3].inner_txns[0].payment_transaction.amount,
                       seller_price=atomic_transfer.transactions[4].inner_txns[1].payment_transaction.amount,
                       time=atomic_transfer.block_time,
                       asa_id=atomic_transfer.asa_id,
                       sale_type=SaleType.buy_now,
                       group_id=atomic_transfer.group_id,
                       block_number=atomic_transfer.block,
                       sale_platform=purchase_platform)

    @staticmethod
    def init_from_8_transactions_offer(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/O7U8A69dtsriUQt9DJ1gE0zVaT4HQjgjVL3hiQrL5GM%3D
        O7U8A69dtsriUQt9DJ1gE0zVaT4HQjgjVL3hiQrL5GM=
        24279614
        """
        inner_transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        price = atomic_transfer.payment_transactions[0].payment_amount + \
                atomic_transfer.payment_transactions[1].payment_amount + \
                atomic_transfer.payment_transactions[2].payment_amount

        # Bank Address for EXA.
        if atomic_transfer.payment_transactions[1].payment_transaction.receiver != EXA_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        return EXASale(seller=atomic_transfer.transactions[2].inner_txns[3].payment_transaction.receiver,
                       buyer=atomic_transfer.transactions[2].inner_txns[0].asset_transfer_transaction.receiver,
                       price=price,
                       platform_fee=atomic_transfer.transactions[2].inner_txns[2].payment_transaction.amount,
                       creator_fee=atomic_transfer.transactions[2].inner_txns[1].payment_transaction.amount,
                       seller_price=atomic_transfer.transactions[2].inner_txns[3].payment_transaction.amount,
                       time=atomic_transfer.block_time,
                       asa_id=atomic_transfer.asa_id,
                       sale_type=SaleType.offer,
                       group_id=atomic_transfer.group_id,
                       block_number=atomic_transfer.block)

    @staticmethod
    def init_from_5_transactions_drop_sale(atomic_transfer: AtomicTransfer):
        """
        https://allo.info/tx/WFC6DP6YP6BFARIF4K4X6SLBP72RBB2UZYGJLGE7BRAU34ADO5UA/group
        block: 43558070
        group:Yx8iehsb6qWYLC19TS8gRoNfjwE8G91J3NTxwPQg6mg=
        """
        inner_transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        # Bank Address for EXA.
        if atomic_transfer.payment_transactions[2].payment_transaction.receiver != EXA_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        purchase_platform = "EXA Market"

        try:
            txn_note = atomic_transfer.payment_transactions[0].note

            if txn_note is not None:
                platform_note = json.loads(base64.b64decode(txn_note).decode('utf-8'))
                platform_name = platform_note.get('platform', None)
                if platform_name == "asalytic":
                    purchase_platform = "Asalytic"
        except:
            pass

        creator_fee = atomic_transfer.payment_transactions[0].payment_amount
        seller_fee = atomic_transfer.payment_transactions[1].payment_amount
        platform_fee = atomic_transfer.payment_transactions[2].payment_amount
        price = creator_fee + seller_fee + platform_fee

        return EXASale(seller=atomic_transfer.payment_transactions[1].payment_transaction.receiver,
                       buyer=atomic_transfer.asset_transfer_transactions[1].asset_transfer_transaction.receiver,
                       price=price,
                       platform_fee=platform_fee,
                       creator_fee=creator_fee,
                       seller_price=seller_fee,
                       time=atomic_transfer.block_time,
                       asa_id=atomic_transfer.asa_id,
                       sale_type=SaleType.shuffle,
                       group_id=atomic_transfer.group_id,
                       block_number=atomic_transfer.block,
                       sale_platform=purchase_platform)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError("Invalid number of transferred ASAs.")

        if atomic_transfer.highest_payment_amount is not None and atomic_transfer.highest_payment_amount < 1000000:
            raise NotImplementedError("Highest sale below 1A")

        try:
            buy = EXASale.init_from_5_transactions_drop_sale(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = EXASale.init_from_6_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = EXASale.init_from_7_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = EXASale.init_from_7_transactions_auction(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = EXASale.init_from_8_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = EXASale.init_from_9_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = EXASale.init_from_10_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = EXASale.init_from_8_transactions_offer(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
