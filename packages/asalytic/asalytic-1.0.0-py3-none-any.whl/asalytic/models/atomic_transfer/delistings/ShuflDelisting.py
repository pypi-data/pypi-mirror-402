from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.atomic_transfer.delistings.AtomicTransferDelisting import AtomicTransferDelisting


class ShuflDelisting(AtomicTransferDelisting):
    platform = "Shufl"

    @staticmethod
    def init_from_2_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/FxO8u%2Bd2LxNejzO8myU0F%2BpPAMZaVQE%2F4KslZXzeq8o%3D
        :param atomic_transfer:
        :return:
        """

        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.application_call,
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        inner_transactions_order = [
            TransactionType.asset_transfer,
            TransactionType.application_call,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=inner_transactions_order):
            raise NotImplementedError("Invalid inner transaction ordering")

        return ShuflDelisting(time=atomic_transfer.block_time,
                              block=atomic_transfer.block,
                              app_id=atomic_transfer.transactions[1].application_transaction.application_id)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):

        try:
            delisting = ShuflDelisting.init_from_2_transactions(atomic_transfer)
            return delisting
        except NotImplementedError:
            pass

        raise NotImplementedError
