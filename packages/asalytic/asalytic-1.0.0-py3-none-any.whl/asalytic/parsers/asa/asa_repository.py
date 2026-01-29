from asalytic.models.algorand import Transaction
from asalytic.models.ASA import ASA

from asalytic.parsers.asa.arc3 import extract_arc3_metadata
from asalytic.parsers.asa.arc19 import extract_arc19_metadata
from asalytic.parsers.asa.arc69 import extract_arc69_metadata


def update_role_addresses_asa_properties(asa_properties: dict, asa: ASA, transaction: Transaction) -> dict:
    # The change of role address should not be allowed if it was first set to null.
    # https://developer.algorand.org/docs/get-details/transactions/#asset-configuration-transaction

    params = transaction.asset_config_transaction.params

    asa_properties['creator'] = params.creator

    if asa.clawback is not None:
        asa_properties['clawback'] = params.clawback

    if asa.freeze is not None:
        asa_properties['freeze'] = params.freeze

    if asa.manager is not None:
        asa_properties['manager'] = params.manager

    if asa.reserve is not None:
        asa_properties['reserve'] = params.reserve

    return asa_properties


def create_asa_from_asset_config_transaction(transaction: Transaction) -> ASA:
    if transaction.txn_type != 'acfg':
        raise NotImplementedError("Invalid transaction type on initialization")

    if transaction.created_asset_index is None:
        raise NotImplementedError("This is not asset creation transaction")

    params = transaction.asset_config_transaction.params

    return ASA(asa_id=transaction.created_asset_index,
               name=params.name,
               unit_name=params.unit_name,
               total=params.total,
               decimals=params.decimals,
               creator=params.creator,
               clawback=params.clawback,
               freeze=params.freeze,
               manager=params.manager,
               reserve=params.reserve,
               created_round=transaction.confirmed_round,
               created_time=transaction.round_time,
               default_frozen=params.default_frozen,
               url=params.url)


def update_asa_arc3_metadata(asa: ASA,
                             transaction: Transaction,
                             ipfs_domain: str = 'https://ipfs.io/ipfs/') -> ASA:
    if not transaction.is_asset_create:
        raise NotImplementedError("This is not a valid asset create transaction")

    asa_properties = asa.dict()

    asa_properties = update_role_addresses_asa_properties(asa_properties=asa_properties,
                                                          asa=asa,
                                                          transaction=transaction)

    arc3_metadata = extract_arc3_metadata(transaction=transaction, ipfs_domain=ipfs_domain)

    if arc3_metadata is not None:
        asa_properties['arc3_metadata'] = arc3_metadata.dict()

    return ASA(**asa_properties)


def update_asa_arc19_metadata(asa: ASA,
                              transaction: Transaction,
                              ipfs_domain: str = 'https://ipfs.io/ipfs/',
                              is_metadata_image: bool = False) -> ASA:
    if transaction.asset_config_transaction is None:
        raise NotImplementedError("This is not a valid transaction type")

    asa_properties = asa.dict()

    asa_properties = update_role_addresses_asa_properties(asa_properties=asa_properties,
                                                          asa=asa,
                                                          transaction=transaction)

    arc19_metadata = extract_arc19_metadata(asa=asa,
                                            transaction=transaction,
                                            ipfs_domain=ipfs_domain,
                                            is_metadata_image=is_metadata_image)

    if arc19_metadata is not None:
        asa_properties['arc19_metadata'] = arc19_metadata.dict()

    return ASA(**asa_properties)


def update_asa_arc69_metadata(asa: ASA, transaction: Transaction) -> ASA:
    if transaction.txn_type != 'acfg':
        raise NotImplementedError("This is not a asset config transaction")

    asa_properties = asa.dict()

    asa_properties = update_role_addresses_asa_properties(asa_properties=asa_properties,
                                                          asa=asa,
                                                          transaction=transaction)

    new_arc69_metadata = extract_arc69_metadata(transaction=transaction)

    if new_arc69_metadata is not None:
        asa_properties['arc69_metadata'] = new_arc69_metadata.dict()

    return ASA(**asa_properties)
