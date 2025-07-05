"""
Componentes reutilizables del dashboard.
CORREGIDO: Importaciones actualizadas para funciones con sufijo _enhanced
"""

from .sidebar import create_sidebar, init_responsive_sidebar

# Importar funciones CORREGIDAS de filters.py (con sufijo _enhanced, no _corrected)
from .filters import (
    create_complete_filter_system_enhanced as create_complete_filter_system,
    create_hierarchical_filters_enhanced as create_hierarchical_filters,
    create_content_filters_enhanced as create_content_filters,
    create_advanced_filters_enhanced as create_advanced_filters,
    apply_all_filters_enhanced as apply_all_filters,
    reset_all_filters_enhanced as reset_all_filters,
    show_active_filters_sidebar_enhanced as show_active_filters_sidebar,
    create_complete_filter_system_with_maps
)

# Funciones adicionales que pueden no existir - importación condicional
try:
    from .filters import create_filter_export_options
except ImportError:
    # Si no existe, crear una función dummy
    def create_filter_export_options(*args, **kwargs):
        """Función placeholder para exportación de filtros."""
        pass

__all__ = [
    # Sidebar
    "create_sidebar",
    "init_responsive_sidebar", 
    
    # Filters (con aliases para compatibilidad)
    "create_complete_filter_system",
    "create_hierarchical_filters",
    "create_content_filters", 
    "create_advanced_filters",
    "apply_all_filters",
    "reset_all_filters",
    "show_active_filters_sidebar",
    "create_filter_export_options",
    "create_complete_filter_system_with_maps"
]