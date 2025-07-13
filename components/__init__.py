"""
Componentes reutilizables
"""

# ===== SIDEBAR (OPTIMIZADO) =====
from .sidebar import create_sidebar, init_responsive_sidebar, add_copyright

# ===== FILTERS (OPTIMIZADO) =====
from .filters import (
    create_unified_filter_system,
    create_hierarchical_filters,
    create_temporal_filters,
    create_advanced_filters,
    apply_all_filters,
    reset_all_filters,
    show_active_filters,
)

# ===== EXPORTS LIMPIOS =====
__all__ = [
    # Sidebar
    "create_sidebar",
    "init_responsive_sidebar", 
    "add_copyright",
    
    # Filters (usando nombres correctos después de optimización)
    "create_unified_filter_system",
    "create_hierarchical_filters",
    "create_temporal_filters",
    "create_advanced_filters",
    "apply_all_filters",
    "reset_all_filters",
    "show_active_filters",
]

# Alias para compatibilidad con código existente
create_complete_filter_system = create_unified_filter_system
create_complete_filter_system_with_maps = create_unified_filter_system