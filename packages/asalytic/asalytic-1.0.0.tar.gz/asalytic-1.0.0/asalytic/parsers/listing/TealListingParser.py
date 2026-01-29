from typing import List, Tuple

from asalytic.models import Listing, Teal
from asalytic.models.algorand import AtomicTransfer

from asalytic.models.smart_signatures.listings.ALGOxNFTListing import ALGOxNFTListing
from asalytic.models.smart_signatures.listings.AsalyticListing import AsalyticListing


class TealListingParser:

    @staticmethod
    def parse_programs(teal_programs: List[Tuple[Teal, AtomicTransfer]]) -> List[Listing]:
        listings: List[Listing] = []

        for teal, atomic_transfer in teal_programs:

            try:
                listing = ALGOxNFTListing.init_from_teal(teal=teal, atomic_transfer=atomic_transfer)
                listings.append(listing)
                continue
            except:
                pass

            try:
                listing = AsalyticListing.init_from_teal(teal=teal, atomic_transfer=atomic_transfer)
                listings.append(listing)
                continue
            except:
                pass

        return [Listing(**listing.dict()) for listing in listings]
