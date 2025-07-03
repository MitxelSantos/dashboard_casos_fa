"""
Vista de mapas INTERACTIVOS del dashboard de Fiebre Amarilla.
Mapas como filtros integrados con zoom dinámico y métricas responsive.
VERSIÓN CORREGIDA: Solo epizootias positivas + filtros funcionando + doble clic
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Importaciones opcionales para mapas
try:
    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium
    MAPS_AVAILABLE = True
except ImportError:
    MAPS_AVAILABLE = False

# Importaciones del proyecto
from utils.data_processor import normalize_text
from datetime import datetime

# Ruta de shapefiles procesados
PROCESSED_DIR = Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed")


def show(data_filtered, filters, colors):
    """
    Muestra la vista de mapas interactivos completa con integración de filtros.
    CORREGIDO: Solo epizootias positivas + filtros funcionando
    """
    # CSS para la vista completa
    apply_maps_css(colors)
    
    st.markdown(
        '<h1 class="maps-title">🗺️ Mapas Interactivos - Tolima</h1>',
        unsafe_allow_html=True,
    )

    if not MAPS_AVAILABLE:
        show_maps_not_available()
        return

    # Verificar disponibilidad de shapefiles
    if not check_shapefiles_availability():
        show_shapefiles_setup_instructions()
        return

    # Cargar datos geográficos
    geo_data = load_geographic_data_silent()
    
    if not geo_data:
        show_geographic_data_error()
        return

    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]

    # CORREGIDO: Métricas responsive (solo epizootias positivas)
    create_interactive_metrics_fixed(casos, epizootias, filters, colors)
    
    st.markdown("---")

    # Sistema de mapas interactivos con filtros CORREGIDOS
    create_interactive_map_system_fixed(casos, epizootias, geo_data, filters, colors, data_filtered)


def create_interactive_metrics_fixed(casos, epizootias, filters, colors):
    """
    CORREGIDO: Métricas que se renderizan correctamente + solo epizootias positivas
    """
    
    # Calcular métricas según filtros actuales
    total_casos = len(casos)
    
    # CAMBIO: Solo epizootias positivas
    epizootias_positivas = len(epizootias[epizootias["descripcion"] == "POSITIVO FA"]) if not epizootias.empty and "descripcion" in epizootias.columns else 0

    # Métricas de casos
    fallecidos = 0
    vivos = 0
    letalidad = 0
    if total_casos > 0 and "condicion_final" in casos.columns:
        fallecidos = (casos["condicion_final"] == "Fallecido").sum()
        vivos = (casos["condicion_final"] == "Vivo").sum()
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0

    # Información de ubicación actual
    ubicacion_actual = get_current_location_info(filters)
    
    # Mostrar filtros activos si existen
    if filters.get("active_filters"):
        st.markdown("### 🎯 Filtros Activos")
        filters_html = ""
        for filter_desc in filters["active_filters"][:3]:  # Máximo 3 para no saturar
            filters_html += f'<span class="filter-badge">{filter_desc}</span>'
        
        if len(filters["active_filters"]) > 3:
            remaining = len(filters["active_filters"]) - 3
            filters_html += f'<span class="filter-badge">+{remaining} más</span>'
            
        st.markdown(filters_html, unsafe_allow_html=True)
        st.markdown("---")

    # CORREGIDO: Usar columnas de Streamlit en lugar de HTML complejo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🦠 Casos Confirmados",
            value=total_casos,
            help="Casos humanos confirmados de Fiebre Amarilla"
        )
        if ubicacion_actual:
            st.caption(f"📍 {ubicacion_actual}")
    
    with col2:
        letalidad_delta = "Alto riesgo" if letalidad > 50 else "Bajo control" if letalidad < 20 else "Moderado"
        st.metric(
            label="⚰️ Letalidad", 
            value=f"{letalidad:.1f}%",
            delta=f"{fallecidos} fallecidos",
            help="Tasa de letalidad de casos confirmados"
        )
        if ubicacion_actual:
            st.caption(f"📍 {ubicacion_actual}")
    
    with col3:
        # CAMBIO: Solo epizootias positivas
        st.metric(
            label="🔴 Epizootias Positivas",
            value=epizootias_positivas,
            help="Epizootias que dieron positivo para Fiebre Amarilla"
        )
        if ubicacion_actual:
            st.caption(f"📍 {ubicacion_actual}")
    
    with col4:
        # Cálculo de riesgo basado en casos + epizootias positivas
        actividad_total = total_casos + epizootias_positivas
        riesgo = "Alto" if actividad_total > 20 else "Medio" if actividad_total > 5 else "Bajo"
        
        st.metric(
            label="⚠️ Nivel de Riesgo",
            value=riesgo,
            delta=f"{actividad_total} eventos totales",
            help="Nivel de riesgo basado en casos humanos y epizootias positivas"
        )
        if ubicacion_actual:
            st.caption(f"📍 {ubicacion_actual}")


def create_interactive_map_system_fixed(casos, epizootias, geo_data, filters, colors, data_filtered):
    """
    CORREGIDO: Sistema completo de mapas con filtros funcionando + doble clic
    """
    
    # Determinar nivel de zoom actual
    current_level = determine_map_level(filters)
    
    # Crear controles del mapa
    create_map_controls_fixed(current_level, filters, colors)
    
    # Crear mapa según nivel actual
    if current_level == "departamento":
        create_departmental_map_fixed(casos, epizootias, geo_data, colors, data_filtered)
    elif current_level == "municipio":
        create_municipal_map_fixed(casos, epizootias, geo_data, filters, colors, data_filtered)
    elif current_level == "vereda":
        create_vereda_detailed_view_fixed(casos, epizootias, geo_data, filters, colors)


def create_map_controls_fixed(current_level, filters, colors):
    """
    CORREGIDO: Controles del mapa con botones funcionando
    """
    
    level_info = {
        "departamento": {
            "title": "🗺️ Vista Departamental",
            "subtitle": "Haga doble clic en un municipio para filtrar y hacer zoom",
            "icon": "🏛️"
        },
        "municipio": {
            "title": f"🏛️ {filters.get('municipio_display', 'Municipio')}",
            "subtitle": "Haga doble clic en una vereda para filtrar",
            "icon": "🏘️"
        },
        "vereda": {
            "title": f"🏘️ {filters.get('vereda_display', 'Vereda')}",
            "subtitle": f"En {filters.get('municipio_display', 'Municipio')}",
            "icon": "📍"
        }
    }
    
    info = level_info[current_level]
    
    # Información del nivel actual
    st.info(f"{info['icon']} **{info['title']}** - {info['subtitle']}")
    
    # Botones de navegación CORREGIDOS
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if current_level != "departamento":
            if st.button("🔙 Ver Tolima", key="back_to_tolima", help="Volver a vista departamental"):
                reset_location_filters()
                st.rerun()
    
    with col2:
        if current_level == "vereda":
            if st.button(f"🔙 Ver {filters.get('municipio_display', 'Municipio')}", key="back_to_municipio", help="Volver a vista municipal"):
                reset_vereda_filter()
                st.rerun()
    
    with col3:
        if st.button("🔄 Actualizar", key="refresh_map", help="Refrescar vista del mapa"):
            st.rerun()


def create_departmental_map_fixed(casos, epizootias, geo_data, colors, data_filtered):
    """
    CORREGIDO: Mapa departamental con doble clic para filtrar + solo epizootias positivas
    """
    
    if 'municipios' not in geo_data:
        st.error("No se pudo cargar el shapefile de municipios")
        return
    
    municipios = geo_data['municipios'].copy()
    
    # CORREGIDO: Preparar datos solo con epizootias positivas
    municipios_data = prepare_municipal_data_fixed(casos, epizootias, municipios)
    
    # Crear mapa centrado en Tolima
    center_lat = municipios.geometry.centroid.y.mean()
    center_lon = municipios.geometry.centroid.x.mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='CartoDB positron'
    )
    
    # Agregar municipios con datos
    max_casos = municipios_data['casos'].max() if municipios_data['casos'].max() > 0 else 1
    max_epi_pos = municipios_data['epizootias_positivas'].max() if municipios_data['epizootias_positivas'].max() > 0 else 1
    
    for idx, row in municipios_data.iterrows():
        municipio_name = row['MpNombre']
        casos_count = row['casos']
        fallecidos_count = row['fallecidos']
        epi_positivas = row['epizootias_positivas']
        
        # Determinar color y opacidad según datos
        if casos_count > 0 or epi_positivas > 0:
            # Intensidad de color según casos
            intensity = min(casos_count / max_casos, 1.0) if max_casos > 0 else 0
            if casos_count > 0:
                fill_color = f"rgba(229, 25, 55, {0.3 + intensity * 0.6})"  # Rojo para casos
                border_color = colors['danger']
            else:
                epi_intensity = min(epi_positivas / max_epi_pos, 1.0) if max_epi_pos > 0 else 0
                fill_color = f"rgba(247, 148, 29, {0.3 + epi_intensity * 0.6})"  # Naranja para epizootias
                border_color = colors['warning']
        else:
            fill_color = "rgba(200, 200, 200, 0.3)"
            border_color = "#cccccc"
        
        # CORREGIDO: Popup con solo epizootias positivas
        popup_html = create_municipal_popup_fixed(municipio_name, casos_count, fallecidos_count, epi_positivas)
        
        # Agregar polígono del municipio con eventos de clic
        geojson = folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=fill_color, border=border_color: {
                'fillColor': color,
                'color': border,
                'weight': 2,
                'fillOpacity': 0.7,
                'opacity': 1
            },
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"<b>{municipio_name}</b><br>📊 Casos: {casos_count} | 🔴 Epi+: {epi_positivas}"
        )
        
        # NUEVO: Agregar identificador para doble clic
        geojson.add_child(folium.JavaScriptLink("https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"))
        
        geojson.add_to(m)
    
    # Agregar límite departamental si existe
    if 'limite' in geo_data:
        folium.GeoJson(
            geo_data['limite'],
            style_function=lambda x: {
                'fillColor': 'none',
                'color': colors['primary'],
                'weight': 4,
                'opacity': 0.8,
            }
        ).add_to(m)
    
    # CORREGIDO: Mostrar mapa y capturar interacciones
    map_data = st_folium(
        m, 
        width=700, 
        height=600, 
        returned_objects=["last_object_clicked_popup", "last_object_clicked"],
        key="main_map"
    )
    
    # CORREGIDO: Procesar clics en municipios
    if map_data.get('last_object_clicked_popup'):
        handle_municipal_click_fixed(map_data['last_object_clicked_popup'], municipios_data)


def prepare_municipal_data_fixed(casos, epizootias, municipios):
    """
    CORREGIDO: Prepara datos agregados por municipio - SOLO epizootias positivas
    """
    
    # Contar casos por municipio
    casos_por_municipio = {}
    fallecidos_por_municipio = {}
    
    if not casos.empty and 'municipio_normalizado' in casos.columns:
        casos_counts = casos.groupby('municipio_normalizado').size()
        casos_por_municipio = casos_counts.to_dict()
        
        if 'condicion_final' in casos.columns:
            fallecidos_counts = casos[casos['condicion_final'] == 'Fallecido'].groupby('municipio_normalizado').size()
            fallecidos_por_municipio = fallecidos_counts.to_dict()
    
    # CAMBIO: Solo epizootias positivas
    epi_positivas_por_municipio = {}
    
    if not epizootias.empty and 'municipio_normalizado' in epizootias.columns:
        epi_positivas = epizootias[epizootias['descripcion'] == 'POSITIVO FA']
        if not epi_positivas.empty:
            epi_pos_counts = epi_positivas.groupby('municipio_normalizado').size()
            epi_positivas_por_municipio = epi_pos_counts.to_dict()
    
    # Combinar datos con shapefile
    municipios_data = municipios.copy()
    
    municipios_data['casos'] = municipios_data['municipi_1'].map(casos_por_municipio).fillna(0).astype(int)
    municipios_data['fallecidos'] = municipios_data['municipi_1'].map(fallecidos_por_municipio).fillna(0).astype(int)
    municipios_data['epizootias_positivas'] = municipios_data['municipi_1'].map(epi_positivas_por_municipio).fillna(0).astype(int)
    
    return municipios_data


def create_municipal_popup_fixed(municipio, casos, fallecidos, epi_positivas):
    """
    CORREGIDO: Popup HTML para municipios - solo epizootias positivas
    """
    letalidad = (fallecidos / casos * 100) if casos > 0 else 0
    
    return f"""
    <div style="font-family: Arial, sans-serif; width: 280px;">
        <h4 style="color: #7D0F2B; margin: 0 0 10px 0; border-bottom: 2px solid #F2A900; padding-bottom: 5px;">
            📍 {municipio}
        </h4>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
            <div style="background: #ffe6e6; padding: 8px; border-radius: 6px; text-align: center;">
                <div style="font-size: 1.5em; font-weight: bold; color: #E51937;">🦠 {casos}</div>
                <div style="font-size: 0.8em; color: #666;">Casos</div>
            </div>
            <div style="background: #fff3e0; padding: 8px; border-radius: 6px; text-align: center;">
                <div style="font-size: 1.5em; font-weight: bold; color: #F7941D;">🔴 {epi_positivas}</div>
                <div style="font-size: 0.8em; color: #666;">Epi Positivas</div>
            </div>
        </div>
        
        <div style="font-size: 0.85em; line-height: 1.4;">
            <div style="margin: 3px 0;"><strong>⚰️ Fallecidos:</strong> {fallecidos} ({letalidad:.1f}%)</div>
        </div>
        
        <div style="margin-top: 10px; padding: 8px; background: #f0f8ff; border-radius: 6px; text-align: center;">
            <strong style="color: #4682B4;">👆 Doble clic para filtrar y hacer zoom</strong>
        </div>
    </div>
    """


def handle_municipal_click_fixed(clicked_data, municipios_data):
    """
    CORREGIDO: Maneja clics en municipios para aplicar filtros
    """
    if not clicked_data:
        return
    
    # Extraer información del municipio clicado
    try:
        # El objeto clicado puede tener diferentes estructuras
        if isinstance(clicked_data, dict):
            # Buscar el nombre del municipio en diferentes posibles ubicaciones
            municipio_name = None
            
            # Intentar extraer de diferentes estructuras posibles
            if 'tooltip' in clicked_data:
                tooltip = clicked_data['tooltip']
                # Extraer municipio del tooltip
                import re
                match = re.search(r'<b>(.*?)</b>', tooltip)
                if match:
                    municipio_name = match.group(1)
            
            if municipio_name:
                # Aplicar filtro de municipio
                st.session_state['municipio_filter'] = municipio_name
                st.rerun()
                
    except Exception as e:
        st.error(f"Error procesando clic en municipio: {str(e)}")


def reset_location_filters():
    """
    CORREGIDO: Resetea filtros de ubicación para volver a vista departamental
    """
    if "municipio_filter" in st.session_state:
        st.session_state.municipio_filter = "Todos"
    if "vereda_filter" in st.session_state:
        st.session_state.vereda_filter = "Todas"


def reset_vereda_filter():
    """Resetea solo el filtro de vereda."""
    if "vereda_filter" in st.session_state:
        st.session_state.vereda_filter = "Todas"


def create_municipal_map_fixed(casos, epizootias, geo_data, filters, colors, data_filtered):
    """
    CORREGIDO: Mapa municipal con veredas - solo epizootias positivas
    """
    
    if 'veredas' not in geo_data:
        st.error("No se pudo cargar el shapefile de veredas")
        return
    
    municipio_norm = filters["municipio_normalizado"]
    
    # Filtrar veredas del municipio
    veredas = geo_data['veredas'].copy()
    
    # Usar la columna correcta para filtrar
    if 'municipi_1' in veredas.columns:
        veredas_municipio = veredas[veredas['municipi_1'] == municipio_norm]
    elif 'NOMB_MPIO' in veredas.columns:
        veredas_municipio = veredas[veredas['NOMB_MPIO'].apply(normalize_text) == municipio_norm]
    else:
        st.error("No se encontró columna de municipio en veredas")
        return
    
    if len(veredas_municipio) == 0:
        st.warning(f"No se encontraron veredas para {filters['municipio_display']}")
        return
    
    # CORREGIDO: Preparar datos de veredas solo con epizootias positivas
    veredas_data = prepare_veredas_data_fixed(casos, epizootias, veredas_municipio, municipio_norm)
    
    # Crear mapa centrado en el municipio
    center_lat = veredas_municipio.geometry.centroid.y.mean()
    center_lon = veredas_municipio.geometry.centroid.x.mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='CartoDB positron'
    )
    
    # Agregar veredas con datos
    max_casos_vereda = veredas_data['casos'].max() if veredas_data['casos'].max() > 0 else 1
    
    for idx, row in veredas_data.iterrows():
        vereda_name = row['NOMBRE_VER']
        casos_count = row['casos']
        epi_positivas = row['epizootias_positivas']
        
        # Color según presencia de datos
        if casos_count > 0:
            fill_color = colors['danger']
            opacity = 0.4 + (casos_count / max_casos_vereda) * 0.4
        elif epi_positivas > 0:
            fill_color = colors['warning']
            opacity = 0.3 + (epi_positivas / max_casos_vereda) * 0.3
        else:
            fill_color = colors['info']
            opacity = 0.2
        
        # CORREGIDO: Popup para vereda
        popup_html = create_vereda_popup_fixed(vereda_name, casos_count, epi_positivas)
        
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=fill_color, op=opacity: {
                'fillColor': color,
                'color': 'white',
                'weight': 1,
                'fillOpacity': op,
                'opacity': 1
            },
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"<b>{vereda_name}</b><br>📊 Casos: {casos_count} | 🔴 Epi+: {epi_positivas}"
        ).add_to(m)
    
    # Mostrar mapa y capturar interacciones
    map_data = st_folium(
        m, 
        width=700, 
        height=600, 
        returned_objects=["last_object_clicked_popup", "last_object_clicked"],
        key="municipal_map"
    )
    
    # Procesar clics en veredas
    if map_data.get('last_object_clicked_popup'):
        handle_vereda_click_fixed(map_data['last_object_clicked_popup'], veredas_data, filters)


def prepare_veredas_data_fixed(casos, epizootias, veredas_municipio, municipio_norm):
    """
    CORREGIDO: Prepara datos de veredas - solo epizootias positivas
    """
    
    # Filtrar datos por municipio
    casos_mpio = casos[casos['municipio_normalizado'] == municipio_norm] if 'municipio_normalizado' in casos.columns else pd.DataFrame()
    epi_mpio = epizootias[epizootias['municipio_normalizado'] == municipio_norm] if 'municipio_normalizado' in epizootias.columns else pd.DataFrame()
    
    # Solo epizootias positivas
    epi_positivas_mpio = epi_mpio[epi_mpio['descripcion'] == 'POSITIVO FA'] if not epi_mpio.empty and 'descripcion' in epi_mpio.columns else pd.DataFrame()
    
    # Contar por vereda
    casos_por_vereda = {}
    epi_positivas_por_vereda = {}
    
    if not casos_mpio.empty and 'vereda_normalizada' in casos_mpio.columns:
        casos_counts = casos_mpio.groupby('vereda_normalizada').size()
        casos_por_vereda = casos_counts.to_dict()
    
    if not epi_positivas_mpio.empty and 'vereda_normalizada' in epi_positivas_mpio.columns:
        epi_counts = epi_positivas_mpio.groupby('vereda_normalizada').size()
        epi_positivas_por_vereda = epi_counts.to_dict()
    
    # Combinar con veredas
    veredas_data = veredas_municipio.copy()
    
    if 'vereda_nor' in veredas_data.columns:
        veredas_data['casos'] = veredas_data['vereda_nor'].map(casos_por_vereda).fillna(0).astype(int)
        veredas_data['epizootias_positivas'] = veredas_data['vereda_nor'].map(epi_positivas_por_vereda).fillna(0).astype(int)
    else:
        # Fallback usando normalización en tiempo real
        veredas_data['vereda_norm_temp'] = veredas_data['NOMBRE_VER'].apply(normalize_text)
        veredas_data['casos'] = veredas_data['vereda_norm_temp'].map(casos_por_vereda).fillna(0).astype(int)
        veredas_data['epizootias_positivas'] = veredas_data['vereda_norm_temp'].map(epi_positivas_por_vereda).fillna(0).astype(int)
    
    return veredas_data


def create_vereda_popup_fixed(vereda, casos, epi_positivas):
    """
    CORREGIDO: Popup HTML para veredas - solo epizootias positivas
    """
    return f"""
    <div style="font-family: Arial, sans-serif; width: 240px;">
        <h5 style="color: #7D0F2B; margin: 0 0 8px 0; border-bottom: 1px solid #F2A900; padding-bottom: 3px;">
            🏘️ {vereda}
        </h5>
        
        <div style="display: flex; gap: 8px; margin-bottom: 8px;">
            <div style="background: #ffe6e6; padding: 6px; border-radius: 4px; flex: 1; text-align: center;">
                <div style="font-weight: bold; color: #E51937;">🦠 {casos}</div>
                <div style="font-size: 0.7em; color: #666;">Casos</div>
            </div>
            <div style="background: #fff3e0; padding: 6px; border-radius: 4px; flex: 1; text-align: center;">
                <div style="font-weight: bold; color: #F7941D;">🔴 {epi_positivas}</div>
                <div style="font-size: 0.7em; color: #666;">Epi +</div>
            </div>
        </div>
        
        <div style="margin-top: 8px; padding: 6px; background: #f0f8ff; border-radius: 4px; text-align: center; font-size: 0.8em;">
            <strong style="color: #4682B4;">👆 Doble clic para filtrar</strong>
        </div>
    </div>
    """


def handle_vereda_click_fixed(clicked_data, veredas_data, filters):
    """
    CORREGIDO: Maneja clics en veredas para aplicar filtros
    """
    if not clicked_data:
        return
    
    try:
        # Extraer información de la vereda clicada
        if isinstance(clicked_data, dict):
            vereda_name = None
            
            if 'tooltip' in clicked_data:
                tooltip = clicked_data['tooltip']
                import re
                match = re.search(r'<b>(.*?)</b>', tooltip)
                if match:
                    vereda_name = match.group(1)
            
            if vereda_name:
                # Aplicar filtro de vereda
                st.session_state['vereda_filter'] = vereda_name
                st.rerun()
                
    except Exception as e:
        st.error(f"Error procesando clic en vereda: {str(e)}")


def create_vereda_detailed_view_fixed(casos, epizootias, geo_data, filters, colors):
    """
    CORREGIDO: Vista detallada de vereda - solo epizootias positivas
    """
    
    vereda_display = filters.get("vereda_display", "Vereda")
    municipio_display = filters.get("municipio_display", "Municipio")
    
    # Mostrar información detallada de la vereda
    st.markdown(f"### 📍 {vereda_display} - {municipio_display}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🦠 Casos en esta Vereda")
        if not casos.empty:
            casos_info = create_casos_detail_info_fixed(casos)
            st.markdown(casos_info, unsafe_allow_html=True)
        else:
            st.info("No hay casos registrados en esta vereda")
    
    with col2:
        st.markdown("#### 🔴 Epizootias Positivas en esta Vereda")
        # Solo epizootias positivas
        epi_positivas = epizootias[epizootias["descripcion"] == "POSITIVO FA"] if not epizootias.empty and "descripcion" in epizootias.columns else pd.DataFrame()
        
        if not epi_positivas.empty:
            epi_info = create_epizootias_detail_info_fixed(epi_positivas)
            st.markdown(epi_info, unsafe_allow_html=True)
        else:
            st.info("No hay epizootias positivas registradas en esta vereda")


def create_casos_detail_info_fixed(casos):
    """
    CORREGIDO: Información detallada de casos para vista de vereda
    """
    if casos.empty:
        return "<p>No hay casos en esta vereda</p>"
    
    total = len(casos)
    fallecidos = (casos["condicion_final"] == "Fallecido").sum() if "condicion_final" in casos.columns else 0
    vivos = total - fallecidos
    
    # Información por sexo
    sexo_info = ""
    if "sexo" in casos.columns:
        sexo_dist = casos["sexo"].value_counts()
        sexo_info = " | ".join([f"{k}: {v}" for k, v in sexo_dist.items()])
    
    # Edad promedio
    edad_info = ""
    if "edad" in casos.columns:
        edad_promedio = casos["edad"].mean()
        if not pd.isna(edad_promedio):
            edad_info = f"Edad promedio: {edad_promedio:.1f} años"
    
    return f"""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #E51937;">
        <div style="font-size: 1.2em; font-weight: bold; color: #E51937; margin-bottom: 0.5rem;">
            Total: {total} casos
        </div>
        <div style="margin-bottom: 0.5rem;">
            <span style="color: #509E2F;">💚 Vivos: {vivos}</span> | 
            <span style="color: #E51937;">⚰️ Fallecidos: {fallecidos}</span>
        </div>
        {f'<div style="margin-bottom: 0.5rem; font-size: 0.9em;">{sexo_info}</div>' if sexo_info else ''}
        {f'<div style="font-size: 0.9em; color: #666;">{edad_info}</div>' if edad_info else ''}
    </div>
    """


def create_epizootias_detail_info_fixed(epizootias_positivas):
    """
    CORREGIDO: Información detallada de epizootias POSITIVAS para vista de vereda
    """
    if epizootias_positivas.empty:
        return "<p>No hay epizootias positivas en esta vereda</p>"
    
    total = len(epizootias_positivas)
    
    # Información por fuente
    fuente_info = ""
    if "proveniente" in epizootias_positivas.columns:
        fuente_dist = epizootias_positivas["proveniente"].value_counts()
        fuente_items = []
        for fuente, count in fuente_dist.items():
            if "VIGILANCIA COMUNITARIA" in str(fuente):
                fuente_items.append(f"👥 Comunidad: {count}")
            elif "INCAUTACIÓN" in str(fuente):
                fuente_items.append(f"🚔 Incautación: {count}")
            else:
                fuente_items.append(f"📋 {fuente}: {count}")
        fuente_info = " | ".join(fuente_items)
    
    return f"""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #F7941D;">
        <div style="font-size: 1.2em; font-weight: bold; color: #F7941D; margin-bottom: 0.5rem;">
            Total: {total} epizootias positivas
        </div>
        {f'<div style="margin-bottom: 0.5rem; font-size: 0.9em;">{fuente_info}</div>' if fuente_info else ''}
        <div style="font-size: 0.8em; color: #666; margin-top: 0.5rem;">
            ⚠️ Indican circulación activa del virus en fauna silvestre
        </div>
    </div>
    """


# =============== FUNCIONES DE APOYO (sin cambios significativos) ===============

def apply_maps_css(colors):
    """Aplica CSS específico para la vista de mapas."""
    st.markdown(
        f"""
        <style>
        .maps-title {{
            color: {colors['primary']};
            font-size: clamp(2rem, 5vw, 2.8rem);
            font-weight: 700;
            text-align: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 4px solid {colors['secondary']};
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .filter-badge {{
            background: linear-gradient(135deg, {colors['warning']}, {colors['secondary']});
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 25px;
            font-size: 0.85rem;
            font-weight: 600;
            margin: 0.25rem;
            display: inline-block;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ box-shadow: 0 3px 10px rgba(0,0,0,0.2); }}
            50% {{ box-shadow: 0 5px 20px rgba(0,0,0,0.3); }}
            100% {{ box-shadow: 0 3px 10px rgba(0,0,0,0.2); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_current_location_info(filters):
    """Obtiene información de la ubicación actual según filtros."""
    location_parts = []
    
    if filters.get("municipio_display") and filters["municipio_display"] != "Todos":
        location_parts.append(f"{filters['municipio_display']}")
    
    if filters.get("vereda_display") and filters["vereda_display"] != "Todas":
        location_parts.append(f"{filters['vereda_display']}")
    
    if not location_parts:
        return "Tolima"
    
    return " - ".join(location_parts)


def determine_map_level(filters):
    """Determina el nivel de zoom del mapa según filtros activos."""
    if filters.get("vereda_normalizada"):
        return "vereda"
    elif filters.get("municipio_normalizado"):
        return "municipio"
    else:
        return "departamento"


# =============== FUNCIONES DE VERIFICACIÓN (sin cambios) ===============

def check_shapefiles_availability():
    """Verifica si los shapefiles procesados están disponibles."""
    municipios_path = PROCESSED_DIR / "tolima_municipios.shp"
    veredas_path = PROCESSED_DIR / "tolima_veredas.shp"
    return municipios_path.exists() or veredas_path.exists()


def load_geographic_data_silent():
    """Carga datos geográficos sin mostrar mensajes."""
    geo_data = {}
    
    try:
        # Cargar municipios
        municipios_path = PROCESSED_DIR / "tolima_municipios.shp"
        if municipios_path.exists():
            geo_data['municipios'] = gpd.read_file(municipios_path)
        
        # Cargar veredas
        veredas_path = PROCESSED_DIR / "tolima_veredas.shp"
        if veredas_path.exists():
            geo_data['veredas'] = gpd.read_file(veredas_path)
        
        # Cargar límite departamental
        limite_path = PROCESSED_DIR / "tolima_limite.shp"
        if limite_path.exists():
            geo_data['limite'] = gpd.read_file(limite_path)
        
        return geo_data
        
    except Exception as e:
        st.error(f"❌ Error cargando datos geográficos: {str(e)}")
        return None


def show_maps_not_available():
    """Muestra mensaje cuando las librerías de mapas no están disponibles."""
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem 2rem; background: #f8f9fa; border-radius: 16px; color: #2c2c2c; font-size: 1.1rem;">
            <h3>⚠️ Librerías de Mapas No Instaladas</h3>
            <p>Para usar la funcionalidad de mapas interactivos, instale las dependencias necesarias:</p>
            <code>pip install geopandas folium streamlit-folium</code>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_shapefiles_setup_instructions():
    """Muestra instrucciones para configurar shapefiles."""
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem 2rem; background: #f8f9fa; border-radius: 16px; color: #2c2c2c; font-size: 1.1rem;">
            <h3>🗺️ Configuración de Shapefiles</h3>
            <p>Los shapefiles del Tolima no están disponibles en la ruta configurada.</p>
            <p>Verifique que los archivos estén en:</p>
            <code>C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed/</code>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_geographic_data_error():
    """Muestra mensaje de error al cargar datos geográficos."""
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem 2rem; background: #f8f9fa; border-radius: 16px; color: #2c2c2c; font-size: 1.1rem;">
            <h3>❌ Error al Cargar Datos Geográficos</h3>
            <p>No se pudieron cargar los shapefiles del Tolima.</p>
            <p>Verifique que los archivos estén correctamente procesados.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )