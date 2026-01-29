""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""


from avesterra.avial import AvTime
from avial import avesterra as avial

from avesterra.avial import AvTime




def get_entity_update_time(
    entity: AvEntity, auth: AvAuthorization
) -> AvTime:
    try:
        return entity_element(
            entity=entity, index=1, authorization=auth
        ).decode_time()
    except EntityError as ae:
        return entity_timestamp(entity=entity, authorization=auth)


def set_entity_update_time(
    entity: AvEntity, auth: AvAuthorization
) -> AvTime:
    output: AvTime = AvTime.utcnow()
    try:
        replace_element(
            entity=entity,
            value=AvValue.encode_time(output),
            index=1,
            authorization=auth,
        )
    except EntityError as ee:
        insert_element(
            entity=entity,
            value=AvValue.encode_time(output),
            index=1,
            authorization=auth,
        )
    return output

def get_registry_entries(
    registry: AvRegistry, authorization: AvAuthorization
) -> Dict[AvKey, Tuple[AvName, AvKey, AvEntity]]:
    """Retrieve the registry and return entries.

    Parameters
    __________
    registry : AvRegistry
        Entity EUID of the registry from which one wants to retrieve entries.
    authorization : AvAuthorization
        An authorization that is able to read from the given registry.

    Examples
    ________

    >>>
    >>> registry: AvRegistry
    >>> authorization: AvAuthorization
    >>> registry_entries = registries.get_registry_entries(registry=registry, authorization=authorization)
    >>> print(registry_entries)
    {'US': ('United States of America', 'us', AvEntity(0,0,193048)),'Taiwan': ('Taiwan', 'tw', AvEntity(0,0,193049)),'France': ('France', 'fr', AvEntity(0,0,193050))}

    Returns
    _______
    Dict[AvKey, Tuple[AvName, AvKey, AvEntity]]
        A Dict of the registry entries

    """
    interchange = retrieve_registry(registry, authorization)
    interchange_obj = json.loads(interchange)

    properties = interchange_obj.get("Properties", [])
    return dict(
        (p[1], (p[0], p[1], AvValue.from_json(p[2]).decode_entity()))
        for p in properties
    )