from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType
import json
import base64

__all__ = ["ALGOxNFTSale", "ALGOxNFT_BANK_ADDRESS"]

ALGOxNFT_BANK_ADDRESS = 'XNFT36FUCFRR6CK675FW4BEBCCCOJ4HOSMGCN6J2W6ZMB34KM2ENTNQCP4'


class ALGOxNFTSale(ASASale):
    sale_platform = "ALGOxNFT"

    @staticmethod
    def init_from_4_transactions_offer(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/66lQITI5pMu27RC9Dpob8kgYVcs8HqLXQYThhbLmW58%3D
        66lQITI5pMu27RC9Dpob8kgYVcs8HqLXQYThhbLmW58=
        block: 19390295
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        if atomic_transfer.payment_transactions[2].payment_transaction.receiver != ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        price = 0
        for txn in atomic_transfer.payment_transactions:
            price += txn.payment_transaction.amount

        return ALGOxNFTSale(seller=atomic_transfer.transactions[2].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[0].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[3].payment_transaction.amount,
                            creator_fee=atomic_transfer.transactions[1].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[2].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.offer,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/93d1Z%2BxRwW10HAGiQmMvqAM9gAM1pLUqvbqBZJR1wxk%3D
        93d1Z+xRwW10HAGiQmMvqAM9gAM1pLUqvbqBZJR1wxk=
        block: 16980315
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction type")

        if atomic_transfer.payment_transactions[0].payment_transaction.close_reminder_to != ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        price = atomic_transfer.payment_transactions[0].payment_transaction.amount + \
                atomic_transfer.payment_transactions[0].payment_transaction.close_amount

        return ALGOxNFTSale(seller=atomic_transfer.transactions[3].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[0].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[3].payment_transaction.close_amount,
                            creator_fee=0,
                            seller_price=atomic_transfer.transactions[3].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.auction,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_5_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/WBSDfYA2%2B1hAadW9iH5XvZ7PCtcyvQ2U3MTSB0aX4Qc%3D
        WBSDfYA2+1hAadW9iH5XvZ7PCtcyvQ2U3MTSB0aX4Qc=
        18666800
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering.")

        if atomic_transfer.payment_transactions[1].payment_transaction.close_reminder_to != ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address.")

        price = atomic_transfer.payment_transactions[0].payment_transaction.amount + \
                atomic_transfer.payment_transactions[1].payment_transaction.amount + \
                atomic_transfer.payment_transactions[1].payment_transaction.close_amount

        return ALGOxNFTSale(seller=atomic_transfer.transactions[4].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[0].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[4].payment_transaction.close_amount,
                            creator_fee=atomic_transfer.transactions[3].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[4].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.auction,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_5_transactions_shuffle(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/grwo2C4I41Dm6NKliUw5xI39WXscFAI12ITl7w12w%2Bo%3D
        grwo2C4I41Dm6NKliUw5xI39WXscFAI12ITl7w12w+o=
        block:19921991
        """
        transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        price = 0
        for t in atomic_transfer.payment_transactions:
            price += t.payment_transaction.amount

        # Bank Address for ALGOxNFT.
        if atomic_transfer.payment_transactions[1].payment_transaction.receiver != ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address.")

        return ALGOxNFTSale(seller=atomic_transfer.transactions[0].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[4].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[1].payment_transaction.amount,
                            creator_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[0].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.shuffle,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_5_transactions_direct_buy(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/r3DH0%2FWeg7r5s%2FEh9fvPTHadxwO1aMpfFEcLOjSetd0%3D
        r3DH0/Weg7r5s/Eh9fvPTHadxwO1aMpfFEcLOjSetd0=
        block:20236953
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering.")

        price = 0
        for t in atomic_transfer.payment_transactions:
            price += t.payment_transaction.amount

        # Bank Address for ALGOxNFT.
        if atomic_transfer.payment_transactions[2].payment_transaction.receiver != ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError

        return ALGOxNFTSale(seller=atomic_transfer.transactions[2].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[0].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[3].payment_transaction.amount,
                            creator_fee=atomic_transfer.transactions[1].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[2].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_6_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/G8XS0TRWMPcrQWOh3SAHUmOjNhdjr8JKqqhwrsMPv5s%3D
        G8XS0TRWMPcrQWOh3SAHUmOjNhdjr8JKqqhwrsMPv5s=
        block: 18853712
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        price = 0
        for t in atomic_transfer.payment_transactions:
            price += t.payment_transaction.amount

        # Bank Address for ALGOxNFT.
        if atomic_transfer.payment_transactions[2].payment_transaction.receiver != ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address.")

        txn_note = atomic_transfer.payment_transactions[2].note

        is_asalytic_note = False

        try:
            if txn_note is not None:
                platform_note = json.loads(base64.b64decode(txn_note).decode('utf-8'))
                platform_name = platform_note.get('platform', None)
                if platform_name is not None:
                    if platform_name == "Asalytic":
                        is_asalytic_note = True
        except:
            pass

        if is_asalytic_note:
            raise NotImplementedError("Invalid transaction note i.e platform")

        return ALGOxNFTSale(seller=atomic_transfer.transactions[3].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[1].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[4].payment_transaction.amount,
                            creator_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[3].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_6_transactions_shuffle(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/j2ARZu3UwBEpp31ikwxS5ii%2BJP2MGT%2FI8vcD3YQCjzk%3D
        j2ARZu3UwBEpp31ikwxS5ii+JP2MGT/I8vcD3YQCjzk=
        block: 27222599
        """
        transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        price = 0
        for t in atomic_transfer.payment_transactions:
            price += t.payment_transaction.amount

        # Bank Address for ALGOxNFT.
        if atomic_transfer.payment_transactions[1].payment_transaction.receiver != ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address.")

        return ALGOxNFTSale(seller=atomic_transfer.transactions[0].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[3].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[1].payment_transaction.amount,
                            creator_fee=0,
                            seller_price=atomic_transfer.transactions[0].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.shuffle,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_6_transactions_collection_offer(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/KXV%2BIS0i1ICUW1NvLpv7G3xPrz%2FEjT5lj%2FpXFhb1%2F2c%3D
        KXV+IS0i1ICUW1NvLpv7G3xPrz/EjT5lj/pXFhb1/2c=
        block: 24356929
        """
        transaction_order = [
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        price = 0
        for t in atomic_transfer.payment_transactions:
            price += t.payment_transaction.amount

        # Bank Address for ALGOxNFT.
        if atomic_transfer.payment_transactions[2].payment_transaction.receiver != ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address.")

        return ALGOxNFTSale(seller=atomic_transfer.transactions[5].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[2].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[4].payment_transaction.amount,
                            creator_fee=atomic_transfer.transactions[3].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[5].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_7_transactions_atomic_swap(atomic_transfer: AtomicTransfer):
        """
        gVQoXLBVtH7bhRRUYk/0+MgH8NovWAI+Q7ADKSmv/e8=
        block: 21556709
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction types.")

        price = 0
        for i in range(3):
            price += atomic_transfer.payment_transactions[i].payment_transaction.amount

        # Bank Address for ALGOxNFT.
        if atomic_transfer.payment_transactions[2].payment_transaction.receiver != ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address")

        return ALGOxNFTSale(seller=atomic_transfer.transactions[3].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[1].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[4].payment_transaction.amount,
                            creator_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[3].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError("Invalid number of transferred ASAs")

        if atomic_transfer.highest_payment_amount is not None and atomic_transfer.highest_payment_amount < 1000000:
            raise NotImplementedError("Highest sale below 1A")

        try:
            buy = ALGOxNFTSale.init_from_4_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ALGOxNFTSale.init_from_4_transactions_offer(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ALGOxNFTSale.init_from_5_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ALGOxNFTSale.init_from_5_transactions_shuffle(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ALGOxNFTSale.init_from_5_transactions_direct_buy(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ALGOxNFTSale.init_from_6_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ALGOxNFTSale.init_from_6_transactions_collection_offer(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ALGOxNFTSale.init_from_6_transactions_shuffle(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = ALGOxNFTSale.init_from_7_transactions_atomic_swap(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
