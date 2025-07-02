"""
Utilidades del dashboard de Fiebre Amarilla.
OPTIMIZADO: Solo exporta las funciones que realmente se usan en el proyecto.
"""

# Solo importar lo que realmente se usa en el proyecto
from .data_processor import (
    normalize_text,
    capitalize_names,
    excel_date_to_datetime,
    format_date_display,
    process_casos_dataframe,
    process_epizootias_dataframe,
    apply_filters_to_data,
    calculate_basic_metrics,
    get_unique_locations,
    create_summary_by_location,
    prepare_dataframe_for_display,
)

# Importaciones condicionales para responsive
try:
    from .responsive import (
        init_responsive_utils,
        create_responsive_metric_cards,
        optimize_plotly_chart,
        create_responsive_dataframe,
    )

    RESPONSIVE_UTILS_AVAILABLE = True
except ImportError:
    RESPONSIVE_UTILS_AVAILABLE = False

# Lista de exports actualizada - SOLO lo que se usa realmente
__all__ = [
    # Data processor (usado en app.py y vistas)
    "normalize_text",
    "capitalize_names",
    "excel_date_to_datetime",
    "format_date_display",
    "process_casos_dataframe",
    "process_epizootias_dataframe",
    "apply_filters_to_data",
    "calculate_basic_metrics",
    "get_unique_locations",
    "create_summary_by_location",
    "prepare_dataframe_for_display",
]

# Agregar responsive utils si están disponibles
if RESPONSIVE_UTILS_AVAILABLE:
    __all__.extend(
        [
            "init_responsive_utils",
            "create_responsive_metric_cards",
            "optimize_plotly_chart",
            "create_responsive_dataframe",
        ]
    )
