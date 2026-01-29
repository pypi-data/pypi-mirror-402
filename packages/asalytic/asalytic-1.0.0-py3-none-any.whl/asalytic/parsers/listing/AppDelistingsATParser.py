from typing import List

from asalytic.models.algorand import AtomicTransfer
from asalytic.models.atomic_transfer.delistings.AtomicTransferDelisting import AtomicTransferDelisting

from asalytic.models.atomic_transfer.delistings.ShuflDelisting import ShuflDelisting


class AppDelistingATParser:

    @staticmethod
    def parse_atomic_transfers(atomic_transfers: List[AtomicTransfer]) -> (
            List[AtomicTransferDelisting], List[AtomicTransfer]):

        parsed_delistings: List[AtomicTransferDelisting] = []
        unknown: List[AtomicTransfer] = []

        for atomic_transfer in atomic_transfers:

            try:
                parsed_delisting = ShuflDelisting.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                parsed_delistings.append(parsed_delisting)
                continue
            except:
                pass

            unknown.append(atomic_transfer)

        parsed_delistings = [AtomicTransferDelisting(**delisting.dict()) for delisting in parsed_delistings]

        return parsed_delistings, unknown
