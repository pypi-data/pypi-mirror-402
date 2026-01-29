""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""

from typing import Dict, Tuple

from avesterra.avial import *

from avesterra.avial import *



class Routing(IntEnum):
    """Enumeration for routing types in AvesTerra network infrastructure
    
    This enumeration defines the different types of routing that can be enabled
    on an AvesTerra server to control network traffic flow and connectivity.
    """
    NULL = NULL_PARAMETER
    LOGICAL = LOGICAL_PARAMETER
    PHYSICAL = PHYSICAL_PARAMETER
    VIRTUAL = VIRTUAL_PARAMETER


def route_host(
    server: AvEntity,
    host: AvEntity,
    authorization: AvAuthorization,
    address: AvAddress = NULL_ADDRESS,
    trusted: bool = False,
):
    """Configure routing for a specific host on the AvesTerra server
    
    This function establishes or modifies routing configuration for a host entity
    on the specified AvesTerra server. It allows setting network addresses and
    trust relationships for host-to-host communication.

    Parameters
    __________
    server : AvEntity
        The AvesTerra server entity that will handle the routing
    host : AvEntity
        The host entity to be routed
    authorization : AvAuthorization
            Root authorizations of the `server`
    address : AvAddress, optional
        Integer network address for the host routing configuration (default: NULL_ADDRESS)
    trusted : bool, optional
        Whether the host should be marked as trusted (default: False)

    Returns
    _______
    AvValue
        Result of the routing configuration operation

    Examples
    ________

    >>> 
    >>> server: AvEntity
    >>> host: AvEntity
    >>> authorization: AvAuthorization
    >>> address: AvAddress # Assume address is a valid integer representation of an IPv4 address
    >>> routing.route_host(server=server, host=host, authorization=authorization, address=address, trusted=True)

    >>> 
    >>> server: AvEntity
    >>> host: AvEntity
    >>> authorization: AvAuthorization
    >>> routing.route_host(server=server, host=host, authorization=authorization, trusted=False)
    """
    return invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=HOST_PARAMETER,
        name="TRUSTED" if trusted else "",
        key=str(host),
        value=AvValue.encode_string(
            str(address) if address is not NULL_ADDRESS else ""
        ),
        authorization=authorization,
    )


def route_network(
    server: AvEntity,
    network: AvEntity,
    authorization: AvAuthorization,
    address: AvAddress = NULL_ADDRESS,
    trusted: bool = False,
):
    """Configure routing for a network on the AvesTerra server
    
    This function establishes or modifies routing configuration for a network entity
    on the specified AvesTerra server. It allows setting network addresses and
    trust relationships for peer-to-peer communication.

    Parameters
    __________
    server : AvEntity
        The AvesTerra server entity that will handle the routing
    network : AvEntity
        The network entity to be routed
    authorization : AvAuthorization
        Root authorizations of the `server`
    address : AvAddress, optional
        Integer network address for the host routing configuration (default: NULL_ADDRESS)
    trusted : bool, optional
        Whether the network should be marked as trusted (default: False)

    Returns
    _______
    AvValue
        Result of the routing configuration operation

    Examples
    ________

    >>> 
    >>> server: AvEntity
    >>> network: AvEntity
    >>> authorization: AvAuthorization
    >>> address: AvAddress # Assume address is a valid integer representation of an IPv4 address
    >>> routing.route_network(server=server, network=network, authorization=authorization, address=address, trusted=True)

    >>> 
    >>> server: AvEntity
    >>> network: AvEntity
    >>> authorization: AvAuthorization
    >>> address: AvAddress # Assume address is a valid integer representation of an IPv4 address
    >>> routing.route_network(server=server, network=network, authorization=authorization, trusted=False)
    """
    return invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=NETWORK_PARAMETER,
        name="TRUSTED" if trusted else "",
        key=str(network),
        value=AvValue.encode_string(
            str(address) if address is not NULL_ADDRESS else ""
        ),
        authorization=authorization,
    )


