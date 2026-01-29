import requests

from asalytic.models.algorand import AtomicTransfer, TransactionType
from asalytic.models import Listing, ListingType
from asalytic.models.atomic_transfer.sales.rand_gallery import RandGallerySale
from asalytic.models.algorand import Transaction

import base64

# TODO: This is hard coded centralized parsing until rand releases their smart contracts

RAND_URI = 'https://www.randswap.com/v1/listings/asset/'
RAND_TOKEN = 'Asalytic_U3sb9YZ0dgQpFNFdL2S0dkzNoWlFnTXw'


def is_valid_listing_atomic_transfer(atomic_transfer: AtomicTransfer) -> bool:
    """
    https://algoexplorer.io/tx/group/ZFfnStd63BPdB8QGGSNWnNLVtXrBPGDI4Qf5vnf%2Fpeo%3D
    """

    transaction_order = [
        TransactionType.payment,
        TransactionType.asset_transfer,
        TransactionType.asset_transfer
    ]

    valid_ordering = False

    try:
        valid_ordering = atomic_transfer.valid_transaction_types(transaction_types=transaction_order)
    except:
        pass

    if not valid_ordering:
        return False

    if atomic_transfer.transactions[0].payment_transaction.amount != 201 * 1e3:
        return False

    receivers = set()

    receivers.add(atomic_transfer.transactions[0].payment_transaction.receiver)
    receivers.add(atomic_transfer.transactions[1].asset_transfer_transaction.receiver)
    receivers.add(atomic_transfer.transactions[2].asset_transfer_transaction.receiver)

    if len(receivers) != 1:
        return False

    if atomic_transfer.transactions[1].asset_transfer_transaction.amount != 0:
        return False

    if atomic_transfer.transactions[1].asset_transfer_transaction.receiver != atomic_transfer.transactions[1].sender:
        return False

    if atomic_transfer.transactions[0].sender != atomic_transfer.transactions[2].sender:
        return False

    return True


def parse_rand_listing(atomic_transfer: AtomicTransfer) -> Listing:
    if not is_valid_listing_atomic_transfer(atomic_transfer=atomic_transfer):
        raise NotImplementedError("Invalid Atomic Transfer")

    asa_id = atomic_transfer.asa_id
    escrow_address = atomic_transfer.transactions[1].sender

    listings_data = []

    try:
        listings_data = requests.get(f'{RAND_URI}{asa_id}?token=${RAND_TOKEN}').json()
    except:
        raise NotImplementedError("Not Able To Fetch Data")

    escrow_data = None

    for listing_data in listings_data:
        if listing_data['escrowAddress'] == escrow_address:
            escrow_data = listing_data
            break

    if escrow_data is None:
        raise NotImplementedError("Escrow Data Not Found")

    return Listing(asa_id=asa_id,
                   asa_creator_address=None,
                   collection_id=None,
                   type=ListingType.smart_signature,
                   price=escrow_data['price'] * 1e6,
                   seller=escrow_data['sellerAddress'],
                   time=atomic_transfer.block_time,
                   block=atomic_transfer.block,
                   platform="Rand Gallery",
                   creator_fee=escrow_data['creatorRoyalty'],
                   marketplace_fee=2.0,
                   referral_fee=0,
                   smart_signature_address=escrow_data['escrowAddress'])


def parse_rand_cancel_listing(atomic_transfer: AtomicTransfer) -> str:
    """
    If it is a valid delisting, it returns the escrow address which acts as an ID of a listing.
    :param atomic_transfer:
    :return:
    """
    transaction_order = [
        TransactionType.asset_transfer,
        TransactionType.asset_transfer,
        TransactionType.payment
    ]

    valid_ordering = False

    try:
        valid_ordering = atomic_transfer.valid_transaction_types(transaction_types=transaction_order)
    except:
        pass

    if not valid_ordering:
        raise NotImplementedError("Invalid Transaction Ordering")

    receivers = set()

    receivers.add(atomic_transfer.transactions[0].asset_transfer_transaction.receiver)
    receivers.add(atomic_transfer.transactions[1].asset_transfer_transaction.receiver)
    receivers.add(atomic_transfer.transactions[2].payment_transaction.receiver)

    if len(receivers) != 1:
        raise NotImplementedError("Invalid Receivers")

    if atomic_transfer.transactions[2].payment_transaction.amount != 198000:
        raise NotImplementedError("Invalid Amount")

    return atomic_transfer.transactions[1].sender


def parse_rand_sale_delisting(atomic_transfer: AtomicTransfer) -> str:
    """
    If it is a valid sale, it returns the escrow address which acts as an ID of a listing.
    """

    sale = None

    try:
        sale = RandGallerySale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
    except:
        raise NotImplementedError("Invalid Sale")

    return atomic_transfer.transactions[4].sender


def parse_rand_delisting(atomic_transfer: AtomicTransfer) -> str:
    try:
        return parse_rand_cancel_listing(atomic_transfer=atomic_transfer)
    except:
        pass

    try:
        return parse_rand_sale_delisting(atomic_transfer=atomic_transfer)
    except:
        raise NotImplementedError("Invalid Delisting")


def parse_rand_update_listing(transaction: Transaction) -> Listing:
    txn_note = base64.b64decode(transaction.note).decode("utf-8")

    asa_id = int(txn_note.split(' ')[-1])

    listings_data = []

    try:
        listings_data = requests.get(f'{RAND_URI}{asa_id}?token=${RAND_TOKEN}').json()
    except:
        raise NotImplementedError("Not Able To Fetch Data")

    escrow_data = None

    for listing_data in listings_data:
        if listing_data['sellerAddress'] == transaction.sender:
            escrow_data = listing_data
            break

    if escrow_data is None:
        raise NotImplementedError("Escrow Data Not Found")

    return Listing(asa_id=asa_id,
                   asa_creator_address=None,
                   collection_id=None,
                   type=ListingType.smart_signature,
                   price=escrow_data['price'] * 1e6,
                   seller=escrow_data['sellerAddress'],
                   time=transaction.round_time,
                   block=transaction.confirmed_round,
                   platform="Rand Gallery",
                   creator_fee=escrow_data['creatorRoyalty'],
                   marketplace_fee=2.0,
                   referral_fee=0,
                   smart_signature_address=escrow_data['escrowAddress'])
