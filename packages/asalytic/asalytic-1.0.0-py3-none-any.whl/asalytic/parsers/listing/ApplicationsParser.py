from typing import List

from asalytic.models.algorand import Application

from asalytic.models.Listing import Listing

from asalytic.models.applications.EXAApplicationListing import EXAApplicationListing
from asalytic.models.applications.ShuflApplicationListing import ShuflApplicationListing
from asalytic.models.applications.AsalyticApplicationListing import AsalyticApplicationListing


class ApplicationParser:

    @staticmethod
    def parse_applications(applications: List[Application]) -> List[Listing]:
        listings: List[Listing] = []

        for application in applications:

            try:
                listing = EXAApplicationListing.init_from_application(application=application)
                listings.append(listing)
                continue
            except:
                pass

            try:
                listing = ShuflApplicationListing.init_from_application(application=application)
                listings.append(listing)
                continue
            except:
                pass

            try:
                listing = AsalyticApplicationListing.init_from_application(application=application)
                listings.append(listing)
                continue
            except:
                pass

        return [Listing(**listing.dict()) for listing in listings]
