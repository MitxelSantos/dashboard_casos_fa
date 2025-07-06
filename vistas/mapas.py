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
import logging

# Importaciones opcionales para mapas
try:
    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium
    MAPS_AVAILABLE = True
except ImportError:
    MAPS_AVAILABLE = False

from utils.data_processor import (
    calculate_basic_metrics,
    get_latest_case_info,
    excel_date_to_datetime
)

# Ruta de shapefiles procesados
PROCESSED_DIR = Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed")


def show(data_filtered, filters, colors):
    """
    CORREGIDO: Vista completa de mapas con datos filtrados.
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

    # **USAR DATOS FILTRADOS**
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # **LOG PARA VERIFICAR FILTRADO**
    total_casos_filtrados = len(casos)
    total_epi_filtradas = len(epizootias)
    
    logging.info(f"🗺️ Vista mapas - Datos filtrados: {total_casos_filtrados} casos, {total_epi_filtradas} epizootias")
    
    # Mostrar información de filtrado si hay filtros activos
    active_filters = filters.get("active_filters", [])
    if active_filters:
        st.info(f"🎯 Mostrando datos filtrados: {' • '.join(active_filters[:2])}")

    # **LAYOUT MEJORADO**: División en columnas lado a lado
    col_mapa, col_tarjetas = st.columns([3, 2])  # 60% mapa, 40% tarjetas
    
    with col_mapa:
        create_enhanced_map_system(casos, epizootias, geo_data, filters, colors, data_filtered)
    
    with col_tarjetas:
        # **PASAR DATOS FILTRADOS A LAS TARJETAS**
        create_beautiful_information_cards(casos, epizootias, filters, colors)

def create_enhanced_map_system(casos, epizootias, geo_data, filters, colors, data_filtered):
    """
    CORREGIDO: Sistema de mapas con logging mejorado.
    """
    
    # Log de datos recibidos
    logging.info(f"🗺️ Sistema mapas recibió: {len(casos)} casos, {len(epizootias)} epizootias")
    
    # Determinar nivel de mapa actual
    current_level = determine_map_level(filters)
    
    # Controles de navegación
    create_navigation_controls(current_level, filters, colors)
    
    # Indicador de filtrado activo
    show_filter_indicator(filters, colors)
    
    # Crear mapa según nivel con datos filtrados
    if current_level == "departamento":
        logging.info("🏛️ Creando mapa departamental con datos filtrados")
        create_departmental_map_enhanced(casos, epizootias, geo_data, colors)
    elif current_level == "municipio":
        logging.info(f"🏘️ Creando mapa municipal para {filters.get('municipio_display')} con datos filtrados")
        create_municipal_map_enhanced(casos, epizootias, geo_data, filters, colors)
    elif current_level == "vereda":
        logging.info(f"📍 Creando vista de vereda {filters.get('vereda_display')} con datos filtrados")
        create_vereda_detail_view(casos, epizootias, filters, colors)

def determine_map_level(filters):
    """
    SIMPLIFICADO: Determina el nivel de zoom del mapa según filtros activos.
    Usa nombres directos sin normalización.
    """
    if filters.get("vereda_display") and filters.get("vereda_display") != "Todas":
        return "vereda"
    elif filters.get("municipio_display") and filters.get("municipio_display") != "Todos":
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
    CORREGIDO: Mapa municipal con manejo seguro de veredas grises.
    """
    
    if 'veredas' not in geo_data:
        st.warning("🗺️ Shapefile de veredas no disponible - mostrando información tabular")
        show_municipal_tabular_view(casos, epizootias, filters, colors)
        return
    
    municipio_selected = filters.get('municipio_display')
    if not municipio_selected or municipio_selected == "Todos":
        st.error("No se pudo determinar el municipio para la vista de veredas")
        return
    
    # Filtrar veredas del municipio usando nombres directos
    veredas = geo_data['veredas'].copy()
    
    # Filtrar por municipi_1 que ahora coincide exactamente con los datos
    veredas_municipio = veredas[veredas['municipi_1'] == municipio_selected]
    
    if veredas_municipio.empty:
        st.warning(f"No se encontraron veredas para el municipio {municipio_selected}")
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
    
    # CREAR TOOLTIPS SEGUROS PARA TODAS LAS VEREDAS
    max_casos_vereda = veredas_data['casos'].max() if veredas_data['casos'].max() > 0 else 1
    max_epi_vereda = veredas_data['epizootias'].max() if veredas_data['epizootias'].max() > 0 else 1
    
    for idx, row in veredas_data.iterrows():
        vereda_name = row['vereda_nor']  # Usar nombre directo del shapefile
        casos_count = row['casos']
        epizootias_count = row['epizootias']
        epizootias_positivas = row.get('epizootias_positivas', 0)
        epizootias_en_estudio = row.get('epizootias_en_estudio', 0)
        
        # Color según datos
        if casos_count > 0:
            intensity = min(casos_count / max_casos_vereda, 1.0)
            fill_color = f"rgba(229, 25, 55, {0.4 + intensity * 0.5})"
            border_color = colors['danger']
            status_info = f"Con {casos_count} casos"
        elif epizootias_count > 0:
            intensity = min(epizootias_count / max_epi_vereda, 1.0)
            fill_color = f"rgba(247, 148, 29, {0.4 + intensity * 0.5})"
            border_color = colors['warning']
            status_info = f"Con {epizootias_count} epizootias"
        else:
            # VEREDAS GRISES - SIN DATOS
            fill_color = "rgba(200, 200, 200, 0.3)"
            border_color = "#cccccc"
            status_info = "Sin datos registrados"
        
        # TOOLTIP SEGURO PARA TODAS LAS VEREDAS (incluso grises)
        tooltip_text = f"""
        <div style="font-family: Arial; padding: 8px; max-width: 220px;">
            <b style="color: {colors['primary']};">{vereda_name}</b><br>
            <span style="color: #666;">{status_info}</span><br>
            🦠 Casos: {casos_count}<br>
            🐒 Epizootias: {epizootias_count}
        """
        
        # Solo agregar detalles si hay datos
        if epizootias_positivas > 0 or epizootias_en_estudio > 0:
            tooltip_text += f"<br>🔴 Positivas: {epizootias_positivas}"
            tooltip_text += f"<br>🔵 En estudio: {epizootias_en_estudio}"
        
        # Instrucciones de clic (solo si hay datos o es seleccionable)
        if casos_count > 0 or epizootias_count > 0:
            tooltip_text += f"<br><i style='color: {colors['info']};'>👆 Clic para filtrar</i>"
        else:
            tooltip_text += f"<br><i style='color: #999;'>📍 Vereda sin eventos</i>"
        
        tooltip_text += "</div>"
        
        # AGREGAR VEREDA CON TOOLTIP SEGURO
        try:
            geojson = folium.GeoJson(
                row['geometry'],
                style_function=lambda x, color=fill_color, border=border_color: {
                    'fillColor': color,
                    'color': border,
                    'weight': 1.5,
                    'fillOpacity': 0.6,
                    'opacity': 1
                },
                tooltip=folium.Tooltip(
                    tooltip_text, 
                    sticky=True,
                    style="font-size: 12px;"
                ),
            )
            
            geojson.add_to(m)
            
        except Exception as e:
            # FALLBACK: Si falla el tooltip, crear uno básico
            logging.warning(f"⚠️ Error creando tooltip para {vereda_name}: {str(e)}")
            
            basic_tooltip = f"<b>{vereda_name}</b><br>📊 {status_info}"
            
            basic_geojson = folium.GeoJson(
                row['geometry'],
                style_function=lambda x, color=fill_color, border=border_color: {
                    'fillColor': color,
                    'color': border,
                    'weight': 1.5,
                    'fillOpacity': 0.6,
                    'opacity': 1
                },
                tooltip=folium.Tooltip(basic_tooltip, sticky=True),
            )
            
            basic_geojson.add_to(m)
    
    # Renderizar mapa con manejo seguro de errores
    try:
        map_data = st_folium(
            m, 
            width=700,
            height=500,
            returned_objects=["last_object_clicked"],
            key="enhanced_municipal_map_safe"
        )
        
        # Procesar clicks de forma segura
        handle_vereda_click_safe(map_data, veredas_data, filters)
        
    except Exception as e:
        logging.error(f"❌ Error renderizando mapa: {str(e)}")
        st.error("Error mostrando el mapa de veredas")
        show_municipal_tabular_view(casos, epizootias, filters, colors)
        
def log_data_filtering_info(data_original, data_filtered, filters):
    """
    NUEVA: Log detallado del filtrado para debugging.
    """
    casos_orig = len(data_original.get("casos", []))
    epi_orig = len(data_original.get("epizootias", []))
    
    casos_filt = len(data_filtered.get("casos", []))
    epi_filt = len(data_filtered.get("epizootias", []))
    
    active_filters = filters.get("active_filters", [])
    
    logging.info(f"📊 Filtrado aplicado:")
    logging.info(f"   📍 Filtros: {len(active_filters)} activos")
    logging.info(f"   🦠 Casos: {casos_orig} → {casos_filt} ({((casos_orig-casos_filt)/casos_orig*100):.1f}% filtrado)" if casos_orig > 0 else f"   🦠 Casos: 0 → 0")
    logging.info(f"   🐒 Epizootias: {epi_orig} → {epi_filt} ({((epi_orig-epi_filt)/epi_orig*100):.1f}% filtrado)" if epi_orig > 0 else f"   🐒 Epizootias: 0 → 0")
    
    if active_filters:
        for i, filtro in enumerate(active_filters[:3]):
            logging.info(f"   🎯 {i+1}. {filtro}")

def handle_vereda_click_safe(map_data, veredas_data, filters):
    """
    NUEVA: Manejo seguro de clicks en veredas (incluso grises).
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
                    try:
                        centroid = row['geometry'].centroid
                        distance = ((centroid.x - clicked_lng)**2 + (centroid.y - clicked_lat)**2)**0.5
                        
                        if distance < min_distance:
                            min_distance = distance
                            vereda_clicked = row['vereda_nor']
                            vereda_data = row
                    except Exception as e:
                        logging.warning(f"⚠️ Error calculando distancia para vereda: {str(e)}")
                        continue
                
                if vereda_clicked and min_distance < 0.05:
                    # **FILTRAR POR VEREDA (incluso si es gris)**
                    st.session_state['vereda_filter'] = vereda_clicked
                    
                    # **MENSAJE CON INFORMACIÓN APROPIADA**
                    casos_count = vereda_data['casos'] if vereda_data is not None else 0
                    epi_count = vereda_data['epizootias'] if vereda_data is not None else 0
                    
                    if casos_count > 0 or epi_count > 0:
                        st.success(f"✅ Filtrado por vereda: **{vereda_clicked}** ({casos_count} casos, {epi_count} epizootias)")
                    else:
                        st.info(f"📍 Filtrado por vereda: **{vereda_clicked}** (sin datos registrados)")
                        st.caption("💡 Esta vereda existe en el territorio pero no tiene eventos de vigilancia registrados")
                    
                    # **ACTUALIZAR SIN CAUSAR BUCLE**
                    st.rerun()
                    
    except Exception as e:
        logging.error(f"❌ Error procesando clic en vereda: {str(e)}")
        st.warning("⚠️ Error procesando clic en el mapa. Intente usar los filtros del sidebar.")

def handle_enhanced_click_interactions(map_data, municipios_data):
    """
    SIMPLIFICADO: Maneja clicks usando nombres directos de shapefiles.
    ELIMINADA toda la lógica de normalización.
    """
    if not map_data or not map_data.get('last_object_clicked'):
        return
    
    try:
        clicked_object = map_data['last_object_clicked']
        
        if isinstance(clicked_object, dict):
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
                        # Usar el nombre del shapefile directamente
                        municipio_clicked = row['municipi_1']  # Nombre directo del shapefile
                        
                if municipio_clicked and min_distance < 0.1:
                    # **FILTRAR AUTOMÁTICAMENTE Y CAMBIAR VISTA** 
                    st.session_state['municipio_filter'] = municipio_clicked
                    
                    # Resetear vereda cuando se cambia municipio
                    st.session_state['vereda_filter'] = 'Todas'
                    
                    # **MENSAJE MEJORADO** 
                    row_data = municipios_data[municipios_data['municipi_1'] == municipio_clicked].iloc[0]
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
    SIMPLIFICADO: Maneja clicks en veredas usando nombres directos.
    ELIMINADA toda la lógica de normalización.
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
                        # Usar el nombre del shapefile directamente
                        vereda_clicked = row['vereda_nor']  # Nombre directo del shapefile
                        vereda_data = row
                
                if vereda_clicked and min_distance < 0.05:
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
    """
    CORREGIDO: Vista detallada de vereda específica con filtrado correcto.
    """
    def normalize_name(name):
        """Normaliza nombres para comparación consistente."""
        if pd.isna(name) or name == "":
            return ""
        return str(name).upper().strip()
    
    vereda_display = filters.get('vereda_display', 'Vereda')
    municipio_display = filters.get('municipio_display', 'Municipio')
    
    # Normalizar nombres para filtrado
    vereda_norm = normalize_name(vereda_display)
    municipio_norm = normalize_name(municipio_display)
    
    # FILTRAR DATOS ESPECÍFICAMENTE POR VEREDA
    casos_vereda = pd.DataFrame()
    epizootias_vereda = pd.DataFrame()
    
    # Filtrar casos por vereda específica
    if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
        casos_vereda = casos[
            (casos["vereda"].apply(normalize_name) == vereda_norm) &
            (casos["municipio"].apply(normalize_name) == municipio_norm)
        ].copy()
    
    # Filtrar epizootias por vereda específica
    if not epizootias.empty and "vereda" in epizootias.columns and "municipio" in epizootias.columns:
        epizootias_vereda = epizootias[
            (epizootias["vereda"].apply(normalize_name) == vereda_norm) &
            (epizootias["municipio"].apply(normalize_name) == municipio_norm)
        ].copy()
    
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
    
    # Estadísticas específicas de la vereda
    total_casos = len(casos_vereda)
    total_epizootias = len(epizootias_vereda)
    
    # Conteos específicos por tipo de epizootia
    positivas_vereda = 0
    en_estudio_vereda = 0
    if not epizootias_vereda.empty and "descripcion" in epizootias_vereda.columns:
        positivas_vereda = len(epizootias_vereda[epizootias_vereda["descripcion"] == "POSITIVO FA"])
        en_estudio_vereda = len(epizootias_vereda[epizootias_vereda["descripcion"] == "EN ESTUDIO"])
    
    # Métricas específicas de la vereda
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🦠 Casos Humanos", total_casos, 
                 help=f"Casos registrados específicamente en {vereda_display}")
    
    with col2:
        st.metric("🔴 Epiz. Positivas", positivas_vereda,
                 help="Epizootias confirmadas positivas para fiebre amarilla")
    
    with col3:
        st.metric("🔵 En Estudio", en_estudio_vereda,
                 help="Epizootias con resultado pendiente")
    
    with col4:
        actividad_total = total_casos + total_epizootias
        st.metric("📊 Total Eventos", actividad_total,
                 help="Total de eventos de vigilancia en esta vereda")
    
    # Log para debugging
    logging.info(f"📍 Vista vereda {vereda_display}: {total_casos} casos, {total_epizootias} epizootias")
    
    # Análisis específico de la vereda
    if total_casos > 0 or total_epizootias > 0:
        st.markdown("---")
        st.markdown("### 📊 Análisis Específico de la Vereda")
        
        # Crear dos columnas para casos y epizootias
        col_casos, col_epi = st.columns(2)
        
        with col_casos:
            st.markdown("#### 🦠 Casos en esta Vereda")
            
            if not casos_vereda.empty:
                # Tabla de casos con todas las columnas relevantes
                casos_display = casos_vereda.copy()
                
                # Preparar columnas para mostrar
                columnas_mostrar = []
                if "fecha_inicio_sintomas" in casos_display.columns:
                    casos_display["Fecha Síntomas"] = casos_display["fecha_inicio_sintomas"].dt.strftime('%d/%m/%Y')
                    columnas_mostrar.append("Fecha Síntomas")
                if "edad" in casos_display.columns:
                    columnas_mostrar.append("edad")
                if "sexo" in casos_display.columns:
                    columnas_mostrar.append("sexo")
                if "condicion_final" in casos_display.columns:
                    casos_display["Condición"] = casos_display["condicion_final"]
                    columnas_mostrar.append("Condición")
                
                if columnas_mostrar:
                    st.dataframe(casos_display[columnas_mostrar], use_container_width=True, height=300)
                else:
                    st.dataframe(casos_display.head(), use_container_width=True, height=300)
                
                # Estadísticas de casos
                if "condicion_final" in casos_vereda.columns:
                    fallecidos_vereda = len(casos_vereda[casos_vereda["condicion_final"] == "Fallecido"])
                    vivos_vereda = len(casos_vereda[casos_vereda["condicion_final"] == "Vivo"])
                    letalidad_vereda = (fallecidos_vereda / total_casos * 100) if total_casos > 0 else 0
                    
                    st.markdown(f"""
                    **📊 Estadísticas:**
                    - 💚 Vivos: {vivos_vereda}
                    - ⚰️ Fallecidos: {fallecidos_vereda}
                    - 📈 Letalidad: {letalidad_vereda:.1f}%
                    """)
            else:
                st.info("📭 No hay casos registrados en esta vereda")
        
        with col_epi:
            st.markdown("#### 🐒 Epizootias en esta Vereda")
            
            if not epizootias_vereda.empty:
                # Tabla de epizootias
                epi_display = epizootias_vereda.copy()
                
                columnas_epi = []
                if "fecha_recoleccion" in epi_display.columns:
                    epi_display["Fecha Recolección"] = epi_display["fecha_recoleccion"].dt.strftime('%d/%m/%Y')
                    columnas_epi.append("Fecha Recolección")
                if "descripcion" in epi_display.columns:
                    epi_display["Resultado"] = epi_display["descripcion"]
                    columnas_epi.append("Resultado")
                if "proveniente" in epi_display.columns:
                    epi_display["Fuente"] = epi_display["proveniente"].apply(
                        lambda x: "Vigilancia Com." if "VIGILANCIA" in str(x) else "Incautación" if "INCAUTACIÓN" in str(x) else str(x)[:20]
                    )
                    columnas_epi.append("Fuente")
                
                if columnas_epi:
                    st.dataframe(epi_display[columnas_epi], use_container_width=True, height=300)
                else:
                    st.dataframe(epi_display.head(), use_container_width=True, height=300)
                
                # Estadísticas de epizootias
                st.markdown(f"""
                **📊 Estadísticas:**
                - 🔴 Positivas: {positivas_vereda}
                - 🔵 En estudio: {en_estudio_vereda}
                - 📈 Total: {total_epizootias}
                """)
            else:
                st.info("📭 No hay epizootias registradas en esta vereda")
        
        # Análisis temporal si hay datos
        st.markdown("---")
        st.markdown("#### 📅 Análisis Temporal de la Vereda")
        
        if not casos_vereda.empty and "fecha_inicio_sintomas" in casos_vereda.columns:
            casos_fecha = casos_vereda.dropna(subset=["fecha_inicio_sintomas"])
            if not casos_fecha.empty:
                st.markdown("**📊 Casos por Fecha**")
                casos_temporal = casos_fecha.groupby(casos_fecha["fecha_inicio_sintomas"].dt.date).size().reset_index()
                casos_temporal.columns = ["Fecha", "Casos"]
                st.dataframe(casos_temporal, use_container_width=True, height=200)
        
        if not epizootias_vereda.empty and "fecha_recoleccion" in epizootias_vereda.columns:
            epi_fecha = epizootias_vereda.dropna(subset=["fecha_recoleccion"])
            if not epi_fecha.empty:
                st.markdown("**📊 Epizootias por Fecha**")
                epi_temporal = epi_fecha.groupby(epi_fecha["fecha_recoleccion"].dt.date).size().reset_index()
                epi_temporal.columns = ["Fecha", "Epizootias"]
                st.dataframe(epi_temporal, use_container_width=True, height=200)
        
        # Información de contexto
        st.markdown("---")
        st.markdown(f"""
        ℹ️ **Información de Contexto:**
        - Esta vista muestra únicamente los datos registrados en la vereda **{vereda_display}**
        - Los datos incluyen casos humanos confirmados y epizootias (positivas + en estudio)
        - Use los filtros del sidebar o navegue con los botones para cambiar la vista
        """)
        
    else:
        st.info(f"📊 No hay eventos registrados en la vereda **{vereda_display}** con los filtros actuales")
        
        # Sugerir verificar filtros
        st.markdown("""
        💡 **Sugerencias:**
        - Verifique que los filtros de fecha no estén muy restrictivos
        - Esta vereda puede no tener eventos registrados en el período seleccionado
        - Use los botones de navegación para volver a la vista municipal o departamental
        """)

def create_beautiful_information_cards(casos, epizootias, filters, colors):
    """
    CORREGIDO: Tarjetas que usan datos filtrados en lugar de datos totales.
    """
    
    # USAR DATOS FILTRADOS para calcular métricas
    metrics = calculate_basic_metrics(casos, epizootias)
    
    # **TARJETA DE CASOS MEJORADA** con datos filtrados
    create_enhanced_cases_card_filtered(metrics, filters, colors)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # **TARJETA DE EPIZOOTIAS MEJORADA** con datos filtrados
    create_enhanced_epizootias_card_filtered(metrics, filters, colors)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
def create_enhanced_cases_card_filtered(metrics, filters, colors):
    """
    NUEVA: Tarjeta de casos con información de filtrado aplicado.
    """
    total_casos = metrics["total_casos"]
    vivos = metrics["vivos"]
    fallecidos = metrics["fallecidos"]
    letalidad = metrics["letalidad"]
    ultimo_caso = metrics["ultimo_caso"]
    
    # Determinar contexto de filtrado
    filter_context = get_filter_context_info(filters)
    
    # Información del último caso
    if ultimo_caso["existe"]:
        ultimo_info = f"""
        <div class="last-event-info">
            <div class="last-event-title">📍 Último Caso {filter_context["suffix"]}</div>
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
            <div class="last-event-title">📍 Último Caso {filter_context["suffix"]}</div>
            <div class="last-event-details">
                <span class="no-data">Sin casos registrados{filter_context["suffix"].lower()}</span>
            </div>
        </div>
        """
    
    st.markdown(
        f"""
        <div class="super-enhanced-card cases-card">
            <div class="card-header">
                <div class="card-icon">🦠</div>
                <div class="card-title">CASOS FIEBRE AMARILLA</div>
                <div class="card-subtitle">{filter_context["title"]}</div>
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

def create_enhanced_epizootias_card_filtered(metrics, filters, colors):
    """
    NUEVA: Tarjeta de epizootias con información de filtrado aplicado.
    """
    total_epizootias = metrics["total_epizootias"]
    positivas = metrics["epizootias_positivas"]
    en_estudio = metrics["epizootias_en_estudio"]
    ultima_epizootia = metrics["ultima_epizootia_positiva"]
    
    # Determinar contexto de filtrado
    filter_context = get_filter_context_info(filters)
    
    # Información de la última epizootia positiva
    if ultima_epizootia["existe"]:
        ultimo_info = f"""
        <div class="last-event-info">
            <div class="last-event-title">🔴 Último Positivo {filter_context["suffix"]}</div>
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
            <div class="last-event-title">🔴 Último Positivo {filter_context["suffix"]}</div>
            <div class="last-event-details">
                <span class="no-data">Sin epizootias positivas{filter_context["suffix"].lower()}</span>
            </div>
        </div>
        """
    
    st.markdown(
        f"""
        <div class="super-enhanced-card epizootias-card">
            <div class="card-header">
                <div class="card-icon">🐒</div>
                <div class="card-title">EPIZOOTIAS</div>
                <div class="card-subtitle">{filter_context["title"]}</div>
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

def get_filter_context_info(filters):
    """
    NUEVA: Obtiene información del contexto de filtrado para mostrar en tarjetas.
    """
    municipio = filters.get("municipio_display", "Todos")
    vereda = filters.get("vereda_display", "Todas")
    
    if vereda != "Todas":
        return {
            "title": f"Vigilancia en {vereda}",
            "suffix": f"en {vereda}"
        }
    elif municipio != "Todos":
        return {
            "title": f"Vigilancia en {municipio}",
            "suffix": f"en {municipio}"
        }
    else:
        return {
            "title": "Vigilancia epidemiológica Tolima",
            "suffix": "en Tolima"
        }

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
    CORREGIDO: Prepara datos por municipio con normalización consistente.
    """
    def normalize_name(name):
        """Normaliza nombres para mapeo consistente."""
        if pd.isna(name) or name == "":
            return ""
        return str(name).upper().strip()
    
    # Normalizar nombres en shapefiles
    municipios = municipios.copy()
    municipios['municipi_1_norm'] = municipios['municipi_1'].apply(normalize_name)
    municipios['MpNombre_norm'] = municipios['MpNombre'].apply(normalize_name)
    
    # Preparar conteos de casos por municipio
    casos_por_municipio = {}
    fallecidos_por_municipio = {}
    
    if not casos.empty and 'municipio' in casos.columns:
        # Normalizar nombres en casos
        casos_norm = casos.copy()
        casos_norm['municipio_norm'] = casos_norm['municipio'].apply(normalize_name)
        
        casos_counts = casos_norm.groupby('municipio_norm').size()
        casos_por_municipio = casos_counts.to_dict()
        
        if 'condicion_final' in casos_norm.columns:
            fallecidos_norm = casos_norm[casos_norm['condicion_final'] == 'Fallecido']
            fallecidos_counts = fallecidos_norm.groupby('municipio_norm').size()
            fallecidos_por_municipio = fallecidos_counts.to_dict()
    
    # Preparar conteos de epizootias por municipio
    epizootias_por_municipio = {}
    positivas_por_municipio = {}
    en_estudio_por_municipio = {}
    
    if not epizootias.empty and 'municipio' in epizootias.columns:
        # Normalizar nombres en epizootias
        epizootias_norm = epizootias.copy()
        epizootias_norm['municipio_norm'] = epizootias_norm['municipio'].apply(normalize_name)
        
        epi_counts = epizootias_norm.groupby('municipio_norm').size()
        epizootias_por_municipio = epi_counts.to_dict()
        
        if 'descripcion' in epizootias_norm.columns:
            positivas_df = epizootias_norm[epizootias_norm['descripcion'] == 'POSITIVO FA']
            if not positivas_df.empty:
                positivas_counts = positivas_df.groupby('municipio_norm').size()
                positivas_por_municipio = positivas_counts.to_dict()
            
            en_estudio_df = epizootias_norm[epizootias_norm['descripcion'] == 'EN ESTUDIO']
            if not en_estudio_df.empty:
                en_estudio_counts = en_estudio_df.groupby('municipio_norm').size()
                en_estudio_por_municipio = en_estudio_counts.to_dict()
    
    # Combinar datos con shapefile
    municipios_data = municipios.copy()
    
    # Intentar mapeo con municipi_1 primero, luego con MpNombre
    def safe_map_data(row, data_dict):
        """Mapea datos de forma segura usando múltiples claves."""
        # Intentar con municipi_1_norm
        result = data_dict.get(row['municipi_1_norm'], 0)
        if result == 0:
            # Intentar con MpNombre_norm como fallback
            result = data_dict.get(row['MpNombre_norm'], 0)
        return result
    
    municipios_data['casos'] = municipios_data.apply(
        lambda row: safe_map_data(row, casos_por_municipio), axis=1
    )
    municipios_data['fallecidos'] = municipios_data.apply(
        lambda row: safe_map_data(row, fallecidos_por_municipio), axis=1
    )
    municipios_data['epizootias'] = municipios_data.apply(
        lambda row: safe_map_data(row, epizootias_por_municipio), axis=1
    )
    municipios_data['epizootias_positivas'] = municipios_data.apply(
        lambda row: safe_map_data(row, positivas_por_municipio), axis=1
    )
    municipios_data['epizootias_en_estudio'] = municipios_data.apply(
        lambda row: safe_map_data(row, en_estudio_por_municipio), axis=1
    )
    
    # Log para debugging
    total_casos_mapeados = municipios_data['casos'].sum()
    total_epi_mapeadas = municipios_data['epizootias'].sum()
    
    logging.info(f"🗺️ Mapeo municipal: {total_casos_mapeados} casos, {total_epi_mapeadas} epizootias")
    
    # Debug: mostrar municipios con datos
    municipios_con_datos = municipios_data[
        (municipios_data['casos'] > 0) | (municipios_data['epizootias'] > 0)
    ]['municipi_1'].tolist()
    logging.info(f"🗺️ Municipios con datos en mapa: {len(municipios_con_datos)}")
    
    return municipios_data

def prepare_vereda_data_enhanced(casos, epizootias, veredas_gdf):
    """
    CORREGIDO: Prepara datos por vereda con normalización consistente.
    """
    def normalize_name(name):
        """Normaliza nombres para mapeo consistente."""
        if pd.isna(name) or name == "":
            return ""
        return str(name).upper().strip()
    
    # Normalizar nombres en shapefile de veredas
    veredas_gdf = veredas_gdf.copy()
    veredas_gdf['vereda_nor_norm'] = veredas_gdf['vereda_nor'].apply(normalize_name)
    veredas_gdf['municipi_1_norm'] = veredas_gdf['municipi_1'].apply(normalize_name)
    
    # Obtener municipio actual del filtro
    municipio_actual = st.session_state.get('municipio_filter', 'Todos')
    municipio_norm = normalize_name(municipio_actual)
    
    # Preparar conteos de casos por vereda
    casos_por_vereda = {}
    if not casos.empty and 'vereda' in casos.columns and 'municipio' in casos.columns:
        casos_norm = casos.copy()
        casos_norm['vereda_norm'] = casos_norm['vereda'].apply(normalize_name)
        casos_norm['municipio_norm'] = casos_norm['municipio'].apply(normalize_name)
        
        # Filtrar casos del municipio actual
        casos_municipio = casos_norm[casos_norm['municipio_norm'] == municipio_norm]
        
        if not casos_municipio.empty:
            casos_counts = casos_municipio.groupby('vereda_norm').size()
            casos_por_vereda = casos_counts.to_dict()
    
    # Preparar conteos de epizootias por vereda
    epizootias_por_vereda = {}
    positivas_por_vereda = {}
    en_estudio_por_vereda = {}
    
    if not epizootias.empty and 'vereda' in epizootias.columns and 'municipio' in epizootias.columns:
        epizootias_norm = epizootias.copy()
        epizootias_norm['vereda_norm'] = epizootias_norm['vereda'].apply(normalize_name)
        epizootias_norm['municipio_norm'] = epizootias_norm['municipio'].apply(normalize_name)
        
        # Filtrar epizootias del municipio actual
        epi_municipio = epizootias_norm[epizootias_norm['municipio_norm'] == municipio_norm]
        
        if not epi_municipio.empty:
            epi_counts = epi_municipio.groupby('vereda_norm').size()
            epizootias_por_vereda = epi_counts.to_dict()
            
            if 'descripcion' in epi_municipio.columns:
                # Positivas
                positivas_df = epi_municipio[epi_municipio['descripcion'] == 'POSITIVO FA']
                if not positivas_df.empty:
                    positivas_counts = positivas_df.groupby('vereda_norm').size()
                    positivas_por_vereda = positivas_counts.to_dict()
                
                # En estudio
                en_estudio_df = epi_municipio[epi_municipio['descripcion'] == 'EN ESTUDIO']
                if not en_estudio_df.empty:
                    en_estudio_counts = en_estudio_df.groupby('vereda_norm').size()
                    en_estudio_por_vereda = en_estudio_counts.to_dict()
    
    # Combinar datos con shapefile
    veredas_data = veredas_gdf.copy()
    
    # Mapear usando vereda_nor_norm
    veredas_data['casos'] = veredas_data['vereda_nor_norm'].map(casos_por_vereda).fillna(0).astype(int)
    veredas_data['epizootias'] = veredas_data['vereda_nor_norm'].map(epizootias_por_vereda).fillna(0).astype(int)
    veredas_data['epizootias_positivas'] = veredas_data['vereda_nor_norm'].map(positivas_por_vereda).fillna(0).astype(int)
    veredas_data['epizootias_en_estudio'] = veredas_data['vereda_nor_norm'].map(en_estudio_por_vereda).fillna(0).astype(int)
    
    # Log para debugging
    total_casos_vereda = veredas_data['casos'].sum()
    total_epi_vereda = veredas_data['epizootias'].sum()
    
    logging.info(f"🏘️ Mapeo veredas {municipio_actual}: {total_casos_vereda} casos, {total_epi_vereda} epizootias")
    
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