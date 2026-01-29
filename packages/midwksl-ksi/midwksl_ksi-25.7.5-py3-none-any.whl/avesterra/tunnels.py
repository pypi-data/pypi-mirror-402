""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""
from avesterra.predefined import tunnel_outlet
from avesterra.avial import *


AvTunnel = AvEntity
AvPortal = AvEntity


def create_tunnel(
    name: AvName = NULL_NAME,
    portal: AvPortal = NULL_ENTITY,
    server: AvEntity = NULL_ENTITY,
    outlet: AvEntity = NULL_ENTITY,
    authority: AvAuthorization = NULL_AUTHORIZATION,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvTunnel:
    """Create a new tunnel construct for AvesTerra P2P network access.

    Tunnels are an AvesTerra construct like a client VPN connection, 
    whereby an AvesTerra server, hidden behind a NAT firewall, is able to be accessed 
    through a proxy AvesTerra server, via the AvesTerra P2P network. An AvesTerra 
    server behind a firewall and is not accessible to the P2P network, 'tunnels into' 
    an AvesTerra server that is accessible via the P2P network, and through that tunnel, 
    traffic is routed to the AvesTerra server behind the NAT firewall.

    The Tunnel, on the tunneling AvesTerra server, must be paired with a Portal, 
    on the P2P accessible AvesTerra server, where the name and authority fields 
    of the Tunnel match the name and authority fields of the Portal.

    Parameters
    __________
    name : AvName, optional
        The name identifier for the tunnel, by default NULL_NAME
    portal : AvPortal, optional
        The portal entity to pair with this tunnel, by default NULL_ENTITY
    server : AvEntity, optional
        The entity of the server that will host the tunnel, by default NULL_ENTITY; the 'local server' is used if NULL_ENTITY is given here
    outlet : AvEntity, optional
        The outlet entity to use for tunnel creation, by default NULL_ENTITY
    authority : AvAuthorization, optional
        The authority for the tunnel, by default NULL_AUTHORIZATION
    authorization : AvAuthorization, optional
        The authorization required to create the tunnel, by default NULL_AUTHORIZATION

    Returns
    _______
    AvTunnel
        The created tunnel entity

    Examples
    ________

    >>> 
    >>> tunnel_name = AvName("epic_tunnel")
    >>> portal_entity: AvPortal  # Assume portal is configured
    >>> server_entity: AvEntity  # Assume server is available
    >>> auth: AvAuthorization  # Assume authorization is available
    >>> authority_of_tunnel: AvAuthorization # Assume authority is available
    >>> tunnel = tunnels.create_tunnel(
    ...     name=tunnel_name,
    ...     portal=portal_entity,
    ...     server=server_entity,
    ...     authority=authority_of_tunnel,
    ...     authorization=auth
    ... )
    >>> print(f"Created tunnel: {tunnel}")
    """
    adapter_outlet = outlet if outlet != NULL_ENTITY else tunnel_outlet
    return invoke_entity(
        entity=adapter_outlet,
        method=AvMethod.CREATE,
        name=name,
        context=AvContext.AVESTERRA,
        category=AvCategory.AVESTERRA,
        klass=AvClass.TUNNEL,
        value=AvValue.encode_authorization(authority),
        auxiliary=portal,
        ancillary=server,
        authorization=authorization,
    ).decode_entity()


def delete_tunnel(
    tunnel: AvTunnel, authorization: AvAuthorization = NULL_AUTHORIZATION
) -> None:
    """Delete an existing tunnel construct.

    Removes a tunnel from the AvesTerra P2P network, terminating the connection 
    between the tunneling server and the portal server.

    Parameters
    __________
    tunnel : AvTunnel
        The tunnel entity to be deleted
    authorization : AvAuthorization, optional
        The authorization required to delete the tunnel, by default NULL_AUTHORIZATION

    Examples
    ________

    >>> 
    >>> tunnel: AvTunnel  # Assume tunnel exists
    >>> auth: AvAuthorization  # Assume authorization is available
    >>> tunnels.delete_tunnel(tunnel=tunnel, authorization=auth)
    """
    invoke_entity(
        entity=tunnel,
        method=AvMethod.DELETE,
        authorization=authorization,
    )


def open_portal(
    portal: AvPortal,
    name: AvName = NULL_NAME,
    server: AvEntity = NULL_ENTITY,
    authority: AvAuthorization = NULL_AUTHORIZATION,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> None:
    """Open a portal on an AvesTerra server for tunnel access.

    Portals are an AvesTerra construct that are not unlike a VPN server within 
    the AvesTerra knowledge space, whereby an AvesTerra server can serve as a 
    'router' to hosts that are unable to be directly connected to by clients 
    and other AvesTerra servers. A Portal can be configured for a 'tunneling' 
    AvesTerra server that is not directly accessible. As long as said
    'tunneling' AvesTerra server is able to make a direct connection with the 
    'portaling' AvesTerra server, where the Portal is configured; traffic can
    be routed to the 'portaling' AvesTerra server, via the Portal, through the 
    Tunnel, and to the 'tunneling' AvesTerra server.

    Parameters
    __________
    portal : AvPortal
        The portal entity to open
    name : AvName, optional
        The name identifier for the portal, by default NULL_NAME
    server : AvEntity, optional
        The entity of the server that will host the portal by default NULL_ENTITY; the 'local server' is used if NULL_ENTITY is given here
    authority : AvAuthorization, optional
        The authority for the portal, by default NULL_AUTHORIZATION
    authorization : AvAuthorization, optional
        The authorization required to open the portal, by default NULL_AUTHORIZATION

    Examples
    ________

    >>> 
    >>> portal: AvPortal  # Assume portal entity exists
    >>> server: AvEntity  # Assume entity of the server exists
    >>> portal_name = AvName("my_portal")
    >>> auth: AvAuthorization  # Assume authorization is available
    >>> tunnels.open_portal(
    ...     portal=portal,
    ...     name=portal_name,
    ...     server=server,
    ...     authorization=auth
    ... )
    """
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        name=name,
        auxiliary=portal,
        parameter=PORTAL_PARAMETER,
        authority=authority,
        authorization=authorization,
    )


def close_portal(
    portal: AvPortal,
    server: AvEntity = NULL_ENTITY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> None:
    """Close an existing portal on an AvesTerra server.

    Terminates the portal connection, preventing further tunnel access through 
    the specified portal.

    Parameters
    __________
    portal : AvPortal
        The portal entity to close
    server : AvEntity, optional
        The entity of the server that hosts the portal, by default NULL_ENTITY; the 'local server' is used if NULL_ENTITY is given here
    authorization : AvAuthorization, optional
        The authorization required to close the portal, by default NULL_AUTHORIZATION

    Examples
    ________

    >>> 
    >>> portal: AvPortal  # Assume portal entity exists
    >>> server: AvEntity  # Assume entity of the server exists
    >>> auth: AvAuthorization  # Assume authorization is available
    >>> tunnels.close_portal(portal=portal, server=server, authorization=auth)
    """
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        auxiliary=portal,
        parameter=UNPORTAL_PARAMETER,
        authorization=authorization,
    )


def parse_portals(server_model: Dict) -> Dict[str, str]:
    """Parse portal information from a server model dictionary.

    Extracts portal attribute information from the server model's attributes,
    creating a mapping of entity strings to portal names.

    Parameters
    __________
    server_model : Dict
        A dictionary containing server model data with "Attributes" key

    Returns
    _______
    Dict[str, str]
        A dictionary mapping entity strings to portal names

    Examples
    ________

    >>> 
    >>> server_model = {
    ...     ...
    ...     "Attributes": [
    ...         ["PORTAL_ATTRIBUTE", {"value": "data"}, [("portal1", "entity1", <1|1100|0>)]],
    ...         ["OTHER_ATTRIBUTE", {"value": "other"}, []]
    ...     ]
    ...     ...
    ... }
    >>> portal_info = tunnels.parse_portals(server_model)
    >>> print(portal_info)
    {'<1|1100|0>': 'portal1'}
    """
    attributes = server_model["Attributes"]
    portal_info: Dict[str, str] = {}
    for attribute in attributes:
        if 'PORTAL_ATTRIBUTE' in attribute:
            for name, entity_str, _ in attribute[2]:
                portal_info[entity_str] = name
    return portal_info