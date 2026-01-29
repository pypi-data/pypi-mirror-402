from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.atomic_transfer.listings.application.ATAppListing import ATAppListing


class EXAListing(ATAppListing):
    platform = "EXA Market"

    @staticmethod
    def init_from_5_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/ecuVA90vLj7sCEhIDjzlFxMvxt1X62ElxaCFhAD99UE%3D
        :param atomic_transfer:
        :return:
        """

        transaction_order = [
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        inner_transactions_order = [
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        return EXAListing(time=atomic_transfer.block_time,
                          block=atomic_transfer.block,
                          app_id=atomic_transfer.transactions[1].application_transaction.application_id)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):

        try:
            listing = EXAListing.init_from_5_transactions(atomic_transfer)
            return listing
        except NotImplementedError:
            pass

        raise NotImplementedError
