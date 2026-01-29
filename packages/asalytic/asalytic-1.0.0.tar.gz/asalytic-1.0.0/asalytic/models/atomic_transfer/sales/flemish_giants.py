from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["FlemishGiantsSale"]


class FlemishGiantsSale(ASASale):
    sale_platform = "Flemish Giants"

    @staticmethod
    def init_from_2_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/cF4Ff7ky5QFqHCc4JJxgiBxTD0NMz7pF2qdG7ugdfGs%3D
        cF4Ff7ky5QFqHCc4JJxgiBxTD0NMz7pF2qdG7ugdfGs=
        block: 20553642
        """

        transaction_order = [
            TransactionType.payment,
            TransactionType.application_call,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid Transaction Order")

        inner_transactions_order = [
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid Inner Transaction Order")

        seller = atomic_transfer.transactions[1].inner_txns[0].payment_transaction.receiver

        return FlemishGiantsSale(seller=seller,
                                 buyer=atomic_transfer.transactions[0].sender,
                                 price=atomic_transfer.transactions[0].payment_transaction.amount,
                                 platform_fee=0,
                                 creator_fee=0,
                                 seller_price=atomic_transfer.transactions[0].payment_transaction.amount,
                                 time=atomic_transfer.block_time,
                                 asa_id=atomic_transfer.asa_id,
                                 sale_type=SaleType.shuffle,
                                 group_id=atomic_transfer.group_id,
                                 block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError("Invalid number of transferred ASAs")

        try:
            buy = FlemishGiantsSale.init_from_2_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
