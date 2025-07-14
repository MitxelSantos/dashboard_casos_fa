"""
Vista de mapas con sistema multi-modal y filtrado múltiple.
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

# ===== CONFIGURACIÓN DE COLORES MULTI-MODAL =====

def get_color_scheme_epidemiological(colors):
    """Esquema de colores epidemiológico."""
    return {
        "casos_epizootias_fallecidos": colors["danger"],      # Rojo intenso
        "solo_epizootias_positivas": colors["warning"],       # Naranja  
        "solo_casos_sin_fallecidos": colors["secondary"],     # Amarillo
        "solo_fallecidos": "#2C2C2C",                        # Gris oscuro
        "en_estudio": colors["info"],                         # Azul
        "sin_datos": "#E5E7EB"                               # Gris claro
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
    """Determina color según modo epidemiológico."""
    
    # Lógica según especificaciones
    if casos_count > 0 and epizootias_count > 0 and fallecidos_count > 0:
        return color_scheme["casos_epizootias_fallecidos"], "Casos + Epizootias + Fallecidos"
    elif positivas_count > 0 and casos_count == 0:
        return color_scheme["solo_epizootias_positivas"], "Solo epizootias positivas"
    elif casos_count > 0 and fallecidos_count == 0:
        return color_scheme["solo_casos_sin_fallecidos"], "Solo casos (sin fallecidos)"
    elif fallecidos_count > 0 and epizootias_count == 0:
        return color_scheme["solo_fallecidos"], "Solo fallecidos"
    elif en_estudio_count > 0:
        return color_scheme["en_estudio"], "En estudio"
    else:
        return color_scheme["sin_datos"], "Sin datos"

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
    """Vista principal de mapas MULTI-MODAL."""
    logger.info("🗺️ INICIANDO VISTA DE MAPAS MULTI-MODAL")
    
    # Aplicar CSS compacto
    apply_compact_maps_css(colors)
    
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

    # Información de filtrado
    active_filters = filters.get("active_filters", [])
    modo_mapa = filters.get("modo_mapa", "Epidemiológico")
    
    if active_filters:
        st.info(f"🎯 Vista: {modo_mapa} | Filtros: {' • '.join(active_filters[:2])}")

    # Layout compacto 70/30
    create_compact_layout(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered)

# ===== LAYOUT COMPACTO 70/30 =====

def create_compact_layout(casos, epizootias, geo_data, filters, colors, data_filtered):
    """Layout compacto 70% mapa - 30% tarjetas SIN SCROLL."""
    
    # Contenedor principal sin scroll
    st.markdown('<div class="compact-dashboard-container">', unsafe_allow_html=True)
    
    # Usar columnas con proporción 70/30
    col_mapa, col_info = st.columns([7, 3], gap="medium")
    
    with col_mapa:
        st.markdown('<div class="map-section-compact">', unsafe_allow_html=True)
        
        # Controles de navegación en la parte superior
        create_navigation_controls_compact(filters, colors)
        
        # Sistema de mapas principal
        create_map_system_compact(casos, epizootias, geo_data, filters, colors)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_info:
        st.markdown('<div class="info-section-compact">', unsafe_allow_html=True)
        
        # Tarjetas informativas compactas
        create_compact_information_cards(casos, epizootias, filters, colors)
        
        # Contadores de afectación (ya implementados en filters.py)
        contadores = filters.get("contadores")
        if contadores:
            # Los contadores ya se muestran en el sidebar, pero podemos agregar resumen aquí
            create_compact_summary_metrics(casos, epizootias, filters, colors)
        
        # Tarjeta de cobertura (placeholder por ahora)
        create_coverage_card_placeholder(filters, colors)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ===== SISTEMA DE MAPAS COMPACTO =====

def create_map_system_compact(casos, epizootias, geo_data, filters, colors):
    """Sistema de mapas compacto optimizado."""
    current_level = determine_map_level(filters)
    modo_mapa = filters.get("modo_mapa", "Epidemiológico")
    
    # Verificar datos geográficos
    has_municipios = 'municipios' in geo_data and not geo_data['municipios'].empty
    has_veredas = 'veredas' in geo_data and not geo_data['veredas'].empty
    
    # Crear mapa según nivel y modo
    if current_level == "vereda" and filters.get("modo") == "unico":
        # Vista específica de vereda
        create_vereda_specific_map(casos, epizootias, geo_data, filters, colors)
    elif current_level == "departamento" and has_municipios:
        if filters.get("modo") == "multiple":
            create_departmental_map_multiple(casos, epizootias, geo_data, filters, colors)
        else:
            create_departmental_map_compact(casos, epizootias, geo_data, filters, colors, modo_mapa)
    elif current_level == "municipio" and has_veredas:
        if filters.get("modo") == "multiple":
            create_municipal_map_multiple(casos, epizootias, geo_data, filters, colors)
        else:
            create_municipal_map_compact(casos, epizootias, geo_data, filters, colors, modo_mapa)
    else:
        show_fallback_summary_table(casos, epizootias, current_level, filters.get('municipio_display'))

def create_departmental_map_compact(casos, epizootias, geo_data, filters, colors, modo_mapa):
    """Mapa departamental compacto."""
    municipios = geo_data['municipios'].copy()
    logger.info(f"🏛️ Mapa departamental {modo_mapa}: {len(municipios)} municipios")
    
    # Preparar datos según modo
    if modo_mapa == "Epidemiológico":
        municipios_data = prepare_municipal_data_epidemiological(casos, epizootias, municipios, colors)
    else:
        municipios_data = prepare_municipal_data_coverage(municipios, colors)  # Placeholder
    
    # Configuración del mapa compacta
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
    add_municipios_to_map_multimodal(m, municipios_data, colors, modo_mapa)
    
    # Renderizar con tamaño compacto
    map_data = st_folium(
        m, 
        width=600,
        height=400,
        returned_objects=["last_object_clicked"],
        key=f"map_departamental_compact_{modo_mapa.lower()}"
    )
    
    # Procesar clicks
    handle_map_click_compact(map_data, municipios_data, "municipio", filters)

def create_municipal_map_compact(casos, epizootias, geo_data, filters, colors, modo_mapa):
    """Mapa municipal compacto."""
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
        veredas_data = prepare_vereda_data_epidemiological(casos, epizootias, veredas_municipio, municipio_selected, colors)
    else:
        veredas_data = prepare_vereda_data_coverage(veredas_municipio, municipio_selected, colors)  # Placeholder
    
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
    add_veredas_to_map_multimodal(m, veredas_data, colors, modo_mapa)
    
    # Renderizar
    map_data = st_folium(
        m, 
        width=600,
        height=400,
        returned_objects=["last_object_clicked"],
        key=f"map_municipal_compact_{modo_mapa.lower()}"
    )
    
    # Procesar clicks
    handle_map_click_compact(map_data, veredas_data, "vereda", filters)

def create_vereda_specific_map(casos, epizootias, geo_data, filters, colors):
    """Vista específica de vereda con mapa del croquis."""
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
    
    # Crear título específico
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']});
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 15px;
            font-weight: 700;
        ">
            📍 CROQUIS: {vereda_selected} - {municipio_selected}
        </div>
        """,
        unsafe_allow_html=True,
    )
    
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
    
    # Renderizar mapa
    st_folium(
        m, 
        width=600,
        height=350,
        returned_objects=[],  # No necesita clicks en vista específica
        key=f"map_vereda_especifica_{vereda_selected}"
    )
    
    # Mostrar datos específicos de la vereda
    show_vereda_specific_data(casos, epizootias, vereda_selected, municipio_selected, colors)

# ===== PREPARACIÓN DE DATOS MULTI-MODAL =====

def prepare_municipal_data_epidemiological(casos, epizootias, municipios, colors):
    """Prepara datos municipales para modo epidemiológico."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipios = municipios.copy()
    municipios['municipi_1_norm'] = municipios['municipi_1'].apply(normalize_name)
    
    # Obtener esquema de colores
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
    
    # Aplicar colores según modo epidemiológico
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

def prepare_municipal_data_coverage(municipios, colors):
    """Prepara datos municipales para modo cobertura (placeholder)."""
    municipios_data = municipios.copy()
    color_scheme = get_color_scheme_coverage(colors)
    
    # Por ahora, datos simulados de cobertura
    # TODO: Integrar con datos reales de cobertura cuando estén disponibles
    import random
    random.seed(42)  # Para resultados reproducibles
    
    for idx, row in municipios_data.iterrows():
        # Simular cobertura entre 40% y 98%
        cobertura_simulada = random.uniform(40, 98)
        
        color, descripcion = determine_feature_color_coverage(cobertura_simulada, color_scheme)
        
        municipios_data.loc[idx, 'color'] = color
        municipios_data.loc[idx, 'descripcion_color'] = descripcion
        municipios_data.loc[idx, 'cobertura'] = cobertura_simulada
    
    logger.info(f"💉 Datos municipales de cobertura preparados: {len(municipios_data)} municipios")
    return municipios_data

def prepare_vereda_data_epidemiological(casos, epizootias, veredas_gdf, municipio_actual, colors):
    """Prepara datos de veredas para modo epidemiológico."""
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
    
    # Aplicar colores
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

def prepare_vereda_data_coverage(veredas_gdf, municipio_actual, colors):
    """Prepara datos de veredas para modo cobertura (placeholder)."""
    veredas_data = veredas_gdf.copy()
    color_scheme = get_color_scheme_coverage(colors)
    
    # Datos simulados de cobertura por vereda
    import random
    random.seed(hash(municipio_actual) % 1000)  # Seed diferente por municipio
    
    for idx, row in veredas_data.iterrows():
        cobertura_simulada = random.uniform(35, 95)
        
        color, descripcion = determine_feature_color_coverage(cobertura_simulada, color_scheme)
        
        veredas_data.loc[idx, 'color'] = color
        veredas_data.loc[idx, 'descripcion_color'] = descripcion
        veredas_data.loc[idx, 'cobertura'] = cobertura_simulada
    
    logger.info(f"💉 Datos veredas cobertura {municipio_actual}: {len(veredas_data)} veredas")
    return veredas_data

# ===== FUNCIONES DE MAPA MULTI-MODAL =====

def add_municipios_to_map_multimodal(folium_map, municipios_data, colors, modo_mapa):
    """Agrega municipios al mapa con colores multi-modales."""
    for idx, row in municipios_data.iterrows():
        municipio_name = row['MpNombre']
        color = row['color']
        descripcion = row['descripcion_color']
        
        # Crear tooltip según modo
        if modo_mapa == "Epidemiológico":
            tooltip_text = create_municipio_tooltip_epidemiological(municipio_name, row, colors)
        else:
            tooltip_text = create_municipio_tooltip_coverage(municipio_name, row, colors)
        
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

def add_veredas_to_map_multimodal(folium_map, veredas_data, colors, modo_mapa):
    """Agrega veredas al mapa con colores multi-modales."""
    for idx, row in veredas_data.iterrows():
        vereda_name = row['vereda_nor']
        color = row['color']
        descripcion = row['descripcion_color']
        
        # Crear tooltip según modo
        if modo_mapa == "Epidemiológico":
            tooltip_text = create_vereda_tooltip_epidemiological(vereda_name, row, colors)
        else:
            tooltip_text = create_vereda_tooltip_coverage(vereda_name, row, colors)
        
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

def create_municipio_tooltip_epidemiological(name, row, colors):
    """Tooltip para municipio en modo epidemiológico."""
    return f"""
    <div style="font-family: Arial; padding: 10px; max-width: 250px;">
        <b style="color: {colors['primary']}; font-size: 1.1em;">{name}</b><br>
        <div style="margin: 8px 0; padding: 6px; background: #f8f9fa; border-radius: 4px;">
            🦠 Casos: {row.get('casos', 0)}<br>
            ⚰️ Fallecidos: {row.get('fallecidos', 0)}<br>
            🐒 Epizootias: {row.get('epizootias', 0)}<br>
            🔴 Positivas: {row.get('positivas', 0)}<br>
            🔵 En estudio: {row.get('en_estudio', 0)}
        </div>
        <div style="color: {colors['info']}; font-size: 0.9em;">
            📊 {row.get('descripcion_color', 'Sin clasificar')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
    </div>
    """

def create_municipio_tooltip_coverage(name, row, colors):
    """Tooltip para municipio en modo cobertura."""
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

def create_vereda_tooltip_epidemiological(name, row, colors):
    """Tooltip para vereda en modo epidemiológico."""
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

def create_vereda_tooltip_coverage(name, row, colors):
    """Tooltip para vereda en modo cobertura."""
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

# ===== TARJETAS INFORMATIVAS COMPACTAS =====

def create_compact_information_cards(casos, epizootias, filters, colors):
    """Tarjetas informativas súper compactas."""
    logger.info("🏷️ Creando tarjetas compactas")
    
    metrics = calculate_basic_metrics(casos, epizootias)
    
    # Tarjeta de casos compacta
    create_compact_cases_card(metrics, filters, colors)
    
    # Tarjeta de epizootias compacta  
    create_compact_epizootias_card(metrics, filters, colors)

def create_compact_cases_card(metrics, filters, colors):
    """Tarjeta de casos súper compacta."""
    total_casos = metrics["total_casos"]
    vivos = metrics["vivos"]
    fallecidos = metrics["fallecidos"]
    letalidad = metrics["letalidad"]
    
    filter_context = get_filter_context_compact(filters)
    
    st.markdown(
        f"""
        <div class="compact-card cases-card">
            <div class="compact-header">
                <span class="compact-icon">🦠</span>
                <div class="compact-title">
                    <div class="title-text">CASOS</div>
                    <div class="subtitle-text">{filter_context}</div>
                </div>
            </div>
            <div class="compact-metrics">
                <div class="metric-row">
                    <div class="metric-item">
                        <div class="metric-num primary">{total_casos}</div>
                        <div class="metric-lbl">Total</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-num success">{vivos}</div>
                        <div class="metric-lbl">Vivos</div>
                    </div>
                </div>
                <div class="metric-row">
                    <div class="metric-item">
                        <div class="metric-num danger">{fallecidos}</div>
                        <div class="metric-lbl">Fallecidos</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-num warning">{letalidad:.1f}%</div>
                        <div class="metric-lbl">Letalidad</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def create_compact_epizootias_card(metrics, filters, colors):
    """Tarjeta de epizootias súper compacta."""
    total_epizootias = metrics["total_epizootias"]
    positivas = metrics["epizootias_positivas"]
    en_estudio = metrics["epizootias_en_estudio"]
    
    filter_context = get_filter_context_compact(filters)
    
    st.markdown(
        f"""
        <div class="compact-card epizootias-card">
            <div class="compact-header">
                <span class="compact-icon">🐒</span>
                <div class="compact-title">
                    <div class="title-text">EPIZOOTIAS</div>
                    <div class="subtitle-text">{filter_context}</div>
                </div>
            </div>
            <div class="compact-metrics">
                <div class="metric-row">
                    <div class="metric-item">
                        <div class="metric-num warning">{total_epizootias}</div>
                        <div class="metric-lbl">Total</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-num danger">{positivas}</div>
                        <div class="metric-lbl">Positivas</div>
                    </div>
                </div>
                <div class="metric-row single-metric">
                    <div class="metric-item">
                        <div class="metric-num info">{en_estudio}</div>
                        <div class="metric-lbl">En Estudio</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def create_coverage_card_placeholder(filters, colors):
    """Tarjeta de cobertura placeholder."""
    # Datos simulados por ahora
    cobertura_simulada = 78.5
    vacunas_aplicadas = 1247
    no_vacunados = 342
    
    filter_context = get_filter_context_compact(filters)
    
    st.markdown(
        f"""
        <div class="compact-card coverage-card">
            <div class="compact-header">
                <span class="compact-icon">💉</span>
                <div class="compact-title">
                    <div class="title-text">COBERTURA</div>
                    <div class="subtitle-text">{filter_context}</div>
                </div>
            </div>
            <div class="compact-metrics">
                <div class="metric-row">
                    <div class="metric-item">
                        <div class="metric-num success">{cobertura_simulada:.1f}%</div>
                        <div class="metric-lbl">Cobertura</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-num info">{vacunas_aplicadas}</div>
                        <div class="metric-lbl">Vacunados</div>
                    </div>
                </div>
                <div class="metric-row single-metric">
                    <div class="metric-item">
                        <div class="metric-num warning">{no_vacunados}</div>
                        <div class="metric-lbl">No Vacunados</div>
                    </div>
                </div>
            </div>
            <div class="card-note">
                📝 Incluye no vacunados por contradicación médica, religión u otras razones
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def create_compact_summary_metrics(casos, epizootias, filters, colors):
    """Métricas de resumen compactas adicionales."""
    # Métricas geográficas rápidas
    municipios_unicos = casos["municipio"].nunique() if not casos.empty and "municipio" in casos.columns else 0
    veredas_unicas = casos["vereda"].nunique() if not casos.empty and "vereda" in casos.columns else 0
    
    st.markdown(
        f"""
        <div class="compact-summary">
            <div class="summary-title">📊 Resumen Geográfico</div>
            <div class="summary-items">
                <span class="summary-item">📍 {municipios_unicos} municipios</span>
                <span class="summary-item">🏘️ {veredas_unicas} veredas</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===== CONTROLES Y NAVEGACIÓN COMPACTOS =====

def create_navigation_controls_compact(filters, colors):
    """Controles de navegación compactos."""
    current_level = determine_map_level(filters)
    modo_mapa = filters.get("modo_mapa", "Epidemiológico")
    
    # Indicador de modo y nivel en una línea
    level_info = {
        "departamento": "🏛️ Tolima",
        "municipio": f"🏘️ {filters.get('municipio_display', 'Municipio')}",
        "vereda": f"📍 {filters.get('vereda_display', 'Vereda')}"
    }
    
    current_level_text = level_info.get(current_level, "🗺️ Vista")
    
    # Encabezado compacto con modo y navegación
    st.markdown(
        f"""
        <div class="compact-nav-header">
            <div class="nav-mode">🎨 {modo_mapa}</div>
            <div class="nav-level">{current_level_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Botones de navegación horizontales
    if current_level != "departamento":
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("🏛️ Tolima", key="nav_tolima_compact", use_container_width=True):
                reset_location_filters()
                st.rerun()
        
        with col2:
            if current_level == "vereda":
                municipio_name = filters.get('municipio_display', 'Municipio')
                if st.button(f"🏘️ {municipio_name[:8]}...", key="nav_municipio_compact", use_container_width=True):
                    st.session_state['vereda_filter'] = 'Todas'
                    st.rerun()
        
        with col3:
            # Placeholder para futuras funciones
            pass

# ===== FUNCIONES DE APOYO =====

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

# ===== MAPAS MÚLTIPLES (FUNCIONES PLACEHOLDER) =====

def create_departmental_map_multiple(casos, epizootias, geo_data, filters, colors):
    """Mapa departamental con selección múltiple."""
    municipios_seleccionados = filters.get("municipios_seleccionados", [])
    
    st.info(f"🗂️ Vista múltiple: {len(municipios_seleccionados)} municipios seleccionados")
    
    # Por ahora, usar lógica estándar pero resaltar municipios seleccionados
    municipios = geo_data['municipios'].copy()
    municipios_data = prepare_municipal_data_epidemiological(casos, epizootias, municipios, colors)
    
    # Marcar municipios seleccionados
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipios_norm = [normalize_name(m) for m in municipios_seleccionados]
    municipios_data['seleccionado'] = municipios_data['municipi_1'].apply(normalize_name).isin(municipios_norm)
    
    # Crear mapa (lógica similar a create_departmental_map_compact)
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
    
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    
    # Agregar municipios con indicador de selección
    for idx, row in municipios_data.iterrows():
        style_params = {
            'fillColor': row['color'],
            'color': colors['secondary'] if row['seleccionado'] else colors['primary'],
            'weight': 4 if row['seleccionado'] else 2,
            'fillOpacity': 0.8 if row['seleccionado'] else 0.6,
            'opacity': 1
        }
        
        tooltip_text = create_municipio_tooltip_epidemiological(row['MpNombre'], row, colors)
        if row['seleccionado']:
            tooltip_text = f"✅ SELECCIONADO<br>{tooltip_text}"
        
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, **kwargs: kwargs,
            style_kwds=style_params,
            tooltip=folium.Tooltip(tooltip_text, sticky=True),
        ).add_to(m)
    
    # Renderizar
    map_data = st_folium(
        m, 
        width=600,
        height=400,
        returned_objects=["last_object_clicked"],
        key="map_departamental_multiple"
    )
    
    # Procesar clicks (añadir/quitar de selección)
    handle_map_click_multiple(map_data, municipios_data, "municipio", filters)

def create_municipal_map_multiple(casos, epizootias, geo_data, filters, colors):
    """Mapa municipal con selección múltiple de veredas."""
    veredas_seleccionadas = filters.get("veredas_seleccionadas", [])
    municipios_seleccionados = filters.get("municipios_seleccionados", [])
    
    st.info(f"🗂️ Vista múltiple: {len(veredas_seleccionadas)} veredas en {len(municipios_seleccionados)} municipios")
    
    # Crear vista combinada de veredas de múltiples municipios
    veredas = geo_data['veredas'].copy()
    
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipios_norm = [normalize_name(m) for m in municipios_seleccionados]
    veredas_filtradas = veredas[veredas['municipi_1'].apply(normalize_name).isin(municipios_norm)]
    
    if veredas_filtradas.empty:
        st.warning("No se encontraron veredas para los municipios seleccionados")
        return
    
    # Preparar datos (usando primer municipio como referencia)
    primer_municipio = municipios_seleccionados[0] if municipios_seleccionados else "IBAGUE"
    veredas_data = prepare_vereda_data_epidemiological(casos, epizootias, veredas_filtradas, primer_municipio, colors)
    
    # Marcar veredas seleccionadas
    veredas_norm = [normalize_name(v) for v in veredas_seleccionadas]
    veredas_data['seleccionada'] = veredas_data['vereda_nor'].apply(normalize_name).isin(veredas_norm)
    
    # Crear mapa
    bounds = veredas_filtradas.total_bounds
    center_lat, center_lon = (bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=9,
        tiles='CartoDB positron',
        attributionControl=False,
        zoom_control=True,
        scrollWheelZoom=True
    )
    
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    
    # Agregar veredas con indicador de selección
    for idx, row in veredas_data.iterrows():
        style_params = {
            'fillColor': row['color'],
            'color': colors['secondary'] if row['seleccionada'] else colors['accent'],
            'weight': 3 if row['seleccionada'] else 1.5,
            'fillOpacity': 0.7 if row['seleccionada'] else 0.5,
            'opacity': 1
        }
        
        tooltip_text = create_vereda_tooltip_epidemiological(row['vereda_nor'], row, colors)
        if row['seleccionada']:
            tooltip_text = f"✅ SELECCIONADA<br>{tooltip_text}"
        
        try:
            folium.GeoJson(
                row['geometry'],
                style_function=lambda x, **kwargs: kwargs,
                style_kwds=style_params,
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            ).add_to(m)
        except Exception as e:
            logger.warning(f"⚠️ Error agregando vereda {row['vereda_nor']}: {str(e)}")
    
    # Renderizar
    map_data = st_folium(
        m, 
        width=600,
        height=400,
        returned_objects=["last_object_clicked"],
        key="map_municipal_multiple"
    )
    
    # Procesar clicks
    handle_map_click_multiple(map_data, veredas_data, "vereda", filters)

# ===== MANEJO DE CLICKS =====

def handle_map_click_compact(map_data, features_data, feature_type, filters):
    """Manejo de clicks para mapas compactos."""
    if not map_data or not map_data.get('last_object_clicked'):
        return
    
    try:
        clicked_object = map_data['last_object_clicked']
        
        if isinstance(clicked_object, dict):
            clicked_lat = clicked_object.get('lat')
            clicked_lng = clicked_object.get('lng')
            
            if clicked_lat and clicked_lng:
                feature_clicked = find_closest_feature_compact(clicked_lat, clicked_lng, features_data, feature_type)
                
                if feature_clicked:
                    apply_feature_filter_compact(feature_clicked, feature_type, filters)
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"❌ Error procesando clic compacto: {str(e)}")
        st.warning("⚠️ Error procesando clic en el mapa")

def handle_map_click_multiple(map_data, features_data, feature_type, filters):
    """Manejo de clicks para selección múltiple."""
    if not map_data or not map_data.get('last_object_clicked'):
        return
    
    try:
        clicked_object = map_data['last_object_clicked']
        
        if isinstance(clicked_object, dict):
            clicked_lat = clicked_object.get('lat')
            clicked_lng = clicked_object.get('lng')
            
            if clicked_lat and clicked_lng:
                feature_clicked = find_closest_feature_compact(clicked_lat, clicked_lng, features_data, feature_type)
                
                if feature_clicked:
                    toggle_feature_selection(feature_clicked, feature_type, filters)
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"❌ Error procesando clic múltiple: {str(e)}")
        st.warning("⚠️ Error procesando clic en el mapa")

def find_closest_feature_compact(lat, lng, features_data, feature_type):
    """Encuentra el feature más cercano."""
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

def apply_feature_filter_compact(feature_name, feature_type, filters):
    """Aplica filtro según el tipo de feature."""
    if feature_type == "municipio":
        if filters.get("modo") == "multiple":
            # En modo múltiple, agregar a la selección
            current_selection = st.session_state.get('municipios_multiselect', [])
            if feature_name not in current_selection:
                current_selection.append(feature_name)
                st.session_state['municipios_multiselect'] = current_selection
            st.success(f"✅ Agregado: **{feature_name}**")
        else:
            # En modo único, filtrar normalmente
            st.session_state['municipio_filter'] = feature_name
            st.session_state['vereda_filter'] = 'Todas'
            st.success(f"✅ Filtrado por municipio: **{feature_name}**")
    
    elif feature_type == "vereda":
        if filters.get("modo") == "multiple":
            # En modo múltiple, agregar a la selección
            current_selection = st.session_state.get('veredas_multiselect', [])
            if feature_name not in current_selection:
                current_selection.append(feature_name)
                st.session_state['veredas_multiselect'] = current_selection
            st.success(f"✅ Agregada: **{feature_name}**")
        else:
            # En modo único, filtrar normalmente
            st.session_state['vereda_filter'] = feature_name
            st.success(f"✅ Filtrado por vereda: **{feature_name}**")

def toggle_feature_selection(feature_name, feature_type, filters):
    """Alterna selección de feature en modo múltiple."""
    if feature_type == "municipio":
        session_key = 'municipios_multiselect'
    else:
        session_key = 'veredas_multiselect'
    
    current_selection = st.session_state.get(session_key, [])
    
    if feature_name in current_selection:
        current_selection.remove(feature_name)
        st.info(f"➖ Removido: **{feature_name}**")
    else:
        current_selection.append(feature_name)
        st.success(f"➕ Agregado: **{feature_name}**")
    
    st.session_state[session_key] = current_selection

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

def reset_location_filters():
    if "municipio_filter" in st.session_state:
        st.session_state.municipio_filter = "Todos"
    if "vereda_filter" in st.session_state:
        st.session_state.vereda_filter = "Todas"
    if "municipios_multiselect" in st.session_state:
        st.session_state.municipios_multiselect = []
    if "veredas_multiselect" in st.session_state:
        st.session_state.veredas_multiselect = []

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

# ===== CSS COMPACTO =====

def apply_compact_maps_css(colors):
    """CSS para layout compacto sin scroll."""
    st.markdown(
        f"""
        <style>
        /* =============== LAYOUT COMPACTO SIN SCROLL =============== */
        
        .compact-dashboard-container {{
            width: 100% !important;
            height: calc(100vh - 200px) !important;
            max-height: calc(100vh - 200px) !important;
            overflow: hidden !important;
            display: flex !important;
            gap: 20px !important;
        }}
        
        .map-section-compact {{
            flex: 0 0 70% !important;
            height: 100% !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
        }}
        
        .info-section-compact {{
            flex: 0 0 30% !important;
            height: 100% !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }}
        
        /* =============== NAVEGACIÓN COMPACTA =============== */
        
        .compact-nav-header {{
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']}) !important;
            color: white !important;
            padding: 10px 20px !important;
            border-radius: 10px !important;
            margin-bottom: 15px !important;
            font-weight: 600 !important;
        }}
        
        .nav-mode {{
            font-size: 0.9rem !important;
            opacity: 0.9 !important;
        }}
        
        .nav-level {{
            font-size: 1rem !important;
            font-weight: 700 !important;
        }}
        
        /* =============== TARJETAS COMPACTAS =============== */
        
        .compact-card {{
            background: linear-gradient(135deg, white, #f8fafc) !important;
            border-radius: 12px !important;
            margin-bottom: 15px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            overflow: hidden !important;
            border-left: 4px solid {colors['primary']} !important;
            transition: all 0.3s ease !important;
        }}
        
        .compact-card:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15) !important;
        }}
        
        .compact-header {{
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
            padding: 15px !important;
            background: linear-gradient(135deg, {colors['light']}, #ffffff) !important;
            border-bottom: 1px solid #e2e8f0 !important;
        }}
        
        .compact-icon {{
            font-size: 1.8rem !important;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2)) !important;
        }}
        
        .compact-title {{
            flex: 1 !important;
        }}
        
        .title-text {{
            font-size: 1rem !important;
            font-weight: 800 !important;
            color: {colors['primary']} !important;
            margin: 0 !important;
        }}
        
        .subtitle-text {{
            font-size: 0.75rem !important;
            color: {colors['accent']} !important;
            font-weight: 600 !important;
            margin: 2px 0 0 0 !important;
        }}
        
        .compact-metrics {{
            padding: 15px !important;
        }}
        
        .metric-row {{
            display: flex !important;
            gap: 10px !important;
            margin-bottom: 10px !important;
        }}
        
        .metric-row.single-metric {{
            justify-content: center !important;
        }}
        
        .metric-item {{
            flex: 1 !important;
            text-align: center !important;
            background: #f8fafc !important;
            padding: 8px !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }}
        
        .metric-item:hover {{
            background: #e2e8f0 !important;
            transform: scale(1.05) !important;
        }}
        
        .metric-num {{
            font-size: 1.2rem !important;
            font-weight: 800 !important;
            margin-bottom: 2px !important;
        }}
        
        .metric-num.primary {{ color: {colors['primary']} !important; }}
        .metric-num.success {{ color: {colors['success']} !important; }}
        .metric-num.danger {{ color: {colors['danger']} !important; }}
        .metric-num.warning {{ color: {colors['warning']} !important; }}
        .metric-num.info {{ color: {colors['info']} !important; }}
        
        .metric-lbl {{
            font-size: 0.7rem !important;
            color: #64748b !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }}
        
        /* =============== TARJETA DE COBERTURA =============== */
        
        .coverage-card {{
            border-left-color: {colors['success']} !important;
        }}
        
        .coverage-card .compact-header {{
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe) !important;
        }}
        
        .card-note {{
            padding: 10px 15px !important;
            background: #f1f5f9 !important;
            font-size: 0.7rem !important;
            color: {colors['accent']} !important;
            border-top: 1px solid #e2e8f0 !important;
            margin: 0 !important;
        }}
        
        /* =============== RESUMEN COMPACTO =============== */
        
        .compact-summary {{
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']}) !important;
            color: white !important;
            padding: 12px !important;
            border-radius: 10px !important;
            margin-bottom: 15px !important;
        }}
        
        .summary-title {{
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            margin-bottom: 8px !important;
            text-align: center !important;
        }}
        
        .summary-items {{
            display: flex !important;
            justify-content: space-around !important;
            flex-wrap: wrap !important;
        }}
        
        .summary-item {{
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            opacity: 0.95 !important;
        }}
        
        /* =============== BOTONES COMPACTOS =============== */
        
        .stButton > button {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']}) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-weight: 600 !important;
            font-size: 0.8rem !important;
            transition: all 0.3s ease !important;
        }}
        
        .stButton > button:hover {{
            background: linear-gradient(135deg, {colors['accent']}, {colors['primary']}) !important;
            transform: translateY(-1px) !important;
        }}
        
        /* =============== RESPONSIVE COMPACTO =============== */
        
        @media (max-width: 1200px) {{
            .compact-dashboard-container {{
                flex-direction: column !important;
                height: auto !important;
                max-height: none !important;
            }}
            
            .map-section-compact,
            .info-section-compact {{
                flex: 1 1 auto !important;
                height: auto !important;
            }}
            
            .info-section-compact {{
                overflow-y: visible !important;
            }}
        }}
        
        @media (max-width: 768px) {{
            .compact-card {{
                margin-bottom: 10px !important;
            }}
            
            .compact-header {{
                padding: 12px !important;
            }}
            
            .compact-metrics {{
                padding: 12px !important;
            }}
            
            .metric-row {{
                flex-direction: column !important;
                gap: 8px !important;
            }}
            
            .metric-num {{
                font-size: 1rem !important;
            }}
            
            .compact-nav-header {{
                flex-direction: column !important;
                gap: 5px !important;
                text-align: center !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )