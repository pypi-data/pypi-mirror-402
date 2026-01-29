from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType
from asalytic.models.atomic_transfer.sales.algoxnft import ALGOxNFT_BANK_ADDRESS

__all__ = ["AlgoGemsSale"]

ALGO_GEMS_BANK_ACCOUNT = 'VWZBFLBUN6O5A5W6IWHMDUVP5NH2LPV4ZYFMAHP4FQBBYP627MP6WPOEG4'


class AlgoGemsSale(ASASale):
    sale_platform = "AlgoGems"

    @staticmethod
    def init_from_3_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/DYFMd8TijSy9NdKvBWw21UmMqdnOuJGvq46q4C5h4Ps%3D
        DYFMd8TijSy9NdKvBWw21UmMqdnOuJGvq46q4C5h4Ps=
        block: 18977298
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering.")

        price = 0
        for p_txn in atomic_transfer.payment_transactions:
            price += p_txn.payment_transaction.amount

        return AlgoGemsSale(seller=atomic_transfer.transactions[1].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[0].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=0,
                            creator_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[1].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/DYFMd8TijSy9NdKvBWw21UmMqdnOuJGvq46q4C5h4Ps%3D
        OHGHJX3SqBd9MZL2vm/1A0/MERMDH8xFXQiifT+kNL0=
        block: 19110194

        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        if atomic_transfer.payment_transactions[2].payment_transaction.receiver == ALGOxNFT_BANK_ADDRESS:
            raise NotImplementedError("Invalid bank address.")

        price = 0
        for p_txn in atomic_transfer.payment_transactions:
            price += p_txn.payment_transaction.amount

        return AlgoGemsSale(seller=atomic_transfer.transactions[1].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[0].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                            creator_fee=atomic_transfer.transactions[3].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[1].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_5_transactions_1(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/v7kPzIXoi%2BcOKt0LPwM0HEm1YAce%2F0O
        v7kPzIXoi+cOKt0LPwM0HEm1YAce/0OqaNaTcb2uwqs=
        block: 19259164
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order.")

        price = 0
        for p_txn in atomic_transfer.payment_transactions:
            price += p_txn.payment_transaction.amount

        if atomic_transfer.payment_transactions[1].payment_transaction.receiver != ALGO_GEMS_BANK_ACCOUNT:
            raise NotImplementedError("Invalid bank address")

        return AlgoGemsSale(seller=atomic_transfer.transactions[1].sender,
                            buyer=atomic_transfer.transactions[1].asset_transfer_transaction.receiver,
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
    def init_from_5_transactions_2(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/csZiX38H8AxiOAvgQ0AtOhBHMsCa3nUmLCKWBp4lyqM%3D
        csZiX38H8AxiOAvgQ0AtOhBHMsCa3nUmLCKWBp4lyqM=
        blocK: 17869766
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        price = 0
        for p_txn in atomic_transfer.payment_transactions:
            price += p_txn.payment_transaction.amount

        # Bank Address for ALGOxNFT.
        if atomic_transfer.payment_transactions[2].payment_transaction.receiver == \
                'XNFT36FUCFRR6CK675FW4BEBCCCOJ4HOSMGCN6J2W6ZMB34KM2ENTNQCP4':
            raise NotImplementedError("Invalid bank address.")

        if atomic_transfer.payment_transactions[1].payment_transaction.receiver != ALGO_GEMS_BANK_ACCOUNT:
            raise NotImplementedError("Invalid bank address")

        return AlgoGemsSale(seller=atomic_transfer.transactions[1].payment_transaction.receiver,
                            buyer=atomic_transfer.transactions[0].asset_transfer_transaction.receiver,
                            price=price,
                            platform_fee=atomic_transfer.transactions[2].payment_transaction.amount,
                            creator_fee=atomic_transfer.transactions[3].payment_transaction.amount,
                            seller_price=atomic_transfer.transactions[1].payment_transaction.amount,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_6_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/VbHPvfVuer9CQOLjeSgfuel1WAehZd3N2%2FjbLMkuj6A%3D
        VbHPvfVuer9CQOLjeSgfuel1WAehZd3N2/jbLMkuj6A=
        block_id: 26400339
        """

        transactions_order = [TransactionType.payment,
                              TransactionType.application_call]

        if not atomic_transfer.valid_transaction_types(transaction_types=transactions_order):
            raise NotImplementedError("Invalid transaction ordering.")

        inner_txns_order = [
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_txns_order):
            raise NotImplementedError("Invalid inner txns ordering.")

        seller = atomic_transfer.transactions[1].inner_txns[2].payment_transaction.receiver
        buyer = atomic_transfer.transactions[0].sender

        platform_fee = atomic_transfer.transactions[1].inner_txns[0].payment_transaction.amount
        creator_fee = atomic_transfer.transactions[1].inner_txns[1].payment_transaction.amount
        seller_fee = atomic_transfer.transactions[1].inner_txns[2].payment_transaction.amount

        if atomic_transfer.payment_transactions[1].payment_transaction.receiver != ALGO_GEMS_BANK_ACCOUNT:
            raise NotImplementedError("Invalid bank address")

        return AlgoGemsSale(seller=seller,
                            buyer=buyer,
                            price=atomic_transfer.transactions[0].payment_transaction.amount,
                            platform_fee=platform_fee,
                            creator_fee=creator_fee,
                            seller_price=seller_fee,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_7_transactions(atomic_transfer: AtomicTransfer):
        """
        # https://algoexplorer.io/tx/group/4kOzv%2BnxmdItst5x3ov1qauyRCtOf5bSu0DSbQmgxr8%3D
        4kOzv+nxmdItst5x3ov1qauyRCtOf5bSu0DSbQmgxr8=
        block_id: 20929013
        """

        transactions_order = [TransactionType.asset_transfer,
                              TransactionType.payment,
                              TransactionType.application_call]

        if not atomic_transfer.valid_transaction_types(transaction_types=transactions_order):
            raise NotImplementedError("Invalid transaction ordering.")

        inner_txns_order = [
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_txns_order):
            raise NotImplementedError("Invalid inner txns ordering.")

        seller = atomic_transfer.transactions[2].inner_txns[2].payment_transaction.receiver
        buyer = atomic_transfer.transactions[1].sender

        platform_fee = atomic_transfer.transactions[2].inner_txns[0].payment_transaction.amount
        creator_fee = atomic_transfer.transactions[2].inner_txns[1].payment_transaction.amount
        seller_fee = atomic_transfer.transactions[2].inner_txns[2].payment_transaction.amount

        return AlgoGemsSale(seller=seller,
                            buyer=buyer,
                            price=atomic_transfer.transactions[1].payment_transaction.amount,
                            platform_fee=platform_fee,
                            creator_fee=creator_fee,
                            seller_price=seller_fee,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.buy_now,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_8_transactions(atomic_transfer: AtomicTransfer):
        """
        # group_id: 7TX7uQxOO42qqRQpGj0AACSxHh4zuRxVRAgWXQhJNpM=
        """

        inner_txns_order = [
            TransactionType.asset_transfer,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_txns_order):
            raise NotImplementedError("Invalid inner txns ordering.")

        buyer = atomic_transfer.all_transactions[5].asset_transfer_transaction.receiver
        seller = atomic_transfer.all_transactions[4].payment_transaction.receiver

        platform_fee = atomic_transfer.all_transactions[2].payment_transaction.amount
        creator_fee = atomic_transfer.all_transactions[3].payment_transaction.amount
        seller_fee = atomic_transfer.all_transactions[4].payment_transaction.amount

        price = platform_fee + creator_fee + seller_fee

        return AlgoGemsSale(seller=seller,
                            buyer=buyer,
                            price=price,
                            platform_fee=platform_fee,
                            creator_fee=creator_fee,
                            seller_price=seller_fee,
                            time=atomic_transfer.block_time,
                            asa_id=atomic_transfer.asa_id,
                            sale_type=SaleType.offer,
                            group_id=atomic_transfer.group_id,
                            block_number=atomic_transfer.block)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):

        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError("Invalid number of transferred ASAs.")

        try:
            buy = AlgoGemsSale.init_from_3_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = AlgoGemsSale.init_from_4_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = AlgoGemsSale.init_from_5_transactions_1(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = AlgoGemsSale.init_from_5_transactions_2(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = AlgoGemsSale.init_from_6_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = AlgoGemsSale.init_from_7_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        try:
            buy = AlgoGemsSale.init_from_8_transactions(atomic_transfer)
            return buy
        except NotImplementedError:
            pass

        raise NotImplementedError
