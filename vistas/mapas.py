"""
Vista de mapas CORREGIDA del dashboard de Fiebre Amarilla.
CORRECCIÓN PRINCIPAL:
- Fix en determine_map_level() para cambiar correctamente al mapa municipal al hacer click
- Limpieza de funciones obsoletas
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Importaciones opcionales para mapas
try:
    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium
    MAPS_AVAILABLE = True
except ImportError:
    MAPS_AVAILABLE = False

from utils.data_processor import (
    normalize_text, 
    calculate_basic_metrics,
    get_latest_case_info,
    format_time_elapsed,
    calculate_days_since
)

# Ruta de shapefiles procesados
PROCESSED_DIR = Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed")


def show(data_filtered, filters, colors):
    """
    Vista completa de mapas con tarjetas MEJORADAS.
    Layout: Columnas lado a lado (mapa | tarjetas estéticas mejoradas)
    """
    
    # CSS para las nuevas tarjetas mejoradas
    apply_enhanced_cards_css(colors)

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

    # **LAYOUT MEJORADO**: División en columnas lado a lado
    col_mapa, col_tarjetas = st.columns([3, 2])  # 60% mapa, 40% tarjetas
    
    with col_mapa:
        create_enhanced_map_system(casos, epizootias, geo_data, filters, colors, data_filtered)
    
    with col_tarjetas:
        create_beautiful_information_cards(casos, epizootias, filters, colors)


def create_enhanced_map_system(casos, epizootias, geo_data, filters, colors, data_filtered):
    """
    MEJORADO: Sistema de mapas con hover para tooltip y click para filtrar (SIN popup).
    """
    
    # Determinar nivel de mapa actual
    current_level = determine_map_level(filters)
    
    # Controles de navegación
    create_navigation_controls(current_level, filters, colors)
    
    # Indicador de filtrado activo
    show_filter_indicator(filters, colors)
    
    # Crear mapa según nivel con INTERACCIONES MEJORADAS
    if current_level == "departamento":
        create_departmental_map_enhanced(casos, epizootias, geo_data, colors)
    elif current_level == "municipio":
        create_municipal_map_enhanced(casos, epizootias, geo_data, filters, colors)
    elif current_level == "vereda":
        create_vereda_detail_view(casos, epizootias, filters, colors)


def determine_map_level(filters):
    """
    CORREGIDO: Determina el nivel de zoom del mapa según filtros activos.
    FIX: Corregidas las claves de los filtros para que funcione correctamente.
    """
    if filters.get("vereda_normalizada"):
        return "vereda"
    elif filters.get("municipio_normalizado"):  # ✅ CORREGIDO: era "municipio_normalizada"
        return "municipio"
    else:
        return "departamento"


def create_departmental_map_enhanced(casos, epizootias, geo_data, colors):
    """
    MEJORADO: Mapa departamental con hover para tooltip y click para filtrar (SIN popup).
    Maneja municipios grises (sin datos).
    """
    
    if 'municipios' not in geo_data:
        st.error("No se pudo cargar el shapefile de municipios")
        return
    
    municipios = geo_data['municipios'].copy()
    
    # Preparar datos agregados por municipio (INCLUYENDO MUNICIPIOS SIN DATOS)
    municipios_data = prepare_municipal_data_enhanced(casos, epizootias, municipios)
    
    # Obtener límites del Tolima
    bounds = municipios.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # **CONFIGURACIÓN MEJORADA**: Mapa fijo con interacciones optimizadas
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='CartoDB positron',
        zoom_control=False,
        scrollWheelZoom=False,
        doubleClickZoom=False,
        dragging=False,
        attributionControl=False,
        max_bounds=True,
        min_zoom=8,
        max_zoom=8
    )
    
    # Limitar navegación al área del Tolima
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    m.options['maxBounds'] = [[bounds[1] - 0.1, bounds[0] - 0.1], [bounds[3] + 0.1, bounds[2] + 0.1]]
    
    # Agregar municipios con INTERACCIONES MEJORADAS
    max_casos = municipios_data['casos'].max() if municipios_data['casos'].max() > 0 else 1
    max_epi = municipios_data['epizootias'].max() if municipios_data['epizootias'].max() > 0 else 1
    
    for idx, row in municipios_data.iterrows():
        municipio_name = row['MpNombre']
        casos_count = row['casos']
        fallecidos_count = row['fallecidos']
        epizootias_count = row['epizootias']
        epizootias_positivas = row.get('epizootias_positivas', 0)
        epizootias_en_estudio = row.get('epizootias_en_estudio', 0)
        
        # MEJORADO: Color según intensidad de datos (SIN análisis de riesgo)
        if casos_count > 0:
            # Municipios con casos humanos - rojo
            intensity = min(casos_count / max_casos, 1.0) if max_casos > 0 else 0
            fill_color = f"rgba(229, 25, 55, {0.4 + intensity * 0.5})"
            border_color = colors['danger']
        elif epizootias_count > 0:
            # Municipios solo con epizootias - naranja
            epi_intensity = min(epizootias_count / max_epi, 1.0) if max_epi > 0 else 0
            fill_color = f"rgba(247, 148, 29, {0.3 + epi_intensity * 0.4})"
            border_color = colors['warning']
        else:
            # Municipios sin datos - gris
            fill_color = "rgba(200, 200, 200, 0.3)"
            border_color = "#cccccc"
        
        # **TOOLTIP SOLO PARA HOVER** (información básica)
        tooltip_text = f"""
        <div style="font-family: Arial; padding: 8px; max-width: 200px;">
            <b style="color: {colors['primary']};">{municipio_name}</b><br>
            🦠 Casos: {casos_count}<br>
            🐒 Epizootias: {epizootias_count}<br>
            {'🔴 Positivas: ' + str(epizootias_positivas) + '<br>' if epizootias_positivas > 0 else ''}
            {'🔵 En estudio: ' + str(epizootias_en_estudio) + '<br>' if epizootias_en_estudio > 0 else ''}
            <i style="color: {colors['info']};">👆 Clic para filtrar</i>
        </div>
        """
        
        # **SIN POPUP** - Solo tooltip y funcionalidad de click
        # Agregar polígono con **INTERACCIONES OPTIMIZADAS**
        geojson = folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=fill_color, border=border_color: {
                'fillColor': color,
                'color': border,
                'weight': 2,
                'fillOpacity': 0.7,
                'opacity': 1
            },
            tooltip=folium.Tooltip(tooltip_text, sticky=True),  # **SOLO HOVER TOOLTIP**
            # NO popup - removido completamente
        )
        
        geojson.add_to(m)
    
    # Renderizar mapa con detección de clicks (SIN popups)
    map_data = st_folium(
        m, 
        width=700,
        height=500,
        returned_objects=["last_object_clicked"],  # **SOLO CLICKS**
        key="enhanced_main_map"
    )
    
    # **LÓGICA MEJORADA**: Procesar clicks (incluyendo municipios grises)
    handle_enhanced_click_interactions(map_data, municipios_data)


def create_municipal_map_enhanced(casos, epizootias, geo_data, filters, colors):
    """
    MEJORADO: Mapa municipal con veredas - hover y click sin popup.
    """
    
    if 'veredas' not in geo_data:
        st.warning("🗺️ Shapefile de veredas no disponible - mostrando información tabular")
        show_municipal_tabular_view(casos, epizootias, filters, colors)
        return
    
    municipio_normalizado = filters.get('municipio_normalizado')
    if not municipio_normalizado:
        st.error("No se pudo determinar el municipio para la vista de veredas")
        return
    
    # Filtrar veredas del municipio
    veredas = geo_data['veredas'].copy()
    
    # Intentar filtrar por diferentes campos posibles
    veredas_municipio = pd.DataFrame()
    for col in ['municipi_1', 'municipio', 'MUNICIPIO', 'Municipio']:
        if col in veredas.columns:
            veredas_temp = veredas[veredas[col].str.upper().str.strip() == municipio_normalizado.upper()]
            if not veredas_temp.empty:
                veredas_municipio = veredas_temp
                break
    
    if veredas_municipio.empty:
        st.warning(f"No se encontraron veredas para el municipio {filters.get('municipio_display', 'seleccionado')}")
        show_municipal_tabular_view(casos, epizootias, filters, colors)
        return
    
    # Preparar datos por vereda
    veredas_data = prepare_vereda_data_enhanced(casos, epizootias, veredas_municipio)
    
    # Obtener límites del municipio
    bounds = veredas_municipio.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Crear mapa de veredas
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB positron',
        zoom_control=False,
        scrollWheelZoom=False,
        doubleClickZoom=False,
        dragging=False,
        attributionControl=False,
    )
    
    # Ajustar vista al municipio
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    
    # Agregar veredas con interacciones mejoradas
    max_casos_vereda = veredas_data['casos'].max() if veredas_data['casos'].max() > 0 else 1
    max_epi_vereda = veredas_data['epizootias'].max() if veredas_data['epizootias'].max() > 0 else 1
    
    for idx, row in veredas_data.iterrows():
        vereda_name = row.get('NOMBRE_VER', row.get('vereda', f'Vereda_{idx}'))
        casos_count = row['casos']
        epizootias_count = row['epizootias']
        epizootias_positivas = row.get('epizootias_positivas', 0)
        epizootias_en_estudio = row.get('epizootias_en_estudio', 0)
        
        # Color según datos
        if casos_count > 0:
            intensity = min(casos_count / max_casos_vereda, 1.0)
            fill_color = f"rgba(229, 25, 55, {0.4 + intensity * 0.5})"
            border_color = colors['danger']
        elif epizootias_count > 0:
            intensity = min(epizootias_count / max_epi_vereda, 1.0)
            fill_color = f"rgba(247, 148, 29, {0.4 + intensity * 0.5})"
            border_color = colors['warning']
        else:
            fill_color = "rgba(200, 200, 200, 0.3)"
            border_color = "#cccccc"
        
        # Tooltip para hover (SIN popup)
        tooltip_text = f"""
        <div style="font-family: Arial; padding: 6px;">
            <b style="color: {colors['primary']};">{vereda_name}</b><br>
            🦠 Casos: {casos_count}<br>
            🐒 Epizootias: {epizootias_count}<br>
            {'🔴 Positivas: ' + str(epizootias_positivas) if epizootias_positivas > 0 else ''}
            {'🔵 En estudio: ' + str(epizootias_en_estudio) if epizootias_en_estudio > 0 else ''}<br>
            <i style="color: {colors['info']};">👆 Clic para filtrar</i>
        </div>
        """
        
        # Agregar vereda (SIN popup)
        geojson = folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=fill_color, border=border_color: {
                'fillColor': color,
                'color': border,
                'weight': 1.5,
                'fillOpacity': 0.6,
                'opacity': 1
            },
            tooltip=folium.Tooltip(tooltip_text, sticky=True),  # **SOLO HOVER**
            # NO popup
        )
        
        geojson.add_to(m)
    
    # Renderizar mapa
    map_data = st_folium(
        m, 
        width=700,
        height=500,
        returned_objects=["last_object_clicked"],
        key="enhanced_municipal_map"
    )
    
    # Procesar clicks en veredas
    handle_vereda_click_enhanced(map_data, veredas_data, filters)


def handle_enhanced_click_interactions(map_data, municipios_data):
    """
    MEJORADO: Maneja clicks incluyendo municipios sin datos (grises).
    """
    if not map_data or not map_data.get('last_object_clicked'):
        return
    
    try:
        clicked_object = map_data['last_object_clicked']
        
        # Verificar si es un click válido
        if isinstance(clicked_object, dict):
            # Buscar el municipio clicado en los datos
            clicked_lat = clicked_object.get('lat')
            clicked_lng = clicked_object.get('lng')
            
            if clicked_lat and clicked_lng:
                # Encontrar el municipio más cercano al punto clicado
                min_distance = float('inf')
                municipio_clicked = None
                
                for idx, row in municipios_data.iterrows():
                    # Calcular el centroide del municipio
                    centroid = row['geometry'].centroid
                    distance = ((centroid.x - clicked_lng)**2 + (centroid.y - clicked_lat)**2)**0.5
                    
                    if distance < min_distance:
                        min_distance = distance
                        municipio_clicked = row['MpNombre']
                        
                
                if municipio_clicked and min_distance < 0.1:  # Umbral de distancia
                    # **FILTRAR AUTOMÁTICAMENTE Y CAMBIAR VISTA** 
                    st.session_state['municipio_filter'] = municipio_clicked
                    
                    # NUEVO: Resetear vereda cuando se cambia municipio
                    st.session_state['vereda_filter'] = 'Todas'
                    
                    # **MENSAJE MEJORADO** según tenga datos o no
                    row_data = municipios_data[municipios_data['MpNombre'] == municipio_clicked].iloc[0]
                    tiene_datos = row_data['casos'] > 0 or row_data['epizootias'] > 0
                    
                    if tiene_datos:
                        st.success(f"✅ Filtrado por municipio: **{municipio_clicked}** ({row_data['casos']} casos, {row_data['epizootias']} epizootias)")
                        st.info("🗺️ El mapa ahora mostrará las veredas de este municipio")
                    else:
                        st.info(f"📍 Filtrado por municipio: **{municipio_clicked}** (sin datos registrados)")
                        st.warning("🗺️ Vista de veredas disponible pero sin datos para mostrar")
                    
                    # **ACTUALIZAR INMEDIATAMENTE**
                    st.rerun()
                    
    except Exception as e:
        st.warning(f"Error procesando clic en mapa: {str(e)}")


def handle_vereda_click_enhanced(map_data, veredas_data, filters):
    """
    MEJORADO: Maneja clicks en veredas.
    """
    if not map_data or not map_data.get('last_object_clicked'):
        return
    
    try:
        clicked_object = map_data['last_object_clicked']
        
        if isinstance(clicked_object, dict):
            clicked_lat = clicked_object.get('lat')
            clicked_lng = clicked_object.get('lng')
            
            if clicked_lat and clicked_lng:
                # Encontrar la vereda más cercana
                min_distance = float('inf')
                vereda_clicked = None
                vereda_data = None
                
                for idx, row in veredas_data.iterrows():
                    centroid = row['geometry'].centroid
                    distance = ((centroid.x - clicked_lng)**2 + (centroid.y - clicked_lat)**2)**0.5
                    
                    if distance < min_distance:
                        min_distance = distance
                        vereda_clicked = row.get('NOMBRE_VER', row.get('vereda', f'Vereda_{idx}'))
                        vereda_data = row
                
                if vereda_clicked and min_distance < 0.05:  # Umbral más pequeño para veredas
                    # **FILTRAR POR VEREDA**
                    st.session_state['vereda_filter'] = vereda_clicked
                    
                    # **MENSAJE CON INFORMACIÓN**
                    casos_count = vereda_data['casos']
                    epi_count = vereda_data['epizootias']
                    
                    if casos_count > 0 or epi_count > 0:
                        st.success(f"✅ Filtrado por vereda: **{vereda_clicked}** ({casos_count} casos, {epi_count} epizootias)")
                    else:
                        st.info(f"📍 Filtrado por vereda: **{vereda_clicked}** (sin datos registrados)")
                    
                    # **ACTUALIZAR**
                    st.rerun()
                    
    except Exception as e:
        st.warning(f"Error procesando clic en vereda: {str(e)}")


def create_navigation_controls(current_level, filters, colors):
    """Controles de navegación simplificados."""
    level_info = {
        "departamento": "🏛️ Vista Departamental - Tolima",
        "municipio": f"🏘️ {filters.get('municipio_display', 'Municipio')}",
        "vereda": f"📍 {filters.get('vereda_display', 'Vereda')} - {filters.get('municipio_display', 'Municipio')}"
    }
    
    current_info = level_info[current_level]
    
    # Botones de navegación
    cols = st.columns([1, 1])
    
    with cols[0]:
        if current_level != "departamento":
            if st.button("🏛️ Ver Tolima", key="nav_tolima_enhanced", use_container_width=True):
                reset_all_location_filters()
                st.rerun()
    
    with cols[1]:
        if current_level == "vereda":
            municipio_name = filters.get('municipio_display', 'Municipio')
            if st.button(f"🏘️ Ver {municipio_name[:10]}...", key="nav_municipio_enhanced", use_container_width=True):
                reset_vereda_filter_only()
                st.rerun()


def show_filter_indicator(filters, colors):
    """Indicador de filtrado activo simplificado."""
    active_filters = filters.get("active_filters", [])
    
    if active_filters:
        filters_text = " • ".join(active_filters[:2])  # Máximo 2 filtros
        
        if len(active_filters) > 2:
            filters_text += f" • +{len(active_filters) - 2} más"
        
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(45deg, {colors['info']}, {colors['warning']});
                color: white;
                padding: 8px 15px;
                border-radius: 20px;
                margin-bottom: 10px;
                text-align: center;
                font-size: 0.85rem;
                font-weight: 600;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            ">
                🎯 FILTROS: {filters_text}
            </div>
            """,
            unsafe_allow_html=True,
        )


