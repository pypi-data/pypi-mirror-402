import json
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, Self, Sequence, Type, TypeVar, overload
from uuid import UUID
from nexo.enums.medical import MedicalService, ListOfMedicalServices
from nexo.enums.status import (
    DataStatus,
    ListOfDataStatuses,
    SimpleDataStatusMixin,
    FULL_DATA_STATUSES,
)
from nexo.schemas.mixins.filter import ListOfDateFilters, convert as convert_filter
from nexo.schemas.mixins.general import Order
from nexo.schemas.mixins.identity import (
    IdentifierMixin,
    DataIdentifier,
    Ids,
    UUIDs,
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
from nexo.types.dict import StrToAnyDict
from nexo.types.integer import OptInt, OptListOfInts
from nexo.types.string import OptListOfStrs, OptStr, ManyStrs
from nexo.types.uuid import OptListOfUUIDs
from ..enums.medical_service import IdentifierType
from ..mixins.medical_service import Key, Name, MedicalServiceIdentifier
from ..types.medical_service import IdentifierValueType


class CreateData(Name[str], Key, Order[OptInt]):
    pass


class CreateDataMixin(BaseModel):
    data: CreateData = Field(..., description="Create data")


class CreateParameter(
    CreateDataMixin,
):
    pass


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    Names[OptListOfStrs],
    Keys[OptListOfStrs],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
):
    ids: Annotated[OptListOfInts, Field(None, description="Ids")] = None
    uuids: Annotated[OptListOfUUIDs, Field(None, description="UUIDs")] = None
    keys: Annotated[OptListOfStrs, Field(None, description="Keys")] = None
    names: Annotated[OptListOfStrs, Field(None, description="Names")] = None

    @classmethod
    def new(
        cls,
        ids: OptListOfInts = None,
        uuids: OptListOfUUIDs = None,
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


class ReadSingleParameter(BaseReadSingleParameter[MedicalServiceIdentifier]):
    @classmethod
    def from_identifier(
        cls,
        identifier: MedicalServiceIdentifier,
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
            identifier=MedicalServiceIdentifier(
                type=identifier_type, value=identifier_value
            ),
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache"}, exclude_none=True
        )


class FullUpdateData(Name[str], Order[OptInt]):
    pass


class PartialUpdateData(Name[OptStr], Order[OptInt]):
    pass


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    UpdateDataMixin[UpdateDataT],
    IdentifierMixin[MedicalServiceIdentifier],
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
            identifier=MedicalServiceIdentifier(
                type=identifier_type, value=identifier_value
            ),
            data=data,
        )


class StatusUpdateParameter(
    BaseStatusUpdateParameter[MedicalServiceIdentifier],
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
            identifier=MedicalServiceIdentifier(
                type=identifier_type, value=identifier_value
            ),
            type=type,
        )


class DeleteSingleParameter(BaseDeleteSingleParameter[MedicalServiceIdentifier]):
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
            identifier=MedicalServiceIdentifier(
                type=identifier_type, value=identifier_value
            )
        )


class BaseMedicalServiceSchema(
    Name[str],
    Key,
    Order[OptInt],
):
    pass


class StandardMedicalServiceSchema(
    BaseMedicalServiceSchema,
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


OptStandardMedicalServiceSchema = StandardMedicalServiceSchema | None
ListOfStandardMedicalServiceSchemas = list[StandardMedicalServiceSchema]
SeqOfStandardMedicalServiceSchemas = Sequence[StandardMedicalServiceSchema]

KeyOrStandardSchema = MedicalService | StandardMedicalServiceSchema
OptKeyOrStandardSchema = KeyOrStandardSchema | None


class FullMedicalServiceSchema(
    BaseMedicalServiceSchema,
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


OptFullMedicalServiceSchema = FullMedicalServiceSchema | None
ListOfFullMedicalServiceSchemas = list[FullMedicalServiceSchema]
SeqOfFullMedicalServiceSchemas = Sequence[FullMedicalServiceSchema]

KeyOrFullSchema = MedicalService | FullMedicalServiceSchema
OptKeyOrFullSchema = KeyOrFullSchema | None


AnyMedicalServiceSchemaType = (
    Type[StandardMedicalServiceSchema] | Type[FullMedicalServiceSchema]
)


# Medical Service Schemas
AnyMedicalServiceSchema = StandardMedicalServiceSchema | FullMedicalServiceSchema
MedicalServiceSchemaT = TypeVar("MedicalServiceSchemaT", bound=AnyMedicalServiceSchema)

OptAnyMedicalServiceSchema = AnyMedicalServiceSchema | None
OptMedicalServiceSchemaT = TypeVar(
    "OptMedicalServiceSchemaT", bound=OptAnyMedicalServiceSchema
)

ListOfAnyMedicalServiceSchemas = (
    ListOfStandardMedicalServiceSchemas | ListOfFullMedicalServiceSchemas
)
ListOfAnyMedicalServiceSchemasT = TypeVar(
    "ListOfAnyMedicalServiceSchemasT", bound=ListOfAnyMedicalServiceSchemas
)

OptListOfAnyMedicalServiceSchemas = ListOfAnyMedicalServiceSchemas | None
OptListOfAnyMedicalServiceSchemasT = TypeVar(
    "OptListOfAnyMedicalServiceSchemasT", bound=OptListOfAnyMedicalServiceSchemas
)


# Medical Service key and Schemas
AnyMedicalService = MedicalService | AnyMedicalServiceSchema
AnyMedicalServiceT = TypeVar("AnyMedicalServiceT", bound=AnyMedicalService)

OptAnyMedicalService = AnyMedicalService | None
OptAnyMedicalServiceT = TypeVar("OptAnyMedicalServiceT", bound=OptAnyMedicalService)

ListOfAnyMedicalServices = ListOfMedicalServices | ListOfAnyMedicalServiceSchemas
ListOfAnyMedicalServicesT = TypeVar(
    "ListOfAnyMedicalServicesT", bound=ListOfAnyMedicalServices
)

OptListOfAnyMedicalServices = ListOfAnyMedicalServices | None
OptListOfAnyMedicalServicesT = TypeVar(
    "OptListOfAnyMedicalServicesT", bound=OptListOfAnyMedicalServices
)


class SimpleMedicalServiceMixin(BaseModel, Generic[OptAnyMedicalServiceT]):
    service: OptAnyMedicalServiceT = Field(..., description="Medical service")


class FullMedicalServiceMixin(BaseModel, Generic[OptAnyMedicalServiceT]):
    medical_service: OptAnyMedicalServiceT = Field(..., description="Medical service")


class SimpleMedicalServicesMixin(BaseModel, Generic[OptListOfAnyMedicalServicesT]):
    services: OptListOfAnyMedicalServicesT = Field(..., description="Medical services")


class FullMedicalServicesMixin(BaseModel, Generic[OptListOfAnyMedicalServicesT]):
    medical_services: OptListOfAnyMedicalServicesT = Field(
        ..., description="Medical services"
    )
