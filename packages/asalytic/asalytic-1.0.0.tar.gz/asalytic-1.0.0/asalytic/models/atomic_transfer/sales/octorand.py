from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["OctorandSale"]


class OctorandSale(ASASale):
    sale_platform = "Octorand"

    @staticmethod
    def init_from_3_transactions(atomic_transfer: AtomicTransfer):
        # ow+jqfgCQZ25J6isfX1lZZj+yRqOSLY1aNVpOT+eI0A=
        # round: 19038349

        transaction_order = [
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        inner_transaction_order = [
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        price = atomic_transfer.transactions[1].payment_transaction.amount + \
                atomic_transfer.transactions[2].payment_transaction.amount

        return OctorandSale(seller=atomic_transfer.transactions[1].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[1].sender,
                            price=price,
                            platform_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                            creator_fee=0,
                            seller_price=atomic_transfer.transactions[1].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/x%2FWv1U1ET6Pi7v8OJw8bFkRjTgT%2BMWxL5iE8ovoHvnQ%3D
        # x/Wv1U1ET6Pi7v8OJw8bFkRjTgT+MWxL5iE8ovoHvnQ=
        # 19506710

        transaction_order = [
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        inner_transaction_order = [
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        price = atomic_transfer.transactions[1].payment_transaction.amount + \
                atomic_transfer.transactions[2].payment_transaction.amount + \
                atomic_transfer.transactions[3].payment_transaction.amount

        return OctorandSale(seller=atomic_transfer.transactions[1].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[1].sender,
                            price=price,
                            platform_fee=price - atomic_transfer.transactions[1].payment_transaction.amount,
                            creator_fee=0,
                            seller_price=atomic_transfer.transactions[1].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_5_transactions(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/IeM27YfWBCrbMfNg5AzjtIGd%2FATElmhqpmz5MX9CmR0%3D
        # IeM27YfWBCrbMfNg5AzjtIGd/ATElmhqpmz5MX9CmR0=
        # 19340966

        transaction_order = [
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        inner_transaction_order = [
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transaction_order):
            raise NotImplementedError("Invalid inner transaction order")

        price = 0
        for p_txn in atomic_transfer.payment_transactions:
            price += p_txn.payment_transaction.amount

        seller_price = atomic_transfer.transactions[1].payment_transaction.amount

        return OctorandSale(seller=atomic_transfer.transactions[1].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[1].sender,
                            price=price,
                            platform_fee=price - seller_price,
                            creator_fee=0,
                            seller_price=seller_price,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):

        try:
            return OctorandSale.init_from_3_transactions(atomic_transfer)
        except NotImplementedError:
            pass

        try:
            return OctorandSale.init_from_4_transactions(atomic_transfer)
        except NotImplementedError:
            pass

        try:
            return OctorandSale.init_from_5_transactions(atomic_transfer)
        except NotImplementedError:
            pass

        raise NotImplementedError
