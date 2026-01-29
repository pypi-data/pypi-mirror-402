import traceback

from asalytic.models.algorand import AtomicTransfer, TransactionType

from asalytic.models.atomic_transfer.delistings.smart_signatures.SignatureDelisting import SignatureDelisting

from asalytic.models.atomic_transfer import AsalyticSale


class AsalyticDelisting(SignatureDelisting):

    @staticmethod
    def init_from_cancel(atomic_transfer: AtomicTransfer):
        """
        - Zszqrjdn/n3eCakMVx/fSb5XCiSxrgEmsqErFygd9Xg=
        - 38346628
        :param atomic_transfer:
        :return:
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        if atomic_transfer.transactions[0].asset_transfer_transaction.receiver != atomic_transfer.transactions[
            1].asset_transfer_transaction.receiver:
            raise NotImplementedError

        if atomic_transfer.transactions[0].asset_transfer_transaction.receiver != atomic_transfer.transactions[
            2].payment_transaction.receiver:
            raise NotImplementedError

        if atomic_transfer.transactions[1].asset_transfer_transaction.amount != 1:
            raise NotImplementedError

        return AsalyticDelisting(address=atomic_transfer.transactions[1].sender,
                                 asa_id=atomic_transfer.transactions[1].asset_transfer_transaction.asset_id)

    @staticmethod
    def init_from_sale(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/wZKxhdX5dSNVixmv8cIuYehgQ0OaUD%2B8ru%2FNJyTpKbc%3D
        :param atomic_transfer:
        :return:
        """
        sale = AsalyticSale.init_from_7_transactions(atomic_transfer=atomic_transfer)

        return AsalyticDelisting(address=atomic_transfer.transactions[5].sender,
                                 asa_id=sale.asa_id)

    @staticmethod
    def init_delisting(atomic_transfer: AtomicTransfer):

        try:
            delisting = AsalyticDelisting.init_from_cancel(atomic_transfer)
            return delisting
        except NotImplementedError:
            pass

        try:
            delisting = AsalyticDelisting.init_from_sale(atomic_transfer)
            return delisting
        except NotImplementedError:
            pass

        raise NotImplementedError
