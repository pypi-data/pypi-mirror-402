from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["AlgorillasExchangeSale"]


class AlgorillasExchangeSale(ASASale):
    sale_platform = "Algorillas Exchange"

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/A6ZxDxjPi5NbbH5Fr%2FkZYN6E%2FIfmd1tcDA5s%2BDJTKbY%3D
        A6ZxDxjPi5NbbH5Fr/kZYN6E/Ifmd1tcDA5s+DJTKbY=
        26144396
        """

        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.application_call,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        inner_transactions_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        return AlgorillasExchangeSale(seller=atomic_transfer.transactions[2].inner_txns[1].payment_transaction.receiver,
                                      buyer=atomic_transfer.transactions[1].sender,
                                      price=atomic_transfer.transactions[1].payment_transaction.amount,
                                      platform_fee=0,
                                      creator_fee=0,
                                      seller_price=atomic_transfer.transactions[1].payment_transaction.amount,
                                      time=atomic_transfer.block_time,
                                      asa_id=atomic_transfer.asa_id,
                                      sale_type=SaleType.buy_now,
                                      group_id=atomic_transfer.group_id,
                                      block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError("Invalid number of transferred ASAs.")

        if atomic_transfer.highest_payment_amount is not None and atomic_transfer.highest_payment_amount < 1000000:
            raise NotImplementedError("Highest sale below 1A")

        try:
            buy = AlgorillasExchangeSale.init_from_4_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
