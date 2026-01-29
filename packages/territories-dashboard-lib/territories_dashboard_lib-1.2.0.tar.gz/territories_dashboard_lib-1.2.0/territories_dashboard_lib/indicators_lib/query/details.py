from ..enums import MeshLevel
from ..models import Indicator
from ..payloads import Territory
from .commons import (
    add_optional_filters,
    calculate_aggregate_values,
    get_last_year,
    get_mesh_column_name,
    get_where_territory,
)
from .utils import get_breakdown_dimension, run_custom_query


def get_proportions_chart(indicator, territory, filters):
    where_territory = get_where_territory(territory)
    last_year = get_last_year(indicator, territory.mesh)
    breakdown_dimension = get_breakdown_dimension(indicator)

    query = f"""
    SELECT {calculate_aggregate_values(indicator, with_alternative=False)}, "{breakdown_dimension.db_name}" as dimension
    FROM "{indicator.db_table_prefix}_{territory.mesh}" as indic
    WHERE {where_territory} AND annee = {last_year}
    {add_optional_filters(indicator, filters)}
    GROUP BY "{breakdown_dimension.db_name}"
"""
    data = run_custom_query(query)
    filters_color = {f.db_name: f.color for f in breakdown_dimension.filters.all()}
    data_dict = {
        d["dimension"]: {
            "label": d["dimension"],
            "data": [d["valeur"]],
            "color": filters_color.get(d["dimension"]),
        }
        for d in data
    }
    breakdown_filters = filters[breakdown_dimension.db_name]
    sorted_data = (
        [data_dict[filter] for filter in breakdown_filters if filter in data_dict]
        if filters
        else list(data_dict.values())
    )
    return sorted_data


def get_values_for_submesh_territories(
    indicator: Indicator, submesh: MeshLevel, territory: Territory, filters
):
    submesh = submesh.lower()
    mesh_col = get_mesh_column_name(submesh)
    parent_territory_join = f"JOIN arbo_{territory.mesh}_{submesh} j ON j.{submesh} = arbo.code AND j.{territory.mesh} IN {territory.sql_codes}"
    if submesh == territory.mesh:
        parent_territory_join = f"AND arbo.code IN {territory.sql_codes}"
    query = f"""
    SELECT {calculate_aggregate_values(indicator)}, indic.{mesh_col} as geocode, arbo.name as geoname
    FROM "{indicator.db_table_prefix}_{submesh}" indic
    JOIN arbo_{submesh} arbo ON arbo.code = indic.{mesh_col}
    {parent_territory_join}
    {add_optional_filters(indicator, filters)}
    AND annee = (
        SELECT MAX(annee)
        FROM "{indicator.db_table_prefix}_{submesh}"
    )
    GROUP BY geocode, geoname
    """
    return run_custom_query(query)
