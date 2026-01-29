""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""
from typing import Tuple, List, Dict


from avesterra.avial import *

from avesterra.avial import *


AvToken = AvAuthorization



def instate(
    token: AvAuthorization,
    authority: AvAuthorization,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
):
    """Enable or activate a token on the AvesTerra server.

    Instates a token by making it active and available for use in the AvesTerra system.
    This function was previously called 'enabled' in earlier versions of 

    Parameters
    __________
    token : AvAuthorization
        The token to be instated/enabled
    authority : AvAuthorization
        The authority that `token` is mapped to
    authorization : AvAuthorization
        The authorization required to perform the instate operation
    server : AvEntity, optional
        The server entity on which to instate the token, by default NULL_ENTITY

    Examples
    ________

    >>> 
    >>> token: AvAuthorization  # Assume token exists
    >>> authority: AvAuthorization  # Assume authority exists
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> tokens.instate(token=token, authority=authority, authorization=auth)
    """
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=INSTATE_PARAMETER,
        value=AvValue.encode(str(token)),
        authority=authority,
        authorization=authorization,
    )



def destate(
    token: AvAuthorization,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
):
    """Disable or deactivate a token on the AvesTerra server.

    Destates a token by making it inactive and unavailable for use in the AvesTerra system.
    This function was previously called 'disable' in earlier versions of 

    Parameters
    __________
    token : AvAuthorization
        The token to be destated/disabled
    authorization : AvAuthorization
        The authorization required to perform the destate operation
    server : AvEntity, optional
        The server entity on which to destate the token, by default NULL_ENTITY

    Examples
    ________

    >>> 
    >>> token: AvAuthorization  # Assume token exists
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> tokens.destate(token=token, authorization=auth)
    """
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=DESTATE_PARAMETER,
        value=AvValue.encode(str(token)),
        authorization=authorization,
    )

def instated(
    token: AvAuthorization,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
) -> bool:
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=INSTATED_PARAMETER,
        value=AvValue.encode_avesterra(
            str(token)
        ),
        authorization=authorization
    ).decode_boolean()


def retrieve(
    authorization: AvAuthorization, server: AvEntity = NULL_ENTITY
) -> List[Tuple[AvAuthorization, AvAuthorization]]:
    """Retrieve all token mappings from the AvesTerra server.

    Fetches a list of all token-to-authorization mappings currently stored on the server.
    Each mapping represents a token and its associated authorization.

    Parameters
    __________
    authorization : AvAuthorization
        The authorization required to retrieve token mappings
    server : AvEntity, optional
        The server entity from which to retrieve tokens, by default NULL_ENTITY

    Returns
    _______
    List[Tuple[AvAuthorization, AvAuthorization]]
        A list of tuples where each tuple contains (token, authorization) pairs.
        Returns an empty list if no tokens are present.

    Examples
    ________

    >>> 
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> token_mappings = tokens.retrieve(authorization=auth)
    >>> print(f"Found {len(token_mappings)} token mappings")
    >>> for token, auth in token_mappings:
    ...     print(f"Token: {token} -> Auth: {auth}")
    """
    result = invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=TRUE_PARAMETER,
        authorization=authorization,
    )

    entity_obj: Dict = json.loads(result.decode_interchange())

    attributes = entity_obj["Attributes"]

    # If no tokens are present, then return empty list
    if "TOKEN_ATTRIBUTE" not in attributes.keys():
        return []

    token_maps = attributes["TOKEN_ATTRIBUTE"][0]["Properties"]

    # Build mapping
    token_mapping: List[Tuple[AvAuthorization, AvAuthorization]] = []
    for token_str, empty, auth_str in token_maps:
        token_mapping.append((AvAuthorization(token_str), AvAuthorization(auth_str)))

    # Return mapping
    return token_mapping


def couple(
    network: AvEntity,
    token: AvToken,
    authority: AvAuthorization,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
):
    """Couple a token with a network entity.

    Associates a token with a specific authority, when said token is used to access resources
    within the specified network entity; this ensures that `token` is converted to `authority`
    when traffic from this server attempts to access `network`

    Parameters
    __________
    network : AvEntity
        The network entity to couple with the token
    token : AvToken
        The token to be coupled with the authority and network
    authority : AvAuthorization
        The authority that the token will be coupled with
    authorization : AvAuthorization
        The authorization required to perform the couple operation
    server : AvEntity, optional
        The server entity on which to perform the coupling, by default NULL_ENTITY

    Examples
    ________

    >>> 
    >>> network: AvEntity  # Assume network entity exists
    >>> token: AvToken  # Assume token exists
    >>> authority: AvAuthorization  # Assume authority exists
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> tokens.couple(network=network, token=token, authority=authority, authorization=auth)
    """
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=COUPLE_PARAMETER,
        value=AvValue.encode_avesterra(str(token)),
        auxiliary=network,
        authority=authority,
        authorization=authorization,
    )


def decouple(
    network: AvEntity,
    token: AvToken,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
):
    """Decouple a token from a network entity.

    Removes the association between a token and a network entity, which prevents
    `token` from translating to the previously specified `authority` of the coupling.

    Parameters
    __________
    network : AvEntity
        The network entity to decouple the token from
    token : AvToken
        The token to be decoupled from the network
    authorization : AvAuthorization
        The authorization required to perform the decouple operation
    server : AvEntity, optional
        The server entity on which to perform the decoupling, by default NULL_ENTITY

    Examples
    ________

    >>> 
    >>> network: AvEntity  # Assume network entity exists
    >>> token: AvToken  # Assume token exists
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> tokens.decouple(network=network, token=token, authorization=auth)
    """
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=DECOUPLE_PARAMETER,
        value=AvValue.encode_avesterra(str(token)),
        auxiliary=network,
        authorization=authorization,
    )

def coupled(
    network: AvEntity,
    token: AvAuthorization,
    authority: AvAuthorization,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
) -> bool:
    return invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=COUPLED_PARAMETER,
        value=AvValue.encode_avesterra(str(token)),
        auxiliary=network,
        authority=authority,
        authorization=authorization,
    ).decode_boolean()


def pair(
    host: AvEntity,
    token: AvToken,
    authority: AvAuthorization,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
):
    """Pair a token with a host entity.

    Associates a token with a specific authority, when said `token` is used to access resources
    on a specified `host` entity; this ensures that `token` is converted to `authority`
    when traffic from this server attempts to access `host`

    Parameters
    __________
    host : AvEntity
        The host entity to pair with the token
    token : AvToken
        The token to be paired with the host
    authority : AvAuthorization
        The authority authorization required to pair the token
    authorization : AvAuthorization
        The authorization required to perform the pair operation
    server : AvEntity, optional
        The server entity on which to perform the pairing, by default NULL_ENTITY

    Examples
    ________

    >>> 
    >>> host: AvEntity  # Assume host entity exists
    >>> token: AvToken  # Assume token exists
    >>> authority: AvAuthorization  # Assume authority exists
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> tokens.pair(host=host, token=token, authority=authority, authorization=auth)
    """
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=PAIR_PARAMETER,
        value=AvValue.encode_avesterra(str(token)),
        auxiliary=host,
        authority=authority,
        authorization=authorization,
    )


def unpair(
    host: AvEntity,
    token: AvToken,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
):
    """Unpair a token from a host entity.

    Removes the association between a token and a `host` entity, which prevents
    `token` from translating to the previously specified `authority` of the pairing.

    Parameters
    __________
    host : AvEntity
        The host entity to unpair from the token
    token : AvToken
        The token to be unpaired from the host
    authorization : AvAuthorization
        The authorization required to perform the unpair operation
    server : AvEntity, optional
        The server entity on which to perform the unpairing, by default NULL_ENTITY

    Examples
    ________

    >>> 
    >>> host: AvEntity  # Assume host entity exists
    >>> token: AvToken  # Assume token exists
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> tokens.unpair(host=host, token=token, authorization=auth)
    """
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=UNPAIR_PARAMETER,
        value=AvValue.encode_avesterra(str(token)),
        auxiliary=host,
        authorization=authorization,
    )

def paired(
    host: AvEntity,
    token: AvAuthorization,
    authority: AvAuthorization,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
) -> bool:
    return invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=PAIRED_PARAMETER,
        value=AvValue.encode_avesterra(str(token)),
        auxiliary=host,
        authority=authority,
        authorization=authorization
    ).decode_boolean()


def map(
    token: AvToken,
    mask: AvMask,
    authority: AvAuthorization,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
):
    """Map a token with a mask to create a credential mapping.

    Creates a credential by combining a token with a mask, then maps this credential
    on the server to the given `authority` for access control purposes.
    This function was introduced in Avial 4.12.

    Parameters
    __________
    token : AvToken
        The token to be mapped
    mask : AvMask
        The mask to be combined with the token
    authority : AvAuthorization
        The authority to which the credential will be mapped to
    authorization : AvAuthorization
        The authorization required to perform the map operation
    server : AvEntity, optional
        The server entity on which to perform the mapping, by default NULL_ENTITY

    Examples
    ________

    >>> 
    >>> token: AvToken  # Assume token exists
    >>> mask: AvMask  # Assume mask exists
    >>> authority: AvAuthorization  # Assume authority exists
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> tokens.map(token=token, mask=mask, authority=authority, authorization=auth)
    """
    credential = encode_credential(token, mask)
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=MAP_PARAMETER,
        value=AvValue.encode_avesterra(str(credential)),
        authority=authority,
        authorization=authorization,
    )



def unmap(
    token: AvToken,
    authority: AvAuthorization,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
):
    """Unmap a token by removing its credential mapping.

    Removes the credential mapping for a `token` by unmapping it from the server. This will prevent
    `token` from being used as a credential for any entity whose authority is `authority`.
    This function was introduced in Avial 4.12.

    Parameters
    __________
    token : AvToken
        The token to be unmapped
    authority : AvAuthorization
        The authority to unmap from the token
    authorization : AvAuthorization
        The authorization required to perform the unmap operation
    server : AvEntity, optional
        The server entity on which to perform the unmapping, by default NULL_ENTITY

    Examples
    ________

    >>> 
    >>> token: AvToken  # Assume token exists
    >>> authority: AvAuthorization  # Assume authority exists
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> tokens.unmap(token=token, authority=authority, authorization=auth)
    """
    token = encode_credential(token, AvMask())
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=UNMAP_PARAMETER,
        value=AvValue.encode_avesterra(str(token)),
        authority=authority,
        authorization=authorization,
    )

def mapped(
    token: AvAuthorization,
    mask: AvMask,
    authority: AvAuthorization,
    authorization: AvAuthorization,
    server: AvEntity = NULL_ENTITY,
) -> bool:
    credential = encode_credential(token,  mask)
    return invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=MAPPED_PARAMETER,
        value=AvValue.encode_avesterra(str(credential)),
        authority=authority,
        authorization=authorization,
    ).decode_boolean()



def resolve(
    token: AvAuthorization | str,
    authorization: AvAuthorization,
    token_map: List[Tuple[AvAuthorization, AvAuthorization]] | None = None,
):
    """Resolve a token to its corresponding authorization.

    Looks up a token in the token mapping to find its associated authorization.
    If no token map is provided, retrieves the current token map from the server.

    Parameters
    __________
    token : AvAuthorization | str
        The token to resolve, can be an AvAuthorization object or string
    authorization : AvAuthorization
        The authorization required to retrieve token mappings if needed
    token_map : List[Tuple[AvAuthorization, AvAuthorization]] | None, optional
        Pre-existing token map to use for resolution, by default None

    Returns
    _______
    AvAuthorization | List
        The authorization associated with the token, or empty list if not found

    Examples
    ________

    >>> 
    >>> token: AvAuthorization  # Assume token exists
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> resolved_auth = tokens.resolve(token=token, authorization=auth)
    >>> if resolved_auth:
    ...     print(f"Token resolved to: {resolved_auth}")
    ... else:
    ...     print("Token not found in mapping")

    >>> # Using pre-existing token map
    >>> token_mappings = tokens.retrieve(authorization=auth)
    >>> resolved_auth = tokens.resolve(token=token, authorization=auth, token_map=token_mappings)
    """
    if isinstance(token, str):
        token = AvAuthorization(token)

    # If no token map was given, get one from the server
    if token_map is None:
        token_map = retrieve(authorization=authorization)

    # Search for auth that maps to
    # given token
    for map_token, map_auth in token_map:
        if map_token == token:
            return map_auth

    # If token not found, return empty token list
    return []


def display(token_map: List[Tuple[AvAuthorization, AvAuthorization]]) -> Dict[str, str]:
    """Display token mappings in a formatted, human-readable way.

    Takes a list of token-to-authorization mappings and displays them as formatted JSON,
    while also returning a dictionary representation of the mappings.

    Parameters
    __________
    token_map : List[Tuple[AvAuthorization, AvAuthorization]]
        List of token-to-authorization mapping tuples

    Returns
    _______
    Dict[str, str]
        Dictionary mapping token strings to authorization strings

    Examples
    ________

    >>> 
    >>> auth: AvAuthorization  # Assume authorization exists
    >>> token_mappings = tokens.retrieve(authorization=auth)
    >>> mapping_dict = tokens.display(token_mappings)
    {
     "token1": "auth1",
     "token2": "auth2"
    }
    >>> print(f"Found {len(mapping_dict)} token mappings")
    """
    mapping: Dict[str, str] = {}

    # Build mapping
    for token, auth in token_map:
        mapping[f"{str(token)}"] = str(auth)

    # Print formatted JSON string for easy reading
    print(json.dumps(mapping, indent=1))

    # Return mapping
    return mapping