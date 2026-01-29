from typing import List, Optional
from enum import Enum
from pydantic import BaseModel

from asalytic.models.ASA import ASA

__all__ = ["CollectionMintStatus", "ASACollection"]


def same_start_pattern(target: str, pattern: str) -> bool:
    if len(target) < len(pattern):
        return False

    return pattern == target[:len(pattern)]


class CollectionMintStatus(str, Enum):
    minted = "minted"
    not_minted = "notminted"
    unknown = "unknown"


class ASACollection(BaseModel):
    collection_name: str
    collection_id: str
    visible_collection: bool

    creator_name: str
    creator_id: str
    creator_addresses: List[str]

    valid_names: List[str] = []
    valid_unit_names: List[str] = []

    names_exceptions: List[str] = []
    unit_names_exceptions: List[str] = []

    asa_id_exceptions: List[int] = []

    description: Optional[str]

    mint_status: CollectionMintStatus

    only_nfts: bool = False

    supports_rarity: bool = False

    twitter: Optional[str]
    discord: Optional[str]
    website: Optional[str]

    collection_image: str
    creator_image: Optional[str]

    class Config:
        extra = "allow"

    def valid_asa(self, asa: ASA) -> bool:
        valid_creator_address = False

        for valid_address in self.creator_addresses:
            if asa.creator == valid_address:
                valid_creator_address = True

        if not valid_creator_address:
            return False

        if self.only_nfts and not asa.is_nft:
            return False

        name_is_valid = False

        if len(self.valid_names) == 0:
            name_is_valid = True
        else:
            for valid_name in self.valid_names:
                if asa.name is not None and valid_name in asa.name:
                    name_is_valid = True

        unit_name_is_valid = False

        if len(self.valid_unit_names) == 0:
            unit_name_is_valid = True
        else:
            for valid_unit_name in self.valid_unit_names:
                if asa.unit_name is not None and same_start_pattern(target=asa.unit_name, pattern=valid_unit_name):
                    unit_name_is_valid = True

        if len(self.asa_id_exceptions) > 0:
            if asa.asa_id in self.asa_id_exceptions:
                return False

        for invalid_name in self.names_exceptions:
            if asa.name is not None and invalid_name in asa.name:
                return False

        for invalid_unit_name in self.unit_names_exceptions:
            if asa.unit_name is not None and invalid_unit_name in asa.unit_name:
                return False

        return name_is_valid and unit_name_is_valid
