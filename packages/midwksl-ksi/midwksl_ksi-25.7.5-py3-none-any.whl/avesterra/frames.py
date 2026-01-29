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


def insert_frame(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Insert a new frame into the tabular structure of a fact
    
    Frames work together with fields to provide a general-purpose means for building 
    tabular structures of arbitrary length (rows) and width (columns). This function
    inserts a new frame (row) into the tabular structure associated with a fact.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute where the frame will be inserted
    key : AvKey
        Unique identifier for the frame
    index : AvIndex
        Position where the frame should be inserted
    instance : AvInstance
        Instance identifier for the fact
    parameter : AvParameter
        Additional parameters for the insertion operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports facts
    >>> authorization: AvAuthorization
    >>> frames.insert_frame(entity=entity, attribute=AvAttribute.DATA, key="row_1", authorization=authorization)

    """
    aspects.insert(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        key=key,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def remove_frame(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove a frame from the tabular structure of a fact
    
    This function removes an existing frame (row) from the tabular structure 
    associated with a fact, effectively deleting the entire row.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute where the frame will be removed
    index : AvIndex
        Position of the frame to be removed
    instance : AvInstance
        Instance identifier for the fact
    parameter : AvParameter
        Additional parameters for the removal operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has existing frames
    >>> authorization: AvAuthorization
    >>> frames.remove_frame(entity=entity, attribute=AvAttribute.DATA, index=1, authorization=authorization)

    """
    aspects.remove(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def replace_frame(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Replace an existing frame in the tabular structure of a fact
    
    This function replaces an entire frame (row) in the tabular structure 
    associated with a fact with new data.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute where the frame will be replaced
    key : AvKey
        Unique identifier for the replacement frame
    index : AvIndex
        Position of the frame to be replaced
    instance : AvInstance
        Instance identifier for the fact
    parameter : AvParameter
        Additional parameters for the replacement operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has existing frames
    >>> authorization: AvAuthorization
    >>> frames.replace_frame(entity=entity, attribute=AvAttribute.DATA, index=1, key="new_row_1", authorization=authorization)

    """
    aspects.replace(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        key=key,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def find_frame(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Find the index of a frame that matches the specified criteria
    
    This function searches through the frames in a tabular structure to find 
    one that matches the given search criteria, returning its index position.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute where the search will take place
    name : AvName
        Column name to search within
    key : AvKey
        Unique identifier to search for
    value : AvValue
        Value to search for within the frames
    index : AvIndex
        Starting index for the search
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Offset from the starting index
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index of the matching frame, or 0 if not found

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames with data
    >>> authorization: AvAuthorization
    >>> frame_index = frames.find_frame(entity=entity, attribute=AvAttribute.DATA, value=AvValue.encode_text("search_value"), authorization=authorization)
    >>> print(frame_index)
    2

    """
    return aspects.find(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        index=index,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def include_frame(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Include a frame in the active set for processing
    
    This function marks a frame as included in the active set, making it 
    available for subsequent operations on the tabular structure.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frame
    key : AvKey
        Unique identifier of the frame to include
    parameter : AvParameter
        Additional parameters for the inclusion operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames
    >>> authorization: AvAuthorization
    >>> frames.include_frame(entity=entity, attribute=AvAttribute.DATA, key="row_1", authorization=authorization)

    """
    aspects.include(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_frame(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Exclude a frame from the active set for processing
    
    This function marks a frame as excluded from the active set, removing it 
    from subsequent operations on the tabular structure without deleting it.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frame
    key : AvKey
        Unique identifier of the frame to exclude
    parameter : AvParameter
        Additional parameters for the exclusion operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames
    >>> authorization: AvAuthorization
    >>> frames.exclude_frame(entity=entity, attribute=AvAttribute.DATA, key="row_1", authorization=authorization)

    """
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def set_frame(
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
    """Set a value in a specific cell of the frame table structure
    
    This function sets a value at a specific position within the tabular structure,
    allowing access to any cell using either row/column position or unique name and key.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frame
    name : AvName
        Column name for the cell
    key : AvKey
        Unique identifier for the frame (row)
    value : AvValue
        Value to set in the specified cell
    index : AvIndex
        Row index position
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Column offset position
    parameter : AvParameter
        Additional parameters for the set operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has a tabular structure
    >>> authorization: AvAuthorization
    >>> frames.set_frame(entity=entity, attribute=AvAttribute.DATA, name="column_1", key="row_1", value=AvValue.encode_text("cell_value"), authorization=authorization)

    """
    aspects.set(
        entity=entity,
        aspect=AvAspect.FRAME,
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


def get_frame(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get a value from a specific cell of the frame table structure
    
    This function retrieves a value from a specific position within the tabular structure,
    allowing access to any cell using either row/column position or unique name and key.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frame
    name : AvName
        Column name for the cell
    key : AvKey
        Unique identifier for the frame (row)
    index : AvIndex
        Row index position
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Column offset position
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        Value stored in the specified cell

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has a tabular structure with data
    >>> authorization: AvAuthorization
    >>> cell_value = frames.get_frame(entity=entity, attribute=AvAttribute.DATA, name="column_1", key="row_1", authorization=authorization)
    >>> print(AvValue.decode_text(cell_value))
    "cell_value"

    """
    return aspects.get(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        name=name,
        key=key,
        index=index,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def clear_frame(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Clear a value from a specific cell of the frame table structure
    
    This function clears (sets to null) a value at a specific position within 
    the tabular structure, allowing access to any cell using either row/column 
    position or unique name and key.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frame
    name : AvName
        Column name for the cell
    key : AvKey
        Unique identifier for the frame (row)
    index : AvIndex
        Row index position
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Column offset position
    parameter : AvParameter
        Additional parameters for the clear operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has a tabular structure with data
    >>> authorization: AvAuthorization
    >>> frames.clear_frame(entity=entity, attribute=AvAttribute.DATA, name="column_1", key="row_1", authorization=authorization)

    """
    aspects.clear(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        name=name,
        key=key,
        index=index,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def frame_count(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvCount:
    """Get the number of frames in the tabular structure
    
    This function returns the total count of frames (rows) in the tabular 
    structure associated with a fact.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frames
    instance : AvInstance
        Instance identifier for the fact
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvCount
        Number of frames in the tabular structure

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames
    >>> authorization: AvAuthorization
    >>> count = frames.frame_count(entity=entity, attribute=AvAttribute.DATA, authorization=authorization)
    >>> print(count)
    5

    """
    return aspects.count(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        instance=instance,
        authorization=authorization,
    )


def frame_member(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvBoolean:
    """Check if a frame with the specified key exists in the tabular structure
    
    This function determines whether a frame with the given key exists in 
    the tabular structure associated with a fact.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frames
    key : AvKey
        Unique identifier to check for
    instance : AvInstance
        Instance identifier for the fact
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvBoolean
        True if the frame exists, False otherwise

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames
    >>> authorization: AvAuthorization
    >>> exists = frames.frame_member(entity=entity, attribute=AvAttribute.DATA, key="row_1", authorization=authorization)
    >>> print(exists)
    True

    """
    return aspects.member(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def frame_name(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    """Get the name of a column in the frame table structure
    
    This function returns the name of a column at the specified offset 
    position in the tabular structure.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frames
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Column offset position
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvName
        Name of the column at the specified position

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has a tabular structure
    >>> authorization: AvAuthorization
    >>> column_name = frames.frame_name(entity=entity, attribute=AvAttribute.DATA, offset=1, authorization=authorization)
    >>> print(column_name)
    "column_1"

    """
    return aspects.name(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def frame_key(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    """Get the key of a frame at the specified index position
    
    This function returns the unique key identifier of a frame (row) at 
    the specified index position in the tabular structure.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frames
    index : AvIndex
        Row index position
    instance : AvInstance
        Instance identifier for the fact
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvKey
        Unique key identifier of the frame at the specified position

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames
    >>> authorization: AvAuthorization
    >>> row_key = frames.frame_key(entity=entity, attribute=AvAttribute.DATA, index=1, authorization=authorization)
    >>> print(row_key)
    "row_1"

    """
    return aspects.key(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def frame_value(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get a value from the frame table structure using various addressing methods
    
    This function retrieves a value from the tabular structure using flexible 
    addressing options including name/key, index/offset, or other combinations.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frames
    name : AvName
        Column name for addressing
    key : AvKey
        Row key for addressing
    index : AvIndex
        Row index for addressing
    instance : AvInstance
        Instance identifier for the fact
    offset : AvOffset
        Column offset for addressing
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        Value at the specified cell position

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has a tabular structure
    >>> authorization: AvAuthorization
    >>> value = frames.frame_value(entity=entity, attribute=AvAttribute.DATA, name="column_1", key="row_1", authorization=authorization)
    >>> print(AvValue.decode_text(value))
    "cell_data"

    """
    return aspects.value(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        name=name,
        key=key,
        index=index,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def frame_index(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Get the index position of a frame with the specified key
    
    This function returns the index position of a frame (row) that has 
    the specified key identifier in the tabular structure.

    Parameters
    __________
    entity : AvEntity
    attribute : AvAttribute
        Fact attribute containing the frames
    key : AvKey
        Unique key identifier to search for
    instance : AvInstance
        Instance identifier for the fact
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index position of the frame with the specified key

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames
    >>> authorization: AvAuthorization
    >>> index = frames.frame_index(entity=entity, attribute=AvAttribute.DATA, key="row_1", authorization=authorization)
    >>> print(index)
    1

    """
    return aspects.index(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def frame_attribute(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    """Get the attribute associated with a frame
    
    This function returns the attribute identifier associated with a frame 
    at the specified position in the tabular structure.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Unique key identifier of the frame
    index : AvIndex
        Index position of the frame
    instance : AvInstance
        Instance identifier for the fact
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvAttribute
        Attribute associated with the specified frame

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames
    >>> authorization: AvAuthorization
    >>> attr = frames.frame_attribute(entity=entity, key="row_1", authorization=authorization)
    >>> print(attr)
    AvAttribute.DATA

    """
    return aspects.attribute(
        entity=entity,
        aspect=AvAspect.FRAME,
        key=key,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def sort_frames(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Sort frames in the tabular structure
    
    This function sorts the frames (rows) in the tabular structure according 
    to the specified sorting criteria.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frames to sort
    instance : AvInstance
        Instance identifier for the fact
    parameter : AvParameter
        Sorting parameters and criteria
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames
    >>> authorization: AvAuthorization
    >>> frames.sort_frames(entity=entity, attribute=AvAttribute.DATA, authorization=authorization)

    """
    aspects.sort(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def erase_frames(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Erase all frames from the tabular structure
    
    This function removes all frames (rows) from the tabular structure 
    associated with a fact, effectively clearing the entire table.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frames to erase
    instance : AvInstance
        Instance identifier for the fact
    parameter : AvParameter
        Additional parameters for the erase operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames
    >>> authorization: AvAuthorization
    >>> frames.erase_frames(entity=entity, attribute=AvAttribute.DATA, authorization=authorization)

    """
    aspects.erase(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_frames(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    """Retrieve all frames from the tabular structure in AvInterchange format
    
    This function retrieves all frames (rows) from the tabular structure 
    associated with a fact and returns them in AvInterchange (JSON) format.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Fact attribute containing the frames to retrieve
    instance : AvInstance
        Instance identifier for the fact
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvInterchange
        All frames in JSON format representing the tabular structure

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has frames with data
    >>> authorization: AvAuthorization
    >>> frames_data = frames.retrieve_frames(entity=entity, attribute=AvAttribute.DATA, authorization=authorization)
    >>> print(frames_data)
    {"Frames":[["row_1",{"TEXT":"value1"},{"TEXT":"value2"}],["row_2",{"TEXT":"value3"},{"TEXT":"value4"}]]}

    """
    return aspects.retrieve(
        entity=entity,
        aspect=AvAspect.FRAME,
        attribute=attribute,
        instance=instance,
        authorization=authorization,
    )