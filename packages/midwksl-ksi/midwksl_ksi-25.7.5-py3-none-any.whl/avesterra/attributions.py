""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""


from avesterra.avial import *
from avesterra.taxonomy import AvAttribute, AvAspect
import avesterra.aspects as aspects


def insert_attribution(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    parameter: AvParameter = NULL_PARAMETER,
) -> None:
    """Inserts an attribute of `attribute` and `value` at `index`, if specified, into `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to insert into `entity`
    value : AvValue
        Value to insert into attribute `attribute`
    index : AvIndex
        Index to insert the attribute into
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(4), authorization=authorization)

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.ENTITY, value=AvValue.encode_integer(2), authorization=authorization)
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.WIDTH, index=2, value=AvValue.encode_integer(3), authorization=authorization)


    Raises
    ______
    ApplicationError
        When an attribute of `attribute` is already present

    """
    aspects.insert(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        value=value,
        index=index,
        parameter=parameter,
        authorization=authorization,
    )


def remove_attribution(
    entity: AvEntity,
    authorization: AvAuthorization,
    index: AvIndex = NULL_INDEX,
    parameter: AvParameter = NULL_PARAMETER,
) -> None:
    """Removes an attribute `attribute` at `index` from `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    index : AvIndex
        Index to insert the attribute into
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(4), authorization=authorization)
    >>> attributions.remove_attribution(entity=entity, authorization=authorization)


    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(4), authorization=authorization)
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.ENTITY, value=AvValue.encode_integer(4), authorization=authorization)
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.ATTRIBUTION, value=AvValue.encode_integer(4), authorization=authorization)
    >>> attributions.remove_attribution(entity=entity, index=2, authorization=authorization)

    Raises
    ______
    ApplicationError
        When an attribute of `attribute` is already present

    """
    aspects.remove(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        index=index,
        parameter=parameter,
        authorization=authorization,
    )


def replace_attribution(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    parameter: AvParameter = NULL_PARAMETER,
) -> None:
    """Replace attribute at `index` with attribute of `attribute` and `value`; replaces last attribute if `index` == NULL_INDEX

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to use
    index : AvIndex
        Index of the attribute that will be replaced
    value : AvValue
        Value to use
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(2), authorization=authorization)
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(3), authorization=authorization)
    >>> attributions.replace_attribution(entity=entity, index=2, attribute=AvAttribute.TERRITORY, value=AvValue.encode_integer(4), authorization=authorization)

    Raises
    ______
    ApplicationError
        When an attribute of `attribute` is already present

    """
    aspects.replace(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        value=value,
        index=index,
        parameter=parameter,
        authorization=authorization,
    )


def find_attribution(
    entity: AvEntity,
    authorization: AvAuthorization,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
) -> AvIndex:
    """Find attribute of value `value` on entity after `index`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    index : AvIndex
        Index where the search will start
    value : AvValue
        Value to search for
    instance : AvInstance
        Instance(Property Table Index) in which the annotation will be inserted
    authorization : AvAuthorization
        An authorization that is able to read from `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(2), authorization=authorization)
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(3), authorization=authorization)
    >>> print(attributions.find_attribution(entity=entity, index=2, value=AvValue.encode_integer(2), authorization=authorization))
    2

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(2), authorization=authorization)
    >>> attributions.insert_attribution(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(3), authorization=authorization)
    >>> print(attributions.find_attribution(entity=entity, value=AvValue.encode_integer(0), authorization=authorization))
    0

    """
    return aspects.find(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        value=value,
        index=index,
        authorization=authorization,
    )


