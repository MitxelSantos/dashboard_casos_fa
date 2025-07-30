"""
Utilidades OPTIMIZADAS para interacciones en mapas.
"""

import streamlit as st
import folium
import time
from typing import Dict, Any, Optional

def detect_map_click(map_data):
    """
    Detecta clic en mapa y extrae información del feature.
    
    Returns:
        dict: {'clicked': bool, 'feature_type': str, 'feature_name': str} o None
    """
    if not map_data or not map_data.get('last_object_clicked'):
        return None
    
    try:
        clicked_object = map_data['last_object_clicked']
        
        # Extraer información según el formato del objeto clicado
        if isinstance(clicked_object, dict):
            # Intentar obtener nombre del feature desde diferentes formatos
            feature_name = None
            feature_type = None
            
            # Para municipios
            if 'municipi_1' in str(clicked_object) or 'MpNombre' in str(clicked_object):
                feature_type = 'municipio'
                # Extraer nombre (implementación simple)
                if hasattr(clicked_object, 'get'):
                    feature_name = clicked_object.get('municipi_1') or clicked_object.get('MpNombre')
            
            # Para veredas
            elif 'vereda_nor' in str(clicked_object) or 'NOMBRE_VER' in str(clicked_object):
                feature_type = 'vereda'
                if hasattr(clicked_object, 'get'):
                    feature_name = clicked_object.get('vereda_nor') or clicked_object.get('NOMBRE_VER')
            
            if feature_name and feature_type:
                return {
                    'clicked': True,
                    'feature_type': feature_type,
                    'feature_name': str(feature_name).strip(),
                    'raw_data': clicked_object
                }
    
    except Exception as e:
        st.warning(f"Error procesando clic en mapa: {str(e)}")
    
    return None

def apply_map_filter(feature_info, available_data):
    """
    Aplica filtro basado en el feature clicado.
    
    Args:
        feature_info: Información del feature clicado
        available_data: Datos disponibles para validación
    
    Returns:
        dict: Resultado de la operación
    """
    if not feature_info or not feature_info.get('feature_name'):
        return {'success': False, 'message': 'No se pudo identificar el elemento clicado'}
    
    feature_name = feature_info['feature_name']
    feature_type = feature_info['feature_type']
    
    try:
        if feature_type == 'municipio':
            return apply_municipio_filter(feature_name, available_data)
        elif feature_type == 'vereda':
            return apply_vereda_filter(feature_name, available_data)
        else:
            return {'success': False, 'message': f'Tipo no reconocido: {feature_type}'}
    
    except Exception as e:
        return {'success': False, 'message': f'Error aplicando filtro: {str(e)}'}

def apply_municipio_filter(municipio_name, available_data):
    """Aplica filtro por municipio."""
    # Validar que el municipio existe
    municipios_disponibles = available_data.get('municipios_normalizados', [])
    
    if municipio_name not in municipios_disponibles:
        return {'success': False, 'message': f'Municipio no encontrado: {municipio_name}'}
    
    # Actualizar filtros en session_state
    st.session_state['municipio_filter'] = municipio_name
    st.session_state['vereda_filter'] = 'Todas'  # Resetear vereda
    
    return {
        'success': True,
        'message': f'✅ Filtrado por municipio: {municipio_name}',
        'action': 'municipio_filtered',
        'municipio': municipio_name
    }

def apply_vereda_filter(vereda_name, available_data):
    """Aplica filtro por vereda."""
    # Verificar que hay un municipio seleccionado
    current_municipio = st.session_state.get('municipio_filter', 'Todos')
    
    if current_municipio == 'Todos':
        return {'success': False, 'message': 'Debe seleccionar un municipio primero'}
    
    # Actualizar filtro de vereda
    st.session_state['vereda_filter'] = vereda_name
    
    return {
        'success': True,
        'message': f'✅ Filtrado por vereda: {vereda_name} ({current_municipio})',
        'action': 'vereda_filtered',
        'municipio': current_municipio,
        'vereda': vereda_name
    }

def create_map_navigation_buttons(filters, colors):
    """Crea botones de navegación para el mapa."""
    municipio_selected = filters.get('municipio_display', 'Todos')
    vereda_selected = filters.get('vereda_display', 'Todas')
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Botón "Ver Tolima"
        if municipio_selected != 'Todos':
            if st.button("🏛️ Ver Tolima", key="nav_tolima_btn"):
                st.session_state['municipio_filter'] = 'Todos'
                st.session_state['vereda_filter'] = 'Todas'
                st.rerun()
    
    with col2:
        # Botón "Ver Municipio" (solo si está en vista de vereda)
        if vereda_selected != 'Todas' and municipio_selected != 'Todos':
            if st.button(f"🏘️ Ver {municipio_selected[:12]}...", key="nav_municipio_btn"):
                st.session_state['vereda_filter'] = 'Todas'
                st.rerun()

def show_navigation_context(filters, colors):
    """Muestra contexto de navegación actual."""
    municipio = filters.get('municipio_display', 'Todos')
    vereda = filters.get('vereda_display', 'Todas')
    
    # Determinar nivel actual
    if vereda != 'Todas':
        nivel = f"📍 {vereda} ({municipio})"
        icon = "📍"
    elif municipio != 'Todos':
        nivel = f"🏘️ {municipio}"
        icon = "🏘️"
    else:
        nivel = "🏛️ Tolima"
        icon = "🏛️"
    
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            text-align: center;
            font-weight: 600;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            {icon} Vista actual: {nivel}
        </div>
        """,
        unsafe_allow_html=True
    )

def create_map_instructions(current_level, colors):
    """Crea instrucciones según el nivel actual del mapa."""
    instructions = {
        'departamento': "💡 Haga clic en cualquier municipio para ver sus veredas",
        'municipio': "💡 Haga clic en cualquier vereda para ver detalles específicos",
        'vereda': "💡 Vista detallada. Use los botones para navegar a otros niveles"
    }
    
    instruction_text = instructions.get(current_level, "💡 Navegue por el mapa para explorar")
    
    st.markdown(
        f"""
        <div style="
            background: {colors['light']};
            border-left: 4px solid {colors['info']};
            padding: 12px 16px;
            border-radius: 6px;
            margin: 10px 0;
            font-size: 0.9rem;
            color: {colors['dark']};
        ">
            {instruction_text}
        </div>
        """,
        unsafe_allow_html=True
    )

def process_map_interaction(map_data, available_data, colors):
    """
    Función principal para procesar interacciones del mapa.
    
    Args:
        map_data: Datos del mapa de st_folium
        available_data: Datos disponibles
        colors: Colores del tema
    
    Returns:
        dict: Resultado de la interacción
    """
    # Detectar clic
    click_info = detect_map_click(map_data)
    
    if not click_info:
        return {'type': 'none', 'message': 'Sin interacción'}
    
    # Aplicar filtro automáticamente al hacer clic
    filter_result = apply_map_filter(click_info, available_data)
    
    if filter_result['success']:
        # Mostrar mensaje de éxito
        st.success(filter_result['message'])
        
        # Forzar recarga de la página para aplicar filtros
        time.sleep(0.5)  # Pequeña pausa para que el usuario vea el mensaje
        st.rerun()
        
        return {
            'type': 'click_success',
            'feature': click_info,
            'result': filter_result,
            'message': filter_result['message']
        }
    else:
        # Mostrar error
        st.error(filter_result['message'])
        
        return {
            'type': 'click_error',
            'feature': click_info,
            'message': filter_result['message']
        }

def get_current_map_level(filters):
    """Determina el nivel actual del mapa según los filtros."""
    municipio = filters.get('municipio_display', 'Todos')
    vereda = filters.get('vereda_display', 'Todas')
    
    if vereda != 'Todas':
        return 'vereda'
    elif municipio != 'Todos':
        return 'municipio'
    else:
        return 'departamento'

def create_simple_popup(feature_type, name, casos=0, epizootias=0, colors=None):
    """
    Crea popup simple para features del mapa.
    
    Args:
        feature_type: 'municipio' o 'vereda'
        name: Nombre del feature
        casos: Número de casos
        epizootias: Número de epizootias
        colors: Diccionario de colores
    """
    if not colors:
        colors = {
            'primary': '#7D0F2B',
            'danger': '#E51937',
            'warning': '#F7941D',
            'info': '#4682B4'
        }
    
    icon = "📍" if feature_type == "municipio" else "🏘️"
    
    popup_html = f"""
    <div style="font-family: Arial, sans-serif; width: 200px; text-align: center;">
        <h4 style="color: {colors['primary']}; margin: 0 0 10px 0;">
            {icon} {name}
        </h4>
        
        <div style="display: flex; gap: 15px; justify-content: center; margin-bottom: 10px;">
            <div>
                <div style="font-size: 1.2em; font-weight: bold; color: {colors['danger']};">🦠 {casos}</div>
                <div style="font-size: 0.8em; color: #666;">Casos</div>
            </div>
            <div>
                <div style="font-size: 1.2em; font-weight: bold; color: {colors['warning']};">🐒 {epizootias}</div>
                <div style="font-size: 0.8em; color: #666;">Epizootias</div>
            </div>
        </div>
        
        <div style="background: {colors['info']}; color: white; padding: 6px; border-radius: 4px; font-size: 0.8em;">
            👆 Clic para filtrar
        </div>
    </div>
    """
    
    return popup_html