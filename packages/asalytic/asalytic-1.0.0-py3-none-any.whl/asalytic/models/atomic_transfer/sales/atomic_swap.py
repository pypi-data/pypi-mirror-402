from collections import defaultdict

from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["AtomicSwapSale"]


class AtomicSwapSale(ASASale):
    sale_platform = "Atomic Swap"

    @staticmethod
    def algoanna_lending_exception_2_transactions(atomic_transfer: AtomicTransfer) -> bool:
        # https://algoexplorer.io/tx/group/cKay2%2BAUFrYxcsI3NEjQTp2il2LipPyV%2FtbY7ZF0hqg%3D

        transaction_order = [
            TransactionType.application_call,
            TransactionType.asset_transfer,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        inner_transactions_order = [
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        valid_lender = atomic_transfer.transactions[0].inner_txns[0].payment_transaction.receiver == \
                       atomic_transfer.transactions[1].sender

        valid_receiver = atomic_transfer.transactions[0].inner_txns[0].sender == atomic_transfer.transactions[
            1].asset_transfer_transaction.receiver

        return valid_lender and valid_receiver

    @staticmethod
    def algoanna_lending_exception_3_transactions(atomic_transfer: AtomicTransfer) -> bool:
        # https://algoexplorer.io/tx/group/j0A6enhT4lmt%2FOVc2NMetJ4fRF7DwfRUv%2BXNiueH3qg%3D

        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.application_call,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        inner_transactions_order = [
            TransactionType.asset_transfer,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        valid_lender = atomic_transfer.transactions[1].inner_txns[0].asset_transfer_transaction.receiver == \
                       atomic_transfer.transactions[2].sender

        valid_receiver = atomic_transfer.transactions[1].inner_txns[0].sender == atomic_transfer.transactions[
            2].payment_transaction.receiver

        return valid_lender and valid_receiver

    @staticmethod
    def init_p2p_sale(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/6w5IdI7yP4qmiqGoOgGXCxwz2UR4k3oU8OI0KIEk%2B9Y%3D
        # 6w5IdI7yP4qmiqGoOgGXCxwz2UR4k3oU8OI0KIEk+9Y=
        # 18668075

        # https://algoexplorer.io/tx/group/sQCLZq10n6Yccwpj3kAB6jCyxrNMkJGpUHacltKGJV8%3D
        # sQCLZq10n6Yccwpj3kAB6jCyxrNMkJGpUHacltKGJV8=

        seller = None
        buyer = None

        spent_amount_per_address = defaultdict(int)

        for txn in atomic_transfer.all_transactions:
            if txn.transaction_type == TransactionType.payment:
                spent_amount_per_address[txn.sender] -= txn.payment_transaction.amount
                if txn.payment_transaction.close_amount is not None:
                    spent_amount_per_address[txn.sender] -= txn.payment_transaction.close_amount

                spent_amount_per_address[txn.payment_transaction.receiver] += txn.payment_transaction.amount

                if txn.payment_transaction.close_reminder_to is not None:
                    spent_amount_per_address[
                        txn.payment_transaction.close_reminder_to] += txn.payment_transaction.close_amount

        if len(spent_amount_per_address) != 2:
            raise NotImplementedError("Invalid number of involved addresses")

        received_asas_per_address = defaultdict(int)

        for txn in atomic_transfer.all_transactions:
            if txn.transaction_type == TransactionType.asset_transfer:
                received_asas_per_address[txn.sender] -= txn.asset_transfer_transaction.amount

                if txn.asset_transfer_transaction.close_to is not None:
                    received_asas_per_address[txn.sender] -= txn.asset_transfer_transaction.close_amount
                    received_asas_per_address[txn.asset_transfer_transaction.close_to] += \
                        txn.asset_transfer_transaction.close_amount

                received_asas_per_address[
                    txn.asset_transfer_transaction.receiver] += txn.asset_transfer_transaction.amount

        if len(received_asas_per_address) != 2:
            raise NotImplementedError("Invalid number of involved addresses")

        for address, spent_amount in spent_amount_per_address.items():
            if spent_amount > 0:
                seller = address
            else:
                buyer = address

        if not (spent_amount_per_address[buyer] < 0 < spent_amount_per_address[seller] and
                received_asas_per_address[buyer] == 1 and
                received_asas_per_address[seller] == -1):
            raise NotImplementedError("Invalid logic")

        if atomic_transfer.highest_payment_amount < 1000000:
            # TODO: Hard-code fix. Everything below 1 is treated as listing/delisting.
            raise NotImplementedError("Invalid min amount")

        return AtomicSwapSale(seller=seller,
                              buyer=buyer,
                              price=spent_amount_per_address[seller],
                              platform_fee=0,
                              creator_fee=0,
                              seller_price=spent_amount_per_address[seller],
                              time=atomic_transfer.block_time,
                              asa_id=atomic_transfer.asa_id,
                              sale_type=SaleType.buy_now,
                              group_id=atomic_transfer.group_id,
                              block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError("Invalid number of transferred ASAs")

        is_exception = False

        try:
            is_exception = AtomicSwapSale.algoanna_lending_exception_2_transactions(atomic_transfer=atomic_transfer)
        except:
            pass

        if is_exception:
            raise NotImplementedError

        try:
            is_exception = AtomicSwapSale.algoanna_lending_exception_3_transactions(atomic_transfer=atomic_transfer)
        except:
            pass

        if is_exception:
            raise NotImplementedError

        try:
            p2p_sale = AtomicSwapSale.init_p2p_sale(atomic_transfer=atomic_transfer)
            return p2p_sale
        except:
            pass

        raise NotImplementedError
