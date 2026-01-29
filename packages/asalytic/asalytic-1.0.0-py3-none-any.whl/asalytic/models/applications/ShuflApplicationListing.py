from enum import Enum

from asalytic.models import Listing, ListingType
from asalytic.models.algorand import Application, StateSchema

CREATOR_FEE = 5.0
PLATFORM_FEE = 3.0
REFERRAL_FEE = 0.0


class ShuflAppStateKeys(str, Enum):
    seller = 'Z2xvYmFsX2xpc3Rfb3duZXI='
    price = 'Z2xvYmFsX2xpc3RfcHJpY2U='
    state = 'Z2xvYmFsX2xpc3Rfc3RhdHVz'
    asa_id = 'Z2xvYmFsX2xpc3RfYXNzZXQ='


def valid_shufl_application(application: Application) -> bool:
    required_keys = [
        e.value for e in ShuflAppStateKeys
    ]

    required_app_state = {
        ShuflAppStateKeys.state: 1,
    }

    required_app_schema = StateSchema(num_byte_slice=1, num_uint=4)

    valid_keys = application.valid_keys(required_keys=required_keys)
    valid_state = application.valid_key_values(required_key_values=required_app_state)
    valid_schema = application.valid_global_schema(required_schema=required_app_schema)

    return valid_keys and valid_state and valid_schema


class ShuflApplicationListing(Listing):
    platform = "Shufl"
    type = ListingType.application

    @staticmethod
    def init_listing_from_app(application: Application):
        is_valid = valid_shufl_application(application=application)

        if not is_valid:
            raise NotImplementedError

        return ShuflApplicationListing(
            asa_id=application.app_state[ShuflAppStateKeys.asa_id],
            asa_creator_address=None,
            app_id=application.id,
            collection_id=None,
            price=application.app_state[ShuflAppStateKeys.price],
            time=None,
            block=None,
            seller=application.app_state[ShuflAppStateKeys.seller],
            creator_fee=CREATOR_FEE,
            marketplace_fee=PLATFORM_FEE,
            referral_fee=REFERRAL_FEE,
            delisting_time=None,
            delisting_block=None
        )

    @staticmethod
    def init_from_application(application: Application):

        try:
            return ShuflApplicationListing.init_listing_from_app(application=application)
        except:
            pass

        raise NotImplementedError
