from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.atomic_transfer.listings.smart_signature.ATSignatureListing import \
    AtomicTransferSignatureListing


class ALGOxNFTSignatureListing(AtomicTransferSignatureListing):
    platform = "ALGOxNFT"

    @staticmethod
    def init_from_3_transactions(atomic_transfer: AtomicTransfer):
        """
        https://algoexplorer.io/tx/group/p8BbdxNj5aqOsxu1b3ySNJlAsIPlQTCcMyl3FlFjxJQ%3D
        :param atomic_transfer:
        :return:
        """

        transaction_order = [
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        return ALGOxNFTSignatureListing(time=atomic_transfer.block_time,
                                        block=atomic_transfer.block,
                                        address=atomic_transfer.transactions[0].payment_transaction.receiver,
                                        teal_tx_id=atomic_transfer.transactions[1].txn_id,
                                        group=atomic_transfer.group_id)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):

        try:
            listing = ALGOxNFTSignatureListing.init_from_3_transactions(atomic_transfer)
            return listing
        except NotImplementedError:
            pass

        raise NotImplementedError
