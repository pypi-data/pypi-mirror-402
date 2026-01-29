from typing import List, Optional

from pydantic import BaseModel, field_validator

from territories_dashboard_lib.commons.types import TerritoryCode
from territories_dashboard_lib.indicators_lib.enums import MeshLevel
from territories_dashboard_lib.indicators_lib.payloads import SubMeshPayload


class GeoFeaturesPayload(SubMeshPayload):
    last: Optional[int] = None
    limit: Optional[int] = 1000
    feature: int


class MainTerritoryParams(BaseModel):
    geo_level: MeshLevel
    geo_id: List[TerritoryCode]

    @field_validator("geo_id", mode="before")
    def split_main_territories(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


class TerritoriesParams(BaseModel):
    mesh: MeshLevel
    territories: List[TerritoryCode]

    @field_validator("territories", mode="before")
    def split_main_territories(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


class TerritoryFeaturePayload(SubMeshPayload):
    codes: List[TerritoryCode] | None = None

    @field_validator("codes", mode="before")
    def split_codes(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


class SearchTerritoriesParams(BaseModel):
    mesh: MeshLevel
    search: str = ""
    offset: int = 0