def include_host(
    server: AvEntity,
    host_entity: AvEntity,
    authorization: AvAuthorization,
    address: AvAddress = NULL_ADDRESS,
    trusted: bool = False,
):
    """Include a host in the AvesTerra server's routing table
    
    This function adds a host to the server's routing configuration, enabling
    network communication to the specified host. The host will be accessible
    through the server's routing infrastructure.

    Parameters
    __________
    server : AvEntity
        The AvesTerra server entity that will handle the routing
    host_entity : AvEntity
        The host entity to be included in routing
    authorization : AvAuthorization
        Root authorization of server that is being configured
    address : AvAddress, optional
        Network address for the host (default: NULL_ADDRESS)
    trusted : bool, optional
        Whether the host should be marked as trusted (default: False)

    Raises
    ______
    ValueError
        When address is NULL or empty, as an address is required for inclusion

    Examples
    ________

    >>> 
    >>> server: AvEntity
    >>> host_entity: AvEntity
    >>> authorization: AvAuthorization
    >>> address: AvAddress # Assume address is a valid integer representation of an IPv4 address
    >>> routing.include_host(server=server, host_entity=host_entity, authorization=authorization, address=address, trusted=True)

    >>> 
    >>> server: AvEntity
    >>> host_entity: AvEntity
    >>> authorization: AvAuthorization
    >>> address: AvAddress # Assume address is a valid integer representation of an IPv4 address
    >>> routing.include_host(server=server, host_entity=host_entity, authorization=authorization, address=address, trusted=False)
    """
    if not address:
        raise ValueError("Argument `address` cannot be NULL when including a host")

    route_host(
        server=server,
        address=address,
        host=host_entity,
        trusted=trusted,
        authorization=authorization,
    )


def exclude_host(server: AvEntity, host: AvEntity, authorization: AvAuthorization):
    """Exclude a host from the AvesTerra server's routing table
    
    This function removes a host from the server's routing configuration,
    preventing network communication to the specified host through this server.

    Parameters
    __________
    server : AvEntity
        The AvesTerra server entity that will handle the routing
    host : AvEntity
        The host entity to be excluded from routing
    authorization : AvAuthorization
        Root authorization of server that is being configured

    Examples
    ________

    >>> 
    >>> server: AvEntity
    >>> host: AvEntity
    >>> authorization: AvAuthorization
    >>> routing.exclude_host(server=server, host=host, authorization=authorization)
    """
    route_host(server=server, host=host, address=0, authorization=authorization)


def include_network(
    server: AvEntity,
    network: AvEntity,
    address: AvAddress,
    authorization: AvAuthorization,
    trusted: bool = False,
):
    """Include a network in the AvesTerra server's routing table
    
    This function adds a network to the server's routing configuration, enabling
    network communication to all hosts within the specified network range.

    Parameters
    __________
    server : AvEntity
        The AvesTerra server entity that will handle the routing
    network : AvEntity
        The network entity to be included in routing
    address : AvAddress
        Network address range for the network (required)
    authorization : AvAuthorization
        Root authorization of server that is being configured
    trusted : bool, optional
        Whether the network should be marked as trusted (default: False)

    Raises
    ______
    ValueError
        When address is NULL or empty, as an address is required for inclusion

    Examples
    ________

    >>> 
    >>> server: AvEntity
    >>> network: AvEntity
    >>> authorization: AvAuthorization
    >>> address: AvAddress # Assume address is a valid integer representation of an IPv4 address
    >>> routing.include_network(server=server, network=network, address=address, authorization=authorization, trusted=True)

    >>> 
    >>> server: AvEntity
    >>> network: AvEntity
    >>> authorization: AvAuthorization
    >>> address: AvAddress # Assume address is a valid integer representation of an IPv4 address
    >>> routing.include_network(server=server, network=network, address=address, authorization=authorization, trusted=False)
    """
    if not address:
        raise ValueError("Argument `address` cannot be NULL when including a network")

    route_network(
        server=server,
        address=address,
        network=network,
        trusted=trusted,
        authorization=authorization,
    )


def exclude_network(
    server: AvEntity, network: AvEntity, authorization: AvAuthorization
):
    """Exclude a network from the AvesTerra server's routing table
    
    This function removes a network from the server's routing configuration,
    preventing network communication to hosts within the specified network range.

    Parameters
    __________
    server : AvEntity
        The AvesTerra server entity that will handle the routing
    network : AvEntity
        The network entity to be excluded from routing
    authorization : AvAuthorization
        Root authorization of server that is being configured

    Examples
    ________

    >>> 
    >>> server: AvEntity
    >>> network: AvEntity
    >>> authorization: AvAuthorization
    >>> routing.exclude_network(server=server, network=network, authorization=authorization)
    """
    route_network(
        server=server,
        network=network,
        authorization=authorization,
    )


