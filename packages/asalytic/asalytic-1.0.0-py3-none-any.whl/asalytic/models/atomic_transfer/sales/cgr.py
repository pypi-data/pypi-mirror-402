from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["CGRSale"]

BANK_ADDRESS = 'ROBOTEKTU645GDM42JVHV6MIOM2YOGF4JK2YRPFXNG7XLJWPCBPBBH7WOI'


class CGRSale(ASASale):
    sale_platform = "Crazy Goose Robots"

    @staticmethod
    def init_from_5_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/yzhZ4YszWHu0dOtnxePECdwgdZyMkhk%2BD96%2BxsP9jU4%3D
        yzhZ4YszWHu0dOtnxePECdwgdZyMkhk+D96+xsP9jU4=
        28180370
        """

        transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_config,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        price = 0
        for t in atomic_transfer.payment_transactions:
            price += t.payment_transaction.amount

        # Bank Address for Robots.
        if atomic_transfer.payment_transactions[1].payment_transaction.receiver != BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        return CGRSale(seller=atomic_transfer.transactions[1].payment_transaction.receiver,
                       buyer=atomic_transfer.transactions[3].asset_transfer_transaction.receiver,
                       price=price,
                       platform_fee=0,
                       creator_fee=0,
                       seller_price=price,
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
            buy = CGRSale.init_from_5_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
