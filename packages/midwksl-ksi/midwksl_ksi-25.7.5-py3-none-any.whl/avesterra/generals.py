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
from avesterra.predefined import general_outlet

from avesterra.avial import *
from avesterra.predefined import general_outlet


AvGeneral = AvEntity


def create_general(
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    context: AvContext = NULL_CONTEXT,
    category: AvCategory = NULL_CATEGORY,
    klass: AvClass = NULL_CLASS,
    mode: AvMode = AvMode.NULL,
    outlet: AvEntity = NULL_ENTITY,
    server: AvEntity = NULL_ENTITY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvGeneral:
    """Create a new general in the AvesTerra knowledge space
    
    Generals are entities that are connected to the General Adapter Outlet(<0|0|14>) 
    at Presence level 0 and have been allocated as Generals in the Generals Adapter 
    file system. Generals are a 'catch-all' solution for Avial, providing the most 
    rich representations possible through support for Attributions, Facts, Properties, 
    and Data access. They should be used when maximal richness/capabilities are needed 
    for system representations, but should be used in a limited capacity to avoid 
    performance bottlenecks.

    Parameters
    __________
    name : AvName, optional
        The name to assign to the new general
    key : AvKey, optional
        Unique identifier key for the general
    context : AvContext, optional
        Context for the general
    category : AvCategory, optional
        Category for the general
    klass : AvClass, optional
        Class for the general
    mode : AvMode, optional
        Operational mode for the general
    outlet : AvEntity, optional
        Custom outlet to use instead of the default general_outlet
    server : AvEntity, optional
        Server entity to associate with the General
    authorization : AvAuthorization, optional
        Authorization required to create the general; must be on both general and general adapter outlet

    Returns
    _______
    AvGeneral
        The newly created general

    Examples
    ________

    >>> 
    >>> authorization: AvAuthorization
    >>> general = generals.create_general(name="MyGeneral", authorization=authorization)
    >>> print(f"Created General: {general}")
    
    Notes
    _____
    Generals support the full range of AvesTerra constructs including:
    - Attributions: Simple attribute/value pairs with optional traits
    - Facts: Complex semantic structures with facets, features, fields, and frames
    - Properties: Name/value pairs with optional keys and annotations
    - Data: Direct storage of arbitrary data content
    
    Due to their comprehensive capabilities, Generals should be used judiciously
    to maintain system performance. Consider using more specialized entity types
    (Files, Folders) when their specific capabilities are enough.
    """
    adapter = general_outlet if outlet == NULL_ENTITY else outlet
    return invoke_entity(
        entity=adapter,
        method=AvMethod.CREATE,
        name=name,
        key=key,
        context=context,
        category=category,
        klass=klass,
        mode=mode,
        ancillary=server,
        authorization=authorization,
    ).decode_entity()


def delete_general(
    general: AvGeneral, authorization: AvAuthorization = NULL_AUTHORIZATION
) -> None:
    """Delete a general from the AvesTerra knowledge space
    
    Permanently removes the specified general and all associated data
    including attributions, facts, properties, and any stored data content.
    This operation cannot be undone.

    Parameters
    __________
    general : AvGeneral
        The general to be deleted
    authorization : AvAuthorization, optional
        Authorization required to delete the general; must be on both general and general adapter outlet.

    Examples
    ________

    >>> 
    >>> general: AvGeneral # Assume this is a valid general
    >>> authorization: AvAuthorization
    >>> generals.delete_general(general=general, authorization=authorization)
    >>> print("general has been deleted")


    >>> 
    >>> general: AvGeneral
    >>> admin_auth: AvAuthorization
    >>> generals.delete_general(general, admin_auth)
    >>> print("General deleted with admin authorization")
    
    Notes
    _____
    Deleting a general will remove all associated constructs:
    - All attributions and their traits
    - All facts with their facets, features, fields, and frames
    - All properties and their annotations
    - All stored data content
    
    Ensure proper authorization is provided as this operation requires
    appropriate permissions to delete the general and its contents.
    """
    invoke_entity(entity=general, method=AvMethod.DELETE, authorization=authorization)