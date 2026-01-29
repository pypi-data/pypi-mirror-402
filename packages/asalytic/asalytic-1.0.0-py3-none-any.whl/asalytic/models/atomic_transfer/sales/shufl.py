from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["ShuflSale"]


class ShuflSale(ASASale):
    sale_platform = "Shufl"

    @staticmethod
    def init_from_11_transactions_offer(atomic_transfer: AtomicTransfer):
        """
        offer
        https://algoexplorer.io/tx/group/0ctNMy1NMBBNhej43TtzUNZ6FG%2BxagA0PEe7G2bYJxE%3D
        0ctNMy1NMBBNhej43TtzUNZ6FG+xagA0PEe7G2bYJxE=
        23098534
        """

        transaction_order = [
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.application_call,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        inner_transactions_order = [
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        platform_fees = atomic_transfer.all_transactions[1].payment_amount + \
                        atomic_transfer.all_transactions[3].payment_amount

        creator_fees = atomic_transfer.all_transactions[5].payment_amount

        seller_price = atomic_transfer.all_transactions[7].payment_amount + \
                       atomic_transfer.all_transactions[10].close_amount

        price = platform_fees + creator_fees + seller_price

        seller = atomic_transfer.all_transactions[7].payment_transaction.receiver
        buyer = atomic_transfer.all_transactions[8].asset_transfer_transaction.receiver

        return ShuflSale(seller=seller,
                         buyer=buyer,
                         price=price,
                         platform_fee=platform_fees,
                         creator_fee=creator_fees,
                         seller_price=seller_price,
                         time=atomic_transfer.block_time,
                         asa_id=atomic_transfer.asa_id,
                         sale_type=SaleType.offer,
                         group_id=atomic_transfer.group_id,
                         block_number=atomic_transfer.block)

    @staticmethod
    def init_from_12_transactions_offer(atomic_transfer: AtomicTransfer):
        """
        offer
        https://algoexplorer.io/tx/group/CL4t0haMQl8x4IUOAdkv7szPDW5fAGmpDatpDeHvP5k%3D
        CL4t0haMQl8x4IUOAdkv7szPDW5fAGmpDatpDeHvP5k=
        23032537
        """

        transaction_order = [
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.application_call,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        inner_transactions_order = [
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        platform_fees = atomic_transfer.all_transactions[1].payment_amount + \
                        atomic_transfer.all_transactions[3].payment_amount + \
                        atomic_transfer.all_transactions[8].payment_amount

        creator_fees = atomic_transfer.all_transactions[5].payment_amount

        seller_price = atomic_transfer.all_transactions[7].payment_amount + \
                       atomic_transfer.all_transactions[11].payment_amount + \
                       atomic_transfer.all_transactions[11].close_amount

        price = platform_fees + creator_fees + seller_price

        seller = atomic_transfer.all_transactions[7].payment_transaction.receiver

        buyer = atomic_transfer.all_transactions[9].asset_transfer_transaction.receiver

        return ShuflSale(seller=seller,
                         buyer=buyer,
                         price=price,
                         platform_fee=platform_fees,
                         creator_fee=creator_fees,
                         seller_price=seller_price,
                         time=atomic_transfer.block_time,
                         asa_id=atomic_transfer.asa_id,
                         sale_type=SaleType.offer,
                         group_id=atomic_transfer.group_id,
                         block_number=atomic_transfer.block)

    @staticmethod
    def init_from_12_transactions_buy(atomic_transfer: AtomicTransfer):
        """
        buy
        https://algoexplorer.io/tx/group/o%2Fuv3HI2n3%2FlgJu5UZ%2Fnl5FA08J%2B1V%2BXD%2F8PfJI3v8s%3D
        o/uv3HI2n3/lgJu5UZ/nl5FA08J+1V+XD/8PfJI3v8s=
        23097987
        """

        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.application_call,
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
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        platform_fees = atomic_transfer.all_transactions[3].payment_amount + \
                        atomic_transfer.all_transactions[4].payment_amount

        creator_fees = atomic_transfer.all_transactions[6].payment_amount

        seller_price = atomic_transfer.all_transactions[9].payment_amount + \
                       atomic_transfer.all_transactions[11].close_amount

        price = platform_fees + creator_fees + seller_price

        seller = atomic_transfer.all_transactions[9].payment_transaction.receiver
        buyer = atomic_transfer.all_transactions[1].sender

        return ShuflSale(seller=seller,
                         buyer=buyer,
                         price=price,
                         platform_fee=platform_fees,
                         creator_fee=creator_fees,
                         seller_price=seller_price,
                         time=atomic_transfer.block_time,
                         asa_id=atomic_transfer.asa_id,
                         sale_type=SaleType.buy_now,
                         group_id=atomic_transfer.group_id,
                         block_number=atomic_transfer.block)

    @staticmethod
    def init_from_13_transactions_buy(atomic_transfer: AtomicTransfer):
        """
        buy
        https://algoexplorer.io/tx/group/uphxuRCMqeuxLrObgGJ61aVaUn9XKczlS%2FqCmIRlAK4%3D
        uphxuRCMqeuxLrObgGJ61aVaUn9XKczlS/qCmIRlAK4=
        23030399
        """

        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.application_call,
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
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        platform_fees = atomic_transfer.all_transactions[3].payment_amount + \
                        atomic_transfer.all_transactions[4].payment_amount + \
                        atomic_transfer.all_transactions[10].payment_amount

        creator_fees = atomic_transfer.all_transactions[6].payment_amount

        seller_price = atomic_transfer.all_transactions[9].payment_amount + \
                       atomic_transfer.all_transactions[12].close_amount

        price = platform_fees + creator_fees + seller_price

        seller = atomic_transfer.all_transactions[9].payment_transaction.receiver
        buyer = atomic_transfer.all_transactions[1].sender

        return ShuflSale(seller=seller,
                         buyer=buyer,
                         price=price,
                         platform_fee=platform_fees,
                         creator_fee=creator_fees,
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
            buy = ShuflSale.init_from_11_transactions_offer(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ShuflSale.init_from_12_transactions_offer(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ShuflSale.init_from_12_transactions_buy(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ShuflSale.init_from_13_transactions_buy(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
