"""
Vista de mapas CORREGIDA del dashboard de Fiebre Amarilla.
CORREGIDO v3.4:
- Ruta de shapefiles FLEXIBLE y configurable
- Importaciones más robustas con manejo de errores
- Debugging mejorado para identificar problemas
- Mantiene toda la funcionalidad existente
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime

# Configurar logger específico para mapas
logger = logging.getLogger("FiebreAmarilla.Mapas")

# Importaciones opcionales para mapas con mejor manejo de errores
try:
    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium
    MAPS_AVAILABLE = True
    logger.info("✅ Librerías de mapas importadas correctamente: geopandas, folium, streamlit-folium")
except ImportError as e:
    MAPS_AVAILABLE = False
    logger.warning(f"⚠️ Librerías de mapas no disponibles: {str(e)}")

# Importaciones de utilidades con manejo de errores mejorado
try:
    from utils.data_processor import (
        normalize_text, 
        calculate_basic_metrics,
        get_latest_case_info,
        format_time_elapsed,
        calculate_days_since
    )
    logger.info("✅ Utilidades de procesamiento de datos importadas correctamente")
except ImportError as e:
    logger.error(f"❌ Error importando utilidades de datos: {str(e)}")
    # Crear funciones dummy para evitar errores
    def normalize_text(text): return str(text).upper().strip() if text else ""
    def calculate_basic_metrics(casos, epizootias): return {"total_casos": len(casos), "total_epizootias": len(epizootias)}
    def get_latest_case_info(df, date_col, location_cols=None): return {"existe": False}
    def format_time_elapsed(days): return f"{days} días" if days else "Sin datos"
    def calculate_days_since(date): return 0

# CORREGIDO: Rutas flexibles para shapefiles
def get_shapefiles_paths():
    """
    NUEVO: Obtiene las rutas de shapefiles de manera flexible.
    Busca en múltiples ubicaciones posibles.
    """
    # Directorio actual
    current_dir = Path(__file__).resolve().parent.parent
    
    # Posibles ubicaciones de shapefiles
    possible_paths = [
        # Ruta original (para compatibilidad)
        Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed"),
        
        # Rutas relativas al proyecto
        current_dir / "shapefiles" / "processed",
        current_dir / "data" / "shapefiles",
        current_dir / "assets" / "shapefiles",
        current_dir / "Tolima-Veredas" / "processed",
        
        # Rutas relativas al directorio padre
        current_dir.parent / "Tolima-Veredas" / "processed",
        current_dir.parent / "shapefiles",
        
        # Ruta en el escritorio del usuario actual
        Path.home() / "Desktop" / "Tolima-Veredas" / "processed",
        Path.home() / "Documents" / "Tolima-Veredas" / "processed",
    ]
    
    logger.info("🔍 Buscando shapefiles en ubicaciones posibles...")
    
    for path in possible_paths:
        logger.debug(f"   Verificando: {path}")
        if path.exists():
            municipios_file = path / "tolima_municipios.shp"
            veredas_file = path / "tolima_veredas.shp"
            
            if municipios_file.exists() or veredas_file.exists():
                logger.info(f"✅ Shapefiles encontrados en: {path}")
                return path
    
    logger.warning("⚠️ No se encontraron shapefiles en ninguna ubicación")
    return None

# Definir ruta de shapefiles de manera flexible
PROCESSED_DIR = get_shapefiles_paths()


def show(data_filtered, filters, colors):
    """
    Vista completa de mapas con navegación jerárquica automática y tarjetas mejoradas.
    CORREGIDA con mejor manejo de errores.
    """
    
    logger.info("🗺️ Iniciando vista de mapas...")
    
    try:
        # CSS para tarjetas mejoradas
        apply_enhanced_cards_css(colors)
        
        # Título principal elegante
        st.markdown(
            f'''
            <div class="hero-title">
                <div class="hero-icon">🗺️</div>
                <h1>Mapas Interactivos Inteligentes</h1>
                <p>Navegación automática • Visualización dinámica • Información completa</p>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        if not MAPS_AVAILABLE:
            logger.warning("⚠️ Librerías de mapas no disponibles")
            show_maps_not_available()
            return

        # Verificar disponibilidad de shapefiles
        if not check_shapefiles_availability():
            logger.warning("⚠️ Shapefiles no disponibles")
            show_shapefiles_setup_instructions()
            return

        # Cargar datos geográficos
        geo_data = load_geographic_data_silent()
        
        if not geo_data:
            logger.warning("⚠️ No se pudieron cargar datos geográficos")
            show_geographic_data_error()
            return

        casos = data_filtered["casos"]
        epizootias = data_filtered["epizootias"]
        
        logger.info(f"📊 Datos cargados: {len(casos)} casos, {len(epizootias)} epizootias")

        # **LAYOUT MEJORADO**: División elegante lado a lado
        col_mapa, col_tarjetas = st.columns([3, 2], gap="large")
        
        with col_mapa:
            create_intelligent_map_system(casos, epizootias, geo_data, filters, colors, data_filtered)
        
        with col_tarjetas:
            create_enhanced_information_cards(casos, epizootias, filters, colors)
            
        logger.info("✅ Vista de mapas completada exitosamente")
            
    except Exception as e:
        logger.error(f"❌ Error crítico en vista de mapas: {str(e)}")
        st.error(f"❌ Error en vista de mapas: {str(e)}")
        
        # Mostrar stack trace para debugging
        import traceback
        with st.expander("🔍 Detalles del error", expanded=False):
            st.code(traceback.format_exc())


def create_intelligent_map_system(casos, epizootias, geo_data, filters, colors, data_filtered):
    """
    Sistema de mapas inteligente con navegación automática jerárquica.
    """
    
    try:
        # Determinar nivel actual
        current_level = determine_map_level(filters)
        
        # Breadcrumb navigation
        create_breadcrumb_navigation(current_level, filters, colors)
        
        # Indicador de estado
        show_status_indicator(filters, colors)
        
        # Sistema de mapas con navegación automática
        if current_level == "departamento":
            create_departmental_map_with_navigation(casos, epizootias, geo_data, colors)
        elif current_level == "municipio":
            create_municipal_map_with_veredas(casos, epizootias, geo_data, filters, colors)
        elif current_level == "vereda":
            create_vereda_detail_view(casos, epizootias, filters, colors)
            
    except Exception as e:
        logger.error(f"❌ Error en sistema de mapas inteligente: {str(e)}")
        st.error(f"Error en sistema de mapas: {str(e)}")


def create_departmental_map_with_navigation(casos, epizootias, geo_data, colors):
    """
    Mapa departamental que automáticamente navega a nivel municipal al hacer clic.
    """
    
    try:
        if 'municipios' not in geo_data:
            st.error("No se pudo cargar el shapefile de municipios")
            return
        
        municipios = geo_data['municipios'].copy()
        
        # Preparar datos agregados por municipio
        municipios_data = prepare_municipal_data(casos, epizootias, municipios)
        
        # Configuración del mapa
        bounds = municipios.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Instrucciones
        st.markdown(
            f'''
            <div class="map-instructions">
                <div class="instruction-icon">💡</div>
                <div class="instruction-text">
                    <strong>Navegación Inteligente:</strong> Haga clic en cualquier municipio para 
                    <span class="highlight">filtrar automáticamente</span> y ver sus veredas
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        
        # Crear mapa
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='CartoDB positron',
            zoom_control=False,
            scrollWheelZoom=False,
            doubleClickZoom=False,
            dragging=False,
            attributionControl=False,
        )
        
        # Limitar al área del Tolima
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        
        # Agregar municipios con colores mejorados
        max_casos = municipios_data['casos'].max() if municipios_data['casos'].max() > 0 else 1
        max_epi = municipios_data['epizootias'].max() if municipios_data['epizootias'].max() > 0 else 1
        
        for idx, row in municipios_data.iterrows():
            municipio_name = row['MpNombre']
            casos_count = row['casos']
            fallecidos_count = row['fallecidos']
            epizootias_count = row['epizootias']
            epizootias_positivas = row.get('epizootias_positivas', 0)
            epizootias_en_estudio = row.get('epizootias_en_estudio', 0)
            
            # Colores mejorados
            if casos_count > 0:
                intensity = min(casos_count / max_casos, 1.0)
                fill_color = f"rgba(229, 25, 55, {0.3 + intensity * 0.6})"
                border_color = colors['danger']
                border_weight = 2 + int(intensity * 2)
            elif epizootias_count > 0:
                epi_intensity = min(epizootias_count / max_epi, 1.0)
                fill_color = f"rgba(247, 148, 29, {0.3 + epi_intensity * 0.5})"
                border_color = colors['warning']
                border_weight = 2 + int(epi_intensity * 2)
            else:
                fill_color = "rgba(200, 200, 200, 0.3)"
                border_color = "#999999"
                border_weight = 1
            
            # Tooltip mejorado
            tooltip_text = f"""
            <div style="font-family: 'Segoe UI', Arial; padding: 12px; max-width: 250px; 
                        background: white; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <div style="color: {colors['primary']}; font-size: 1.1rem; font-weight: 700; 
                            margin-bottom: 8px; border-bottom: 2px solid {colors['secondary']}; padding-bottom: 4px;">
                    📍 {municipio_name}
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 8px 0;">
                    <div style="background: #ffebee; padding: 6px; border-radius: 4px; text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: bold; color: {colors['danger']};">🦠 {casos_count}</div>
                        <div style="font-size: 0.7rem; color: #666;">Casos</div>
                    </div>
                    <div style="background: #fff3e0; padding: 6px; border-radius: 4px; text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: bold; color: {colors['warning']};">🐒 {epizootias_count}</div>
                        <div style="font-size: 0.7rem; color: #666;">Epizootias</div>
                    </div>
                </div>
                
                {f'<div style="font-size: 0.8rem; color: #666; margin-top: 6px;">🔴 {epizootias_positivas} positivas • 🔵 {epizootias_en_estudio} en estudio</div>' if epizootias_positivas > 0 or epizootias_en_estudio > 0 else ''}
                
                <div style="background: linear-gradient(45deg, {colors['info']}, {colors['secondary']}); 
                            color: white; padding: 6px; border-radius: 4px; text-align: center; 
                            margin-top: 8px; font-size: 0.8rem; font-weight: 600;">
                    👆 Clic para navegar a veredas
                </div>
            </div>
            """
            
            # Agregar polígono
            geojson = folium.GeoJson(
                row['geometry'],
                style_function=lambda x, color=fill_color, border=border_color, weight=border_weight: {
                    'fillColor': color,
                    'color': border,
                    'weight': weight,
                    'fillOpacity': 0.7,
                    'opacity': 1
                },
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            )
            
            geojson.add_to(m)
        
        # Renderizar mapa
        map_data = st_folium(
            m, 
            width=700,
            height=500,
            returned_objects=["last_object_clicked"],
            key="intelligent_departmental_map"
        )
        
        # Navegación automática
        handle_intelligent_navigation(map_data, municipios_data)
        
    except Exception as e:
        logger.error(f"❌ Error en mapa departamental: {str(e)}")
        st.error(f"Error creando mapa departamental: {str(e)}")


def create_municipal_map_with_veredas(casos, epizootias, geo_data, filters, colors):
    """
    Mapa municipal mostrando veredas con navegación inteligente.
    """
    
    try:
        municipio_display = filters.get('municipio_display', 'Municipio')
        municipio_normalizado = filters.get('municipio_normalizado')
        
        if not municipio_normalizado:
            st.error("No se pudo determinar el municipio para la vista de veredas")
            return
        
        # Header elegante para vista municipal
        st.markdown(
            f'''
            <div class="municipal-header">
                <div class="municipal-icon">🏘️</div>
                <div class="municipal-info">
                    <h3>Vista Municipal: {municipio_display}</h3>
                    <p>Explorando veredas y distribución detallada</p>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        
        if 'veredas' not in geo_data:
            st.warning("🗺️ Shapefile de veredas no disponible - mostrando información tabular")
            show_municipal_tabular_view(casos, epizootias, filters, colors)
            return
        
        # Filtrar veredas del municipio
        veredas = geo_data['veredas'].copy()
        veredas_municipio = pd.DataFrame()
        
        for col in ['municipi_1', 'municipio', 'MUNICIPIO', 'Municipio']:
            if col in veredas.columns:
                veredas_temp = veredas[veredas[col].str.upper().str.strip() == municipio_normalizado.upper()]
                if not veredas_temp.empty:
                    veredas_municipio = veredas_temp
                    break
        
        if veredas_municipio.empty:
            st.warning(f"No se encontraron veredas para el municipio {municipio_display}")
            show_municipal_tabular_view(casos, epizootias, filters, colors)
            return
        
        # Preparar datos por vereda
        veredas_data = prepare_vereda_data(casos, epizootias, veredas_municipio)
        
        # Configuración del mapa de veredas
        bounds = veredas_municipio.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Estadísticas rápidas
        total_veredas = len(veredas_data)
        veredas_con_datos = len(veredas_data[(veredas_data['casos'] > 0) | (veredas_data['epizootias'] > 0)])
        
        st.markdown(
            f'''
            <div class="map-stats">
                <div class="stat-item">
                    <span class="stat-number">{total_veredas}</span>
                    <span class="stat-label">Veredas Total</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{veredas_con_datos}</span>
                    <span class="stat-label">Con Datos</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{total_veredas - veredas_con_datos}</span>
                    <span class="stat-label">Sin Eventos</span>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        
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
        
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        
        # Agregar veredas
        max_casos_vereda = veredas_data['casos'].max() if veredas_data['casos'].max() > 0 else 1
        max_epi_vereda = veredas_data['epizootias'].max() if veredas_data['epizootias'].max() > 0 else 1
        
        for idx, row in veredas_data.iterrows():
            vereda_name = row.get('NOMBRE_VER', row.get('vereda', f'Vereda_{idx}'))
            casos_count = row['casos']
            epizootias_count = row['epizootias']
            epizootias_positivas = row.get('epizootias_positivas', 0)
            epizootias_en_estudio = row.get('epizootias_en_estudio', 0)
            
            # Colores para veredas
            if casos_count > 0:
                intensity = min(casos_count / max_casos_vereda, 1.0)
                fill_color = f"rgba(229, 25, 55, {0.4 + intensity * 0.5})"
                border_color = colors['danger']
                border_weight = 3
            elif epizootias_count > 0:
                intensity = min(epizootias_count / max_epi_vereda, 1.0)
                fill_color = f"rgba(247, 148, 29, {0.4 + intensity * 0.5})"
                border_color = colors['warning']
                border_weight = 2
            else:
                fill_color = "rgba(200, 200, 200, 0.2)"
                border_color = "#cccccc"
                border_weight = 1
            
            # Tooltip para veredas
            tooltip_text = f"""
            <div style="font-family: 'Segoe UI', Arial; padding: 10px; max-width: 220px; 
                        background: white; border-radius: 6px; box-shadow: 0 3px 12px rgba(0,0,0,0.15);">
                <div style="color: {colors['primary']}; font-size: 1rem; font-weight: 700; 
                            margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                    🏘️ {vereda_name}
                </div>
                
                <div style="display: flex; gap: 8px; margin: 6px 0;">
                    <div style="background: #ffebee; padding: 4px 8px; border-radius: 3px; flex: 1; text-align: center;">
                        <div style="font-weight: bold; color: {colors['danger']};">🦠 {casos_count}</div>
                        <div style="font-size: 0.7rem; color: #666;">Casos</div>
                    </div>
                    <div style="background: #fff3e0; padding: 4px 8px; border-radius: 3px; flex: 1; text-align: center;">
                        <div style="font-weight: bold; color: {colors['warning']};">🐒 {epizootias_count}</div>
                        <div style="font-size: 0.7rem; color: #666;">Epizootias</div>
                    </div>
                </div>
                
                {f'<div style="font-size: 0.75rem; color: #666; margin-top: 4px; text-align: center;">🔴 {epizootias_positivas} pos. • 🔵 {epizootias_en_estudio} est.</div>' if epizootias_positivas > 0 or epizootias_en_estudio > 0 else ''}
                
                <div style="background: linear-gradient(45deg, {colors['info']}, {colors['primary']}); 
                            color: white; padding: 4px; border-radius: 3px; text-align: center; 
                            margin-top: 6px; font-size: 0.75rem; font-weight: 600;">
                    👆 Clic para vista detallada
                </div>
            </div>
            """
            
            # Agregar vereda
            geojson = folium.GeoJson(
                row['geometry'],
                style_function=lambda x, color=fill_color, border=border_color, weight=border_weight: {
                    'fillColor': color,
                    'color': border,
                    'weight': weight,
                    'fillOpacity': 0.6,
                    'opacity': 1
                },
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            )
            
            geojson.add_to(m)
        
        # Renderizar mapa de veredas
        map_data = st_folium(
            m, 
            width=700,
            height=500,
            returned_objects=["last_object_clicked"],
            key="intelligent_municipal_map"
        )
        
        # Manejar clics en veredas
        handle_vereda_navigation(map_data, veredas_data, filters)
        
    except Exception as e:
        logger.error(f"❌ Error en mapa municipal: {str(e)}")
        st.error(f"Error creando mapa municipal: {str(e)}")


def create_enhanced_information_cards(casos, epizootias, filters, colors):
    """
    Tarjetas de información mejoradas y funcionales.
    """
    
    try:
        st.markdown(
            '''
            <div class="cards-section-header">
                <h2>📊 Información Detallada</h2>
                <p>Datos actualizados en tiempo real</p>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        
        # Calcular métricas completas
        metrics = calculate_basic_metrics(casos, epizootias)
        
        # Tarjeta 1: Casos Humanos
        create_cases_card(metrics, colors)
        
        # Tarjeta 2: Epizootias
        create_epizootias_card(metrics, colors)
        
        # Tarjeta 3: Ubicación y Navegación
        create_location_card(filters, colors)
        
        # Tarjeta 4: Insights
        create_insights_card(casos, epizootias, metrics, colors)
        
    except Exception as e:
        logger.error(f"❌ Error creando tarjetas de información: {str(e)}")
        st.error(f"Error en tarjetas de información: {str(e)}")


def create_cases_card(metrics, colors):
    """
    Tarjeta de casos con diseño mejorado.
    """
    total_casos = metrics["total_casos"]
    vivos = metrics.get("vivos", 0)
    fallecidos = metrics.get("fallecidos", 0)
    letalidad = metrics.get("letalidad", 0)
    ultimo_caso = metrics.get("ultimo_caso", {"existe": False})
    
    # Determinar nivel de intensidad
    if total_casos == 0:
        intensity_color = "#e0e0e0"
        intensity_level = "Sin casos"
    elif total_casos <= 5:
        intensity_color = colors['success']
        intensity_level = "Bajo"
    elif total_casos <= 15:
        intensity_color = colors['warning']
        intensity_level = "Moderado"
    else:
        intensity_color = colors['danger']
        intensity_level = "Alto"
    
    st.markdown(
        f'''
        <div class="enhanced-card cases-card">
            <div class="card-header">
                <div class="header-icon">🦠</div>
                <div class="header-content">
                    <h3>Casos Humanos</h3>
                    <div class="intensity-badge" style="background: {intensity_color};">
                        Nivel: {intensity_level}
                    </div>
                </div>
                <div class="header-number">{total_casos}</div>
            </div>
            
            <div class="card-body">
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-icon">💚</div>
                        <div class="metric-number" style="color: {colors['success']};">{vivos}</div>
                        <div class="metric-label">Vivos</div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-icon">⚰️</div>
                        <div class="metric-number" style="color: {colors['danger']};">{fallecidos}</div>
                        <div class="metric-label">Fallecidos</div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-icon">📊</div>
                        <div class="metric-number" style="color: {colors['warning']};">{letalidad:.1f}%</div>
                        <div class="metric-label">Letalidad</div>
                    </div>
                </div>
                
                <div class="last-event">
                    {''.join([
                        f'''
                        <div class="event-header">🕐 Último Caso Registrado</div>
                        <div class="event-details">
                            <div class="event-location">📍 {ultimo_caso["ubicacion"]}</div>
                            <div class="event-time">
                                <span class="event-date">{ultimo_caso["fecha"].strftime("%d/%m/%Y") if ultimo_caso["fecha"] else "Sin fecha"}</span>
                                <span class="event-elapsed">{ultimo_caso["tiempo_transcurrido"]}</span>
                            </div>
                        </div>
                        ''' if ultimo_caso["existe"] else '''
                        <div class="event-header">📭 Sin Casos Registrados</div>
                        <div class="event-details no-data">
                            No hay casos disponibles con los filtros actuales
                        </div>
                        '''
                    ])}
                </div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def create_epizootias_card(metrics, colors):
    """
    Tarjeta de epizootias con diseño mejorado.
    """
    total_epizootias = metrics["total_epizootias"]
    positivas = metrics.get("epizootias_positivas", 0)
    en_estudio = metrics.get("epizootias_en_estudio", 0)
    ultima_epizootia = metrics.get("ultima_epizootia_positiva", {"existe": False})
    
    # Calcular porcentaje de positividad
    positividad = (positivas / total_epizootias * 100) if total_epizootias > 0 else 0
    
    # Determinar estado de vigilancia
    if positivas > 0:
        vigilancia_estado = "Activa"
        vigilancia_color = colors['danger']
    elif en_estudio > 0:
        vigilancia_estado = "En Proceso"
        vigilancia_color = colors['warning']
    else:
        vigilancia_estado = "Tranquila"
        vigilancia_color = colors['success']
    
    st.markdown(
        f'''
        <div class="enhanced-card epizootias-card">
            <div class="card-header epi-header">
                <div class="header-icon">🐒</div>
                <div class="header-content">
                    <h3>Vigilancia Epizootias</h3>
                    <div class="intensity-badge" style="background: {vigilancia_color};">
                        Estado: {vigilancia_estado}
                    </div>
                </div>
                <div class="header-number">{total_epizootias}</div>
            </div>
            
            <div class="card-body">
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-icon">🔴</div>
                        <div class="metric-number" style="color: {colors['danger']};">{positivas}</div>
                        <div class="metric-label">Positivas</div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-icon">🔵</div>
                        <div class="metric-number" style="color: {colors['info']};">{en_estudio}</div>
                        <div class="metric-label">En Estudio</div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-icon">📈</div>
                        <div class="metric-number" style="color: {colors['warning']};">{positividad:.1f}%</div>
                        <div class="metric-label">Positividad</div>
                    </div>
                </div>
                
                <div class="last-event">
                    {''.join([
                        f'''
                        <div class="event-header">🔴 Última Epizootia Positiva</div>
                        <div class="event-details">
                            <div class="event-location">📍 {ultima_epizootia["ubicacion"]}</div>
                            <div class="event-time">
                                <span class="event-date">{ultima_epizootia["fecha"].strftime("%d/%m/%Y") if ultima_epizootia["fecha"] else "Sin fecha"}</span>
                                <span class="event-elapsed">{ultima_epizootia["tiempo_transcurrido"]}</span>
                            </div>
                        </div>
                        ''' if ultima_epizootia["existe"] else '''
                        <div class="event-header">✅ Sin Epizootias Positivas</div>
                        <div class="event-details no-data">
                            No hay epizootias positivas registradas actualmente
                        </div>
                        '''
                    ])}
                </div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def create_location_card(filters, colors):
    """
    Tarjeta de ubicación y navegación.
    """
    ubicacion_actual = get_current_location_info(filters)
    filtros_activos = filters.get("active_filters", [])
    current_level = determine_map_level(filters)
    
    # Información de navegación
    level_info = {
        "departamento": {"icon": "🏛️", "name": "Vista Departamental", "description": "Explorando todo el Tolima"},
        "municipio": {"icon": "🏘️", "name": "Vista Municipal", "description": "Analizando veredas del municipio"}, 
        "vereda": {"icon": "📍", "name": "Vista de Vereda", "description": "Datos específicos de la vereda"}
    }
    
    level = level_info[current_level]
    
    st.markdown(
        f'''
        <div class="enhanced-card location-card">
            <div class="card-header location-header">
                <div class="header-icon">{level["icon"]}</div>
                <div class="header-content">
                    <h3>Navegación & Ubicación</h3>
                    <div class="intensity-badge" style="background: {colors['info']};">
                        {level["name"]}
                    </div>
                </div>
            </div>
            
            <div class="card-body">
                <div class="location-breadcrumb">
                    <div class="breadcrumb-header">📍 Ubicación Actual</div>
                    <div class="breadcrumb-path">{ubicacion_actual}</div>
                    <div class="breadcrumb-description">{level["description"]}</div>
                </div>
                
                {''.join([
                    f'''
                    <div class="active-filters">
                        <div class="filters-header">🎯 Filtros Activos ({len(filtros_activos)})</div>
                        <div class="filters-list">
                            {'<br>'.join(filtros_activos[:3])}
                            {f'<div class="more-filters">+{len(filtros_activos) - 3} filtros más</div>' if len(filtros_activos) > 3 else ''}
                        </div>
                    </div>
                    ''' if filtros_activos else '''
                    <div class="active-filters">
                        <div class="filters-header">🌐 Vista Completa</div>
                        <div class="filters-list no-data">
                            Mostrando todos los datos disponibles
                        </div>
                    </div>
                    '''
                ])}
                
                <div class="navigation-help">
                    <div class="help-header">💡 Navegación Inteligente</div>
                    <div class="help-items">
                        <div class="help-item">
                            <span class="help-icon">👆</span>
                            <span class="help-text">Clic en municipio → Vista de veredas</span>
                        </div>
                        <div class="help-item">
                            <span class="help-icon">🔍</span>
                            <span class="help-text">Hover para información rápida</span>
                        </div>
                        <div class="help-item">
                            <span class="help-icon">🧭</span>
                            <span class="help-text">Breadcrumbs para navegar</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def create_insights_card(casos, epizootias, metrics, colors):
    """
    Tarjeta de insights con análisis rápido.
    """
    total_eventos = len(casos) + len(epizootias)
    
    # Actividad reciente (último mes)
    fecha_corte = datetime.now() - pd.Timedelta(days=30)
    casos_recientes = len(casos[casos["fecha_inicio_sintomas"] > fecha_corte]) if not casos.empty and "fecha_inicio_sintomas" in casos.columns else 0
    epi_recientes = len(epizootias[epizootias["fecha_recoleccion"] > fecha_corte]) if not epizootias.empty and "fecha_recoleccion" in epizootias.columns else 0
    
    # Diversidad geográfica
    municipios_afectados = set()
    if not casos.empty and "municipio" in casos.columns:
        municipios_afectados.update(casos["municipio"].dropna())
    if not epizootias.empty and "municipio" in epizootias.columns:
        municipios_afectados.update(epizootias["municipio"].dropna())
    
    # Tendencia
    if casos_recientes + epi_recientes > 0:
        tendencia = "Actividad Reciente"
        tendencia_color = colors['warning']
        tendencia_icon = "📈"
    else:
        tendencia = "Período Tranquilo"
        tendencia_color = colors['success'] 
        tendencia_icon = "📊"
    
    st.markdown(
        f'''
        <div class="enhanced-card insights-card">
            <div class="card-header insights-header">
                <div class="header-icon">🧠</div>
                <div class="header-content">
                    <h3>Insights & Análisis</h3>
                    <div class="intensity-badge" style="background: {tendencia_color};">
                        {tendencia}
                    </div>
                </div>
                <div class="header-number">{total_eventos}</div>
            </div>
            
            <div class="card-body">
                <div class="insights-grid">
                    <div class="insight-item">
                        <div class="insight-icon">🗓️</div>
                        <div class="insight-number">{casos_recientes + epi_recientes}</div>
                        <div class="insight-label">Eventos último mes</div>
                    </div>
                    
                    <div class="insight-item">
                        <div class="insight-icon">🌍</div>
                        <div class="insight-number">{len(municipios_afectados)}</div>
                        <div class="insight-label">Municipios con datos</div>
                    </div>
                    
                    <div class="insight-item">
                        <div class="insight-icon">{tendencia_icon}</div>
                        <div class="insight-number">{(casos_recientes + epi_recientes) / total_eventos * 100 if total_eventos > 0 else 0:.0f}%</div>
                        <div class="insight-label">Actividad reciente</div>
                    </div>
                </div>
                
                <div class="executive-summary">
                    <div class="summary-header">📋 Resumen Ejecutivo</div>
                    <div class="summary-content">
                        {''.join([
                            f"📊 <strong>{total_eventos}</strong> eventos totales registrados<br>",
                            f"🗓️ <strong>{casos_recientes + epi_recientes}</strong> eventos en los últimos 30 días<br>",
                            f"🌍 <strong>{len(municipios_afectados)}</strong> municipios con actividad documentada<br>",
                            f"🔍 Sistema de vigilancia epidemiológica {'activo' if casos_recientes + epi_recientes > 0 else 'en estado de tranquilidad'}"
                        ])}
                    </div>
                </div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def apply_enhanced_cards_css(colors):
    """
    CSS mejorado para tarjetas atractivas.
    """
    st.markdown(
        f'''
        <style>
        /* Hero Title */
        .hero-title {{
            background: linear-gradient(135deg, {colors['primary']} 0%, {colors['accent']} 50%, {colors['secondary']} 100%);
            color: white;
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            position: relative;
            overflow: hidden;
        }}
        
        .hero-title::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: shine 3s infinite;
        }}
        
        @keyframes shine {{
            0% {{ transform: translateX(-100%) translateY(-100%) rotate(45deg); }}
            100% {{ transform: translateX(100%) translateY(100%) rotate(45deg); }}
        }}
        
        .hero-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            animation: float 3s ease-in-out infinite;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
        }}
        
        .hero-title h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 800;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .hero-title p {{
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 500;
        }}
        
        /* Cards Section */
        .cards-section-header {{
            text-align: center;
            margin-bottom: 1.5rem;
        }}
        
        .cards-section-header h2 {{
            color: {colors['primary']};
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .cards-section-header p {{
            color: #666;
            font-size: 1rem;
            margin: 0;
        }}
        
        /* Enhanced Cards */
        .enhanced-card {{
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.12);
            overflow: hidden;
            margin-bottom: 1.5rem;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            border: 1px solid rgba(255,255,255,0.8);
        }}
        
        .enhanced-card:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 16px 48px rgba(0,0,0,0.18);
        }}
        
        .enhanced-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, {colors['primary']}, {colors['secondary']}, {colors['accent']});
        }}
        
        /* Card Headers */
        .card-header {{
            padding: 1.5rem;
            background: linear-gradient(135deg, {colors['primary']} 0%, {colors['accent']} 100%);
            color: white;
            display: flex;
            align-items: center;
            gap: 1rem;
            position: relative;
        }}
        
        .card-header.epi-header {{
            background: linear-gradient(135deg, {colors['warning']} 0%, #e67e22 100%);
        }}
        
        .card-header.location-header {{
            background: linear-gradient(135deg, {colors['info']} 0%, {colors['primary']} 100%);
        }}
        
        .card-header.insights-header {{
            background: linear-gradient(135deg, #9b59b6 0%, {colors['accent']} 100%);
        }}
        
        .header-icon {{
            font-size: 2.5rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
        }}
        
        .header-content {{
            flex: 1;
        }}
        
        .header-content h3 {{
            margin: 0;
            font-size: 1.4rem;
            font-weight: 700;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        }}
        
        .intensity-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 0.25rem;
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.3);
        }}
        
        .header-number {{
            font-size: 2.5rem;
            font-weight: 800;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            animation: countup 1s ease-out;
        }}
        
        @keyframes countup {{
            from {{ transform: scale(0); opacity: 0; }}
            to {{ transform: scale(1); opacity: 1; }}
        }}
        
        /* Card Body */
        .card-body {{
            padding: 1.5rem;
        }}
        
        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        
        .metric-item {{
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            border: 2px solid transparent;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .metric-item:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .metric-icon {{
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .metric-number {{
            font-size: 1.6rem;
            font-weight: 800;
            color: {colors['primary']};
            margin-bottom: 0.25rem;
        }}
        
        .metric-label {{
            font-size: 0.8rem;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Last Event Section */
        .last-event {{
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            padding: 1rem;
            border-radius: 12px;
            border-left: 4px solid {colors['info']};
        }}
        
        .event-header {{
            font-size: 0.9rem;
            font-weight: 700;
            color: {colors['primary']};
            margin-bottom: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .event-details {{
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        
        .event-location {{
            font-weight: 600;
            color: {colors['accent']};
            margin-bottom: 0.25rem;
        }}
        
        .event-time {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .event-date {{
            color: {colors['info']};
            font-weight: 600;
        }}
        
        .event-elapsed {{
            color: {colors['warning']};
            font-weight: 500;
            font-style: italic;
            background: rgba(255,255,255,0.8);
            padding: 0.2rem 0.5rem;
            border-radius: 8px;
            font-size: 0.8rem;
        }}
        
        .no-data {{
            color: #999;
            font-style: italic;
            text-align: center;
        }}
        
        /* Location Specific */
        .location-breadcrumb {{
            background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
        }}
        
        .breadcrumb-header {{
            font-size: 0.9rem;
            font-weight: 700;
            color: {colors['primary']};
            margin-bottom: 0.5rem;
            text-transform: uppercase;
        }}
        
        .breadcrumb-path {{
            font-size: 1.2rem;
            font-weight: 700;
            color: {colors['accent']};
            margin-bottom: 0.25rem;
        }}
        
        .breadcrumb-description {{
            font-size: 0.85rem;
            color: #666;
            font-style: italic;
        }}
        
        .active-filters {{
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b3 100%);
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            border-left: 4px solid {colors['warning']};
        }}
        
        .filters-header {{
            font-size: 0.9rem;
            font-weight: 700;
            color: {colors['primary']};
            margin-bottom: 0.5rem;
            text-transform: uppercase;
        }}
        
        .filters-list {{
            font-size: 0.85rem;
            color: #333;
            line-height: 1.5;
        }}
        
        .more-filters {{
            color: {colors['info']};
            font-weight: 600;
            margin-top: 0.25rem;
            font-style: italic;
        }}
        
        .navigation-help {{
            background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
            padding: 1rem;
            border-radius: 12px;
            border-left: 4px solid {colors['success']};
        }}
        
        .help-header {{
            font-size: 0.9rem;
            font-weight: 700;
            color: {colors['primary']};
            margin-bottom: 0.75rem;
            text-transform: uppercase;
        }}
        
        .help-items {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        
        .help-item {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.85rem;
        }}
        
        .help-icon {{
            font-size: 1rem;
            width: 1.5rem;
            text-align: center;
        }}
        
        .help-text {{
            color: #555;
            line-height: 1.4;
        }}
        
        /* Insights Card */
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        
        .insight-item {{
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            border: 2px solid {colors['info']};
            transition: all 0.3s ease;
        }}
        
        .insight-item:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        }}
        
        .insight-icon {{
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .insight-number {{
            font-size: 1.4rem;
            font-weight: 800;
            color: {colors['primary']};
            margin-bottom: 0.25rem;
        }}
        
        .insight-label {{
            font-size: 0.75rem;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .executive-summary {{
            background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
            padding: 1rem;
            border-radius: 12px;
            border-left: 4px solid #9b59b6;
        }}
        
        .summary-header {{
            font-size: 0.9rem;
            font-weight: 700;
            color: {colors['primary']};
            margin-bottom: 0.75rem;
            text-transform: uppercase;
        }}
        
        .summary-content {{
            font-size: 0.85rem;
            color: #333;
            line-height: 1.6;
        }}
        
        /* Map Enhancements */
        .map-instructions {{
            background: linear-gradient(135deg, {colors['info']} 0%, {colors['secondary']} 100%);
            color: white;
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }}
        
        .instruction-icon {{
            font-size: 1.5rem;
            animation: bounce 2s infinite;
        }}
        
        @keyframes bounce {{
            0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
            40% {{ transform: translateY(-10px); }}
            60% {{ transform: translateY(-5px); }}
        }}
        
        .instruction-text {{
            flex: 1;
            font-size: 0.95rem;
            line-height: 1.4;
        }}
        
        .highlight {{
            background: rgba(255,255,255,0.2);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-weight: 600;
        }}
        
        .municipal-header {{
            background: linear-gradient(135deg, {colors['accent']} 0%, {colors['primary']} 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }}
        
        .municipal-icon {{
            font-size: 2rem;
            animation: rotate 4s linear infinite;
        }}
        
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        .municipal-info h3 {{
            margin: 0;
            font-size: 1.4rem;
            font-weight: 700;
        }}
        
        .municipal-info p {{
            margin: 0.25rem 0 0 0;
            opacity: 0.9;
            font-size: 0.9rem;
        }}
        
        .map-stats {{
            display: flex;
            justify-content: space-around;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-number {{
            display: block;
            font-size: 1.5rem;
            font-weight: 800;
            color: {colors['primary']};
        }}
        
        .stat-label {{
            font-size: 0.8rem;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .metrics-grid {{
                grid-template-columns: 1fr;
                gap: 0.75rem;
            }}
            
            .insights-grid {{
                grid-template-columns: 1fr;
                gap: 0.75rem;
            }}
            
            .hero-title h1 {{
                font-size: 2rem;
            }}
            
            .header-number {{
                font-size: 2rem;
            }}
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )


def handle_intelligent_navigation(map_data, municipios_data):
    """
    Navegación inteligente que automáticamente cambia al nivel municipal con veredas.
    """
    try:
        if not map_data or not map_data.get('last_object_clicked'):
            return
        
        clicked_object = map_data['last_object_clicked']
        
        if isinstance(clicked_object, dict) and 'lat' in clicked_object and 'lng' in clicked_object:
            clicked_lat = clicked_object.get('lat')
            clicked_lng = clicked_object.get('lng')
            
            if clicked_lat and clicked_lng:
                # Encontrar el municipio más cercano
                min_distance = float('inf')
                municipio_clicked = None
                municipio_data = None
                
                for idx, row in municipios_data.iterrows():
                    try:
                        centroid = row['geometry'].centroid
                        distance = ((centroid.x - clicked_lng)**2 + (centroid.y - clicked_lat)**2)**0.5
                        
                        if distance < min_distance:
                            min_distance = distance
                            municipio_clicked = row['MpNombre']
                            municipio_data = row
                    except Exception:
                        continue
                
                if municipio_clicked and min_distance < 0.1:
                    # Navegación automática inteligente
                    st.session_state['municipio_filter'] = municipio_clicked
                    st.session_state['vereda_filter'] = 'Todas'  # Resetear vereda
                    
                    # Mensaje de transición elegante
                    casos_count = municipio_data['casos'] if municipio_data is not None else 0
                    epi_count = municipio_data['epizootias'] if municipio_data is not None else 0
                    
                    if casos_count > 0 or epi_count > 0:
                        st.success(
                            f"🗺️ **Navegación Automática Activada**\n\n"
                            f"📍 **Municipio:** {municipio_clicked}\n"
                            f"📊 **Datos:** {casos_count} casos humanos • {epi_count} epizootias\n"
                            f"🔄 **Vista:** Cambiando a nivel municipal con veredas..."
                        )
                    else:
                        st.info(
                            f"🗺️ **Navegación Automática Activada**\n\n"
                            f"📍 **Municipio:** {municipio_clicked}\n"
                            f"📊 **Estado:** Sin eventos registrados\n"
                            f"🔄 **Vista:** Explorando veredas del municipio..."
                        )
                    
                    # Rerun inmediato para mostrar veredas
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"❌ Error en navegación automática: {str(e)}")
        st.error(f"Error en navegación automática: {str(e)}")


def handle_vereda_navigation(map_data, veredas_data, filters):
    """
    Navegación a nivel de vereda específica.
    """
    try:
        if not map_data or not map_data.get('last_object_clicked'):
            return
        
        clicked_object = map_data['last_object_clicked']
        
        if isinstance(clicked_object, dict) and 'lat' in clicked_object and 'lng' in clicked_object:
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
                            vereda_clicked = row.get('NOMBRE_VER', row.get('vereda', f'Vereda_{idx}'))
                            vereda_data = row
                    except Exception:
                        continue
                
                if vereda_clicked and min_distance < 0.05:
                    # Filtrar por vereda específica
                    st.session_state['vereda_filter'] = vereda_clicked
                    
                    # Mensaje elegante de navegación a vereda
                    casos_count = vereda_data['casos'] if vereda_data is not None else 0
                    epi_count = vereda_data['epizootias'] if vereda_data is not None else 0
                    municipio_name = filters.get('municipio_display', 'Municipio')
                    
                    if casos_count > 0 or epi_count > 0:
                        st.success(
                            f"📍 **Navegación a Vereda Específica**\n\n"
                            f"🏘️ **Vereda:** {vereda_clicked}\n"
                            f"🏛️ **Municipio:** {municipio_name}\n"
                            f"📊 **Datos:** {casos_count} casos • {epi_count} epizootias\n"
                            f"🔍 **Vista:** Análisis detallado activado"
                        )
                    else:
                        st.info(
                            f"📍 **Navegación a Vereda Específica**\n\n"
                            f"🏘️ **Vereda:** {vereda_clicked}\n"
                            f"🏛️ **Municipio:** {municipio_name}\n"
                            f"📊 **Estado:** Sin eventos registrados\n"
                            f"🔍 **Vista:** Análisis de zona tranquila"
                        )
                    
                    # Actualizar vista
                    st.rerun()
                    
    except Exception as e:
        logger.warning(f"Error en navegación de vereda: {str(e)}")


def create_breadcrumb_navigation(current_level, filters, colors):
    """
    Sistema de breadcrumb elegante con navegación funcional.
    """
    try:
        # Construir breadcrumb path
        breadcrumb_items = []
        
        # Siempre empezar con Tolima
        breadcrumb_items.append({
            'name': 'Tolima',
            'icon': '🏛️',
            'level': 'departamento',
            'active': current_level == 'departamento'
        })
        
        # Agregar municipio si está seleccionado
        if filters.get('municipio_display') and filters['municipio_display'] != 'Todos':
            breadcrumb_items.append({
                'name': filters['municipio_display'],
                'icon': '🏘️',
                'level': 'municipio', 
                'active': current_level == 'municipio'
            })
        
        # Agregar vereda si está seleccionada
        if filters.get('vereda_display') and filters['vereda_display'] != 'Todas':
            breadcrumb_items.append({
                'name': filters['vereda_display'],
                'icon': '📍',
                'level': 'vereda',
                'active': current_level == 'vereda'
            })
        
        # Crear HTML del breadcrumb
        breadcrumb_html = '<div class="elegant-breadcrumb">'
        
        for i, item in enumerate(breadcrumb_items):
            # Separador
            if i > 0:
                breadcrumb_html += '<div class="breadcrumb-separator">→</div>'
            
            # Item
            active_class = 'active' if item['active'] else ''
            breadcrumb_html += f'''
            <div class="breadcrumb-item {active_class}">
                <span class="breadcrumb-icon">{item['icon']}</span>
                <span class="breadcrumb-text">{item['name']}</span>
            </div>
            '''
        
        breadcrumb_html += '</div>'
        
        # CSS para el breadcrumb
        st.markdown(
            f'''
            <style>
            .elegant-breadcrumb {{
                display: flex;
                align-items: center;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 1rem 1.5rem;
                border-radius: 12px;
                margin-bottom: 1rem;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                border-left: 4px solid {colors['primary']};
            }}
            
            .breadcrumb-item {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                transition: all 0.3s ease;
                cursor: pointer;
            }}
            
            .breadcrumb-item:hover {{
                background: rgba(255,255,255,0.8);
                transform: translateY(-1px);
            }}
            
            .breadcrumb-item.active {{
                background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
                color: white;
                font-weight: 600;
            }}
            
            .breadcrumb-icon {{
                font-size: 1.2rem;
            }}
            
            .breadcrumb-text {{
                font-size: 0.9rem;
                font-weight: 500;
            }}
            
            .breadcrumb-separator {{
                margin: 0 0.5rem;
                color: {colors['accent']};
                font-weight: 600;
                font-size: 1.1rem;
            }}
            </style>
            ''',
            unsafe_allow_html=True,
        )
        
        st.markdown(breadcrumb_html, unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"❌ Error creando breadcrumb: {str(e)}")


def show_status_indicator(filters, colors):
    """
    Indicador de estado animado para mostrar el nivel actual.
    """
    try:
        current_level = determine_map_level(filters)
        
        level_config = {
            'departamento': {
                'name': 'Vista Departamental',
                'description': 'Explorando todos los municipios del Tolima',
                'icon': '🏛️',
                'color': colors['info']
            },
            'municipio': {
                'name': 'Vista Municipal',
                'description': f"Analizando veredas de {filters.get('municipio_display', 'Municipio')}",
                'icon': '🏘️',
                'color': colors['warning']
            },
            'vereda': {
                'name': 'Vista de Vereda',
                'description': f"Datos específicos de {filters.get('vereda_display', 'Vereda')}",
                'icon': '📍',
                'color': colors['danger']
            }
        }
        
        config = level_config[current_level]
        
        st.markdown(
            f'''
            <div class="status-indicator" style="background: {config['color']};">
                <div class="status-icon">{config['icon']}</div>
                <div class="status-content">
                    <div class="status-title">{config['name']}</div>
                    <div class="status-description">{config['description']}</div>
                </div>
                <div class="status-pulse"></div>
            </div>
            
            <style>
            .status-indicator {{
                display: flex;
                align-items: center;
                gap: 1rem;
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 12px;
                margin-bottom: 1rem;
                position: relative;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            }}
            
            .status-icon {{
                font-size: 1.8rem;
                animation: glow 2s ease-in-out infinite alternate;
            }}
            
            @keyframes glow {{
                from {{ text-shadow: 0 0 5px rgba(255,255,255,0.5); }}
                to {{ text-shadow: 0 0 20px rgba(255,255,255,0.8), 0 0 30px rgba(255,255,255,0.6); }}
            }}
            
            .status-content {{
                flex: 1;
            }}
            
            .status-title {{
                font-size: 1.1rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
            }}
            
            .status-description {{
                font-size: 0.9rem;
                opacity: 0.9;
            }}
            
            .status-pulse {{
                position: absolute;
                top: 0;
                right: 0;
                bottom: 0;
                width: 4px;
                background: rgba(255,255,255,0.6);
                animation: pulse-bar 1.5s ease-in-out infinite;
            }}
            
            @keyframes pulse-bar {{
                0%, 100% {{ opacity: 0.6; transform: scaleY(1); }}
                50% {{ opacity: 1; transform: scaleY(1.2); }}
            }}
            </style>
            ''',
            unsafe_allow_html=True,
        )
        
    except Exception as e:
        logger.error(f"❌ Error creando indicador de estado: {str(e)}")


# === FUNCIONES DE APOYO EXISTENTES ===

def prepare_municipal_data(casos, epizootias, municipios):
    """Prepara datos agregados por municipio."""
    try:
        casos_por_municipio = {}
        fallecidos_por_municipio = {}
        
        if not casos.empty and 'municipio_normalizado' in casos.columns:
            casos_counts = casos.groupby('municipio_normalizado').size()
            casos_por_municipio = casos_counts.to_dict()
            
            if 'condicion_final' in casos.columns:
                fallecidos_counts = casos[casos['condicion_final'] == 'Fallecido'].groupby('municipio_normalizado').size()
                fallecidos_por_municipio = fallecidos_counts.to_dict()
        
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
        
        municipios_data = municipios.copy()
        
        municipios_data['casos'] = municipios_data['municipi_1'].map(casos_por_municipio).fillna(0).astype(int)
        municipios_data['fallecidos'] = municipios_data['municipi_1'].map(fallecidos_por_municipio).fillna(0).astype(int)
        municipios_data['epizootias'] = municipios_data['municipi_1'].map(epizootias_por_municipio).fillna(0).astype(int)
        municipios_data['epizootias_positivas'] = municipios_data['municipi_1'].map(positivas_por_municipio).fillna(0).astype(int)
        municipios_data['epizootias_en_estudio'] = municipios_data['municipi_1'].map(en_estudio_por_municipio).fillna(0).astype(int)
        
        return municipios_data
        
    except Exception as e:
        logger.error(f"❌ Error preparando datos municipales: {str(e)}")
        return municipios


def prepare_vereda_data(casos, epizootias, veredas_gdf):
    """Prepara datos agregados por vereda."""
    try:
        casos_por_vereda = {}
        epizootias_por_vereda = {}
        positivas_por_vereda = {}
        en_estudio_por_vereda = {}
        
        if not casos.empty and 'vereda_normalizada' in casos.columns:
            for vereda_norm, group in casos.groupby('vereda_normalizada'):
                casos_por_vereda[vereda_norm.upper()] = len(group)
        
        if not epizootias.empty and 'vereda_normalizada' in epizootias.columns:
            for vereda_norm, group in epizootias.groupby('vereda_normalizada'):
                epizootias_por_vereda[vereda_norm.upper()] = len(group)
                
                if 'descripcion' in group.columns:
                    positivas_por_vereda[vereda_norm.upper()] = len(group[group['descripcion'] == 'POSITIVO FA'])
                    en_estudio_por_vereda[vereda_norm.upper()] = len(group[group['descripcion'] == 'EN ESTUDIO'])
        
        veredas_data = veredas_gdf.copy()
        
        for col in ['NOMBRE_VER', 'vereda', 'Vereda']:
            if col in veredas_data.columns:
                veredas_data['casos'] = veredas_data[col].str.upper().str.strip().map(casos_por_vereda).fillna(0).astype(int)
                veredas_data['epizootias'] = veredas_data[col].str.upper().str.strip().map(epizootias_por_vereda).fillna(0).astype(int)
                veredas_data['epizootias_positivas'] = veredas_data[col].str.upper().str.strip().map(positivas_por_vereda).fillna(0).astype(int)
                veredas_data['epizootias_en_estudio'] = veredas_data[col].str.upper().str.strip().map(en_estudio_por_vereda).fillna(0).astype(int)
                break
        
        for col in ['casos', 'epizootias', 'epizootias_positivas', 'epizootias_en_estudio']:
            if col not in veredas_data.columns:
                veredas_data[col] = 0
        
        return veredas_data
        
    except Exception as e:
        logger.error(f"❌ Error preparando datos de veredas: {str(e)}")
        return veredas_gdf


def determine_map_level(filters):
    """Determina el nivel actual del mapa."""
    if filters.get("vereda_normalizada"):
        return "vereda"
    elif filters.get("municipio_normalizado"):
        return "municipio"
    else:
        return "departamento"


def get_current_location_info(filters):
    """Obtiene información de ubicación actual."""
    location_parts = []
    
    if filters.get("municipio_display") and filters["municipio_display"] != "Todos":
        location_parts.append(f"{filters['municipio_display']}")
    
    if filters.get("vereda_display") and filters["vereda_display"] != "Todas":
        location_parts.append(f"{filters['vereda_display']}")
    
    if not location_parts:
        return "Tolima - Vista Departamental"
    
    return " → ".join(location_parts)

def create_vereda_detail_view(casos, epizootias, filters, colors):
    """Vista detallada para vereda específica."""
    vereda_display = filters.get('vereda_display', 'Vereda')
    municipio_display = filters.get('municipio_display', 'Municipio')
    
    st.markdown(
        f'''
        <div class="vereda-detail-hero">
            <div class="detail-icon">📍</div>
            <div class="detail-content">
                <h2>{vereda_display}</h2>
                <p>Análisis detallado • {municipio_display}</p>
            </div>
        </div>
        
        <style>
        .vereda-detail-hero {{
            background: linear-gradient(135deg, {colors['accent']} 0%, {colors['primary']} 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 1.5rem;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }}
        
        .detail-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            animation: float 3s ease-in-out infinite;
        }}
        
        .detail-content h2 {{
            margin: 0;
            font-size: 1.8rem;
            font-weight: 700;
        }}
        
        .detail-content p {{
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
            font-size: 1rem;
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )
    
    # Estadísticas rápidas
    total_casos = len(casos)
    total_epizootias = len(epizootias)
    actividad_total = total_casos + total_epizootias
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🦠 Casos Humanos", total_casos)
    
    with col2:
        st.metric("🐒 Epizootias", total_epizootias)
    
    with col3:
        st.metric("📊 Actividad Total", actividad_total)
    
    if actividad_total > 0:
        st.markdown("---")
        st.markdown("### 📊 Análisis Detallado de la Vereda")
        
        # Análisis temporal si hay datos
        if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
            casos_fecha = casos.dropna(subset=["fecha_inicio_sintomas"])
            if not casos_fecha.empty:
                st.markdown("**📅 Casos por Fecha**")
                casos_temporal = casos_fecha.groupby(casos_fecha["fecha_inicio_sintomas"].dt.date).size().reset_index()
                casos_temporal.columns = ["Fecha", "Casos"]
                st.dataframe(casos_temporal, use_container_width=True, height=200)
        
        if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
            epi_fecha = epizootias.dropna(subset=["fecha_recoleccion"])
            if not epi_fecha.empty:
                st.markdown("**📅 Epizootias por Fecha y Tipo**")
                epi_temporal = epi_fecha.groupby([epi_fecha["fecha_recoleccion"].dt.date, "descripcion"]).size().reset_index()
                epi_temporal.columns = ["Fecha", "Tipo", "Cantidad"]
                st.dataframe(epi_temporal, use_container_width=True, height=200)
    else:
        st.info("📊 Esta vereda no presenta eventos registrados en el período actual")


def show_municipal_tabular_view(casos, epizootias, filters, colors):
    """Vista tabular cuando no hay shapefiles."""
    municipio_display = filters.get('municipio_display', 'Municipio')
    
    st.markdown(
        f'''
        <div class="tabular-view-notice">
            <div class="notice-icon">📊</div>
            <div class="notice-content">
                <h3>Vista Tabular: {municipio_display}</h3>
                <p>Mapa de veredas no disponible - mostrando análisis tabular detallado</p>
            </div>
        </div>
        
        <style>
        .tabular-view-notice {{
            background: linear-gradient(135deg, {colors['info']} 0%, {colors['secondary']} 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }}
        
        .notice-icon {{
            font-size: 2rem;
        }}
        
        .notice-content h3 {{
            margin: 0;
            font-size: 1.3rem;
            font-weight: 700;
        }}
        
        .notice-content p {{
            margin: 0.25rem 0 0 0;
            opacity: 0.9;
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not casos.empty and "vereda" in casos.columns:
            st.markdown("**📊 Casos por Vereda**")
            vereda_casos = casos["vereda"].value_counts().head(10)
            if not vereda_casos.empty:
                st.dataframe(vereda_casos.to_frame("Casos"), use_container_width=True)
            else:
                st.info("No hay casos registrados por vereda")
    
    with col2:
        if not epizootias.empty and "vereda" in epizootias.columns:
            st.markdown("**📊 Epizootias por Vereda**")
            vereda_epi = epizootias["vereda"].value_counts().head(10)
            if not vereda_epi.empty:
                st.dataframe(vereda_epi.to_frame("Epizootias"), use_container_width=True)
            else:
                st.info("No hay epizootias registradas por vereda")


def check_shapefiles_availability():
    """Verifica disponibilidad de shapefiles."""
    municipios_path = PROCESSED_DIR / "tolima_municipios.shp"
    veredas_path = PROCESSED_DIR / "tolima_veredas.shp"
    return municipios_path.exists() or veredas_path.exists()


def load_geographic_data_silent():
    """Carga datos geográficos sin mensajes."""
    geo_data = {}
    
    try:
        municipios_path = PROCESSED_DIR / "tolima_municipios.shp"
        if municipios_path.exists():
            geo_data['municipios'] = gpd.read_file(municipios_path)
        
        veredas_path = PROCESSED_DIR / "tolima_veredas.shp"
        if veredas_path.exists():
            geo_data['veredas'] = gpd.read_file(veredas_path)
        
        return geo_data
        
    except Exception as e:
        st.error(f"❌ Error cargando datos geográficos: {str(e)}")
        return None


def show_maps_not_available():
    """Mensaje cuando librerías no están disponibles."""
    st.error("⚠️ Librerías de mapas no instaladas. Instale: geopandas folium streamlit-folium")


def show_shapefiles_setup_instructions():
    """Instrucciones para configurar shapefiles."""
    st.error("🗺️ Shapefiles no encontrados en la ruta configurada")


def show_geographic_data_error():
    """Mensaje de error al cargar datos."""
    st.error("❌ Error al cargar datos geográficos")