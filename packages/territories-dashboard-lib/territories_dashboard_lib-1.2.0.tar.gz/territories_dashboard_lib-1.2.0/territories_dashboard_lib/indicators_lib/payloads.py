from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field, model_validator

from territories_dashboard_lib.commons.types import MutualisedTerritoryCode, SQlName
from territories_dashboard_lib.indicators_lib.query.utils import format_sql_codes

from .enums import MeshLevel


class Territory(BaseModel):
    id: MutualisedTerritoryCode
    mesh: MeshLevel

    @property
    def sql_codes(territory) -> str:
        return format_sql_codes(territory.id.split(","))


def validate_territory(value):
    if value and "-" in value:
        return {"id": value.split("-")[0], "mesh": value.split("-")[1]}


class BasePayload(BaseModel):
    territory: Annotated[Territory, BeforeValidator(validate_territory)]


class SubMeshPayload(BasePayload):
    submesh: MeshLevel


class SubMeshOnlyPayload(SubMeshPayload):
    @model_validator(mode="after")
    def check_not_same_mesh(self):
        if self.submesh == self.territory.mesh:
            raise ValueError("submesh and territory mesh should not be equal")
        return self


class FlowsPayload(SubMeshPayload):
    prefix: SQlName
    dimension: SQlName | None = None


class ComparisonQueryPayload(SubMeshPayload):
    cmp_territory: Annotated[
        Territory, BeforeValidator(validate_territory), Field(alias="cmp-territory")
    ]


class OptionalComparisonQueryPayload(SubMeshPayload):
    cmp_territory: Annotated[
        Optional[Territory],
        BeforeValidator(validate_territory),
        Field(default=None, alias="cmp-territory"),
    ]


class IndicatorTablePayload(SubMeshPayload):
    column_order: SQlName | None = None
    column_order_flow: SQlName | None = None
    pagination: int = 1
    limit: int = 20
    previous_limit: int | None = None
    search: str | None = None
    year: int | None = None
    flows: bool | None = False
    focus: bool | None = False
