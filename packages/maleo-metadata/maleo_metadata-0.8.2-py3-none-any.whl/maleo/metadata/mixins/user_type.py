from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier
from nexo.types.string import OptStrT
from ..enums.user_type import IdentifierType
from ..types.user_type import IdentifierValueType


class Key(BaseModel):
    key: str = Field(..., max_length=20, description="User type's key")


class Name(BaseModel, Generic[OptStrT]):
    name: OptStrT = Field(..., max_length=20, description="User type's name")


class UserTypeIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdUserTypeIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDUserTypeIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


class KeyUserTypeIdentifier(Identifier[Literal[IdentifierType.KEY], str]):
    type: Annotated[
        Literal[IdentifierType.KEY],
        Field(IdentifierType.KEY, description="Identifier's type"),
    ] = IdentifierType.KEY
    value: Annotated[str, Field(..., description="Identifier's value", max_length=20)]


class NameUserTypeIdentifier(Identifier[Literal[IdentifierType.NAME], str]):
    type: Annotated[
        Literal[IdentifierType.NAME],
        Field(IdentifierType.NAME, description="Identifier's type"),
    ] = IdentifierType.NAME
    value: Annotated[str, Field(..., description="Identifier's value", max_length=20)]


AnyUserTypeIdentifier = (
    UserTypeIdentifier
    | IdUserTypeIdentifier
    | UUIDUserTypeIdentifier
    | KeyUserTypeIdentifier
    | NameUserTypeIdentifier
)


def is_id_identifier(
    identifier: AnyUserTypeIdentifier,
) -> TypeGuard[IdUserTypeIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyUserTypeIdentifier,
) -> TypeGuard[UUIDUserTypeIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)


def is_key_identifier(
    identifier: AnyUserTypeIdentifier,
) -> TypeGuard[KeyUserTypeIdentifier]:
    return identifier.type is IdentifierType.KEY and isinstance(identifier.value, str)


def is_name_identifier(
    identifier: AnyUserTypeIdentifier,
) -> TypeGuard[NameUserTypeIdentifier]:
    return identifier.type is IdentifierType.NAME and isinstance(identifier.value, str)
