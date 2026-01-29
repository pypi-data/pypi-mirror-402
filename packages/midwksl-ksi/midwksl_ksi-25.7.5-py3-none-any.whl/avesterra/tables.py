"""
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
This file is part of the Midwest Knowledge System Labs library, which helps developer use our Midwest Knowledge System Labs technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with Midwest Knowledge System Labs.
The Midwest Knowledge System Labs library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Midwest Knowledge System Labs library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Midwest Knowledge System Labs library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Midwest Knowledge System Labs library, you can contact us at support@midwksl.net.
"""


from avesterra.avial import *

from avesterra.avial import *
import avesterra.aspects as aspects


def insert_table(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.insert(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=NULL_VALUE,
        index=NULL_INDEX,
        instance=instance,
        offset=NULL_OFFSET,
        parameter=parameter,
        authorization=authorization,
    )


def remove_table(
    entity: AvEntity,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.remove(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        index=NULL_INDEX,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def replace_table(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.replace(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=NULL_VALUE,
        index=NULL_INDEX,
        instance=instance,
        offset=NULL_OFFSET,
        parameter=parameter,
        authorization=authorization,
    )


def find_table(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    return aspects.find(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        name=name,
        instance=instance,
        authorization=authorization,
    )


def include_table(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.include(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=NULL_VALUE,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_table(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def set_table(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.set(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        key=key,
        value=value,
        index=index,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def get_table(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    return aspects.get(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        key=key,
        index=index,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def clear_table(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.clear(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        key=key,
        index=index,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def table_count(
    entity: AvEntity,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvCount:
    return aspects.count(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        authorization=authorization,
    )


def table_member(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> bool:
    return aspects.member(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        key=key,
        authorization=authorization,
    )


def table_name(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    return aspects.name(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def table_key(
    entity: AvEntity,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    return aspects.key(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        instance=instance,
        authorization=authorization,
    )


def table_value(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    return aspects.value(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def table_index(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    return aspects.index(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        key=key,
        authorization=authorization,
    )


def table_attribute(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    return aspects.attribute(
        entity=entity,
        aspect=AvAspect.TABLE,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def sort_tables(
    entity: AvEntity,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.sort(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        parameter=parameter,
        authorization=authorization,
    )


def erase_tables(
    entity: AvEntity,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.erase(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_tables(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    return aspects.retrieve(
        entity=entity,
        aspect=AvAspect.TABLE,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )