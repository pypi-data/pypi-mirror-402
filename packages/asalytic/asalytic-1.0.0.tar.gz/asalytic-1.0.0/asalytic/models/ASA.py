from pydantic import BaseModel
from typing import Optional, List

__all__ = ["Trait", "ARC3Metadata", "ARC19Metadata", "ARC69Metadata", "ASA", "SimilarASA"]

# IPFS_DOMAIN = 'https://ipfs.io/ipfs/'
IPFS_DOMAIN = 'https://ipfs.algonode.xyz/ipfs/'


class Trait(BaseModel):
    type: str
    value: str

    @property
    def id(self):
        return f'{self.type}__{self.value}'


class ARC3Metadata(BaseModel):
    traits: Optional[List[Trait]]
    filters: Optional[List[Trait]]
    description: Optional[str]
    ipfs_image_url: Optional[str]


class ARC19Metadata(BaseModel):
    traits: Optional[List[Trait]]
    filters: Optional[List[Trait]]
    description: Optional[str]
    ipfs_image_url: Optional[str]

    update_time: Optional[int]
    block_number: Optional[int]


class ARC69Metadata(BaseModel):
    traits: Optional[List[Trait]]
    filters: Optional[List[Trait]]
    description: Optional[str]

    update_time: Optional[int]
    block_number: Optional[int]


# TODO: Add IPFS hash
class ASA(BaseModel):
    asa_id: int

    name: Optional[str]
    unit_name: Optional[str]

    total: int
    decimals: int

    creator: str
    clawback: Optional[str]
    freeze: Optional[str]
    manager: Optional[str]
    reserve: Optional[str]

    created_round: Optional[int]
    created_time: Optional[int]

    default_frozen: Optional[bool]

    is_deleted: bool = False

    url: Optional[str]

    image_cached_url: Optional[str]

    collection_id: Optional[str]
    creator_id: Optional[str]

    arc3_metadata: Optional[ARC3Metadata]
    arc19_metadata: Optional[ARC19Metadata]
    arc69_metadata: Optional[ARC69Metadata]

    @property
    def is_nft(self):
        return self.total == 1 and self.decimals == 0

    @property
    def total_supply(self):
        return self.total

        if self.decimals == 0:
            return self.total
        else:
            return self.total * pow(10, self.decimals)

    @property
    def traits(self) -> Optional[List[Trait]]:
        if self.arc69_metadata is not None:
            if self.arc69_metadata.traits is not None and len(self.arc69_metadata.traits) > 0:
                return self.arc69_metadata.traits

        if self.arc3_metadata is not None:
            if self.arc3_metadata.traits is not None and len(self.arc3_metadata.traits) > 0:
                return self.arc3_metadata.traits

        if self.arc19_metadata is not None:
            if self.arc19_metadata.traits is not None and len(self.arc19_metadata.traits) > 0:
                return self.arc19_metadata.traits

        return None

    @property
    def ipfs_image_cid(self) -> Optional[str]:
        curr_image_url = self.url if self.url is not None else ''

        if self.arc3_metadata is not None and self.arc3_metadata.ipfs_image_url is not None:
            curr_image_url = self.arc3_metadata.ipfs_image_url

        if self.arc19_metadata is not None and self.arc19_metadata.ipfs_image_url is not None:
            curr_image_url = self.arc19_metadata.ipfs_image_url

        if 'ipfs://' in curr_image_url:
            ipfs_hash = curr_image_url.split('ipfs://')[1]
            return ipfs_hash

        return None

    @property
    def image_url(self) -> str:
        if self.image_cached_url:
            return self.image_cached_url

        curr_image_url = self.url if self.url is not None else ''

        if self.arc3_metadata is not None and self.arc3_metadata.ipfs_image_url is not None:
            curr_image_url = self.arc3_metadata.ipfs_image_url

        if self.arc19_metadata is not None and self.arc19_metadata.ipfs_image_url is not None:
            curr_image_url = self.arc19_metadata.ipfs_image_url

        if 'https' in curr_image_url:
            return curr_image_url

        if 'ipfs://' in curr_image_url:
            ipfs_hash = curr_image_url.split('ipfs://')[1]
            return f'{IPFS_DOMAIN}{ipfs_hash}'

        return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mPUrgcAANsArNNv+moAAAAASUVORK5CYII='

    def has_trait(self, trait: Trait) -> bool:
        if self.traits is None:
            return False

        for curr_trait in self.traits:
            if curr_trait.type == trait.type and curr_trait.value == trait.value:
                return True

        return False


# TODO: Remove this.
class SimilarASA(BaseModel):
    asa_id: int
    similar_nfts: List[int]
