# from typing import List
#
# from asalytic.models.ASA import ASAMetadata
# from asalytic.parsers.asa.arc3 import extract_arc3_metadata
# from asalytic.parsers.asa.arc19 import extract_arc19_metadata
# from asalytic.parsers.asa.arc69 import extract_arc69_metadata
#
#
# def extract_asa_metadata(asset_config_transaction: dict,
#                          arc3_ipfs_domain: str = 'https://ipfs.io/ipfs/',
#                          arc19_ipfs_domain: str = 'https://ipfs.io/ipfs/') -> List[ASAMetadata]:
#     asa_metadata: List[ASAMetadata] = []
#
#     try:
#         arc3_metadata = extract_arc3_metadata(asset_config_transaction=asset_config_transaction,
#                                               ipfs_domain=arc3_ipfs_domain)
#         asa_metadata.append(arc3_metadata)
#     except:
#         pass
#
#     try:
#         arc19_metadata = extract_arc19_metadata(asset_config_transaction=asset_config_transaction,
#                                                 ipfs_domain=arc19_ipfs_domain)
#         asa_metadata.append(arc19_metadata)
#     except:
#         pass
#
#     try:
#         arc69_metadata = extract_arc69_metadata(asset_config_transaction=asset_config_transaction)
#         asa_metadata.append(arc69_metadata)
#     except:
#         pass
#
#     return asa_metadata
#
#
# def merge_asa_metadata(previous_asa_metadata: ASAMetadata, extracted_asa_metadata: List[ASAMetadata]) -> ASAMetadata:
#     new_asa_metadata = ASAMetadata(**previous_asa_metadata.dict())
#
#     for asa_metadata in extracted_asa_metadata:
#         new_asa_metadata.supports_arc3 = new_asa_metadata.supports_arc3 or asa_metadata.supports_arc3
#         new_asa_metadata.supports_arc19 = new_asa_metadata.supports_arc19 or asa_metadata.supports_arc19
#         new_asa_metadata.supports_arc69 = new_asa_metadata.supports_arc69 or asa_metadata.supports_arc69
#
#         if asa_metadata.traits is not None and len(asa_metadata.traits) > 0:
#             new_asa_metadata.traits = asa_metadata.traits
#
#         if asa_metadata.image_url is not None:
#             new_asa_metadata.image_url = asa_metadata.image_url
#
#         if asa_metadata.description is not None:
#             new_asa_metadata.description = asa_metadata.description
#
#     return new_asa_metadata
