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


def insert_item(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Insert an item into a collection at a specific index

    Items are name/value pairs with an associated attribute from the Attribute taxonomy.

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    attribute : AvAttribute
        Attribute from the Attribute taxonomy to associate with this item
    name : AvName
        Name of the item (UTF-8 string, max 256 characters, non-empty)
    key : AvKey
        Optional key identifier for the item
    value : AvValue
        Avial value to store in the item
    index : AvIndex
        Position where the item should be inserted
    instance : AvInstance
        Collection instance identifier
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to modify the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection that supports items
    >>> authorization: AvAuthorization
    >>> items.insert_item(entity=entity, attribute=AvAttribute.DESCRIPTION, name="Item 1", key="key1", value=AvValue.encode_text("First item"), index=1, authorization=authorization)

    """
    aspects.insert(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def remove_item(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove an item from a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Key identifier of the item to remove
    index : AvIndex
        Index position of the item to remove
    instance : AvInstance
        Collection instance identifier
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to modify the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with existing items
    >>> authorization: AvAuthorization
    >>> items.remove_item(entity=entity, key="key1", authorization=authorization)
    >>> items.remove_item(entity=entity, index=1, authorization=authorization)

    """
    aspects.remove(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def replace_item(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Replace an existing item in a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    attribute : AvAttribute
        New attribute from the Attribute taxonomy to associate with this item
    name : AvName
        New name of the item (UTF-8 string, max 256 characters, non-empty)
    key : AvKey
        Key identifier of the item to replace
    value : AvValue
        New Avial value to store in the item
    index : AvIndex
        Index position of the item to replace
    instance : AvInstance
        Collection instance identifier
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to modify the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with existing items
    >>> authorization: AvAuthorization
    >>> items.replace_item(entity=entity, attribute=AvAttribute.TITLE, name="Updated Item", key="key1", value=AvValue.encode_text("Updated value"), authorization=authorization)

    """
    aspects.replace(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def find_item(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Find the index of an item in a collection based on search criteria

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    attribute : AvAttribute
        Attribute to search for
    name : AvName
        Name to search for
    key : AvKey
        Key identifier to search for
    index : AvIndex
        Starting index for the search
    instance : AvInstance
        Collection instance identifier
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index position of the found item, or NULL_INDEX if not found

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> index1 = items.find_item(entity=entity, key="key1", authorization=authorization)
    >>> index2 = items.find_item(entity=entity, name="Item Name", authorization=authorization)

    """
    return aspects.find(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=attribute,
        name=name,
        key=key,
        value=NULL_VALUE,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def include_item(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Include an item in a collection if it doesn't already exist

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    attribute : AvAttribute
        Attribute from the Attribute taxonomy to associate with this item
    name : AvName
        Name of the item (UTF-8 string, max 256 characters, non-empty)
    key : AvKey
        Key identifier for the item
    value : AvValue
        Avial value to store in the item
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to modify the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection
    >>> authorization: AvAuthorization
    >>> items.include_item(entity=entity, attribute=AvAttribute.CATEGORY, name="Category Item", key="cat1", value=AvValue.encode_text("Category value"), authorization=authorization)

    """
    aspects.include(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_item(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Exclude (remove) an item from a collection if it exists

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Key identifier of the item to exclude
    value : AvValue
        Value of the item to exclude
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to modify the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> items.exclude_item(entity=entity, key="cat1", authorization=authorization)
    >>> items.exclude_item(entity=entity, value=AvValue.encode_text("Specific value"), authorization=authorization)

    """
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def set_item(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Set an item in a collection, replacing if it exists or adding if it doesn't

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    attribute : AvAttribute
        Attribute from the Attribute taxonomy to associate with this item
    name : AvName
        Name of the item (UTF-8 string, max 256 characters, non-empty)
    key : AvKey
        Key identifier for the item
    value : AvValue
        Avial value to store in the item
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to modify the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection
    >>> authorization: AvAuthorization
    >>> items.set_item(entity=entity, attribute=AvAttribute.STATUS, name="Status Item", key="status1", value=AvValue.encode_text("Active"), authorization=authorization)

    """
    aspects.set(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def get_item(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of an item from a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Key identifier of the item to retrieve
    value : AvValue
        Value to search for
    index : AvIndex
        Index position of the item to retrieve
    instance : AvInstance
        Collection instance identifier
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        The value of the specified item

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> value1 = items.get_item(entity=entity, key="status1", authorization=authorization)
    >>> value2 = items.get_item(entity=entity, index=1, authorization=authorization)

    """
    return aspects.get(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        value=value,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def clear_item(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Clear (reset to null) an item's value in a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Key identifier of the item to clear
    value : AvValue
        Value to match for clearing
    index : AvIndex
        Index position of the item to clear
    instance : AvInstance
        Collection instance identifier
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to modify the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> items.clear_item(entity=entity, key="status1", authorization=authorization)
    >>> items.clear_item(entity=entity, index=1, authorization=authorization)

    """
    aspects.clear(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        value=value,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def item_count(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvCount:
    """Get the number of items in a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Optional key filter for counting specific items
    instance : AvInstance
        Collection instance identifier
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvCount
        Number of items in the collection

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> count = items.item_count(entity=entity, authorization=authorization)
    >>> print(f"Collection has {count} items")

    """
    return aspects.count(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def item_member(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> bool:
    """Check if an item exists in a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Key identifier to check for membership
    value : AvValue
        Value to check for membership
    instance : AvInstance
        Collection instance identifier
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    bool
        True if the item exists in the collection, False otherwise

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> exists = items.item_member(entity=entity, key="status1", authorization=authorization)

    """
    return aspects.member(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        value=value,
        instance=instance,
        authorization=authorization,
    )


def item_name(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    """Get the name of an item in a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Key identifier of the item
    index : AvIndex
        Index position of the item
    instance : AvInstance
        Collection instance identifier
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvName
        Name of the specified item

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> name1 = items.item_name(entity=entity, key="status1", authorization=authorization)
    >>> name2 = items.item_name(entity=entity, index=1, authorization=authorization)

    """
    return aspects.name(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def item_key(
    entity: AvEntity,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    """Get the key of an item at a specific index in a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    index : AvIndex
        Index position of the item
    instance : AvInstance
        Collection instance identifier
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvKey
        Key identifier of the item at the specified index

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> key = items.item_key(entity=entity, index=1, authorization=authorization)

    """
    return aspects.key(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def item_value(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of an item in a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Key identifier of the item
    index : AvIndex
        Index position of the item
    instance : AvInstance
        Collection instance identifier
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        Value of the specified item

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> value1 = items.item_value(entity=entity, key="status1", authorization=authorization)
    >>> value2 = items.item_value(entity=entity, index=1, authorization=authorization)

    """
    return aspects.value(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def item_index(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Get the index position of an item in a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Key identifier of the item
    instance : AvInstance
        Collection instance identifier
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index position of the specified item

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> index1 = items.item_index(entity=entity, key="status1", authorization=authorization)

    """
    return aspects.index(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def item_attribute(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    """Get the attribute associated with an item in a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Key identifier of the item
    value : AvValue
        Value of the item
    index : AvIndex
        Index position of the item
    instance : AvInstance
        Collection instance identifier
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvAttribute
        Attribute from the Attribute taxonomy associated with the item

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> attribute1 = items.item_attribute(entity=entity, key="status1", authorization=authorization)
    >>> attribute2 = items.item_attribute(entity=entity, index=1, authorization=authorization)

    """
    return aspects.attribute(
        entity=entity,
        aspect=AvAspect.ITEM,
        key=key,
        value=value,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def sort_items(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Sort items in a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Optional key filter for sorting specific items
    instance : AvInstance
        Collection instance identifier
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to modify the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> items.sort_items(entity=entity, authorization=authorization)

    """
    aspects.sort(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def erase_items(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Erase all items from a collection

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Optional key filter for erasing specific items
    instance : AvInstance
        Collection instance identifier
    parameter : AvParameter
        Defer writing to disk if set to anything but NULL_PARAMETER
    authorization : AvAuthorization
        An authorization that is able to modify the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> items.insert_item(entity=entity, attribute=AvAttribute.CATEGORY, name="Item 1", key="key1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> items.insert_item(entity=entity, attribute=AvAttribute.STATUS, name="Item 2", key="key2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> items.erase_items(entity=entity, authorization=authorization)

    """
    aspects.erase(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_items(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    """Retrieve items from a collection in AvInterchange format

    Parameters
    __________
    entity : AvEntity
        Target collection entity euid
    key : AvKey
        Optional key filter for retrieving specific items
    instance : AvInstance
        Collection instance identifier
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvInterchange
        Collection items in AvInterchange format

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is a collection with items
    >>> authorization: AvAuthorization
    >>> items.insert_item(entity=entity, attribute=AvAttribute.CATEGORY, name="Category Item", key="cat1", value=AvValue.encode_text("Category value"), authorization=authorization)
    >>> items.insert_item(entity=entity, attribute=AvAttribute.STATUS, name="Status Item", key="status1", value=AvValue.encode_text("Active"), authorization=authorization)
    >>> print(items.retrieve_items(entity=entity, authorization=authorization))

    """
    return aspects.retrieve(
        entity=entity,
        aspect=AvAspect.ITEM,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )