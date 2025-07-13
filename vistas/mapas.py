"""
Vista de mapas.
"""

import streamlit as st
import pandas as pd
import logging

# Configurar logger CORREGIDO
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
    verify_filtered_data_usage,
    debug_data_flow
)

# Sistema híbrido de shapefiles
try:
    from utils.shapefile_loader import (
        load_tolima_shapefiles,
        check_shapefiles_availability,
        show_shapefile_setup_instructions
    )
    SHAPEFILE_LOADER_AVAILABLE = True
except ImportError:
    SHAPEFILE_LOADER_AVAILABLE = False

# ===== FUNCIÓN PRINCIPAL =====

def show(data_filtered, filters, colors):
    """Vista principal de mapas OPTIMIZADA."""
    logger.info("🗺️ INICIANDO VISTA DE MAPAS OPTIMIZADA")
    
    # Aplicar CSS UNA SOLA VEZ
    apply_maps_css_optimized(colors)
    
    # Verificar datos filtrados
    casos_filtrados = data_filtered["casos"]
    epizootias_filtradas = data_filtered["epizootias"]
    
    verify_filtered_data_usage(casos_filtrados, "vista_mapas - casos")
    verify_filtered_data_usage(epizootias_filtradas, "vista_mapas - epizootias")
    
    debug_data_flow(data_filtered, data_filtered, filters, "VISTA_MAPAS_OPTIMIZADA")

    # Verificaciones básicas
    if not MAPS_AVAILABLE:
        show_maps_not_available()
        return

    if not check_shapefiles_availability():
        show_shapefile_setup_instructions()
        return

    # Cargar datos geográficos
    geo_data = load_geographic_data()
    if not geo_data:
        show_geographic_data_error()
        return

    # Información de filtrado
    active_filters = filters.get("active_filters", [])
    if active_filters:
        st.info(f"🎯 Mostrando datos filtrados: {' • '.join(active_filters[:2])}")

    # Layout responsive
    device_type = detect_device_type()
    
    if device_type == "mobile":
        create_mobile_layout_optimized(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered)
    else:
        create_desktop_layout_optimized(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered)

# ===== FUNCIONES DE LAYOUT =====

def create_mobile_layout_optimized(casos, epizootias, geo_data, filters, colors, data_filtered):
    """Layout móvil optimizado."""
    st.markdown('<div class="mobile-maps-container">', unsafe_allow_html=True)
    
    # Mapa móvil
    st.markdown('<div class="mobile-map-section">', unsafe_allow_html=True)
    st.caption("📱 Vista móvil - Mapa responsive centrado")
    
    create_map_system_optimized(casos, epizootias, geo_data, filters, colors, "mobile")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tarjetas informativas
    st.markdown('<div class="mobile-cards-section">', unsafe_allow_html=True)
    create_information_cards_optimized(casos, epizootias, filters, colors)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_desktop_layout_optimized(casos, epizootias, geo_data, filters, colors, data_filtered):
    """Layout desktop optimizado."""
    st.markdown('<div class="desktop-maps-container">', unsafe_allow_html=True)
    
    col_mapa, col_tarjetas = st.columns([3, 2], gap="large")
    
    with col_mapa:
        st.markdown('<div class="desktop-map-section">', unsafe_allow_html=True)
        create_map_system_optimized(casos, epizootias, geo_data, filters, colors, "desktop")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_tarjetas:
        st.markdown('<div class="desktop-cards-section">', unsafe_allow_html=True)
        create_information_cards_optimized(casos, epizootias, filters, colors)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ===== SISTEMA DE MAPAS UNIFICADO =====

def create_map_system_optimized(casos, epizootias, geo_data, filters, colors, device_type):
    """Sistema de mapas unificado y optimizado."""
    current_level = determine_map_level(filters)
    
    # Controles de navegación
    create_navigation_controls_optimized(current_level, filters, colors)
    show_filter_indicator_optimized(filters, colors)
    
    # Verificar datos geográficos
    has_municipios = 'municipios' in geo_data and not geo_data['municipios'].empty
    has_veredas = 'veredas' in geo_data and not geo_data['veredas'].empty
    
    # Crear mapa según nivel
    if current_level == "departamento" and has_municipios:
        create_departmental_map_optimized(casos, epizootias, geo_data, colors, device_type)
    elif current_level == "municipio" and has_veredas:
        create_municipal_map_optimized(casos, epizootias, geo_data, filters, colors, device_type)
    elif current_level == "vereda":
        create_vereda_detail_view_optimized(casos, epizootias, filters, colors)
    else:
        show_fallback_summary_table(casos, epizootias, current_level, filters.get('municipio_display'))

def create_departmental_map_optimized(casos, epizootias, geo_data, colors, device_type):
    """Mapa departamental optimizado."""
    municipios = geo_data['municipios'].copy()
    logger.info(f"🏛️ Creando mapa departamental con {len(municipios)} municipios")
    
    # Preparar datos
    municipios_data = prepare_municipal_data_optimized(casos, epizootias, municipios)
    
    # Configuración del mapa
    bounds = municipios.total_bounds
    center_lat, center_lon = (bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2
    
    # Configuración según dispositivo
    map_config = get_map_config_by_device(device_type, center_lat, center_lon)
    m = folium.Map(**map_config)
    
    # Aplicar límites
    apply_map_bounds(m, bounds)
    
    # Agregar municipios
    add_municipios_to_map(m, municipios_data, colors)
    
    # Renderizar
    map_data = st_folium(
        m, 
        width=get_map_width_by_device(device_type),
        height=get_map_height_by_device(device_type),
        returned_objects=["last_object_clicked"],
        key=f"map_departamental_{device_type}"
    )
    
    # Procesar clicks
    handle_map_click_optimized(map_data, municipios_data, "municipio")

def create_municipal_map_optimized(casos, epizootias, geo_data, filters, colors, device_type):
    """Mapa municipal optimizado."""
    municipio_selected = filters.get('municipio_display')
    if not municipio_selected or municipio_selected == "Todos":
        st.error("No se pudo determinar el municipio para la vista de veredas")
        return
    
    veredas = geo_data['veredas'].copy()
    veredas_municipio = veredas[veredas['municipi_1'] == municipio_selected]
    
    if veredas_municipio.empty:
        st.warning(f"No se encontraron veredas para {municipio_selected}")
        show_municipal_tabular_view(casos, epizootias, filters, colors)
        return
    
    # Preparar datos
    veredas_data = prepare_vereda_data_optimized(casos, epizootias, veredas_municipio, municipio_selected)
    
    # Crear mapa
    bounds = veredas_municipio.total_bounds
    center_lat, center_lon = (bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2
    
    map_config = get_map_config_by_device(device_type, center_lat, center_lon, zoom=10)
    m = folium.Map(**map_config)
    
    # Aplicar límites y agregar veredas
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    add_veredas_to_map(m, veredas_data, colors)
    
    # Renderizar
    map_data = st_folium(
        m, 
        width=get_map_width_by_device(device_type),
        height=get_map_height_by_device(device_type),
        returned_objects=["last_object_clicked"],
        key=f"map_municipal_{device_type}"
    )
    
    # Procesar clicks
    handle_map_click_optimized(map_data, veredas_data, "vereda")

# ===== FUNCIONES DE PREPARACIÓN DE DATOS =====

def prepare_municipal_data_optimized(casos, epizootias, municipios):
    """Prepara datos municipales de forma optimizada."""
    def normalize_name(name):
        if pd.isna(name) or name == "":
            return ""
        return str(name).upper().strip()
    
    # Normalizar
    municipios = municipios.copy()
    municipios['municipi_1_norm'] = municipios['municipi_1'].apply(normalize_name)
    
    # Contar casos
    casos_por_municipio = {}
    fallecidos_por_municipio = {}
    
    if not casos.empty and 'municipio' in casos.columns:
        casos_norm = casos.copy()
        casos_norm['municipio_norm'] = casos_norm['municipio'].apply(normalize_name)
        
        casos_counts = casos_norm.groupby('municipio_norm').size()
        casos_por_municipio = casos_counts.to_dict()
        
        if 'condicion_final' in casos_norm.columns:
            fallecidos_norm = casos_norm[casos_norm['condicion_final'] == 'Fallecido']
            fallecidos_counts = fallecidos_norm.groupby('municipio_norm').size()
            fallecidos_por_municipio = fallecidos_counts.to_dict()
    
    # Contar epizootias
    epizootias_por_municipio = {}
    positivas_por_municipio = {}
    
    if not epizootias.empty and 'municipio' in epizootias.columns:
        epizootias_norm = epizootias.copy()
        epizootias_norm['municipio_norm'] = epizootias_norm['municipio'].apply(normalize_name)
        
        epi_counts = epizootias_norm.groupby('municipio_norm').size()
        epizootias_por_municipio = epi_counts.to_dict()
        
        if 'descripcion' in epizootias_norm.columns:
            positivas_df = epizootias_norm[epizootias_norm['descripcion'] == 'POSITIVO FA']
            if not positivas_df.empty:
                positivas_counts = positivas_df.groupby('municipio_norm').size()
                positivas_por_municipio = positivas_counts.to_dict()
    
    # Combinar datos
    municipios_data = municipios.copy()
    municipios_data['casos'] = municipios_data['municipi_1_norm'].map(casos_por_municipio).fillna(0).astype(int)
    municipios_data['fallecidos'] = municipios_data['municipi_1_norm'].map(fallecidos_por_municipio).fillna(0).astype(int)
    municipios_data['epizootias'] = municipios_data['municipi_1_norm'].map(epizootias_por_municipio).fillna(0).astype(int)
    municipios_data['epizootias_positivas'] = municipios_data['municipi_1_norm'].map(positivas_por_municipio).fillna(0).astype(int)
    
    logger.info(f"🗺️ Datos municipales preparados: {municipios_data['casos'].sum()} casos, {municipios_data['epizootias'].sum()} epizootias")
    return municipios_data

def prepare_vereda_data_optimized(casos, epizootias, veredas_gdf, municipio_actual):
    """Prepara datos de veredas de forma optimizada."""
    def normalize_name(name):
        if pd.isna(name) or name == "":
            return ""
        return str(name).upper().strip()
    
    # Normalizar
    veredas_gdf = veredas_gdf.copy()
    veredas_gdf['vereda_nor_norm'] = veredas_gdf['vereda_nor'].apply(normalize_name)
    municipio_norm = normalize_name(municipio_actual)
    
    # Preparar conteos por vereda (filtrados por municipio)
    casos_por_vereda = {}
    if not casos.empty and 'vereda' in casos.columns and 'municipio' in casos.columns:
        casos_norm = casos.copy()
        casos_norm['vereda_norm'] = casos_norm['vereda'].apply(normalize_name)
        casos_norm['municipio_norm'] = casos_norm['municipio'].apply(normalize_name)
        
        casos_municipio = casos_norm[casos_norm['municipio_norm'] == municipio_norm]
        if not casos_municipio.empty:
            casos_counts = casos_municipio.groupby('vereda_norm').size()
            casos_por_vereda = casos_counts.to_dict()
    
    epizootias_por_vereda = {}
    positivas_por_vereda = {}
    
    if not epizootias.empty and 'vereda' in epizootias.columns and 'municipio' in epizootias.columns:
        epizootias_norm = epizootias.copy()
        epizootias_norm['vereda_norm'] = epizootias_norm['vereda'].apply(normalize_name)
        epizootias_norm['municipio_norm'] = epizootias_norm['municipio'].apply(normalize_name)
        
        epi_municipio = epizootias_norm[epizootias_norm['municipio_norm'] == municipio_norm]
        if not epi_municipio.empty:
            epi_counts = epi_municipio.groupby('vereda_norm').size()
            epizootias_por_vereda = epi_counts.to_dict()
            
            if 'descripcion' in epi_municipio.columns:
                positivas_df = epi_municipio[epi_municipio['descripcion'] == 'POSITIVO FA']
                if not positivas_df.empty:
                    positivas_counts = positivas_df.groupby('vereda_norm').size()
                    positivas_por_vereda = positivas_counts.to_dict()
    
    # Combinar datos
    veredas_data = veredas_gdf.copy()
    veredas_data['casos'] = veredas_data['vereda_nor_norm'].map(casos_por_vereda).fillna(0).astype(int)
    veredas_data['epizootias'] = veredas_data['vereda_nor_norm'].map(epizootias_por_vereda).fillna(0).astype(int)
    veredas_data['epizootias_positivas'] = veredas_data['vereda_nor_norm'].map(positivas_por_vereda).fillna(0).astype(int)
    
    logger.info(f"🏘️ Datos veredas preparados {municipio_actual}: {veredas_data['casos'].sum()} casos, {veredas_data['epizootias'].sum()} epizootias")
    return veredas_data

# ===== FUNCIONES DE MAPA =====

def add_municipios_to_map(folium_map, municipios_data, colors):
    """Agrega municipios al mapa."""
    max_casos = municipios_data['casos'].max() if municipios_data['casos'].max() > 0 else 1
    max_epi = municipios_data['epizootias'].max() if municipios_data['epizootias'].max() > 0 else 1
    
    for idx, row in municipios_data.iterrows():
        municipio_name = row['MpNombre']
        casos_count = row['casos']
        epizootias_count = row['epizootias']
        
        # Color según datos
        fill_color, border_color = get_feature_colors(casos_count, epizootias_count, max_casos, max_epi, colors)
        
        # Tooltip
        tooltip_text = create_municipio_tooltip(municipio_name, casos_count, epizootias_count, colors)
        
        # Agregar polígono
        geojson = folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=fill_color, border=border_color: {
                'fillColor': color,
                'color': border,
                'weight': 2,
                'fillOpacity': 0.7,
                'opacity': 1
            },
            tooltip=folium.Tooltip(tooltip_text, sticky=True),
        )
        geojson.add_to(folium_map)

def add_veredas_to_map(folium_map, veredas_data, colors):
    """Agrega veredas al mapa."""
    max_casos = veredas_data['casos'].max() if veredas_data['casos'].max() > 0 else 1
    max_epi = veredas_data['epizootias'].max() if veredas_data['epizootias'].max() > 0 else 1
    
    for idx, row in veredas_data.iterrows():
        vereda_name = row['vereda_nor']
        casos_count = row['casos']
        epizootias_count = row['epizootias']
        
        # Color según datos
        fill_color, border_color = get_feature_colors(casos_count, epizootias_count, max_casos, max_epi, colors)
        
        # Tooltip
        tooltip_text = create_vereda_tooltip(vereda_name, casos_count, epizootias_count, colors)
        
        # Agregar polígono
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
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            )
            geojson.add_to(folium_map)
        except Exception as e:
            logger.warning(f"⚠️ Error agregando vereda {vereda_name}: {str(e)}")

# ===== FUNCIONES DE UTILIDAD =====

def get_feature_colors(casos_count, epizootias_count, max_casos, max_epi, colors):
    """Obtiene colores para features según datos."""
    if casos_count > 0:
        intensity = min(casos_count / max_casos, 1.0) if max_casos > 0 else 0
        fill_color = f"rgba(229, 25, 55, {0.4 + intensity * 0.5})"
        border_color = colors['danger']
    elif epizootias_count > 0:
        epi_intensity = min(epizootias_count / max_epi, 1.0) if max_epi > 0 else 0
        fill_color = f"rgba(247, 148, 29, {0.3 + epi_intensity * 0.4})"
        border_color = colors['warning']
    else:
        fill_color = "rgba(200, 200, 200, 0.3)"
        border_color = "#cccccc"
    
    return fill_color, border_color

def create_municipio_tooltip(name, casos, epizootias, colors):
    """Crea tooltip para municipio."""
    return f"""
    <div style="font-family: Arial; padding: 8px; max-width: 200px;">
        <b style="color: {colors['primary']};">{name}</b><br>
        🦠 Casos: {casos}<br>
        🐒 Epizootias: {epizootias}<br>
        <i style="color: {colors['info']};">👆 Clic para filtrar</i>
    </div>
    """

def create_vereda_tooltip(name, casos, epizootias, colors):
    """Crea tooltip para vereda."""
    status = "Con datos" if casos > 0 or epizootias > 0 else "Sin datos"
    return f"""
    <div style="font-family: Arial; padding: 8px; max-width: 180px;">
        <b style="color: {colors['primary']};">{name}</b><br>
        <span style="color: #666;">{status}</span><br>
        🦠 Casos: {casos}<br>
        🐒 Epizootias: {epizootias}<br>
        <i style="color: {colors['info']};">👆 Clic para filtrar</i>
    </div>
    """

def get_map_config_by_device(device_type, center_lat, center_lon, zoom=8):
    """Configuración de mapa según dispositivo."""
    base_config = {
        'location': [center_lat, center_lon],
        'zoom_start': zoom,
        'tiles': 'CartoDB positron',
        'attributionControl': False,
    }
    
    if device_type == "mobile":
        base_config.update({
            'zoom_control': True,
            'scrollWheelZoom': True,
            'doubleClickZoom': True,
            'dragging': True,
            'min_zoom': zoom - 2,
            'max_zoom': zoom
        })
    else:
        base_config.update({
            'zoom_control': False,
            'scrollWheelZoom': False,
            'doubleClickZoom': False,
            'dragging': False,
            'min_zoom': zoom,
            'max_zoom': zoom
        })
    
    return base_config

def get_map_width_by_device(device_type):
    """Ancho de mapa según dispositivo."""
    return 380 if device_type == "mobile" else 700

def get_map_height_by_device(device_type):
    """Altura de mapa según dispositivo."""
    return 400 if device_type == "mobile" else 500

def apply_map_bounds(folium_map, bounds, buffer=0.1):
    """Aplica límites al mapa."""
    bounds_with_buffer = [
        [bounds[1] - buffer, bounds[0] - buffer],
        [bounds[3] + buffer, bounds[2] + buffer]
    ]
    folium_map.fit_bounds(bounds_with_buffer)
    folium_map.options['maxBounds'] = bounds_with_buffer

# ===== MANEJO DE INTERACCIONES =====

def handle_map_click_optimized(map_data, features_data, feature_type):
    """Manejo optimizado de clicks en mapa."""
    if not map_data or not map_data.get('last_object_clicked'):
        return
    
    try:
        clicked_object = map_data['last_object_clicked']
        
        if isinstance(clicked_object, dict):
            clicked_lat = clicked_object.get('lat')
            clicked_lng = clicked_object.get('lng')
            
            if clicked_lat and clicked_lng:
                feature_clicked = find_closest_feature(clicked_lat, clicked_lng, features_data, feature_type)
                
                if feature_clicked:
                    apply_feature_filter(feature_clicked, feature_type)
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"❌ Error procesando clic: {str(e)}")
        st.warning("⚠️ Error procesando clic en el mapa")

def find_closest_feature(lat, lng, features_data, feature_type):
    """Encuentra el feature más cercano al punto clicado."""
    min_distance = float('inf')
    closest_feature = None
    
    name_column = 'municipi_1' if feature_type == 'municipio' else 'vereda_nor'
    
    for idx, row in features_data.iterrows():
        try:
            centroid = row['geometry'].centroid
            distance = ((centroid.x - lng)**2 + (centroid.y - lat)**2)**0.5
            
            if distance < min_distance and distance < 0.1:
                min_distance = distance
                closest_feature = row[name_column]
        except Exception:
            continue
    
    return closest_feature

def apply_feature_filter(feature_name, feature_type):
    """Aplica filtro según el tipo de feature."""
    if feature_type == "municipio":
        st.session_state['municipio_filter'] = feature_name
        st.session_state['vereda_filter'] = 'Todas'
        st.success(f"✅ Filtrado por municipio: **{feature_name}**")
    elif feature_type == "vereda":
        st.session_state['vereda_filter'] = feature_name
        st.success(f"✅ Filtrado por vereda: **{feature_name}**")

# ===== CONTROLES Y NAVEGACIÓN =====

def create_navigation_controls_optimized(current_level, filters, colors):
    """Controles de navegación optimizados."""
    level_info = {
        "departamento": "🏛️ Tolima",
        "municipio": f"🏘️ {filters.get('municipio_display', 'Municipio')}",
        "vereda": f"📍 {filters.get('vereda_display', 'Vereda')}"
    }
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if current_level != "departamento":
            if st.button("🏛️ Ver Tolima", key="nav_tolima_opt", use_container_width=True):
                reset_location_filters()
                st.rerun()
    
    with col2:
        if current_level == "vereda":
            municipio_name = filters.get('municipio_display', 'Municipio')
            if st.button(f"🏘️ Ver {municipio_name[:10]}...", key="nav_municipio_opt", use_container_width=True):
                st.session_state['vereda_filter'] = 'Todas'
                st.rerun()

def show_filter_indicator_optimized(filters, colors):
    """Indicador de filtros activos optimizado."""
    active_filters = filters.get("active_filters", [])
    
    if active_filters:
        filters_text = " • ".join(active_filters[:2])
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
            ">
                🎯 FILTROS: {filters_text}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ===== TARJETAS INFORMATIVAS =====

def create_information_cards_optimized(casos, epizootias, filters, colors):
    """Tarjetas informativas optimizadas."""
    logger.info("🏷️ Creando tarjetas informativas optimizadas")
    
    verify_filtered_data_usage(casos, "tarjetas_informativas_opt")
    verify_filtered_data_usage(epizootias, "tarjetas_informativas_opt")
    
    metrics = calculate_basic_metrics(casos, epizootias)
    
    # Tarjeta de casos
    create_cases_card_optimized(metrics, filters, colors)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tarjeta de epizootias
    create_epizootias_card_optimized(metrics, filters, colors)

def create_cases_card_optimized(metrics, filters, colors):
    """Tarjeta de casos súper estética CORREGIDA."""
    total_casos = metrics["total_casos"]
    vivos = metrics["vivos"]
    fallecidos = metrics["fallecidos"]
    letalidad = metrics["letalidad"]
    ultimo_caso = metrics["ultimo_caso"]
    
    filter_context = get_filter_context(filters)
    
    # PARTE 1: Header de la tarjeta
    st.markdown(
        f"""
        <div class="super-enhanced-card cases-card">
            <div class="card-header">
                <div class="card-icon">🦠</div>
                <div>
                    <div class="card-title">CASOS FIEBRE AMARILLA</div>
                    <div class="card-subtitle">{filter_context}</div>
                </div>
            </div>
            <div class="card-body">
        """,
        unsafe_allow_html=True,
    )
    
    # PARTE 2: Grid de métricas
    st.markdown(
        f"""
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
                <div class="metric-label">Letalidad</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # PARTE 3: Información del último caso
    if ultimo_caso["existe"]:
        fecha_str = ultimo_caso["fecha"].strftime("%d/%m/%Y") if ultimo_caso["fecha"] else "Sin fecha"
        st.markdown(
            f"""
            <div class="last-event-info">
                <div class="last-event-title">📍 Último Caso</div>
                <div class="last-event-details">
                    <strong>{ultimo_caso["ubicacion"]}</strong><br>
                    <span class="last-event-date">{fecha_str}</span><br>
                    <span class="last-event-time">Hace {ultimo_caso["tiempo_transcurrido"]}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="last-event-info">
                <div class="last-event-title">📍 Último Caso</div>
                <div class="last-event-details">
                    <span class="no-data">Sin casos registrados</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # PARTE 4: Cerrar tarjeta
    st.markdown("</div></div>", unsafe_allow_html=True)

def create_epizootias_card_optimized(metrics, filters, colors):
    """Tarjeta de epizootias súper estética CORREGIDA."""
    total_epizootias = metrics["total_epizootias"]
    positivas = metrics["epizootias_positivas"]
    en_estudio = metrics["epizootias_en_estudio"]
    ultima_epizootia = metrics["ultima_epizootia_positiva"]
    
    filter_context = get_filter_context(filters)
    
    # PARTE 1: Header de la tarjeta
    st.markdown(
        f"""
        <div class="super-enhanced-card epizootias-card">
            <div class="card-header">
                <div class="card-icon">🐒</div>
                <div>
                    <div class="card-title">EPIZOOTIAS</div>
                    <div class="card-subtitle">{filter_context}</div>
                </div>
            </div>
            <div class="card-body">
        """,
        unsafe_allow_html=True,
    )
    
    # PARTE 2: Grid de métricas
    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True,
    )
    
    # PARTE 3: Información de la última epizootia
    if ultima_epizootia["existe"]:
        fecha_str = ultima_epizootia["fecha"].strftime("%d/%m/%Y") if ultima_epizootia["fecha"] else "Sin fecha"
        st.markdown(
            f"""
            <div class="last-event-info">
                <div class="last-event-title">🔴 Último Positivo</div>
                <div class="last-event-details">
                    <strong>{ultima_epizootia["ubicacion"]}</strong><br>
                    <span class="last-event-date">{fecha_str}</span><br>
                    <span class="last-event-time">Hace {ultima_epizootia["tiempo_transcurrido"]}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="last-event-info">
                <div class="last-event-title">🔴 Último Positivo</div>
                <div class="last-event-details">
                    <span class="no-data">Sin epizootias positivas</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # PARTE 4: Cerrar tarjeta
    st.markdown("</div></div>", unsafe_allow_html=True)

# ===== FUNCIONES DE APOYO =====

def load_geographic_data():
    """Carga datos geográficos usando sistema híbrido."""
    if not SHAPEFILE_LOADER_AVAILABLE:
        logger.warning("⚠️ Sistema híbrido no disponible")
        return None
    
    try:
        return load_tolima_shapefiles()
    except Exception as e:
        logger.error(f"❌ Error cargando datos geográficos: {str(e)}")
        return None

def detect_device_type():
    """Detecta tipo de dispositivo (simplificado)."""
    return 'responsive'

def determine_map_level(filters):
    """Determina nivel del mapa según filtros."""
    if filters.get("vereda_display") and filters.get("vereda_display") != "Todas":
        return "vereda"
    elif filters.get("municipio_display") and filters.get("municipio_display") != "Todos":
        return "municipio"
    else:
        return "departamento"

def get_filter_context(filters):
    """Obtiene contexto de filtrado."""
    municipio = filters.get("municipio_display", "Todos")
    vereda = filters.get("vereda_display", "Todas")
    
    if vereda != "Todas":
        return f"Vigilancia en {vereda}"
    elif municipio != "Todos":
        return f"Vigilancia en {municipio}"
    else:
        return "Vigilancia epidemiológica Tolima"

def reset_location_filters():
    """Resetea filtros de ubicación."""
    if "municipio_filter" in st.session_state:
        st.session_state.municipio_filter = "Todos"
    if "vereda_filter" in st.session_state:
        st.session_state.vereda_filter = "Todas"

def show_fallback_summary_table(casos, epizootias, level, location=None):
    """Tabla resumen cuando no hay mapas."""
    level_info = {
        "departamental": "🏛️ Vista Departamental - Tolima",
        "municipal": f"🏘️ Vista Municipal - {location}" if location else "🏘️ Vista Municipal"
    }
    
    st.info(f"📊 {level_info[level]} (modo tabular - mapas no disponibles)")

def show_municipal_tabular_view(casos, epizootias, filters, colors):
    """Vista tabular municipal."""
    municipio_display = filters.get('municipio_display', 'Municipio')
    st.info(f"🗺️ Vista tabular para {municipio_display} (mapa no disponible)")

def create_vereda_detail_view_optimized(casos, epizootias, filters, colors):
    """Vista detallada de vereda optimizada."""
    vereda_display = filters.get('vereda_display', 'Vereda')
    municipio_display = filters.get('municipio_display', 'Municipio')
    
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']});
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
        ">
            <h3 style="margin: 0;">📍 Vista Detallada</h3>
            <p style="margin: 10px 0 0 0;">
                <strong>{vereda_display}</strong> - {municipio_display}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Métricas de la vereda
    total_casos = len(casos)
    total_epizootias = len(epizootias)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🦠 Casos", total_casos)
    with col2:
        st.metric("🐒 Epizootias", total_epizootias)
    with col3:
        if not epizootias.empty and "descripcion" in epizootias.columns:
            positivas = len(epizootias[epizootias["descripcion"] == "POSITIVO FA"])
            st.metric("🔴 Positivas", positivas)
        else:
            st.metric("🔴 Positivas", 0)
    with col4:
        actividad_total = total_casos + total_epizootias
        st.metric("📊 Total", actividad_total)

def show_maps_not_available():
    """Mensaje cuando mapas no están disponibles."""
    st.error("⚠️ Librerías de mapas no instaladas")
    st.info("Instale: `pip install geopandas folium streamlit-folium`")

def show_geographic_data_error():
    """Error cuando no hay datos geográficos."""
    st.error("🗺️ No se pudieron cargar los datos de mapas")
    st.info("Verifique la configuración de shapefiles")

# ===== CSS SUPER ESTÉTICO CORREGIDO =====

def apply_maps_css_optimized(colors):
    """CSS súper estético corregido - UNA SOLA VEZ."""
    st.markdown(
        f"""
        <style>
        /* =============== CORRECCIÓN SCROLL INFINITO =============== */
        
        /* Contenedor principal con altura limitada */
        .main .block-container {{
            max-height: calc(100vh - 100px) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }}
        
        /* Limitar altura de elementos que pueden crecer */
        .stDataFrame > div {{
            max-height: 400px !important;
            overflow-y: auto !important;
        }}
        
        .js-plotly-plot {{
            max-height: 500px !important;
            overflow: hidden !important;
        }}
        
        /* =============== MAPAS RESPONSIVE =============== */
        .mobile-maps-container, .desktop-maps-container {{
            width: 100% !important;
            max-width: 100% !important;
            overflow: visible !important;
        }}
        
        .mobile-map-section {{
            width: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            padding: 0 15px !important;
            margin-bottom: 1.5rem !important;
            box-sizing: border-box !important;
        }}
        
        /* =============== TARJETAS SÚPER ESTÉTICAS =============== */
        
        /* RESET para evitar conflictos */
        .super-enhanced-card * {{
            box-sizing: border-box;
        }}
        
        .super-enhanced-card {{
            background: linear-gradient(135deg, white 0%, #fafafa 100%) !important;
            border-radius: 18px !important;
            box-shadow: 0 12px 40px rgba(0,0,0,0.12) !important;
            overflow: hidden !important;
            margin-bottom: 2rem !important;
            border: 2px solid #e8ecf0 !important;
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
            width: 100% !important;
            display: block !important;
        }}
        
        .super-enhanced-card:hover {{
            box-shadow: 0 20px 60px rgba(0,0,0,0.18) !important;
            transform: translateY(-8px) scale(1.02) !important;
            border-color: {colors['secondary']} !important;
        }}
        
        .super-enhanced-card::before {{
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 6px !important;
            background: linear-gradient(90deg, {colors['primary']}, {colors['secondary']}, {colors['accent']}) !important;
            box-shadow: 0 2px 8px rgba(125,15,43,0.3) !important;
        }}
        
        .super-enhanced-card::after {{
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(255,255,255,0.4)) !important;
            opacity: 0 !important;
            transition: opacity 0.3s ease !important;
            pointer-events: none !important;
        }}
        
        .super-enhanced-card:hover::after {{
            opacity: 1 !important;
        }}
        
        /* Headers específicos por tipo de tarjeta */
        .cases-card .card-header {{
            background: linear-gradient(135deg, {colors['danger']}, #e74c3c, #c0392b) !important;
            color: white !important;
            padding: 25px !important;
            position: relative !important;
            overflow: hidden !important;
        }}
        
        .cases-card .card-header::before {{
            content: '' !important;
            position: absolute !important;
            top: -50% !important;
            left: -50% !important;
            width: 200% !important;
            height: 200% !important;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%) !important;
            animation: shimmer 3s ease-in-out infinite !important;
        }}
        
        .epizootias-card .card-header {{
            background: linear-gradient(135deg, {colors['warning']}, #f39c12, #e67e22) !important;
            color: white !important;
            padding: 25px !important;
            position: relative !important;
            overflow: hidden !important;
        }}
        
        .epizootias-card .card-header::before {{
            content: '' !important;
            position: absolute !important;
            top: -50% !important;
            left: -50% !important;
            width: 200% !important;
            height: 200% !important;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%) !important;
            animation: shimmer 3s ease-in-out infinite alternate !important;
        }}
        
        @keyframes shimmer {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .card-header {{
            display: flex !important;
            align-items: center !important;
            gap: 20px !important;
            position: relative !important;
            z-index: 2 !important;
        }}
        
        .card-icon {{
            font-size: 2.8rem !important;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3)) !important;
            animation: pulse 2s ease-in-out infinite !important;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
        }}
        
        .card-title {{
            font-size: 1.4rem !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            margin: 0 !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        }}
        
        .card-subtitle {{
            font-size: 0.95rem !important;
            opacity: 0.95 !important;
            font-weight: 600 !important;
            margin: 4px 0 0 0 !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
        }}
        
        /* Cuerpo de tarjetas */
        .card-body {{
            padding: 30px !important;
            background: linear-gradient(145deg, #ffffff, #f8fafc) !important;
        }}
        
        .main-metrics-grid {{
            display: grid !important;
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 20px !important;
            margin-bottom: 25px !important;
        }}
        
        .main-metric {{
            background: linear-gradient(145deg, #ffffff, #f1f5f9) !important;
            padding: 20px !important;
            border-radius: 16px !important;
            text-align: center !important;
            border: 2px solid transparent !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
            overflow: hidden !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
        }}
        
        .main-metric::before {{
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.8), transparent) !important;
            transform: translateX(-100%) !important;
            transition: transform 0.6s ease !important;
        }}
        
        .main-metric:hover {{
            transform: translateY(-5px) scale(1.05) !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
            border-color: {colors['secondary']} !important;
        }}
        
        .main-metric:hover::before {{
            transform: translateX(100%) !important;
        }}
        
        .main-metric.mortality {{
            border-color: {colors['warning']} !important;
            background: linear-gradient(145deg, #fff8e1, #ffecb3) !important;
        }}
        
        .metric-number {{
            font-size: 2.2rem !important;
            font-weight: 900 !important;
            margin-bottom: 8px !important;
            line-height: 1 !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }}
        
        .metric-number.primary {{ color: {colors['primary']} !important; }}
        .metric-number.success {{ color: {colors['success']} !important; }}
        .metric-number.danger {{ color: {colors['danger']} !important; }}
        .metric-number.warning {{ color: {colors['warning']} !important; }}
        .metric-number.info {{ color: {colors['info']} !important; }}
        
        .metric-label {{
            font-size: 0.8rem !important;
            color: #64748b !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }}
        
        /* Información del último evento - SÚPER ESTÉTICA */
        .last-event-info {{
            background: linear-gradient(135deg, #f0f8ff, #e6f3ff, #dbeafe) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            border: 2px solid {colors['info']} !important;
            margin-top: 20px !important;
            position: relative !important;
            overflow: hidden !important;
            box-shadow: 0 6px 20px rgba(70,130,180,0.15) !important;
        }}
        
        .last-event-info::before {{
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 4px !important;
            background: linear-gradient(90deg, {colors['info']}, {colors['primary']}) !important;
        }}
        
        .last-event-title {{
            font-size: 1rem !important;
            font-weight: 800 !important;
            color: {colors['primary']} !important;
            margin-bottom: 12px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
        }}
        
        .last-event-details {{
            font-size: 0.95rem !important;
            line-height: 1.5 !important;
        }}
        
        .last-event-date {{
            color: {colors['info']} !important;
            font-weight: 700 !important;
        }}
        
        .last-event-time {{
            color: {colors['accent']} !important;
            font-weight: 600 !important;
            font-style: italic !important;
        }}
        
        .no-data {{
            color: #94a3b8 !important;
            font-style: italic !important;
            font-weight: 500 !important;
        }}
        
        /* =============== RESPONSIVE MEJORADO =============== */
        @media (max-width: 768px) {{
            .desktop-maps-container {{ display: none !important; }}
            .mobile-maps-container {{ display: block !important; }}
            
            .mobile-map-section iframe {{
                width: 100% !important;
                max-width: min(350px, calc(100vw - 30px)) !important;
                height: 350px !important;
                margin: 0 auto !important;
                border-radius: 12px !important;
                border: 2px solid #e1e5e9 !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            }}
            
            .main-metrics-grid {{
                grid-template-columns: 1fr !important;
                gap: 15px !important;
            }}
            
            .card-header {{
                padding: 20px !important;
            }}
            
            .card-body {{
                padding: 25px !important;
            }}
            
            .card-icon {{
                font-size: 2.2rem !important;
            }}
            
            .card-title {{
                font-size: 1.2rem !important;
            }}
            
            .metric-number {{
                font-size: 1.8rem !important;
            }}
        }}
        
        @media (min-width: 769px) {{
            .mobile-maps-container {{ display: none !important; }}
            .desktop-maps-container {{ display: block !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )