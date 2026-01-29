from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier
from nexo.types.string import OptStrT
from ..enums.medical_service import IdentifierType
from ..types.medical_service import IdentifierValueType


class Key(BaseModel):
    key: str = Field(..., max_length=20, description="Medical service's key")


class Name(BaseModel, Generic[OptStrT]):
    name: OptStrT = Field(..., max_length=20, description="Medical service's name")


class MedicalServiceIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdMedicalServiceIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDMedicalServiceIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


class KeyMedicalServiceIdentifier(Identifier[Literal[IdentifierType.KEY], str]):
    type: Annotated[
        Literal[IdentifierType.KEY],
        Field(IdentifierType.KEY, description="Identifier's type"),
    ] = IdentifierType.KEY
    value: Annotated[str, Field(..., description="Identifier's value", max_length=20)]


class NameMedicalServiceIdentifier(Identifier[Literal[IdentifierType.NAME], str]):
    type: Annotated[
        Literal[IdentifierType.NAME],
        Field(IdentifierType.NAME, description="Identifier's type"),
    ] = IdentifierType.NAME
    value: Annotated[str, Field(..., description="Identifier's value", max_length=20)]


AnyMedicalServiceIdentifier = (
    MedicalServiceIdentifier
    | IdMedicalServiceIdentifier
    | UUIDMedicalServiceIdentifier
    | KeyMedicalServiceIdentifier
    | NameMedicalServiceIdentifier
)


def is_id_identifier(
    identifier: AnyMedicalServiceIdentifier,
) -> TypeGuard[IdMedicalServiceIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyMedicalServiceIdentifier,
) -> TypeGuard[UUIDMedicalServiceIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)


def is_key_identifier(
    identifier: AnyMedicalServiceIdentifier,
) -> TypeGuard[KeyMedicalServiceIdentifier]:
    return identifier.type is IdentifierType.KEY and isinstance(identifier.value, str)


def is_name_identifier(
    identifier: AnyMedicalServiceIdentifier,
) -> TypeGuard[NameMedicalServiceIdentifier]:
    return identifier.type is IdentifierType.NAME and isinstance(identifier.value, str)
