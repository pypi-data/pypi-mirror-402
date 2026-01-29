from asalytic.models.algorand import AtomicTransfer, TransactionType

from asalytic.models.atomic_transfer.delistings.smart_signatures.SignatureDelisting import SignatureDelisting

ALGOxNFT_BANK = 'XNFT36FUCFRR6CK675FW4BEBCCCOJ4HOSMGCN6J2W6ZMB34KM2ENTNQCP4'


class ALGOxNFTDelisting(SignatureDelisting):

    @staticmethod
    def init_from_cancel(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/fhJ%2Fnn%2FmbjDN7Vk%2FZCn91O%2FiMQ2Ovn4O265Qv7VGNR4%3D
        :param atomic_transfer:
        :return:
        """
        transaction_order = [
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        if atomic_transfer.transactions[2].payment_transaction.receiver != ALGOxNFT_BANK:
            raise NotImplementedError("Invalid bank address")

        return ALGOxNFTDelisting(address=atomic_transfer.transactions[1].sender,
                                 asa_id=atomic_transfer.transactions[1].asset_transfer_transaction.asset_id)

    @staticmethod
    def init_from_sale(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/wZKxhdX5dSNVixmv8cIuYehgQ0OaUD%2B8ru%2FNJyTpKbc%3D
        :param atomic_transfer:
        :return:
        """
        transaction_order = [
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment,
            TransactionType.payment
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        if atomic_transfer.transactions[4].payment_transaction.receiver != ALGOxNFT_BANK:
            raise NotImplementedError("Invalid bank address")

        return ALGOxNFTDelisting(address=atomic_transfer.transactions[1].sender,
                                 asa_id=atomic_transfer.transactions[1].asset_transfer_transaction.asset_id)

    @staticmethod
    def init_delisting(atomic_transfer: AtomicTransfer):

        try:
            delisting = ALGOxNFTDelisting.init_from_cancel(atomic_transfer)
            return delisting
        except NotImplementedError:
            pass

        try:
            delisting = ALGOxNFTDelisting.init_from_sale(atomic_transfer)
            return delisting
        except NotImplementedError:
            pass

        raise NotImplementedError
