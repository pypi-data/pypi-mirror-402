""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""



import avesterra.properties as properties
from avesterra.properties import *
from avesterra.predefined import folder_outlet
import avesterra.aspects as aspects


AvFolder = AvEntity


def create_folder(
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    mode: AvMode = AvMode.NULL,
    outlet: AvEntity = NULL_ENTITY,
    server: AvEntity = NULL_ENTITY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvFolder:
    """Create a new folder in the AvesTerra knowledge space
    
    Folders are entities that are connected to the Folder Adapter Outlet (<0|0|12>) 
    at Presence level 0 and have been allocated as Folders in the Folder Adapter. 
    Folders are used to store "stuff" and are able to represent both tabular and 
    object-oriented objects through their support for Attributions, Facts, and 
    Properties. This flexibility makes folders suitable for rich representations 
    while maintaining efficient storage and retrieval capabilities.

    Parameters
    __________
    name : AvName, optional
        The name to assign to the new folder
    key : AvKey, optional
        Unique identifier key for the folder
    mode : AvMode, optional
        Operational mode for the folder
    outlet : AvEntity, optional
        Custom outlet to use instead of the default folder_outlet
    server : AvEntity, optional
        Server entity to associate with the folder
    authorization : AvAuthorization, optional
        Authorization required to create the folder; must be on both folder and folder adapter outlet

    Returns
    _______
    AvFolder
        The newly created folder entity

    Examples
    ________

    >>> 
    >>> authorization: AvAuthorization
    >>> folder = folders.create_folder(name="MyFolder", authorization=authorization)
    >>> print(f"Created folder: {folder}")

    Notes
    _____
    Folders support multiple AvesTerra constructs:
    - Attributions: Simple attribute/value pairs with optional traits
    - Facts: Complex semantic structures with facets, features, fields, and frames
    - Properties: Name/value pairs with optional keys and annotations
    
    While folders are flexible, they shouldn't be used as a 'catch-all' adapter
    as this would create performance bottlenecks. Use folders when you explicitly
    need rich representation capabilities and tabular/list-based representations.
    """
    adapter = folder_outlet if outlet == NULL_ENTITY else outlet
    value = invoke_entity(
        entity=adapter,
        method=AvMethod.CREATE,
        name=name,
        key=key,
        context=AvContext.AVESTERRA,
        category=AvCategory.AVESTERRA,
        klass=AvClass.FILE,
        mode=mode,
        ancillary=server,
        authorization=authorization,
    )
    return value.decode_entity()


def delete_folder(
    folder: AvFolder, authorization: AvAuthorization = NULL_AUTHORIZATION
):
    """Delete a folder from the AvesTerra knowledge space
    
    Permanently removes the specified folder and all associated data including
    attributions, facts, properties, and any stored content. This operation
    cannot be undone.

    Parameters
    __________
    folder : AvFolder
        The folder to be deleted
    authorization : AvAuthorization, optional
        Authorization required to delete the folder; must be on both folder and folder adapter outlet

    Examples
    ________

    >>> 
    >>> folder: AvFolder  # Assume this is a valid folder
    >>> authorization: AvAuthorization
    >>> folders.delete_folder(folder=folder, authorization=authorization)
    >>> print("Folder has been deleted")

    Notes
    _____
    Deleting a folder will remove all associated constructs:
    - All attributions and their traits
    - All facts with their facets, features, fields, and frames
    - All properties and their annotations
    
    Ensure proper authorization is provided as this operation requires
    appropriate permissions to delete the folder and its contents.
    """
    invoke_entity(entity=folder, method=AvMethod.DELETE, authorization=authorization)


def insert_folder(
    folder: AvFolder,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Insert a property into the folder's property list
    
    Adds a new property to the folder at the specified index or at the end
    if no index is specified. Properties are name/value pairs with optional
    keys that can be used to organize and retrieve folder contents.

    Parameters
    __________
    folder : AvFolder
        The folder to insert the property into
    name : AvName, optional
        The name of the property being inserted
    key : AvKey, optional
        Unique identifier key for the property
    value : AvValue, optional
        The value to be stored in the property
    index : AvIndex, optional
        Position in the property list where the property should be inserted
    parameter : AvParameter, optional
        Additional parameters for the insertion operation
    authorization : AvAuthorization, optional
        Authorization required to modify the folder; must be on both folder and folder adapter outlet

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> folders.insert_folder(
    ...     folder=folder,
    ...     name="document1",
    ...     key="doc1",
    ...     value=AvValue.encode_text("Important document"),
    ...     authorization=authorization
    ... )
    """
    properties.insert_property(
        entity=folder,
        name=name,
        key=key,
        value=value,
        index=index,
        parameter=parameter,
        authorization=authorization,
    )


def remove_folder(
    folder: AvFolder,
    index: AvIndex = NULL_INDEX,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove a property from the folder's property list
    
    Removes the property at the specified index from the folder's property list.
    This operation permanently deletes the property and cannot be undone.

    Parameters
    __________
    folder : AvFolder
        The folder to remove the property from
    index : AvIndex, optional
        Position of the property to be removed
    parameter : AvParameter, optional
        Additional parameters for the removal operation
    authorization : AvAuthorization, optional
        Authorization required to modify the folder; must be on both folder and folder adapter outlet

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> folders.remove_folder(folder=folder, index=1, authorization=authorization)

    >>> 
    >>> folders.remove_folder(
    ...     folder=folder,
    ...     index=3,
    ...     parameter=AVESTERRA_PARAMETER.,
    ...     authorization=authorization
    ... )
    """
    properties.remove_property(
        entity=folder, index=index, parameter=parameter, authorization=authorization
    )


def replace_folder(
    folder: AvFolder,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Replace a property in the folder's property list
    
    Replaces the property at the specified index with new name, key, and value.
    This operation modifies the existing property in place via an index.

    Parameters
    __________
    folder : AvFolder
        The folder containing the property to be replaced
    name : AvName, optional
        The new name for the property
    key : AvKey, optional
        The new key for the property
    value : AvValue, optional
        The new value for the property
    index : AvIndex, optional
        Position of the property to be replaced
    parameter : AvParameter, optional
        Additional parameters for the replacement operation
    authorization : AvAuthorization, optional
        Authorization required to modify the folder; must be on both folder and folder adapter outlet

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> folders.replace_folder(
    ...     folder=folder,
    ...     name="updated_document",
    ...     key="updated_doc",
    ...     value=AvValue.encode_text("Updated content"),
    ...     index=2,
    ...     authorization=authorization
    ... )
    """
    properties.replace_property(
        entity=folder,
        name=name,
        key=key,
        value=value,
        index=index,
        parameter=parameter,
        authorization=authorization,
    )


def find_item(
    folder: AvFolder,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Find the index of a property in the folder by its value
    
    Searches the folder's property list for the first property matching the
    specified value and returns its index position.

    Parameters
    __________
    folder : AvFolder
        The folder to search within
    value : AvValue, optional
        The value to search for
    index : AvIndex, optional
        Starting index for the search
    authorization : AvAuthorization, optional
        Authorization required to read from the folder

    Returns
    _______
    AvIndex
        The index of the first matching property, or NULL_INDEX if not found

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> target_value = AvValue.encode_text("Important document")
    >>> index = folders.find_item(
    ...     folder=folder,
    ...     value=target_value,
    ...     authorization=authorization
    ... )
    >>> print(f"Found item at index: {index}")
    """
    return properties.find_property(
        entity=folder, value=value, index=index, authorization=authorization
    )


def lookup_item(
    folder: AvFolder,
    key: AvKey = NULL_KEY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Retrieve the value of a property in the folder by its key
    
    Looks up a property in the folder using its unique key and returns
    the associated value.

    Parameters
    __________
    folder : AvFolder
        The folder to search within
    key : AvKey, optional
        The key of the property to retrieve
    authorization : AvAuthorization, optional
        Authorization required to read from the folder

    Returns
    _______
    AvValue
        The value associated with the specified key

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> value = folders.lookup_item(
    ...     folder=folder,
    ...     key="document1",
    ...     authorization=authorization
    ... )
    >>> print(f"Retrieved value: {value}")

    >>> 
    >>> try:
    ...     value = folders.lookup_item(folder=folder, key="nonexistent", authorization=authorization)
    ...     print(f"Found: {value}")
    ... except Exception as e:
    ...     print(f"Key not found: {e}")
    """
    return properties.property_value(
        entity=folder, key=key, authorization=authorization
    )


def item_count(folder: AvFolder, authorization: AvAuthorization = NULL_AUTHORIZATION):
    """Get the number of properties in the folder
    
    Returns the total count of properties stored in the folder's property list.

    Parameters
    __________
    folder : AvFolder
        The folder to count properties for
    authorization : AvAuthorization, optional
        Authorization required to read from the folder

    Returns
    _______
    int
        The number of properties in the folder

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> count = folders.item_count(folder=folder, authorization=authorization)
    >>> print(f"Folder contains {count} properties")

    >>> 
    >>> if folders.item_count(folder, authorization) == 0:
    ...     print("Folder is empty")
    ... else:
    ...     print("Folder contains items")
    """
    return properties.property_count(entity=folder, authorization=authorization)


def item_member(
    folder: AvFolder, key: AvKey, authorization: AvAuthorization = NULL_AUTHORIZATION
):
    """Check if a property with the specified key exists in the folder
    
    Determines whether a property with the given key is present in the
    folder's property list.

    Parameters
    __________
    folder : AvFolder
        The folder to check
    key : AvKey
        The key to search for
    authorization : AvAuthorization, optional
        Authorization required to read from the folder

    Returns
    _______
    bool
        True if the key exists in the folder, False otherwise

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> if folders.item_member(folder=folder, key="document1", authorization=authorization):
    ...     print("Document1 exists in folder")
    ... else:
    ...     print("Document1 not found")

    >>> 
    >>> key = "important_file"
    >>> if folders.item_member(folder, key, authorization):
    ...     value = folders.lookup_item(folder, key, authorization)
    ...     print(f"Found: {value}")
    """
    return properties.property_member(
        entity=folder, key=key, authorization=authorization
    )


def item_name(
    folder: AvFolder,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    """Get the name of a property at the specified index
    
    Retrieves the name of the property located at the given index position
    in the folder's property list.

    Parameters
    __________
    folder : AvFolder
        The folder to read from
    index : AvIndex, optional
        The index position of the property
    authorization : AvAuthorization, optional
        Authorization required to read from the folder

    Returns
    _______
    AvName
        The name of the property at the specified index

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> name = folders.item_name(folder=folder, index=1, authorization=authorization)
    >>> print(f"Property name: {name}")

    >>> 
    >>> count = folders.item_count(folder, authorization)
    >>> for i in range(1, count + 1):
    ...     name = folders.item_name(folder, i, authorization)
    ...     print(f"Property {i}: {name}")
    """
    return properties.property_name(
        entity=folder, index=index, authorization=authorization
    )


def item_key(
    folder: AvFolder,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    """Get the key of a property at the specified index
    
    Retrieves the key of the property located at the given index position
    in the folder's property list.

    Parameters
    __________
    folder : AvFolder
        The folder to read from
    index : AvIndex, optional
        The index position of the property
    authorization : AvAuthorization, optional
        Authorization required to read from the folder

    Returns
    _______
    AvKey
        The key of the property at the specified index

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> key = folders.item_key(folder=folder, index=2, authorization=authorization)
    >>> print(f"Property key: {key}")

    >>> 
    >>> count = folders.item_count(folder, authorization)
    >>> keys = [folders.item_key(folder, i, authorization) for i in range(1, count + 1)]
    >>> print(f"All keys: {keys}")
    """
    return properties.property_key(
        entity=folder, index=index, authorization=authorization
    )


def item_value(
    folder: AvFolder,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a property at the specified index
    
    Retrieves the value of the property located at the given index position
    in the folder's property list.

    Parameters
    __________
    folder : AvFolder
        The folder to read from
    index : AvIndex, optional
        The index position of the property
    authorization : AvAuthorization, optional
        Authorization required to read from the folder

    Returns
    _______
    AvValue
        The value of the property at the specified index

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> value = folders.item_value(folder=folder, index=1, authorization=authorization)
    >>> print(f"Property value: {value}")

    >>> 
    >>> count = folders.item_count(folder, authorization)
    >>> values = [folders.item_value(folder, i, authorization) for i in range(1, count + 1)]
    >>> print(f"All values: {values}")
    """
    return properties.property_value(
        entity=folder, index=index, authorization=authorization
    )


def save_folder(folder: AvFolder, authorization: AvAuthorization = NULL_AUTHORIZATION):
    """Save the folder and persist all changes to storage
    
    Commits all pending changes to the folder, including modifications to
    properties, attributions, and facts, ensuring data persistence.

    Parameters
    __________
    folder : AvFolder
        The folder to save
    authorization : AvAuthorization, optional
        Authorization required to save the folder

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> folders.save_folder(folder=folder, authorization=authorization)
    >>> print("Folder saved successfully")

    >>> 
    >>> folders.insert_folder(folder, name="item1", value=AvValue.encode_text("value1"), authorization=authorization)
    >>> folders.insert_folder(folder, name="item2", value=AvValue.encode_text("value2"), authorization=authorization)
    >>> folders.save_folder(folder, authorization)
    >>> print("Batch operations saved")
    """
    save_entity(entity=folder, authorization=authorization)


def erase_registry(
    folder: AvFolder, authorization: AvAuthorization = NULL_AUTHORIZATION
):
    """Erase all properties from the folder
    
    Removes all properties from the folder's property list, effectively
    clearing all stored content while preserving the folder entity itself.

    Parameters
    __________
    folder : AvFolder
        The folder to erase properties from
    authorization : AvAuthorization, optional
        Authorization required to modify the folder

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> folders.erase_registry(folder=folder, authorization=authorization)
    >>> print("All properties erased from folder")

    >>> 
    >>> folders.erase_registry(folder, authorization)
    >>> count = folders.item_count(folder, authorization)
    >>> print(f"Folder now contains {count} properties")
    """
    properties.erase_properties(entity=folder, authorization=authorization)


def sort_registry(
    folder: AvFolder, authorization: AvAuthorization = NULL_AUTHORIZATION
):
    """Sort the properties in the folder
    
    Reorganizes the folder's property list according to the default sorting
    criteria, typically by key or name for improved organization and retrieval.

    Parameters
    __________
    folder : AvFolder
        The folder to sort properties for
    authorization : AvAuthorization, optional
        Authorization required to modify the folder

    Examples
    ________

    >>> 
    >>> folder: AvFolder
    >>> authorization: AvAuthorization
    >>> folders.sort_registry(folder=folder, authorization=authorization)
    >>> print("Folder properties sorted")

    >>> 
    >>> folders.sort_registry(folder, authorization)
    >>> folders.save_folder(folder, authorization)
    >>> print("Folder sorted and saved")
    """
    properties.sort_properties(entity=folder, authorization=authorization)