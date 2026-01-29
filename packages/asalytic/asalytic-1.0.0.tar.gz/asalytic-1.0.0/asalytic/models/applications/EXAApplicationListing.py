from enum import Enum

from asalytic.models import Listing, ListingType
from asalytic.models.algorand import Application, StateSchema


class EXAAppStateKeys(str, Enum):
    seller = 'U0w='
    price = 'RkE='
    version = 'VkVS'
    state = 'U1Q='
    marketplace_address = 'UEZB'
    marketplace_fee = 'UEZQ'
    royalty = 'R1JQAAAAAAAAAAA='
    creator_address = 'R1JBAAAAAAAAAAA='
    asa_id = 'R0kAAAAAAAAAAA=='


def valid_exa_application_version_6(application: Application) -> bool:
    required_keys = [
        e.value for e in EXAAppStateKeys
    ]

    required_app_state = {
        EXAAppStateKeys.version: 6,
        EXAAppStateKeys.state: 'FUND',
    }

    required_app_schema = StateSchema(num_byte_slice=9, num_uint=24)

    valid_keys = application.valid_keys(required_keys=required_keys)
    valid_state = application.valid_key_values(required_key_values=required_app_state)
    valid_schema = application.valid_global_schema(required_schema=required_app_schema)

    return valid_keys and valid_state and valid_schema


class EXAApplicationListing(Listing):
    platform = "EXA Market"
    type = ListingType.application

    @staticmethod
    def init_listing_from_version_6(application: Application):
        is_valid = valid_exa_application_version_6(application=application)

        if not is_valid:
            raise NotImplementedError

        creator_fee = None

        try:
            creator_fee = application.app_state[EXAAppStateKeys.royalty]
            creator_fee /= 1e8
        except:
            pass

        platform_fee = None

        try:
            platform_fee = application.app_state[EXAAppStateKeys.marketplace_fee]
            platform_fee /= 100
        except:
            pass

        return EXAApplicationListing(
            asa_id=application.app_state[EXAAppStateKeys.asa_id],
            asa_creator_address=None,
            app_id=application.id,
            collection_id=None,
            price=application.app_state[EXAAppStateKeys.price],
            time=None,
            block=None,
            seller=application.app_state[EXAAppStateKeys.seller],
            creator_fee=creator_fee,
            marketplace_fee=platform_fee,
            referral_fee=20,
            delisting_time=None,
            delisting_block=None
        )

    @staticmethod
    def init_from_application(application: Application):

        try:
            return EXAApplicationListing.init_listing_from_version_6(application=application)
        except:
            pass

        raise NotImplementedError
