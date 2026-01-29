from enum import Enum

from asalytic.models import Listing, ListingType
from asalytic.models.algorand import Application, StateSchema
from asalytic.models.atomic_transfer.sales.constants import ASALYTIC_VALID_FACTORY_CREATOR_ADDRESSES


class AsalyticAppStateKeys(str, Enum):
    price = 'cHJpY2U='
    creator_amt = 'Y3JlYXRvcl9hbXQ='
    seller_amt = 'c2VsbGVyX2FtdA=='
    marketplace_amt = 'bWFya2V0cGxhY2VfYW10'
    asset = 'YXNzZXQ='
    creator = 'Y3JlYXRvcg=='
    marketplace = 'bWFya2V0cGxhY2U='
    seller = 'c2VsbGVy'


def valid_asalytic_application(application: Application) -> bool:
    required_keys = [
        e.value for e in AsalyticAppStateKeys
    ]

    required_app_schema = StateSchema(num_byte_slice=3, num_uint=5)

    valid_keys = application.valid_keys(required_keys=required_keys)
    valid_schema = application.valid_global_schema(required_schema=required_app_schema)
    valid_creator = application.params.creator in ASALYTIC_VALID_FACTORY_CREATOR_ADDRESSES

    return valid_keys and valid_schema and valid_creator


class AsalyticApplicationListing(Listing):
    platform = "Asalytic"
    type = ListingType.application

    @staticmethod
    def init_listing(application: Application):
        is_valid = valid_asalytic_application(application=application)

        if not is_valid:
            raise NotImplementedError

        creator_fee = 5
        marketplace_fee = (application.app_state[AsalyticAppStateKeys.marketplace_amt] * 2) / application.app_state[
            AsalyticAppStateKeys.price] * 100

        return AsalyticApplicationListing(
            asa_id=application.app_state[AsalyticAppStateKeys.asset],
            asa_creator_address=None,
            app_id=application.id,
            collection_id=None,
            price=application.app_state[AsalyticAppStateKeys.price],
            time=None,
            block=None,
            seller=application.app_state[AsalyticAppStateKeys.seller],
            creator_fee=creator_fee,
            marketplace_fee=marketplace_fee,
            referral_fee=50,
            delisting_time=None,
            delisting_block=None,
            a_seller_amount=application.app_state[AsalyticAppStateKeys.seller_amt],
            a_contract_amount=application.app_state[AsalyticAppStateKeys.marketplace_amt],
            a_creator_amount=application.app_state[AsalyticAppStateKeys.creator_amt],
            a_listing_wallet=application.app_state[AsalyticAppStateKeys.marketplace],
            a_creator_wallet=application.app_state[AsalyticAppStateKeys.creator],
        )

    @staticmethod
    def init_from_application(application: Application):

        try:
            return AsalyticApplicationListing.init_listing(application=application)
        except:
            pass

        raise NotImplementedError
