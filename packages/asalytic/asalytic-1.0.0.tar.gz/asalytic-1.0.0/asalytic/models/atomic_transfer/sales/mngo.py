from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["MNGOSale"]


class MNGOSale(ASASale):
    sale_platform = "Mostly Frens"

    @staticmethod
    def init_from_6_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/FeCsCs8slza5do9eckRK3XRZucFjWkrw7MvHdH1n3u8%3D
        FeCsCs8slza5do9eckRK3XRZucFjWkrw7MvHdH1n3u8=
        block: 22337688
        """

        transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_config,

        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction type")

        price = 0
        for txn in atomic_transfer.payment_transactions:
            price += txn.payment_transaction.amount

        return MNGOSale(seller=atomic_transfer.transactions[0].payment_transaction.receiver,
                        buyer=atomic_transfer.transactions[0].sender,
                        price=price,
                        platform_fee=price - atomic_transfer.payment_transactions[0].payment_transaction.amount,
                        creator_fee=0,
                        seller_price=atomic_transfer.payment_transactions[0].payment_transaction.amount,
                        time=atomic_transfer.block_time,
                        asa_id=atomic_transfer.asa_id,
                        sale_type=SaleType.buy_now,
                        group_id=atomic_transfer.group_id,
                        block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError("Invalid number of transferred ASAs.")

        try:
            buy = MNGOSale.init_from_6_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
