import json
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, Self, Sequence, Type, TypeVar, overload
from uuid import UUID
from nexo.enums.medical import MedicalRole, ListOfMedicalRoles
from nexo.enums.status import (
    DataStatus,
    ListOfDataStatuses,
    SimpleDataStatusMixin,
    FULL_DATA_STATUSES,
)
from nexo.schemas.mixins.filter import ListOfDateFilters, convert as convert_filter
from nexo.schemas.mixins.general import Codes, Order
from nexo.schemas.mixins.hierarchy import IsRoot, IsParent, IsChild, IsLeaf
from nexo.schemas.mixins.identity import (
    IdentifierMixin,
    DataIdentifier,
    Ids,
    UUIDs,
    ParentId,
    ParentIds,
    Keys,
    Names,
)
from nexo.schemas.mixins.sort import ListOfSortColumns, convert as convert_sort
from nexo.schemas.mixins.timestamp import DataTimestamp
from nexo.schemas.operation.enums import ResourceOperationStatusUpdateType
from nexo.schemas.pagination import Limit
from nexo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from nexo.types.boolean import OptBool
from nexo.types.dict import StrToAnyDict
from nexo.types.integer import OptInt, OptListOfInts
from nexo.types.string import OptListOfStrs, OptStr, ManyStrs
from nexo.types.uuid import OptListOfUUIDs
from ..enums.medical_role import IdentifierType
from ..mixins.medical_role import Code, Key, Name, MedicalRoleIdentifier
from ..types.medical_role import IdentifierValueType


class CreateData(
    Name[str],
    Key,
    Code[str],
    Order[OptInt],
    ParentId[OptInt],
):
    pass


class CreateDataMixin(BaseModel):
    data: CreateData = Field(..., description="Create data")


class CreateParameter(
    CreateDataMixin,
):
    pass


class ReadMultipleSpecializationsParameter(
    ReadPaginatedMultipleParameter,
    Names[OptListOfStrs],
    Keys[OptListOfStrs],
    Codes[OptListOfStrs],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
    ParentId[int],
):
    parent_id: Annotated[int, Field(..., description="Parent's ID", ge=1)]
    ids: Annotated[OptListOfInts, Field(None, description="Ids")] = None
    uuids: Annotated[OptListOfUUIDs, Field(None, description="UUIDs")] = None
    codes: Annotated[OptListOfStrs, Field(None, description="Codes")] = None
    keys: Annotated[OptListOfStrs, Field(None, description="Keys")] = None
    names: Annotated[OptListOfStrs, Field(None, description="Names")] = None

    @classmethod
    def new(
        cls,
        parent_id: int,
        ids: OptListOfInts = None,
        uuids: OptListOfUUIDs = None,
        codes: OptListOfStrs = None,
        keys: OptListOfStrs = None,
        names: OptListOfStrs = None,
        date_filters: ListOfDateFilters = ListOfDateFilters(),
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        search: OptStr = None,
        sort_columns: ListOfSortColumns = ListOfSortColumns(),
        page: int = 1,
        limit: Limit = Limit.LIM_10,
        use_cache: bool = True,
    ) -> Self:
        return cls(
            parent_id=parent_id,
            ids=ids,
            uuids=uuids,
            codes=codes,
            keys=keys,
            names=names,
            date_filters=date_filters,
            statuses=statuses,
            search=search,
            sort_columns=sort_columns,
            page=page,
            limit=limit,
            use_cache=use_cache,
        )

    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "keys",
            "names",
            "search",
            "page",
            "limit",
            "use_cache",
        }

    def to_query_params(self) -> StrToAnyDict:
        params = self.model_dump(
            mode="json", include=self._query_param_fields, exclude_none=True
        )
        params["filters"] = convert_filter(self.date_filters)
        params["sorts"] = convert_sort(self.sort_columns)
        params = {k: v for k, v in params.items()}
        return params


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    Names[OptListOfStrs],
    Keys[OptListOfStrs],
    Codes[OptListOfStrs],
    IsLeaf[OptBool],
    IsChild[OptBool],
    IsParent[OptBool],
    IsRoot[OptBool],
    ParentIds[OptListOfInts],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
):
    ids: Annotated[OptListOfInts, Field(None, description="Ids")] = None
    uuids: Annotated[OptListOfUUIDs, Field(None, description="UUIDs")] = None
    parent_ids: Annotated[OptListOfInts, Field(None, description="Parent's IDs")] = None
    is_root: Annotated[OptBool, Field(None, description="Whether is root")] = None
    is_parent: Annotated[OptBool, Field(None, description="Whether is parent")] = None
    is_child: Annotated[OptBool, Field(None, description="Whether is child")] = None
    is_leaf: Annotated[OptBool, Field(None, description="Whether is leaf")] = None
    codes: Annotated[OptListOfStrs, Field(None, description="Codes")] = None
    keys: Annotated[OptListOfStrs, Field(None, description="Keys")] = None
    names: Annotated[OptListOfStrs, Field(None, description="Names")] = None

    @classmethod
    def new(
        cls,
        ids: OptListOfInts = None,
        uuids: OptListOfUUIDs = None,
        parent_ids: OptListOfInts = None,
        is_root: OptBool = None,
        is_parent: OptBool = None,
        is_child: OptBool = None,
        is_leaf: OptBool = None,
        codes: OptListOfStrs = None,
        keys: OptListOfStrs = None,
        names: OptListOfStrs = None,
        date_filters: ListOfDateFilters = ListOfDateFilters(),
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        search: OptStr = None,
        sort_columns: ListOfSortColumns = ListOfSortColumns(),
        page: int = 1,
        limit: Limit = Limit.LIM_10,
        use_cache: bool = True,
    ) -> Self:
        return cls(
            ids=ids,
            uuids=uuids,
            parent_ids=parent_ids,
            is_root=is_root,
            is_parent=is_parent,
            is_child=is_child,
            is_leaf=is_leaf,
            codes=codes,
            keys=keys,
            names=names,
            date_filters=date_filters,
            statuses=statuses,
            search=search,
            sort_columns=sort_columns,
            page=page,
            limit=limit,
            use_cache=use_cache,
        )

    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "parent_ids",
            "is_root",
            "is_parent",
            "is_child",
            "is_leaf",
            "statuses",
            "keys",
            "names",
            "search",
            "page",
            "limit",
            "use_cache",
        }

    def to_query_params(self) -> StrToAnyDict:
        params = self.model_dump(
            mode="json", include=self._query_param_fields, exclude_none=True
        )
        params["filters"] = convert_filter(self.date_filters)
        params["sorts"] = convert_sort(self.sort_columns)
        params = {k: v for k, v in params.items()}
        return params


class ReadSingleParameter(BaseReadSingleParameter[MedicalRoleIdentifier]):
    @classmethod
    def from_identifier(
        cls,
        identifier: MedicalRoleIdentifier,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(identifier=identifier, statuses=statuses, use_cache=use_cache)

    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.KEY, IdentifierType.NAME],
        identifier_value: str,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(
            identifier=MedicalRoleIdentifier(
                type=identifier_type, value=identifier_value
            ),
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache"}, exclude_none=True
        )


class FullUpdateData(
    Name[str],
    Code[str],
    Order[OptInt],
    ParentId[OptInt],
):
    pass


class PartialUpdateData(
    Name[OptStr],
    Code[OptStr],
    Order[OptInt],
    ParentId[OptInt],
):
    pass


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    UpdateDataMixin[UpdateDataT],
    IdentifierMixin[MedicalRoleIdentifier],
    Generic[UpdateDataT],
):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        data: UpdateDataT,
    ) -> "UpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        data: UpdateDataT,
    ) -> "UpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.KEY, IdentifierType.NAME],
        identifier_value: str,
        data: UpdateDataT,
    ) -> "UpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        data: UpdateDataT,
    ) -> "UpdateParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        data: UpdateDataT,
    ) -> "UpdateParameter":
        return cls(
            identifier=MedicalRoleIdentifier(
                type=identifier_type, value=identifier_value
            ),
            data=data,
        )


class StatusUpdateParameter(
    BaseStatusUpdateParameter[MedicalRoleIdentifier],
):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.KEY, IdentifierType.NAME],
        identifier_value: str,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter":
        return cls(
            identifier=MedicalRoleIdentifier(
                type=identifier_type, value=identifier_value
            ),
            type=type,
        )


class DeleteSingleParameter(BaseDeleteSingleParameter[MedicalRoleIdentifier]):
    @overload
    @classmethod
    def new(
        cls, identifier_type: Literal[IdentifierType.ID], identifier_value: int
    ) -> "DeleteSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls, identifier_type: Literal[IdentifierType.UUID], identifier_value: UUID
    ) -> "DeleteSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.KEY, IdentifierType.NAME],
        identifier_value: str,
    ) -> "DeleteSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls, identifier_type: IdentifierType, identifier_value: IdentifierValueType
    ) -> "DeleteSingleParameter": ...
    @classmethod
    def new(
        cls, identifier_type: IdentifierType, identifier_value: IdentifierValueType
    ) -> "DeleteSingleParameter":
        return cls(
            identifier=MedicalRoleIdentifier(
                type=identifier_type, value=identifier_value
            )
        )


class BaseMedicalRoleSchema(
    Name[str],
    Key,
    Code[str],
    Order[OptInt],
    ParentId[OptInt],
):
    pass


class StandardMedicalRoleSchema(
    BaseMedicalRoleSchema,
    SimpleDataStatusMixin[DataStatus],
    DataIdentifier,
):
    @property
    def _identifiers(self) -> tuple[tuple[IdentifierType, IdentifierValueType], ...]:
        return (
            (IdentifierType.ID, self.id),
            (IdentifierType.UUID, str(self.uuid)),
            (IdentifierType.KEY, self.key),
            (IdentifierType.NAME, self.name),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


OptStandardMedicalRoleSchema = StandardMedicalRoleSchema | None
ListOfStandardMedicalRoleSchemas = list[StandardMedicalRoleSchema]
SeqOfStandardMedicalRoleSchemas = Sequence[StandardMedicalRoleSchema]

KeyOrStandardSchema = MedicalRole | StandardMedicalRoleSchema
OptKeyOrStandardSchema = KeyOrStandardSchema | None


class FullMedicalRoleSchema(
    BaseMedicalRoleSchema,
    SimpleDataStatusMixin[DataStatus],
    DataTimestamp,
    DataIdentifier,
):
    @property
    def _identifiers(self) -> tuple[tuple[IdentifierType, IdentifierValueType], ...]:
        return (
            (IdentifierType.ID, self.id),
            (IdentifierType.UUID, str(self.uuid)),
            (IdentifierType.KEY, self.key),
            (IdentifierType.NAME, self.name),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


OptFullMedicalRoleSchema = FullMedicalRoleSchema | None
ListOfFullMedicalRoleSchemas = list[FullMedicalRoleSchema]
SeqOfFullMedicalRoleSchemas = Sequence[FullMedicalRoleSchema]

KeyOrFullSchema = MedicalRole | FullMedicalRoleSchema
OptKeyOrFullSchema = KeyOrFullSchema | None


AnyMedicalRoleSchemaType = Type[StandardMedicalRoleSchema] | Type[FullMedicalRoleSchema]


# Medical Role Schemas
AnyMedicalRoleSchema = StandardMedicalRoleSchema | FullMedicalRoleSchema
MedicalRoleSchemaT = TypeVar("MedicalRoleSchemaT", bound=AnyMedicalRoleSchema)

OptAnyMedicalRoleSchema = AnyMedicalRoleSchema | None
OptMedicalRoleSchemaT = TypeVar("OptMedicalRoleSchemaT", bound=OptAnyMedicalRoleSchema)

ListOfAnyMedicalRoleSchemas = (
    ListOfStandardMedicalRoleSchemas | ListOfFullMedicalRoleSchemas
)
ListOfAnyMedicalRoleSchemasT = TypeVar(
    "ListOfAnyMedicalRoleSchemasT", bound=ListOfAnyMedicalRoleSchemas
)

OptListOfAnyMedicalRoleSchemas = ListOfAnyMedicalRoleSchemas | None
OptListOfAnyMedicalRoleSchemasT = TypeVar(
    "OptListOfAnyMedicalRoleSchemasT", bound=OptListOfAnyMedicalRoleSchemas
)


# Medical Role key and Schemas
AnyMedicalRole = MedicalRole | AnyMedicalRoleSchema
AnyMedicalRoleT = TypeVar("AnyMedicalRoleT", bound=AnyMedicalRole)

OptAnyMedicalRole = AnyMedicalRole | None
OptAnyMedicalRoleT = TypeVar("OptAnyMedicalRoleT", bound=OptAnyMedicalRole)

ListOfAnyMedicalRoles = ListOfMedicalRoles | ListOfAnyMedicalRoleSchemas
ListOfAnyMedicalRolesT = TypeVar("ListOfAnyMedicalRolesT", bound=ListOfAnyMedicalRoles)

OptListOfAnyMedicalRoles = ListOfAnyMedicalRoles | None
OptListOfAnyMedicalRolesT = TypeVar(
    "OptListOfAnyMedicalRolesT", bound=OptListOfAnyMedicalRoles
)


class SimpleMedicalRoleMixin(BaseModel, Generic[OptAnyMedicalRoleT]):
    role: OptAnyMedicalRoleT = Field(..., description="Medical role")


class FullMedicalRoleMixin(BaseModel, Generic[OptAnyMedicalRoleT]):
    medical_role: OptAnyMedicalRoleT = Field(..., description="Medical role")


class SimpleMedicalRolesMixin(BaseModel, Generic[OptListOfAnyMedicalRolesT]):
    roles: OptListOfAnyMedicalRolesT = Field(..., description="Medical roles")


class FullMedicalRolesMixin(BaseModel, Generic[OptListOfAnyMedicalRolesT]):
    medical_roles: OptListOfAnyMedicalRolesT = Field(..., description="Medical roles")
