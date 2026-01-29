from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.atomic_transfer.listings.application.ATAppListing import ATAppListing


class ShuflListing(ATAppListing):
    platform = "Shufl"

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/4SffZWFcOjrpLl2RFFLlU51aeTommZVZ5ix17rDgcOE%3D
        :param atomic_transfer:
        :return:
        """

        transaction_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        inner_transactions_order = [
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        return ShuflListing(time=atomic_transfer.block_time,
                            block=atomic_transfer.block,
                            app_id=atomic_transfer.transactions[2].application_transaction.application_id)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):

        try:
            listing = ShuflListing.init_from_4_transactions(atomic_transfer)
            return listing
        except NotImplementedError:
            pass

        raise NotImplementedError
