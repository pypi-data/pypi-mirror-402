from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier
from nexo.types.string import OptStrT
from ..enums.system_role import IdentifierType
from ..types.system_role import IdentifierValueType


class Key(BaseModel):
    key: str = Field(..., max_length=20, description="System role's key")


class Name(BaseModel, Generic[OptStrT]):
    name: OptStrT = Field(..., max_length=20, description="System role's name")


class SystemRoleIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdSystemRoleIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDSystemRoleIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


class KeySystemRoleIdentifier(Identifier[Literal[IdentifierType.KEY], str]):
    type: Annotated[
        Literal[IdentifierType.KEY],
        Field(IdentifierType.KEY, description="Identifier's type"),
    ] = IdentifierType.KEY
    value: Annotated[str, Field(..., description="Identifier's value", max_length=20)]


class NameSystemRoleIdentifier(Identifier[Literal[IdentifierType.NAME], str]):
    type: Annotated[
        Literal[IdentifierType.NAME],
        Field(IdentifierType.NAME, description="Identifier's type"),
    ] = IdentifierType.NAME
    value: Annotated[str, Field(..., description="Identifier's value", max_length=20)]


AnySystemRoleIdentifier = (
    SystemRoleIdentifier
    | IdSystemRoleIdentifier
    | UUIDSystemRoleIdentifier
    | KeySystemRoleIdentifier
    | NameSystemRoleIdentifier
)


def is_id_identifier(
    identifier: AnySystemRoleIdentifier,
) -> TypeGuard[IdSystemRoleIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnySystemRoleIdentifier,
) -> TypeGuard[UUIDSystemRoleIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)


def is_key_identifier(
    identifier: AnySystemRoleIdentifier,
) -> TypeGuard[KeySystemRoleIdentifier]:
    return identifier.type is IdentifierType.KEY and isinstance(identifier.value, str)


def is_name_identifier(
    identifier: AnySystemRoleIdentifier,
) -> TypeGuard[NameSystemRoleIdentifier]:
    return identifier.type is IdentifierType.NAME and isinstance(identifier.value, str)
