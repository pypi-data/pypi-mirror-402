from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["NFDSale"]


class NFDSale(ASASale):
    sale_platform = "NFD"

    @staticmethod
    def init_from_3_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/9l288X9QWV5vsNklfKtGhf4QSHNWo1bOMEoSlgT4sYk%3D
        # 9l288X9QWV5vsNklfKtGhf4QSHNWo1bOMEoSlgT4sYk=
        # 21661042
        """

        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        inner_transactions_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        price = atomic_transfer.transactions[2].inner_txns[0].payment_transaction.amount + \
                atomic_transfer.transactions[2].inner_txns[1].payment_transaction.amount

        seller = atomic_transfer.transactions[2].inner_txns[0].payment_transaction.receiver
        buyer = atomic_transfer.transactions[1].sender

        platform_fee = atomic_transfer.transactions[2].inner_txns[1].payment_transaction.amount
        seller_price = atomic_transfer.transactions[2].inner_txns[0].payment_transaction.amount

        return NFDSale(seller=seller,
                       buyer=buyer,
                       price=price,
                       platform_fee=platform_fee,
                       creator_fee=0,
                       seller_price=seller_price,
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
            buy = NFDSale.init_from_3_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
