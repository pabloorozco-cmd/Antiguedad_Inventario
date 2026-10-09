"""Catálogos operativos de ARGOS Guatemala."""

from __future__ import annotations

from collections import OrderedDict

TIMEZONE = "America/Guatemala"
APP_TITLE = "ARGOS | Inventario inteligente"

WAREHOUSE_USERS: dict[str, tuple[str, ...]] = OrderedDict(
    {
        "Morales 2": (
            "Edwin Ramírez",
        ),
        "Morales": (
            "Jefrie Anthony Sandoval Estrada",
            "Oscar Ovidio Molina Montesinos",
            "Henry Geovanni Ramírez",
            "Mateo Adonai Santiago",
            "Sergio Gustavo Pascual",
            "Julio Cesar Hernández",
            "Lester Iván Alvarado López",
        ),
        "Bárcenas": (
            "Pedro Chajón",
            "Herbert Estuardo Méndez Paiz",
            "Edsson Alexander Vargas Puluc",
            "Emerson Alexander Chavarria Zamora",
        ),
    }
)

SUPERVISOR_NAME = "Rudy Anavisca"
SUPERVISOR_ACCESS = "Supervisión"

PRODUCTS = ("UNO", "ECO", "GU", "HE", "ECO PL", "UNO PL", "GU PL")

# Etiquetas operativas mostradas en la interfaz; no reemplazan logos oficiales.
PRODUCT_STYLES = {
    "UNO": {"background": "#B93E4A", "foreground": "#FFFFFF"},
    "ECO": {"background": "#43A12E", "foreground": "#FFFFFF"},
    "GU": {"background": "#A9C9F2", "foreground": "#071D49"},
    "HE": {"background": "#9299AC", "foreground": "#FFFFFF"},
    "ECO PL": {"background": "#E0F2D8", "foreground": "#246B20"},
    "UNO PL": {"background": "#F9E1E3", "foreground": "#912E3A"},
    "GU PL": {"background": "#DDEBFC", "foreground": "#315C93"},
}

SACKS_PER_PALLET = 40
MAX_SACKS_PER_ENTRY = 100_000
