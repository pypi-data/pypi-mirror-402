from typing import List

from asalytic.models.algorand import AtomicTransfer
from asalytic.models.atomic_transfer.listings.smart_signature.ATSignatureListing import \
    AtomicTransferSignatureListing

from asalytic.models.atomic_transfer.listings.smart_signature.ALGOxNFTSignatureListing import ALGOxNFTSignatureListing
from asalytic.models.atomic_transfer.listings.smart_signature.AsalyticSignatureListing import AsalyticSignatureListing


class SignatureListingsATParser:

    @staticmethod
    def parse_atomic_transfers(atomic_transfers: List[AtomicTransfer]) -> List[AtomicTransferSignatureListing]:
        parsed_listings: List[AtomicTransferSignatureListing] = []

        for atomic_transfer in atomic_transfers:

            try:
                parsed_listing = ALGOxNFTSignatureListing.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                parsed_listings.append(parsed_listing)
                continue
            except:
                pass

            try:
                parsed_listing = AsalyticSignatureListing.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                parsed_listings.append(parsed_listing)
                continue
            except:
                pass

        return [AtomicTransferSignatureListing(**listing.dict()) for listing in parsed_listings]
