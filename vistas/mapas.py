"""
Vista de mapas INTERACTIVOS del dashboard de Fiebre Amarilla.
Mapas como filtros integrados con zoom dinámico y métricas responsive.
VERSIÓN COMPLETA con shapefiles y sincronización bidireccional.
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

# Ruta de shapefiles procesados (CORREGIDA)
PROCESSED_DIR = Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed")


def show(data_filtered, filters, colors):
    """
    Muestra la vista de mapas interactivos completa con integración de filtros.

    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
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

    # Métricas interactivas duplicadas (responsive)
    create_interactive_metrics(casos, epizootias, filters, colors)
    
    st.markdown("---")

    # Sistema de mapas interactivos con filtros
    create_interactive_map_system(casos, epizootias, geo_data, filters, colors, data_filtered)


def apply_maps_css(colors):
    """Aplica CSS específico para la vista de mapas."""
    st.markdown(
        f"""
        <style>
        /* =============== MAPAS CSS ESPECÍFICO =============== */
        
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
        
        /* Métricas interactivas para mapas */
        .map-metrics-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: clamp(1rem, 3vw, 1.5rem);
            margin: 2rem 0;
            padding: 0 0.5rem;
        }}
        
        .map-metric-card {{
            background: linear-gradient(135deg, white 0%, #f8f9fa 100%);
            border-radius: 16px;
            padding: clamp(1.25rem, 3vw, 2rem);
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border-top: 5px solid {colors['primary']};
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
            min-height: 160px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        
        .map-metric-card:before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, {colors['primary']}, {colors['secondary']});
        }}
        
        .map-metric-card:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        }}
        
        .map-metric-icon {{
            font-size: clamp(2rem, 4vw, 2.8rem);
            margin-bottom: 0.75rem;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
        }}
        
        .map-metric-title {{
            font-size: clamp(0.85rem, 2vw, 1rem);
            color: {colors['dark']};
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .map-metric-value {{
            font-size: clamp(2rem, 5vw, 2.8rem);
            font-weight: 800;
            color: {colors['primary']};
            margin-bottom: 0.5rem;
            line-height: 1;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .map-metric-subtitle {{
            font-size: clamp(0.8rem, 2vw, 0.9rem);
            color: #666;
            font-weight: 500;
            line-height: 1.3;
        }}
        
        .map-location-badge {{
            background: linear-gradient(135deg, {colors['info']}, {colors['secondary']});
            color: white;
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 0.5rem;
            display: inline-block;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        
        /* Container del mapa */
        .map-container {{
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin: 2rem 0;
            border: 1px solid #e9ecef;
        }}
        
        .map-header {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px 12px 0 0;
            margin: -1.5rem -1.5rem 1.5rem -1.5rem;
            font-weight: 600;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .map-controls {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid {colors['info']};
        }}
        
        /* Responsive breakpoints */
        @media (max-width: 768px) {{
            .maps-title {{
                font-size: 1.8rem;
                padding: 1rem;
            }}
            
            .map-metrics-container {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 1rem;
                margin: 1rem 0;
            }}
            
            .map-metric-card {{
                min-height: 120px;
                padding: 1rem;
            }}
            
            .map-metric-icon {{
                font-size: 1.8rem;
                margin-bottom: 0.5rem;
            }}
            
            .map-metric-value {{
                font-size: 1.8rem;
            }}
            
            .map-container {{
                padding: 1rem;
                margin: 1rem 0;
            }}
            
            .map-header {{
                padding: 0.75rem 1rem;
                margin: -1rem -1rem 1rem -1rem;
                font-size: 1rem;
            }}
        }}
        
        @media (min-width: 1200px) {{
            .map-metrics-container {{
                grid-template-columns: repeat(4, 1fr);
            }}
        }}
        
        /* Animaciones suaves */
        .map-metric-card,
        .map-container {{
            animation: fadeInUp 0.6s ease-out;
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        /* Estilos para información de filtros activos */
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
        
        .no-data-message {{
            text-align: center;
            padding: 3rem 2rem;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 16px;
            color: {colors['dark']};
            font-size: 1.1rem;
            box-shadow: inset 0 4px 8px rgba(0,0,0,0.1);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_interactive_metrics(casos, epizootias, filters, colors):
    """Crea métricas interactivas que se actualizan con los filtros del mapa."""
    
    # Calcular métricas según filtros actuales
    total_casos = len(casos)
    total_epizootias = len(epizootias)

    # Métricas de casos
    fallecidos = 0
    vivos = 0
    letalidad = 0
    if total_casos > 0 and "condicion_final" in casos.columns:
        fallecidos = (casos["condicion_final"] == "Fallecido").sum()
        vivos = (casos["condicion_final"] == "Vivo").sum()
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0

    # Métricas de epizootias
    positivos_fa = 0
    positividad = 0
    if total_epizootias > 0 and "descripcion" in epizootias.columns:
        positivos_fa = (epizootias["descripcion"] == "POSITIVO FA").sum()
        positividad = (positivos_fa / total_epizootias * 100) if total_epizootias > 0 else 0

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

    # Crear grid de métricas responsive
    st.markdown(
        f"""
        <div class="map-metrics-container">
            <div class="map-metric-card">
                <div class="map-metric-icon">🦠</div>
                <div class="map-metric-title">Casos Confirmados</div>
                <div class="map-metric-value">{total_casos}</div>
                <div class="map-metric-subtitle">Fiebre Amarilla</div>
                {f'<div class="map-location-badge">{ubicacion_actual}</div>' if ubicacion_actual else ''}
            </div>
            
            <div class="map-metric-card">
                <div class="map-metric-icon">{'💚' if letalidad < 20 else '⚰️'}</div>
                <div class="map-metric-title">Letalidad</div>
                <div class="map-metric-value">{letalidad:.1f}%</div>
                <div class="map-metric-subtitle">{fallecidos} fallecidos de {total_casos}</div>
                {f'<div class="map-location-badge">{ubicacion_actual}</div>' if ubicacion_actual else ''}
            </div>
            
            <div class="map-metric-card">
                <div class="map-metric-icon">🐒</div>
                <div class="map-metric-title">Epizootias</div>
                <div class="map-metric-value">{total_epizootias}</div>
                <div class="map-metric-subtitle">Registradas</div>
                {f'<div class="map-location-badge">{ubicacion_actual}</div>' if ubicacion_actual else ''}
            </div>
            
            <div class="map-metric-card">
                <div class="map-metric-icon">{'🟢' if positividad < 30 else '🔴'}</div>
                <div class="map-metric-title">Positividad</div>
                <div class="map-metric-value">{positividad:.1f}%</div>
                <div class="map-metric-subtitle">{positivos_fa} positivas de {total_epizootias}</div>
                {f'<div class="map-location-badge">{ubicacion_actual}</div>' if ubicacion_actual else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_current_location_info(filters):
    """Obtiene información de la ubicación actual según filtros."""
    location_parts = []
    
    if filters.get("municipio_display") and filters["municipio_display"] != "Todos":
        location_parts.append(f"📍 {filters['municipio_display']}")
    
    if filters.get("vereda_display") and filters["vereda_display"] != "Todas":
        location_parts.append(f"🏘️ {filters['vereda_display']}")
    
    if not location_parts:
        return "📍 Tolima"
    
    return " - ".join(location_parts)


def create_interactive_map_system(casos, epizootias, geo_data, filters, colors, data_filtered):
    """Crea el sistema completo de mapas interactivos con filtros."""
    
    # Determinar nivel de zoom actual
    current_level = determine_map_level(filters)
    
    # Crear controles del mapa
    create_map_controls(current_level, filters, colors)
    
    # Crear mapa según nivel actual
    if current_level == "departamento":
        create_departmental_map(casos, epizootias, geo_data, colors, data_filtered)
    elif current_level == "municipio":
        create_municipal_map(casos, epizootias, geo_data, filters, colors, data_filtered)
    elif current_level == "vereda":
        create_vereda_detailed_view(casos, epizootias, geo_data, filters, colors)


def determine_map_level(filters):
    """Determina el nivel de zoom del mapa según filtros activos."""
    if filters.get("vereda_normalizada"):
        return "vereda"
    elif filters.get("municipio_normalizado"):
        return "municipio"
    else:
        return "departamento"


def create_map_controls(current_level, filters, colors):
    """Crea controles e información del mapa actual."""
    
    level_info = {
        "departamento": {
            "title": "🗺️ Vista Departamental",
            "subtitle": "Haga clic en un municipio para hacer zoom",
            "icon": "🏛️"
        },
        "municipio": {
            "title": f"🏛️ {filters.get('municipio_display', 'Municipio')}",
            "subtitle": "Haga clic en una vereda para más detalles",
            "icon": "🏘️"
        },
        "vereda": {
            "title": f"🏘️ {filters.get('vereda_display', 'Vereda')}",
            "subtitle": f"En {filters.get('municipio_display', 'Municipio')}",
            "icon": "📍"
        }
    }
    
    info = level_info[current_level]
    
    st.markdown(
        f"""
        <div class="map-container">
            <div class="map-header">
                {info['icon']} {info['title']}
            </div>
            <div class="map-controls">
                <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px;">
                        <strong>💡 {info['subtitle']}</strong>
                    </div>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
        """,
        unsafe_allow_html=True,
    )
    
    # Botones de navegación
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if current_level != "departamento":
            if st.button("🔙 Ver Tolima", key="back_to_tolima"):
                reset_location_filters()
                st.rerun()
    
    with col2:
        if current_level == "vereda":
            if st.button(f"🔙 Ver {filters.get('municipio_display', 'Municipio')}", key="back_to_municipio"):
                reset_vereda_filter()
                st.rerun()
    
    with col3:
        if st.button("🔄 Actualizar", key="refresh_map"):
            st.rerun()
    
    st.markdown(
        """
                    </div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )


def create_departmental_map(casos, epizootias, geo_data, colors, data_filtered):
    """Crea mapa departamental con municipios clicables."""
    
    if 'municipios' not in geo_data:
        st.error("No se pudo cargar el shapefile de municipios")
        return
    
    municipios = geo_data['municipios'].copy()
    
    # Preparar datos agregados por municipio
    municipios_data = prepare_municipal_data(casos, epizootias, municipios)
    
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
    max_epi = municipios_data['epizootias_positivas'].max() if municipios_data['epizootias_positivas'].max() > 0 else 1
    
    for idx, row in municipios_data.iterrows():
        municipio_name = row['MpNombre']
        casos_count = row['casos']
        fallecidos_count = row['fallecidos']
        epi_total = row['epizootias_total']
        epi_positivas = row['epizootias_positivas']
        
        # Determinar color y opacidad según datos
        if casos_count > 0 or epi_positivas > 0:
            # Intensidad de color según casos
            intensity = min(casos_count / max_casos, 1.0) if max_casos > 0 else 0
            if casos_count > 0:
                fill_color = f"rgba(229, 25, 55, {0.3 + intensity * 0.6})"  # Rojo para casos
                border_color = colors['danger']
            else:
                fill_color = f"rgba(247, 148, 29, {0.3 + (epi_positivas/max_epi) * 0.6})"  # Naranja para epizootias
                border_color = colors['warning']
        else:
            fill_color = "rgba(200, 200, 200, 0.3)"
            border_color = "#cccccc"
        
        # Popup con información completa
        popup_html = create_municipal_popup(municipio_name, casos_count, fallecidos_count, epi_total, epi_positivas)
        
        # Agregar polígono del municipio
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=fill_color, border=border_color: {
                'fillColor': color,
                'color': border,
                'weight': 2,
                'fillOpacity': 0.7,
                'opacity': 1
            },
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"<b>{municipio_name}</b><br>📊 Casos: {casos_count} | 🐒 Epizootias: {epi_total}"
        ).add_to(m)
    
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
    
    # Mostrar mapa y capturar interacciones
    map_data = st_folium(m, width=700, height=600, returned_objects=["last_object_clicked"])
    
    # Procesar clics en municipios
    if map_data['last_object_clicked']:
        handle_municipal_click(map_data['last_object_clicked'], municipios_data)
    
    st.markdown("</div>", unsafe_allow_html=True)


def create_municipal_map(casos, epizootias, geo_data, filters, colors, data_filtered):
    """Crea mapa municipal con veredas clicables."""
    
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
    
    # Preparar datos de veredas
    veredas_data = prepare_veredas_data(casos, epizootias, veredas_municipio, municipio_norm)
    
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
        epi_count = row['epizootias']
        
        # Color según presencia de datos
        if casos_count > 0:
            fill_color = colors['danger']
            opacity = 0.4 + (casos_count / max_casos_vereda) * 0.4
        elif epi_count > 0:
            fill_color = colors['warning']
            opacity = 0.3
        else:
            fill_color = colors['info']
            opacity = 0.2
        
        # Popup para vereda
        popup_html = create_vereda_popup(vereda_name, casos_count, epi_count)
        
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
            tooltip=f"<b>{vereda_name}</b><br>📊 Casos: {casos_count} | 🐒 Epizootias: {epi_count}"
        ).add_to(m)
    
    # Mostrar mapa y capturar interacciones
    map_data = st_folium(m, width=700, height=600, returned_objects=["last_object_clicked"])
    
    # Procesar clics en veredas
    if map_data['last_object_clicked']:
        handle_vereda_click(map_data['last_object_clicked'], veredas_data, filters)
    
    st.markdown("</div>", unsafe_allow_html=True)


def create_vereda_detailed_view(casos, epizootias, geo_data, filters, colors):
    """Crea vista detallada de una vereda específica."""
    
    vereda_display = filters.get("vereda_display", "Vereda")
    municipio_display = filters.get("municipio_display", "Municipio")
    
    # Mostrar información detallada de la vereda
    st.markdown(
        f"""
        <div class="map-container">
            <div class="map-header">
                📍 Información Detallada - {vereda_display}
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🦠 Casos en esta Vereda")
        if not casos.empty:
            casos_info = create_casos_detail_info(casos)
            st.markdown(casos_info, unsafe_allow_html=True)
        else:
            st.info("No hay casos registrados en esta vereda")
    
    with col2:
        st.markdown("### 🐒 Epizootias en esta Vereda")
        if not epizootias.empty:
            epi_info = create_epizootias_detail_info(epizootias)
            st.markdown(epi_info, unsafe_allow_html=True)
        else:
            st.info("No hay epizootias registradas en esta vereda")
    
    st.markdown("</div>", unsafe_allow_html=True)


# =============== FUNCIONES DE APOYO ===============

def prepare_municipal_data(casos, epizootias, municipios):
    """Prepara datos agregados por municipio."""
    
    # Contar casos por municipio
    casos_por_municipio = {}
    fallecidos_por_municipio = {}
    
    if not casos.empty and 'municipio_normalizado' in casos.columns:
        casos_counts = casos.groupby('municipio_normalizado').size()
        casos_por_municipio = casos_counts.to_dict()
        
        if 'condicion_final' in casos.columns:
            fallecidos_counts = casos[casos['condicion_final'] == 'Fallecido'].groupby('municipio_normalizado').size()
            fallecidos_por_municipio = fallecidos_counts.to_dict()
    
    # Contar epizootias por municipio
    epi_por_municipio = {}
    epi_positivas_por_municipio = {}
    
    if not epizootias.empty and 'municipio_normalizado' in epizootias.columns:
        epi_counts = epizootias.groupby('municipio_normalizado').size()
        epi_por_municipio = epi_counts.to_dict()
        
        if 'descripcion' in epizootias.columns:
            epi_pos_counts = epizootias[epizootias['descripcion'] == 'POSITIVO FA'].groupby('municipio_normalizado').size()
            epi_positivas_por_municipio = epi_pos_counts.to_dict()
    
    # Combinar datos con shapefile
    municipios_data = municipios.copy()
    
    municipios_data['casos'] = municipios_data['municipi_1'].map(casos_por_municipio).fillna(0).astype(int)
    municipios_data['fallecidos'] = municipios_data['municipi_1'].map(fallecidos_por_municipio).fillna(0).astype(int)
    municipios_data['epizootias_total'] = municipios_data['municipi_1'].map(epi_por_municipio).fillna(0).astype(int)
    municipios_data['epizootias_positivas'] = municipios_data['municipi_1'].map(epi_positivas_por_municipio).fillna(0).astype(int)
    
    return municipios_data


def prepare_veredas_data(casos, epizootias, veredas_municipio, municipio_norm):
    """Prepara datos de veredas para un municipio específico."""
    
    # Filtrar datos por municipio
    casos_mpio = casos[casos['municipio_normalizado'] == municipio_norm] if 'municipio_normalizado' in casos.columns else pd.DataFrame()
    epi_mpio = epizootias[epizootias['municipio_normalizado'] == municipio_norm] if 'municipio_normalizado' in epizootias.columns else pd.DataFrame()
    
    # Contar por vereda
    casos_por_vereda = {}
    epi_por_vereda = {}
    
    if not casos_mpio.empty and 'vereda_normalizada' in casos_mpio.columns:
        casos_counts = casos_mpio.groupby('vereda_normalizada').size()
        casos_por_vereda = casos_counts.to_dict()
    
    if not epi_mpio.empty and 'vereda_normalizada' in epi_mpio.columns:
        epi_counts = epi_mpio.groupby('vereda_normalizada').size()
        epi_por_vereda = epi_counts.to_dict()
    
    # Combinar con veredas
    veredas_data = veredas_municipio.copy()
    
    if 'vereda_nor' in veredas_data.columns:
        veredas_data['casos'] = veredas_data['vereda_nor'].map(casos_por_vereda).fillna(0).astype(int)
        veredas_data['epizootias'] = veredas_data['vereda_nor'].map(epi_por_vereda).fillna(0).astype(int)
    else:
        # Fallback usando normalización en tiempo real
        veredas_data['vereda_norm_temp'] = veredas_data['NOMBRE_VER'].apply(normalize_text)
        veredas_data['casos'] = veredas_data['vereda_norm_temp'].map(casos_por_vereda).fillna(0).astype(int)
        veredas_data['epizootias'] = veredas_data['vereda_norm_temp'].map(epi_por_vereda).fillna(0).astype(int)
    
    return veredas_data


def create_municipal_popup(municipio, casos, fallecidos, epi_total, epi_positivas):
    """Crea popup HTML para municipios."""
    letalidad = (fallecidos / casos * 100) if casos > 0 else 0
    positividad = (epi_positivas / epi_total * 100) if epi_total > 0 else 0
    
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
                <div style="font-size: 1.5em; font-weight: bold; color: #F7941D;">🐒 {epi_total}</div>
                <div style="font-size: 0.8em; color: #666;">Epizootias</div>
            </div>
        </div>
        
        <div style="font-size: 0.85em; line-height: 1.4;">
            <div style="margin: 3px 0;"><strong>⚰️ Fallecidos:</strong> {fallecidos} ({letalidad:.1f}%)</div>
            <div style="margin: 3px 0;"><strong>🔴 Epizootias +:</strong> {epi_positivas} ({positividad:.1f}%)</div>
        </div>
        
        <div style="margin-top: 10px; padding: 8px; background: #f0f8ff; border-radius: 6px; text-align: center;">
            <strong style="color: #4682B4;">👆 Haga clic para filtrar y hacer zoom</strong>
        </div>
    </div>
    """


def create_vereda_popup(vereda, casos, epizootias):
    """Crea popup HTML para veredas."""
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
                <div style="font-weight: bold; color: #F7941D;">🐒 {epizootias}</div>
                <div style="font-size: 0.7em; color: #666;">Epizootias</div>
            </div>
        </div>
        
        <div style="margin-top: 8px; padding: 6px; background: #f0f8ff; border-radius: 4px; text-align: center; font-size: 0.8em;">
            <strong style="color: #4682B4;">👆 Clic para ver detalles</strong>
        </div>
    </div>
    """


def create_casos_detail_info(casos):
    """Crea información detallada de casos para vista de vereda."""
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


def create_epizootias_detail_info(epizootias):
    """Crea información detallada de epizootias para vista de vereda."""
    if epizootias.empty:
        return "<p>No hay epizootias en esta vereda</p>"
    
    total = len(epizootias)
    
    # Distribución por resultado
    resultado_info = ""
    if "descripcion" in epizootias.columns:
        resultado_dist = epizootias["descripcion"].value_counts()
        resultado_items = []
        for resultado, count in resultado_dist.items():
            if resultado == "POSITIVO FA":
                resultado_items.append(f"🔴 Positivas: {count}")
            elif resultado == "NEGATIVO FA":
                resultado_items.append(f"🟢 Negativas: {count}")
            elif resultado == "NO APTA":
                resultado_items.append(f"🟡 No aptas: {count}")
            else:
                resultado_items.append(f"🔵 {resultado}: {count}")
        resultado_info = " | ".join(resultado_items)
    
    return f"""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #F7941D;">
        <div style="font-size: 1.2em; font-weight: bold; color: #F7941D; margin-bottom: 0.5rem;">
            Total: {total} epizootias
        </div>
        {f'<div style="margin-bottom: 0.5rem; font-size: 0.9em;">{resultado_info}</div>' if resultado_info else ''}
    </div>
    """


def handle_municipal_click(clicked_object, municipios_data):
    """Maneja clics en municipios para filtrar y hacer zoom."""
    # Esta función se activaría en una implementación más avanzada
    # Por ahora mostramos información del municipio clicado
    pass


def handle_vereda_click(clicked_object, veredas_data, filters):
    """Maneja clics en veredas para filtrar."""
    # Esta función se activaría en una implementación más avanzada
    pass


def reset_location_filters():
    """Resetea filtros de ubicación para volver a vista departamental."""
    if "municipio_filter" in st.session_state:
        st.session_state.municipio_filter = "Todos"
    if "vereda_filter" in st.session_state:
        st.session_state.vereda_filter = "Todas"


def reset_vereda_filter():
    """Resetea solo el filtro de vereda."""
    if "vereda_filter" in st.session_state:
        st.session_state.vereda_filter = "Todas"


# =============== FUNCIONES DE VERIFICACIÓN ===============

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
        <div class="no-data-message">
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
        <div class="no-data-message">
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
        <div class="no-data-message">
            <h3>❌ Error al Cargar Datos Geográficos</h3>
            <p>No se pudieron cargar los shapefiles del Tolima.</p>
            <p>Verifique que los archivos estén correctamente procesados.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )