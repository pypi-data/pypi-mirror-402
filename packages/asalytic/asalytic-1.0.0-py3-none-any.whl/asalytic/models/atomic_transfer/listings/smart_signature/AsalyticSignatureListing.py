from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models.atomic_transfer.listings.smart_signature.ATSignatureListing import \
    AtomicTransferSignatureListing


class AsalyticSignatureListing(AtomicTransferSignatureListing):
    platform = "Asalytic"

    @staticmethod
    def init_from_4_transactions(atomic_transfer: AtomicTransfer):
        """
        https://allo.info/tx/group/9v0R%2FlfI14ACwav%2BijN3BPo16BgB6N5jXNDn6LBQF7E%3D/
        - 9v0R/lfI14ACwav+ijN3BPo16BgB6N5jXNDn6LBQF7E=
        - 38346626
        """

        transaction_order = [
            TransactionType.payment,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer,
            TransactionType.asset_transfer
        ]

        if not atomic_transfer.valid_inner_transaction_types(transaction_types=transaction_order):
            raise NotImplementedError("Invalid transaction ordering")

        return AsalyticSignatureListing(time=atomic_transfer.block_time,
                                        block=atomic_transfer.block,
                                        address=atomic_transfer.transactions[1].asset_transfer_transaction.receiver,
                                        teal_tx_id=atomic_transfer.transactions[1].txn_id,
                                        group=atomic_transfer.group_id)

    @staticmethod
    def init_from_atomic_transfer(atomic_transfer: AtomicTransfer):

        try:
            listing = AsalyticSignatureListing.init_from_4_transactions(atomic_transfer)
            return listing
        except NotImplementedError:
            pass

        raise NotImplementedError
