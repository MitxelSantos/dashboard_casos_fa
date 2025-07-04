"""
Utilidades MEJORADAS para manejar interacciones avanzadas en mapas.
NUEVA FUNCIONALIDAD: 
- Detección robusta de 1 clic vs 2 clics
- Sincronización bidireccional con filtros
- Sistema de navegación completo (Departamento → Municipio → Vereda)
- Límites geográficos fijos del Tolima
"""

import streamlit as st
import folium
import json
import time
from typing import Dict, Any, Optional, Tuple
import geopandas as gpd
import pandas as pd


class MapInteractionManager:
    """
    NUEVA: Clase para manejar todas las interacciones del mapa de manera centralizada.
    """
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Inicializa variables de estado para interacciones del mapa."""
        if 'last_click_time' not in st.session_state:
            st.session_state['last_click_time'] = 0
        
        if 'click_count' not in st.session_state:
            st.session_state['click_count'] = 0
        
        if 'last_clicked_feature' not in st.session_state:
            st.session_state['last_clicked_feature'] = None
        
        if 'map_navigation_history' not in st.session_state:
            st.session_state['map_navigation_history'] = []
        
        if 'double_click_threshold' not in st.session_state:
            st.session_state['double_click_threshold'] = 0.5  # segundos
    
    def detect_interaction_type(self, map_data):
        """
        NUEVA: Detecta si fue 1 clic, 2 clics o ninguna interacción.
        
        Returns:
            tuple: (interaction_type, feature_data)
            interaction_type: 'none', 'single_click', 'double_click'
        """
        if not map_data or not map_data.get('last_object_clicked_popup'):
            return 'none', None
        
        current_time = time.time()
        last_time = st.session_state.get('last_click_time', 0)
        time_diff = current_time - last_time
        
        # Actualizar tiempo del último clic
        st.session_state['last_click_time'] = current_time
        
        # Si han pasado menos de X segundos = posible doble clic
        if time_diff < st.session_state['double_click_threshold']:
            st.session_state['click_count'] += 1
            
            if st.session_state['click_count'] >= 2:
                # Es doble clic
                st.session_state['click_count'] = 0
                return 'double_click', map_data['last_object_clicked_popup']
            else:
                # Primer clic, esperar a ver si hay segundo
                return 'single_click', map_data['last_object_clicked_popup']
        else:
            # Ha pasado mucho tiempo, resetear contador
            st.session_state['click_count'] = 1
            return 'single_click', map_data['last_object_clicked_popup']
    
    def extract_feature_info(self, clicked_data):
        """
        NUEVA: Extrae información del feature clicado independientemente del formato.
        
        Returns:
            dict: {'type': 'municipio'|'vereda', 'name': str, 'properties': dict}
        """
        if not clicked_data or not isinstance(clicked_data, dict):
            return None
        
        feature_info = {
            'type': None,
            'name': None,
            'properties': {},
            'raw_data': clicked_data
        }
        
        # Intentar extraer información del tooltip
        if 'tooltip' in clicked_data:
            tooltip = clicked_data['tooltip']
            
            # Extraer nombre usando regex
            import re
            name_match = re.search(r'<b>(.*?)</b>', tooltip)
            if name_match:
                feature_info['name'] = name_match.group(1).strip()
            
            # Determinar tipo basado en el contenido del tooltip
            if '👆👆 2 clics' in tooltip.lower() or 'doble clic' in tooltip.lower():
                # Es un feature interactivo (municipio o vereda)
                if 'municipio' in tooltip.lower() or 'casos:' in tooltip.lower():
                    feature_info['type'] = 'municipio'
                elif 'vereda' in tooltip.lower():
                    feature_info['type'] = 'vereda'
        
        # Intentar extraer información adicional si está disponible
        if 'properties' in clicked_data:
            feature_info['properties'] = clicked_data['properties']
        
        return feature_info if feature_info['name'] else None
    
    def handle_double_click_action(self, feature_info, available_data):
        """
        NUEVA: Maneja la acción de doble clic para filtrar automáticamente.
        
        Args:
            feature_info: Información del feature clicado
            available_data: Datos disponibles para validación
        
        Returns:
            dict: Resultado de la acción
        """
        if not feature_info or not feature_info['name']:
            return {'success': False, 'message': 'No se pudo identificar el elemento clicado'}
        
        feature_name = feature_info['name']
        feature_type = feature_info['type']
        
        # Actualizar filtros según el tipo de feature
        if feature_type == 'municipio':
            return self._filter_by_municipio(feature_name, available_data)
        elif feature_type == 'vereda':
            return self._filter_by_vereda(feature_name, available_data)
        else:
            return {'success': False, 'message': f'Tipo de elemento no reconocido: {feature_type}'}
    
    def _filter_by_municipio(self, municipio_name, available_data):
        """Filtra por municipio específico."""
        # Validar que el municipio existe en los datos
        municipios_disponibles = list(available_data.get('municipio_display_map', {}).values())
        
        if municipio_name not in municipios_disponibles:
            return {'success': False, 'message': f'Municipio no encontrado: {municipio_name}'}
        
        # Actualizar filtros
        st.session_state['municipio_filter'] = municipio_name
        st.session_state['vereda_filter'] = 'Todas'  # Resetear vereda
        st.session_state['map_filter_updated'] = True
        
        # Agregar a historial de navegación
        self._add_to_navigation_history('municipio', municipio_name)
        
        return {
            'success': True, 
            'message': f'✅ Filtrado por municipio: {municipio_name}',
            'action': 'municipio_filtered',
            'municipio': municipio_name
        }
    
    def _filter_by_vereda(self, vereda_name, available_data):
        """Filtra por vereda específica."""
        # Para filtrar por vereda, necesitamos saber el municipio actual
        current_municipio = st.session_state.get('municipio_filter', 'Todos')
        
        if current_municipio == 'Todos':
            return {'success': False, 'message': 'Debe seleccionar un municipio primero'}
        
        # Validar que la vereda existe en el municipio actual
        municipio_norm = None
        for norm, display in available_data.get('municipio_display_map', {}).items():
            if display == current_municipio:
                municipio_norm = norm
                break
        
        if not municipio_norm:
            return {'success': False, 'message': 'Municipio actual no válido'}
        
        veredas_disponibles = available_data.get('vereda_display_map', {}).get(municipio_norm, {}).values()
        
        if vereda_name not in veredas_disponibles:
            return {'success': False, 'message': f'Vereda no encontrada en {current_municipio}: {vereda_name}'}
        
        # Actualizar filtro de vereda
        st.session_state['vereda_filter'] = vereda_name
        st.session_state['map_filter_updated'] = True
        
        # Agregar a historial de navegación
        self._add_to_navigation_history('vereda', vereda_name)
        
        return {
            'success': True,
            'message': f'✅ Filtrado por vereda: {vereda_name} ({current_municipio})',
            'action': 'vereda_filtered',
            'municipio': current_municipio,
            'vereda': vereda_name
        }
    
    def _add_to_navigation_history(self, level, name):
        """Agrega un elemento al historial de navegación."""
        history = st.session_state.get('map_navigation_history', [])
        
        # Evitar duplicados consecutivos
        if not history or history[-1] != (level, name):
            history.append((level, name))
            
            # Mantener solo los últimos 10 elementos
            if len(history) > 10:
                history = history[-10:]
            
            st.session_state['map_navigation_history'] = history
    
    def get_navigation_breadcrumb(self):
        """
        NUEVA: Genera breadcrumb de navegación basado en filtros actuales.
        
        Returns:
            list: Lista de elementos de navegación
        """
        breadcrumb = [{'level': 'departamento', 'name': 'Tolima', 'icon': '🏛️'}]
        
        municipio = st.session_state.get('municipio_filter', 'Todos')
        vereda = st.session_state.get('vereda_filter', 'Todas')
        
        if municipio != 'Todos':
            breadcrumb.append({'level': 'municipio', 'name': municipio, 'icon': '🏘️'})
        
        if vereda != 'Todas':
            breadcrumb.append({'level': 'vereda', 'name': vereda, 'icon': '📍'})
        
        return breadcrumb


class MapBoundsManager:
    """
    NUEVA: Clase para manejar límites geográficos fijos del Tolima.
    """
    
    def __init__(self, tolima_shapefile_path=None):
        self.bounds = None
        self.center = None
        self.load_tolima_bounds(tolima_shapefile_path)
    
    def load_tolima_bounds(self, shapefile_path=None):
        """Carga los límites geográficos del Tolima desde shapefile."""
        try:
            if shapefile_path:
                gdf = gpd.read_file(shapefile_path)
                self.bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
            else:
                # Coordenadas aproximadas del Tolima si no hay shapefile
                self.bounds = [-75.8, 3.2, -74.4, 5.8]  # [minx, miny, maxx, maxy]
            
            # Calcular centro
            self.center = [
                (self.bounds[1] + self.bounds[3]) / 2,  # lat (centro Y)
                (self.bounds[0] + self.bounds[2]) / 2   # lon (centro X)
            ]
            
        except Exception as e:
            st.warning(f"No se pudieron cargar límites del Tolima: {e}")
            # Coordenadas por defecto del Tolima
            self.bounds = [-75.8, 3.2, -74.4, 5.8]
            self.center = [4.5, -75.1]
    
    def get_fixed_map_config(self, zoom_level=8):
        """
        NUEVA: Retorna configuración para mapa fijo sin navegación.
        
        Returns:
            dict: Configuración de Folium para mapa fijo
        """
        return {
            'location': self.center,
            'zoom_start': zoom_level,
            'tiles': 'CartoDB positron',
            'zoom_control': False,
            'scrollWheelZoom': False,
            'doubleClickZoom': False,
            'dragging': False,
            'attributionControl': False,
            'max_bounds': True,
            'min_zoom': zoom_level,
            'max_zoom': zoom_level
        }
    
    def apply_bounds_to_map(self, folium_map, buffer=0.1):
        """Aplica límites geográficos al mapa."""
        if self.bounds:
            # Agregar buffer para evitar que el contenido esté exactamente en el borde
            bounds_with_buffer = [
                [self.bounds[1] - buffer, self.bounds[0] - buffer],  # SW corner
                [self.bounds[3] + buffer, self.bounds[2] + buffer]   # NE corner
            ]
            
            folium_map.fit_bounds(bounds_with_buffer)
            folium_map.options['maxBounds'] = bounds_with_buffer
    
    def is_point_in_tolima(self, lat, lon, buffer=0.05):
        """Verifica si un punto está dentro de los límites del Tolima."""
        if not self.bounds:
            return True
        
        return (
            self.bounds[0] - buffer <= lon <= self.bounds[2] + buffer and
            self.bounds[1] - buffer <= lat <= self.bounds[3] + buffer
        )


class PopupManager:
    """
    NUEVA: Clase para crear popups mejorados y consistentes.
    """
    
    def __init__(self, colors):
        self.colors = colors
    
    def create_enhanced_popup(self, feature_type, name, data, extra_info=None):
        """
        NUEVA: Crea popup mejorado según el tipo de feature.
        
        Args:
            feature_type: 'municipio' o 'vereda'
            name: Nombre del feature
            data: Datos estadísticos
            extra_info: Información adicional opcional
        """
        if feature_type == 'municipio':
            return self._create_municipio_popup(name, data, extra_info)
        elif feature_type == 'vereda':
            return self._create_vereda_popup(name, data, extra_info)
        else:
            return self._create_generic_popup(name, data)
    
    def _create_municipio_popup(self, municipio, data, extra_info=None):
        """Crea popup específico para municipios."""
        casos = data.get('casos', 0)
        fallecidos = data.get('fallecidos', 0)
        epizootias = data.get('epizootias', 0)
        
        letalidad = (fallecidos / casos * 100) if casos > 0 else 0
        actividad_total = casos + epizootias
        
        # Determinar nivel de riesgo
        if actividad_total > 20:
            riesgo = "Alto"
            riesgo_color = self.colors['danger']
        elif actividad_total > 5:
            riesgo = "Medio"
            riesgo_color = self.colors['warning']
        else:
            riesgo = "Bajo"
            riesgo_color = self.colors['success']
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 340px; line-height: 1.4;">
            <h3 style="color: {self.colors['primary']}; margin: 0 0 15px 0; border-bottom: 3px solid {self.colors['secondary']}; padding-bottom: 8px; text-align: center;">
                📍 {municipio}
            </h3>
            
            <!-- Métricas principales en grid -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 15px;">
                <div style="background: linear-gradient(135deg, #ffe6e6, #ffcccc); padding: 15px; border-radius: 10px; text-align: center; border: 2px solid {self.colors['danger']};">
                    <div style="font-size: 2rem; font-weight: bold; color: {self.colors['danger']};">🦠 {casos}</div>
                    <div style="font-size: 0.85rem; color: #333; font-weight: 600; margin-top: 5px;">CASOS HUMANOS</div>
                </div>
                <div style="background: linear-gradient(135deg, #fff3e0, #ffe0b3); padding: 15px; border-radius: 10px; text-align: center; border: 2px solid {self.colors['warning']};">
                    <div style="font-size: 2rem; font-weight: bold; color: {self.colors['warning']};">🐒 {epizootias}</div>
                    <div style="font-size: 0.85rem; color: #333; font-weight: 600; margin-top: 5px;">EPIZOOTIAS</div>
                </div>
            </div>
            
            <!-- Métricas secundarias -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 15px;">
                <div style="background: #f5f5f5; padding: 10px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 1.2em; font-weight: bold; color: {self.colors['dark']};">⚰️ {fallecidos}</div>
                    <div style="font-size: 0.7em; color: #666;">Fallecidos</div>
                </div>
                <div style="background: #f5f5f5; padding: 10px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 1.2em; font-weight: bold; color: {self.colors['info']};">📊 {letalidad:.1f}%</div>
                    <div style="font-size: 0.7em; color: #666;">Letalidad</div>
                </div>
                <div style="background: {riesgo_color}; padding: 10px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 1em; font-weight: bold; color: white;">⚠️ {riesgo}</div>
                    <div style="font-size: 0.7em; color: white; opacity: 0.9;">Riesgo</div>
                </div>
            </div>
            
            <!-- Actividad total destacada -->
            <div style="background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['accent']}); padding: 15px; border-radius: 10px; text-align: center; color: white; margin-bottom: 15px;">
                <div style="font-size: 1.6em; font-weight: bold;">📈 {actividad_total}</div>
                <div style="font-size: 0.9em; opacity: 0.9;">Actividad Total (Casos + Epizootias)</div>
            </div>
            
            <!-- Información adicional si está disponible -->
            {f'<div style="background: #e3f2fd; padding: 10px; border-radius: 6px; margin-bottom: 15px; font-size: 0.8em; color: #1565c0;"><strong>Info:</strong> {extra_info}</div>' if extra_info else ''}
            
            <!-- Instrucciones de interacción -->
            <div style="background: linear-gradient(135deg, {self.colors['info']}, {self.colors['secondary']}); padding: 12px; border-radius: 8px; text-align: center; color: white;">
                <div style="font-size: 0.95em; font-weight: bold; margin-bottom: 4px;">🖱️ INTERACCIONES</div>
                <div style="font-size: 0.8em; opacity: 0.9;">👆 1 clic: Ver esta información</div>
                <div style="font-size: 0.8em; opacity: 0.9;">👆👆 2 clics rápidos: Filtrar y ver veredas</div>
            </div>
        </div>
        """
        
        return popup_html
    
    def _create_vereda_popup(self, vereda, data, extra_info=None):
        """Crea popup específico para veredas."""
        casos = data.get('casos', 0)
        epizootias = data.get('epizootias', 0)
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 280px;">
            <h4 style="color: {self.colors['primary']}; margin: 0 0 12px 0; border-bottom: 2px solid {self.colors['secondary']}; padding-bottom: 5px;">
                🏘️ {vereda}
            </h4>
            
            <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                <div style="background: #ffe6e6; padding: 10px; border-radius: 6px; flex: 1; text-align: center;">
                    <div style="font-weight: bold; color: {self.colors['danger']}; font-size: 1.3em;">🦠 {casos}</div>
                    <div style="font-size: 0.75em; color: #666;">Casos</div>
                </div>
                <div style="background: #fff3e0; padding: 10px; border-radius: 6px; flex: 1; text-align: center;">
                    <div style="font-weight: bold; color: {self.colors['warning']}; font-size: 1.3em;">🐒 {epizootias}</div>
                    <div style="font-size: 0.75em; color: #666;">Epizootias</div>
                </div>
            </div>
            
            {f'<div style="background: #e8f5e8; padding: 8px; border-radius: 4px; margin-bottom: 12px; font-size: 0.8em; color: #2e7d32;"><strong>Info:</strong> {extra_info}</div>' if extra_info else ''}
            
            <div style="background: linear-gradient(135deg, {self.colors['info']}, {self.colors['primary']}); padding: 10px; border-radius: 6px; text-align: center; color: white;">
                <div style="font-size: 0.85em; font-weight: bold;">👆👆 Doble clic para filtrar esta vereda</div>
            </div>
        </div>
        """
        
        return popup_html
    
    def _create_generic_popup(self, name, data):
        """Crea popup genérico para otros elementos."""
        return f"""
        <div style="font-family: Arial, sans-serif; width: 200px;">
            <h4 style="color: {self.colors['primary']}; margin: 0 0 10px 0;">
                📍 {name}
            </h4>
            <div style="font-size: 0.9em; color: #666;">
                Información no disponible
            </div>
        </div>
        """


# FUNCIONES DE UTILIDAD GLOBALES

def create_fixed_tolima_map(center_coords=None, zoom_level=8, enable_interactions=True):
    """
    NUEVA: Crea un mapa fijo del Tolima con límites geográficos restringidos.
    
    Args:
        center_coords: Coordenadas del centro [lat, lon]
        zoom_level: Nivel de zoom fijo
        enable_interactions: Si permite interacciones básicas
    
    Returns:
        folium.Map: Mapa configurado
    """
    if not center_coords:
        center_coords = [4.5, -75.1]  # Centro aproximado del Tolima
    
    # Configuración base del mapa fijo
    map_config = {
        'location': center_coords,
        'zoom_start': zoom_level,
        'tiles': 'CartoDB positron',
        'zoom_control': False,
        'scrollWheelZoom': False,
        'doubleClickZoom': False,
        'dragging': False,
        'attributionControl': False,
    }
    
    # Si se deshabilitan las interacciones, agregar más restricciones
    if not enable_interactions:
        map_config.update({
            'keyboard': False,
            'boxZoom': False,
            'touchZoom': False,
        })
    
    m = folium.Map(**map_config)
    
    # Aplicar límites geográficos del Tolima
    bounds_manager = MapBoundsManager()
    bounds_manager.apply_bounds_to_map(m)
    
    return m


def add_navigation_controls_to_map(folium_map, current_level, colors):
    """
    NUEVA: Agrega controles de navegación personalizados al mapa.
    """
    # CSS para controles de navegación
    navigation_css = f"""
    <style>
    .map-nav-controls {{
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }}
    
    .map-nav-btn {{
        background: {colors['primary']};
        color: white;
        border: none;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }}
    
    .map-nav-btn:hover {{
        background: {colors['accent']};
        transform: translateY(-1px);
    }}
    
    .map-nav-level {{
        background: {colors['info']};
        color: white;
        padding: 6px 10px;
        border-radius: 4px;
        font-size: 11px;
        text-align: center;
        font-weight: bold;
    }}
    </style>
    """
    
    # HTML para controles
    controls_html = f"""
    {navigation_css}
    <div class="map-nav-controls">
        <div class="map-nav-level">📍 {current_level.upper()}</div>
        <button class="map-nav-btn" onclick="resetMapView()">🏛️ TOLIMA</button>
    </div>
    
    <script>
    function resetMapView() {{
        // Enviar evento personalizado para resetear vista
        window.parent.postMessage({{
            type: 'mapReset',
            action: 'reset_to_department'
        }}, '*');
    }}
    </script>
    """
    
    folium_map.get_root().html.add_child(folium.Element(controls_html))


def process_map_interaction_complete(map_data, available_data, colors):
    """
    NUEVA: Función completa para procesar cualquier interacción del mapa.
    
    Args:
        map_data: Datos del mapa de st_folium
        available_data: Datos disponibles para validación
        colors: Colores del tema
    
    Returns:
        dict: Resultado completo de la interacción
    """
    # Inicializar manager
    interaction_manager = MapInteractionManager()
    popup_manager = PopupManager(colors)
    
    # Detectar tipo de interacción
    interaction_type, clicked_data = interaction_manager.detect_interaction_type(map_data)
    
    if interaction_type == 'none':
        return {'type': 'none', 'message': 'Sin interacción'}
    
    # Extraer información del feature clicado
    feature_info = interaction_manager.extract_feature_info(clicked_data)
    
    if not feature_info:
        return {'type': 'error', 'message': 'No se pudo identificar el elemento clicado'}
    
    if interaction_type == 'single_click':
        # Para 1 clic, solo mostrar popup (manejo automático por Folium)
        return {
            'type': 'single_click',
            'feature': feature_info,
            'message': f'Información mostrada para {feature_info["name"]}'
        }
    
    elif interaction_type == 'double_click':
        # Para doble clic, filtrar automáticamente
        action_result = interaction_manager.handle_double_click_action(feature_info, available_data)
        
        if action_result['success']:
            return {
                'type': 'double_click',
                'feature': feature_info,
                'action_result': action_result,
                'message': action_result['message'],
                'requires_rerun': True
            }
        else:
            return {
                'type': 'double_click_error',
                'feature': feature_info,
                'message': f"Error: {action_result['message']}"
            }
    
    return {'type': 'unknown', 'message': 'Tipo de interacción no reconocido'}


def create_interaction_feedback_ui(interaction_result, colors):
    """
    NUEVA: Crea UI de feedback para las interacciones del mapa.
    """
    if interaction_result['type'] == 'none':
        return
    
    if interaction_result['type'] == 'single_click':
        st.info(f"ℹ️ {interaction_result['message']}")
    
    elif interaction_result['type'] == 'double_click':
        st.success(f"✅ {interaction_result['message']}")
        
        # Mostrar navegación actualizada
        if 'action_result' in interaction_result:
            action = interaction_result['action_result']
            if action.get('action') == 'municipio_filtered':
                st.markdown(
                    f"""
                    <div style="background: {colors['info']}; color: white; padding: 10px; border-radius: 6px; margin: 10px 0;">
                        🗺️ <strong>Vista actualizada:</strong> Ahora viendo veredas de {action['municipio']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            elif action.get('action') == 'vereda_filtered':
                st.markdown(
                    f"""
                    <div style="background: {colors['success']}; color: white; padding: 10px; border-radius: 6px; margin: 10px 0;">
                        📍 <strong>Vista detallada:</strong> {action['vereda']} en {action['municipio']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    elif interaction_result['type'] in ['double_click_error', 'error']:
        st.error(f"❌ {interaction_result['message']}")


# INSTANCIAS GLOBALES para reutilización
_interaction_manager = None
_bounds_manager = None
_popup_manager = None

def get_interaction_manager():
    """Singleton para MapInteractionManager."""
    global _interaction_manager
    if _interaction_manager is None:
        _interaction_manager = MapInteractionManager()
    return _interaction_manager

def get_bounds_manager():
    """Singleton para MapBoundsManager."""
    global _bounds_manager
    if _bounds_manager is None:
        _bounds_manager = MapBoundsManager()
    return _bounds_manager

def get_popup_manager(colors):
    """Factory para PopupManager con colores."""
    global _popup_manager
    if _popup_manager is None:
        _popup_manager = PopupManager(colors)
    return _popup_manager