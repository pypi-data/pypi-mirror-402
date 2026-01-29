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


def insert_facet(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Insert a facet at a specified index in a fact's facet list

    Facets are name/value pairs where each name, if not null, must be unique. 
    Facets provide a convenient way to represent multiple named instances of a fact attribute.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet to insert
    value : AvValue
        Value to be associated with the facet
    index : AvIndex
        Position at which to insert the facet
    instance : AvInstance
        Instance (fact index) containing the facet
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.insert_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="facet_1", value=AvValue.encode_text("First Facet"), index=1, authorization=authorization)
    >>> facets.insert_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="facet_2", value=AvValue.encode_text("Second Facet"), index=2, authorization=authorization)

    """
    aspects.insert(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        value=value,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def remove_facet(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove a facet at a specified index from a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    index : AvIndex
        Position of the facet to remove
    instance : AvInstance
        Instance (fact index) containing the facet
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.insert_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="facet_1", value=AvValue.encode_text("To be removed"), index=1, authorization=authorization)
    >>> facets.remove_facet(entity=entity, attribute=AvAttribute.EXAMPLE, index=1, authorization=authorization)

    """
    aspects.remove(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def replace_facet(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Replace a facet at a specified index in a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        New name for the facet
    value : AvValue
        New value for the facet
    index : AvIndex
        Position of the facet to replace
    instance : AvInstance
        Instance (fact index) containing the facet
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.insert_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="old_facet", value=AvValue.encode_text("Old Value"), index=1, authorization=authorization)
    >>> facets.replace_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="new_facet", value=AvValue.encode_text("New Value"), index=1, authorization=authorization)

    """
    aspects.replace(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        value=value,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def find_facet(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Find the index of a facet with the specified value in a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    value : AvValue
        Value to search for
    index : AvIndex
        Index to start searching from (front-to-back)
    instance : AvInstance
        Instance (fact index) containing the facet
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index of the facet with matching value, or 0 if not found

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.insert_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="facet_1", value=AvValue.encode_text("Find me"), authorization=authorization)
    >>> index = facets.find_facet(entity=entity, attribute=AvAttribute.EXAMPLE, value=AvValue.encode_text("Find me"), authorization=authorization)
    >>> print(index)
    1

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> index = facets.find_facet(entity=entity, attribute=AvAttribute.EXAMPLE, value=AvValue.encode_text("Not here"), authorization=authorization)
    >>> print(index)
    0

    """
    return aspects.find(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        value=value,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def include_facet(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Include a facet in a fact's facet list, ensuring unique names

    If a facet with the same name already exists, it will be updated with the new value.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet to include
    value : AvValue
        Value to be associated with the facet
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="unique_facet", value=AvValue.encode_text("Unique Value"), authorization=authorization)

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="update_me", value=AvValue.encode_text("Old Value"), authorization=authorization)
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="update_me", value=AvValue.encode_text("New Value"), authorization=authorization)

    """
    aspects.include(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_facet(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Exclude (remove) a facet by name from a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet to exclude
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="remove_me", value=AvValue.encode_text("To be removed"), authorization=authorization)
    >>> facets.exclude_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="remove_me", authorization=authorization)

    """
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        parameter=parameter,
        authorization=authorization,
    )


def set_facet(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Set the value of a facet by name in a fact's facet list

    If the facet doesn't exist, it will be created. If it exists, its value will be updated.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet to set
    value : AvValue
        Value to assign to the facet
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.set_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="my_facet", value=AvValue.encode_text("My Value"), authorization=authorization)

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.set_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="my_facet", value=AvValue.encode_text("First Value"), authorization=authorization)
    >>> facets.set_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="my_facet", value=AvValue.encode_text("Updated Value"), authorization=authorization)

    """
    aspects.set(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def get_facet(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a facet by name from a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet to retrieve
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        Value of the specified facet, or NULL_VALUE if not found

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.set_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="my_facet", value=AvValue.encode_text("Retrieved Value"), authorization=authorization)
    >>> print(facets.get_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="my_facet", authorization=authorization).decode_text())
    Retrieved Value

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> print(facets.get_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="nonexistent", authorization=authorization))
    {"NULL": ""}

    """
    return aspects.get(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        authorization=authorization,
    )


def clear_facet(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Clear the value of a facet by name, setting it to NULL_VALUE

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet to clear
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.set_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="clear_me", value=AvValue.encode_text("Will be cleared"), authorization=authorization)
    >>> facets.clear_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="clear_me", authorization=authorization)
    >>> print(facets.get_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="clear_me", authorization=authorization))
    {"NULL": ""}

    """
    aspects.clear(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        parameter=parameter,
        authorization=authorization,
    )


def facet_count(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvCount:
    """Get the count of facets in a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facets
    instance : AvInstance
        Instance (fact index) containing the facets
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvCount
        Number of facets in the specified fact

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="facet_1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="facet_2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> print(facets.facet_count(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization))
    2

    """
    return aspects.count(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        instance=instance,
        authorization=authorization,
    )


def facet_member(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvBoolean:
    """Check if a facet with the specified name exists in a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet to check for
    instance : AvInstance
        Instance (fact index) containing the facet
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvBoolean
        True if the facet exists, False otherwise

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="exists", value=AvValue.encode_text("I exist"), authorization=authorization)
    >>> print(facets.facet_member(entity=entity, attribute=AvAttribute.EXAMPLE, name="exists", authorization=authorization))
    True

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> print(facets.facet_member(entity=entity, attribute=AvAttribute.EXAMPLE, name="nonexistent", authorization=authorization))
    False

    """
    return aspects.member(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        instance=instance,
        authorization=authorization,
    )


def facet_name(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    """Get the name of a facet at a specified index in a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    index : AvIndex
        Index of the facet to get the name from
    instance : AvInstance
        Instance (fact index) containing the facet
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvName
        Name of the facet at the specified index

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="first_facet", value=AvValue.encode_text("Value"), authorization=authorization)
    >>> print(facets.facet_name(entity=entity, attribute=AvAttribute.EXAMPLE, index=1, authorization=authorization))
    first_facet

    """
    return aspects.name(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def facet_key(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    """Get the key of a facet by name or index in a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet to get the key from
    index : AvIndex
        Index of the facet to get the key from
    instance : AvInstance
        Instance (fact index) containing the facet
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvKey
        Key of the specified facet

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="keyed_facet", value=AvValue.encode_text("Value"), authorization=authorization)
    >>> print(facets.facet_key(entity=entity, attribute=AvAttribute.EXAMPLE, name="keyed_facet", authorization=authorization))
    keyed_facet

    """
    return aspects.key(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def facet_value(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a facet by name or index in a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet to get the value from
    index : AvIndex
        Index of the facet to get the value from
    instance : AvInstance
        Instance (fact index) containing the facet
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        Value of the specified facet

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="valued_facet", value=AvValue.encode_text("Retrieved Value"), authorization=authorization)
    >>> print(facets.facet_value(entity=entity, attribute=AvAttribute.EXAMPLE, name="valued_facet", authorization=authorization).decode_text())
    Retrieved Value

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="indexed_facet", value=AvValue.encode_text("Indexed Value"), authorization=authorization)
    >>> print(facets.facet_value(entity=entity, attribute=AvAttribute.EXAMPLE, index=1, authorization=authorization).decode_text())
    Indexed Value

    """
    return aspects.value(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def facet_index(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Get the index of a facet by name in a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facet
    name : AvName
        Name of the facet to get the index for
    instance : AvInstance
        Instance (fact index) containing the facet
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index of the specified facet, or 0 if not found

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="find_my_index", value=AvValue.encode_text("Value"), authorization=authorization)
    >>> print(facets.facet_index(entity=entity, attribute=AvAttribute.EXAMPLE, name="find_my_index", authorization=authorization))
    1

    """
    return aspects.index(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        name=name,
        instance=instance,
        authorization=authorization,
    )


def facet_attribute(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    """Get the attribute of the fact containing a facet by name or index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    name : AvName
        Name of the facet to get the attribute for
    index : AvIndex
        Index of the facet to get the attribute for
    instance : AvInstance
        Instance (fact index) containing the facet
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvAttribute
        Attribute of the fact containing the specified facet

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="my_facet", value=AvValue.encode_text("Value"), authorization=authorization)
    >>> print(facets.facet_attribute(entity=entity, name="my_facet", authorization=authorization))
    EXAMPLE

    """
    return aspects.attribute(
        entity=entity,
        aspect=AvAspect.FACET,
        name=name,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def sort_facets(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Sort facets in a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facets
    instance : AvInstance
        Instance (fact index) containing the facets
    parameter : AvParameter
        Sort parameter (e.g., sort order)
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="zebra", value=AvValue.encode_text("Last"), authorization=authorization)
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="alpha", value=AvValue.encode_text("First"), authorization=authorization)
    >>> facets.sort_facets(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization)

    """
    aspects.sort(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def erase_facets(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Erase all facets from a fact's facet list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facets
    instance : AvInstance
        Instance (fact index) containing the facets
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="facet_1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="facet_2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> facets.erase_facets(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization)
    >>> print(facets.facet_count(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization))
    0

    """
    aspects.erase(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_facets(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    """Return contents of a fact's facet list as an Interchange (JSON)

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the facets
    instance : AvInstance
        Instance (fact index) containing the facets
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvInterchange
        JSON representation of the facet list

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facets
    >>> authorization: AvAuthorization
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="facet_1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> facets.include_facet(entity=entity, attribute=AvAttribute.EXAMPLE, name="facet_2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> print(facets.retrieve_facets(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization))
    {"Facets":[["facet_1",{"TEXT":"Value 1"}],["facet_2",{"TEXT":"Value 2"}]]}

    """
    return aspects.retrieve(
        entity=entity,
        aspect=AvAspect.FACET,
        attribute=attribute,
        instance=instance,
        authorization=authorization,
    )