def enable_routing(
    server: AvEntity,
    local: AvEntity,
    authorization: AvAuthorization,
    routing: Routing = Routing.NULL,
    gateway: AvEntity = NULL_ENTITY,
):
    """Enable routing functionality on an AvesTerra server
    
    This function activates routing capabilities on the specified AvesTerra server,
    allowing it to route network traffic between different entities. It supports
    logical, physical, and virtual routing types, and can configure gateway relationships.

    Routing must be configured before adapters or other entities are configured on the server,
    otherwise problems may occur; this includes re-configuring.

    Parameters
    __________
    server : AvEntity
        The AvesTerra server entity on which to enable routing
    local : AvEntity
        The EID(Entity ID) that the AvesTerra server will become in the global, p2p, knowledge space
    authorization : AvAuthorization
        Root authorization of server that is being configured
    routing : Routing, optional
        The type of routing to enable (default: Routing.NULL); Logical routing is most popular at the moment
    gateway : AvEntity, optional
        The gateway entity for routing configuration (default: NULL_ENTITY); if NULL_ENTITY, then local becomes its own Gateway

    Examples
    ________

    >>> 
    >>> server: AvEntity
    >>> local: AvEntity
    >>> gateway: AvEntity
    >>> authorization: AvAuthorization
    >>> enable_routing(server=server, local=local, authorization=authorization, routing=Routing.LOGICAL, gateway=gateway)

    """
    if not isinstance(routing, Routing):
        raise TypeError("Argument `routing` must be an instance of Routing")

    # If routing is NULL, then don't change routing,
    # only allow the change of the routing type
    if routing != Routing.NULL:
        # Turn on routing
        invoke_entity(
            entity=server,
            method=AvMethod.AVESTERRA,
            parameter=AvParameter(routing.value),
            authorization=authorization,
        )

    # If no gateway was specified, assume that host_entity is its own gateway
    if gateway == NULL_ENTITY:
        gateway = local

    # Configure routing
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=CONFIGURE_PARAMETER,
        key=str(local),
        value=AvValue.encode_entity(gateway),
        authorization=authorization,
    )

def parse_networks(server_model: Dict) -> Dict[str, Tuple[bool, int]]:
    """Parse network routing information from an AvesTerra server model
    
    This function extracts network routing configuration from a server model
    structure, returning a dictionary mapping network entity strings to their
    trust status and address information.

    Parameters
    __________
    server_model : Dict
        Dictionary containing server model with network routing attributes

    Returns
    _______
    Dict[str, Tuple[bool, int]]
        Dictionary mapping network entity strings to tuples of (trusted, address)
        where trusted is a boolean indicating trust status and address is the
        numeric network address

    Examples
    ________

    >>> 
    >>> server_model = {
    ...     "Attributes": [
    ...         ["NETWORK_ATTRIBUTE", {}, [
    ...             ["TRUSTED", "<0|1002|0>", "2273762998"],
    ...             ["", "<0|999|0>", "134744072"]
    ...         ]]
    ...     ]
    ... }
    >>> network_info = routing.parse_networks(server_model)
    >>> print(network_info)
    {'<1002|0|0>': (True, 2273762998), '<999|0|0>': (False, 134744072)}
    """
    attributes = server_model["Attributes"]
    network_info: Dict[str, Tuple[bool, int]] = {}
    for attribute in attributes:
        if 'NETWORK_ATTRIBUTE' in attribute:
            for trusted, entity_str, num_address_str in attribute[2]:
                network_info[entity_str] = (trusted == "TRUSTED", int(num_address_str))
    return network_info

def parse_hosts(server_model: Dict) -> Dict[str, Tuple[bool, int]]:
    """Parse host routing information from an AvesTerra server model
    
    This function extracts host routing configuration from a server model
    structure, returning a dictionary mapping host entity strings to their
    trust status and address information.

    Parameters
    __________
    server_model : Dict
        Dictionary containing server model with host routing attributes

    Returns
    _______
    Dict[str, Tuple[bool, int]]
        Dictionary mapping host entity strings to tuples of (trusted, address)
        where trusted is a boolean indicating trust status and address is the
        numeric host address

    Examples
    ________

    >>> 
    >>> server_model = {
    ...     "Attributes": [
    ...         ["HOST_ATTRIBUTE", {}, [
    ...             ["TRUSTED", "<0|1002|0>", "2273762998"],
    ...             ["", "<0|999|0>", "134744072"]
    ...         ]]
    ...     ]
    ... }
    >>> host_info = routing.parse_hosts(server_model)
    >>> print(host_info)
    {'<0|1002|0>': (True, 2273762998), '<0|999|0>': (False, 134744072)}
    """
    attributes = server_model["Attributes"]
    host_info: Dict[str, Tuple[bool, int]] = {}
    for attribute in attributes:
        if 'HOST_ATTRIBUTE' in attribute:
            for trusted, entity_str, num_address_str in attribute[2]:
                host_info[entity_str] = (trusted == "TRUSTED", int(num_address_str))
    return host_info