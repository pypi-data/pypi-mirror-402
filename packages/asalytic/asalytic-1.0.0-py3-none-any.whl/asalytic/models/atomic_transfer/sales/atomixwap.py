from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["Atomixwap"]


class Atomixwap(ASASale):
    sale_platform = "Atomixwap"

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/94rbE5lqnsMr%2Bn4NR15DajdqNIMFz1oHyTcd%2FgdVilQ%3D
        94rbE5lqnsMr+n4NR15DajdqNIMFz1oHyTcd/gdVilQ=
        block: 21901587
        """

        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction types")

        price = 0
        for txn in atomic_transfer.payment_transactions:
            price += txn.payment_transaction.amount

        if atomic_transfer.transactions[1].note != 'YXRvbWl4d2Fw':
            raise NotImplementedError("Invalid transaction note")

        return Atomixwap(seller=atomic_transfer.transactions[2].payment_transaction.receiver,
                         buyer=atomic_transfer.transactions[1].asset_transfer_transaction.receiver,
                         price=price,
                         platform_fee=0,
                         creator_fee=atomic_transfer.transactions[3].payment_transaction.amount,
                         seller_price=atomic_transfer.transactions[2].payment_transaction.amount,
                         time=atomic_transfer.block_time,
                         asa_id=atomic_transfer.asa_id,
                         sale_type=SaleType.buy_now,
                         group_id=atomic_transfer.group_id,
                         block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError("Invalid number of transferred ASAs")

        try:
            buy = Atomixwap.init_from_4_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
