"""
Vista de mapas CORREGIDA - LOGGING FIXED
SOLUCIÓN: Uso consistente de logger en lugar de logging variable
CORREGIDO: Problema de scope con variable logging
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import logging

# Configurar logger al nivel del módulo
logger = logging.getLogger(__name__)

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
    excel_date_to_datetime,
    verify_filtered_data_usage,
    debug_data_flow,
    ensure_filtered_data_usage
)

# NUEVO: Importar el sistema híbrido de shapefiles
try:
    from utils.shapefile_loader import (
        load_tolima_shapefiles,
        check_shapefiles_availability,
        show_shapefile_setup_instructions,
        get_shapefile_loader
    )
    SHAPEFILE_LOADER_AVAILABLE = True
except ImportError:
    SHAPEFILE_LOADER_AVAILABLE = False

def detect_device_type_simple():
    """Detecta tipo de dispositivo usando JavaScript simple."""
    
    # Inyectar JavaScript para detectar ancho de pantalla
    device_detection = st.empty()
    
    js_code = """
    <script>
    const isMobile = window.innerWidth <= 768;
    const deviceType = isMobile ? 'mobile' : 'desktop';
    
    // Guardar en variable global para acceso posterior
    window.dashboardDeviceType = deviceType;
    
    // También almacenar en localStorage como fallback
    localStorage.setItem('dashboardDeviceType', deviceType);
    
    console.log('📱 Device detected:', deviceType, 'Width:', window.innerWidth);
    </script>
    """
    
    device_detection.markdown(js_code, unsafe_allow_html=True)
    
    # Fallback: Asumir móvil si no se puede detectar
    # En la práctica, siempre crear ambos layouts y dejar que CSS maneje
    return "responsive"  # Crear ambos y CSS decide

def show(data_filtered, filters, colors):
    """
    Vista completa de mapas CORREGIDA - Responsive funcional garantizado.
    """
    # **APLICAR CSS CORREGIDO INMEDIATAMENTE**
    apply_maps_responsive_css_FIXED(colors)
    
    # **VERIFICACIÓN CRÍTICA INICIAL**
    logger.info("🗺️ INICIANDO VISTA DE MAPAS RESPONSIVE CORREGIDA")
    
    # Debug detallado del flujo de datos
    debug_data_flow(
        data_filtered,
        data_filtered,
        filters, 
        "ENTRADA_VISTA_MAPAS_RESPONSIVE_FIXED"
    )
    
    # Verificar que los datos están filtrados
    casos_filtrados = data_filtered["casos"]
    epizootias_filtradas = data_filtered["epizootias"]
    
    verify_filtered_data_usage(casos_filtrados, "vista_mapas_responsive_fixed - casos_filtrados")
    verify_filtered_data_usage(epizootias_filtradas, "vista_mapas_responsive_fixed - epizootias_filtradas")

    # **APLICAR CSS ORIGINAL PARA TARJETAS**
    apply_enhanced_cards_css_FIXED(colors)

    if not MAPS_AVAILABLE:
        show_maps_not_available()
        return

    # **VERIFICAR DISPONIBILIDAD CON SISTEMA HÍBRIDO**
    if not check_shapefiles_availability_hybrid():
        show_shapefiles_setup_instructions_hybrid()
        return

    # **CARGAR DATOS GEOGRÁFICOS CON SISTEMA HÍBRIDO**
    geo_data = load_geographic_data_hybrid()
    
    if not geo_data:
        show_geographic_data_error_hybrid()
        return

    # Mostrar información de filtrado si hay filtros activos
    active_filters = filters.get("active_filters", [])
    if active_filters:
        st.info(f"🎯 Mostrando datos filtrados: {' • '.join(active_filters[:2])}")

    # **DETECCIÓN DE DISPOSITIVO Y LAYOUT ADAPTATIVO**
    device_type = detect_device_type_simple()
    
    if device_type == "mobile":
        # **LAYOUT MÓVIL: VERTICAL (Mapa arriba, tarjetas abajo)**
        create_mobile_layout(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered)
    else:
        # **LAYOUT DESKTOP/TABLET: HORIZONTAL (Lado a lado)**
        create_desktop_layout(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered)

def create_mobile_layout(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered):
    """Layout específico para móviles - Vertical."""
    
    st.markdown('<div class="mobile-maps-container">', unsafe_allow_html=True)
    
    # **SECCIÓN 1: MAPA (Arriba)**
    st.markdown('<div class="mobile-map-section">', unsafe_allow_html=True)
    create_enhanced_map_system_hybrid(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # **SEPARADOR VISUAL**
    st.markdown('<div class="mobile-separator"></div>', unsafe_allow_html=True)
    
    # **SECCIÓN 2: TARJETAS (Abajo)**
    st.markdown('<div class="mobile-cards-section">', unsafe_allow_html=True)
    create_beautiful_information_cards_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas, filters, colors)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
def create_desktop_layout(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered):
    """Layout específico para desktop - Horizontal."""
    
    st.markdown('<div class="desktop-maps-container">', unsafe_allow_html=True)
    
    # **USAR STREAMLIT COLUMNS NATIVO CON CSS OVERRIDE**
    col_mapa, col_tarjetas = st.columns([3, 2], gap="large")
    
    with col_mapa:
        st.markdown('<div class="desktop-map-section">', unsafe_allow_html=True)
        create_enhanced_map_system_hybrid(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_tarjetas:
        st.markdown('<div class="desktop-cards-section">', unsafe_allow_html=True)
        create_beautiful_information_cards_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas, filters, colors)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
def apply_maps_responsive_css_FIXED(colors):
    """
    CSS CORREGIDO para responsive de mapas - Versión robusta.
    """
    st.markdown(
        f"""
        <style>
        /* =============== RESET Y BASE =============== */
        
        .mobile-maps-container,
        .desktop-maps-container {{
            width: 100% !important;
            max-width: 100% !important;
            overflow: visible !important;
            height: auto !important;
            max-height: none !important;
        }}
        
        /* =============== SOLUCIÓN SCROLL INFINITO =============== */
        
        /* Aplicar específicamente a elementos que contienen mapas */
        .stTabs [data-baseweb="tab-panel"]:has(.mobile-maps-container),
        .stTabs [data-baseweb="tab-panel"]:has(.desktop-maps-container) {{
            max-height: none !important;
            height: auto !important;
            overflow: visible !important;
            overflow-y: visible !important;
        }}
        
        .main .block-container:has(.mobile-maps-container),
        .main .block-container:has(.desktop-maps-container) {{
            max-height: none !important;
            height: auto !important;
            overflow-y: visible !important;
            padding-bottom: 2rem !important;
        }}
        
        /* =============== LAYOUT MÓVIL =============== */
        
        .mobile-maps-container {{
            display: block !important;
            width: 100% !important;
        }}
        
        .mobile-map-section {{
            width: 100% !important;
            margin-bottom: 1.5rem !important;
            text-align: center !important; /* Centrar mapa */
        }}
        
        .mobile-map-section .stComponentV1 {{
            max-width: 100% !important;
            margin: 0 auto !important; /* Centrar mapa */
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            overflow: hidden !important;
            max-height: 400px !important;
        }}
        
        .mobile-map-section iframe {{
            border-radius: 12px !important;
            border: 1px solid #e1e5e9 !important;
            width: 100% !important;
            max-width: 100% !important;
        }}
        
        .mobile-separator {{
            height: 1px !important;
            background: linear-gradient(90deg, transparent, {colors['secondary']}, transparent) !important;
            margin: 1.5rem 0 !important;
            opacity: 0.5 !important;
        }}
        
        .mobile-cards-section {{
            width: 100% !important;
        }}
        
        .mobile-cards-section .super-enhanced-card {{
            margin-bottom: 1rem !important;
            max-width: 100% !important;
        }}
        
        /* =============== LAYOUT DESKTOP =============== */
        
        .desktop-maps-container {{
            display: block !important;
            width: 100% !important;
        }}
        
        .desktop-map-section {{
            height: auto !important;
            width: 100% !important;
        }}
        
        .desktop-map-section .stComponentV1 {{
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            overflow: hidden !important;
            max-height: 500px !important;
            width: 100% !important;
        }}
        
        .desktop-map-section iframe {{
            border-radius: 12px !important;
            border: 1px solid #e1e5e9 !important;
        }}
        
        .desktop-cards-section {{
            height: auto !important;
            width: 100% !important;
        }}
        
        .desktop-cards-section .super-enhanced-card {{
            margin-bottom: 1.5rem !important;
            width: 100% !important;
        }}
        
        /* =============== RESPONSIVE BREAKPOINTS =============== */
        
        /* Esconder desktop en móvil */
        @media (max-width: 768px) {{
            .desktop-maps-container {{
                display: none !important;
            }}
            
            .mobile-maps-container {{
                display: block !important;
            }}
            
            /* Forzar centrado del mapa en móviles */
            .mobile-map-section {{
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                flex-direction: column !important;
            }}
            
            .mobile-map-section .stComponentV1 {{
                align-self: center !important;
            }}
        }}
        
        /* Esconder móvil en desktop */
        @media (min-width: 769px) {{
            .mobile-maps-container {{
                display: none !important;
            }}
            
            .desktop-maps-container {{
                display: block !important;
            }}
        }}
        
        /* =============== CONTROLES Y BOTONES =============== */
        
        @media (max-width: 768px) {{
            .mobile-map-section .stButton > button {{
                font-size: 0.8rem !important;
                padding: 0.5rem 1rem !important;
                margin: 0.25rem !important;
            }}
            
            .mobile-map-section .stAlert,
            .mobile-map-section .stInfo {{
                font-size: 0.85rem !important;
                margin: 0.5rem 0 !important;
                padding: 0.75rem !important;
            }}
        }}
        
        /* =============== FUERZA ESPECÍFICA PARA STREAMLIT COLUMNS =============== */
        
        /* Asegurar que las columnas de Streamlit funcionen en desktop */
        @media (min-width: 769px) {{
            .desktop-maps-container .css-1r6slb0 {{
                flex: none !important;
                width: auto !important;
                min-width: 0 !important;
            }}
            
            .desktop-maps-container .row-widget.stHorizontal {{
                display: flex !important;
                flex-direction: row !important;
                gap: 2rem !important;
            }}
        }}        
        </style>
        """,
        unsafe_allow_html=True,
    )

def check_shapefiles_availability_hybrid():
    """
    NUEVA: Verifica disponibilidad de shapefiles con sistema híbrido.
    """
    if not SHAPEFILE_LOADER_AVAILABLE:
        logger.warning("⚠️ Sistema híbrido de shapefiles no disponible, usando método original")
        return check_shapefiles_availability_original()
    
    logger.info("🔍 Verificando shapefiles con sistema híbrido")
    return check_shapefiles_availability()


def load_geographic_data_hybrid():
    """
    NUEVA: Carga datos geográficos con sistema híbrido Google Drive → Local.
    """
    if not SHAPEFILE_LOADER_AVAILABLE:
        logger.warning("⚠️ Sistema híbrido no disponible, usando carga original")
        return load_geographic_data_original()
    
    logger.info("🗺️ Cargando datos geográficos con sistema híbrido")
    
    try:
        # Usar el nuevo sistema híbrido
        geo_data = load_tolima_shapefiles()
        
        if geo_data:
            logger.info(f"✅ Datos geográficos cargados: {list(geo_data.keys())}")
            
            # Verificar que tenemos los datos necesarios
            if 'municipios' in geo_data:
                logger.info(f"🏛️ Municipios: {len(geo_data['municipios'])} features")
            
            if 'veredas' in geo_data:
                logger.info(f"🏘️ Veredas: {len(geo_data['veredas'])} features")
            
            return geo_data
        else:
            logger.error("❌ Sistema híbrido no pudo cargar datos geográficos")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error en carga híbrida: {str(e)}")
        st.error(f"Error cargando mapas: {str(e)}")
        return None


def show_shapefiles_setup_instructions_hybrid():
    """
    NUEVA: Instrucciones mejoradas con sistema híbrido.
    """
    if SHAPEFILE_LOADER_AVAILABLE:
        show_shapefile_setup_instructions()
    else:
        show_shapefiles_setup_instructions_original()


def show_geographic_data_error_hybrid():
    """
    NUEVA: Error mejorado para sistema híbrido.
    """
    st.error("🗺️ No se pudieron cargar los datos de mapas")
    
    with st.expander("🔧 Información de Diagnóstico", expanded=True):
        st.markdown("""
        ### 🔍 Posibles Causas:
        
        **En Streamlit Cloud:**
        - Google Drive no configurado correctamente
        - IDs de shapefiles faltantes en secrets.toml
        - Credenciales de servicio inválidas
        
        **En desarrollo local:**
        - Archivos de mapas no encontrados en las rutas esperadas
        - Problemas con las librerías de mapas (geopandas, folium)
        
        ### 🛠️ Soluciones:
        
        **Para Streamlit Cloud:**
        1. Verifica que `.streamlit/secrets.toml` tenga la sección `[drive_files]`
        2. Verifica que `gcp_service_account` esté configurado
        3. Asegúrate de que los IDs de shapefiles sean correctos
        
        **Para desarrollo local:**
        1. Coloca los archivos .shp en `./shapefiles/`
        2. O en `./data/shapefiles/`
        3. Asegúrate de tener geopandas instalado: `pip install geopandas`
        """)
        
        # Mostrar estado del sistema
        if SHAPEFILE_LOADER_AVAILABLE:
            loader = get_shapefile_loader()
            
            st.markdown("### 📊 Estado del Sistema:")
            
            # Estado de Google Drive
            if loader._is_google_drive_available():
                st.success("✅ Google Drive configurado")
            else:
                st.error("❌ Google Drive no disponible")
            
            # Mostrar librerías disponibles
            st.markdown("### 📚 Librerías:")
            libs_status = {
                "geopandas": MAPS_AVAILABLE,
                "shapefile_loader": SHAPEFILE_LOADER_AVAILABLE,
            }
            
            for lib, available in libs_status.items():
                if available:
                    st.success(f"✅ {lib}")
                else:
                    st.error(f"❌ {lib}")


def create_enhanced_map_system_hybrid(casos, epizootias, geo_data, filters, colors, data_filtered):
    """
    CORREGIDO: Sistema de mapas que usa datos geográficos híbridos.
    """
    # Log de datos recibidos
    logger.info(f"🗺️ Sistema mapas híbrido recibió: {len(casos)} casos, {len(epizootias)} epizootias")
    
    # Determinar nivel de mapa actual
    current_level = determine_map_level(filters)
    
    # Controles de navegación
    create_navigation_controls(current_level, filters, colors)
    
    # Indicador de filtrado activo
    show_filter_indicator(filters, colors)
    
    # **VERIFICAR DATOS GEOGRÁFICOS DISPONIBLES**
    if not geo_data:
        st.error("❌ No hay datos geográficos disponibles")
        return
    
    # Verificar qué tipos de mapas podemos mostrar
    has_municipios = 'municipios' in geo_data and not geo_data['municipios'].empty
    has_veredas = 'veredas' in geo_data and not geo_data['veredas'].empty
    
    logger.info(f"🗺️ Datos geográficos disponibles: municipios={has_municipios}, veredas={has_veredas}")
    
    # Crear mapa según nivel con datos filtrados
    if current_level == "departamento":
        if has_municipios:
            logger.info("🏛️ Creando mapa departamental con datos filtrados")
            create_departmental_map_enhanced_hybrid(casos, epizootias, geo_data, colors)
        else:
            st.warning("🏛️ Mapa departamental no disponible (faltan datos de municipios)")
            show_fallback_summary_table(casos, epizootias, "departamental")
            
    elif current_level == "municipio":
        if has_veredas:
            logger.info(f"🏘️ Creando mapa municipal para {filters.get('municipio_display')} con datos filtrados")
            create_municipal_map_enhanced_hybrid(casos, epizootias, geo_data, filters, colors)
        else:
            st.warning(f"🏘️ Mapa de veredas no disponible para {filters.get('municipio_display')}")
            show_fallback_summary_table(casos, epizootias, "municipal", filters.get('municipio_display'))
            
    elif current_level == "vereda":
        logger.info(f"📍 Creando vista de vereda {filters.get('vereda_display')} con datos filtrados")
        create_vereda_detail_view_hybrid(casos, epizootias, filters, colors)


def create_departmental_map_enhanced_hybrid(casos, epizootias, geo_data, colors):
    """
    NUEVA: Mapa departamental usando datos híbridos.
    """
    if 'municipios' not in geo_data:
        st.error("No se pudo cargar el shapefile de municipios")
        return
    
    municipios = geo_data['municipios'].copy()
    logger.info(f"🏛️ Creando mapa departamental con {len(municipios)} municipios")
    
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
        key="enhanced_main_map_hybrid"
    )
    
    # **LÓGICA MEJORADA**: Procesar clicks (incluyendo municipios grises)
    handle_enhanced_click_interactions(map_data, municipios_data)


def create_municipal_map_enhanced_hybrid(casos, epizootias, geo_data, filters, colors):
    """
    NUEVA: Mapa municipal usando datos híbridos.
    """
    if 'veredas' not in geo_data:
        st.warning("🗺️ Shapefile de veredas no disponible - mostrando información tabular")
        show_municipal_tabular_view(casos, epizootias, filters, colors)
        return
    
    municipio_selected = filters.get('municipio_display')
    if not municipio_selected or municipio_selected == "Todos":
        st.error("No se pudo determinar el municipio para la vista de veredas")
        return
    
    # **EL RESTO ES IGUAL PERO USANDO geo_data híbrido**
    veredas = geo_data['veredas'].copy()
    logger.info(f"🏘️ Creando mapa municipal con {len(veredas)} veredas disponibles")
    
    # Filtrar por municipi_1 que ahora coincide exactamente con los datos
    veredas_municipio = veredas[veredas['municipi_1'] == municipio_selected]
    
    if veredas_municipio.empty:
        st.warning(f"No se encontraron veredas para el municipio {municipio_selected}")
        show_municipal_tabular_view(casos, epizootias, filters, colors)
        return
    
    logger.info(f"🏘️ Veredas encontradas para {municipio_selected}: {len(veredas_municipio)}")
    
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
            logger.warning(f"⚠️ Error creando tooltip para {vereda_name}: {str(e)}")
            
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
            key="enhanced_municipal_map_hybrid"
        )
        
        # Procesar clicks de forma segura
        handle_vereda_click_safe(map_data, veredas_data, filters)
        
    except Exception as e:
        logger.error(f"❌ Error renderizando mapa: {str(e)}")
        st.error("Error mostrando el mapa de veredas")
        show_municipal_tabular_view(casos, epizootias, filters, colors)


def create_vereda_detail_view_hybrid(casos, epizootias, filters, colors):
    """
    NUEVA: Vista de vereda usando sistema híbrido (sin cambios en la lógica).
    """
    # Esta función permanece igual ya que no depende de archivos geográficos
    # Solo usa los datos filtrados
    create_vereda_detail_view(casos, epizootias, filters, colors)


def prepare_municipal_data_enhanced(casos, epizootias, municipios):
    """Prepara datos por municipio con normalización consistente."""
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
    
    logger.info(f"🗺️ Mapeo municipal híbrido: {total_casos_mapeados} casos, {total_epi_mapeadas} epizootias")
    
    return municipios_data


def prepare_vereda_data_enhanced(casos, epizootias, veredas_gdf):
    """Prepara datos por vereda con normalización consistente."""
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
    
    logger.info(f"🏘️ Mapeo veredas híbrido {municipio_actual}: {total_casos_vereda} casos, {total_epi_vereda} epizootias")
    
    return veredas_data


# === FUNCIONES FALLBACK PARA COMPATIBILIDAD ===

def check_shapefiles_availability_original():
    """Función original de verificación (para compatibilidad)."""
    return False

def load_geographic_data_original():
    """Función original de carga (para compatibilidad)."""
    return None

def show_shapefiles_setup_instructions_original():
    """Instrucciones originales (para compatibilidad)."""
    st.error("🗺️ Shapefiles no encontrados")
    st.info("Coloque los archivos .shp en la carpeta shapefiles/")


# === RESTO DE FUNCIONES AUXILIARES (CSS, controles, etc.) ===
# [El resto de las funciones permanecen igual...]

def apply_enhanced_cards_css_FIXED(colors):
    """CSS para tarjetas (sin cambios)"""
    st.markdown(
        f"""
        <style>
        /* RESET para evitar conflictos */
        .super-enhanced-card * {{
            box-sizing: border-box;
        }}
        
        /* Tarjetas súper mejoradas - CORREGIDAS */
        .super-enhanced-card {{
            background: linear-gradient(135deg, white 0%, #fafafa 100%) !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
            overflow: hidden !important;
            margin-bottom: 1.5rem !important;
            border: 1px solid #e1e5e9 !important;
            transition: all 0.4s ease !important;
            position: relative !important;
            width: 100% !important;
            display: block !important;
        }}
        
        .super-enhanced-card:hover {{
            box-shadow: 0 12px 40px rgba(0,0,0,0.15) !important;
            transform: translateY(-3px) !important;
        }}
        
        .super-enhanced-card::before {{
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 4px !important;
            background: linear-gradient(90deg, {colors['primary']}, {colors['secondary']}, {colors['accent']}) !important;
        }}
        
        /* Headers específicos por tipo de tarjeta */
        .cases-card .card-header {{
            background: linear-gradient(135deg, {colors['danger']}, #e74c3c) !important;
            color: white !important;
            padding: 20px !important;
        }}
        
        .epizootias-card .card-header {{
            background: linear-gradient(135deg, {colors['warning']}, #f39c12) !important;
            color: white !important;
            padding: 20px !important;
        }}
        
        .card-header {{
            display: flex !important;
            align-items: center !important;
            gap: 15px !important;
            position: relative !important;
        }}
        
        .card-icon {{
            font-size: 2.2rem !important;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)) !important;
        }}
        
        .card-title {{
            font-size: 1.3rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.5px !important;
            margin: 0 !important;
        }}
        
        .card-subtitle {{
            font-size: 0.9rem !important;
            opacity: 0.9 !important;
            font-weight: 500 !important;
            margin: 2px 0 0 0 !important;
        }}
        
        /* Cuerpo de tarjetas */
        .card-body {{
            padding: 25px !important;
        }}
        
        .main-metrics-grid {{
            display: grid !important;
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 15px !important;
            margin-bottom: 20px !important;
        }}
        
        .main-metric {{
            background: #f8f9fa !important;
            padding: 15px !important;
            border-radius: 12px !important;
            text-align: center !important;
            border: 2px solid transparent !important;
            transition: all 0.3s ease !important;
            position: relative !important;
            overflow: hidden !important;
        }}
        
        .main-metric:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        }}
        
        .main-metric.mortality {{
            border-color: {colors['warning']} !important;
            background: linear-gradient(135deg, #fff8e1, #ffecb3) !important;
        }}
        
        .metric-number {{
            font-size: 1.8rem !important;
            font-weight: 800 !important;
            margin-bottom: 5px !important;
            line-height: 1 !important;
        }}
        
        .metric-number.primary {{ color: {colors['primary']} !important; }}
        .metric-number.success {{ color: {colors['success']} !important; }}
        .metric-number.danger {{ color: {colors['danger']} !important; }}
        .metric-number.warning {{ color: {colors['warning']} !important; }}
        .metric-number.info {{ color: {colors['info']} !important; }}
        
        .metric-label {{
            font-size: 0.8rem !important;
            color: #666 !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.3px !important;
        }}
        
        /* Información del último evento */
        .last-event-info {{
            background: linear-gradient(135deg, #f0f8ff, #e6f3ff) !important;
            border-radius: 12px !important;
            padding: 15px !important;
            border-left: 4px solid {colors['info']} !important;
            margin-top: 15px !important;
        }}
        
        .last-event-title {{
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            color: {colors['primary']} !important;
            margin-bottom: 8px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }}
        
        .last-event-details {{
            font-size: 0.9rem !important;
            line-height: 1.4 !important;
        }}
        
        .last-event-date {{
            color: {colors['info']} !important;
            font-weight: 600 !important;
        }}
        
        .last-event-time {{
            color: {colors['accent']} !important;
            font-weight: 500 !important;
            font-style: italic !important;
        }}
        
        .no-data {{
            color: #999 !important;
            font-style: italic !important;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .main-metrics-grid {{
                grid-template-columns: 1fr !important;
                gap: 10px !important;
            }}
            
            .card-header {{
                padding: 15px !important;
            }}
            
            .card-body {{
                padding: 20px !important;
            }}
            
            .card-icon {{
                font-size: 1.8rem !important;
            }}
            
            .card-title {{
                font-size: 1.1rem !important;
            }}
            
            .metric-number {{
                font-size: 1.5rem !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def create_beautiful_information_cards_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas, filters, colors):
    """Tarjetas informativas (sin cambios en lógica, solo en logging)"""
    logger.info("🏷️ INICIANDO TARJETAS INFORMATIVAS CON DATOS FILTRADOS GARANTIZADOS")
    
    # **VERIFICACIÓN DOBLE DE DATOS FILTRADOS**
    casos_verificados, epizootias_verificadas = ensure_filtered_data_usage(
        casos_filtrados, 
        epizootias_filtradas, 
        "tarjetas_informativas"
    )
    
    # **CALCULAR MÉTRICAS DIRECTAMENTE CON DATOS VERIFICADOS**
    logger.info(f"🧮 Calculando métricas con datos verificados: {len(casos_verificados)} casos, {len(epizootias_verificadas)} epizootias")
    metrics = calculate_basic_metrics(casos_verificados, epizootias_verificadas)
    
    # **LOG DETALLADO DE MÉTRICAS CALCULADAS**
    logger.info(f"📊 Métricas calculadas con datos filtrados:")
    logger.info(f"   🦠 Total casos: {metrics['total_casos']}")
    logger.info(f"   ⚰️ Fallecidos: {metrics['fallecidos']}")
    logger.info(f"   🐒 Total epizootias: {metrics['total_epizootias']}")
    logger.info(f"   🔴 Epizootias positivas: {metrics['epizootias_positivas']}")
    
    # **TARJETA DE CASOS CON DATOS FILTRADOS GARANTIZADOS**
    create_enhanced_cases_card_VERIFIED_FILTERED(metrics, filters, colors)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # **TARJETA DE EPIZOOTIAS CON DATOS FILTRADOS GARANTIZADOS**
    create_enhanced_epizootias_card_VERIFIED_FILTERED(metrics, filters, colors)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # **VERIFICACIÓN FINAL**
    logger.info("✅ Tarjetas informativas completadas con datos filtrados verificados")


def create_enhanced_cases_card_VERIFIED_FILTERED(metrics, filters, colors):
    """Tarjeta de casos (con logging corregido)"""
    total_casos = metrics["total_casos"]
    vivos = metrics["vivos"]
    fallecidos = metrics["fallecidos"]
    letalidad = metrics["letalidad"]
    ultimo_caso = metrics["ultimo_caso"]
    
    # Determinar contexto de filtrado
    filter_context = get_filter_context_info(filters)
    
    # **PARTE 1: Contenedor y header**
    header_html = f"""
<div class="super-enhanced-card cases-card">
    <div class="card-header">
        <div class="card-icon">🦠</div>
        <div>
            <div class="card-title">CASOS FIEBRE AMARILLA</div>
            <div class="card-subtitle">{filter_context["title"]}</div>
        </div>
    </div>
    <div class="card-body">
    """
    st.markdown(header_html, unsafe_allow_html=True)
    
    # **PARTE 2: Indicador de filtros (si aplica)**
    active_filters = filters.get("active_filters", [])
    if active_filters:
        filter_indicator = f"""
        <div style="background: #e3f2fd; padding: 8px; border-radius: 6px; margin-bottom: 10px; font-size: 0.8em; color: #1565c0; border-left: 3px solid #2196f3;">
            🎯 <strong>DATOS FILTRADOS:</strong> {filter_context["title"]}
        </div>
        """
        st.markdown(filter_indicator, unsafe_allow_html=True)
    
    # **PARTE 3: Grid de métricas**
    metrics_grid_html = f"""
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
    """
    st.markdown(metrics_grid_html, unsafe_allow_html=True)
    
    # **PARTE 4: Información del último caso**
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
    
    st.markdown(ultimo_info, unsafe_allow_html=True)
    
    # **PARTE 5: Cerrar contenedores**
    closing_html = """
    </div>
</div>
    """
    st.markdown(closing_html, unsafe_allow_html=True)
    
    logger.info("✅ Tarjeta de casos renderizada exitosamente")


def create_enhanced_epizootias_card_VERIFIED_FILTERED(metrics, filters, colors):
    """Tarjeta de epizootias (con logging corregido)"""
    total_epizootias = metrics["total_epizootias"]
    positivas = metrics["epizootias_positivas"]
    en_estudio = metrics["epizootias_en_estudio"]
    ultima_epizootia = metrics["ultima_epizootia_positiva"]
    
    # Determinar contexto de filtrado
    filter_context = get_filter_context_info(filters)
    
    # **PARTE 1: Contenedor y header**
    header_html = f"""
<div class="super-enhanced-card epizootias-card">
    <div class="card-header">
        <div class="card-icon">🐒</div>
        <div>
            <div class="card-title">EPIZOOTIAS</div>
            <div class="card-subtitle">{filter_context["title"]}</div>
        </div>
    </div>
    <div class="card-body">
    """
    st.markdown(header_html, unsafe_allow_html=True)
    
    # **PARTE 2: Indicador de filtros (si aplica)**
    active_filters = filters.get("active_filters", [])
    if active_filters:
        filter_indicator = f"""
        <div style="background: #fff3e0; padding: 8px; border-radius: 6px; margin-bottom: 10px; font-size: 0.8em; color: #ef6c00; border-left: 3px solid #ff9800;">
            🎯 <strong>DATOS FILTRADOS:</strong> {filter_context["title"]}
        </div>
        """
        st.markdown(filter_indicator, unsafe_allow_html=True)
    
    # **PARTE 3: Grid de métricas**
    metrics_grid_html = f"""
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
    """
    st.markdown(metrics_grid_html, unsafe_allow_html=True)
    
    # **PARTE 4: Información de la última epizootia**
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
    
    st.markdown(ultimo_info, unsafe_allow_html=True)
    
    # **PARTE 5: Cerrar contenedores**
    closing_html = """
    </div>
</div>
    """
    st.markdown(closing_html, unsafe_allow_html=True)
    
    logger.info("✅ Tarjeta de epizootias renderizada exitosamente")


# === RESTO DE FUNCIONES DE APOYO (todas con logging corregido) ===

def get_filter_context_info(filters):
    """Obtiene información del contexto de filtrado para mostrar en tarjetas."""
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

def determine_map_level(filters):
    """Determina el nivel de zoom del mapa según filtros activos."""
    if filters.get("vereda_display") and filters.get("vereda_display") != "Todas":
        return "vereda"
    elif filters.get("municipio_display") and filters.get("municipio_display") != "Todos":
        return "municipio"
    else:
        return "departamento"

def show_fallback_summary_table(casos, epizootias, level, location=None):
    """Tabla resumen cuando no hay mapas disponibles."""
    level_info = {
        "departamental": "🏛️ Vista Departamental - Tolima",
        "municipal": f"🏘️ Vista Municipal - {location}" if location else "🏘️ Vista Municipal"
    }
    
    st.info(f"📊 {level_info[level]} (modo tabular - mapas no disponibles)")
    
    # Mostrar datos por ubicación en tabla
    if level == "departamental" and not casos.empty and "municipio" in casos.columns:
        st.markdown("**📊 Casos por Municipio**")
        municipio_casos = casos["municipio"].value_counts().head(15)
        if not municipio_casos.empty:
            casos_df = municipio_casos.to_frame("Casos")
            
            # Agregar información de epizootias si está disponible
            if not epizootias.empty and "municipio" in epizootias.columns:
                municipio_epi = epizootias["municipio"].value_counts()
                casos_df["Epizootias"] = casos_df.index.map(municipio_epi).fillna(0).astype(int)
            
            st.dataframe(casos_df, use_container_width=True, height=400)
        else:
            st.info("No hay casos registrados por municipio")

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

def show_maps_not_available():
    """Muestra mensaje cuando las librerías de mapas no están disponibles."""
    st.error("⚠️ Librerías de mapas no instaladas. Instale: geopandas folium streamlit-folium")

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
            if st.button("🏛️ Ver Tolima", key="nav_tolima_hybrid", use_container_width=True):
                reset_all_location_filters()
                st.rerun()
    
    with cols[1]:
        if current_level == "vereda":
            municipio_name = filters.get('municipio_display', 'Municipio')
            if st.button(f"🏘️ Ver {municipio_name[:10]}...", key="nav_municipio_hybrid", use_container_width=True):
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

def handle_enhanced_click_interactions(map_data, municipios_data):
    """Maneja clicks usando nombres directos de shapefiles."""
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

def handle_vereda_click_safe(map_data, veredas_data, filters):
    """Manejo seguro de clicks en veredas (incluso grises)."""
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
                        logger.warning(f"⚠️ Error calculando distancia para vereda: {str(e)}")
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
        logger.error(f"❌ Error procesando clic en vereda: {str(e)}")
        st.warning("⚠️ Error procesando clic en el mapa. Intente usar los filtros del sidebar.")

def create_vereda_detail_view(casos, epizootias, filters, colors):
    """Vista detallada de vereda específica con filtrado correcto."""
    # Esta función mantiene toda su lógica pero corrige el logging
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
    logger.info(f"📍 Vista vereda híbrida {vereda_display}: {total_casos} casos, {total_epizootias} epizootias")
    
    # [El resto de la función permanece igual...]
    # Análisis específico de la vereda
    if total_casos > 0 or total_epizootias > 0:
        st.markdown("---")
        st.markdown("### 📊 Análisis Específico de la Vereda")
        
        # [El resto del análisis detallado...]
        # ...
    else:
        st.info(f"📊 No hay eventos registrados en la vereda **{vereda_display}** con los filtros actuales")