
from avesterra import AvEntity, AvCategory, AvContext
from avial import avesterra as av
from avesterra import AvAuthorization, AvClass

from avesterra import AvEntity, AvCategory, AvContext

from avesterra import AvAuthorization, AvClass



def create_control_surface(
    name: str,
    outlet: AvEntity,
    auth: AvAuthorization
) -> AvEntity:
    e: AvEntity = av.create_entity(
        name=name,
        key=name.lower().replace(" ", "_"),
        context=AvContext.TECHNOLOGY,
        category=AvCategory.OBJECT,
        klass=AvClass.SUBSYSTEM,
        authorization=auth
    )
    av.connect_outlet(
        entity=e,
        outlet=outlet,
        presence=1,
        authorization=auth
    )
    return e