def create_vereda_detail_view(casos, epizootias, filters, colors):
    """Vista detallada de vereda específica."""
    vereda_display = filters.get('vereda_display', 'Vereda')
    municipio_display = filters.get('municipio_display', 'Municipio')
    
    # Información de la vereda
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']});
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            <h3 style="margin: 0; font-size: 1.4rem;">📍 Vista Detallada</h3>
            <p style="margin: 10px 0 0 0; font-size: 1rem; opacity: 0.9;">
                <strong>{vereda_display}</strong> - {municipio_display}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Estadísticas de la vereda
    total_casos = len(casos)
    total_epizootias = len(epizootias)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🦠 Casos Humanos", total_casos)
    
    with col2:
        st.metric("🐒 Epizootias", total_epizootias)
    
    with col3:
        actividad_total = total_casos + total_epizootias
        st.metric("📊 Total Eventos", actividad_total)
    
    # Análisis específico de la vereda
    if total_casos > 0 or total_epizootias > 0:
        st.markdown("---")
        st.markdown("### 📊 Análisis Específico")
        
        # Casos por fecha si hay datos
        if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
            casos_fecha = casos.dropna(subset=["fecha_inicio_sintomas"])
            if not casos_fecha.empty:
                st.markdown("**📅 Casos por Fecha**")
                casos_temporal = casos_fecha.groupby(casos_fecha["fecha_inicio_sintomas"].dt.date).size().reset_index()
                casos_temporal.columns = ["Fecha", "Casos"]
                st.dataframe(casos_temporal, use_container_width=True, height=200)
        
        # Epizootias por fecha si hay datos
        if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
            epi_fecha = epizootias.dropna(subset=["fecha_recoleccion"])
            if not epi_fecha.empty:
                st.markdown("**📅 Epizootias por Fecha**")
                epi_temporal = epi_fecha.groupby(epi_fecha["fecha_recoleccion"].dt.date).size().reset_index()
                epi_temporal.columns = ["Fecha", "Epizootias"]
                st.dataframe(epi_temporal, use_container_width=True, height=200)
    else:
        st.info("📊 No hay eventos registrados en esta vereda con los filtros actuales")


def create_beautiful_information_cards(casos, epizootias, filters, colors):
    """
    NUEVAS: Tarjetas súper mejoradas con toda la información solicitada.
    """
    
    # Calcular métricas completas
    metrics = calculate_basic_metrics(casos, epizootias)
    
    # **TARJETA DE CASOS MEJORADA** con porcentaje de mortalidad y último caso
    create_enhanced_cases_card(metrics, colors)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # **TARJETA DE EPIZOOTIAS MEJORADA** con positivas + en estudio y último caso positivo
    create_enhanced_epizootias_card(metrics, colors)
    
    st.markdown("<br>", unsafe_allow_html=True)


def create_enhanced_cases_card(metrics, colors):
    """
    NUEVA: Tarjeta súper mejorada para casos con toda la información solicitada.
    """
    total_casos = metrics["total_casos"]
    vivos = metrics["vivos"]
    fallecidos = metrics["fallecidos"]
    letalidad = metrics["letalidad"]
    ultimo_caso = metrics["ultimo_caso"]
    
    # Información del último caso
    if ultimo_caso["existe"]:
        ultimo_info = f"""
        <div class="last-event-info">
            <div class="last-event-title">📍 Último Caso</div>
            <div class="last-event-details">
                <strong>{ultimo_caso["ubicacion"]}</strong><br>
                <span class="last-event-date">{ultimo_caso["fecha"].strftime("%d/%m/%Y") if ultimo_caso["fecha"] else "Sin fecha"}</span><br>
                <span class="last-event-time">Hace {ultimo_caso["tiempo_transcurrido"]}</span>
            </div>
        </div>
        """
    else:
        ultimo_info = f"""
        <div class="last-event-info">
            <div class="last-event-title">📍 Último Caso</div>
            <div class="last-event-details">
                <span class="no-data">Sin casos registrados</span>
            </div>
        </div>
        """
    
    st.markdown(
        f"""
        <div class="super-enhanced-card cases-card">
            <div class="card-header">
                <div class="card-icon">🦠</div>
                <div class="card-title">CASOS FIEBRE AMARILLA</div>
                <div class="card-subtitle">Vigilancia epidemiológica</div>
            </div>
            <div class="card-body">
                <div class="main-metrics-grid">
                    <div class="main-metric">
                        <div class="metric-number primary">{total_casos}</div>
                        <div class="metric-label">Total Casos</div>
                    </div>
                    <div class="main-metric">
                        <div class="metric-number success">{vivos}</div>
                        <div class="metric-label">Vivos</div>
                    </div>
                    <div class="main-metric">
                        <div class="metric-number danger">{fallecidos}</div>
                        <div class="metric-label">Fallecidos</div>
                    </div>
                    <div class="main-metric mortality">
                        <div class="metric-number warning">{letalidad:.1f}%</div>
                        <div class="metric-label">Mortalidad</div>
                    </div>
                </div>
                {ultimo_info}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_enhanced_epizootias_card(metrics, colors):
    """
    NUEVA: Tarjeta súper mejorada para epizootias con positivas + en estudio.
    """
    total_epizootias = metrics["total_epizootias"]
    positivas = metrics["epizootias_positivas"]
    en_estudio = metrics["epizootias_en_estudio"]
    ultima_epizootia = metrics["ultima_epizootia_positiva"]
    
    # Información de la última epizootia positiva
    if ultima_epizootia["existe"]:
        ultimo_info = f"""
        <div class="last-event-info">
            <div class="last-event-title">🔴 Último Positivo</div>
            <div class="last-event-details">
                <strong>{ultima_epizootia["ubicacion"]}</strong><br>
                <span class="last-event-date">{ultima_epizootia["fecha"].strftime("%d/%m/%Y") if ultima_epizootia["fecha"] else "Sin fecha"}</span><br>
                <span class="last-event-time">Hace {ultima_epizootia["tiempo_transcurrido"]}</span>
            </div>
        </div>
        """
    else:
        ultimo_info = f"""
        <div class="last-event-info">
            <div class="last-event-title">🔴 Último Positivo</div>
            <div class="last-event-details">
                <span class="no-data">Sin epizootias positivas</span>
            </div>
        </div>
        """
    
    st.markdown(
        f"""
        <div class="super-enhanced-card epizootias-card">
            <div class="card-header">
                <div class="card-icon">🐒</div>
                <div class="card-title">EPIZOOTIAS</div>
                <div class="card-subtitle">Vigilancia en fauna silvestre</div>
            </div>
            <div class="card-body">
                <div class="main-metrics-grid">
                    <div class="main-metric">
                        <div class="metric-number warning">{total_epizootias}</div>
                        <div class="metric-label">Total</div>
                    </div>
                    <div class="main-metric">
                        <div class="metric-number danger">{positivas}</div>
                        <div class="metric-label">Positivas</div>
                    </div>
                    <div class="main-metric">
                        <div class="metric-number info">{en_estudio}</div>
                        <div class="metric-label">En Estudio</div>
                    </div>
                </div>
                {ultimo_info}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )  


