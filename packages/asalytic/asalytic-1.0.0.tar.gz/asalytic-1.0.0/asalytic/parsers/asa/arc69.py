import json
import base64
from asalytic.models.ASA import ARC69Metadata
from asalytic.parsers.asa.utils import extract_traits, extract_filters
from typing import Optional
from asalytic.models.algorand import Transaction


def extract_arc69_metadata(transaction: Transaction) -> Optional[ARC69Metadata]:
    if transaction.note is None:
        return None

    try:
        arc69 = json.loads(base64.b64decode(transaction.note).decode('utf-8'))
        standard = arc69.get("standard", "invalid")
        filters = extract_filters(data=arc69)
        traits = extract_traits(data=arc69)
    except:
        return None

    if standard == 'arc69' and len(traits) > 0:
        return ARC69Metadata(traits=traits,
                             filters=filters if len(filters) > 0 else None,
                             description=arc69.get("description", None),
                             update_time=transaction.round_time,
                             block_number=transaction.confirmed_round)

    return None
