from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["FracctalLabsSale"]

SHUFFLE_BANK_ADDRESS = 'V6CK3HRC4JBRBDIBB4JWOBMYNUYIP7SYHRPVHH5ZMJQME337C57IBIZVFI'
SECONDARY_BANK_ADDRESS = 'HTTUDMPCLNFSB3HGESJHQUHFGXRFFEWQNRORAPPNRMMYPOQGKKKVXSA224'


class FracctalLabsSale(ASASale):
    sale_platform = "Fracctal Labs"

    @staticmethod
    def init_from_14_transactions_shuffle(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/yBtgi550H9YJ9p84aS6TsQM0Zvca0e0VFYDGg6YN96k%3D
        yBtgi550H9YJ9p84aS6TsQM0Zvca0e0VFYDGg6YN96k=
        block: 26612921
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
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid Inner Transaction Order")

        seller = atomic_transfer.transactions[1].inner_txns[0].payment_transaction.receiver
        buyer = atomic_transfer.transactions[1].inner_txns[1].asset_transfer_transaction.receiver
        asa_id = atomic_transfer.transactions[1].inner_txns[1].asset_transfer_transaction.asset_id

        if seller != SHUFFLE_BANK_ADDRESS:
            raise NotImplementedError("Invalid Bank Address")

        return FracctalLabsSale(seller=seller,
                                buyer=buyer,
                                price=atomic_transfer.transactions[0].payment_transaction.amount,
                                platform_fee=0,
                                creator_fee=0,
                                seller_price=atomic_transfer.transactions[0].payment_transaction.amount,
                                time=atomic_transfer.block_time,
                                asa_id=asa_id,
                                sale_type=SaleType.shuffle,
                                group_id=atomic_transfer.group_id,
                                block_number=atomic_transfer.block)

    @staticmethod
    def init_from_10_transactions_1(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/PXPoDPEd1rsMKObhFEQs60mAW01ik%2FOOvConiZFGM4g%3D
        PXPoDPEd1rsMKObhFEQs60mAW01ik/OOvConiZFGM4g=
        block: 26634432
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
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid Inner Transaction Order")

        seller = atomic_transfer.transactions[1].inner_txns[6].payment_transaction.receiver
        buyer = atomic_transfer.transactions[1].inner_txns[0].asset_transfer_transaction.receiver
        asa_id = atomic_transfer.transactions[1].inner_txns[0].asset_transfer_transaction.asset_id

        if atomic_transfer.transactions[1].inner_txns[0].asset_transfer_transaction.amount != 1:
            raise NotImplementedError("Invalid Asset")

        if SECONDARY_BANK_ADDRESS != atomic_transfer.transactions[1].inner_txns[5].payment_transaction.receiver:
            raise NotImplementedError("Invalid Bank Address")

        return FracctalLabsSale(seller=seller,
                                buyer=buyer,
                                price=atomic_transfer.transactions[0].payment_transaction.amount,
                                platform_fee=atomic_transfer.transactions[1].inner_txns[5].payment_transaction.amount,
                                creator_fee=0,
                                seller_price=atomic_transfer.transactions[1].inner_txns[6].payment_transaction.amount,
                                time=atomic_transfer.block_time,
                                asa_id=asa_id,
                                sale_type=SaleType.buy_now,
                                group_id=atomic_transfer.group_id,
                                block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):

        try:
            buy = FracctalLabsSale.init_from_14_transactions_shuffle(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = FracctalLabsSale.init_from_10_transactions_1(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
