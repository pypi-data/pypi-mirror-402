from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.atomic_transfer.listings.application.ATAppListing import ATAppListing
from asalytic.models.atomic_transfer.sales.constants import ASALYTIC_VALID_FACTORY_APP_IDS


class AsalyticListing(ATAppListing):
    platform = "Asalytic"

    @staticmethod
    def init_from_12_transactions(atomic_transfer: AtomicTransfer):
        """
         'wP+pbtoy5IovISi8BspvCYA29HQ18wWg6qS0MqAJe/A='
         39159483
        :param atomic_transfer:
        :return:
        """

        inner_transactions_order = [
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.application_call,
            TransactionType.application_call,
            TransactionType.payment,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.application_call,
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        all_txns = atomic_transfer.all_transactions

        if all_txns[1].application_transaction.application_id not in ASALYTIC_VALID_FACTORY_APP_IDS:
            raise NotImplementedError("Invalid Factory App ID")

        return AsalyticListing(time=atomic_transfer.block_time,
                               block=atomic_transfer.block,
                               app_id=all_txns[6].created_application_index)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):

        try:
            listing = AsalyticListing.init_from_12_transactions(atomic_transfer)
            return listing
        except NotImplementedError:
            pass

        raise NotImplementedError
