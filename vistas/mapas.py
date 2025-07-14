"""
Vista de mapas con sistema multi-modal y filtrado múltiple CORREGIDA.
"""

import streamlit as st
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Importaciones opcionales para mapas
try:
    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium
    MAPS_AVAILABLE = True
except ImportError:
    MAPS_AVAILABLE = False

from utils.data_processor import calculate_basic_metrics, verify_filtered_data_usage, debug_data_flow

# Sistema híbrido de shapefiles
try:
    from utils.shapefile_loader import load_tolima_shapefiles, check_shapefiles_availability, show_shapefile_setup_instructions
    SHAPEFILE_LOADER_AVAILABLE = True
except ImportError:
    SHAPEFILE_LOADER_AVAILABLE = False

# ===== CONFIGURACIÓN DE COLORES MULTI-MODAL CORREGIDA =====

def get_color_scheme_epidemiological(colors):
    """Esquema de colores epidemiológico CORREGIDO."""
    return {
        "casos_epizootias_fallecidos": colors["danger"],      # 🔴 Rojo: Casos + Epizootias + Fallecidos
        "solo_casos": colors["warning"],                      # 🟠 Naranja: Solo casos  
        "solo_epizootias": colors["secondary"],               # 🟡 Amarillo: Solo epizootias
        "sin_datos": "#E5E7EB"                               # ⚪ Gris claro: Sin datos
    }

def get_color_scheme_coverage(colors):
    """Esquema de colores por cobertura de vacunación."""
    return {
        "cobertura_alta": colors["success"],      # Verde intenso: >95%
        "cobertura_buena": colors["secondary"],   # Amarillo: 80-95%
        "cobertura_regular": colors["warning"],   # Naranja: 60-80%
        "cobertura_baja": colors["danger"],       # Rojo: <60%
        "sin_datos": "#E5E7EB"                   # Gris
    }

def determine_feature_color_epidemiological(casos_count, epizootias_count, fallecidos_count, positivas_count, en_estudio_count, color_scheme):
    """Determina color según modo epidemiológico CORREGIDO."""
    
    # Nueva lógica según especificaciones
    if casos_count > 0 and epizootias_count > 0 and fallecidos_count > 0:
        return color_scheme["casos_epizootias_fallecidos"], "🔴 Casos + Epizootias + Fallecidos"
    elif casos_count > 0 and epizootias_count == 0:
        return color_scheme["solo_casos"], "🟠 Solo casos"
    elif casos_count == 0 and epizootias_count > 0:
        return color_scheme["solo_epizootias"], "🟡 Solo epizootias"
    else:
        return color_scheme["sin_datos"], "⚪ Sin datos"

def determine_feature_color_coverage(cobertura_porcentaje, color_scheme):
    """Determina color según cobertura de vacunación."""
    
    if pd.isna(cobertura_porcentaje):
        return color_scheme["sin_datos"], "Sin datos de cobertura"
    
    if cobertura_porcentaje > 95:
        return color_scheme["cobertura_alta"], f"Cobertura alta: {cobertura_porcentaje:.1f}%"
    elif cobertura_porcentaje >= 80:
        return color_scheme["cobertura_buena"], f"Cobertura buena: {cobertura_porcentaje:.1f}%"
    elif cobertura_porcentaje >= 60:
        return color_scheme["cobertura_regular"], f"Cobertura regular: {cobertura_porcentaje:.1f}%"
    else:
        return color_scheme["cobertura_baja"], f"Cobertura baja: {cobertura_porcentaje:.1f}%"

# ===== FUNCIÓN PRINCIPAL =====

def show(data_filtered, filters, colors):
    """Vista principal de mapas MULTI-MODAL CORREGIDA."""
    logger.info("🗺️ INICIANDO VISTA DE MAPAS MULTI-MODAL CORREGIDA")
    
    # Aplicar CSS compacto CORREGIDO
    apply_compact_maps_css_corrected(colors)
    
    # Verificar datos filtrados
    casos_filtrados = data_filtered["casos"]
    epizootias_filtradas = data_filtered["epizootias"]
    
    verify_filtered_data_usage(casos_filtrados, "vista_mapas_multimodal")
    verify_filtered_data_usage(epizootias_filtradas, "vista_mapas_multimodal")

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

    # Información de filtrado CORREGIDA - sin espacio excesivo
    active_filters = filters.get("active_filters", [])
    modo_mapa = filters.get("modo_mapa", "Epidemiológico")
    
    if active_filters:
        st.markdown(
            f"""
            <div class="filter-info-compact">
                🎯 Vista: <strong>{modo_mapa}</strong> | Filtros: <strong>{' • '.join(active_filters[:2])}</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Layout compacto 70/30 CORREGIDO
    create_compact_layout_corrected(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered)

# ===== LAYOUT COMPACTO 70/30 CORREGIDO =====

def create_compact_layout_corrected(casos, epizootias, geo_data, filters, colors, data_filtered):
    """Layout compacto 70% mapa - 30% tarjetas CORREGIDO."""
    
    # Usar columnas con proporción 70/30
    col_mapa, col_info = st.columns([7, 3], gap="medium")
    
    with col_mapa:
        # Sistema de mapas principal CORREGIDO
        create_map_system_corrected(casos, epizootias, geo_data, filters, colors)
    
    with col_info:
        # Tarjetas informativas compactas MEJORADAS
        create_compact_information_cards_improved(casos, epizootias, filters, colors)

def create_map_system_corrected(casos, epizootias, geo_data, filters, colors):
    """Sistema de mapas compacto CORREGIDO."""
    current_level = determine_map_level(filters)
    modo_mapa = filters.get("modo_mapa", "Epidemiológico")
    
    # Verificar datos geográficos
    has_municipios = 'municipios' in geo_data and not geo_data['municipios'].empty
    has_veredas = 'veredas' in geo_data and not geo_data['veredas'].empty
    
    # Crear mapa según nivel y modo
    if current_level == "vereda" and filters.get("modo") == "unico":
        create_vereda_specific_map_corrected(casos, epizootias, geo_data, filters, colors)
    elif current_level == "departamento" and has_municipios:
        if filters.get("modo") == "multiple":
            create_departmental_map_multiple_corrected(casos, epizootias, geo_data, filters, colors)
        else:
            create_departmental_map_corrected(casos, epizootias, geo_data, filters, colors, modo_mapa)
    elif current_level == "municipio" and has_veredas:
        if filters.get("modo") == "multiple":
            create_municipal_map_multiple_corrected(casos, epizootias, geo_data, filters, colors)
        else:
            create_municipal_map_corrected(casos, epizootias, geo_data, filters, colors, modo_mapa)
    else:
        show_fallback_summary_table(casos, epizootias, current_level, filters.get('municipio_display'))

def create_departmental_map_corrected(casos, epizootias, geo_data, filters, colors, modo_mapa):
    """Mapa departamental CORREGIDO."""
    municipios = geo_data['municipios'].copy()
    logger.info(f"🏛️ Mapa departamental {modo_mapa}: {len(municipios)} municipios")
    
    # Preparar datos según modo
    if modo_mapa == "Epidemiológico":
        municipios_data = prepare_municipal_data_epidemiological_corrected(casos, epizootias, municipios, colors)
    else:
        municipios_data = prepare_municipal_data_coverage_manual(municipios, colors)
    
    # Configuración del mapa MEJORADA - tamaño completo
    bounds = municipios.total_bounds
    center_lat, center_lon = (bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='CartoDB positron',
        attributionControl=False,
        zoom_control=True,
        scrollWheelZoom=True
    )
    
    # Aplicar límites
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    
    # Agregar municipios con colores según modo
    add_municipios_to_map_multimodal_corrected(m, municipios_data, colors, modo_mapa)
    
    # Renderizar con tamaño COMPLETO
    map_data = st_folium(
        m, 
        width=700,  # Aumentado
        height=500,  # Aumentado
        returned_objects=["last_object_clicked"],
        key=f"map_departamental_corrected_{modo_mapa.lower()}"
    )
    
    # Procesar clicks CORREGIDO para evitar bucles
    handle_map_click_corrected(map_data, municipios_data, "municipio", filters, casos, epizootias)

def create_municipal_map_corrected(casos, epizootias, geo_data, filters, colors, modo_mapa):
    """Mapa municipal CORREGIDO."""
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
    
    # Preparar datos según modo
    if modo_mapa == "Epidemiológico":
        veredas_data = prepare_vereda_data_epidemiological_corrected(casos, epizootias, veredas_municipio, municipio_selected, colors)
    else:
        veredas_data = prepare_vereda_data_coverage_manual(veredas_municipio, municipio_selected, colors)
    
    # Crear mapa
    bounds = veredas_municipio.total_bounds
    center_lat, center_lon = (bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB positron',
        attributionControl=False,
        zoom_control=True,
        scrollWheelZoom=True
    )
    
    # Aplicar límites y agregar veredas
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    add_veredas_to_map_multimodal_corrected(m, veredas_data, colors, modo_mapa)
    
    # Renderizar con tamaño COMPLETO
    map_data = st_folium(
        m, 
        width=700,  # Aumentado
        height=500,  # Aumentado
        returned_objects=["last_object_clicked"],
        key=f"map_municipal_corrected_{modo_mapa.lower()}"
    )
    
    # Procesar clicks CORREGIDO
    handle_map_click_corrected(map_data, veredas_data, "vereda", filters, casos, epizootias)

def create_vereda_specific_map_corrected(casos, epizootias, geo_data, filters, colors):
    """Vista específica de vereda CORREGIDA."""
    vereda_selected = filters.get('vereda_display')
    municipio_selected = filters.get('municipio_display')
    
    if not vereda_selected or vereda_selected == "Todas":
        st.error("No se pudo determinar la vereda para vista específica")
        return
    
    veredas = geo_data['veredas'].copy()
    
    # Buscar la vereda específica
    vereda_especifica = veredas[
        (veredas['vereda_nor'] == vereda_selected) & 
        (veredas['municipi_1'] == municipio_selected)
    ]
    
    if vereda_especifica.empty:
        st.warning(f"No se encontró el croquis para {vereda_selected} en {municipio_selected}")
        create_vereda_detail_view_optimized(casos, epizootias, filters, colors)
        return
    
    # Crear mapa centrado solo en la vereda
    bounds = vereda_especifica.total_bounds
    center_lat, center_lon = (bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap',
        attributionControl=False,
        zoom_control=True,
        scrollWheelZoom=True
    )
    
    # Solo mostrar el contorno de la vereda
    for idx, row in vereda_especifica.iterrows():
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x: {
                'fillColor': colors['secondary'],
                'color': colors['primary'],
                'weight': 3,
                'fillOpacity': 0.4,
                'opacity': 1
            },
            tooltip=folium.Tooltip(
                f"""
                <div style="font-family: Arial; padding: 10px;">
                    <b style="color: {colors['primary']};">{vereda_selected}</b><br>
                    📍 {municipio_selected}<br>
                    🗺️ Vista de croquis específico
                </div>
                """,
                sticky=True
            ),
        ).add_to(m)
    
    # Ajustar vista a la vereda específica
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    
    # Renderizar mapa con tamaño COMPLETO
    st_folium(
        m, 
        width=700,  # Aumentado
        height=450,  # Aumentado
        returned_objects=[],
        key=f"map_vereda_especifica_{vereda_selected}"
    )
    
    # Mostrar datos específicos de la vereda
    show_vereda_specific_data(casos, epizootias, vereda_selected, municipio_selected, colors)

# ===== PREPARACIÓN DE DATOS CORREGIDA =====

def prepare_municipal_data_epidemiological_corrected(casos, epizootias, municipios, colors):
    """Prepara datos municipales para modo epidemiológico CORREGIDO."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipios = municipios.copy()
    municipios['municipi_1_norm'] = municipios['municipi_1'].apply(normalize_name)
    
    # Obtener esquema de colores CORREGIDO
    color_scheme = get_color_scheme_epidemiological(colors)
    
    # Contadores por municipio
    contadores_municipios = {}
    
    if not casos.empty and 'municipio' in casos.columns:
        casos_norm = casos.copy()
        casos_norm['municipio_norm'] = casos_norm['municipio'].apply(normalize_name)
        
        for municipio_norm in municipios['municipi_1_norm'].unique():
            casos_mun = casos_norm[casos_norm['municipio_norm'] == municipio_norm]
            fallecidos_mun = casos_mun[casos_mun['condicion_final'] == 'Fallecido'] if 'condicion_final' in casos_mun.columns else pd.DataFrame()
            
            contadores_municipios[municipio_norm] = {
                'casos': len(casos_mun),
                'fallecidos': len(fallecidos_mun)
            }
    
    if not epizootias.empty and 'municipio' in epizootias.columns:
        epi_norm = epizootias.copy()
        epi_norm['municipio_norm'] = epi_norm['municipio'].apply(normalize_name)
        
        for municipio_norm in municipios['municipi_1_norm'].unique():
            if municipio_norm not in contadores_municipios:
                contadores_municipios[municipio_norm] = {'casos': 0, 'fallecidos': 0}
            
            epi_mun = epi_norm[epi_norm['municipio_norm'] == municipio_norm]
            positivas_mun = epi_mun[epi_mun['descripcion'] == 'POSITIVO FA'] if 'descripcion' in epi_mun.columns else pd.DataFrame()
            en_estudio_mun = epi_mun[epi_mun['descripcion'] == 'EN ESTUDIO'] if 'descripcion' in epi_mun.columns else pd.DataFrame()
            
            contadores_municipios[municipio_norm].update({
                'epizootias': len(epi_mun),
                'positivas': len(positivas_mun),
                'en_estudio': len(en_estudio_mun)
            })
    
    # Aplicar colores según modo epidemiológico CORREGIDO
    municipios_data = municipios.copy()
    
    for idx, row in municipios_data.iterrows():
        municipio_norm = row['municipi_1_norm']
        contadores = contadores_municipios.get(municipio_norm, {
            'casos': 0, 'fallecidos': 0, 'epizootias': 0, 'positivas': 0, 'en_estudio': 0
        })
        
        color, descripcion = determine_feature_color_epidemiological(
            contadores['casos'],
            contadores['epizootias'], 
            contadores['fallecidos'],
            contadores['positivas'],
            contadores['en_estudio'],
            color_scheme
        )
        
        municipios_data.loc[idx, 'color'] = color
        municipios_data.loc[idx, 'descripcion_color'] = descripcion
        
        # Agregar contadores como columnas
        for key, value in contadores.items():
            municipios_data.loc[idx, key] = value
    
    logger.info(f"🎨 Datos municipales epidemiológicos preparados: {len(municipios_data)} municipios")
    return municipios_data

def prepare_vereda_data_epidemiological_corrected(casos, epizootias, veredas_gdf, municipio_actual, colors):
    """Prepara datos de veredas para modo epidemiológico CORREGIDO."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    veredas_gdf = veredas_gdf.copy()
    veredas_gdf['vereda_nor_norm'] = veredas_gdf['vereda_nor'].apply(normalize_name)
    municipio_norm = normalize_name(municipio_actual)
    
    color_scheme = get_color_scheme_epidemiological(colors)
    
    # Contadores por vereda
    contadores_veredas = {}
    
    if not casos.empty and 'vereda' in casos.columns and 'municipio' in casos.columns:
        casos_norm = casos.copy()
        casos_norm['vereda_norm'] = casos_norm['vereda'].apply(normalize_name)
        casos_norm['municipio_norm'] = casos_norm['municipio'].apply(normalize_name)
        
        casos_municipio = casos_norm[casos_norm['municipio_norm'] == municipio_norm]
        
        for vereda_norm in veredas_gdf['vereda_nor_norm'].unique():
            casos_ver = casos_municipio[casos_municipio['vereda_norm'] == vereda_norm]
            fallecidos_ver = casos_ver[casos_ver['condicion_final'] == 'Fallecido'] if 'condicion_final' in casos_ver.columns else pd.DataFrame()
            
            contadores_veredas[vereda_norm] = {
                'casos': len(casos_ver),
                'fallecidos': len(fallecidos_ver)
            }
    
    if not epizootias.empty and 'vereda' in epizootias.columns and 'municipio' in epizootias.columns:
        epi_norm = epizootias.copy()
        epi_norm['vereda_norm'] = epi_norm['vereda'].apply(normalize_name)
        epi_norm['municipio_norm'] = epi_norm['municipio'].apply(normalize_name)
        
        epi_municipio = epi_norm[epi_norm['municipio_norm'] == municipio_norm]
        
        for vereda_norm in veredas_gdf['vereda_nor_norm'].unique():
            if vereda_norm not in contadores_veredas:
                contadores_veredas[vereda_norm] = {'casos': 0, 'fallecidos': 0}
            
            epi_ver = epi_municipio[epi_municipio['vereda_norm'] == vereda_norm]
            positivas_ver = epi_ver[epi_ver['descripcion'] == 'POSITIVO FA'] if 'descripcion' in epi_ver.columns else pd.DataFrame()
            en_estudio_ver = epi_ver[epi_ver['descripcion'] == 'EN ESTUDIO'] if 'descripcion' in epi_ver.columns else pd.DataFrame()
            
            contadores_veredas[vereda_norm].update({
                'epizootias': len(epi_ver),
                'positivas': len(positivas_ver),
                'en_estudio': len(en_estudio_ver)
            })
    
    # Aplicar colores CORREGIDOS
    veredas_data = veredas_gdf.copy()
    
    for idx, row in veredas_data.iterrows():
        vereda_norm = row['vereda_nor_norm']
        contadores = contadores_veredas.get(vereda_norm, {
            'casos': 0, 'fallecidos': 0, 'epizootias': 0, 'positivas': 0, 'en_estudio': 0
        })
        
        color, descripcion = determine_feature_color_epidemiological(
            contadores['casos'],
            contadores['epizootias'],
            contadores['fallecidos'],
            contadores['positivas'],
            contadores['en_estudio'],
            color_scheme
        )
        
        veredas_data.loc[idx, 'color'] = color
        veredas_data.loc[idx, 'descripcion_color'] = descripcion
        
        for key, value in contadores.items():
            veredas_data.loc[idx, key] = value
    
    logger.info(f"🎨 Datos veredas epidemiológicos {municipio_actual}: {len(veredas_data)} veredas")
    return veredas_data

# ===== DATOS DE COBERTURA MANUALES =====

def prepare_municipal_data_coverage_manual(municipios, colors):
    """Prepara datos municipales para modo cobertura MANUAL."""
    municipios_data = municipios.copy()
    color_scheme = get_color_scheme_coverage(colors)
    
    # AQUÍ PUEDES MODIFICAR LOS PORCENTAJES MANUALMENTE
    # Diccionario de coberturas por municipio (puedes editarlo)
    COBERTURAS_MUNICIPIOS = {
        'IBAGUE': 85.2,
        'ALPUJARRA': 78.5,
        'ALVARADO': 92.1,
        'AMBALEMA': 67.8,
        'ANZOATEGUI': 73.4,
        'ARMERO': 69.2,
        'ATACO': 81.7,
        'CAJAMARCA': 88.3,
        'CARMEN DE APICALA': 74.9,
        'CASABIANCA': 82.6,
        'CHAPARRAL': 79.1,
        'COELLO': 86.4,
        'COYAIMA': 71.3,
        'CUNDAY': 77.8,
        'DOLORES': 65.7,
        'ESPINAL': 89.5,
        'FALAN': 83.2,
        'FLANDES': 91.8,
        'FRESNO': 76.4,
        'GUAMO': 84.1,
        'HERVEO': 72.9,
        'HONDA': 87.6,
        'ICONONZO': 75.3,
        'LERIDA': 80.7,
        'LIBANO': 85.9,
        'MARIQUITA': 88.2,
        'MELGAR': 82.4,
        'MURILLO': 70.6,
        'NATAGAIMA': 68.9,
        'ORTEGA': 79.8,
        'PALOCABILDO': 74.2,
        'PIEDRAS': 86.7,
        'PLANADAS': 77.1,
        'PRADO': 83.5,
        'PURIFICACION': 81.3,
        'RIOBLANCO': 69.8,
        'RONCESVALLES': 75.6,
        'ROVIRA': 84.8,
        'SALDAÑA': 87.3,
        'SAN ANTONIO': 73.7,
        'SAN LUIS': 78.9,
        'SANTA ISABEL': 80.4,
        'SUAREZ': 76.8,
        'VALLE DE SAN JUAN': 85.6,
        'VENADILLO': 89.1,
        'VILLAHERMOSA': 72.2,
        'VILLARRICA': 81.9
    }
    
    for idx, row in municipios_data.iterrows():
        municipio_name = row.get('MpNombre', row.get('municipi_1', 'DESCONOCIDO'))
        cobertura_value = COBERTURAS_MUNICIPIOS.get(municipio_name, 75.0)  # Default 75%
        
        color, descripcion = determine_feature_color_coverage(cobertura_value, color_scheme)
        
        municipios_data.loc[idx, 'color'] = color
        municipios_data.loc[idx, 'descripcion_color'] = descripcion
        municipios_data.loc[idx, 'cobertura'] = cobertura_value
    
    logger.info(f"💉 Datos municipales de cobertura MANUAL: {len(municipios_data)} municipios")
    return municipios_data

def prepare_vereda_data_coverage_manual(veredas_gdf, municipio_actual, colors):
    """Prepara datos de veredas para modo cobertura MANUAL."""
    veredas_data = veredas_gdf.copy()
    color_scheme = get_color_scheme_coverage(colors)
    
    # AQUÍ PUEDES MODIFICAR LOS PORCENTAJES POR VEREDA
    # Por ahora uso variación del municipio base
    cobertura_base_municipio = {
        'IBAGUE': 85,
        'ALPUJARRA': 78,
        'ALVARADO': 92,
        # Agrega más municipios según necesites
    }.get(municipio_actual, 75)
    
    import random
    random.seed(hash(municipio_actual) % 1000)
    
    for idx, row in veredas_data.iterrows():
        # Variación ±10% del municipio base
        variacion = random.uniform(-10, 10)
        cobertura_vereda = max(30, min(98, cobertura_base_municipio + variacion))
        
        color, descripcion = determine_feature_color_coverage(cobertura_vereda, color_scheme)
        
        veredas_data.loc[idx, 'color'] = color
        veredas_data.loc[idx, 'descripcion_color'] = descripcion
        veredas_data.loc[idx, 'cobertura'] = cobertura_vereda
    
    logger.info(f"💉 Datos veredas cobertura MANUAL {municipio_actual}: {len(veredas_data)} veredas")
    return veredas_data

# ===== MANEJO DE CLICKS CORREGIDO =====

def handle_map_click_corrected(map_data, features_data, feature_type, filters, casos, epizootias):
    """Manejo de clicks CORREGIDO para evitar bucles infinitos."""
    if not map_data or not map_data.get('last_object_clicked'):
        return
    
    try:
        clicked_object = map_data['last_object_clicked']
        
        if isinstance(clicked_object, dict):
            clicked_lat = clicked_object.get('lat')
            clicked_lng = clicked_object.get('lng')
            
            if clicked_lat and clicked_lng:
                feature_clicked = find_closest_feature_corrected(clicked_lat, clicked_lng, features_data, feature_type)
                
                if feature_clicked:
                    # Aplicar filtro sin bucle infinito
                    apply_feature_filter_corrected(feature_clicked, feature_type, filters)
                    
                    # Verificar si el área tiene datos ANTES de rerun
                    has_data = check_area_has_data(feature_clicked, feature_type, casos, epizootias)
                    
                    if has_data:
                        st.success(f"✅ Filtrado: **{feature_clicked}** (con datos)")
                    else:
                        st.info(f"📊 Filtrado: **{feature_clicked}** (área sin datos - métricas en cero)")
                    
                    # Delay antes de rerun para evitar bucles
                    import time
                    time.sleep(0.5)
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"❌ Error procesando clic: {str(e)}")

def find_closest_feature_corrected(lat, lng, features_data, feature_type):
    """Encuentra el feature más cercano CORREGIDO."""
    min_distance = float('inf')
    closest_feature = None
    
    name_column = 'MpNombre' if feature_type == 'municipio' else 'vereda_nor'
    
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

def apply_feature_filter_corrected(feature_name, feature_type, filters):
    """Aplica filtro CORREGIDO según el tipo de feature."""
    if feature_type == "municipio":
        if filters.get("modo") == "multiple":
            # En modo múltiple, agregar a la selección
            current_selection = st.session_state.get('municipios_multiselect', [])
            if feature_name not in current_selection:
                current_selection.append(feature_name)
                st.session_state['municipios_multiselect'] = current_selection
        else:
            # En modo único, filtrar normalmente
            st.session_state['municipio_filter'] = feature_name
            st.session_state['vereda_filter'] = 'Todas'
    
    elif feature_type == "vereda":
        if filters.get("modo") == "multiple":
            # En modo múltiple, agregar a la selección
            current_selection = st.session_state.get('veredas_multiselect', [])
            if feature_name not in current_selection:
                current_selection.append(feature_name)
                st.session_state['veredas_multiselect'] = current_selection
        else:
            # En modo único, filtrar normalmente
            st.session_state['vereda_filter'] = feature_name

def check_area_has_data(feature_name, feature_type, casos, epizootias):
    """Verifica si un área tiene datos ANTES de filtrar."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    feature_norm = normalize_name(feature_name)
    
    # Verificar casos
    has_casos = False
    if not casos.empty:
        if feature_type == "municipio" and "municipio" in casos.columns:
            has_casos = len(casos[casos["municipio"].apply(normalize_name) == feature_norm]) > 0
        elif feature_type == "vereda" and "vereda" in casos.columns:
            has_casos = len(casos[casos["vereda"].apply(normalize_name) == feature_norm]) > 0
    
    # Verificar epizootias
    has_epizootias = False
    if not epizootias.empty:
        if feature_type == "municipio" and "municipio" in epizootias.columns:
            has_epizootias = len(epizootias[epizootias["municipio"].apply(normalize_name) == feature_norm]) > 0
        elif feature_type == "vereda" and "vereda" in epizootias.columns:
            has_epizootias = len(epizootias[epizootias["vereda"].apply(normalize_name) == feature_norm]) > 0
    
    return has_casos or has_epizootias

# ===== TARJETAS MEJORADAS =====

def create_compact_information_cards_improved(casos, epizootias, filters, colors):
    """Tarjetas informativas MEJORADAS estéticamente."""
    logger.info("🏷️ Creando tarjetas mejoradas")
    
    metrics = calculate_basic_metrics(casos, epizootias)
    
    # Tarjeta de casos MEJORADA
    create_improved_cases_card(metrics, filters, colors)
    
    # Tarjeta de epizootias MEJORADA  
    create_improved_epizootias_card(metrics, filters, colors)
    
    # Tarjeta de cobertura MEJORADA
    create_improved_coverage_card(filters, colors)

def create_improved_cases_card(metrics, filters, colors):
    """Tarjeta de casos MEJORADA."""
    total_casos = metrics["total_casos"]
    vivos = metrics["vivos"]
    fallecidos = metrics["fallecidos"]
    letalidad = metrics["letalidad"]
    
    filter_context = get_filter_context_compact(filters)
    
    st.markdown(
        f"""
        <div class="improved-card cases-card">
            <div class="card-header">
                <div class="card-icon">🦠</div>
                <div class="card-title-section">
                    <div class="card-title">CASOS HUMANOS</div>
                    <div class="card-subtitle">{filter_context}</div>
                </div>
                <div class="card-total">{total_casos}</div>
            </div>
            <div class="card-metrics">
                <div class="metric-grid">
                    <div class="metric-cell success">
                        <div class="metric-value">{vivos}</div>
                        <div class="metric-label">Vivos</div>
                    </div>
                    <div class="metric-cell danger">
                        <div class="metric-value">{fallecidos}</div>
                        <div class="metric-label">Fallecidos</div>
                    </div>
                </div>
                <div class="metric-footer">
                    <span class="footer-label">Letalidad:</span>
                    <span class="footer-value">{letalidad:.1f}%</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def create_improved_epizootias_card(metrics, filters, colors):
    """Tarjeta de epizootias MEJORADA."""
    total_epizootias = metrics["total_epizootias"]
    positivas = metrics["epizootias_positivas"]
    en_estudio = metrics["epizootias_en_estudio"]
    
    filter_context = get_filter_context_compact(filters)
    
    st.markdown(
        f"""
        <div class="improved-card epizootias-card">
            <div class="card-header">
                <div class="card-icon">🐒</div>
                <div class="card-title-section">
                    <div class="card-title">EPIZOOTIAS</div>
                    <div class="card-subtitle">{filter_context}</div>
                </div>
                <div class="card-total">{total_epizootias}</div>
            </div>
            <div class="card-metrics">
                <div class="metric-grid">
                    <div class="metric-cell danger">
                        <div class="metric-value">{positivas}</div>
                        <div class="metric-label">Positivas</div>
                    </div>
                    <div class="metric-cell info">
                        <div class="metric-value">{en_estudio}</div>
                        <div class="metric-label">En Estudio</div>
                    </div>
                </div>
                <div class="metric-footer">
                    <span class="footer-label">Positividad:</span>
                    <span class="footer-value">{(positivas/total_epizootias*100) if total_epizootias > 0 else 0:.1f}%</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def create_improved_coverage_card(filters, colors):
    """Tarjeta de cobertura MEJORADA."""
    # Datos simulados mejorados
    cobertura_simulada = 82.3
    meta_cobertura = 95.0
    gap_cobertura = meta_cobertura - cobertura_simulada
    
    filter_context = get_filter_context_compact(filters)
    
    st.markdown(
        f"""
        <div class="improved-card coverage-card">
            <div class="card-header">
                <div class="card-icon">💉</div>
                <div class="card-title-section">
                    <div class="card-title">COBERTURA</div>
                    <div class="card-subtitle">{filter_context}</div>
                </div>
                <div class="card-total">{cobertura_simulada:.1f}%</div>
            </div>
            <div class="card-metrics">
                <div class="coverage-bar">
                    <div class="coverage-progress" style="width: {cobertura_simulada}%"></div>
                </div>
                <div class="metric-grid">
                    <div class="metric-cell success">
                        <div class="metric-value">Meta</div>
                        <div class="metric-label">{meta_cobertura:.0f}%</div>
                    </div>
                    <div class="metric-cell warning">
                        <div class="metric-value">Gap</div>
                        <div class="metric-label">{gap_cobertura:.1f}%</div>
                    </div>
                </div>
            </div>
            <div class="card-note">
                💡 Datos simulados - en desarrollo
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===== FUNCIONES DE APOYO (mantener las existentes) =====

def load_geographic_data():
    if not SHAPEFILE_LOADER_AVAILABLE:
        logger.warning("⚠️ Sistema híbrido no disponible")
        return None
    
    try:
        return load_tolima_shapefiles()
    except Exception as e:
        logger.error(f"❌ Error cargando datos geográficos: {str(e)}")
        return None

def determine_map_level(filters):
    if filters.get("vereda_display") and filters.get("vereda_display") != "Todas":
        return "vereda"
    elif filters.get("municipio_display") and filters.get("municipio_display") != "Todos":
        return "municipio"
    else:
        return "departamento"

def get_filter_context_compact(filters):
    """Contexto de filtrado compacto."""
    if filters.get("modo") == "multiple":
        municipios_sel = len(filters.get("municipios_seleccionados", []))
        if municipios_sel > 0:
            return f"{municipios_sel} municipios"
    
    municipio = filters.get("municipio_display", "Todos")
    vereda = filters.get("vereda_display", "Todas")
    
    if vereda != "Todas":
        return f"{vereda[:12]}..."
    elif municipio != "Todos":
        return f"{municipio[:12]}..."
    else:
        return "Tolima"

def show_vereda_specific_data(casos, epizootias, vereda_selected, municipio_selected, colors):
    """Muestra datos específicos de la vereda."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    vereda_norm = normalize_name(vereda_selected)
    municipio_norm = normalize_name(municipio_selected)
    
    # Filtrar datos de la vereda específica
    casos_vereda = pd.DataFrame()
    epizootias_vereda = pd.DataFrame()
    
    if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
        casos_vereda = casos[
            (casos["vereda"].apply(normalize_name) == vereda_norm) &
            (casos["municipio"].apply(normalize_name) == municipio_norm)
        ]
    
    if not epizootias.empty and "vereda" in epizootias.columns and "municipio" in epizootias.columns:
        epizootias_vereda = epizootias[
            (epizootias["vereda"].apply(normalize_name) == vereda_norm) &
            (epizootias["municipio"].apply(normalize_name) == municipio_norm)
        ]
    
    # Métricas específicas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🦠 Casos", len(casos_vereda))
    with col2:
        fallecidos = len(casos_vereda[casos_vereda["condicion_final"] == "Fallecido"]) if not casos_vereda.empty and "condicion_final" in casos_vereda.columns else 0
        st.metric("⚰️ Fallecidos", fallecidos)
    with col3:
        st.metric("🐒 Epizootias", len(epizootias_vereda))
    with col4:
        positivas = len(epizootias_vereda[epizootias_vereda["descripcion"] == "POSITIVO FA"]) if not epizootias_vereda.empty and "descripcion" in epizootias_vereda.columns else 0
        st.metric("🔴 Positivas", positivas)

# ===== PLACEHOLDERS PARA FUNCIONES MÚLTIPLES =====

def create_departmental_map_multiple_corrected(casos, epizootias, geo_data, filters, colors):
    """Placeholder para mapa departamental múltiple."""
    st.info("🗂️ Vista múltiple departamental - en desarrollo")

def create_municipal_map_multiple_corrected(casos, epizootias, geo_data, filters, colors):
    """Placeholder para mapa municipal múltiple."""
    st.info("🗂️ Vista múltiple municipal - en desarrollo")

def add_municipios_to_map_multimodal_corrected(folium_map, municipios_data, colors, modo_mapa):
    """Agrega municipios al mapa CORREGIDO."""
    for idx, row in municipios_data.iterrows():
        municipio_name = row['MpNombre']
        color = row['color']
        descripcion = row['descripcion_color']
        
        # Crear tooltip según modo
        if modo_mapa == "Epidemiológico":
            tooltip_text = create_municipio_tooltip_epidemiological_corrected(municipio_name, row, colors)
        else:
            tooltip_text = create_municipio_tooltip_coverage_corrected(municipio_name, row, colors)
        
        # Agregar polígono
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=color: {
                'fillColor': color,
                'color': colors['primary'],
                'weight': 2,
                'fillOpacity': 0.7,
                'opacity': 1
            },
            tooltip=folium.Tooltip(tooltip_text, sticky=True),
        ).add_to(folium_map)

def add_veredas_to_map_multimodal_corrected(folium_map, veredas_data, colors, modo_mapa):
    """Agrega veredas al mapa CORREGIDO."""
    for idx, row in veredas_data.iterrows():
        vereda_name = row['vereda_nor']
        color = row['color']
        descripcion = row['descripcion_color']
        
        # Crear tooltip según modo
        if modo_mapa == "Epidemiológico":
            tooltip_text = create_vereda_tooltip_epidemiological_corrected(vereda_name, row, colors)
        else:
            tooltip_text = create_vereda_tooltip_coverage_corrected(vereda_name, row, colors)
        
        try:
            folium.GeoJson(
                row['geometry'],
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': colors['accent'],
                    'weight': 1.5,
                    'fillOpacity': 0.6,
                    'opacity': 1
                },
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            ).add_to(folium_map)
        except Exception as e:
            logger.warning(f"⚠️ Error agregando vereda {vereda_name}: {str(e)}")

def create_municipio_tooltip_epidemiological_corrected(name, row, colors):
    """Tooltip para municipio epidemiológico CORREGIDO."""
    return f"""
    <div style="font-family: Arial; padding: 10px; max-width: 250px;">
        <b style="color: {colors['primary']}; font-size: 1.1em;">{name}</b><br>
        <div style="margin: 8px 0; padding: 6px; background: #f8f9fa; border-radius: 4px;">
            🦠 Casos: {row.get('casos', 0)}<br>
            ⚰️ Fallecidos: {row.get('fallecidos', 0)}<br>
            🐒 Epizootias: {row.get('epizootias', 0)}<br>
            🔴 Positivas: {row.get('positivas', 0)}
        </div>
        <div style="color: {colors['info']}; font-size: 0.9em;">
            {row.get('descripcion_color', 'Sin clasificar')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
    </div>
    """

def create_municipio_tooltip_coverage_corrected(name, row, colors):
    """Tooltip para municipio cobertura CORREGIDO."""
    return f"""
    <div style="font-family: Arial; padding: 10px; max-width: 200px;">
        <b style="color: {colors['primary']}; font-size: 1.1em;">{name}</b><br>
        <div style="margin: 8px 0; padding: 6px; background: #f0f8ff; border-radius: 4px;">
            💉 Cobertura: {row.get('cobertura', 0):.1f}%<br>
            📊 {row.get('descripcion_color', 'Sin datos')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
    </div>
    """

def create_vereda_tooltip_epidemiological_corrected(name, row, colors):
    """Tooltip para vereda epidemiológico CORREGIDO."""
    return f"""
    <div style="font-family: Arial; padding: 8px; max-width: 200px;">
        <b style="color: {colors['primary']};">{name}</b><br>
        <div style="margin: 6px 0; font-size: 0.9em;">
            🦠 Casos: {row.get('casos', 0)}<br>
            🐒 Epizootias: {row.get('epizootias', 0)}<br>
            🔴 Positivas: {row.get('positivas', 0)}
        </div>
        <div style="color: {colors['info']}; font-size: 0.8em;">
            {row.get('descripcion_color', 'Sin datos')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
    </div>
    """

def create_vereda_tooltip_coverage_corrected(name, row, colors):
    """Tooltip para vereda cobertura CORREGIDO."""
    return f"""
    <div style="font-family: Arial; padding: 8px; max-width: 180px;">
        <b style="color: {colors['primary']};">{name}</b><br>
        <div style="margin: 6px 0;">
            💉 Cobertura: {row.get('cobertura', 0):.1f}%
        </div>
        <div style="color: {colors['info']}; font-size: 0.8em;">
            {row.get('descripcion_color', 'Sin datos')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
    </div>
    """

def show_fallback_summary_table(casos, epizootias, level, location=None):
    """Tabla resumen cuando no hay mapas."""
    level_info = {
        "departamento": "🏛️ Vista Departamental - Tolima",
        "municipio": f"🏘️ Vista Municipal - {location}" if location else "🏘️ Vista Municipal"
    }
    
    st.info(f"📊 {level_info.get(level, 'Vista')} (modo tabular - mapas no disponibles)")

def show_municipal_tabular_view(casos, epizootias, filters, colors):
    """Vista tabular municipal."""
    municipio_display = filters.get('municipio_display', 'Municipio')
    st.info(f"🗺️ Vista tabular para {municipio_display} (mapa no disponible)")

def create_vereda_detail_view_optimized(casos, epizootias, filters, colors):
    """Vista detallada de vereda sin mapa."""
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

def show_maps_not_available():
    """Mensaje cuando mapas no están disponibles."""
    st.error("⚠️ Librerías de mapas no instaladas")
    st.info("Instale: `pip install geopandas folium streamlit-folium`")

def show_geographic_data_error():
    """Error cuando no hay datos geográficos."""
    st.error("🗺️ No se pudieron cargar los datos de mapas")
    st.info("Verifique la configuración de shapefiles")

# ===== CSS COMPACTO CORREGIDO =====

def apply_compact_maps_css_corrected(colors):
    """CSS para layout compacto CORREGIDO."""
    st.markdown(
        f"""
        <style>
        /* =============== CORRECCIÓN ESPACIADO =============== */
        
        .filter-info-compact {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            text-align: center;
            margin: 10px 0 15px 0;  /* REDUCIDO */
            font-size: 0.9rem;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        /* =============== TARJETAS MEJORADAS =============== */
        
        .improved-card {{
            background: linear-gradient(135deg, white, #f8fafc);
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
            overflow: hidden;
            transition: all 0.3s ease;
            border: 1px solid #e2e8f0;
        }}
        
        .improved-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(0,0,0,0.18);
        }}
        
        .card-header {{
            background: linear-gradient(135deg, {colors['light']}, #ffffff);
            padding: 20px;
            border-bottom: 2px solid #f1f5f9;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .card-icon {{
            font-size: 2.2rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }}
        
        .card-title-section {{
            flex: 1;
        }}
        
        .card-title {{
            color: {colors['primary']};
            font-size: 1rem;
            font-weight: 800;
            margin: 0;
        }}
        
        .card-subtitle {{
            color: {colors['accent']};
            font-size: 0.8rem;
            font-weight: 600;
            margin: 2px 0 0 0;
        }}
        
        .card-total {{
            font-size: 2rem;
            font-weight: 900;
            color: {colors['primary']};
            text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        }}
        
        .card-metrics {{
            padding: 20px;
        }}
        
        .metric-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .metric-cell {{
            background: #f8fafc;
            padding: 12px;
            border-radius: 12px;
            text-align: center;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }}
        
        .metric-cell:hover {{
            transform: scale(1.05);
            background: #f1f5f9;
        }}
        
        .metric-cell.success {{
            border-color: {colors['success']};
        }}
        
        .metric-cell.danger {{
            border-color: {colors['danger']};
        }}
        
        .metric-cell.info {{
            border-color: {colors['info']};
        }}
        
        .metric-cell.warning {{
            border-color: {colors['warning']};
        }}
        
        .metric-value {{
            font-size: 1.4rem;
            font-weight: 800;
            color: {colors['primary']};
            margin-bottom: 2px;
        }}
        
        .metric-label {{
            font-size: 0.75rem;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric-footer {{
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']});
            color: white;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            font-size: 0.9rem;
            font-weight: 600;
        }}
        
        .footer-label {{
            margin-right: 8px;
        }}
        
        .footer-value {{
            font-weight: 800;
            font-size: 1.1rem;
        }}
        
        /* =============== TARJETA DE COBERTURA ESPECIAL =============== */
        
        .coverage-card .card-header {{
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        }}
        
        .coverage-bar {{
            background: #e2e8f0;
            height: 8px;
            border-radius: 4px;
            margin: 15px 0;
            overflow: hidden;
        }}
        
        .coverage-progress {{
            background: linear-gradient(135deg, {colors['success']}, {colors['secondary']});
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        
        .card-note {{
            background: #f8fafc;
            color: {colors['accent']};
            padding: 8px 12px;
            font-size: 0.75rem;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}
        
        /* =============== RESPONSIVE MEJORADO =============== */
        
        @media (max-width: 1200px) {{
            .improved-card {{
                margin-bottom: 15px;
            }}
            
            .card-header {{
                padding: 15px;
            }}
            
            .card-metrics {{
                padding: 15px;
            }}
        }}
        
        @media (max-width: 768px) {{
            .metric-grid {{
                grid-template-columns: 1fr;
                gap: 10px;
            }}
            
            .card-total {{
                font-size: 1.5rem;
            }}
            
            .metric-value {{
                font-size: 1.2rem;
            }}
            
            .filter-info-compact {{
                font-size: 0.8rem;
                padding: 6px 12px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )