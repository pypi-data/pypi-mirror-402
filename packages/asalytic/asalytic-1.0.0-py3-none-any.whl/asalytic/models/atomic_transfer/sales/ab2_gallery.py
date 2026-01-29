from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.ASASale import ASASale, SaleType

__all__ = ["AB2GallerySale"]


class AB2GallerySale(ASASale):
    sale_platform = "AB2 Gallery"

    @staticmethod
    def init_from_3_transactions_1(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/1S0mVvXGorO1fOe26PjPuRFSE7tFA1n%2FHbQUPk6LNCY%3D
        # 1S0mVvXGorO1fOe26PjPuRFSE7tFA1n/HbQUPk6LNCY=
        # block_number: 16133583

        transaction_order = [
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order.")

        price = atomic_transfer.transactions[1].payment_transaction.amount

        if atomic_transfer.transactions[0].note != 'YWIyLmdhbGxlcnk=':
            raise NotImplementedError("Invalid transaction note.")

        return AB2GallerySale(seller=atomic_transfer.transactions[1].payment_transaction.receiver,
                              buyer=atomic_transfer.transactions[2].asset_transfer_transaction.receiver,
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
    def init_from_4_transactions_1(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/w8NqGJ5y2XeCwvr98WpBmw2v7REoQ74qzH9gg8Jd9OM%3D
        # w8NqGJ5y2XeCwvr98WpBmw2v7REoQ74qzH9gg8Jd9OM=
        # block: 16369571

        transaction_order = [
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction order")

        if atomic_transfer.transactions[0].note != 'YWIyLmdhbGxlcnk=':
            raise NotImplementedError("Invalid transaction note.")

        price = atomic_transfer.transactions[1].payment_transaction.amount

        return AB2GallerySale(seller=atomic_transfer.transactions[3].payment_transaction.close_reminder_to,
                              buyer=atomic_transfer.transactions[1].sender,
                              price=price,
                              platform_fee=0,
                              creator_fee=int(price * 0.1),
                              seller_price=int(price * 0.9),
                              time=atomic_transfer.block_time,
                              asa_id=atomic_transfer.asa_id,
                              sale_type=SaleType.buy_now,
                              group_id=atomic_transfer.group_id,
                              block_number=atomic_transfer.block)

    @staticmethod
    def init_from_4_transactions_2(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/LIv%2F0qQ8CuSfGimEQC9tb5k3EFEnrPNImVJF%2BPaGn3w%3D
        # LIv/0qQ8CuSfGimEQC9tb5k3EFEnrPNImVJF+PaGn3w=
        # round: 16369554

        transaction_order = [
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.asset_transfer,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction type")

        if atomic_transfer.transactions[0].note != 'YWIyLmdhbGxlcnk=':
            raise NotImplementedError("Invalid transaction note")

        price = atomic_transfer.transactions[2].payment_transaction.amount

        # TODO: Need to properly determine the seller. The creator of the escrow is the actual seller.
        return AB2GallerySale(seller=atomic_transfer.transactions[2].payment_transaction.receiver,
                              buyer=atomic_transfer.transactions[2].sender,
                              price=price,
                              platform_fee=0,
                              creator_fee=int(price * 0.1),
                              seller_price=int(price * 0.9),
                              time=atomic_transfer.block_time,
                              asa_id=atomic_transfer.asa_id,
                              sale_type=SaleType.buy_now,
                              group_id=atomic_transfer.group_id,
                              block_number=atomic_transfer.block)

    @staticmethod
    def init_from_5_transactions_1(atomic_transfer: AtomicTransfer):
        # https://algoexplorer.io/tx/group/zdcC0NHrgZ7s9ET6iw0tGR3QYldWsFkziE76rSzSAFw%3D
        # zdcC0NHrgZ7s9ET6iw0tGR3QYldWsFkziE76rSzSAFw=
        # round: 16133565

        transaction_order = [
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        if atomic_transfer.transactions[0].note != 'YWIyLmdhbGxlcnk=':
            raise NotImplementedError("Invalid transaction note")

        price = atomic_transfer.transactions[2].payment_transaction.amount

        return AB2GallerySale(seller=atomic_transfer.transactions[4].payment_transaction.close_reminder_to,
                              buyer=atomic_transfer.transactions[2].sender,
                              price=price,
                              platform_fee=0,
                              creator_fee=int(price * 0.1),
                              seller_price=int(price * 0.9),
                              time=atomic_transfer.block_time,
                              asa_id=atomic_transfer.asa_id,
                              sale_type=SaleType.buy_now,
                              group_id=atomic_transfer.group_id,
                              block_number=atomic_transfer.block)

    # @staticmethod
    # def init_from_5_transactions_2(atomic_transfer: AtomicTransfer, collection_name):
    #     if atomic_transfer.has_unknown_transactions:
    #         raise NotImplementedError
    #
    #     if len(atomic_transfer.asa_ids) > 1:
    #         raise NotImplementedError
    #
    #     if len(atomic_transfer.payment_transactions) != 2 or \
    #             len(atomic_transfer.asa_transfer_transactions) != 2 or \
    #             len(atomic_transfer.app_call_transactions) != 1:
    #         raise NotImplementedError
    #
    #     if len(atomic_transfer.settled_payments) != 4:
    #         raise NotImplementedError
    #
    #     return AB2GalleryBuy(buyer=atomic_transfer.settled_payments[0][1],
    #                          seller=atomic_transfer.settled_payments[3][1],
    #                          price=atomic_transfer.settled_payments[0][0] * (-1),
    #                          seller_amount=atomic_transfer.settled_payments[3][0],
    #                          creator_fee=atomic_transfer.settled_payments[2][0],
    #                          asa_id=atomic_transfer.asa_id,
    #                          time=atomic_transfer.round_time)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
        if atomic_transfer.number_of_unique_asa_transferred != 1:
            raise NotImplementedError(
                f"{atomic_transfer.number_of_unique_asa_transferred} involved in the atomic transfer")

        try:
            if len(atomic_transfer.transactions) == 3:
                return AB2GallerySale.init_from_3_transactions_1(atomic_transfer)
        except NotImplementedError:
            pass

        try:
            if len(atomic_transfer.transactions) == 4:
                return AB2GallerySale.init_from_4_transactions_1(atomic_transfer)
        except NotImplementedError:
            pass

        try:
            if len(atomic_transfer.transactions) == 4:
                return AB2GallerySale.init_from_4_transactions_2(atomic_transfer)
        except NotImplementedError:
            pass

        try:
            if len(atomic_transfer.transactions) == 5:
                return AB2GallerySale.init_from_5_transactions_1(atomic_transfer)
        except NotImplementedError:
            pass

        # try:
        #     if len(atomic_transfer.transactions) == 5:
        #         return AB2GalleryBuy.init_from_5_transactions_2(atomic_transfer, collection_name)
        # except NotImplementedError:
        #     pass

        raise NotImplementedError

# class AB2GallerySellOffer(BaseModel):
#     seller: str
#     price: int
#     asa_id: int
#     app_id: int
#     time: int
#
#     @staticmethod
#     def init_from_atomic_transfer(atomic_transfer: AtomicTransfer, indexer: IndexerClient):
#         if atomic_transfer.has_unknown_transactions:
#             raise NotImplementedError
#
#         if len(atomic_transfer.asa_ids) > 1:
#             raise NotImplementedError
#
#         if len(atomic_transfer.payment_transactions) != 1 or \
#                 len(atomic_transfer.asa_transfer_transactions) != 2 or \
#                 len(atomic_transfer.app_call_transactions) != 1:
#             raise NotImplementedError
#
#         seller = None
#         for address, amount in atomic_transfer.settled_asa_transfers:
#             if amount == -1:
#                 seller = address
#
#         price = -1
#
#         # price = AB2GalleryIndexer.retrieve_sell_offer_price(indexer=indexer,
#         #                                                     app_id=atomic_transfer.app_id)
#
#         return AB2GallerySellOffer(seller=seller,
#                                    price=price,
#                                    asa_id=atomic_transfer.asa_id,
#                                    app_id=atomic_transfer.app_id,
#                                    time=atomic_transfer.round_time)
#
#
# class AB2GalleryCancelSellOffer(BaseModel):
#     seller: str
#     asa_id: int
#     app_id: int
#     time: int
#
#     @staticmethod
#     def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):
#         if atomic_transfer.has_unknown_transactions:
#             raise NotImplementedError
#
#         if len(atomic_transfer.asa_ids) > 1:
#             raise NotImplementedError
#
#         if len(atomic_transfer.payment_transactions) != 1 or \
#                 len(atomic_transfer.asa_transfer_transactions) != 1 or \
#                 len(atomic_transfer.app_call_transactions) != 1:
#             raise NotImplementedError
#
#         seller = None
#         for address, amount in atomic_transfer.settled_asa_transfers:
#             if amount == 1:
#                 seller = address
#
#         if seller is None:
#             raise NotImplementedError
#
#         return AB2GalleryCancelSellOffer(seller=seller,
#                                          asa_id=atomic_transfer.asa_id,
#                                          app_id=atomic_transfer.app_id,
#                                          time=atomic_transfer.round_time)
