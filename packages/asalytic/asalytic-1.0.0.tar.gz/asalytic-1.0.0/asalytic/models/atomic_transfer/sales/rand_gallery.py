from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["RandGallerySale"]

PROMOTION_BANK_ADDRESS = 'ATWDHYB5TLHKSEMNJ73CPLMUBRFUNTITTPWQGO6WYXJK47TXHV7FSADF3E'


class RandGallerySale(ASASale):
    sale_platform = "Rand Gallery"

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/gFKGY7u9wexEJOkEIQSHmiZIWDTaTS4aa6NSnyJ8giU%3D
        # group_id: gFKGY7u9wexEJOkEIQSHmiZIWDTaTS4aa6NSnyJ8giU=
        # block: 16328751

        transaction_order = [
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        price = atomic_transfer.transactions[0].payment_transaction.amount \
                + atomic_transfer.transactions[2].payment_transaction.amount

        if 'RAND' != atomic_transfer.transactions[0].payment_transaction.receiver[:4]:
            raise NotImplementedError

        return RandGallerySale(seller=atomic_transfer.transactions[2].payment_transaction.receiver,
                               buyer=atomic_transfer.transactions[3].asset_transfer_transaction.receiver,
                               price=price,
                               platform_fee=atomic_transfer.transactions[0].payment_transaction.amount,
                               creator_fee=0,
                               seller_price=atomic_transfer.transactions[2].payment_transaction.amount,
                               time=atomic_transfer.block_time,
                               asa_id=atomic_transfer.asa_id,
                               sale_type=SaleType.buy_now,
                               group_id=atomic_transfer.group_id,
                               block_number=atomic_transfer.block)

    @staticmethod
    def init_from_5_transactions_offer(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/Pg1O0s%2ByiHmtxUX1sjpU%2BZKM1cndE8H%2BDmXylXyROhI%3D
        # Pg1O0s+yiHmtxUX1sjpU+ZKM1cndE8H+DmXylXyROhI=
        # block: 20669893

        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        price = 0
        for txn in atomic_transfer.payment_transactions:
            price += txn.payment_transaction.amount

        if atomic_transfer.transactions[3].payment_transaction.receiver[:4] != 'RAND':
            raise NotImplementedError("Invalid marketplace address")

        return RandGallerySale(seller=atomic_transfer.transactions[2].payment_transaction.receiver,
                               buyer=atomic_transfer.transactions[4].asset_transfer_transaction.receiver,
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
    def init_from_5_transactions(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/gvh0GH6xNXOzcJhbYC%2FiN%2BGD12BtS6SOQ8C5Mz%2B6QbU%3D
        # gvh0GH6xNXOzcJhbYC/iN+GD12BtS6SOQ8C5Mz+6QbU=
        # round: 15755210

        transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order.")

        price = 0
        for txn in atomic_transfer.payment_transactions:
            price += txn.payment_transaction.amount

        if atomic_transfer.transactions[1].payment_transaction.receiver[:4] != 'RAND':
            raise NotImplementedError("Invalid marketplace address.")

        return RandGallerySale(seller=atomic_transfer.transactions[0].payment_transaction.receiver,
                               buyer=atomic_transfer.payment_transactions[0].sender,
                               price=price,
                               platform_fee=atomic_transfer.transactions[1].payment_transaction.amount,
                               creator_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                               seller_price=atomic_transfer.transactions[0].payment_transaction.amount,
                               time=atomic_transfer.block_time,
                               asa_id=atomic_transfer.asa_id,
                               sale_type=SaleType.buy_now,
                               group_id=atomic_transfer.group_id,
                               block_number=atomic_transfer.block)

    @staticmethod
    def init_from_5_transactions_promotion(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/koOjLyVfjEYzirbSArsXsvTbTPH2pzCj%2F3qT%2FL5zRE0%3D

        transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order.")

        price = 0
        for txn in atomic_transfer.payment_transactions:
            price += txn.payment_transaction.amount

        if atomic_transfer.transactions[1].payment_transaction.receiver != PROMOTION_BANK_ADDRESS:
            raise NotImplementedError("Invalid marketplace address.")

        return RandGallerySale(seller=atomic_transfer.transactions[0].payment_transaction.receiver,
                               buyer=atomic_transfer.payment_transactions[0].sender,
                               price=price,
                               platform_fee=atomic_transfer.transactions[1].payment_transaction.amount,
                               creator_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                               seller_price=atomic_transfer.transactions[0].payment_transaction.amount,
                               time=atomic_transfer.block_time,
                               asa_id=atomic_transfer.asa_id,
                               sale_type=SaleType.buy_now,
                               group_id=atomic_transfer.group_id,
                               block_number=atomic_transfer.block)

    @staticmethod
    def init_from_6_transactions(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/%2F%2FfllsUGW%2Bqx1JpcP3AWRnmFq%2FRnhN4XDQRbkalqcn4%3D
        # //fllsUGW+qx1JpcP3AWRnmFq/RnhN4XDQRbkalqcn4=
        # round: 17704613

        transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError

        buyer = atomic_transfer.transactions[0].sender

        price = 0
        for txn in atomic_transfer.payment_transactions:
            if txn.sender == buyer:
                price += txn.payment_transaction.amount

        if atomic_transfer.transactions[2].payment_transaction.receiver[:4] != 'RAND':
            raise NotImplementedError("Invalid marketplace address.")

        return RandGallerySale(seller=atomic_transfer.transactions[0].payment_transaction.receiver,
                               buyer=buyer,
                               price=price,
                               platform_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                               creator_fee=atomic_transfer.transactions[1].payment_transaction.amount,
                               seller_price=atomic_transfer.transactions[0].payment_transaction.amount,
                               time=atomic_transfer.block_time,
                               asa_id=atomic_transfer.asa_id,
                               sale_type=SaleType.buy_now,
                               group_id=atomic_transfer.group_id,
                               block_number=atomic_transfer.block)

    @staticmethod
    def init_from_6_transactions_promotion(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/C0y05Hb1to10QNkIgJJZp1gzl5%2Fky%2Ff6Ha%2BJRamVZAo%3D

        transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError

        buyer = atomic_transfer.transactions[0].sender

        price = 0
        for txn in atomic_transfer.payment_transactions:
            if txn.sender == buyer:
                price += txn.payment_transaction.amount

        if atomic_transfer.transactions[2].payment_transaction.receiver != PROMOTION_BANK_ADDRESS:
            raise NotImplementedError("Invalid marketplace address.")

        return RandGallerySale(seller=atomic_transfer.transactions[0].payment_transaction.receiver,
                               buyer=buyer,
                               price=price,
                               platform_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                               creator_fee=atomic_transfer.transactions[1].payment_transaction.amount,
                               seller_price=atomic_transfer.transactions[0].payment_transaction.amount,
                               time=atomic_transfer.block_time,
                               asa_id=atomic_transfer.asa_id,
                               sale_type=SaleType.buy_now,
                               group_id=atomic_transfer.group_id,
                               block_number=atomic_transfer.block)

    @staticmethod
    def init_from_7_transactions(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/6Kg11pR7h%2FYzGpA%2BpFBSTUDMD8WwRZNsizJL3iR%2FVv4%3D
        # 6Kg11pR7h/YzGpA+pFBSTUDMD8WwRZNsizJL3iR/Vv4=
        # round: 17590811

        transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order.")

        price = 0
        for txn in atomic_transfer.payment_transactions:
            price += txn.payment_transaction.amount

        if atomic_transfer.transactions[3].payment_transaction.receiver[:4] != 'RAND':
            raise NotImplementedError("Invalid marketplace address.")

        return RandGallerySale(seller=atomic_transfer.transactions[2].payment_transaction.receiver,
                               buyer=atomic_transfer.transactions[0].sender,
                               price=price,
                               platform_fee=atomic_transfer.transactions[3].payment_transaction.amount,
                               creator_fee=atomic_transfer.transactions[4].payment_transaction.amount,
                               seller_price=atomic_transfer.transactions[2].payment_transaction.amount,
                               time=atomic_transfer.block_time,
                               asa_id=atomic_transfer.asa_id,
                               sale_type=SaleType.buy_now,
                               group_id=atomic_transfer.group_id,
                               block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError

        try:
            rand_buy = RandGallerySale.init_from_4_transactions(atomic_transfer)
            return rand_buy
        except NotImplementedError:
            pass

        try:
            rand_buy = RandGallerySale.init_from_5_transactions(atomic_transfer)
            return rand_buy
        except NotImplementedError:
            pass

        try:
            rand_buy = RandGallerySale.init_from_5_transactions_promotion(atomic_transfer)
            return rand_buy
        except NotImplementedError:
            pass

        try:
            rand_buy = RandGallerySale.init_from_5_transactions_offer(atomic_transfer)
            return rand_buy
        except NotImplementedError:
            pass

        try:
            rand_buy = RandGallerySale.init_from_6_transactions(atomic_transfer)
            return rand_buy
        except NotImplementedError:
            pass

        try:
            rand_buy = RandGallerySale.init_from_6_transactions_promotion(atomic_transfer)
            return rand_buy
        except NotImplementedError:
            pass

        try:
            rand_buy = RandGallerySale.init_from_7_transactions(atomic_transfer)
            return rand_buy
        except NotImplementedError:
            pass

        raise NotImplementedError
