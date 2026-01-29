from typing import Literal, Type, overload
from ..schemas.organization_role import (
    StandardOrganizationRoleSchema,
    FullOrganizationRoleSchema,
    AnyOrganizationRoleSchemaType,
)
from ..enums.organization_role import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardOrganizationRoleSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullOrganizationRoleSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyOrganizationRoleSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyOrganizationRoleSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardOrganizationRoleSchema
    elif granularity is Granularity.FULL:
        return FullOrganizationRoleSchema
