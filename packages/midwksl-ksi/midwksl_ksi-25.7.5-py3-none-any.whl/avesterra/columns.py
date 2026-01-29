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


def insert_column(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.insert(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        index=NULL_INDEX,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def remove_column(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.remove(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        key=key,
        index=NULL_INDEX,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def replace_column(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.replace(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        index=NULL_INDEX,
        instance=instance,
        offset=offset,
        parameter=parameter,
        authorization=authorization,
    )


def find_column(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    return aspects.find(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        index=NULL_INDEX,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def include_column(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.include(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_column(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def set_column(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.set(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def get_column(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    return aspects.get(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        authorization=authorization,
    )


def clear_column(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.clear(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def column_count(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvCount:
    return aspects.count(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def column_member(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> bool:
    return aspects.member(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def column_name(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    return aspects.name(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def column_key(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    return aspects.key(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def column_value(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    return aspects.value(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def column_index(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    return aspects.index(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def column_attribute(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    offset: AvOffset = NULL_OFFSET,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    return aspects.attribute(
        entity=entity,
        aspect=AvAspect.COLUMN,
        name=name,
        key=key,
        instance=instance,
        offset=offset,
        authorization=authorization,
    )


def sort_columns(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.sort(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def erase_columns(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.erase(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_columns(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    return aspects.retrieve(
        entity=entity,
        aspect=AvAspect.COLUMN,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )