from territories_dashboard_lib.indicators_lib.enums import MeshLevel
from territories_dashboard_lib.indicators_lib.query.utils import run_custom_query

from .models import Dashboard


def get_territory_meshes(territory_id: str, territory_mesh: MeshLevel):
    current_reg = None
    current_dep = None
    current_epci = None
    current_com = None
    if territory_mesh != MeshLevel.fr:
        query = f"""
        SELECT
            name_reg,
            name_dep,
            name_epci,
            name_com
        FROM arborescence_geo
        WHERE code_{territory_mesh} = '{territory_id}'
        LIMIT 1
        """
        row = run_custom_query(query)[0]
        if territory_mesh in [
            MeshLevel.reg,
            MeshLevel.dep,
            MeshLevel.epci,
            MeshLevel.com,
        ]:
            current_reg = row["name_reg"]
        if territory_mesh in [
            MeshLevel.dep,
            MeshLevel.epci,
            MeshLevel.com,
        ]:
            current_dep = row["name_dep"]
        if territory_mesh in [
            MeshLevel.epci,
            MeshLevel.com,
        ]:
            current_epci = row["name_epci"]
        if territory_mesh in [
            MeshLevel.com,
        ]:
            current_com = row["name_com"]
    territory_meshes = {
        MeshLevel.reg: current_reg,
        MeshLevel.dep: current_dep,
        MeshLevel.epci: current_epci,
        MeshLevel.com: current_com,
    }
    return territory_meshes


def make_filter(dashboard: Dashboard, territory_id: str, territory_mesh: MeshLevel):
    if dashboard.filters.count() == 0:
        return None
    territory_meshes = get_territory_meshes(territory_id, territory_mesh)
    filters = []
    for f in dashboard.filters.all():
        value = territory_meshes.get(f.mesh)
        if value:
            value = value.replace("'", "!'")  # RISON escape
            filter_string = f"""NATIVE_FILTER-{f.superset_id}:(__cache:(label:'{value}',validateStatus:!f,value:!('{value}')),extraFormData:(filters:!((col:{f.superset_col},op:IN,val:!('{value}')))),filterState:(label:'{value}',validateStatus:!f,value:!('{value}')),id:NATIVE_FILTER-{f.superset_id},ownState:())"""
            filters.append(filter_string)
    if not filters:
        return None
    return f"""({",".join(filters)})"""
