"""
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
This file is part of the Midwest Knowledge System Labs library, which helps developer use our Midwest Knowledge System Labs technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with Midwest Knowledge System Labs.
The Midwest Knowledge System Labs library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Midwest Knowledge System Labs library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Midwest Knowledge System Labs library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Midwest Knowledge System Labs library, you can contact us at support@midwksl.net.
"""


from avesterra.avial import *

from avesterra.avial import *
import avesterra.aspects as aspects



def insert_collection(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Insert a collection into an entity

    Collections are name/value pairs where names are UTF-8 strings (max 256 chars, non-empty)
    and values are Avial Values. Each collection has an associated Attribute from the
    Attribute taxonomy.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    name : AvName
        Name of the collection (UTF-8 string, max 256 characters, non-empty)
    key : AvKey
        Key identifier for the collection (UTF-8 string, max 256 characters, non-empty)
    value : AvValue
        Avial value to store in the collection
    instance : AvInstance
        Collection instance index for the collection
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.insert_collection(entity=entity, name="collection_name", value=AvValue.encode_text("Sample collection value"), authorization=authorization)

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.insert_collection(entity=entity, name="first_collection", key="key1", value=AvValue.encode_integer(100), authorization=authorization)
    >>> collections.insert_collection(entity=entity, name="second_collection", key="key2", value=AvValue.encode_text("Another value"), authorization=authorization)
    """
    aspects.insert(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def remove_collection(
    entity: AvEntity,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove a collection from an entity

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    instance : AvInstance
        Collection instance index to remove
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.remove_collection(entity=entity, instance=1, authorization=authorization)
    """
    aspects.remove(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def replace_collection(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Replace an existing collection in an entity

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    name : AvName
        New name for the collection
    key : AvKey
        Key identifier for the collection (UTF-8 string, max 256 characters, non-empty) to replace
    value : AvValue
        New Avial value for the collection
    instance : AvInstance
        Collection instance index to replace
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.replace_collection(entity=entity, key="existing_key", name="updated_name", value=AvValue.encode_text("Updated value"), authorization=authorization)

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.replace_collection(entity=entity, instance=1, name="new_name", value=AvValue.encode_integer(999), authorization=authorization)
    """
    aspects.replace(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        index=NULL_INDEX,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def find_collection(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Find the index of a collection based on name or value

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    name : AvName
        Name of the collection to find
    value : AvValue
        Value of the collection to find
    instance : AvInstance
        Collection instance to search within
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index of the found collection, or appropriate null value if not found

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> index = collections.find_collection(entity=entity, name="target_collection", authorization=authorization)
    >>> print(f"Found at index: {index}")

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> index = collections.find_collection(entity=entity, value=AvValue.encode_text("search_value"), authorization=authorization)
    """
    return aspects.find(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        name=name,
        value=value,
        instance=instance,
        authorization=authorization,
    )


def include_collection(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Include a collection, creating it if it doesn't exist

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    name : AvName
        Name of the collection
    key : AvKey
        Key identifier for the collection (UTF-8 string, max 256 characters, non-empty)
    value : AvValue
        Avial value for the collection
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.include_collection(entity=entity, name="ensure_collection", key="ensure_key", value=AvValue.encode_text("Ensured value"), authorization=authorization)
    """
    aspects.include(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_collection(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Exclude (remove) a collection by key

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Key identifier of the collection to exclude
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.exclude_collection(entity=entity, key="collection_to_remove", authorization=authorization)
    """
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def set_collection(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Set a collection, creating or updating as needed

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    name : AvName
        Name of the collection
    key : AvKey
        Key identifier for the collection (UTF-8 string, max 256 characters, non-empty)
    value : AvValue
        Avial value to set for the collection
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.set_collection(entity=entity, name="config_collection", key="config_key", value=AvValue.encode_text("Configuration value"), authorization=authorization)

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.set_collection(entity=entity, name="setting_1", key="key1", value=AvValue.encode_boolean(True), authorization=authorization)
    >>> collections.set_collection(entity=entity, name="setting_2", key="key2", value=AvValue.encode_real(3.14), authorization=authorization)
    """
    aspects.set(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def get_collection(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a collection by key

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Key identifier of the collection to retrieve
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        The Avial value stored in the collection

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> value = collections.get_collection(entity=entity, key="my_key", authorization=authorization)
    >>> print(f"Collection value: {AvValue.decode_text(value)}")
    """
    return aspects.get(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        key=key,
        authorization=authorization,
    )


def clear_collection(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Clear collections from an entity

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Specific key to clear, or NULL_KEY to clear all collections
    parameter : AvParameter
        Defer saving changes to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.clear_collection(entity=entity, key="specific_key", authorization=authorization)

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.clear_collection(entity=entity, authorization=authorization)
    """
    aspects.clear(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def collection_count(
    entity: AvEntity,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvCount:
    """Get the count of collections in an entity

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvCount
        Number of collections in the entity

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> count = collections.collection_count(entity=entity, authorization=authorization)
    >>> print(f"Entity has {count} collections")
    """
    return aspects.count(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        authorization=authorization,
    )


def collection_member(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> bool:
    """Check if a collection exists for the given key

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Key identifier to check for membership
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    bool
        True if the collection exists, False otherwise

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> exists = collections.collection_member(entity=entity, key="check_key", authorization=authorization)
    >>> if exists:
    ...     print("collection exists")
    ... else:
    ...     print("collection not found")
    """
    return aspects.member(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        key=key,
        authorization=authorization,
    )


def collection_name(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    """Get the name of a collection

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Key identifier of the collection
    instance : AvInstance
        Collection instance index
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvName
        Name of the collection

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> name = collections.collection_name(entity=entity, key="my_key", authorization=authorization)
    >>> print(f"Collection name: {name}")

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> name = collections.collection_name(entity=entity, instance=1, authorization=authorization)
    """
    return aspects.name(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def collection_key(
    entity: AvEntity,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    """Get the key of a collection by instance

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    instance : AvInstance
        Collection instance index
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvKey
        Key identifier of the collection

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> key = collections.collection_key(entity=entity, instance=1, authorization=authorization)
    >>> print(f"Collection key: {key}")
    """
    return aspects.key(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        instance=instance,
        authorization=authorization,
    )


def collection_value(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a collection

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Key identifier of the collection
    instance : AvInstance
        Collection instance index
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        Avial value stored in the collection

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> value = collections.collection_value(entity=entity, key="my_key", authorization=authorization)

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> value = collections.collection_value(entity=entity, instance=1, authorization=authorization)
    """
    return aspects.value(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def collection_index(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Get the index of a collection by key

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Key identifier of the collection
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index position of the collection

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> index = collections.collection_index(entity=entity, key="my_key", authorization=authorization)
    >>> print(f"Collection index: {index}")
    """
    return aspects.index(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        key=key,
        authorization=authorization,
    )


def collection_attribute(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    """Get the attribute associated with a collection

    Each collection has an associated Attribute from the Attribute taxonomy.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Key identifier of the collection
    instance : AvInstance
        Collection instance index
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvAttribute
        Attribute associated with the collection

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> attribute = collections.collection_attribute(entity=entity, key="my_key", authorization=authorization)

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> attribute = collections.collection_attribute(entity=entity, instance=1, authorization=authorization)
    """
    return aspects.attribute(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def sort_collections(
    entity: AvEntity,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Sort collections in an entity

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
    >>> collections.sort_collections(entity=entity, authorization=authorization)
    """
    aspects.sort(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        parameter=parameter,
        authorization=authorization,
    )


def erase_collections(
    entity: AvEntity,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Erase all collections from an entity

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
    >>> collections.erase_collections(entity=entity, authorization=authorization)
    """
    aspects.erase(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        attribute=NULL_ATTRIBUTE,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_collections(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    """Retrieve collections from an entity in AvInterchange format

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Specific key to retrieve, or NULL_KEY to retrieve all
    instance : AvInstance
        Specific instance to retrieve
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvInterchange
        Collection data in interchange format

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> collections.set_collection(entity=entity, name="collection1", key="key1", value=AvValue.encode_text("value1"), authorization=authorization)
    >>> collections.set_collection(entity=entity, name="collection2", key="key2", value=AvValue.encode_integer(42), authorization=authorization)
    >>> result = collections.retrieve_collections(entity=entity, authorization=authorization)
    >>> print(result)

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> result = collections.retrieve_collections(entity=entity, key="specific_key", authorization=authorization)
    """
    return aspects.retrieve(
        entity=entity,
        aspect=AvAspect.COLLECTION,
        key=key,
        instance=instance,
        authorization=authorization,
    )