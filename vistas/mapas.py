"""
Vista de mapas.
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta

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
        "casos_epizootias_fallecidos": colors["danger"],      # 🔴 Rojo: Casos + Epizootias + Fallecidos
        "solo_casos": colors["warning"],                      # 🟠 Naranja: Solo casos  
        "solo_epizootias": colors["secondary"],               # 🟡 Amarillo: Solo epizootias
        "sin_datos": "#E5E7EB",                              # ⚪ Gris claro: Sin datos
        "seleccionado": colors["primary"],                    # 🔵 Azul: Seleccionado
        "no_seleccionado": "#F3F4F6"                         # ⚪ Gris muy claro: No seleccionado
    }

def get_color_scheme_coverage(colors):
    """Esquema de colores por cobertura de vacunación."""
    return {
        "cobertura_alta": colors["success"],      # Verde intenso: >95%
        "cobertura_buena": colors["secondary"],   # Amarillo: 80-95%
        "cobertura_regular": colors["warning"],   # Naranja: 60-80%
        "cobertura_baja": colors["danger"],       # Rojo: <60%
        "sin_datos": "#E5E7EB",                  # Gris
        "seleccionado": colors["primary"],        # Azul: Seleccionado
        "no_seleccionado": "#F3F4F6"            # Gris muy claro: No seleccionado
    }

def determine_feature_color_epidemiological(casos_count, epizootias_count, fallecidos_count, positivas_count, en_estudio_count, color_scheme):
    """Determina color según modo epidemiológico."""
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
    """Vista principal de mapas."""
    logger.info("🗺️ INICIANDO VISTA DE MAPAS")
    
    # Aplicar CSS compacto
    apply_maps_css_full_responsive(colors)
    
    # Verificar datos filtrados
    casos_filtrados = data_filtered["casos"]
    epizootias_filtradas = data_filtered["epizootias"]
    
    verify_filtered_data_usage(casos_filtrados, "vista_mapas_optimizada")
    verify_filtered_data_usage(epizootias_filtradas, "vista_mapas_optimizada")

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
        st.markdown(
            f"""
            <div class="filter-info-compact">
                🎯 Vista: <strong>{modo_mapa}</strong> | Filtros: <strong>{' • '.join(active_filters[:2])}</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Layout compacto con mapa al 100%
    create_optimized_layout(casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered)

# ===== LAYOUT =====

def create_optimized_layout(casos, epizootias, geo_data, filters, colors, data_filtered):
    """Layout."""
    
    # Usar columnas con proporción 75/25
    col_mapa, col_info = st.columns([3, 1], gap="medium")
    
    with col_mapa:
        # Sistema de mapas optimizado
        create_map_system_optimized(casos, epizootias, geo_data, filters, colors)
    
    with col_info:
        # Tarjetas informativas optimizadas
        create_information_cards_optimized(casos, epizootias, filters, colors)

def create_map_system_optimized(casos, epizootias, geo_data, filters, colors):
    """Sistema de mapas."""
    current_level = determine_map_level(filters)
    modo_mapa = filters.get("modo_mapa", "Epidemiológico")
    
    # Verificar datos geográficos
    has_municipios = 'municipios' in geo_data and not geo_data['municipios'].empty
    has_veredas = 'veredas' in geo_data and not geo_data['veredas'].empty
    
    # Crear mapa según nivel y modo
    if current_level == "vereda" and filters.get("modo") == "unico":
        create_vereda_specific_map(casos, epizootias, geo_data, filters, colors)
    elif current_level == "departamento":
        if filters.get("modo") == "multiple":
            create_departmental_map_multiple(casos, epizootias, geo_data, filters, colors)
        else:
            create_departmental_map_single(casos, epizootias, geo_data, filters, colors, modo_mapa)
    elif current_level == "municipio":
        if filters.get("modo") == "multiple":
            create_municipal_map_multiple(casos, epizootias, geo_data, filters, colors)
        else:
            create_municipal_map_single(casos, epizootias, geo_data, filters, colors, modo_mapa)
    else:
        show_fallback_summary(casos, epizootias, current_level, filters.get('municipio_display'))

# ===== MAPAS DEPARTAMENTALES =====

def create_departmental_map_single(casos, epizootias, geo_data, filters, colors, modo_mapa):
    """Mapa departamental."""
    municipios = geo_data['municipios'].copy()
    logger.info(f"🏛️ Mapa departamental único {modo_mapa}: {len(municipios)} municipios")
    
    # Preparar datos según modo
    if modo_mapa == "Epidemiológico":
        municipios_data = prepare_municipal_data_epidemiological(casos, epizootias, municipios, colors)
    else:
        municipios_data = prepare_municipal_data_coverage(municipios, colors)
    
    # Crear y mostrar mapa
    m = create_folium_map(municipios_data, zoom_start=8)
    add_municipios_to_map(m, municipios_data, colors, modo_mapa)
    
    # Renderizar
    map_data = st_folium(
        m, 
        width="100%",
        height=600,
        returned_objects=["last_object_clicked"],
        key=f"map_dept_single_{modo_mapa.lower()}"
    )
    
    # Procesar clicks
    handle_map_click(map_data, municipios_data, "municipio", filters, casos, epizootias)
    
