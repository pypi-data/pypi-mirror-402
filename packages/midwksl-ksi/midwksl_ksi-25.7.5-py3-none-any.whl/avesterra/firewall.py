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



def allow_rule(
    address: AvAddress,
    server: AvEntity = NULL_ENTITY,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Allow access to `server` from an `address` by placing the rule at index `index` of the firewall rules

        Parameters
        __________
        address : AvAddress
            Integer IPv4 address
        server : AvEntity
            Server to apply firewall rule to
        index : AvIndex
            Index to place the new firewall rule at
        authorization : AvAuthorization
            Root authorization of the server

        Returns
        _______
        None

        Examples
        ________

        >>> 
        >>> authorization: AvAuthorization
        >>> firewall.allow_rule(address=2130706433, index=1, authorization=authorization) # 2130706433 = 127.0.0.1
        """

    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=ALLOW_PARAMETER,
        value=AvValue.encode_avesterra(str(address)),
        index=index,
        authorization=authorization,
    )


def deny_rule(
    address: AvAddress,
    server: AvEntity = NULL_ENTITY,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Deny access to `server` from an `address` by placing the rule at index `index` of the firewall rules

            Parameters
            __________
            address : AvAddress
                Integer IPv4 address
            server : AvEntity
                Server to apply firewall rule to
            index : AvIndex
                Index to place the new firewall rule at
            authorization : AvAuthorization
                Root authorization of the server

            Returns
            _______
            None

            Examples
            ________

            >>> 
            >>> authorization: AvAuthorization
            >>> firewall.deny_rule(address=3232235786, index=1, authorization=authorization) # 3232235786 = 192.168.1.10
            """
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=DENY_PARAMETER,
        value=AvValue.encode_avesterra(str(address)),
        index=index,
        authorization=authorization,
    )


def void_rule(
    server: AvEntity = NULL_ENTITY,
    index: AvIndex = NULL_INDEX,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    """Remove rule at index `index` of the firewall rules

                Parameters
                __________
                server : AvEntity
                    Server to apply firewall rule to
                index : AvIndex
                    Index to place the new firewall rule at
                authorization : AvAuthorization
                    Root authorization of the server

                Returns
                _______
                None

                Examples
                ________

                >>> 
                >>> authorization: AvAuthorization
                >>> firewall.deny_rule(address=3232235786, index=1, authorization=authorization) # 3232235786 = 192.168.1.10
                >>> firewall.void_rule(index=1, authorization=authorization) # 3232235786 = 192.168.1.10
                """
    invoke_entity(
        entity=server,
        method=AvMethod.AVESTERRA,
        parameter=VOID_PARAMETER,
        index=index,
        authorization=authorization,
    )
