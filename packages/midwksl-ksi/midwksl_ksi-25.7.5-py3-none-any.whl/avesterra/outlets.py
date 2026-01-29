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




AvOutlet = AvEntity


def create_outlet(
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    context: AvContext = NULL_CONTEXT,
    category: AvCategory = NULL_CATEGORY,
    klass: AvClass = NULL_CLASS,
    server: AvEntity = NULL_ENTITY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvOutlet:
    outlet = create_entity(
        name=name,
        key=key,
        context=context,
        category=category,
        klass=klass,
        server=server,
        authorization=authorization,
    )
    activate_entity(outlet, authorization)
    reference_entity(outlet, authorization)
    return outlet


def delete_outlet(
    outlet: AvOutlet,
    timeout: AvTimeout = NULL_TIMEOUT,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    halt_outlet(outlet, authorization)
    disarm_outlet(outlet, authorization)
    flush_outlet(outlet, authorization)
    unlock_outlet(outlet, authorization)
    synchronize_outlet(outlet, authorization)
    deactivate_entity(outlet, authorization)
    dereference_entity(outlet, authorization)
    delete_entity(outlet, timeout=timeout, authorization=authorization)
