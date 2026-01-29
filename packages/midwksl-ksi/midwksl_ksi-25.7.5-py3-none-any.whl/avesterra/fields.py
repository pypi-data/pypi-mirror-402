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


def insert_field(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Insert a field at the specified index in the field list
    
    Fields serve as column guides for frames, providing tabular structure. 
    Adding a field results in corresponding values being inserted into every frame.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the field to be inserted
    name : AvName
        Name of the field to be inserted
    value : AvValue
        Value of the field to be inserted (serves as default for new frame columns)
    index : AvIndex
        Index position where the field will be inserted
    instance : AvInstance
        Instance where the field will be inserted
    parameter : AvParameter
        Additional parameter for the insertion operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports fields
    >>> authorization: AvAuthorization
    >>> fields.insert_field(entity=entity, attribute=AvAttribute.NAME, name="Column1", value=AvValue.encode_text("Default"), index=1, authorization=authorization)
    >>> fields.insert_field(entity=entity, attribute=AvAttribute.TYPE, name="Column2", value=AvValue.encode_integer(0), index=2, authorization=authorization)

    """
    aspects.insert(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        value=value,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def remove_field(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove a field at the specified index from the field list
    
    Removing a field results in corresponding values being removed from every frame
    at the corresponding column position.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the field to be removed
    index : AvIndex
        Index position of the field to be removed
    instance : AvInstance
        Instance from which the field will be removed
    parameter : AvParameter
        Additional parameter for the removal operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has existing fields
    >>> authorization: AvAuthorization
    >>> fields.remove_field(entity=entity, index=2, authorization=authorization)
    >>> fields.remove_field(entity=entity, attribute=AvAttribute.NAME, index=1, authorization=authorization)

    """
    aspects.remove(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def replace_field(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Replace a field at the specified index with new field data

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        New attribute for the field
    name : AvName
        New name for the field
    value : AvValue
        New value for the field
    index : AvIndex
        Index position of the field to be replaced
    instance : AvInstance
        Instance where the field will be replaced
    parameter : AvParameter
        Additional parameter for the replacement operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has existing fields
    >>> authorization: AvAuthorization
    >>> fields.replace_field(entity=entity, attribute=AvAttribute.DESCRIPTION, name="NewColumn", value=AvValue.encode_text("NewDefault"), index=1, authorization=authorization)

    """
    aspects.replace(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        value=value,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def find_field(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Find the index of the field which has the specified value
    
    Searches through the field list to locate a field with the matching value.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the field to search for
    value : AvValue
        Value to lookup in the field list
    index : AvIndex
        Index position to begin the search from (front-to-back)
    instance : AvInstance
        Instance in which the field search will take place
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index of the field with matching value, or 0 if not found

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity has fields with values
    >>> authorization: AvAuthorization
    >>> fields.insert_field(entity=entity, name="Field1", value=AvValue.encode_text("SearchValue"), authorization=authorization)
    >>> fields.insert_field(entity=entity, name="Field2", value=AvValue.encode_text("OtherValue"), authorization=authorization)
    >>> fields.find_field(entity=entity, value=AvValue.encode_text("SearchValue"), authorization=authorization)
    1

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.find_field(entity=entity, value=AvValue.encode_text("NonExistentValue"), authorization=authorization)
    0

    """
    return aspects.find(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        value=value,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def include_field(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Include a field in the field collection if it doesn't already exist
    
    This operation ensures the field is present without creating duplicates.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the field to be included
    name : AvName
        Name of the field to be included
    value : AvValue
        Value of the field to be included
    parameter : AvParameter
        Additional parameter for the inclusion operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.include_field(entity=entity, attribute=AvAttribute.NAME, name="UniqueField", value=AvValue.encode_text("UniqueValue"), authorization=authorization)

    """
    aspects.include(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_field(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Exclude a field from the field collection if it exists
    
    This operation removes the field if present, but doesn't fail if absent.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the field to be excluded
    name : AvName
        Name of the field to be excluded
    parameter : AvParameter
        Additional parameter for the exclusion operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.exclude_field(entity=entity, name="FieldToRemove", authorization=authorization)

    """
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        parameter=parameter,
        authorization=authorization,
    )


def set_field(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Set the value of a field, creating it if it doesn't exist
    
    This operation will either update an existing field or create a new one.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the field to be set
    name : AvName
        Name of the field to be set
    value : AvValue
        Value to be assigned to the field
    parameter : AvParameter
        Additional parameter for the set operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.set_field(entity=entity, attribute=AvAttribute.TYPE, name="StatusField", value=AvValue.encode_text("Active"), authorization=authorization)
    >>> fields.set_field(entity=entity, name="CountField", value=AvValue.encode_integer(42), authorization=authorization)

    """
    aspects.set(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def get_field(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a field by its attribute and/or name

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the field to retrieve
    name : AvName
        Name of the field to retrieve
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        Value of the field, or NULL value if field doesn't exist

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.set_field(entity=entity, name="TestField", value=AvValue.encode_text("TestValue"), authorization=authorization)
    >>> print(fields.get_field(entity=entity, name="TestField", authorization=authorization).decode_text())
    TestValue

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> print(fields.get_field(entity=entity, name="NonExistentField", authorization=authorization))
    {"NULL": ""}

    """
    return aspects.get(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        authorization=authorization,
    )


def clear_field(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Clear the value of a field, setting it to NULL
    
    This operation resets the field value without removing the field itself.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the field to be cleared
    name : AvName
        Name of the field to be cleared
    parameter : AvParameter
        Additional parameter for the clear operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.set_field(entity=entity, name="FieldToClear", value=AvValue.encode_text("SomeValue"), authorization=authorization)
    >>> fields.clear_field(entity=entity, name="FieldToClear", authorization=authorization)
    >>> print(fields.get_field(entity=entity, name="FieldToClear", authorization=authorization))
    {"NULL": ""}

    """
    aspects.clear(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        parameter=parameter,
        authorization=authorization,
    )


def field_count(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvCount:
    """Get the count of fields in the field collection

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute filter for counting fields
    instance : AvInstance
        Instance for which to count fields
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvCount
        Number of fields in the collection

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.set_field(entity=entity, name="Field1", value=AvValue.encode_text("Value1"), authorization=authorization)
    >>> fields.set_field(entity=entity, name="Field2", value=AvValue.encode_text("Value2"), authorization=authorization)
    >>> fields.field_count(entity=entity, authorization=authorization)
    2

    """
    return aspects.count(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        instance=instance,
        authorization=authorization,
    )


def field_member(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvBoolean:
    """Check if a field with the specified name exists in the field collection

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the field to check for membership
    name : AvName
        Name of the field to check for existence
    instance : AvInstance
        Instance in which to check for field membership
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvBoolean
        True if the field exists, False otherwise

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.set_field(entity=entity, name="ExistingField", value=AvValue.encode_text("Value"), authorization=authorization)
    >>> fields.field_member(entity=entity, name="ExistingField", authorization=authorization)
    True

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.field_member(entity=entity, name="NonExistentField", authorization=authorization)
    False

    """
    return aspects.member(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        instance=instance,
        authorization=authorization,
    )


def field_name(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    """Get the name of a field at the specified index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute filter for the field
    index : AvIndex
        Index position of the field whose name to retrieve
    instance : AvInstance
        Instance from which to get the field name
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvName
        Name of the field at the specified index

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.insert_field(entity=entity, name="FirstField", value=AvValue.encode_text("Value1"), index=1, authorization=authorization)
    >>> fields.insert_field(entity=entity, name="SecondField", value=AvValue.encode_text("Value2"), index=2, authorization=authorization)
    >>> fields.field_name(entity=entity, index=1, authorization=authorization)
    "FirstField"

    """
    return aspects.name(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def field_key(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    """Get the key of a field by name or index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute filter for the field
    name : AvName
        Name of the field whose key to retrieve
    index : AvIndex
        Index position of the field whose key to retrieve
    instance : AvInstance
        Instance from which to get the field key
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvKey
        Key of the specified field

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.set_field(entity=entity, name="KeyedField", value=AvValue.encode_text("Value"), authorization=authorization)
    >>> fields.field_key(entity=entity, name="KeyedField", authorization=authorization)

    """
    return aspects.key(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def field_value(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a field by name or index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute filter for the field
    name : AvName
        Name of the field whose value to retrieve
    index : AvIndex
        Index position of the field whose value to retrieve
    instance : AvInstance
        Instance from which to get the field value
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvValue
        Value of the specified field

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.set_field(entity=entity, name="ValueField", value=AvValue.encode_text("TestValue"), authorization=authorization)
    >>> print(fields.field_value(entity=entity, name="ValueField", authorization=authorization).decode_text())
    TestValue

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.insert_field(entity=entity, name="IndexedField", value=AvValue.encode_integer(123), index=1, authorization=authorization)
    >>> print(fields.field_value(entity=entity, index=1, authorization=authorization).decode_integer())
    123

    """
    return aspects.value(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def field_index(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Get the index position of a field by its name

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute filter for the field
    name : AvName
        Name of the field whose index to retrieve
    instance : AvInstance
        Instance in which to find the field index
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvIndex
        Index position of the named field

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.insert_field(entity=entity, name="FirstField", value=AvValue.encode_text("Value1"), index=1, authorization=authorization)
    >>> fields.insert_field(entity=entity, name="SecondField", value=AvValue.encode_text("Value2"), index=2, authorization=authorization)
    >>> fields.field_index(entity=entity, name="SecondField", authorization=authorization)
    2

    """
    return aspects.index(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        name=name,
        instance=instance,
        authorization=authorization,
    )


def field_attribute(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    """Get the attribute of a field by its name or index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    name : AvName
        Name of the field whose attribute to retrieve
    index : AvIndex
        Index position of the field whose attribute to retrieve
    instance : AvInstance
        Instance from which to get the field attribute
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvAttribute
        Attribute of the specified field

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.set_field(entity=entity, attribute=AvAttribute.TYPE, name="TypedField", value=AvValue.encode_text("Value"), authorization=authorization)
    >>> fields.field_attribute(entity=entity, name="TypedField", authorization=authorization)
    TYPE_ATTRIBUTE

    """
    return aspects.attribute(
        entity=entity,
        aspect=AvAspect.FIELD,
        name=name,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def sort_fields(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Sort the fields in the field collection
    
    Sorts fields according to the specified parameter criteria.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute filter for fields to be sorted
    instance : AvInstance
        Instance containing the fields to be sorted
    parameter : AvParameter
        Sort parameter defining the sort criteria
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.insert_field(entity=entity, name="ZField", value=AvValue.encode_text("Last"), authorization=authorization)
    >>> fields.insert_field(entity=entity, name="AField", value=AvValue.encode_text("First"), authorization=authorization)
    >>> fields.sort_fields(entity=entity, authorization=authorization)

    """
    aspects.sort(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def erase_fields(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Erase all fields from the field collection
    
    This operation removes all fields and affects corresponding frame structures.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute filter for fields to be erased
    instance : AvInstance
        Instance from which fields will be erased
    parameter : AvParameter
        Additional parameter for the erase operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity
    >>> authorization: AvAuthorization
    >>> fields.erase_fields(entity=entity, authorization=authorization)

    """
    aspects.erase(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_fields(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    """Retrieve all fields as an AvInterchange (JSON) structure
    
    Returns the complete field collection in interchange format for serialization
    or external processing.

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute filter for fields to be retrieved
    instance : AvInstance
        Instance from which to retrieve fields
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Returns
    _______
    AvInterchange
        JSON structure containing all fields

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports fields
    >>> authorization: AvAuthorization
    >>> fields.set_field(entity=entity, attribute=AvAttribute.NAME, name="Field1", value=AvValue.encode_text("Value1"), authorization=authorization)
    >>> fields.set_field(entity=entity, attribute=AvAttribute.TYPE, name="Field2", value=AvValue.encode_integer(42), authorization=authorization)
    >>> fields.set_field(entity=entity, name="Field3", value=AvValue.encode_text("Value3"), authorization=authorization)
    >>> print(fields.retrieve_fields(entity=entity, authorization=authorization))
    {"Fields":[["NAME_ATTRIBUTE","Field1",{"TEXT":"Value1"}],["TYPE_ATTRIBUTE","Field2",{"INTEGER":"42"}],["","Field3",{"TEXT":"Value3"}]]}

    """
    return aspects.retrieve(
        entity=entity,
        aspect=AvAspect.FIELD,
        attribute=attribute,
        instance=instance,
        authorization=authorization,
    )