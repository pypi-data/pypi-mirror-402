from territories_dashboard_lib.indicators_lib.payloads import Territory

from ..enums import FRANCE_DB_VALUES, MeshLevel
from ..models import AggregationFunctions, Indicator
from .utils import format_sql_codes, get_breakdown_dimension, run_custom_query


def get_mesh_column_name(mesh: MeshLevel):
    return f"code_{mesh}"


def get_sub_territories(
    *,
    submesh: MeshLevel,
    territory: Territory = None,
    with_center=False,
    codes: list[str] = None,
):
    """
    Récupère une liste des territoires appartenant à un territoire parent.
    params:
        submesh: maille des sous-territoires à récupérer
        territory: territoire parent des sous-territoires
        with_center: si True, ajoute le centre de chaque territoire
        codes: codes des sous-territoires à récupérer, peut-être utilisé en absence du territoire parent
    """
    parent_mesh_join = ""
    condition = ""
    if territory is None and codes:
        condition = f"WHERE arbo.code IN {format_sql_codes(codes)}"
    elif territory and submesh == territory.mesh:
        condition = f"WHERE arbo.code IN {territory.sql_codes}"
    elif territory:
        parent_mesh_join = f"JOIN arbo_{territory.mesh}_{submesh} AS j ON j.{submesh}=arbo.code AND j.{territory.mesh} IN {territory.sql_codes}"

    center = ""
    contours_join = ""
    if with_center:
        center = ", ST_ASGEOJSON(ST_CENTROID(contours.geometry)) as center"
        contours_join = f"JOIN contours_simplified_{submesh} as contours ON arbo.code = contours.code"

    query = f"""
        SELECT DISTINCT
            arbo.code,
            arbo.name
            {center}
        FROM arbo_{submesh} AS arbo
        {parent_mesh_join}
        {contours_join}
        {condition}
    """
    return run_custom_query(query)


def get_last_year(indicator, mesh):
    query = f""" SELECT MAX(annee) as last_year FROM "{indicator.db_table_prefix}_{mesh}" """
    return run_custom_query(query)[0]["last_year"]


def generate_aggregate_query(indicator, territory, submesh, filters, slicer):
    query = f"""
    WITH annee_max AS
    (SELECT MAX(annee) FROM "{indicator.db_table_prefix}_{submesh}"),
    aggregat AS
    (
        SELECT
        {calculate_aggregate_values(indicator)}, indic.{slicer}
        FROM
        {get_values_for_indicator_territory_submesh(indicator=indicator, territory=territory, submesh=submesh)}
        {add_optional_filters(indicator, filters)}
        AND annee = (SELECT * FROM annee_max)
        GROUP BY (indic.{slicer})
    )
    """
    return query


def generate_aggregate_query_for_location(indicator, territory, submesh, filters):
    mesh_col = get_mesh_column_name(submesh)
    return generate_aggregate_query(indicator, territory, submesh, filters, mesh_col)


def add_optional_filters(indicator: Indicator, filters):
    condition = ""
    all_dimensions = [dimension.db_name for dimension in indicator.dimensions.all()]
    for dimension in all_dimensions:
        if filters and filters.get(dimension):
            filters_str = ", ".join(
                [f"'{value.replace("'", "''")}'" for value in filters.get(dimension)]
            )
            condition += f' AND indic."{dimension}" in ({filters_str}) '
    return condition


def get_values_for_indicator_territory_submesh(
    *,
    indicator: Indicator,
    territory: Territory,
    submesh: MeshLevel,
    flows: bool = False,
):
    mesh_col = get_mesh_column_name(submesh)
    if submesh == territory.mesh:
        arbo_join = f"""
        JOIN arbo_{submesh} arbo ON arbo.code = indic.{mesh_col} AND arbo.code IN {territory.sql_codes}
        """
    else:
        arbo_join = f"""
        JOIN arbo_{territory.mesh}_{submesh} j 
            ON j.{submesh} = indic.{mesh_col} AND j.{territory.mesh} IN {territory.sql_codes}
        JOIN arbo_{submesh} arbo
            ON arbo.code = indic.{mesh_col}
        """
    if flows:
        if submesh == territory.mesh:
            arbo_join = f"""
                JOIN arbo_{submesh} arbo1 ON arbo1.code = indic.{mesh_col}_1 AND arbo1.code IN {territory.sql_codes}

                JOIN arbo_{submesh} arbo2 ON arbo2.code = indic.{mesh_col}_2 AND arbo2.code IN {territory.sql_codes}
            """
        else:
            arbo_join = f"""
            JOIN arbo_{territory.mesh}_{submesh} j1 
                ON j1.{submesh} = indic.{mesh_col}_1 AND j1.{territory.mesh} IN {territory.sql_codes}
            JOIN arbo_{submesh} arbo1
                ON arbo1.code = indic.{mesh_col}_1

            JOIN arbo_{territory.mesh}_{submesh} j2
                ON j2.{submesh} = indic.{mesh_col}_2 AND j2.{territory.mesh} IN {territory.sql_codes}
            JOIN arbo_{submesh} arbo2
                ON arbo2.code = indic.{mesh_col}_2
            """

    return f"""
    "{indicator.table_name(submesh, flows=flows)}" indic
    {arbo_join}
    """


def calculate_aggregate_values(indicator, with_alternative=True):
    if not indicator.is_composite:
        return "SUM(valeur) as valeur"

    if indicator.aggregation_function == AggregationFunctions.DISCRETE_COMPONENT_2:
        sql = f"SUM(composante_1) / COALESCE(NULLIF(SUM(composante_2), 0), 1) * {indicator.aggregation_constant} as valeur"
        if with_alternative:
            sql += ", SUM(composante_1) as valeur_alternative"
        return sql
    breakdown_dimension = get_breakdown_dimension(indicator)
    breakdown_count = (
        f" * COUNT(DISTINCT({breakdown_dimension.db_name})) "
        if breakdown_dimension
        else ""
    )
    sql = f"SUM(composante_1) / COALESCE(NULLIF(SUM(composante_2), 0), 1) {breakdown_count} * {indicator.aggregation_constant} as valeur"
    if with_alternative:
        sql += ", SUM(composante_1) as valeur_alternative"
    return sql


def get_where_territory(territory):
    territory_id = (
        FRANCE_DB_VALUES[territory.id]
        if territory.mesh == MeshLevel.fr
        else territory.id
    )
    mesh_col = get_mesh_column_name(territory.mesh)
    return f""" "{mesh_col}" = '{territory_id}' """


def get_values_for_territory(indicator, territory, filters=None):
    value = calculate_aggregate_values(indicator)
    where_territory = get_where_territory(territory)
    query = f"""
        SELECT {value}, annee
        FROM "{indicator.db_table_prefix}_{territory.mesh}" as indic
        WHERE {where_territory}
        {add_optional_filters(indicator, filters)}
        GROUP BY annee
        ORDER BY annee DESC
    """
    return query


def get_territory_name(territory):
    query = f"""SELECT name FROM arbo_{territory.mesh} WHERE code IN {territory.sql_codes} LIMIT 1;"""
    results = run_custom_query(query)
    return results[0]["name"] if results else ""
