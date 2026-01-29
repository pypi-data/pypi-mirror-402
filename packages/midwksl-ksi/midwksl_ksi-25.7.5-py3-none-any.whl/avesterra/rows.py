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


def insert_row(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.insert(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        index=index,
        instance=instance,
        offset=NULL_OFFSET,
        parameter=parameter,
        authorization=authorization,
    )


def remove_row(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.remove(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        key=key,
        index=index,
        instance=instance,
        offset=NULL_OFFSET,
        parameter=parameter,
        authorization=authorization,
    )


def replace_row(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.replace(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        index=index,
        instance=instance,
        offset=NULL_OFFSET,
        parameter=parameter,
        authorization=authorization,
    )


def find_row(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    return aspects.find(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        index=index,
        instance=instance,
        offset=NULL_OFFSET,
        authorization=authorization,
    )


def include_row(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.include(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def exclude_row(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.exclude(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def set_row(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    value: AvValue = NULL_VALUE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.set(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        value=value,
        parameter=parameter,
        authorization=authorization,
    )


def get_row(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    return aspects.get(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        authorization=authorization,
    )


def clear_row(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.clear(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        parameter=parameter,
        authorization=authorization,
    )


def row_count(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvCount:
    return aspects.count(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def row_member(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> bool:
    return aspects.member(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def row_name(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvName:
    return aspects.name(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        key=key,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def row_key(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvKey:
    return aspects.key(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def row_value(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvValue:
    return aspects.value(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def row_index(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvIndex:
    return aspects.index(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        name=name,
        key=key,
        instance=instance,
        authorization=authorization,
    )


def row_attribute(
    entity: AvEntity,
    name: AvName = NULL_NAME,
    key: AvKey = NULL_KEY,
    index: AvIndex = NULL_INDEX,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvAttribute:
    return aspects.attribute(
        entity=entity,
        aspect=AvAspect.ROW,
        name=name,
        key=key,
        index=index,
        instance=instance,
        authorization=authorization,
    )


def sort_rows(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.sort(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def erase_rows(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    parameter: AvParameter = NULL_PARAMETER,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
):
    aspects.erase(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        parameter=parameter,
        authorization=authorization,
    )


def retrieve_rows(
    entity: AvEntity,
    key: AvKey = NULL_KEY,
    instance: AvInstance = NULL_INSTANCE,
    authorization: AvAuthorization = NULL_AUTHORIZATION,
) -> AvInterchange:
    return aspects.retrieve(
        entity=entity,
        aspect=AvAspect.ROW,
        attribute=NULL_ATTRIBUTE,
        key=key,
        instance=instance,
        authorization=authorization,
    )