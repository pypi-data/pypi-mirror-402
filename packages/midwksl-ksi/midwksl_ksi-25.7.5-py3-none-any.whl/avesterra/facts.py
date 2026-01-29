""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""


import avesterra.aspects as aspects
from avesterra.avial import *

import avesterra.aspects as aspects
from avesterra.avial import *
import avesterra.aspects as aspects


def insert_fact(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Insert a fact into the fact list at a specific index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to be inserted, must be unique if not null
    value : AvValue
        Value of the fact to be inserted
    index : AvIndex
        Index in the fact list where the fact will be inserted
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(50), index=2, authorization=authorization)
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(25), index=1, authorization=authorization) # This will shift HEIGHT to index 2

    """
    aspects.insert(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        value=value,
        index=index,
        parameter=parameter,
        authorization=authorization,
    )


def remove_fact(
    entity: AvEntity,
    index: AvIndex = NULL_INDEX,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove a fact from the fact list at a specific index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    index : AvIndex
        Index of the fact to be removed from the fact list
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)
    >>> facts.remove_fact(entity=entity, index=1, authorization=authorization)

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(50), index=2, authorization=authorization)
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.DEPTH, value=AvValue.encode_integer(25), index=3, authorization=authorization)
    >>> facts.remove_fact(entity=entity, index=2, authorization=authorization) # Removes WIDTH, DEPTH moves to index 2

    """
    aspects.remove(
        entity=entity,
        aspect=AvAspect.FACT,
        index=index,
        parameter=parameter,
        authorization=authorization,
    )


def replace_fact(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Replace a fact at a specific index with a new attribute/value pair

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        New attribute for the fact, must be unique if not null
    value : AvValue
        New value for the fact
    index : AvIndex
        Index of the fact to be replaced
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)
    >>> facts.replace_fact(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(50), index=1, authorization=authorization)

    """
    aspects.replace(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        value=value,
        index=index,
        parameter=parameter,
        authorization=authorization,
    )


def find_fact(
    entity: AvEntity,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Find the index of a fact with a specific value

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    value : AvValue
        Value to search for in the fact list
    index : AvIndex
        Starting index for the search
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index of the fact with the specified value, or NULL_INDEX if not found

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(50), index=2, authorization=authorization)
    >>> index = facts.find_fact(entity=entity, value=AvValue.encode_integer(50), authorization=authorization)
    >>> print(index) # Will print 2

    """
    return aspects.find(
        entity=entity,
        aspect=AvAspect.FACT,
        value=value,
        index=index,
        authorization=authorization,
    )


def include_fact(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Include a fact if it doesn't already exist (set-like behavior)

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to be included, must be unique if not null
    value : AvValue
        Value of the fact to be included
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.include_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> facts.include_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization) # Won't duplicate

    """
    aspects.include(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_fact(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Exclude (remove) a fact with a specific attribute

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to be excluded
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> facts.exclude_fact(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization)

    """
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        parameter=parameter,
        authorization=authorization,
    )


def set_fact(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Set a fact with a specific attribute to a value (replaces if exists)

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to be set, must be unique if not null
    value : AvValue
        Value to set for the fact
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(150), authorization=authorization) # Updates existing

    """
    aspects.set(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def get_fact(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a fact with a specific attribute

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to retrieve
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        Value of the fact with the specified attribute, or NULL_VALUE if not found

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> value = facts.get_fact(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization)
    >>> print(value.decode_integer()) # Will print 100

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> value = facts.get_fact(entity=entity, attribute=AvAttribute.WIDTH, authorization=authorization)
    >>> print(value) # Will print {"NULL": ""}

    """
    return aspects.get(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        authorization=authorization,
    )


def clear_fact(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Clear (remove) a fact with a specific attribute

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to be cleared
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> facts.clear_fact(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization)

    """
    aspects.clear(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        parameter=parameter,
        authorization=authorization,
    )


def fact_count(
    entity: AvEntity, authorization: AvAuthorization = NULL_AUTHORIZATION
) -> AvCount:
    """Get the number of facts in the fact list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvCount
        Total number of facts in the entity's fact list

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(50), authorization=authorization)
    >>> count = facts.fact_count(entity=entity, authorization=authorization)
    >>> print(count) # Will print 2

    """
    return aspects.count(
        entity=entity, aspect=AvAspect.FACT, authorization=authorization
    )


def fact_member(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvBoolean:
    """Check if a fact with a specific attribute exists

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to check for in the fact list
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvBoolean
        True if a fact with the specified attribute exists, False otherwise

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> exists = facts.fact_member(entity=entity, attribute=AvAttribute.HEIGHT, authorization=authorization)
    >>> print(exists) # Will print True
    >>> exists = facts.fact_member(entity=entity, attribute=AvAttribute.WIDTH, authorization=authorization)
    >>> print(exists) # Will print False

    """
    return aspects.member(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        authorization=authorization,
    )


def fact_name(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    """Get the name of a fact attribute at a specific index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to get the name for
    index : AvIndex
        Index of the fact in the fact list
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvName
        Name of the fact attribute

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)
    >>> name = facts.fact_name(entity=entity, index=1, authorization=authorization)
    >>> print(name) # Will print the name of HEIGHT_ATTRIBUTE

    """
    return aspects.name(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        index=index,
        authorization=authorization,
    )


def fact_key(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    """Get the key of a fact at a specific index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to get the key for
    index : AvIndex
        Index of the fact in the fact list
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvKey
        Key of the fact (typically empty for facts)

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)
    >>> key = facts.fact_key(entity=entity, index=1, authorization=authorization)
    >>> print(key) # Will typically print empty string

    """
    return aspects.key(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        index=index,
        authorization=authorization,
    )


def fact_value(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a fact at a specific index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to get the value for
    index : AvIndex
        Index of the fact in the fact list
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        Value of the fact at the specified index

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)
    >>> value = facts.fact_value(entity=entity, index=1, authorization=authorization)
    >>> print(value.decode_integer()) # Will print 100

    """
    return aspects.value(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        index=index,
        authorization=authorization,
    )


def fact_index(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Get the index of a fact with a specific attribute

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute to find the index for
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index of the fact with the specified attribute, or NULL_INDEX if not found

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(50), index=2, authorization=authorization)
    >>> index = facts.fact_index(entity=entity, attribute=AvAttribute.WIDTH, authorization=authorization)
    >>> print(index) # Will print 2

    """
    return aspects.index(
        entity=entity,
        aspect=AvAspect.FACT,
        attribute=attribute,
        authorization=authorization,
    )


def fact_attribute(
    entity: AvEntity,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    """Get the attribute of a fact at a specific index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    index : AvIndex
        Index of the fact in the fact list
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvAttribute
        Attribute of the fact at the specified index

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.insert_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), index=1, authorization=authorization)
    >>> attribute = facts.fact_attribute(entity=entity, index=1, authorization=authorization)
    >>> print(attribute) # Will print AvAttribute.HEIGHT

    """
    return aspects.attribute(
        entity=entity, aspect=AvAspect.FACT, index=index, authorization=authorization
    )


def sort_facts(
    entity: AvEntity,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Sort facts by their attribute ordinal value in the Attribute Taxonomy

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(50), authorization=authorization)
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.DEPTH, value=AvValue.encode_integer(25), authorization=authorization)
    >>> facts.sort_facts(entity=entity, authorization=authorization)
    >>> # Facts are now sorted by their attribute taxonomy order

    """
    aspects.sort(
        entity=entity,
        aspect=AvAspect.FACT,
        parameter=parameter,
        authorization=authorization,
    )


def erase_facts(
    entity: AvEntity,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Erase all facts from the entity

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(50), authorization=authorization)
    >>> facts.erase_facts(entity=entity, authorization=authorization)
    >>> count = facts.fact_count(entity=entity, authorization=authorization)
    >>> print(count) # Will print 0

    """
    aspects.erase(
        entity=entity,
        aspect=AvAspect.FACT,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_facts(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION
) -> AvInterchange:
    """Retrieve all facts from the entity in AvInterchange format

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Target attribute
    instance : AvInstance
        Target instance
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvInterchange
        All facts from the entity in JSON format

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.HEIGHT, value=AvValue.encode_integer(100), authorization=authorization)
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.WIDTH, value=AvValue.encode_integer(50), authorization=authorization)
    >>> facts.set_fact(entity=entity, attribute=AvAttribute.WEIGHT, value=AvValue.encode_integer(25), authorization=authorization)
    >>> print(facts.retrieve_facts(entity=entity, authorization=authorization))
    {"Facts":[["HEIGHT_ATTRIBUTE",{"INTEGER":"100"}],["WIDTH_ATTRIBUTE",{"INTEGER":"50"}],["WEIGHT_ATTRIBUTE",{"INTEGER":"25"}]]}

    """
    return aspects.retrieve(
        entity=entity, aspect=AvAspect.FACT, attribute=attribute, instance=instance, authorization=authorization
    )