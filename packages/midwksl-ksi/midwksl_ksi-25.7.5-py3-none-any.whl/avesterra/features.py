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


def insert_feature(
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
    """Insert a feature at a specific index position

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to associate the feature with
    name : AvName
        Name of the feature
    key : AvKey
        Unique key identifier for the feature
    value : AvValue
        Value to be stored in the feature
    index : AvIndex
        Position where the feature should be inserted
    instance : AvInstance
        Instance identifier for the feature
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.insert_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="key_1", value=AvValue.encode_text("Value 1"), index=0, authorization=authorization)
    >>> features.insert_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 2", key="key_2", value=AvValue.encode_text("Value 2"), index=1, authorization=authorization)
    >>> print(features.feature_count(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization))
    2

    """
    aspects.insert(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def remove_feature(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove a feature at a specific index position

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the feature to remove
    index : AvIndex
        Position of the feature to be removed
    instance : AvInstance
        Instance identifier for the feature
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="key_1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 2", key="key_2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> features.remove_feature(entity=entity, attribute=AvAttribute.EXAMPLE, index=0, authorization=authorization)
    >>> print(features.feature_count(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization))
    1

    """
    aspects.remove(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def replace_feature(
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
    """Replace a feature at a specific index position

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the feature to replace
    name : AvName
        New name for the feature
    key : AvKey
        New unique key identifier for the feature
    value : AvValue
        New value to be stored in the feature
    index : AvIndex
        Position of the feature to be replaced
    instance : AvInstance
        Instance identifier for the feature
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Original", key="key_1", value=AvValue.encode_text("Original Value"), authorization=authorization)
    >>> features.replace_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Replaced", key="key_1", value=AvValue.encode_text("New Value"), index=0, authorization=authorization)
    >>> print(features.feature_value(entity=entity, attribute=AvAttribute.EXAMPLE, index=0, authorization=authorization).decode_text())
    New Value

    """
    aspects.replace(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        index=index,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def find_feature(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Find the index of a feature based on name or value

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the feature to find
    name : AvName
        Name of the feature to search for
    value : AvValue
        Value of the feature to search for
    index : AvIndex
        Starting index for the search
    instance : AvInstance
        Instance identifier for the feature
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Target Feature", key="key_1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Other Feature", key="key_2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> index = features.find_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Target Feature", authorization=authorization)
    >>> print(index)
    0

    """
    return aspects.find(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        name=name,
        value=value,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def include_feature(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Include a feature with unique key in the feature list

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to associate the feature with
    name : AvName
        Name of the feature
    key : AvKey
        Unique key identifier for the feature (must be unique)
    value : AvValue
        Value to be stored in the feature
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="unique_key", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> print(features.get_feature(entity=entity, attribute=AvAttribute.EXAMPLE, key="unique_key", authorization=authorization).decode_text())
    Value 1

    """
    aspects.include(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_feature(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove a feature by its unique key

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the feature to exclude
    key : AvKey
        Unique key identifier of the feature to remove
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="to_remove", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> features.exclude_feature(entity=entity, attribute=AvAttribute.EXAMPLE, key="to_remove", authorization=authorization)
    >>> print(features.get_feature(entity=entity, attribute=AvAttribute.EXAMPLE, key="to_remove", authorization=authorization))
    {"NULL": ""}

    """
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def set_feature(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Set or update a feature value by key

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to associate the feature with
    name : AvName
        Name of the feature
    key : AvKey
        Unique key identifier for the feature
    value : AvValue
        Value to be stored in the feature
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.set_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="set_key", value=AvValue.encode_text("Initial Value"), authorization=authorization)
    >>> features.set_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="set_key", value=AvValue.encode_text("Updated Value"), authorization=authorization)
    >>> print(features.get_feature(entity=entity, attribute=AvAttribute.EXAMPLE, key="set_key", authorization=authorization).decode_text())
    Updated Value

    """
    aspects.set(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def get_feature(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a feature by its key

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the feature
    key : AvKey
        Unique key identifier of the feature to retrieve
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="get_key", value=AvValue.encode_text("Retrieved Value"), authorization=authorization)
    >>> print(features.get_feature(entity=entity, attribute=AvAttribute.EXAMPLE, key="get_key", authorization=authorization).decode_text())
    Retrieved Value

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> print(features.get_feature(entity=entity, attribute=AvAttribute.EXAMPLE, key="nonexistent_key", authorization=authorization))
    {"NULL": ""}

    """
    return aspects.get(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        key=key,
        authorization=authorization,
    )


def clear_feature(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Clear the value of a feature while keeping the feature entry

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the feature to clear
    key : AvKey
        Unique key identifier of the feature to clear
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="clear_key", value=AvValue.encode_text("To be cleared"), authorization=authorization)
    >>> features.clear_feature(entity=entity, attribute=AvAttribute.EXAMPLE, key="clear_key", authorization=authorization)
    >>> print(features.get_feature(entity=entity, attribute=AvAttribute.EXAMPLE, key="clear_key", authorization=authorization))
    {"NULL": ""}

    """
    aspects.clear(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def feature_count(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvCount:
    """Get the count of features for a specific attribute

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to count features for
    instance : AvInstance
        Instance identifier for the features
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="key_1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 2", key="key_2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> print(features.feature_count(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization))
    2

    """
    return aspects.count(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        instance=instance,
        authorization=authorization,
    )


def feature_member(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvBoolean:
    """Check if a feature with the given key exists

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact to check for feature membership
    key : AvKey
        Unique key identifier to check for
    instance : AvInstance
        Instance identifier for the feature
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="member_key", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> print(features.feature_member(entity=entity, attribute=AvAttribute.EXAMPLE, key="member_key", authorization=authorization))
    True
    >>> print(features.feature_member(entity=entity, attribute=AvAttribute.EXAMPLE, key="nonexistent_key", authorization=authorization))
    False

    """
    return aspects.member(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def feature_name(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    """Get the name of a feature by key or index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the feature
    key : AvKey
        Unique key identifier of the feature
    index : AvIndex
        Index position of the feature
    instance : AvInstance
        Instance identifier for the feature
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Named Feature", key="name_key", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> print(features.feature_name(entity=entity, attribute=AvAttribute.EXAMPLE, key="name_key", authorization=authorization))
    Named Feature

    """
    return aspects.name(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        key=key,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def feature_key(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    """Get the key of a feature by index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the feature
    index : AvIndex
        Index position of the feature
    instance : AvInstance
        Instance identifier for the feature
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="indexed_key", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> print(features.feature_key(entity=entity, attribute=AvAttribute.EXAMPLE, index=0, authorization=authorization))
    indexed_key

    """
    return aspects.key(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def feature_value(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    """Get the value of a feature by key or index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the feature
    key : AvKey
        Unique key identifier of the feature
    index : AvIndex
        Index position of the feature
    instance : AvInstance
        Instance identifier for the feature
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="value_key", value=AvValue.encode_text("Retrieved Value"), authorization=authorization)
    >>> print(features.feature_value(entity=entity, attribute=AvAttribute.EXAMPLE, key="value_key", authorization=authorization).decode_text())
    Retrieved Value

    """
    return aspects.value(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        key=key,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def feature_index(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    """Get the index position of a feature by key

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing the feature
    key : AvKey
        Unique key identifier of the feature
    instance : AvInstance
        Instance identifier for the feature
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="index_key", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 2", key="other_key", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> print(features.feature_index(entity=entity, attribute=AvAttribute.EXAMPLE, key="index_key", authorization=authorization))
    0

    """
    return aspects.index(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def feature_attribute(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    """Get the attribute of a feature by key or index

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    key : AvKey
        Unique key identifier of the feature
    index : AvIndex
        Index position of the feature
    instance : AvInstance
        Instance identifier for the feature
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="attr_key", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> print(features.feature_attribute(entity=entity, key="attr_key", authorization=authorization))
    EXAMPLE_ATTRIBUTE

    """
    return aspects.attribute(
        entity=entity,
        aspect=AvAspect.FEATURE,
        key=key,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def sort_features(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Sort features by name or other criteria

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing features to sort
    instance : AvInstance
        Instance identifier for the features
    parameter : AvParameter
        Sort parameter (e.g., sort criteria)
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Z Feature", key="key_z", value=AvValue.encode_text("Value Z"), authorization=authorization)
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="A Feature", key="key_a", value=AvValue.encode_text("Value A"), authorization=authorization)
    >>> features.sort_features(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization)
    >>> print(features.feature_name(entity=entity, attribute=AvAttribute.EXAMPLE, index=0, authorization=authorization))
    A Feature

    """
    aspects.sort(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def erase_features(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove all features for a specific attribute

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing features to erase
    instance : AvInstance
        Instance identifier for the features
    parameter : AvParameter
        Additional parameter for the operation
    authorization : AvAuthorization
        An authorization that is able to write to the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="key_1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 2", key="key_2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> features.erase_features(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization)
    >>> print(features.feature_count(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization))
    0

    """
    aspects.erase(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_features(
    entity: AvEntity,
    attribute: AvAttribute = NULL_ATTRIBUTE,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    """Return contents of feature list as an Interchange (JSON)

    Parameters
    __________
    entity : AvEntity
        Target entity euid
    attribute : AvAttribute
        Attribute of the fact containing features to retrieve
    instance : AvInstance
        Instance identifier for the features
    authorization : AvAuthorization
        An authorization that is able to read from the `entity`

    Examples
    ________

    >>> 
    >>> entity: AvEntity # Assume entity is connected to an outlet that supports features
    >>> authorization: AvAuthorization
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 1", key="key_1", value=AvValue.encode_text("Value 1"), authorization=authorization)
    >>> features.include_feature(entity=entity, attribute=AvAttribute.EXAMPLE, name="Feature 2", key="key_2", value=AvValue.encode_text("Value 2"), authorization=authorization)
    >>> print(features.retrieve_features(entity=entity, attribute=AvAttribute.EXAMPLE, authorization=authorization))
    {"Features":[["Feature 1","key_1",{"TEXT":"Value 1"}],["Feature 2","key_2",{"TEXT":"Value 2"}]]}

    """
    return aspects.retrieve(
        entity=entity,
        aspect=AvAspect.FEATURE,
        attribute=attribute,
        instance=instance,
        authorization=authorization,
    )