from typing import List

from asalytic.models.algorand import AtomicTransfer
from asalytic.models.atomic_transfer.listings.application.ATAppListing import ATAppListing

from asalytic.models.atomic_transfer.listings.application.EXAListings import EXAListing
from asalytic.models.atomic_transfer.listings.application.ShuflListing import ShuflListing
from asalytic.models.atomic_transfer.listings.application.AsalyticListing import AsalyticListing


class AppListingsATParser:

    @staticmethod
    def parse_atomic_transfers(atomic_transfers: List[AtomicTransfer]) -> List[ATAppListing]:
        parsed_listings: List[ATAppListing] = []

        for atomic_transfer in atomic_transfers:

            try:
                parsed_listing = EXAListing.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                parsed_listings.append(parsed_listing)
                continue
            except:
                pass

            try:
                parsed_listing = ShuflListing.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                parsed_listings.append(parsed_listing)
                continue
            except:
                pass

            try:
                parsed_listing = AsalyticListing.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                parsed_listings.append(parsed_listing)
                continue
            except:
                pass

        return [ATAppListing(**listing.dict()) for listing in parsed_listings]
