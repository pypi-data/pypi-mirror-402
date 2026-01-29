from typing import List
from asalytic.models.ASA import Trait


def extract_traits_from_dict(data) -> List[Trait]:
    """
    Tries to extract list of traits from the current dictionary.
    We know how to parse on of the following trait types:
    - dict: {"trait_type": "trait_value", "trait_type": "trait_value"}
    - list of traits: [{trait_type: TRAIT_TYPE, trait_value: TRAIT_VALUE},
    {trait_type: TRAIT_TYPE, trait_value: TRAIT_VALUE}]
    :param data: - can be a list or a dictionary.
    :return:
    """
    traits: List[Trait] = []

    for attribute in data:
        try:
            trait_type = attribute.get('trait_type', None)
            trait_value = attribute.get('value', None)
            if trait_type is not None and trait_value is not None:
                traits.append(Trait(type=str(trait_type),
                                    value=str(trait_value)))
        except:
            continue

    if len(traits) > 0:
        return traits

    try:
        # Normal dictionary
        for trait_type, trait_value in data.items():
            traits.append(Trait(type=str(trait_type),
                                value=str(trait_value)))
    except:
        pass

    if len(traits) > 0:
        return traits


def extract_traits(data: dict) -> List[Trait]:
    traits: List[Trait] = []

    # Cosmic Champs Exception?
    # This should go first, because we will treat attributes as traits.
    # https://ipfs.algonft.tools/ipfs/Qmf52u8mT4H1s3pqpiH3boJ4xYiwB7m3WQLC7GGcV9xGN4#arc3
    if 'properties' in data:
        try:
            if 'attributes' in data['properties']:
                curr_traits = extract_traits_from_dict(data['properties']['attributes'])
                if len(curr_traits) > 0:
                    return curr_traits
        except:
            pass

    if 'properties' in data:
        try:
            if 'traits' in data['properties']:
                curr_traits = extract_traits_from_dict(data['properties']['traits'])
                if len(curr_traits) > 0:
                    return curr_traits

            curr_traits = extract_traits_from_dict(data['properties'])
            if len(curr_traits) > 0:
                return curr_traits
        except:
            pass

    if 'attributes' in data:
        try:
            for attribute in data['attributes']:
                trait_type = attribute.get('trait_type', None)
                trait_value = attribute.get('value', None)
                if trait_type is not None and trait_value is not None:
                    traits.append(Trait(type=trait_type,
                                        value=trait_value))
            return traits
        except:
            pass

    return traits


def extract_filters(data: dict) -> List[Trait]:
    if 'properties' in data:
        try:
            if 'filters' in data['properties']:
                curr_traits = extract_traits_from_dict(data['properties']['filters'])
                if len(curr_traits) > 0:
                    return curr_traits
        except:
            pass

    if 'filters' in data:
        try:
            curr_traits = extract_traits_from_dict(data['filters'])
            if len(curr_traits) > 0:
                return curr_traits
        except:
            pass
    return []