def apply_enhanced_cards_css(colors):
    """
    CSS súper mejorado para tarjetas hermosas y funcionales.
    """
    st.markdown(
        f"""
        <style>
        /* Título principal sin espaciado excesivo */
        .maps-title {{
            color: {colors['primary']};
            font-size: clamp(1.8rem, 5vw, 2.2rem);
            font-weight: 700;
            text-align: center;
            margin: 0.5rem 0 1rem 0;
            padding: 1rem;
            border-radius: 12px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-left: 6px solid {colors['secondary']};
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        /* Tarjetas súper mejoradas */
        .super-enhanced-card {{
            background: linear-gradient(135deg, white 0%, #fafafa 100%);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-bottom: 1.5rem;
            border: 1px solid #e1e5e9;
            transition: all 0.4s ease;
            position: relative;
        }}
        
        .super-enhanced-card:hover {{
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
            transform: translateY(-3px);
        }}
        
        .super-enhanced-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, {colors['primary']}, {colors['secondary']}, {colors['accent']});
        }}
        
        /* Headers específicos por tipo de tarjeta */
        .cases-card .card-header {{
            background: linear-gradient(135deg, {colors['danger']}, #e74c3c);
            color: white;
            padding: 20px;
        }}
        
        .epizootias-card .card-header {{
            background: linear-gradient(135deg, {colors['warning']}, #f39c12);
            color: white;
            padding: 20px;
        }}
        
        .location-card .card-header {{
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']});
            color: white;
            padding: 20px;
        }}
        
        .card-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            position: relative;
        }}
        
        .card-icon {{
            font-size: 2.2rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        }}
        
        .card-title {{
            font-size: 1.3rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            margin: 0;
        }}
        
        .card-subtitle {{
            font-size: 0.9rem;
            opacity: 0.9;
            font-weight: 500;
            margin: 2px 0 0 0;
        }}
        
        /* Cuerpo de tarjetas */
        .card-body {{
            padding: 25px;
        }}
        
        .main-metrics-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .main-metric {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            border: 2px solid transparent;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .main-metric:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .main-metric.mortality {{
            border-color: {colors['warning']};
            background: linear-gradient(135deg, #fff8e1, #ffecb3);
        }}
        
        .main-metric.laboratory {{
            border-color: {colors['info']};
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        }}
        
        .metric-number {{
            font-size: 1.8rem;
            font-weight: 800;
            margin-bottom: 5px;
            line-height: 1;
        }}
        
        .metric-number.primary {{ color: {colors['primary']}; }}
        .metric-number.success {{ color: {colors['success']}; }}
        .metric-number.danger {{ color: {colors['danger']}; }}
        .metric-number.warning {{ color: {colors['warning']}; }}
        .metric-number.info {{ color: {colors['info']}; }}
        
        .metric-label {{
            font-size: 0.8rem;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        
        /* Información del último evento */
        .last-event-info {{
            background: linear-gradient(135deg, #f0f8ff, #e6f3ff);
            border-radius: 12px;
            padding: 15px;
            border-left: 4px solid {colors['info']};
            margin-top: 15px;
        }}
        
        .last-event-title {{
            font-size: 0.9rem;
            font-weight: 700;
            color: {colors['primary']};
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .last-event-details {{
            font-size: 0.9rem;
            line-height: 1.4;
        }}
        
        .last-event-date {{
            color: {colors['info']};
            font-weight: 600;
        }}
        
        .last-event-time {{
            color: {colors['accent']};
            font-weight: 500;
            font-style: italic;
        }}
        
        .no-data {{
            color: #999;
            font-style: italic;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .main-metrics-grid {{
                grid-template-columns: 1fr;
                gap: 10px;
            }}
            
            .card-header {{
                padding: 15px;
            }}
            
            .card-body {{
                padding: 20px;
            }}
            
            .card-icon {{
                font-size: 1.8rem;
            }}
            
            .card-title {{
                font-size: 1.1rem;
            }}
            
            .metric-number {{
                font-size: 1.5rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# === FUNCIONES DE APOYO ===

def prepare_municipal_data_enhanced(casos, epizootias, municipios):
    """
    MEJORADO: Prepara datos por municipio incluyendo estadísticas de positivas + en estudio.
    """
    casos_por_municipio = {}
    fallecidos_por_municipio = {}
    
    if not casos.empty and 'municipio_normalizado' in casos.columns:
        casos_counts = casos.groupby('municipio_normalizado').size()
        casos_por_municipio = casos_counts.to_dict()
        
        if 'condicion_final' in casos.columns:
            fallecidos_counts = casos[casos['condicion_final'] == 'Fallecido'].groupby('municipio_normalizado').size()
            fallecidos_por_municipio = fallecidos_counts.to_dict()
    
    # NUEVAS ESTADÍSTICAS: Epizootias por tipo
    epizootias_por_municipio = {}
    positivas_por_municipio = {}
    en_estudio_por_municipio = {}
    
    if not epizootias.empty and 'municipio_normalizado' in epizootias.columns:
        epi_counts = epizootias.groupby('municipio_normalizado').size()
        epizootias_por_municipio = epi_counts.to_dict()
        
        if 'descripcion' in epizootias.columns:
            positivas_counts = epizootias[epizootias['descripcion'] == 'POSITIVO FA'].groupby('municipio_normalizado').size()
            positivas_por_municipio = positivas_counts.to_dict()
            
            en_estudio_counts = epizootias[epizootias['descripcion'] == 'EN ESTUDIO'].groupby('municipio_normalizado').size()
            en_estudio_por_municipio = en_estudio_counts.to_dict()
    
    # Combinar datos con shapefile
    municipios_data = municipios.copy()
    
    municipios_data['casos'] = municipios_data['municipi_1'].map(casos_por_municipio).fillna(0).astype(int)
    municipios_data['fallecidos'] = municipios_data['municipi_1'].map(fallecidos_por_municipio).fillna(0).astype(int)
    municipios_data['epizootias'] = municipios_data['municipi_1'].map(epizootias_por_municipio).fillna(0).astype(int)
    municipios_data['epizootias_positivas'] = municipios_data['municipi_1'].map(positivas_por_municipio).fillna(0).astype(int)
    municipios_data['epizootias_en_estudio'] = municipios_data['municipi_1'].map(en_estudio_por_municipio).fillna(0).astype(int)
    
    return municipios_data


def prepare_vereda_data_enhanced(casos, epizootias, veredas_gdf):
    """
    MEJORADO: Prepara datos por vereda con estadísticas completas.
    """
    casos_por_vereda = {}
    epizootias_por_vereda = {}
    positivas_por_vereda = {}
    en_estudio_por_vereda = {}
    
    # Contar casos por vereda
    if not casos.empty and 'vereda_normalizada' in casos.columns:
        for vereda_norm, group in casos.groupby('vereda_normalizada'):
            casos_por_vereda[vereda_norm.upper()] = len(group)
    
    # Contar epizootias por vereda (con desglose)
    if not epizootias.empty and 'vereda_normalizada' in epizootias.columns:
        for vereda_norm, group in epizootias.groupby('vereda_normalizada'):
            epizootias_por_vereda[vereda_norm.upper()] = len(group)
            
            if 'descripcion' in group.columns:
                positivas_por_vereda[vereda_norm.upper()] = len(group[group['descripcion'] == 'POSITIVO FA'])
                en_estudio_por_vereda[vereda_norm.upper()] = len(group[group['descripcion'] == 'EN ESTUDIO'])
    
    # Combinar con shapefile
    veredas_data = veredas_gdf.copy()
    
    # Intentar mapear con diferentes campos
    for col in ['NOMBRE_VER', 'vereda', 'Vereda']:
        if col in veredas_data.columns:
            veredas_data['casos'] = veredas_data[col].str.upper().str.strip().map(casos_por_vereda).fillna(0).astype(int)
            veredas_data['epizootias'] = veredas_data[col].str.upper().str.strip().map(epizootias_por_vereda).fillna(0).astype(int)
            veredas_data['epizootias_positivas'] = veredas_data[col].str.upper().str.strip().map(positivas_por_vereda).fillna(0).astype(int)
            veredas_data['epizootias_en_estudio'] = veredas_data[col].str.upper().str.strip().map(en_estudio_por_vereda).fillna(0).astype(int)
            break
    
    # Si no se pudo mapear, llenar con 0
    for col in ['casos', 'epizootias', 'epizootias_positivas', 'epizootias_en_estudio']:
        if col not in veredas_data.columns:
            veredas_data[col] = 0
    
    return veredas_data


def reset_all_location_filters():
    """Resetea todos los filtros de ubicación"""
    if "municipio_filter" in st.session_state:
        st.session_state.municipio_filter = "Todos"
    if "vereda_filter" in st.session_state:
        st.session_state.vereda_filter = "Todas"


def reset_vereda_filter_only():
    """Resetea solo el filtro de vereda"""
    if "vereda_filter" in st.session_state:
        st.session_state.vereda_filter = "Todas"


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
        
        return geo_data
        
    except Exception as e:
        st.error(f"❌ Error cargando datos geográficos: {str(e)}")
        return None


def show_municipal_tabular_view(casos, epizootias, filters, colors):
    """Vista tabular cuando no hay shapefiles de veredas."""
    municipio_display = filters.get('municipio_display', 'Municipio')
    
    st.info(f"🗺️ Vista tabular para {municipio_display} (mapa de veredas no disponible)")
    
    # Mostrar datos por vereda en tablas
    if not casos.empty and "vereda" in casos.columns:
        st.markdown("**📊 Casos por Vereda**")
        vereda_casos = casos["vereda"].value_counts().head(10)
        if not vereda_casos.empty:
            st.dataframe(vereda_casos.to_frame("Casos"), use_container_width=True)
        else:
            st.info("No hay casos registrados por vereda")
    
    if not epizootias.empty and "vereda" in epizootias.columns:
        st.markdown("**📊 Epizootias por Vereda**")
        vereda_epi = epizootias["vereda"].value_counts().head(10)
        if not vereda_epi.empty:
            st.dataframe(vereda_epi.to_frame("Epizootias"), use_container_width=True)
        else:
            st.info("No hay epizootias registradas por vereda")


def show_maps_not_available():
    """Muestra mensaje cuando las librerías de mapas no están disponibles."""
    st.error("⚠️ Librerías de mapas no instaladas. Instale: geopandas folium streamlit-folium")


def show_shapefiles_setup_instructions():
    """Muestra instrucciones para configurar shapefiles."""
    st.error("🗺️ Shapefiles no encontrados en la ruta configurada")


def show_geographic_data_error():
    """Muestra mensaje de error al cargar datos geográficos."""
    st.error("❌ Error al cargar datos geográficos")