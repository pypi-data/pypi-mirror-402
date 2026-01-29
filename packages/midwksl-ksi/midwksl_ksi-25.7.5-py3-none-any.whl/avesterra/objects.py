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
from avesterra.predefined import object_outlet

from avesterra.avial import *
from avesterra.predefined import object_outlet


AvObject = AvEntity


def create_object(
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    context: AvContext = NULL_CONTEXT,
    category: AvCategory = NULL_CATEGORY,
    klass: AvClass = NULL_CLASS,
    mode: AvMode = AvMode.NULL,
    outlet: AvEntity = NULL_ENTITY,
    server: AvEntity = NULL_ENTITY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvObject:
    """Create a new AvesTerra object with specified attributes.

    Creates a new AvObject (which is an AvEntity) through the AvesTerra system using
    the object outlet. Objects are a fundamental knowledge representation construct
    in AvesTerra that can be classified using context, category, and class taxonomies.
    They serve as the foundation for knowledge representation and can have various model aspects
    (attributions and facts) applied to them.

    Parameters
    __________
    name : AvName, optional
        The name identifier for the object. Defaults to NULL_NAME.
    key : AvKey, optional
        A unique key identifier for the object. Defaults to NULL_KEY.
    value : AvValue, optional
        An initial value to associate with the object. Defaults to NULL_VALUE.
    context : AvContext, optional
        The context classification from the AvesTerra Context Taxonomy. Defaults to NULL_CONTEXT.
    category : AvCategory, optional
        The category classification from the AvesTerra Category Taxonomy. Defaults to NULL_CATEGORY.
    klass : AvClass, optional
        The class classification from the AvesTerra Class Taxonomy. Defaults to NULL_CLASS.
    mode : AvMode, optional
        The mode for object creation. Defaults to AvMode.NULL.
    outlet : AvEntity, optional
        The outlet entity to use for object creation. If NULL_ENTITY, uses the default object_outlet.
    server : AvEntity, optional
        The server entity in which to create the object in. Defaults to NULL_ENTITY.
    authorization : AvAuthorization, optional
        Authorization for creating the object. Defaults to NULL_AUTHORIZATION.

    Returns
    _______
    AvObject
        The newly created object.

    Examples
    ________
    >>> 
    >>> authorization: AvAuthorization  # Assume valid authorization
    >>> # Create a simple object with name and key
    >>> obj = objects.create_object(
    ...     name="MyObject",
    ...     key="my_object",
    ...     authorization=authorization
    ... )
    >>> print(f"Created object: {obj}")

    Raises
    ______
    ApplicationError
        When object creation fails due to invalid parameters or authorization issues.
    """
    adapter = object_outlet if outlet == NULL_ENTITY else outlet
    return invoke_entity(
        entity=adapter,
        method=AvMethod.CREATE,
        name=name,
        key=key,
        value=value,
        context=context,
        category=category,
        klass=klass,
        mode=mode,
        ancillary=server,
        authorization=authorization,
    ).decode_entity()


def delete_object(
    object: AvObject, authorization: AvAuthorization = NULL_AUTHORIZATION
):
    """Delete an existing AvesTerra object.

    Permanently removes an AvObject from the AvesTerra system. This operation
    will delete the object and all its associated data, including any model
    aspects (attributions, facts) that may be attached to it.
    This is a destructive operation that cannot be undone.

    Parameters
    __________
    object : AvObject
        The object to be deleted. Must be a valid AvObject.
    authorization : AvAuthorization, optional
        Authorization for deleting the object; must be on both object and object adapter.

    Examples
    ________
    >>> 
    >>> authorization: AvAuthorization  # Assume valid authorization
    >>> # Create an object first
    >>> obj = objects.create_object(
    ...     name="TempObject",
    ...     authorization=authorization
    ... )
    >>> # Delete the object
    >>> objects.delete_object(object=obj, authorization=authorization)
    >>> print("Object deleted successfully")

    Raises
    ______
    ApplicationError
        When deletion fails due to invalid object, insufficient authorization,
        or if the object is referenced by other entities that prevent deletion.
    """
    invoke_entity(entity=object, method=AvMethod.DELETE, authorization=authorization)