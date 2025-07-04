"""
Vista de mapas CORREGIDA del dashboard de Fiebre Amarilla.
CORRECCIONES:
- Hover para popup informativo
- 1 click para filtrar (no doble click)
- Mapas veredales implementados
- Tarjetas estéticas mejoradas (tipo rectangulares como popup)
- Sin análisis de riesgo
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

from utils.data_processor import normalize_text

# Ruta de shapefiles procesados
PROCESSED_DIR = Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed")


def show(data_filtered, filters, colors):
    """
    Vista completa de mapas con interacciones CORREGIDAS.
    Layout: Columnas lado a lado (mapa | tarjetas mejoradas)
    """
    
    # CSS para la nueva vista
    apply_enhanced_maps_css(colors)
    
    # Título principal (SIN espacio excesivo)
    st.markdown(
        '<h1 class="maps-title">🗺️ Mapas Interactivos</h1>',
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

    # **LAYOUT MEJORADO**: División en columnas lado a lado
    col_mapa, col_tarjetas = st.columns([3, 2])  # 60% mapa, 40% tarjetas
    
    with col_mapa:
        st.markdown("### 🗺️ Mapa del Tolima")
        create_hover_click_map_system(casos, epizootias, geo_data, filters, colors, data_filtered)
    
    with col_tarjetas:
        st.markdown("### 📊 Información")
        # **TARJETAS MEJORADAS**: Estilo rectangular como popup
        create_enhanced_rectangular_cards(casos, epizootias, filters, colors)


def create_hover_click_map_system(casos, epizootias, geo_data, filters, colors, data_filtered):
    """
    NUEVO: Sistema de mapas con hover para popup y click para filtrar.
    """
    
    # Determinar nivel de mapa actual
    current_level = determine_map_level(filters)
    
    # Controles de navegación
    create_navigation_controls(current_level, filters, colors)
    
    # Indicador de filtrado activo
    show_filter_indicator(filters, colors)
    
    # Crear mapa según nivel con NUEVAS INTERACCIONES
    if current_level == "departamento":
        create_departmental_hover_click_map(casos, epizootias, geo_data, colors)
    elif current_level == "municipio":
        create_municipal_hover_click_map(casos, epizootias, geo_data, filters, colors)
    elif current_level == "vereda":
        create_vereda_detail_view(casos, epizootias, filters, colors)


def create_departmental_hover_click_map(casos, epizootias, geo_data, colors):
    """
    CORREGIDO: Mapa departamental con hover para popup y click para filtrar.
    """
    
    if 'municipios' not in geo_data:
        st.error("No se pudo cargar el shapefile de municipios")
        return
    
    municipios = geo_data['municipios'].copy()
    
    # Preparar datos agregados por municipio
    municipios_data = prepare_municipal_data_fixed(casos, epizootias, municipios)
    
    # Obtener límites del Tolima
    bounds = municipios.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # **CONFIGURACIÓN CORREGIDA**: Mapa fijo con nuevas interacciones
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
    
    # Agregar municipios con NUEVAS INTERACCIONES
    max_casos = municipios_data['casos'].max() if municipios_data['casos'].max() > 0 else 1
    max_epi = municipios_data['epizootias'].max() if municipios_data['epizootias'].max() > 0 else 1
    
    for idx, row in municipios_data.iterrows():
        municipio_name = row['MpNombre']
        casos_count = row['casos']
        fallecidos_count = row['fallecidos']
        epizootias_count = row['epizootias']
        
        # Color según intensidad de datos (SIN análisis de riesgo)
        if casos_count > 0 or epizootias_count > 0:
            intensity = min(casos_count / max_casos, 1.0) if max_casos > 0 else 0
            if casos_count > 0:
                fill_color = f"rgba(229, 25, 55, {0.3 + intensity * 0.6})"
                border_color = colors['danger']
            else:
                epi_intensity = min(epizootias_count / max_epi, 1.0) if max_epi > 0 else 0
                fill_color = f"rgba(247, 148, 29, {0.3 + epi_intensity * 0.6})"
                border_color = colors['warning']
        else:
            fill_color = "rgba(200, 200, 200, 0.3)"
            border_color = "#cccccc"
        
        # **NUEVO TOOLTIP PARA HOVER** (más simple)
        tooltip_text = f"""
        <div style="font-family: Arial; padding: 5px;">
            <b>{municipio_name}</b><br>
            🦠 Casos: {casos_count}<br>
            🐒 Epizootias: {epizootias_count}<br>
            <i>👆 Clic para filtrar</i>
        </div>
        """
        
        # **POPUP DETALLADO** (para mantener información completa)
        popup_html = create_simple_municipal_popup(municipio_name, casos_count, fallecidos_count, epizootias_count, colors)
        
        # Agregar polígono con **NUEVAS INTERACCIONES**
        geojson = folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=fill_color, border=border_color: {
                'fillColor': color,
                'color': border,
                'weight': 2,
                'fillOpacity': 0.7,
                'opacity': 1
            },
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=folium.Tooltip(tooltip_text, sticky=True),  # **HOVER TOOLTIP**
        )
        
        geojson.add_to(m)
    
    # **INSTRUCCIONES DE USO**
    st.info("💡 **Interacciones:** Pase el cursor sobre un municipio para ver información básica • Haga clic para filtrar por ese municipio")
    
    # Renderizar mapa con detección de clicks
    map_data = st_folium(
        m, 
        width=700,
        height=500,
        returned_objects=["last_object_clicked"],  # **SOLO CLICKS, NO POPUPS**
        key="hover_click_main_map"
    )
    
    # **NUEVA LÓGICA**: Procesar clicks simples (no doble click)
    handle_simple_click_interactions(map_data, municipios_data)


def create_municipal_hover_click_map(casos, epizootias, geo_data, filters, colors):
    """
    NUEVO: Mapa municipal con veredas - hover y click implementados.
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
    veredas_data = prepare_vereda_data(casos, epizootias, veredas_municipio)
    
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
    
    # Agregar veredas con interacciones
    max_casos_vereda = veredas_data['casos'].max() if veredas_data['casos'].max() > 0 else 1
    max_epi_vereda = veredas_data['epizootias'].max() if veredas_data['epizootias'].max() > 0 else 1
    
    for idx, row in veredas_data.iterrows():
        vereda_name = row.get('NOMBRE_VER', row.get('vereda', f'Vereda_{idx}'))
        casos_count = row['casos']
        epizootias_count = row['epizootias']
        
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
        
        # Tooltip para hover
        tooltip_text = f"""
        <div style="font-family: Arial; padding: 5px;">
            <b>{vereda_name}</b><br>
            🦠 Casos: {casos_count}<br>
            🐒 Epizootias: {epizootias_count}<br>
            <i>👆 Clic para filtrar</i>
        </div>
        """
        
        # Popup detallado
        popup_html = create_simple_vereda_popup(vereda_name, casos_count, epizootias_count, colors)
        
        # Agregar vereda
        geojson = folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=fill_color, border=border_color: {
                'fillColor': color,
                'color': border,
                'weight': 1.5,
                'fillOpacity': 0.6,
                'opacity': 1
            },
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=folium.Tooltip(tooltip_text, sticky=True),
        )
        
        geojson.add_to(m)
    
    st.info("💡 **Interacciones:** Pase el cursor sobre una vereda para ver información • Haga clic para filtrar por esa vereda")
    
    # Renderizar mapa
    map_data = st_folium(
        m, 
        width=700,
        height=500,
        returned_objects=["last_object_clicked"],
        key="municipal_vereda_map"
    )
    
    # Procesar clicks en veredas
    handle_vereda_click_interactions(map_data, veredas_data, filters)


def create_vereda_detail_view(casos, epizootias, filters, colors):
    """
    NUEVO: Vista detallada de vereda específica (sin mapa geográfico).
    """
    
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


def create_enhanced_rectangular_cards(casos, epizootias, filters, colors):
    """
    NUEVAS: Tarjetas estéticas rectangulares estilo popup mejorado.
    """
    
    # Calcular métricas
    total_casos = len(casos)
    total_epizootias = len(epizootias)

    # Métricas de casos
    fallecidos = 0
    vivos = 0
    if total_casos > 0 and "condicion_final" in casos.columns:
        fallecidos = (casos["condicion_final"] == "Fallecido").sum()
        vivos = (casos["condicion_final"] == "Vivo").sum()

    # Fechas importantes
    ultima_fecha_caso = None
    ultima_fecha_epi = None

    if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
        fechas_casos = casos["fecha_inicio_sintomas"].dropna()
        if not fechas_casos.empty:
            ultima_fecha_caso = fechas_casos.max()

    if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
        fechas_epi = epizootias["fecha_recoleccion"].dropna()
        if not fechas_epi.empty:
            ultima_fecha_epi = fechas_epi.max()

    # **TARJETAS ESTILO RECTANGULAR COMO POPUP**
    
    # Tarjeta principal de casos
    st.markdown(
        f"""
        <div class="enhanced-card-main">
            <div class="card-header-cases">
                <div class="card-icon">🦠</div>
                <div class="card-title">CASOS HUMANOS</div>
            </div>
            <div class="card-body">
                <div class="metric-grid">
                    <div class="metric-item">
                        <div class="metric-number">{total_casos}</div>
                        <div class="metric-label">Total Casos</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-number" style="color: {colors['success']};">{vivos}</div>
                        <div class="metric-label">Vivos</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-number" style="color: {colors['danger']};">{fallecidos}</div>
                        <div class="metric-label">Fallecidos</div>
                    </div>
                </div>
                {f'<div class="card-footer">Último caso: {ultima_fecha_caso.strftime("%d/%m/%Y")}</div>' if ultima_fecha_caso else '<div class="card-footer">Sin fechas registradas</div>'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Tarjeta principal de epizootias
    st.markdown(
        f"""
        <div class="enhanced-card-main">
            <div class="card-header-epizootias">
                <div class="card-icon">🐒</div>
                <div class="card-title">EPIZOOTIAS</div>
            </div>
            <div class="card-body">
                <div class="metric-grid">
                    <div class="metric-item">
                        <div class="metric-number">{total_epizootias}</div>
                        <div class="metric-label">Total Epizootias</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-number" style="color: {colors['warning']};">100%</div>
                        <div class="metric-label">Confirmadas</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-number" style="color: {colors['info']};">FA+</div>
                        <div class="metric-label">Positivas</div>
                    </div>
                </div>
                {f'<div class="card-footer">Última epizootia: {ultima_fecha_epi.strftime("%d/%m/%Y")}</div>' if ultima_fecha_epi else '<div class="card-footer">Sin fechas registradas</div>'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Tarjeta de resumen
    actividad_total = total_casos + total_epizootias
    ubicacion_actual = get_current_location_info(filters)
    
    st.markdown(
        f"""
        <div class="enhanced-card-summary">
            <div class="card-header-summary">
                <div class="card-icon">📊</div>
                <div class="card-title">RESUMEN</div>
            </div>
            <div class="card-body">
                <div class="summary-location">
                    📍 <strong>{ubicacion_actual}</strong>
                </div>
                <div class="summary-metrics">
                    <div class="summary-item">
                        <span class="summary-number">{actividad_total}</span>
                        <span class="summary-text">eventos totales</span>
                    </div>
                </div>
                <div class="card-footer-summary">
                    Datos filtrados según selección actual
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # **TARJETAS ADICIONALES PEQUEÑAS**
    if filters.get("active_filters"):
        active_count = len(filters["active_filters"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown(
            f"""
            <div class="enhanced-card-small">
                <div class="small-card-content">
                    <div class="small-icon">🎯</div>
                    <div class="small-text">
                        <div class="small-number">{active_count}</div>
                        <div class="small-label">Filtros Activos</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Información de navegación
    current_level = determine_map_level(filters)
    level_info = {
        "departamento": "Vista Departamental",
        "municipio": "Vista Municipal", 
        "vereda": "Vista de Vereda"
    }
    
    st.markdown(
        f"""
        <div class="enhanced-card-small">
            <div class="small-card-content">
                <div class="small-icon">🗺️</div>
                <div class="small-text">
                    <div class="small-number">{level_info[current_level]}</div>
                    <div class="small-label">Nivel Actual</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_enhanced_maps_css(colors):
    """
    CSS mejorado para tarjetas rectangulares estilo popup.
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
            margin: 0.5rem 0 1rem 0;  /* REDUCIDO: menos margen */
            padding: 1rem;
            border-radius: 12px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-left: 6px solid {colors['secondary']};
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        /* Tarjetas principales estilo popup rectangular */
        .enhanced-card-main {{
            background: linear-gradient(135deg, white 0%, #fafafa 100%);
            border-radius: 15px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            overflow: hidden;
            margin-bottom: 1.5rem;
            border: 1px solid #e1e5e9;
            transition: all 0.3s ease;
        }}
        
        .enhanced-card-main:hover {{
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
            transform: translateY(-2px);
        }}
        
        /* Headers de tarjetas */
        .card-header-cases {{
            background: linear-gradient(135deg, {colors['danger']}, #e74c3c);
            color: white;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .card-header-epizootias {{
            background: linear-gradient(135deg, {colors['warning']}, #f39c12);
            color: white;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .card-header-summary {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
            color: white;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .card-icon {{
            font-size: 1.8rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        }}
        
        .card-title {{
            font-size: 1.1rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        
        /* Cuerpo de tarjetas */
        .card-body {{
            padding: 20px;
        }}
        
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .metric-item {{
            text-align: center;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }}
        
        .metric-number {{
            font-size: 1.8rem;
            font-weight: 800;
            color: {colors['primary']};
            margin-bottom: 5px;
            line-height: 1;
        }}
        
        .metric-label {{
            font-size: 0.8rem;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        
        .card-footer {{
            font-size: 0.85rem;
            color: {colors['info']};
            font-weight: 600;
            text-align: center;
            background: #f1f3f4;
            padding: 8px;
            border-radius: 6px;
            margin-top: 10px;
        }}
        
        /* Tarjeta de resumen */
        .enhanced-card-summary {{
            background: linear-gradient(135deg, white 0%, #f0f8ff 100%);
            border-radius: 15px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            overflow: hidden;
            margin-bottom: 1.5rem;
            border: 2px solid {colors['info']};
        }}
        
        .summary-location {{
            font-size: 1rem;
            color: {colors['primary']};
            font-weight: 600;
            text-align: center;
            margin-bottom: 15px;
            padding: 10px;
            background: rgba(125, 15, 43, 0.1);
            border-radius: 8px;
        }}
        
        .summary-metrics {{
            text-align: center;
            margin: 15px 0;
        }}
        
        .summary-item {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin: 8px 0;
        }}
        
        .summary-number {{
            font-size: 2rem;
            font-weight: 800;
            color: {colors['primary']};
        }}
        
        .summary-text {{
            font-size: 0.9rem;
            color: #666;
            font-weight: 600;
        }}
        
        .card-footer-summary {{
            font-size: 0.8rem;
            color: {colors['info']};
            text-align: center;
            font-style: italic;
            margin-top: 15px;
        }}
        
        /* Tarjetas pequeñas */
        .enhanced-card-small {{
            background: linear-gradient(135deg, white 0%, #f8f9fa 100%);
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            border: 1px solid #e1e5e9;
            overflow: hidden;
        }}
        
        .small-card-content {{
            padding: 15px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .small-icon {{
            font-size: 1.5rem;
            color: {colors['primary']};
        }}
        
        .small-text {{
            flex: 1;
        }}
        
        .small-number {{
            font-size: 0.9rem;
            font-weight: 700;
            color: {colors['primary']};
            line-height: 1;
        }}
        
        .small-label {{
            font-size: 0.75rem;
            color: #666;
            font-weight: 500;
            margin-top: 2px;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .metric-grid {{
                grid-template-columns: 1fr;
                gap: 10px;
            }}
            
            .card-header-cases,
            .card-header-epizootias,
            .card-header-summary {{
                padding: 12px 15px;
            }}
            
            .card-icon {{
                font-size: 1.5rem;
            }}
            
            .card-title {{
                font-size: 0.95rem;
            }}
            
            .metric-number {{
                font-size: 1.4rem;
            }}
            
            .metric-label {{
                font-size: 0.7rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# === FUNCIONES DE APOYO ===

def handle_simple_click_interactions(map_data, municipios_data):
    """
    CORREGIDO: Maneja clicks simples (no doble click) para filtrar municipios.
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
                    # **FILTRAR AUTOMÁTICAMENTE**
                    st.session_state['municipio_filter'] = municipio_clicked
                    
                    # Mostrar confirmación visual
                    st.success(f"✅ Filtrado por municipio: **{municipio_clicked}**")
                    
                    # **ACTUALIZAR INMEDIATAMENTE**
                    st.rerun()
                    
    except Exception as e:
        st.warning(f"Error procesando clic en mapa: {str(e)}")


def handle_vereda_click_interactions(map_data, veredas_data, filters):
    """
    NUEVO: Maneja clicks en veredas para filtrar.
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
                
                for idx, row in veredas_data.iterrows():
                    centroid = row['geometry'].centroid
                    distance = ((centroid.x - clicked_lng)**2 + (centroid.y - clicked_lat)**2)**0.5
                    
                    if distance < min_distance:
                        min_distance = distance
                        vereda_clicked = row.get('NOMBRE_VER', row.get('vereda', f'Vereda_{idx}'))
                
                if vereda_clicked and min_distance < 0.05:  # Umbral más pequeño para veredas
                    # **FILTRAR POR VEREDA**
                    st.session_state['vereda_filter'] = vereda_clicked
                    
                    # Mostrar confirmación
                    st.success(f"✅ Filtrado por vereda: **{vereda_clicked}**")
                    
                    # **ACTUALIZAR**
                    st.rerun()
                    
    except Exception as e:
        st.warning(f"Error procesando clic en vereda: {str(e)}")


def prepare_vereda_data(casos, epizootias, veredas_gdf):
    """
    NUEVO: Prepara datos agregados por vereda.
    """
    casos_por_vereda = {}
    epizootias_por_vereda = {}
    
    # Contar casos por vereda
    if not casos.empty and 'vereda_normalizada' in casos.columns:
        for vereda_norm, group in casos.groupby('vereda_normalizada'):
            casos_por_vereda[vereda_norm.upper()] = len(group)
    
    # Contar epizootias por vereda
    if not epizootias.empty and 'vereda_normalizada' in epizootias.columns:
        for vereda_norm, group in epizootias.groupby('vereda_normalizada'):
            epizootias_por_vereda[vereda_norm.upper()] = len(group)
    
    # Combinar con shapefile
    veredas_data = veredas_gdf.copy()
    
    # Intentar mapear con diferentes campos
    for col in ['NOMBRE_VER', 'vereda', 'Vereda']:
        if col in veredas_data.columns:
            veredas_data['casos'] = veredas_data[col].str.upper().str.strip().map(casos_por_vereda).fillna(0).astype(int)
            veredas_data['epizootias'] = veredas_data[col].str.upper().str.strip().map(epizootias_por_vereda).fillna(0).astype(int)
            break
    
    # Si no se pudo mapear, llenar con 0
    if 'casos' not in veredas_data.columns:
        veredas_data['casos'] = 0
    if 'epizootias' not in veredas_data.columns:
        veredas_data['epizootias'] = 0
    
    return veredas_data


def show_municipal_tabular_view(casos, epizootias, filters, colors):
    """
    NUEVO: Vista tabular cuando no hay shapefiles de veredas.
    """
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


def create_simple_municipal_popup(municipio, casos, fallecidos, epizootias, colors):
    """
    CORREGIDO: Popup simple para municipios (sin análisis de riesgo).
    """
    return f"""
    <div style="font-family: Arial, sans-serif; width: 300px;">
        <h3 style="color: {colors['primary']}; margin: 0 0 15px 0; border-bottom: 2px solid {colors['secondary']}; padding-bottom: 8px; text-align: center;">
            📍 {municipio}
        </h3>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
            <div style="background: #ffe6e6; padding: 12px; border-radius: 8px; text-align: center;">
                <div style="font-size: 1.6em; font-weight: bold; color: {colors['danger']};">🦠 {casos}</div>
                <div style="font-size: 0.8em; color: #666; font-weight: 600;">CASOS</div>
            </div>
            <div style="background: #fff3e0; padding: 12px; border-radius: 8px; text-align: center;">
                <div style="font-size: 1.6em; font-weight: bold; color: {colors['warning']};">🐒 {epizootias}</div>
                <div style="font-size: 0.8em; color: #666; font-weight: 600;">EPIZOOTIAS</div>
            </div>
        </div>
        
        <div style="text-align: center; background: #f0f0f0; padding: 10px; border-radius: 6px;">
            <div style="font-size: 1.2em; font-weight: bold; color: {colors['dark']};">⚰️ {fallecidos} Fallecidos</div>
        </div>
        
        <div style="margin-top: 15px; padding: 10px; background: {colors['info']}; border-radius: 6px; text-align: center; color: white;">
            <strong>👆 Clic en el mapa para filtrar por este municipio</strong>
        </div>
    </div>
    """


def create_simple_vereda_popup(vereda, casos, epizootias, colors):
    """
    NUEVO: Popup simple para veredas.
    """
    return f"""
    <div style="font-family: Arial, sans-serif; width: 250px;">
        <h4 style="color: {colors['primary']}; margin: 0 0 12px 0; border-bottom: 2px solid {colors['secondary']}; padding-bottom: 5px;">
            🏘️ {vereda}
        </h4>
        
        <div style="display: flex; gap: 10px; margin-bottom: 12px;">
            <div style="background: #ffe6e6; padding: 10px; border-radius: 6px; flex: 1; text-align: center;">
                <div style="font-weight: bold; color: {colors['danger']}; font-size: 1.3em;">🦠 {casos}</div>
                <div style="font-size: 0.75em; color: #666;">Casos</div>
            </div>
            <div style="background: #fff3e0; padding: 10px; border-radius: 6px; flex: 1; text-align: center;">
                <div style="font-weight: bold; color: {colors['warning']}; font-size: 1.3em;">🐒 {epizootias}</div>
                <div style="font-size: 0.75em; color: #666;">Epizootias</div>
            </div>
        </div>
        
        <div style="background: {colors['info']}; padding: 8px; border-radius: 6px; text-align: center; color: white;">
            <strong style="font-size: 0.85em;">👆 Clic para filtrar esta vereda</strong>
        </div>
    </div>
    """


# === FUNCIONES DE UTILIDAD REUTILIZADAS ===

def determine_map_level(filters):
    """Determina el nivel de zoom del mapa según filtros activos."""
    if filters.get("vereda_normalizada"):
        return "vereda"
    elif filters.get("municipio_normalizado"):
        return "municipio"
    else:
        return "departamento"


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


def create_navigation_controls(current_level, filters, colors):
    """Controles de navegación simplificados."""
    level_info = {
        "departamento": "🏛️ Vista Departamental - Tolima",
        "municipio": f"🏘️ {filters.get('municipio_display', 'Municipio')}",
        "vereda": f"📍 {filters.get('vereda_display', 'Vereda')} - {filters.get('municipio_display', 'Municipio')}"
    }
    
    current_info = level_info[current_level]
    
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            text-align: center;
            font-weight: 600;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        ">
            {current_info}
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Botones de navegación
    cols = st.columns([1, 1, 1])
    
    with cols[0]:
        if current_level != "departamento":
            if st.button("🏛️ Ver Tolima", key="nav_tolima_fixed", use_container_width=True):
                reset_all_location_filters()
                st.rerun()
    
    with cols[1]:
        if current_level == "vereda":
            municipio_name = filters.get('municipio_display', 'Municipio')
            if st.button(f"🏘️ Ver {municipio_name[:10]}...", key="nav_municipio_fixed", use_container_width=True):
                reset_vereda_filter_only()
                st.rerun()
    
    with cols[2]:
        if st.button("🔄 Actualizar", key="refresh_map_fixed", use_container_width=True):
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


# === FUNCIONES DE APOYO EXISTENTES ===

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


def prepare_municipal_data_fixed(casos, epizootias, municipios):
    """Prepara datos agregados por municipio."""
    casos_por_municipio = {}
    fallecidos_por_municipio = {}
    
    if not casos.empty and 'municipio_normalizado' in casos.columns:
        casos_counts = casos.groupby('municipio_normalizado').size()
        casos_por_municipio = casos_counts.to_dict()
        
        if 'condicion_final' in casos.columns:
            fallecidos_counts = casos[casos['condicion_final'] == 'Fallecido'].groupby('municipio_normalizado').size()
            fallecidos_por_municipio = fallecidos_counts.to_dict()
    
    epizootias_por_municipio = {}
    if not epizootias.empty and 'municipio_normalizado' in epizootias.columns:
        epi_counts = epizootias.groupby('municipio_normalizado').size()
        epizootias_por_municipio = epi_counts.to_dict()
    
    # Combinar datos con shapefile
    municipios_data = municipios.copy()
    
    municipios_data['casos'] = municipios_data['municipi_1'].map(casos_por_municipio).fillna(0).astype(int)
    municipios_data['fallecidos'] = municipios_data['municipi_1'].map(fallecidos_por_municipio).fillna(0).astype(int)
    municipios_data['epizootias'] = municipios_data['municipi_1'].map(epizootias_por_municipio).fillna(0).astype(int)
    
    return municipios_data


def show_maps_not_available():
    """Muestra mensaje cuando las librerías de mapas no están disponibles."""
    st.error("⚠️ Librerías de mapas no instaladas. Instale: geopandas folium streamlit-folium")


def show_shapefiles_setup_instructions():
    """Muestra instrucciones para configurar shapefiles."""
    st.error("🗺️ Shapefiles no encontrados en la ruta configurada")


def show_geographic_data_error():
    """Muestra mensaje de error al cargar datos geográficos."""
    st.error("❌ Error al cargar datos geográficos")