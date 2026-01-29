from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType
from asalytic.models.atomic_transfer.sales.algoxnft import ALGOxNFT_BANK_ADDRESS

__all__ = ["DartroomSale"]


class DartroomSale(ASASale):
    sale_platform = "Dartroom"

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/xFfa4wEJR9C1pI30MAaVqWvjyweHvM8pBqnr2RZBoOA%3D
        xFfa4wEJR9C1pI30MAaVqWvjyweHvM8pBqnr2RZBoOA=
        block: 19339085
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        # Atomixwap
        if atomic_transfer.transactions[1].note == 'YXRvbWl4d2Fw':
            raise NotImplementedError("Invalid transaction note.")

        price = 0
        for p_txn in atomic_transfer.payment_transactions:
            price += p_txn.payment_transaction.amount

        return DartroomSale(seller=atomic_transfer.transactions[2].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[1].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[3].payment_transaction.amount,
                            creator_fee=0,
                            seller_price=atomic_transfer.transactions[2].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_5_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/8d3BnA2EAmGp2F4CoZ2z4oO0lCGgfQ7UKaokzAVzq7E%3D
        8d3BnA2EAmGp2F4CoZ2z4oO0lCGgfQ7UKaokzAVzq7E=
        block: 19636860
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError

        price = 0
        for p_txn in atomic_transfer.payment_transactions:
            price += p_txn.payment_transaction.amount

        # ALGOxNFT
        if atomic_transfer.payment_transactions[1].payment_transaction.receiver == ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        return DartroomSale(seller=atomic_transfer.transactions[2].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[1].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[4].payment_transaction.amount,
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
            buy = DartroomSale.init_from_4_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = DartroomSale.init_from_5_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
