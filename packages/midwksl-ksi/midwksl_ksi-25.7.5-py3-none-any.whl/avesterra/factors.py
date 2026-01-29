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

from avesterra.avial import *
import avesterra.aspects as aspects


def insert_factor(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Insert a factor into a facet within a fact
    
    Factors are key/value pairs that belong to facets. Each key within a facet must be unique.
    Factors provide a means to add uniquely keyed values to facets within the fact construct.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Unique key identifier for the factor within the facet
    value : AvValue
        Value to be stored with the factor
    index : AvIndex
        Position in the factor list to insert the factor
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position for the insertion
    parameter : AvParameter
        Additional parameter for the insertion operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.insert_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="factor_key", value=AvValue.encode_text("Factor Value"), authorization=authorization)

    """
    aspects.insert(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        index=index,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def remove_factor(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove a factor from a facet within a fact

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    index : AvIndex
        Index of the factor to remove
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position for the removal
    parameter : AvParameter
        Additional parameter for the removal operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.insert_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="factor_key", value=AvValue.encode_text("Factor Value"), authorization=authorization)
    >>> factors.remove_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", index=1, authorization=authorization)

    """
    aspects.remove(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        index=index,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def replace_factor(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Replace an existing factor in a facet within a fact

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Key identifier for the factor within the facet
    value : AvValue
        New value to replace the existing factor value
    index : AvIndex
        Index of the factor to replace
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position for the replacement
    parameter : AvParameter
        Additional parameter for the replacement operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.insert_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="factor_key", value=AvValue.encode_text("Original Value"), authorization=authorization)
    >>> factors.replace_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="factor_key", value=AvValue.encode_text("Replaced Value"), authorization=authorization)

    """
    aspects.replace(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        index=index,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def find_factor(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Find the index of a factor with the specified value in a facet

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    value : AvValue
        Value to search for
    index : AvIndex
        Index to begin the search; front-to-back
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position for the search
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.insert_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="key1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> factors.insert_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="key2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> factors.find_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", value=AvValue.encode_text("Value 2"), authorization=authorization)
    2

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.insert_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="key1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> factors.find_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", value=AvValue.encode_text("Non-existent"), authorization=authorization)
    0

    """
    return aspects.find(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        value=value,
        index=index,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def include_factor(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Include a factor in a facet within a fact if it doesn't already exist

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Unique key identifier for the factor within the facet
    value : AvValue
        Value to be stored with the factor
    parameter : AvParameter
        Additional parameter for the include operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.include_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="new_key", value=AvValue.encode_text("New Factor"), authorization=authorization)

    """
    aspects.include(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_factor(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Exclude a factor from a facet within a fact if it exists

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Key identifier for the factor to exclude
    parameter : AvParameter
        Additional parameter for the exclude operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.include_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="remove_key", value=AvValue.encode_text("To be removed"), authorization=authorization)
    >>> factors.exclude_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="remove_key", authorization=authorization)

    """
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def set_factor(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Set the value of a factor in a facet within a fact

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Unique key identifier for the factor within the facet
    value : AvValue
        Value to be set for the factor
    parameter : AvParameter
        Additional parameter for the set operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="set_key", value=AvValue.encode_text("Set Value"), authorization=authorization)

    """
    aspects.set(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def get_factor(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a factor from a facet within a fact

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Key identifier for the factor
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="get_key", value=AvValue.encode_text("Retrieved Value"), authorization=authorization)
    >>> print(factors.get_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="get_key", authorization=authorization).decode_text())
    Retrieved Value

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> print(factors.get_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="nonexistent_key", authorization=authorization))
    {"NULL": ""}

    """
    return aspects.get(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        key=key,
        authorization=authorization,
    )


def clear_factor(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Clear a factor from a facet within a fact

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Key identifier for the factor to clear
    parameter : AvParameter
        Additional parameter for the clear operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="clear_key", value=AvValue.encode_text("To be cleared"), authorization=authorization)
    >>> factors.clear_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="clear_key", authorization=authorization)

    """
    aspects.clear(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def factor_count(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvCount:
    """Get the count of factors in a facet within a fact

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factors
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position for the count
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="key1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="key2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> print(factors.factor_count(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", authorization=authorization))
    2

    """
    return aspects.count(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def factor_member(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvBoolean:
    """Check if a factor is a member of a facet within a fact

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Key identifier for the factor
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position for the membership check
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="member_key", value=AvValue.encode_text("Member Value"), authorization=authorization)
    >>> print(factors.factor_member(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="member_key", authorization=authorization))
    True

    >>> print(factors.factor_member(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="nonexistent_key", authorization=authorization))
    False

    """
    return aspects.member(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        key=key,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def factor_name(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    """Get the name of the facet containing a factor at the specified position

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    key : AvKey
        Key identifier for the factor
    index : AvIndex
        Index position of the factor
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="test_facet", key="test_key", value=AvValue.encode_text("Test Value"), authorization=authorization)
    >>> print(factors.factor_name(entity=entity, attribute=AvAttribute.EXAMPLE, key="test_key", authorization=authorization))
    test_facet

    """
    return aspects.name(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        key=key,
        index=index,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def factor_key(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    """Get the key of a factor at the specified position in a facet

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    index : AvIndex
        Index position of the factor
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="indexed_key", value=AvValue.encode_text("Indexed Value"), authorization=authorization)
    >>> print(factors.factor_key(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", index=1, authorization=authorization))
    indexed_key

    """
    return aspects.key(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        index=index,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def factor_value(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a factor at the specified position in a facet

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Key identifier for the factor
    index : AvIndex
        Index position of the factor
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="value_key", value=AvValue.encode_text("Retrieved by Index"), authorization=authorization)
    >>> print(factors.factor_value(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", index=1, authorization=authorization).decode_text())
    Retrieved by Index

    """
    return aspects.value(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        key=key,
        index=index,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def factor_index(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Get the index position of a factor in a facet

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Key identifier for the factor
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="index_key", value=AvValue.encode_text("Find My Index"), authorization=authorization)
    >>> print(factors.factor_index(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="index_key", authorization=authorization))
    1

    """
    return aspects.index(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        key=key,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def factor_attribute(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    """Get the attribute of the fact containing a factor

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    name : AvName
        Name of the facet containing the factor
    key : AvKey
        Key identifier for the factor
    index : AvIndex
        Index position of the factor
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="attr_key", value=AvValue.encode_text("Attribute Test"), authorization=authorization)
    >>> print(factors.factor_attribute(entity=entity, name="example_facet", key="attr_key", authorization=authorization))
    EXAMPLE

    """
    return aspects.attribute(
        entity=entity,
        aspect=AvAspect.FACTOR,
        name=name,
        key=key,
        index=index,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def sort_factors(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Sort the factors within a facet

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factors to sort
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position for the sort
    parameter : AvParameter
        Additional parameter for the sort operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="z_key", value=AvValue.encode_text("Z Value"), authorization=authorization)
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="a_key", value=AvValue.encode_text("A Value"), authorization=authorization)
    >>> factors.sort_factors(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", authorization=authorization)

    """
    aspects.sort(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def erase_factors(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Erase all factors from a facet within a fact

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet containing the factors to erase
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset position for the erase
    parameter : AvParameter
        Additional parameter for the erase operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="key1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="key2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> factors.erase_factors(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", authorization=authorization)

    """
    aspects.erase(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        name=name,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_factors(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    """Return contents of factors in a facet as an Interchange(JSON)

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    instance : AvInstance
        Instance identifier for the fact
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="key1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> factors.set_factor(entity=entity, attribute=AvAttribute.EXAMPLE, name="example_facet", key="key2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> print(factors.retrieve_factors(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization))
    {"Factors":[["key1",{"TEXT":"Value 1"}],["key2",{"TEXT":"Value 2"}]]}

    """
    return aspects.retrieve(
        entity=entity,
        aspect=AvAspect.FACTOR,
        attribute=attribute,
        instance=instance,
        authorization=authorization,
    )

