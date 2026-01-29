from typing import List

from asalytic.models.algorand import AtomicTransfer
from asalytic.models.atomic_transfer.delistings.smart_signatures.SignatureDelisting import SignatureDelisting

from asalytic.models.atomic_transfer.delistings.smart_signatures.ALGOxNFTDelisting import ALGOxNFTDelisting
from asalytic.models.atomic_transfer.delistings.smart_signatures.AsalyticDelisting import AsalyticDelisting


class SignatureDelistingsATParser:

    @staticmethod
    def parse_atomic_transfers(atomic_transfers: List[AtomicTransfer]) -> List[SignatureDelisting]:
        parsed_delistings: List[SignatureDelisting] = []

        for atomic_transfer in atomic_transfers:

            try:
                parsed_delisting = ALGOxNFTDelisting.init_delisting(atomic_transfer=atomic_transfer)
                parsed_delistings.append(parsed_delisting)
                continue
            except:
                pass

            try:
                parsed_delisting = AsalyticDelisting.init_delisting(atomic_transfer=atomic_transfer)
                parsed_delistings.append(parsed_delisting)
                continue
            except:
                pass

        return [SignatureDelisting(**listing.dict()) for listing in parsed_delistings]
