from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier
from nexo.types.string import OptStrT
from ..enums.medical_role import IdentifierType
from ..types.medical_role import IdentifierValueType


class Code(BaseModel, Generic[OptStrT]):
    code: OptStrT = Field(..., max_length=20, description="Medical role's code")


class Key(BaseModel):
    key: str = Field(..., max_length=255, description="Medical role's key")


class Name(BaseModel, Generic[OptStrT]):
    name: OptStrT = Field(..., max_length=255, description="Medical role's name")


class MedicalRoleId(BaseModel):
    medical_role_id: int = Field(..., ge=1, description="Medical role's id")


class MedicalRoleIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdMedicalRoleIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDMedicalRoleIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


class CodeMedicalRoleIdentifier(Identifier[Literal[IdentifierType.CODE], str]):
    type: Annotated[
        Literal[IdentifierType.CODE],
        Field(IdentifierType.CODE, description="Identifier's type"),
    ] = IdentifierType.CODE
    value: Annotated[str, Field(..., description="Identifier's value", max_length=20)]


class KeyMedicalRoleIdentifier(Identifier[Literal[IdentifierType.KEY], str]):
    type: Annotated[
        Literal[IdentifierType.KEY],
        Field(IdentifierType.KEY, description="Identifier's type"),
    ] = IdentifierType.KEY
    value: Annotated[str, Field(..., description="Identifier's value", max_length=255)]


class NameMedicalRoleIdentifier(Identifier[Literal[IdentifierType.NAME], str]):
    type: Annotated[
        Literal[IdentifierType.NAME],
        Field(IdentifierType.NAME, description="Identifier's type"),
    ] = IdentifierType.NAME
    value: Annotated[str, Field(..., description="Identifier's value", max_length=255)]


AnyMedicalRoleIdentifier = (
    MedicalRoleIdentifier
    | IdMedicalRoleIdentifier
    | UUIDMedicalRoleIdentifier
    | CodeMedicalRoleIdentifier
    | KeyMedicalRoleIdentifier
    | NameMedicalRoleIdentifier
)


def is_id_identifier(
    identifier: AnyMedicalRoleIdentifier,
) -> TypeGuard[IdMedicalRoleIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyMedicalRoleIdentifier,
) -> TypeGuard[UUIDMedicalRoleIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)


def is_code_identifier(
    identifier: AnyMedicalRoleIdentifier,
) -> TypeGuard[CodeMedicalRoleIdentifier]:
    return identifier.type is IdentifierType.CODE and isinstance(identifier.value, str)


def is_key_identifier(
    identifier: AnyMedicalRoleIdentifier,
) -> TypeGuard[KeyMedicalRoleIdentifier]:
    return identifier.type is IdentifierType.KEY and isinstance(identifier.value, str)


def is_name_identifier(
    identifier: AnyMedicalRoleIdentifier,
) -> TypeGuard[NameMedicalRoleIdentifier]:
    return identifier.type is IdentifierType.NAME and isinstance(identifier.value, str)
