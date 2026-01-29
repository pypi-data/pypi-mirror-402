import requests
from requests.adapters import HTTPAdapter

from asalytic.models.ASA import ARC3Metadata
from asalytic.parsers.asa.utils import extract_traits, extract_filters

from typing import Optional
from asalytic.models.algorand import Transaction


def extract_arc3_metadata(transaction: Transaction,
                          ipfs_domain: str = 'https://ipfs.io/ipfs/') -> Optional[ARC3Metadata]:
    if not transaction.is_asset_create:
        return None

    params = transaction.asset_config_transaction.params

    if params.url is None or params.name is None:
        return None

    is_valid_request_url = False

    if params.url[-4:] == 'arc3':
        is_valid_request_url = True

    if 'arc3' in params.name:
        is_valid_request_url = True

    if 'template-ipfs://' in params.url:
        is_valid_request_url = False

    if 'template-ipfs' in params.url:
        is_valid_request_url = False

    if not is_valid_request_url:
        return None

    request_url = None

    if 'ipfs://' in params.url:
        ipfs_hash = params.url.split('ipfs://')[1]
        request_url = f'{ipfs_domain}{ipfs_hash}'
    elif 'https://' in params.url:
        request_url = params.url

    if request_url is None:
        return None

    try:
        s = requests.Session()
        s.mount(request_url, HTTPAdapter(max_retries=5))
        response = s.get(url=request_url)

        response = response.json()
        image_url = response['image']
        traits = extract_traits(data=response)
        filters = extract_filters(data=response)
        return ARC3Metadata(ipfs_image_url=image_url,
                            traits=traits if len(traits) > 0 else None,
                            filters=filters if len(filters) > 0 else None,
                            description=response.get('description', None))
    except:
        return None
