from django.db import models

from territories_dashboard_lib.commons.models import CommonModel
from territories_dashboard_lib.indicators_lib.models import Indicator

from .enums import GeoFeatureType


class GeoFeature(CommonModel):
    name = models.TextField(
        verbose_name="Nom de la table en base",
        help_text="attention le nom doit être exactement le même que celui en base.",
    )
    title = models.TextField(verbose_name="Titre à afficher", default="à compléter")
    unite = models.TextField(verbose_name="Unité au pluriel")
    indicator = models.ForeignKey(
        Indicator,
        related_name="geo_features",
        on_delete=models.CASCADE,
        help_text="Cette donnée géographique sera ajoutée à la carte de l'indicateur.",
    )
    geo_type = models.TextField(
        choices=GeoFeatureType.choices,
        default=GeoFeatureType.point,
        verbose_name="Type de géométrie",
    )
    point_icon_svg = models.TextField(
        blank=True,
        null=True,
        verbose_name="Icone des points",
        help_text="Icone SVG a utilisé pour les points.<br/>Laisser vide pour les autres types de géométrie.<br/>Veuillez charger un fichier provenant des <a href='/'>Material Icons</a> de Google.",
    )
    color = models.TextField(
        default="#000000",
        verbose_name="Couleur",
        help_text="Couleur des données sur la date, à renseigner au format hexadécimal, par exemple: '#05B2F9'",
    )
    show_on_fr_level = models.BooleanField(
        default=True,
        verbose_name="Afficher au niveau France entière",
        help_text="Décochez si la quantité de données est trop importante pour le niveau France entière.",
    )
    color_column = models.TextField(
        blank=True,
        null=True,
        verbose_name="Colonne de la couleur",
        help_text="Optionnel. Nom de la colonne qui définit une couleur par point. Les valeurs de la colonne doivent être sous le format #ffffff (hexadecimale). Si renseigné, le champ 'color' ne sera pas utilisé. Seulement pour les points.",
    )
    size_column = models.TextField(
        blank=True,
        null=True,
        verbose_name="Colonne de la taille",
        help_text="Optionnel. Nom de la colonne qui définit une taille par point. Les valeurs de la colonne doivent être 'sm' (small) ou 'md' (medium). Seulement pour les points.",
    )
    legend = models.TextField(
        blank=True,
        null=True,
        verbose_name="Légende",
        help_text="""Si les points sur la carte ont une couleur ou une taille différente par point, veuillez indiquer une légende dans ce champ.<br/>
        Le format est le suivant :<br/>
        <ul>
            <li>
                Chaque ligne correspond à une ligne de la légende.
            </li>
            <li>
                Vous pouvez commencez une ligne avec un icone du point selon une couleur et une taille précise.<br/>
                Dans ce cas commencez la ligne par le format suivant : "icone(couleur:#000000,taille:sm)"<br/>
                Utilisez un code couleur hexadécimal, ou bien "couleur:nulle" pour ne pas mettre de couleur.<br/>
                Les deux valeurs possibles pour la taille sont : "sm" et "md".<br/>
                <i>Exemple:</i> "icone(couleur:nulle,taille:md) Stationnement avec capacité > 20 places"
            </li>
            <li>
                Vous pouvez commencer une ligne par un carré de couleur.<br/>
                Le format est : "couleur(#000000)"<br/>
                <i>Exemple</i> "couleur(#ff00ff) Stationnement payant"
            </li>
        </ul>""",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("indicator", "name")
        verbose_name = "Données de la carte"


class GeoElement(CommonModel):
    geo_feature = models.ForeignKey(
        GeoFeature, related_name="items", on_delete=models.CASCADE
    )
    name = models.TextField(verbose_name="Nom de la colonne en DB")
    label = models.TextField()
    filterable = models.BooleanField(default=True, verbose_name="Filtrable")
    linked_to_indicator = models.BooleanField(
        default=False,
        verbose_name="Relié aux filtres de l'indicateur",
        help_text="Si coché, le filtre de l'indicateur avec le même nom sere relié au filtre de la carte.",
    )
