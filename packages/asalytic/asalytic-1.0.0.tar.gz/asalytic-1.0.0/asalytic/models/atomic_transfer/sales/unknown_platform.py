from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["UnknownPlatformSale"]


class UnknownPlatformSale(ASASale):
    sale_platform = "Unknown Platform"

    @staticmethod
    def init_from_3_transactions(atomic_transfer: AtomicTransfer):
        """
        UAJ8yMMpMBftLZsbwoP9oZhjctAlJcHdvuZkfg3YsV8=
        42658742
        """
        transaction_order = [
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError

        if atomic_transfer.payment_transactions[0].payment_transaction.receiver != "7PWMEGVTGLHQ427HEWC4ZNYYOHPXKUIANUUMSWPLEFMI7KNNJU6PG4WHZM":
            # not maars
            raise NotImplementedError

        return UnknownPlatformSale(seller=atomic_transfer.payment_transactions[0].payment_transaction.receiver,
                                   buyer=atomic_transfer.payment_transactions[0].sender,
                                   price=atomic_transfer.payment_transactions[0].payment_transaction.amount,
                                   platform_fee=0,
                                   creator_fee=0,
                                   seller_price=atomic_transfer.payment_transactions[0].payment_transaction.amount,
                                   time=atomic_transfer.block_time,
                                   asa_id=atomic_transfer.asa_id,
                                   sale_type=SaleType.buy_now,
                                   group_id=atomic_transfer.group_id,
                                   block_number=atomic_transfer.block)

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/AKaOYuQ%2BuWOaNBl0gGykc2sZJtg0A%2Bpk9rV7gQ
        AKaOYuQ+uWOaNBl0gGykc2sZJtg0A+pk9rV7gQ7nDQI=
        block: 20651171
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError

        price = 0
        for p_txn in atomic_transfer.payment_transactions:
            price += p_txn.payment_transaction.amount

        return UnknownPlatformSale(seller=atomic_transfer.transactions[1].payment_transaction.receiver,
                                   buyer=atomic_transfer.transactions[0].asset_transfer_transaction.receiver,
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
    def init_from_4_transactions_1(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/8pKlDYvXCLoS0ZjXlNDXiwYs8PsK6lD22WpEY9BcYJU%3D
        8pKlDYvXCLoS0ZjXlNDXiwYs8PsK6lD22WpEY9BcYJU=
        block: 34156830
        """
        transaction_order = [
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_config,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError

        payment_txn = atomic_transfer.payment_transactions[0]

        if payment_txn.payment_transaction.receiver != 'GOODBOISQJDPGS5BWRRIMIPYVCSMMPJ7X7U76YFGRNYFXZG6ZRSC32XPEU':
            raise NotImplementedError

        return UnknownPlatformSale(seller=payment_txn.payment_transaction.receiver,
                                   buyer=payment_txn.sender,
                                   price=payment_txn.payment_amount,
                                   platform_fee=0,
                                   creator_fee=0,
                                   seller_price=payment_txn.payment_amount,
                                   time=atomic_transfer.block_time,
                                   asa_id=atomic_transfer.asa_id,
                                   sale_type=SaleType.buy_now,
                                   group_id=atomic_transfer.group_id,
                                   block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError("Invalid number of ASAs transferred")

        try:
            buy = UnknownPlatformSale.init_from_3_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass


        try:
            buy = UnknownPlatformSale.init_from_4_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = UnknownPlatformSale.init_from_4_transactions_1(atomic_transfer)
            return buy
        except NotImplementedError:
            pass


        raise NotImplementedError
