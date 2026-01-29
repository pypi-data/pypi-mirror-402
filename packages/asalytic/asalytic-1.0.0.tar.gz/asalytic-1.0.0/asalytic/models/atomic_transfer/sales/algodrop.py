from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["AlgoDropSale"]


class AlgoDropSale(ASASale):
    sale_platform = "AlgoDrop"

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/ABCkNxi%2BAvIeWGqdmkArVDU9hxBDGhCD5VmhILuNEBE%3D
        ABCkNxi+AvIeWGqdmkArVDU9hxBDGhCD5VmhILuNEBE=
        block: 19850686
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order.")

        if 'BNK' != atomic_transfer.transactions[2].payment_transaction.receiver[:3]:
            raise NotImplementedError("Invalid marketplace address.")

        price = 0
        for p_txn in atomic_transfer.payment_transactions:
            price += p_txn.payment_transaction.amount

        return AlgoDropSale(seller=atomic_transfer.transactions[1].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[3].asset_transfer_transaction.receiver,
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
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError(
                f"Invalid number of transferred ASAs {atomic_transfer.number_of_unique_asa_transferred}")

        try:
            buy = AlgoDropSale.init_from_4_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
