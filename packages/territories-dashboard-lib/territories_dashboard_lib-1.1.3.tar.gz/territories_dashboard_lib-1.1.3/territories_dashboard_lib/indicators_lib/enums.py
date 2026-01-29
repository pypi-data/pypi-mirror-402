from typing import List

from django.conf import settings
from django.db import models


class AggregationFunctions(models.TextChoices):
    DISCRETE_COMPONENT_2 = "discrete"
    REPEATED_COMPONENT_2 = "repeated"


class MeshLevel(models.TextChoices):
    fr = "fr"
    reg = "reg"
    dep = "dep"
    epci = "epci"
    com = "com"
    aom = "aom"


STANDARD_MESHES = [
    MeshLevel.fr,
    MeshLevel.reg,
    MeshLevel.dep,
    MeshLevel.epci,
    MeshLevel.com,
]

ALL_MESHES_ABSOLUTE = [
    MeshLevel.fr,
    MeshLevel.reg,
    MeshLevel.dep,
    MeshLevel.aom,
    MeshLevel.epci,
    MeshLevel.com,
]


MESHES_ORDERED_FOR_PRESENTATION = [
    MeshLevel.fr,
    MeshLevel.reg,
    MeshLevel.dep,
    MeshLevel.epci,
    MeshLevel.com,
    MeshLevel.aom,
]


def order_meshes_for_presentation(meshes: List[MeshLevel]) -> List[MeshLevel]:
    """
    Orders a list of MeshLevel values according to MESHES_ORDERED_FOR_PRESENTATION.
    """
    order_index = {mesh: i for i, mesh in enumerate(MESHES_ORDERED_FOR_PRESENTATION)}
    return sorted(meshes, key=lambda mesh: order_index[mesh])


class FranceGeoLevel(models.TextChoices):
    All = "FR0,FR1,FR2"
    METRO = "FR0,FR1"
    METRO_HORS_IDF = "FR0"


FRANCE_GEOLEVEL_TITLES = {
    FranceGeoLevel.All: "France entière",
    FranceGeoLevel.METRO: "France métropolitaine",
    FranceGeoLevel.METRO_HORS_IDF: "France métropolitaine hors IDF",
}

FRANCE_DB_VALUES = {
    FranceGeoLevel.All: "FR_TOT",
    FranceGeoLevel.METRO: "FR_METRO",
    FranceGeoLevel.METRO_HORS_IDF: "FR_METRO_HORS_IDF",
}


DEFAULT_MESH = MeshLevel.reg

MESHES_SHORT_TITLES = {
    MeshLevel.fr: "France",
    MeshLevel.reg: "Région",
    MeshLevel.dep: "Département",
    MeshLevel.epci: "Intercommunalité",
    MeshLevel.com: "Commune",
    MeshLevel.aom: "AOM",
}

MESHES_LONG_TITLES = {
    MeshLevel.fr: "France",
    MeshLevel.reg: "Région",
    MeshLevel.dep: "Département",
    MeshLevel.epci: "Intercommunalité",
    MeshLevel.com: "Commune",
    MeshLevel.aom: "Autorité Organisatrice de la Mobilité",
}


def get_miminum_mesh():
    try:
        town_mesh_is_disabled = settings.DISABLE_TOWN_MESH
        return MeshLevel.epci if town_mesh_is_disabled else MeshLevel.com
    except AttributeError:
        return MeshLevel.com


def get_allow_same_mesh():
    try:
        return bool(settings.ALLOW_SAME_MESH)
    except AttributeError:
        return False
