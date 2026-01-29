import requests
from requests.adapters import HTTPAdapter
import algosdk
from cid import CIDv1
import multihash
from typing import Optional
from asalytic.models.algorand import Transaction
from asalytic.models.ASA import ARC19Metadata, ASA
from asalytic.parsers.asa.utils import extract_traits, extract_filters

ASSET_NODE_URL = 'https://mainnet-api.algonode.cloud/v2/assets/'


class ARC19Exception(Exception):
    pass


def resolve_arc19_asset_url(asa_url: str, reserve_address: str) -> str:
    url_parts = asa_url.split('://')

    if url_parts[0] != 'template-ipfs' or len(url_parts) != 2:
        raise ARC19Exception("Invalid url template")

    template_parts = url_parts[1].split('}')

    template_parts[0] = template_parts[0].replace('{', '')
    template_parts[0] = template_parts[0].replace('}', '')

    parameters = template_parts[0].split(':')

    if len(parameters) != 5:
        raise ARC19Exception(f"Invalid number of ARC url parameters: {parameters}")

    if parameters[0] != 'ipfscid' or parameters[3] != 'reserve' or parameters[4] != 'sha2-256':
        raise NotImplementedError

    if parameters[2] != 'dag-pb' and parameters[2] != 'raw':
        raise NotImplementedError

    decoded_address = algosdk.encoding.decode_address(reserve_address)

    mhdigest = multihash.encode(decoded_address, 'sha2-256')
    cid = CIDv1(parameters[2], mhdigest)

    if len(template_parts) == 1:
        return str(cid)
    else:
        document_location = '/'.join(template_parts[1:])
        return f'{cid}/{document_location}'


def extract_arc19_metadata(asa: ASA,
                           transaction: Transaction,
                           ipfs_domain: str = 'https://ipfs.io/ipfs/',
                           is_metadata_image: bool = False) -> Optional[ARC19Metadata]:
    asa_url = asa.url
    reserve_address = asa.reserve

    if transaction.is_asset_update:
        reserve_address = transaction.asset_config_transaction.params.reserve

    if asa_url is None or reserve_address is None:
        return None

    try:
        arc19_url = resolve_arc19_asset_url(asa_url=asa_url,
                                            reserve_address=reserve_address)
    except:
        return None

    if arc19_url is None:
        return None

    if is_metadata_image:
        # Hard code that it is an image
        return ARC19Metadata(ipfs_image_url=f'ipfs://{arc19_url}',
                             traits=None,
                             description=None,
                             update_time=transaction.round_time,
                             block_number=transaction.confirmed_round)

    arc19_response = None
    try:
        s = requests.Session()
        ipfs_data_url = f'{ipfs_domain}{arc19_url}'
        s.mount(ipfs_data_url, HTTPAdapter(max_retries=5))
        arc19_response = s.get(url=ipfs_data_url)
    except:
        pass

    # Assume it is a JSON
    try:
        arc19_metadata = arc19_response.json()

        traits = extract_traits(data=arc19_metadata)
        filters = extract_filters(data=arc19_metadata)
        return ARC19Metadata(ipfs_image_url=arc19_metadata.get('image', None),
                             traits=traits if len(traits) > 0 else None,
                             filters=filters if len(filters) > 0 else None,
                             description=arc19_metadata.get('description', None),
                             update_time=transaction.round_time,
                             block_number=transaction.confirmed_round)
    except:
        pass

    # Assume it is an Image.
    if arc19_response.status_code == 200:
        return ARC19Metadata(ipfs_image_url=f'ipfs://{arc19_url}',
                             traits=None,
                             description=None,
                             update_time=transaction.round_time,
                             block_number=transaction.confirmed_round)

    return None
