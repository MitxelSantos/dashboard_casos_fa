"""
Utilidades del dashboard de Fiebre Amarilla
"""

# ===== DATA PROCESSOR =====
from .data_processor import (
    excel_date_to_datetime,
    calculate_basic_metrics,
    verify_filtered_data_usage,
    debug_data_flow,
    handle_empty_area_filter_simple
)

# ===== RESPONSIVE UTILS =====
try:
    from .responsive import (
        init_responsive_utils,
        create_responsive_metric_cards,
        optimize_plotly_chart,
        create_responsive_dataframe,
    )
    RESPONSIVE_AVAILABLE = True
except ImportError:
    RESPONSIVE_AVAILABLE = False

# ===== MAP INTERACTIONS =====
try:
    from .map_interactions import (
        detect_map_click,
        apply_map_filter,
        create_map_navigation_buttons,
        process_map_interaction,
        create_simple_popup,
    )
    MAP_INTERACTIONS_AVAILABLE = True
except ImportError:
    MAP_INTERACTIONS_AVAILABLE = False

# ===== SHAPEFILE LOADER =====
try:
    from .shapefile_loader import (
        load_tolima_shapefiles,
        check_shapefiles_availability,
        show_shapefile_setup_instructions,
    )
    SHAPEFILE_LOADER_AVAILABLE = True
except ImportError:
    SHAPEFILE_LOADER_AVAILABLE = False

# ===== EXPORTS LIMPIOS =====
__all__ = [
    # Data processor (CORE - siempre disponible)
    "excel_date_to_datetime",
    "calculate_basic_metrics", 
    "verify_filtered_data_usage",
    "debug_data_flow",
]

# Agregar responsive si disponible
if RESPONSIVE_AVAILABLE:
    __all__.extend([
        "init_responsive_utils",
        "create_responsive_metric_cards", 
        "optimize_plotly_chart",
        "create_responsive_dataframe",
    ])

# Agregar map interactions si disponible
if MAP_INTERACTIONS_AVAILABLE:
    __all__.extend([
        "detect_map_click",
        "apply_map_filter",
        "create_map_navigation_buttons",
        "process_map_interaction", 
        "create_simple_popup",
    ])

# Agregar shapefile loader si disponible
if SHAPEFILE_LOADER_AVAILABLE:
    __all__.extend([
        "load_tolima_shapefiles",
        "check_shapefiles_availability",
        "show_shapefile_setup_instructions",
    ])

# ===== INFO DE DISPONIBILIDAD =====
def get_utils_info():
    """Retorna información de utilidades disponibles."""
    return {
        "data_processor": True,  # Siempre disponible
        "responsive": RESPONSIVE_AVAILABLE,
        "map_interactions": MAP_INTERACTIONS_AVAILABLE, 
        "shapefile_loader": SHAPEFILE_LOADER_AVAILABLE,
        "total_functions": len(__all__),
    }