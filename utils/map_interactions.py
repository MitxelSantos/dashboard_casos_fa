"""
Utilidades para manejar interacciones avanzadas en mapas.
Incluye funcionalidad de doble clic y sincronización con filtros.
"""

import streamlit as st
import folium
import json
from typing import Dict, Any, Optional, Tuple


def add_double_click_functionality(folium_map, municipios_data=None):
    """
    Agrega funcionalidad de doble clic a un mapa de Folium.
    
    Args:
        folium_map: Mapa de Folium
        municipios_data: Datos de municipios para identificación
    """
    
    # JavaScript para manejar doble clic
    double_click_js = """
    <script>
    // Variable para detectar doble clic
    var clickTimer = null;
    var clickCount = 0;
    
    // Función para manejar clics en el mapa
    function handleMapClick(feature, layer) {
        clickCount++;
        
        if (clickCount === 1) {
            // Primer clic - mostrar popup (comportamiento normal)
            clickTimer = setTimeout(function() {
                clickCount = 0;
                // El popup se muestra automáticamente
            }, 400);
        } else if (clickCount === 2) {
            // Doble clic - aplicar filtro
            clearTimeout(clickTimer);
            clickCount = 0;
            
            // Obtener propiedades del feature
            var props = feature.properties;
            var municipioName = props.MpNombre || props.NOMBRE_VER || 'Desconocido';
            
            // Enviar evento personalizado a Streamlit
            var event = new CustomEvent('municipioDoubleClick', {
                detail: {
                    municipio: municipioName,
                    properties: props,
                    action: 'filter'
                }
            });
            
            window.dispatchEvent(event);
            
            // Mostrar indicador visual
            console.log('Doble clic en:', municipioName);
            
            // Opcional: Mostrar mensaje temporal
            var notification = document.createElement('div');
            notification.innerHTML = '🔄 Aplicando filtro para ' + municipioName;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #7D0F2B;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                z-index: 9999;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            `;
            document.body.appendChild(notification);
            
            setTimeout(function() {
                document.body.removeChild(notification);
            }, 2000);
        }
    }
    
    // Aplicar event listeners cuando el mapa esté listo
    document.addEventListener('DOMContentLoaded', function() {
        // Buscar todos los elementos del mapa que pueden ser clicados
        setTimeout(function() {
            var mapElements = document.querySelectorAll('.leaflet-interactive');
            mapElements.forEach(function(element) {
                element.addEventListener('click', function(e) {
                    // Extraer información del elemento clicado
                    var municipio = e.target.getAttribute('data-municipio') || 'Desconocido';
                    handleMapClick({properties: {MpNombre: municipio}}, null);
                });
            });
        }, 1000);
    });
    </script>
    """
    
    # Agregar el JavaScript al mapa
    folium_map.get_root().html.add_child(folium.Element(double_click_js))