def include_attribution(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    parameter: AvParameter = NULL_PARAMETER,
    value: AvValue = NULL_VALUE,
) -> None:
    """Include attribute `attribute` of value `value` on `entity`; will overwrite `attribute` if already present

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to include
    value : AvValue
        Value to include
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.include_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.include_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(2), authorization=authorization)
    >>> attributions.include_attribution(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(3), authorization=authorization)

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.include_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.include_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(2), authorization=authorization)

    """
    return aspects.include(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_attribution(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    parameter: AvParameter = NULL_PARAMETER,
) -> None:
    """Exclude attribute `attribute` from `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to include
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.include_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.exclude_attribution(entity=entity, attribute=AvAttribute.WEIGHT, authorization=authorization)

    """
    return aspects.exclude(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        parameter=parameter,
        authorization=authorization,
    )


def set_attribution(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
) -> None:
    """Set attribute `attribute` with `value` on `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to set
    value : AvValue
        Value to set
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(2), authorization=authorization)

    """
    return aspects.set(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def get_attribution(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
) -> AvValue:
    """Get value of attribute `attribute` on `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to set
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.get_attribution(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization).decode_integer())
    1

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.get_attribution(entity=entity, attribute=AvAttribute.WIDTH, authorization=authorization))
    {"NULL": ""}

    """
    return aspects.get(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        authorization=authorization,
    )


def clear_attribution(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    parameter: AvParameter = NULL_PARAMETER,
) -> None:
    """Clear value of attribute `attribute` on `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to set
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.clear_attribution(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization)
    >>> print(attributions.get_attribution(entity=entity, attribute=AvAttribute.WIDTH, authorization=authorization))
    {"NULL": ""}

    """
    aspects.clear(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        parameter=parameter,
        authorization=authorization,
    )


def attribute_count(
    entity: AvEntity,
    authorization: AvAuthorization,
) -> AvCount:
    """Get number of attributions on `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.attribute_count(entity=entity, authorization=authorization))
    1

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> print(attributions.attribute_count(entity=entity, authorization=authorization))
    0

    """
    return aspects.count(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        authorization=authorization,
    )


def attribute_member(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
) -> bool:
    """Check if attribute `attribute` exists on `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to check for
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.attribute_member(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization))
    True

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.attribute_member(entity=entity, attribute=AvAttribute.HEAT, authorization=authorization))
    False

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> print(attributions.attribute_member(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization))
    False

    """
    return aspects.member(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        authorization=authorization,
    )


def attribute_name(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
) -> AvName:
    """Return attribute name(NULL_ATTRIBUTE, LOCATION_ATTRIBUTE, etc.) at `attribute` or `index` on `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to get name of
    index : AvIndex
        Index to get name of
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.attribute_name(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization))
    ATTRIBUTE_HEIGHT

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.ATTRIBUTE, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.attribute_name(entity=entity, index=1, authorization=authorization))
    ATTRIBUTE_ATTRIBUTE

    """
    return aspects.name(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        index=index,
        authorization=authorization,
    )


def attribute_key(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
) -> AvKey:
    """Return attribute key(NULL_ATTRIBUTE, LOCATION_ATTRIBUTE, etc.) at `attribute` or `index` on `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to get key of
    index : AvIndex
        Index to get key of
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.attribute_key(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization))
    ATTRIBUTE_HEIGHT

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.ATTRIBUTE, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.attribute_name(entity=entity, index=1, authorization=authorization))
    ATTRIBUTE_ATTRIBUTE

    """
    return aspects.key(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        index=index,
        authorization=authorization,
    )


def attribute_value(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
) -> AvValue:
    """Return value of attribute `attribute` or `index` on `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to get key of
    index : AvIndex
        Index to get key of
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.attribute_value(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization).decode_integer())
    1

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> print(attributions.attribute_value(entity=entity, index=1, authorization=authorization))
    1

    Raises
    ______
    ApplicationError
        When an attribute of `attribute` is not present on `entity`

    """
    return aspects.value(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        index=index,
        authorization=authorization,
    )


def attribute_index(
    entity: AvEntity,
    authorization: AvAuthorization,
    attribute: AvAttribute = NULL_ATTRIBUTE,
) -> AvIndex:
    """Return index of attribute `attribute` on `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to get key of
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(2), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(3), authorization=authorization)
    >>> print(attributions.attribute_index(entity=entity, attribute=AvAttribute.WIDTH, authorization=authorization))
    2

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(2), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(3), authorization=authorization)
    >>> print(attributions.attribute_index(entity=entity, attribute=AvAttribute.LOCATION, authorization=authorization))
    0

    """
    return aspects.index(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        authorization=authorization,
    )


def sort_attributions(
    entity: AvEntity,
    authorization: AvAuthorization,
    parameter: AvParameter = NULL_PARAMETER,
) -> None:
    """Sort attributions on `entity` by ordinal value in Taxonomy

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(2), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(3), authorization=authorization)
    >>> attributions.sort_attributions(entity=entity, authorization=authorization)

    """
    aspects.sort(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        parameter=parameter,
        authorization=authorization,
    )


def erase_attributions(
    entity: AvEntity,
    authorization: AvAuthorization,
    parameter: AvParameter = NULL_PARAMETER,
) -> None:
    """Erase all attributions on `entity`

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(2), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(3), authorization=authorization)
    >>> attributions.erase_attributions(entity=entity, authorization=authorization)
    >>> print(attributions.attribute_count(entity=entity, authorization=authorization))
    0

    """
    aspects.erase(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_attributions(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    """Retrieve attreibutes of `entity` in AvInterchange format

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to target
    instance : AvInstance
        Instance to target
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports attributions
    >>> authorization: AvAuthorization
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(1), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(2), authorization=authorization)
    >>> attributions.set_attribution(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(3), authorization=authorization)
    >>> print(attributions.retrieve_attributions(entity=entity, authorization=authorization))
    {"Attributes":[["HEIGHT_ATTRIBUTE",{"INTEGER":"1"},[]],["WIDTH_ATTRIBUTE",{"INTEGER":"2"},[]],["WEIGHT_ATTRIBUTE",{"INTEGER":"3"},[]]]}
    """
    return aspects.retrieve(
        aspect=AvAspect.ATTRIBUTION,
        entity=entity,
        attribute=attribute,
        instance=instance,
        authorization=authorization,
    )
