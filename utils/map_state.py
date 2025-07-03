"""
Utilidades para manejo de estado bidireccional entre mapas y filtros.
Sistema de sincronización para mapas interactivos del dashboard.
"""

import streamlit as st
import json
from typing import Dict, Optional, Tuple, Any


class MapState:
    """Gestor de estado para mapas interactivos."""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Inicializa el estado de la sesión para mapas."""
        if 'map_level' not in st.session_state:
            st.session_state.map_level = 'departamento'
        
        if 'map_selected_municipio' not in st.session_state:
            st.session_state.map_selected_municipio = None
        
        if 'map_selected_vereda' not in st.session_state:
            st.session_state.map_selected_vereda = None
        
        if 'map_zoom_coords' not in st.session_state:
            st.session_state.map_zoom_coords = None
        
        if 'map_filter_changed' not in st.session_state:
            st.session_state.map_filter_changed = False
    
    def set_departamento_view(self):
        """Establece vista departamental."""
        st.session_state.map_level = 'departamento'
        st.session_state.map_selected_municipio = None
        st.session_state.map_selected_vereda = None
        st.session_state.map_zoom_coords = None
        st.session_state.map_filter_changed = True
        
        # Actualizar filtros del sidebar
        if 'municipio_filter' in st.session_state:
            st.session_state.municipio_filter = 'Todos'
        if 'vereda_filter' in st.session_state:
            st.session_state.vereda_filter = 'Todas'
    
    def set_municipio_view(self, municipio_name: str, municipio_norm: str, coords: Optional[Tuple[float, float]] = None):
        """Establece vista municipal."""
        st.session_state.map_level = 'municipio'
        st.session_state.map_selected_municipio = {
            'display': municipio_name,
            'normalized': municipio_norm
        }
        st.session_state.map_selected_vereda = None
        st.session_state.map_zoom_coords = coords
        st.session_state.map_filter_changed = True
        
        # Actualizar filtros del sidebar
        if 'municipio_filter' in st.session_state:
            st.session_state.municipio_filter = municipio_name
        if 'vereda_filter' in st.session_state:
            st.session_state.vereda_filter = 'Todas'
    
    def set_vereda_view(self, vereda_name: str, vereda_norm: str, coords: Optional[Tuple[float, float]] = None):
        """Establece vista de vereda."""
        st.session_state.map_level = 'vereda'
        st.session_state.map_selected_vereda = {
            'display': vereda_name,
            'normalized': vereda_norm
        }
        st.session_state.map_zoom_coords = coords
        st.session_state.map_filter_changed = True
        
        # Actualizar filtros del sidebar
        if 'vereda_filter' in st.session_state:
            st.session_state.vereda_filter = vereda_name
    
    def get_current_level(self) -> str:
        """Obtiene el nivel actual del mapa."""
        return st.session_state.get('map_level', 'departamento')
    
    def get_selected_municipio(self) -> Optional[Dict[str, str]]:
        """Obtiene municipio seleccionado."""
        return st.session_state.get('map_selected_municipio')
    
    def get_selected_vereda(self) -> Optional[Dict[str, str]]:
        """Obtiene vereda seleccionada."""
        return st.session_state.get('map_selected_vereda')
    
    def get_zoom_coords(self) -> Optional[Tuple[float, float]]:
        """Obtiene coordenadas de zoom."""
        return st.session_state.get('map_zoom_coords')
    
    def sync_with_filters(self, filters: Dict[str, Any]):
        """Sincroniza estado del mapa con filtros del sidebar."""
        
        # Evitar loops infinitos
        if st.session_state.get('map_filter_changed', False):
            st.session_state.map_filter_changed = False
            return
        
        municipio_display = filters.get('municipio_display', 'Todos')
        vereda_display = filters.get('vereda_display', 'Todas')
        
        # Determinar nivel según filtros
        if vereda_display != 'Todas':
            if (not self.get_selected_vereda() or 
                self.get_selected_vereda()['display'] != vereda_display):
                
                vereda_norm = filters.get('vereda_normalizada', '')
                self.set_vereda_view(vereda_display, vereda_norm)
        
        elif municipio_display != 'Todos':
            if (not self.get_selected_municipio() or 
                self.get_selected_municipio()['display'] != municipio_display):
                
                municipio_norm = filters.get('municipio_normalizado', '')
                self.set_municipio_view(municipio_display, municipio_norm)
        
        else:
            if self.get_current_level() != 'departamento':
                self.set_departamento_view()
    
    def clear_filter_change_flag(self):
        """Limpia la bandera de cambio de filtros."""
        st.session_state.map_filter_changed = False


def process_map_click(click_data: Dict, data_filtered: Dict) -> Optional[Dict[str, Any]]:
    """
    Procesa clics en el mapa y retorna información de filtrado.
    
    Args:
        click_data: Datos del clic del mapa
        data_filtered: Datos filtrados actuales
    
    Returns:
        Diccionario con información de filtrado o None
    """
    if not click_data:
        return None
    
    # Extraer propiedades del objeto clicado
    try:
        properties = click_data.get('properties', {})
        
        # Identificar tipo de objeto clicado
        if 'MpNombre' in properties:  # Es un municipio
            municipio_name = properties['MpNombre']
            municipio_norm = properties.get('municipi_1', municipio_name)
            
            return {
                'type': 'municipio',
                'display': municipio_name,
                'normalized': municipio_norm,
                'action': 'filter_and_zoom'
            }
        
        elif 'NOMBRE_VER' in properties:  # Es una vereda
            vereda_name = properties['NOMBRE_VER']
            vereda_norm = properties.get('vereda_nor', vereda_name)
            
            return {
                'type': 'vereda',
                'display': vereda_name,
                'normalized': vereda_norm,
                'action': 'filter_and_zoom'
            }
    
    except Exception as e:
        st.error(f"Error procesando clic en mapa: {str(e)}")
    
    return None


def create_map_navigation_buttons(map_state: MapState, colors: Dict[str, str]):
    """Crea botones de navegación para el mapa."""
    
    current_level = map_state.get_current_level()
    selected_municipio = map_state.get_selected_municipio()
    selected_vereda = map_state.get_selected_vereda()
    
    # CSS para botones de navegación
    st.markdown(
        f"""
        <style>
        .map-nav-buttons {{
            display: flex;
            gap: 0.75rem;
            margin: 1rem 0;
            flex-wrap: wrap;
        }}
        
        .map-nav-btn {{
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']});
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 25px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            min-width: 120px;
            text-align: center;
        }}
        
        .map-nav-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}
        
        .map-nav-btn:active {{
            transform: translateY(0);
        }}
        
        .map-nav-btn-back {{
            background: linear-gradient(135deg, {colors['warning']}, {colors['secondary']});
        }}
        
        .map-nav-btn-disabled {{
            background: #cccccc;
            cursor: not-allowed;
            opacity: 0.6;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        # Botón "Ver Tolima"
        if current_level != 'departamento':
            if st.button("🏛️ Ver Tolima", key="nav_tolima"):
                map_state.set_departamento_view()
                st.rerun()
        else:
            st.markdown('<div class="map-nav-btn map-nav-btn-disabled">🏛️ Tolima Actual</div>', 
                       unsafe_allow_html=True)
    
    with col2:
        # Botón "Ver Municipio"
        if current_level == 'vereda' and selected_municipio:
            municipio_name = selected_municipio['display']
            if st.button(f"🏘️ Ver {municipio_name[:12]}...", key="nav_municipio"):
                map_state.set_municipio_view(
                    selected_municipio['display'],
                    selected_municipio['normalized']
                )
                st.rerun()
        elif current_level == 'municipio':
            municipio_name = selected_municipio['display'] if selected_municipio else 'Municipio'
            st.markdown(f'<div class="map-nav-btn map-nav-btn-disabled">🏘️ {municipio_name[:12]}... Actual</div>', 
                       unsafe_allow_html=True)
    
    with col3:
        # Botón "Actualizar"
        if st.button("🔄 Actualizar", key="nav_refresh"):
            st.rerun()
    
    with col4:
        # Indicador de nivel actual
        level_info = {
            'departamento': '🗺️ Vista: Tolima',
            'municipio': f"🏘️ Vista: {selected_municipio['display'] if selected_municipio else 'Municipio'}",
            'vereda': f"📍 Vista: {selected_vereda['display'] if selected_vereda else 'Vereda'}"
        }
        
        st.markdown(
            f'<div style="background: {colors["accent"]}; color: white; padding: 0.6rem 1.2rem; '
            f'border-radius: 25px; font-weight: 600; font-size: 0.9rem; text-align: center; '
            f'box-shadow: 0 3px 10px rgba(0,0,0,0.2);">{level_info[current_level]}</div>',
            unsafe_allow_html=True
        )


def create_breadcrumb_navigation(map_state: MapState, colors: Dict[str, str]):
    """Crea navegación tipo breadcrumb para el mapa."""
    
    current_level = map_state.get_current_level()
    selected_municipio = map_state.get_selected_municipio()
    selected_vereda = map_state.get_selected_vereda()
    
    breadcrumbs = ['🏛️ Tolima']
    
    if selected_municipio:
        breadcrumbs.append(f"🏘️ {selected_municipio['display']}")
    
    if selected_vereda:
        breadcrumbs.append(f"📍 {selected_vereda['display']}")
    
    # Crear breadcrumb HTML
    breadcrumb_html = f"""
    <div style="
        background: linear-gradient(135deg, {colors['light']}, white);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid {colors['primary']};
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    ">
        <div style="
            font-size: 0.9rem;
            color: {colors['dark']};
            font-weight: 500;
        ">
            📍 <strong>Ubicación actual:</strong>
        </div>
        <div style="
            font-size: 1.1rem;
            color: {colors['primary']};
            font-weight: 600;
            margin-top: 0.5rem;
        ">
            {' → '.join(breadcrumbs)}
        </div>
    </div>
    """
    
    st.markdown(breadcrumb_html, unsafe_allow_html=True)


def get_map_instructions(level: str) -> str:
    """Retorna instrucciones según el nivel del mapa."""
    
    instructions = {
        'departamento': "💡 Haga clic en cualquier municipio para filtrar datos y hacer zoom a sus veredas",
        'municipio': "💡 Haga clic en cualquier vereda para filtrar datos específicos de esa vereda",
        'vereda': "💡 Vista detallada de la vereda seleccionada. Use los botones para navegar a otros niveles"
    }
    
    return instructions.get(level, "💡 Navegue por el mapa para explorar los datos")


def sync_sidebar_with_map(map_state: MapState):
    """Sincroniza los filtros del sidebar con el estado del mapa."""
    
    selected_municipio = map_state.get_selected_municipio()
    selected_vereda = map_state.get_selected_vereda()
    
    # Evitar loops de sincronización
    if st.session_state.get('map_filter_changed', False):
        return
    
    # Actualizar filtros según estado del mapa
    if selected_municipio:
        if 'municipio_filter' in st.session_state:
            if st.session_state.municipio_filter != selected_municipio['display']:
                st.session_state.municipio_filter = selected_municipio['display']
    else:
        if 'municipio_filter' in st.session_state:
            if st.session_state.municipio_filter != 'Todos':
                st.session_state.municipio_filter = 'Todos'
    
    if selected_vereda:
        if 'vereda_filter' in st.session_state:
            if st.session_state.vereda_filter != selected_vereda['display']:
                st.session_state.vereda_filter = selected_vereda['display']
    else:
        if 'vereda_filter' in st.session_state:
            if st.session_state.vereda_filter != 'Todas':
                st.session_state.vereda_filter = 'Todas'


def create_map_legend(colors: Dict[str, str]):
    """Crea leyenda para el mapa."""
    
    legend_html = f"""
    <div style="
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid {colors['primary']};
        margin: 1rem 0;
    ">
        <h4 style="color: {colors['primary']}; margin: 0 0 0.75rem 0; font-size: 1rem;">
            🎨 Leyenda del Mapa
        </h4>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 20px; height: 20px; background: {colors['danger']}; border-radius: 4px; opacity: 0.7;"></div>
                <span style="font-size: 0.85rem;">Municipios/Veredas con casos</span>
            </div>
            
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 20px; height: 20px; background: {colors['warning']}; border-radius: 4px; opacity: 0.7;"></div>
                <span style="font-size: 0.85rem;">Solo epizootias</span>
            </div>
            
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 20px; height: 20px; background: {colors['info']}; border-radius: 4px; opacity: 0.7;"></div>
                <span style="font-size: 0.85rem;">Sin eventos registrados</span>
            </div>
            
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 20px; height: 20px; background: #8B0000; border-radius: 4px; opacity: 0.7;"></div>
                <span style="font-size: 0.85rem;">Casos + Epizootias</span>
            </div>
        </div>
        
        <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #eee; font-size: 0.8rem; color: #666;">
            💡 <strong>Tip:</strong> La intensidad del color indica la cantidad de eventos. Haga clic para filtrar y hacer zoom.
        </div>
    </div>
    """
    
    st.markdown(legend_html, unsafe_allow_html=True)


# Instancia global del gestor de estado
map_state = MapState()