from territories_dashboard_lib.indicators_lib.enums import (
    ALL_MESHES_ABSOLUTE,
    MESHES_ORDERED_FOR_PRESENTATION,
)
from territories_dashboard_lib.website_lib.models import MainConf


class MissingMainConf(Exception):
    def __init__(self):
        super().__init__()
        self.message = "Configuration principale du site (MainConf) manquante, veuillez la créer via le backoffice ou le shell."


def get_meshes_for_current_project():
    main_conf = get_main_conf()
    return [m for m in ALL_MESHES_ABSOLUTE if m in main_conf.meshes]


def get_ordered_meshes_for_current_project():
    main_conf = get_main_conf()
    return [m for m in MESHES_ORDERED_FOR_PRESENTATION if m in main_conf.meshes]


def get_main_conf():
    main_conf = MainConf.objects.first()
    if main_conf is None:
        raise MissingMainConf
    return main_conf