def create_map_with_enhanced_interactions(center_coords, zoom_level=8):
    """
    Crea un mapa con interacciones mejoradas.
    
    Args:
        center_coords: Tupla con (lat, lon) del centro
        zoom_level: Nivel de zoom inicial
        
    Returns:
        Mapa de Folium configurado
    """
    
    # Crear mapa base
    m = folium.Map(
        location=center_coords,
        zoom_start=zoom_level,
        tiles='CartoDB positron',
        control_scale=True
    )
    
    # Agregar control de capas
    folium.LayerControl().add_to(m)
    
    # CSS personalizado para mejor interacción
    custom_css = """
    <style>
    .leaflet-interactive {
        cursor: pointer !important;
        transition: all 0.3s ease;
    }
    
    .leaflet-interactive:hover {
        stroke-width: 3 !important;
        stroke-opacity: 1 !important;
        filter: brightness(1.1);
    }
    
    .leaflet-popup-content {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        line-height: 1.4;
    }
    
    .map-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #7D0F2B;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        z-index: 9999;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .click-instruction {
        position: absolute;
        bottom: 20px;
        left: 20px;
        background: rgba(255, 255, 255, 0.9);
        padding: 10px 15px;
        border-radius: 8px;
        font-size: 12px;
        color: #333;
        border-left: 4px solid #7D0F2B;
        z-index: 1000;
        font-weight: 500;
    }
    </style>
    """
    
    # Agregar CSS al mapa
    m.get_root().html.add_child(folium.Element(custom_css))
    
    # Agregar instrucciones de uso
    instructions_html = """
    <div class="click-instruction">
        💡 <strong>Instrucciones:</strong><br>
        • 1 clic: Ver información<br>
        • 2 clics rápidos: Filtrar y hacer zoom
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(instructions_html))
    
    return m


def add_enhanced_geojson_layer(folium_map, geodata, style_function, popup_function, 
                             layer_name="Capa", municipios_data=None):
    """
    Agrega una capa GeoJSON con interacciones mejoradas.
    
    Args:
        folium_map: Mapa de Folium
        geodata: Datos geográficos (GeoDataFrame o dict)
        style_function: Función de estilo
        popup_function: Función para crear popups
        layer_name: Nombre de la capa
        municipios_data: Datos adicionales de municipios
    """
    
    # Crear feature group
    feature_group = folium.FeatureGroup(name=layer_name)
    
    # Procesar cada feature
    if hasattr(geodata, 'iterrows'):
        # Es un GeoDataFrame
        for idx, row in geodata.iterrows():
            municipio_name = row.get('MpNombre', row.get('NOMBRE_VER', f'Municipio_{idx}'))
            
            # Crear popup
            popup_content = popup_function(row) if popup_function else f"<b>{municipio_name}</b>"
            
            # Crear tooltip
            tooltip_content = f"<b>{municipio_name}</b><br>🖱️ Doble clic para filtrar"
            
            # Agregar GeoJson con eventos personalizados
            geojson = folium.GeoJson(
                row['geometry'],
                style_function=style_function,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=folium.Tooltip(tooltip_content),
            )
            
            # Agregar atributo personalizado para identificación
            geojson.add_child(folium.JavaScriptLink(""))
            
            geojson.add_to(feature_group)
    
    feature_group.add_to(folium_map)
    
    return feature_group


def handle_map_interactions(map_data, session_state_key="map_interactions"):
    """
    Maneja las interacciones del mapa y actualiza el estado de Streamlit.
    
    Args:
        map_data: Datos retornados por st_folium
        session_state_key: Clave para almacenar el estado
        
    Returns:
        Dict con información de la interacción
    """
    
    interaction_info = {
        "type": None,
        "municipio": None,
        "action": None,
        "changed": False
    }
    
    if not map_data:
        return interaction_info
    
    # Verificar si hay un objeto clicado
    if map_data.get('last_object_clicked_popup'):
        clicked_data = map_data['last_object_clicked_popup']
        
        # Extraer información del clic
        if isinstance(clicked_data, dict):
            interaction_info["type"] = "click"
            interaction_info["changed"] = True
            
            # Intentar extraer el nombre del municipio
            if 'tooltip' in clicked_data:
                import re
                tooltip = clicked_data['tooltip']
                match = re.search(r'<b>(.*?)</b>', tooltip)
                if match:
                    interaction_info["municipio"] = match.group(1)
            
            # Determinar si es doble clic basado en timing
            current_time = st.session_state.get(f"{session_state_key}_last_click", 0)
            import time
            new_time = time.time()
            
            if new_time - current_time < 0.5:  # Doble clic detectado
                interaction_info["action"] = "filter"
                st.session_state[f"{session_state_key}_double_click"] = True
            else:
                interaction_info["action"] = "popup"
                st.session_state[f"{session_state_key}_double_click"] = False
            
            st.session_state[f"{session_state_key}_last_click"] = new_time
    
    return interaction_info


def apply_map_filter_from_interaction(interaction_info, available_municipios):
    """
    Aplica filtros basado en la interacción del mapa.
    
    Args:
        interaction_info: Información de la interacción
        available_municipios: Lista de municipios disponibles
        
    Returns:
        bool: True si se aplicó un filtro
    """
    
    if (interaction_info["action"] == "filter" and 
        interaction_info["municipio"] and
        interaction_info["municipio"] in available_municipios):
        
        # Aplicar filtro de municipio
        st.session_state["municipio_filter"] = interaction_info["municipio"]
        
        # Mostrar mensaje de confirmación
        st.success(f"✅ Filtro aplicado: {interaction_info['municipio']}")
        
        return True
    
    return False


def create_map_state_indicator(current_filters, colors):
    """
    Crea un indicador visual del estado actual del mapa.
    
    Args:
        current_filters: Filtros actuales
        colors: Diccionario de colores
        
    Returns:
        str: HTML del indicador
    """
    
    municipio = current_filters.get("municipio_display", "Todos")
    vereda = current_filters.get("vereda_display", "Todas")
    
    # Determinar el nivel actual
    if vereda != "Todas":
        nivel = "📍 Vereda"
        ubicacion = f"{vereda} ({municipio})"
        color = colors["info"]
    elif municipio != "Todos":
        nivel = "🏛️ Municipio"
        ubicacion = municipio
        color = colors["warning"]
    else:
        nivel = "🗺️ Departamento"
        ubicacion = "Tolima"
        color = colors["primary"]
    
    return f"""
    <div style="
        background: {color};
        color: white;
        padding: 8px 15px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 3px 10px rgba(0,0,0,0.3);
    ">
        {nivel}: {ubicacion}
    </div>
    """


def add_map_legend(folium_map, colors):
    """
    Agrega una leyenda personalizada al mapa.
    
    Args:
        folium_map: Mapa de Folium
        colors: Diccionario de colores
    """
    
    legend_html = f"""
    <div style="
        position: fixed;
        top: 20px;
        left: 20px;
        width: 200px;
        background: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 9998;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 12px;
    ">
        <h4 style="margin: 0 0 10px 0; color: {colors['primary']}; font-size: 14px;">
            🎨 Leyenda del Mapa
        </h4>
        
        <div style="margin: 5px 0; display: flex; align-items: center;">
            <div style="width: 20px; height: 15px; background: {colors['danger']}; margin-right: 8px; border-radius: 3px; opacity: 0.7;"></div>
            <span>Casos confirmados</span>
        </div>
        
        <div style="margin: 5px 0; display: flex; align-items: center;">
            <div style="width: 20px; height: 15px; background: {colors['warning']}; margin-right: 8px; border-radius: 3px; opacity: 0.7;"></div>
            <span>Epizootias positivas</span>
        </div>
        
        <div style="margin: 5px 0; display: flex; align-items: center;">
            <div style="width: 20px; height: 15px; background: #cccccc; margin-right: 8px; border-radius: 3px; opacity: 0.7;"></div>
            <span>Sin eventos</span>
        </div>
        
        <hr style="margin: 10px 0; border: 0; border-top: 1px solid #eee;">
        
        <div style="font-size: 11px; color: #666; line-height: 1.3;">
            💡 <strong>Interacciones:</strong><br>
            • 1 clic: Ver información<br>
            • 2 clics: Filtrar zona
        </div>
    </div>
    """
    
    folium_map.get_root().html.add_child(folium.Element(legend_html))


def create_navigation_controls(current_level, municipio_name=None):
    """
    Crea controles de navegación para el mapa.
    
    Args:
        current_level: Nivel actual ('departamento', 'municipio', 'vereda')
        municipio_name: Nombre del municipio actual
        
    Returns:
        str: HTML de los controles
    """
    
    controls_html = """
    <div style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        z-index: 9998;
    ">
    """
    
    # Botón para ver Tolima completo
    if current_level != 'departamento':
        controls_html += """
        <button onclick="resetMapView()" style="
            background: #7D0F2B;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 12px;
            cursor: pointer;
            box-shadow: 0 3px 10px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        " onmouseover="this.style.background='#5A4214'" onmouseout="this.style.background='#7D0F2B'">
            🔙 Ver Tolima
        </button>
        """
    
    # Botón para vista de municipio (si estamos en vereda)
    if current_level == 'vereda' and municipio_name:
        controls_html += f"""
        <button onclick="showMunicipioView()" style="
            background: #F2A900;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 12px;
            cursor: pointer;
            box-shadow: 0 3px 10px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        " onmouseover="this.style.background='#D69600'" onmouseout="this.style.background='#F2A900'">
            🔙 Ver {municipio_name[:15]}...
        </button>
        """
    
    controls_html += """
    </div>
    
    <script>
    function resetMapView() {
        // Enviar evento para resetear vista
        var event = new CustomEvent('resetMapView', {
            detail: { action: 'reset_to_department' }
        });
        window.dispatchEvent(event);
    }
    
    function showMunicipioView() {
        // Enviar evento para vista municipal
        var event = new CustomEvent('showMunicipioView', {
            detail: { action: 'back_to_municipio' }
        });
        window.dispatchEvent(event);
    }
    </script>
    """
    
    return controls_html


# Funciones de utilidad para eventos de mapa

def detect_double_click_from_session():
    """
    Detecta si hubo un doble clic basado en el estado de la sesión.
    
    Returns:
        bool: True si se detectó doble clic
    """
    
    return st.session_state.get("map_interactions_double_click", False)


def clear_map_interaction_flags():
    """
    Limpia las banderas de interacción del mapa.
    """
    
    for key in list(st.session_state.keys()):
        if key.startswith("map_interactions_"):
            del st.session_state[key]


def get_last_clicked_municipio():
    """
    Obtiene el último municipio clicado desde el estado de la sesión.
    
    Returns:
        str or None: Nombre del municipio o None
    """
    
    return st.session_state.get("map_interactions_last_municipio")