def prepare_municipal_data_epidemiological_multiple(casos, epizootias, municipios, municipios_seleccionados, colors):
    """Prepara datos municipales para modo múltiple epidemiológico."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipios = municipios.copy()
    municipios['municipi_1_norm'] = municipios['municipi_1'].apply(normalize_name)
    municipios_sel_norm = [normalize_name(m) for m in municipios_seleccionados]
    
    # Obtener esquema de colores
    color_scheme = get_color_scheme_epidemiological(colors)
    
    # Contadores por municipio (igual que antes)
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
    
    # Aplicar colores con diferenciación de selección
    municipios_data = municipios.copy()
    
    for idx, row in municipios_data.iterrows():
        municipio_norm = row['municipi_1_norm']
        es_seleccionado = municipio_norm in municipios_sel_norm
        
        contadores = contadores_municipios.get(municipio_norm, {
            'casos': 0, 'fallecidos': 0, 'epizootias': 0, 'positivas': 0, 'en_estudio': 0
        })
        
        if es_seleccionado:
            # Municipio seleccionado: usar color normal epidemiológico
            color, descripcion = determine_feature_color_epidemiological(
                contadores['casos'],
                contadores['epizootias'], 
                contadores['fallecidos'],
                contadores['en_estudio'],
                color_scheme
            )
        else:
            # Municipio no seleccionado: usar color gris claro
            color = color_scheme["no_seleccionado"]
            descripcion = "No seleccionado"
        
        municipios_data.loc[idx, 'color'] = color
        municipios_data.loc[idx, 'descripcion_color'] = descripcion
        municipios_data.loc[idx, 'es_seleccionado'] = es_seleccionado
        
        # Agregar contadores como columnas
        for key, value in contadores.items():
            municipios_data.loc[idx, key] = value
    
    logger.info(f"🎨 Datos municipales múltiples preparados: {len(municipios_sel_norm)} seleccionados de {len(municipios_data)}")
    return municipios_data

def prepare_municipal_data_coverage_multiple(municipios, municipios_seleccionados, colors):
    """Prepara datos municipales para modo múltiple cobertura."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipios_data = municipios.copy()
    municipios_data['municipi_1_norm'] = municipios_data['municipi_1'].apply(normalize_name)
    municipios_sel_norm = [normalize_name(m) for m in municipios_seleccionados]
    
    color_scheme = get_color_scheme_coverage(colors)
    
    # Datos de cobertura manual
    COBERTURAS_MUNICIPIOS = {
        'IBAGUE': 85.2, 'ALPUJARRA': 78.5, 'ALVARADO': 92.1, 'AMBALEMA': 67.8,
        'ANZOATEGUI': 73.4, 'ARMERO': 69.2, 'ATACO': 81.7, 'CAJAMARCA': 88.3,
        'CARMEN DE APICALA': 74.9, 'CASABIANCA': 82.6, 'CHAPARRAL': 79.1, 'COELLO': 86.4,
        'COYAIMA': 71.3, 'CUNDAY': 77.8, 'DOLORES': 65.7, 'ESPINAL': 89.5,
        'FALAN': 83.2, 'FLANDES': 91.8, 'FRESNO': 76.4, 'GUAMO': 84.1,
        'HERVEO': 72.9, 'HONDA': 87.6, 'ICONONZO': 75.3, 'LERIDA': 80.7,
        'LIBANO': 85.9, 'MARIQUITA': 88.2, 'MELGAR': 82.4, 'MURILLO': 70.6,
        'NATAGAIMA': 68.9, 'ORTEGA': 79.8, 'PALOCABILDO': 74.2, 'PIEDRAS': 86.7,
        'PLANADAS': 77.1, 'PRADO': 83.5, 'PURIFICACION': 81.3, 'RIOBLANCO': 69.8,
        'RONCESVALLES': 75.6, 'ROVIRA': 84.8, 'SALDAÑA': 87.3, 'SAN ANTONIO': 73.7,
        'SAN LUIS': 78.9, 'SANTA ISABEL': 80.4, 'SUAREZ': 76.8, 'VALLE DE SAN JUAN': 85.6,
        'VENADILLO': 89.1, 'VILLAHERMOSA': 72.2, 'VILLARRICA': 81.9
    }
    
    for idx, row in municipios_data.iterrows():
        municipio_name = row.get('MpNombre', row.get('municipi_1', 'DESCONOCIDO'))
        municipio_norm = row['municipi_1_norm']
        es_seleccionado = municipio_norm in municipios_sel_norm
        
        cobertura_value = COBERTURAS_MUNICIPIOS.get(municipio_name, 75.0)
        
        if es_seleccionado:
            # Municipio seleccionado: usar color normal de cobertura
            color, descripcion = determine_feature_color_coverage(cobertura_value, color_scheme)
        else:
            # Municipio no seleccionado: usar color gris claro
            color = color_scheme["no_seleccionado"]
            descripcion = "No seleccionado"
        
        municipios_data.loc[idx, 'color'] = color
        municipios_data.loc[idx, 'descripcion_color'] = descripcion
        municipios_data.loc[idx, 'es_seleccionado'] = es_seleccionado
        municipios_data.loc[idx, 'cobertura'] = cobertura_value
    
    logger.info(f"💉 Datos municipales cobertura múltiple: {len(municipios_sel_norm)} seleccionados")
    return municipios_data

def create_departmental_map_multiple(casos, epizootias, geo_data, filters, colors):
    """Mapa departamental múltiple."""
    logger.info("🗂️ Creando mapa múltiple departamental OPTIMIZADO")
    
    municipios = geo_data['municipios'].copy()
    municipios_seleccionados = filters.get("municipios_seleccionados", [])
    modo_mapa = filters.get("modo_mapa", "Epidemiológico")
    
    # Preparar datos con diferenciación de selección
    if modo_mapa == "Epidemiológico":
        municipios_data = prepare_municipal_data_epidemiological_multiple(casos, epizootias, municipios, municipios_seleccionados, colors)
    else:
        municipios_data = prepare_municipal_data_coverage_multiple(municipios, municipios_seleccionados, colors)
    
    # Crear y mostrar mapa
    m = create_folium_map(municipios_data, zoom_start=8)
    add_municipios_to_map_differentiated(m, municipios_data, municipios_seleccionados, colors, modo_mapa)
    
    # Renderizar
    map_data = st_folium(
        m, 
        width="100%",
        height=600,
        returned_objects=["last_object_clicked"],
        key=f"map_dept_multiple_{modo_mapa.lower()}"
    )
    
    # Procesar clicks múltiples
    handle_map_click_multiple(map_data, municipios_data, "municipio", filters, casos, epizootias)

# ===== MAPAS MUNICIPALES =====

def create_municipal_map_single(casos, epizootias, geo_data, filters, colors, modo_mapa):
    """Mapa municipal único."""
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
        veredas_data = prepare_vereda_data_coverage(veredas_municipio, municipio_selected, colors)
    
    # Crear y mostrar mapa
    m = create_folium_map(veredas_data, zoom_start=10)
    add_veredas_to_map(m, veredas_data, colors, modo_mapa)
    
    # Renderizar
    map_data = st_folium(
        m, 
        width="100%",
        height=600,
        returned_objects=["last_object_clicked"],
        key=f"map_mun_single_{modo_mapa.lower()}"
    )
    
    # Procesar clicks
    handle_map_click(map_data, veredas_data, "vereda", filters, casos, epizootias)

