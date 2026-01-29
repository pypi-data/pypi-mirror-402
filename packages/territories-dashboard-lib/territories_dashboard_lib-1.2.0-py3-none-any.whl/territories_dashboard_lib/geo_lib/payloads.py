from typing import List, Optional

from pydantic import BaseModel, field_validator

from territories_dashboard_lib.commons.types import TerritoryCode
from territories_dashboard_lib.indicators_lib.enums import MeshLevel
from territories_dashboard_lib.indicators_lib.payloads import SubMeshPayload


def split_comma_separated(v):
    """Split comma-separated strings into a list, handling both strings and lists."""
    if isinstance(v, str):
        return v.split(",")
    if isinstance(v, list):
        result = []
        for item in v:
            if isinstance(item, str) and "," in item:
                result.extend(item.split(","))
            else:
                result.append(item)
        return result
    return v


class GeoFeaturesPayload(SubMeshPayload):
    last: Optional[int] = None
    limit: Optional[int] = 1000
    feature: int


class MainTerritoryParams(BaseModel):
    geo_level: MeshLevel
    geo_id: List[TerritoryCode]

    @field_validator("geo_id", mode="before")
    @classmethod
    def split_geo_id(cls, v):
        return split_comma_separated(v)


class TerritoriesParams(BaseModel):
    mesh: MeshLevel
    territories: List[TerritoryCode]

    @field_validator("territories", mode="before")
    @classmethod
    def split_territories(cls, v):
        return split_comma_separated(v)


class TerritoryFeaturePayload(SubMeshPayload):
    codes: List[TerritoryCode] | None = None

    @field_validator("codes", mode="before")
    @classmethod
    def split_codes(cls, v):
        return split_comma_separated(v)


class SearchTerritoriesParams(BaseModel):
    mesh: MeshLevel
    search: str = ""
    offset: int = 0