def prepare_veredas_data_epidemiological_multiple(casos, epizootias, veredas_gdf, municipios_seleccionados, veredas_seleccionadas, colors):
    """Prepara datos de veredas para modo múltiple epidemiológico."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    veredas_gdf = veredas_gdf.copy()
    veredas_gdf['vereda_nor_norm'] = veredas_gdf['vereda_nor'].apply(normalize_name)
    veredas_sel_norm = [normalize_name(v) for v in veredas_seleccionadas]
    
    color_scheme = get_color_scheme_epidemiological(colors)
    
    # Contadores por vereda
    contadores_veredas = {}
    
    if not casos.empty and 'vereda' in casos.columns and 'municipio' in casos.columns:
        casos_norm = casos.copy()
        casos_norm['vereda_norm'] = casos_norm['vereda'].apply(normalize_name)
        casos_norm['municipio_norm'] = casos_norm['municipio'].apply(normalize_name)
        
        casos_municipios = casos_norm[casos_norm['municipio_norm'].isin([normalize_name(m) for m in municipios_seleccionados])]
        
        for vereda_norm in veredas_gdf['vereda_nor_norm'].unique():
            casos_ver = casos_municipios[casos_municipios['vereda_norm'] == vereda_norm]
            fallecidos_ver = casos_ver[casos_ver['condicion_final'] == 'Fallecido'] if 'condicion_final' in casos_ver.columns else pd.DataFrame()
            
            contadores_veredas[vereda_norm] = {
                'casos': len(casos_ver),
                'fallecidos': len(fallecidos_ver)
            }
    
    if not epizootias.empty and 'vereda' in epizootias.columns and 'municipio' in epizootias.columns:
        epi_norm = epizootias.copy()
        epi_norm['vereda_norm'] = epi_norm['vereda'].apply(normalize_name)
        epi_norm['municipio_norm'] = epi_norm['municipio'].apply(normalize_name)
        
        epi_municipios = epi_norm[epi_norm['municipio_norm'].isin([normalize_name(m) for m in municipios_seleccionados])]
        
        for vereda_norm in veredas_gdf['vereda_nor_norm'].unique():
            if vereda_norm not in contadores_veredas:
                contadores_veredas[vereda_norm] = {'casos': 0, 'fallecidos': 0}
            
            epi_ver = epi_municipios[epi_municipios['vereda_norm'] == vereda_norm]
            positivas_ver = epi_ver[epi_ver['descripcion'] == 'POSITIVO FA'] if 'descripcion' in epi_ver.columns else pd.DataFrame()
            en_estudio_ver = epi_ver[epi_ver['descripcion'] == 'EN ESTUDIO'] if 'descripcion' in epi_ver.columns else pd.DataFrame()
            
            contadores_veredas[vereda_norm].update({
                'epizootias': len(epi_ver),
                'positivas': len(positivas_ver),
                'en_estudio': len(en_estudio_ver)
            })
    
    # Aplicar colores con diferenciación
    veredas_data = veredas_gdf.copy()
    
    for idx, row in veredas_data.iterrows():
        vereda_norm = row['vereda_nor_norm']
        es_seleccionada = vereda_norm in veredas_sel_norm
        
        contadores = contadores_veredas.get(vereda_norm, {
            'casos': 0, 'fallecidos': 0, 'epizootias': 0, 'positivas': 0, 'en_estudio': 0
        })
        
        if es_seleccionada:
            # Vereda seleccionada: usar color normal epidemiológico
            color, descripcion = determine_feature_color_epidemiological(
                contadores['casos'],
                contadores['epizootias'],
                contadores['fallecidos'],
                contadores['positivas'],
                contadores['en_estudio'],
                color_scheme
            )
        else:
            # Vereda no seleccionada: usar color gris claro
            color = color_scheme["no_seleccionado"]
            descripcion = "No seleccionada"
        
        veredas_data.loc[idx, 'color'] = color
        veredas_data.loc[idx, 'descripcion_color'] = descripcion
        veredas_data.loc[idx, 'es_seleccionada'] = es_seleccionada
        
        for key, value in contadores.items():
            veredas_data.loc[idx, key] = value
    
    logger.info(f"🎨 Datos veredas múltiples: {len(veredas_sel_norm)} seleccionadas de {len(veredas_data)}")
    return veredas_data

# ===== TOOLTIPS MÚLTIPLES =====

def create_municipio_tooltip_multiple_epidemiological(name, row, colors, es_seleccionado):
    """Tooltip para municipio múltiple epidemiológico."""
    status_icon = "✅" if es_seleccionado else "⚪"
    status_text = "Seleccionado" if es_seleccionado else "No seleccionado"
    
    return f"""
    <div style="font-family: Arial; padding: 10px; max-width: 250px;">
        <b style="color: {colors['primary']}; font-size: 1.1em;">{status_icon} {name}</b><br>
        <div style="margin: 8px 0; padding: 6px; background: #f8f9fa; border-radius: 4px;">
            🦠 Casos: {row.get('casos', 0)}<br>
            ⚰️ Fallecidos: {row.get('fallecidos', 0)}<br>
            🐒 Epizootias: {row.get('epizootias', 0)}<br>
            🔴 Positivas: {row.get('positivas', 0)}
        </div>
        <div style="color: {colors['info']}; font-size: 0.9em;">
            {row.get('descripcion_color', 'Sin clasificar')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para {('quitar' if es_seleccionado else 'agregar')} selección</i>
    </div>
    """

def create_municipio_tooltip_multiple_coverage(name, row, colors, es_seleccionado):
    """Tooltip para municipio múltiple cobertura."""
    status_icon = "✅" if es_seleccionado else "⚪"
    status_text = "Seleccionado" if es_seleccionado else "No seleccionado"
    
    return f"""
    <div style="font-family: Arial; padding: 10px; max-width: 200px;">
        <b style="color: {colors['primary']}; font-size: 1.1em;">{status_icon} {name}</b><br>
        <div style="margin: 8px 0; padding: 6px; background: #f0f8ff; border-radius: 4px;">
            💉 Cobertura: {row.get('cobertura', 0):.1f}%<br>
            📊 {row.get('descripcion_color', 'Sin datos')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para {('quitar' if es_seleccionado else 'agregar')} selección</i>
    </div>
    """

def create_vereda_tooltip_multiple_epidemiological(name, row, colors, es_seleccionada):
    """Tooltip para vereda múltiple epidemiológico."""
    status_icon = "✅" if es_seleccionada else "⚪"
    
    return f"""
    <div style="font-family: Arial; padding: 8px; max-width: 200px;">
        <b style="color: {colors['primary']};">{status_icon} {name}</b><br>
        <div style="margin: 6px 0; font-size: 0.9em;">
            🦠 Casos: {row.get('casos', 0)}<br>
            🐒 Epizootias: {row.get('epizootias', 0)}<br>
        </div>
        <div style="color: {colors['info']}; font-size: 0.8em;">
            {row.get('descripcion_color', 'Sin datos')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para {('quitar' if es_seleccionada else 'agregar')} selección</i>
    </div>
    """

def create_vereda_tooltip_multiple_coverage(name, row, colors, es_seleccionada):
    """Tooltip para vereda múltiple cobertura."""
    status_icon = "✅" if es_seleccionada else "⚪"
    
    return f"""
    <div style="font-family: Arial; padding: 8px; max-width: 180px;">
        <b style="color: {colors['primary']};">{status_icon} {name}</b><br>
        <div style="margin: 6px 0;">
            💉 Cobertura: {row.get('cobertura', 0):.1f}%
        </div>
        <div style="color: {colors['info']}; font-size: 0.8em;">
            {row.get('descripcion_color', 'Sin datos')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para {('quitar' if es_seleccionada else 'agregar')} selección</i>
    </div>
    """

def prepare_veredas_data_coverage_multiple(veredas_gdf, municipios_seleccionados, veredas_seleccionadas, colors):
    """Prepara datos de veredas para modo múltiple cobertura."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    veredas_data = veredas_gdf.copy()
    veredas_data['vereda_nor_norm'] = veredas_data['vereda_nor'].apply(normalize_name)
    veredas_sel_norm = [normalize_name(v) for v in veredas_seleccionadas]
    
    color_scheme = get_color_scheme_coverage(colors)
    
    import random
    random.seed(42)  # Semilla fija para consistencia
    
    for idx, row in veredas_data.iterrows():
        vereda_norm = row['vereda_nor_norm']
        es_seleccionada = vereda_norm in veredas_sel_norm
        
        # Cobertura simulada con variación
        cobertura_base = random.uniform(70, 95)
        
        if es_seleccionada:
            # Vereda seleccionada: usar color normal de cobertura
            color, descripcion = determine_feature_color_coverage(cobertura_base, color_scheme)
        else:
            # Vereda no seleccionada: usar color gris claro
            color = color_scheme["no_seleccionado"]
            descripcion = "No seleccionada"
        
        veredas_data.loc[idx, 'color'] = color
        veredas_data.loc[idx, 'descripcion_color'] = descripcion
        veredas_data.loc[idx, 'es_seleccionada'] = es_seleccionada
        veredas_data.loc[idx, 'cobertura'] = cobertura_base
    
    return veredas_data

def create_municipal_map_multiple(casos, epizootias, geo_data, filters, colors):
    """Mapa municipal múltiple OPTIMIZADO."""
    municipios_seleccionados = filters.get("municipios_seleccionados", [])
    veredas_seleccionadas = filters.get("veredas_seleccionadas", [])
    
    if not municipios_seleccionados:
        st.info("🗂️ Seleccione municipios primero para ver veredas en modo múltiple")
        return
    
    logger.info("🏘️ Creando mapa múltiple municipal OPTIMIZADO")
    
    veredas = geo_data['veredas'].copy()
    # Filtrar veredas de municipios seleccionados
    veredas_municipios = veredas[veredas['municipi_1'].isin(municipios_seleccionados)]
    
    if veredas_municipios.empty:
        st.warning(f"No se encontraron veredas para los municipios seleccionados")
        return
    
    modo_mapa = filters.get("modo_mapa", "Epidemiológico")
    
    # Preparar datos con diferenciación
    if modo_mapa == "Epidemiológico":
        veredas_data = prepare_veredas_data_epidemiological_multiple(casos, epizootias, veredas_municipios, municipios_seleccionados, veredas_seleccionadas, colors)
    else:
        veredas_data = prepare_veredas_data_coverage_multiple(veredas_municipios, municipios_seleccionados, veredas_seleccionadas, colors)
    
    # Crear y mostrar mapa
    m = create_folium_map(veredas_data, zoom_start=10)
    add_veredas_to_map_differentiated(m, veredas_data, veredas_seleccionadas, colors, modo_mapa)
    
    # Renderizar
    map_data = st_folium(
        m, 
        width="100%",
        height=600,
        returned_objects=["last_object_clicked"],
        key=f"map_mun_multiple_{modo_mapa.lower()}"
    )
    
    # Procesar clicks múltiples
    handle_map_click_multiple(map_data, veredas_data, "vereda", filters, casos, epizootias)

def create_vereda_specific_map(casos, epizootias, geo_data, filters, colors):
    """Vista específica de vereda."""
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
        create_vereda_detail_view(casos, epizootias, filters, colors)
        return
    
    # Crear mapa centrado solo en la vereda
    m = create_folium_map(vereda_especifica, zoom_start=12)
    
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
    
    # Renderizar mapa
    st_folium(
        m, 
        width="100%",
        height=600,
        returned_objects=[],
        key=f"map_vereda_especifica_{vereda_selected}"
    )
    
    # Mostrar datos específicos de la vereda
    show_vereda_specific_data(casos, epizootias, vereda_selected, municipio_selected, colors)

# ===== FUNCIONES DE PREPARACIÓN DE DATOS =====

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
    
    # Aplicar colores
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
    
    return municipios_data

def prepare_municipal_data_coverage(municipios, colors):
    """Prepara datos municipales para modo cobertura (CONSOLIDADA)."""
    municipios_data = municipios.copy()
    color_scheme = get_color_scheme_coverage(colors)
    
    # Datos de cobertura simulados
    COBERTURAS_MUNICIPIOS = {
        'IBAGUE': 85.2, 'ALPUJARRA': 78.5, 'ALVARADO': 92.1, 'AMBALEMA': 67.8,
        'ANZOATEGUI': 73.4, 'ARMERO': 69.2, 'ATACO': 81.7, 'CAJAMARCA': 88.3,
        'CARMEN DE APICALA': 74.9, 'CASABIANCA': 82.6, 'CHAPARRAL': 79.1, 'COELLO': 86.4,
        'COYAIMA': 71.3, 'CUNDAY': 77.8, 'DOLORES': 65.7, 'ESPINAL': 89.5,
        'FALAN': 83.2, 'FLANDES': 91.8, 'FRESNO': 76.4, 'GUAMO': 84.1,
        'HERVEO': 72.9, 'HONDA': 87.6, 'ICONONZO': 75.3, 'LERIDA': 80.7,
        'LIBANO': 85.9, 'MARIQUITA': 88.2, 'MELGAR': 82.4, 'MURILLO': 70.6,
        'NATAGAIMA': 68.9, 'ORTEGA': 79.8, 'PALOCABILDO': 74.2, 'PIEDRAS': 86.7,
        'PLANADAS': 77.1, 'PRADO': 83.5, 'PURIFICACION': 81.3, 'RIOBLANCO': 69.8,
        'RONCESVALLES': 75.6, 'ROVIRA': 84.8, 'SALDAÑA': 87.3, 'SAN ANTONIO': 73.7,
        'SAN LUIS': 78.9, 'SANTA ISABEL': 80.4, 'SUAREZ': 76.8, 'VALLE DE SAN JUAN': 85.6,
        'VENADILLO': 89.1, 'VILLAHERMOSA': 72.2, 'VILLARRICA': 81.9
    }
    
    for idx, row in municipios_data.iterrows():
        municipio_name = row.get('MpNombre', row.get('municipi_1', 'DESCONOCIDO'))
        cobertura_value = COBERTURAS_MUNICIPIOS.get(municipio_name, 75.0)
        
        color, descripcion = determine_feature_color_coverage(cobertura_value, color_scheme)
        
        municipios_data.loc[idx, 'color'] = color
        municipios_data.loc[idx, 'descripcion_color'] = descripcion
        municipios_data.loc[idx, 'cobertura'] = cobertura_value
    
    return municipios_data

def prepare_vereda_data_epidemiological(casos, epizootias, veredas_gdf, municipio_selected, colors):
    """Prepara datos de veredas para modo epidemiológico."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    veredas_gdf = veredas_gdf.copy()
    municipio_norm = normalize_name(municipio_selected)
    color_scheme = get_color_scheme_epidemiological(colors)
    
    # Contadores por vereda
    contadores_veredas = {}
    
    if not casos.empty and 'vereda' in casos.columns and 'municipio' in casos.columns:
        casos_norm = casos.copy()
        casos_norm['vereda_norm'] = casos_norm['vereda'].apply(normalize_name)
        casos_norm['municipio_norm'] = casos_norm['municipio'].apply(normalize_name)
        
        casos_municipio = casos_norm[casos_norm['municipio_norm'] == municipio_norm]
        
        for vereda_name in veredas_gdf['vereda_nor'].unique():
            vereda_norm = normalize_name(vereda_name)
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
        
        for vereda_name in veredas_gdf['vereda_nor'].unique():
            vereda_norm = normalize_name(vereda_name)
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
        vereda_norm = normalize_name(row['vereda_nor'])
        contadores = contadores_veredas.get(vereda_norm, {
            'casos': 0, 'fallecidos': 0, 'epizootias': 0, 'positivas': 0, 'en_estudio': 0
        })
        
        color, descripcion = determine_feature_color_epidemiological(
            contadores['casos'],
            contadores['epizootias'],
            contadores['fallecidos'],
            contadores['en_estudio'],
            color_scheme
        )
        
        veredas_data.loc[idx, 'color'] = color
        veredas_data.loc[idx, 'descripcion_color'] = descripcion
        
        for key, value in contadores.items():
            veredas_data.loc[idx, key] = value
    
    return veredas_data

def prepare_vereda_data_coverage(veredas_gdf, municipio_selected, colors):
    """Prepara datos de veredas para modo cobertura."""
    veredas_data = veredas_gdf.copy()
    color_scheme = get_color_scheme_coverage(colors)
    
    import random
    random.seed(42)  # Semilla fija para consistencia
    
    for idx, row in veredas_data.iterrows():
        # Cobertura simulada con variación
        cobertura_base = random.uniform(70, 95)
        
        color, descripcion = determine_feature_color_coverage(cobertura_base, color_scheme)
        
        veredas_data.loc[idx, 'color'] = color
        veredas_data.loc[idx, 'descripcion_color'] = descripcion
        veredas_data.loc[idx, 'cobertura'] = cobertura_base
    
    return veredas_data

# ===== FUNCIONES DE APOYO PARA MAPAS =====

def create_folium_map(geo_data, zoom_start=8):
    """Crea mapa base de Folium."""
    if hasattr(geo_data, 'total_bounds'):
        bounds = geo_data.total_bounds
    else:
        # Para DataFrame de municipios/veredas
        bounds = geo_data.bounds
        if len(bounds) > 0:
            bounds = [bounds.minx.min(), bounds.miny.min(), bounds.maxx.max(), bounds.maxy.max()]
        else:
            # Fallback para Tolima
            bounds = [-76.0, 3.5, -74.5, 5.5]
    
    center_lat, center_lon = (bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles='CartoDB positron',
        attributionControl=False,
        zoom_control=True,
        scrollWheelZoom=True
    )
    
    # Aplicar límites si es posible
    if len(bounds) == 4:
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    
    return m

def add_municipios_to_map(folium_map, municipios_data, colors, modo_mapa):
    """Agrega municipios al mapa."""
    for idx, row in municipios_data.iterrows():
        municipio_name = row.get('MpNombre', row.get('municipi_1', 'DESCONOCIDO'))
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

def add_veredas_to_map(folium_map, veredas_data, colors, modo_mapa):
    """Agrega veredas al mapa CONSOLIDADO."""
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
                    'opacity': 0.8
                },
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            ).add_to(folium_map)
        except Exception as e:
            logger.warning(f"⚠️ Error agregando vereda {vereda_name}: {str(e)}")

def add_municipios_to_map_differentiated(folium_map, municipios_data, municipios_seleccionados, colors, modo_mapa):
    """Agrega municipios con diferenciación de selección."""
    for idx, row in municipios_data.iterrows():
        municipio_name = row.get('MpNombre', row.get('municipi_1', 'DESCONOCIDO'))
        color = row['color']
        es_seleccionado = row.get('es_seleccionado', False)
        
        # Grosor de borde según selección
        weight = 3 if es_seleccionado else 1
        opacity = 1.0 if es_seleccionado else 0.7
        fillOpacity = 0.8 if es_seleccionado else 0.5
        
        # Crear tooltip según modo y selección
        if modo_mapa == "Epidemiológico":
            tooltip_text = create_municipio_tooltip_multiple_epidemiological(municipio_name, row, colors, es_seleccionado)
        else:
            tooltip_text = create_municipio_tooltip_multiple_coverage(municipio_name, row, colors, es_seleccionado)
        
        # Agregar polígono
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=color, weight=weight, opacity=opacity, fillOpacity=fillOpacity: {
                'fillColor': color,
                'color': colors['primary'] if es_seleccionado else '#9CA3AF',
                'weight': weight,
                'fillOpacity': fillOpacity,
                'opacity': opacity
            },
            tooltip=folium.Tooltip(tooltip_text, sticky=True),
        ).add_to(folium_map)

def add_veredas_to_map_differentiated(folium_map, veredas_data, veredas_seleccionadas, colors, modo_mapa):
    """Agrega veredas con diferenciación de selección."""
    for idx, row in veredas_data.iterrows():
        vereda_name = row['vereda_nor']
        color = row['color']
        es_seleccionada = row.get('es_seleccionada', False)
        
        # Grosor de borde según selección
        weight = 2.5 if es_seleccionada else 1
        opacity = 1.0 if es_seleccionada else 0.6
        fillOpacity = 0.7 if es_seleccionada else 0.4
        
        # Crear tooltip según modo
        if modo_mapa == "Epidemiológico":
            tooltip_text = create_vereda_tooltip_multiple_epidemiological(vereda_name, row, colors, es_seleccionada)
        else:
            tooltip_text = create_vereda_tooltip_multiple_coverage(vereda_name, row, colors, es_seleccionada)
        
        try:
            folium.GeoJson(
                row['geometry'],
                style_function=lambda x, color=color, weight=weight, opacity=opacity, fillOpacity=fillOpacity: {
                    'fillColor': color,
                    'color': colors['accent'] if es_seleccionada else '#D1D5DB',
                    'weight': weight,
                    'fillOpacity': fillOpacity,
                    'opacity': opacity
                },
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            ).add_to(folium_map)
        except Exception as e:
            logger.warning(f"⚠️ Error agregando vereda {vereda_name}: {str(e)}")

# ===== TOOLTIPS =====

def create_municipio_tooltip_epidemiological(name, row, colors):
    """Tooltip para municipio epidemiológico."""
    return f"""
    <div style="font-family: Arial; padding: 10px; max-width: 250px;">
        <b style="color: {colors['primary']}; font-size: 1.1em;">🏛️ {name}</b><br>
        <div style="margin: 8px 0; padding: 6px; background: #f8f9fa; border-radius: 4px;">
            🦠 Casos: {row.get('casos', 0)}<br>
            ⚰️ Fallecidos: {row.get('fallecidos', 0)}<br>
            🐒 Epizootias: {row.get('epizootias', 0)}<br>
        </div>
        <div style="color: {colors['info']}; font-size: 0.9em;">
            {row.get('descripcion_color', 'Sin clasificar')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
    </div>
    """

def create_municipio_tooltip_coverage(name, row, colors):
    """Tooltip para municipio cobertura."""
    return f"""
    <div style="font-family: Arial; padding: 10px; max-width: 200px;">
        <b style="color: {colors['primary']}; font-size: 1.1em;">🏛️ {name}</b><br>
        <div style="margin: 8px 0; padding: 6px; background: #f0f8ff; border-radius: 4px;">
            💉 Cobertura: {row.get('cobertura', 0):.1f}%<br>
            📊 {row.get('descripcion_color', 'Sin datos')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
    </div>
    """

def create_vereda_tooltip_epidemiological(name, row, colors):
    """Tooltip para vereda epidemiológico."""
    return f"""
    <div style="font-family: Arial; padding: 8px; max-width: 200px;">
        <b style="color: {colors['primary']};">🏘️ {name}</b><br>
        <div style="margin: 6px 0; font-size: 0.9em;">
            🦠 Casos: {row.get('casos', 0)}<br>
            🐒 Epizootias: {row.get('epizootias', 0)}<br>
        </div>
        <div style="color: {colors['info']}; font-size: 0.8em;">
            {row.get('descripcion_color', 'Sin datos')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
    </div>
    """

def create_vereda_tooltip_coverage(name, row, colors):
    """Tooltip para vereda cobertura."""
    return f"""
    <div style="font-family: Arial; padding: 8px; max-width: 180px;">
        <b style="color: {colors['primary']};">🏘️ {name}</b><br>
        <div style="margin: 6px 0;">
            💉 Cobertura: {row.get('cobertura', 0):.1f}%
        </div>
        <div style="color: {colors['info']}; font-size: 0.8em;">
            {row.get('descripcion_color', 'Sin datos')}
        </div>
        <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
    </div>
    """

# ===== MANEJO DE CLICKS =====

def handle_map_click(map_data, features_data, feature_type, filters, casos, epizootias):
    """Manejo de clicks."""
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
                    # Aplicar filtro único
                    apply_single_filter(feature_clicked, feature_type, filters)
                    
                    # Mensaje informativo
                    st.success(f"✅ **{feature_clicked}** seleccionado")
                    
                    # Delay antes de rerun
                    import time
                    time.sleep(0.5)
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"❌ Error procesando clic: {str(e)}")

def handle_map_click_multiple(map_data, features_data, feature_type, filters, casos, epizootias):
    """Manejo de clicks PARA MODO MÚLTIPLE."""
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
                    # Agregar/quitar de selección múltiple
                    toggle_multiple_selection(feature_clicked, feature_type, filters)
                    
                    # Mensaje informativo
                    current_selection = get_current_multiple_selection(feature_type, filters)
                    action = "agregado a" if feature_clicked in current_selection else "quitado de"
                    
                    st.success(f"✅ **{feature_clicked}** {action} la selección múltiple")
                    
                    # Delay antes de rerun
                    import time
                    time.sleep(0.5)
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"❌ Error procesando clic múltiple: {str(e)}")

def find_closest_feature(lat, lng, features_data, feature_type):
    """Encuentra el feature más cercano al clic."""
    try:
        from shapely.geometry import Point
        from shapely.ops import nearest_points
        
        click_point = Point(lng, lat)
        min_distance = float('inf')
        closest_feature = None
        
        for idx, row in features_data.iterrows():
            try:
                feature_geom = row['geometry']
                distance = click_point.distance(feature_geom)
                
                if distance < min_distance:
                    min_distance = distance
                    if feature_type == "municipio":
                        closest_feature = row.get('MpNombre', row.get('municipi_1', 'DESCONOCIDO'))
                    else:  # vereda
                        closest_feature = row.get('vereda_nor', 'DESCONOCIDA')
            except Exception as e:
                continue
        
        return closest_feature
        
    except ImportError:
        # Fallback sin shapely
        logger.warning("⚠️ Shapely no disponible, usando fallback simple")
        if not features_data.empty:
            row = features_data.iloc[0]
            if feature_type == "municipio":
                return row.get('MpNombre', row.get('municipi_1', 'DESCONOCIDO'))
            else:
                return row.get('vereda_nor', 'DESCONOCIDA')
        return None

def apply_single_filter(feature_name, feature_type, filters):
    """Aplica filtro único."""
    if feature_type == "municipio":
        st.session_state['municipio_filter'] = feature_name
        st.session_state['vereda_filter'] = 'Todas'  # Resetear vereda
    elif feature_type == "vereda":
        st.session_state['vereda_filter'] = feature_name

def toggle_multiple_selection(feature_name, feature_type, filters):
    """Agrega o quita un feature de la selección múltiple."""
    if feature_type == "municipio":
        session_key = 'municipios_multiselect'
        current_selection = st.session_state.get(session_key, [])
        
        if feature_name in current_selection:
            current_selection.remove(feature_name)
        else:
            current_selection.append(feature_name)
        
        st.session_state[session_key] = current_selection
        
    elif feature_type == "vereda":
        session_key = 'veredas_multiselect'
        current_selection = st.session_state.get(session_key, [])
        
        if feature_name in current_selection:
            current_selection.remove(feature_name)
        else:
            current_selection.append(feature_name)
        
        st.session_state[session_key] = current_selection

def get_current_multiple_selection(feature_type, filters):
    """Obtiene la selección múltiple actual."""
    if feature_type == "municipio":
        return filters.get("municipios_seleccionados", [])
    elif feature_type == "vereda":
        return filters.get("veredas_seleccionadas", [])
    else:
        return []

# ===== TARJETAS INFORMATIVAS =====

def create_information_cards_optimized(casos, epizootias, filters, colors):
    """Tarjetas informativas optimizadas."""
    logger.info("🏷️ Creando tarjetas informativas optimizadas")
    
    metrics = calculate_basic_metrics(casos, epizootias)
    
    # Estilo gradiente moderno
    create_cards_style_gradients(metrics, filters, colors)

def create_cards_style_gradients(metrics, filters, colors):
    """Estilo de tarjetas con gradientes modernos."""
    filter_context = get_filter_context_compact(filters)
    
    # Tarjeta de cobertura - Estilo gradiente
    cobertura_simulada = 82.3
    dosis_aplicadas = 45650  # Simulado
    gap_cobertura = 95.0 - cobertura_simulada
    ultima_actualizacion = datetime.now().strftime("%d/%m/%Y")
    
    st.markdown(
        f"""
        <div class="gradient-card coverage-gradient">
            <div class="gradient-header">
                <div class="gradient-icon">💉</div>
                <div class="gradient-title-section">
                    <div class="gradient-title">COBERTURA</div>
                    <div class="gradient-subtitle">{filter_context}</div>
                </div>
                <div class="gradient-total">{cobertura_simulada:.1f}%</div>
            </div>
            <div class="gradient-metrics">
                <div class="coverage-bar-gradient">
                    <div class="coverage-progress-gradient" style="width: {cobertura_simulada}%"></div>
                </div>
                <div class="gradient-grid">
                    <div class="gradient-cell warning">
                        <div class="gradient-value">{dosis_aplicadas:,}</div>
                        <div class="gradient-label">Dosis Aplicadas</div>
                    </div>
                    <div class="gradient-cell danger">
                        <div class="gradient-value">{gap_cobertura:.1f}%</div>
                        <div class="gradient-label">GAP</div>
                    </div>
                </div>
                <div class="gradient-ultimo">
                    <strong>📅 Última actualización:</strong><br>
                    <span style="font-size: 0.85em;">{ultima_actualizacion}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
        
    # Tarjeta de casos
    total_casos = metrics["total_casos"]
    vivos = metrics["vivos"]
    fallecidos = metrics["fallecidos"]
    letalidad = metrics["letalidad"]
    ultimo_caso = metrics["ultimo_caso"]
    
    ultimo_caso_info = "Sin casos registrados"
    if ultimo_caso["existe"]:
        ultimo_caso_info = f"{ultimo_caso['ubicacion']} • Hace {ultimo_caso['tiempo_transcurrido']}"
    
    st.markdown(
        f"""
        <div class="gradient-card casos-gradient">
            <div class="gradient-header">
                <div class="gradient-icon">🦠</div>
                <div class="gradient-title-section">
                    <div class="gradient-title">CASOS HUMANOS</div>
                    <div class="gradient-subtitle">{filter_context}</div>
                </div>
                <div class="gradient-total">{total_casos}</div>
            </div>
            <div class="gradient-metrics">
                <div class="gradient-grid">
                    <div class="gradient-cell success">
                        <div class="gradient-value">{vivos}</div>
                        <div class="gradient-label">Vivos</div>
                    </div>
                    <div class="gradient-cell danger">
                        <div class="gradient-value">{fallecidos}</div>
                        <div class="gradient-label">Fallecidos</div>
                    </div>
                </div>
                <div class="gradient-footer">
                    <span class="footer-label">Letalidad:</span>
                    <span class="footer-value">{letalidad:.1f}%</span>
                </div>
                <div class="gradient-ultimo">
                    <strong>📍 Último caso:</strong><br>
                    <span style="font-size: 0.85em;">{ultimo_caso_info}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Tarjeta de epizootias
    total_epizootias = metrics["total_epizootias"]
    positivas = metrics["epizootias_positivas"]
    en_estudio = metrics["epizootias_en_estudio"]
    ultima_epizootia = metrics["ultima_epizootia_positiva"]
    
    ultima_epi_info = "Sin epizootias registradas"
    if ultima_epizootia["existe"]:
        ultima_epi_info = f"{ultima_epizootia['ubicacion']} • Hace {ultima_epizootia['tiempo_transcurrido']}"
    
    st.markdown(
        f"""
        <div class="gradient-card epizootias-gradient">
            <div class="gradient-header">
                <div class="gradient-icon">🐒</div>
                <div class="gradient-title-section">
                    <div class="gradient-title">EPIZOOTIAS</div>
                    <div class="gradient-subtitle">{filter_context}</div>
                </div>
                <div class="gradient-total">{total_epizootias}</div>
            </div>
            <div class="gradient-metrics">
                <div class="gradient-grid">
                    <div class="gradient-cell danger">
                        <div class="gradient-value">{positivas}</div>
                        <div class="gradient-label">Positivas</div>
                    </div>
                    <div class="gradient-cell info">
                        <div class="gradient-value">{en_estudio}</div>
                        <div class="gradient-label">En Estudio</div>
                    </div>
                </div>
                <div class="gradient-ultimo">
                    <strong>🔴 Última positiva:</strong><br>
                    <span style="font-size: 0.85em;">{ultima_epi_info}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===== FUNCIONES DE APOYO =====

def load_geographic_data():
    """Carga datos geográficos."""
    if not SHAPEFILE_LOADER_AVAILABLE:
        logger.warning("⚠️ Sistema híbrido no disponible")
        return None
    
    try:
        return load_tolima_shapefiles()
    except Exception as e:
        logger.error(f"❌ Error cargando datos geográficos: {str(e)}")
        return None

def determine_map_level(filters):
    """Determina el nivel del mapa según filtros."""
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

def show_fallback_summary(casos, epizootias, level, location=None):
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

def create_vereda_detail_view(casos, epizootias, filters, colors):
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
        unsafe_allow_html=True
    )

def show_maps_not_available():
    """Muestra mensaje cuando mapas no están disponibles."""
    st.error("🗺️ Los mapas no están disponibles")
    st.info("Para habilitar los mapas, instale las dependencias: `pip install geopandas folium streamlit-folium`")

def show_geographic_data_error():
    """Muestra error cuando no se pueden cargar datos geográficos."""
    st.error("❌ No se pudieron cargar los datos geográficos")
    st.info("Verifique la configuración de shapefiles en Google Drive o archivos locales")

# Mantener las funciones existentes para modo múltiple que ya funcionan
# (Las que están bien definidas en el código original)

# ===== CSS RESPONSIVE =====

def apply_maps_css_full_responsive(colors):
    """CSS para mapas fullsize y tarjetas."""
    st.markdown(
        f"""
        <style>
        /* =============== MAPAS FULLSIZE =============== */
        
        .filter-info-compact {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            text-align: center;
            margin: 10px 0 15px 0;
            font-size: 0.9rem;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        /* Asegurar que el iframe del mapa ocupe el 100% */
        iframe[title="st_folium.st_folium"] {{
            width: 100% !important;
            height: 600px !important;
            border-radius: 12px !important;
            border: 2px solid #e2e8f0 !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
        }}
        
        /* =============== ESTILO GRADIENTES =============== */
        
        .gradient-card {{
            background: linear-gradient(135deg, white 0%, #f8fafc 50%, #f1f5f9 100%);
            border-radius: 20px;
            margin-bottom: 25px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
            overflow: hidden;
            transition: all 0.4s ease;
            border: 1px solid rgba(255,255,255,0.2);
            position: relative;
        }}
        
        .gradient-card::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 80px;
            height: 80px;
            background: radial-gradient(circle, {colors['secondary']}40, transparent);
            border-radius: 50%;
            transform: translate(40%, -40%);
        }}
        
        .gradient-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.25);
        }}
        
        .casos-gradient {{
            background: linear-gradient(135deg, #fef2f2, white, #fef2f2);
            border-left: 6px solid {colors['danger']};
        }}
        
        .epizootias-gradient {{
            background: linear-gradient(135deg, #fffbeb, white, #fffbeb);
            border-left: 6px solid {colors['warning']};
        }}
        
        .gradient-header {{
            background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(248,250,252,0.9));
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            position: relative;
            z-index: 2;
        }}
        
        .gradient-icon {{
            font-size: 2.5rem;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        }}
        
        .gradient-title-section {{
            flex: 1;
        }}
        
        .gradient-title {{
            color: {colors['primary']};
            font-size: 1.1rem;
            font-weight: 800;
            margin: 0;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }}
        
        .gradient-subtitle {{
            color: {colors['accent']};
            font-size: 0.8rem;
            font-weight: 600;
            margin: 2px 0 0 0;
        }}
        
        .gradient-total {{
            font-size: 2.5rem;
            font-weight: 900;
            color: {colors['primary']};
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .gradient-metrics {{
            padding: 20px;
            position: relative;
            z-index: 2;
        }}
        
        .gradient-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .gradient-cell {{
            background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            transition: all 0.3s ease;
            border: 2px solid transparent;
            backdrop-filter: blur(10px);
        }}
        
        .gradient-cell:hover {{
            transform: scale(1.05);
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.95));
        }}
        
        .gradient-cell.success {{ border-color: {colors['success']}; }}
        .gradient-cell.danger {{ border-color: {colors['danger']}; }}
        .gradient-cell.info {{ border-color: {colors['info']}; }}
        .gradient-cell.warning {{ border-color: {colors['warning']}; }}
        
        .gradient-value {{
            font-size: 1.6rem;
            font-weight: 800;
            color: {colors['primary']};
            margin-bottom: 5px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }}
        
        .gradient-label {{
            font-size: 0.75rem;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .gradient-footer {{
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']});
            color: white;
            padding: 12px;
            border-radius: 12px;
            text-align: center;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        .gradient-ultimo {{
            background: linear-gradient(135deg, rgba(248,250,252,0.8), rgba(241,245,249,0.8));
            padding: 12px;
            border-radius: 10px;
            font-size: 0.9rem;
            border-left: 4px solid {colors['secondary']};
        }}
        
        /* =============== RESPONSIVE =============== */
        @media (max-width: 768px) {{
            iframe[title="st_folium.st_folium"] {{
                height: 400px !important;
            }}
            
            .gradient-card {{
                margin-bottom: 15px;
            }}
            
            .gradient-header {{
                padding: 12px;
            }}
            
            .gradient-metrics {{
                padding: 12px;
            }}
            
            .gradient-grid {{
                grid-template-columns: 1fr;
                gap: 10px;
            }}
            
            .gradient-total {{
                font-size: 2rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )