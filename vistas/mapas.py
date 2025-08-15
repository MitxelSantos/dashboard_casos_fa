"""
Vista de mapas
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta

from utils.cobertura_processor import (
    get_cobertura_for_municipio,
    get_cobertura_for_vereda,
    debug_vereda_mapping  
)

from utils.data_processor import (
    calculate_basic_metrics, 
    verify_filtered_data_usage
)

logger = logging.getLogger(__name__)

# Importaciones opcionales para mapas
try:
    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium

    MAPS_AVAILABLE = True
except ImportError:
    MAPS_AVAILABLE = False

# Sistema híbrido de shapefiles
try:
    from data_loader import load_shapefile_data, check_data_availability,show_data_setup_instructions


    SHAPEFILE_LOADER_AVAILABLE = True
except ImportError:
    SHAPEFILE_LOADER_AVAILABLE = False

# ===== DICCIONARIO DE MAPEO PARA INCONSISTENCIAS CONOCIDAS =====
MUNICIPIO_MAPPING = {
    # Shapefile → Base de datos
    "SAN SEBASTIAN DE MARIQUITA": "MARIQUITA",
    "MARIQUITA": "MARIQUITA",
    # Agregar otros mapeos según sea necesario
}

MUNICIPIO_MAPPING_REVERSE = {
    # Base de datos → Shapefile
    "MARIQUITA": "SAN SEBASTIAN DE MARIQUITA",
    "SAN SEBASTIAN DE MARIQUITA": "SAN SEBASTIAN DE MARIQUITA",  # Mantener consistencia
    # Se generará automáticamente desde MUNICIPIO_MAPPING
}

VEREDA_MUNICIPIO_MAPPING = {
    # Para casos donde el municipio en shapefile no coincide con base de datos
    "SAN SEBASTIAN DE MARIQUITA": "MARIQUITA",
}

# ===== FUNCIONES DE MAPEO =====

def simple_name_match(name1: str, name2: str) -> bool:
    """
    Comparación simple de nombres con mapeo de inconsistencias.
    """
    if not name1 or not name2:
        return False

    name1_clean = str(name1).strip().upper()
    name2_clean = str(name2).strip().upper()

    # Comparación directa
    if name1_clean == name2_clean:
        return True

    # Verificar mapeos conocidos usando las funciones existentes
    try:
        mapped_name1 = get_mapped_municipio(name1_clean, "shapefile_to_data").upper()
        mapped_name2 = get_mapped_municipio(name2_clean, "shapefile_to_data").upper()
        
        return mapped_name1 == name2_clean or name1_clean == mapped_name2 or mapped_name1 == mapped_name2
    except:
        # Si falla el mapeo, solo comparación directa
        return name1_clean == name2_clean

def initialize_bidirectional_mapping():
    """Inicializa el mapeo bidireccional automáticamente."""
    global MUNICIPIO_MAPPING_REVERSE

    # Generar mapeo inverso automáticamente
    for shapefile_name, data_name in MUNICIPIO_MAPPING.items():
        if data_name not in MUNICIPIO_MAPPING_REVERSE:
            MUNICIPIO_MAPPING_REVERSE[data_name] = shapefile_name

    logger.info(
        f"🔗 Mapeo bidireccional inicializado: {len(MUNICIPIO_MAPPING)} → {len(MUNICIPIO_MAPPING_REVERSE)}"
    )

def get_mapped_municipio(municipio_name, direction="shapefile_to_data"):
    """
    Obtiene el nombre mapeado de un municipio en ambas direcciones.

    Args:
        municipio_name: Nombre del municipio
        direction: "shapefile_to_data" o "data_to_shapefile"
    """
    if not municipio_name:
        return ""

    municipio_clean = str(municipio_name).strip()

    if direction == "shapefile_to_data":
        return MUNICIPIO_MAPPING.get(municipio_clean, municipio_clean)
    elif direction == "data_to_shapefile":
        return MUNICIPIO_MAPPING_REVERSE.get(municipio_clean, municipio_clean)
    else:
        return municipio_clean

def find_municipio_name_in_shapefile(
    municipio_from_data, municipios_gdf, municipio_col
):
    """
    Encuentra el nombre correcto de municipio en el shapefile.

    Args:
        municipio_from_data: Nombre del municipio como aparece en los datos
        municipios_gdf: GeoDataFrame de municipios
        municipio_col: Columna de municipios en el shapefile
    """
    try:
        municipio_clean = str(municipio_from_data).strip()
        municipios_en_shapefile = municipios_gdf[municipio_col].dropna().unique()

        # 1. Buscar coincidencia directa
        for municipio_shapefile in municipios_en_shapefile:
            if str(municipio_shapefile).strip() == municipio_clean:
                logger.info(f"✅ Coincidencia directa: {municipio_clean}")
                return municipio_shapefile

        # 2. Buscar usando mapeo inverso (datos → shapefile)
        municipio_mapeado = get_mapped_municipio(municipio_clean, "data_to_shapefile")
        if municipio_mapeado != municipio_clean:
            for municipio_shapefile in municipios_en_shapefile:
                if str(municipio_shapefile).strip() == municipio_mapeado:
                    logger.info(
                        f"✅ Encontrado por mapeo inverso: {municipio_clean} → {municipio_mapeado}"
                    )
                    return municipio_shapefile

        # 3. Buscar usando mapeo directo (por si acaso)
        municipio_mapeado_directo = get_mapped_municipio(
            municipio_clean, "shapefile_to_data"
        )
        if municipio_mapeado_directo != municipio_clean:
            for municipio_shapefile in municipios_en_shapefile:
                if str(municipio_shapefile).strip() == municipio_mapeado_directo:
                    logger.info(
                        f"✅ Encontrado por mapeo directo: {municipio_clean} → {municipio_mapeado_directo}"
                    )
                    return municipio_shapefile

        logger.warning(f"⚠️ Municipio '{municipio_clean}' no encontrado en shapefile")
        return None

    except Exception as e:
        logger.error(f"❌ Error buscando municipio en shapefile: {str(e)}")
        return None


def find_municipio_in_data(shapefile_municipio: str, available_municipios: list) -> str:
    """Encuentra municipio en datos usando mapeo simple."""
    if not shapefile_municipio or not available_municipios:
        return None

    shapefile_clean = str(shapefile_municipio).strip()

    # Buscar coincidencia exacta primero
    for municipio in available_municipios:
        if simple_name_match(shapefile_clean, municipio):
            return municipio

    # Buscar usando mapeo
    mapped_municipio = get_mapped_municipio(shapefile_clean)
    for municipio in available_municipios:
        if simple_name_match(mapped_municipio, municipio):
            return municipio

    return None

# ===== CONFIGURACIÓN DE COLORES =====

def get_color_scheme_epidemiological(colors):
    """Esquema de colores epidemiológico."""
    return {
        "casos_y_epizootias": colors["danger"],      # 🔴 Rojo: Casos + Epizootias
        "solo_casos": colors["warning"],             # 🟠 Naranja: Solo casos
        "solo_epizootias": colors["secondary"],      # 🟡 Amarillo: Solo epizootias  
        "seleccionado": colors["primary"],
        "sin_datos": "#E5E7EB",
        "no_seleccionado": "#F3F4F6",
    }

def get_color_scheme_coverage(colors):
    """Esquema de colores por cobertura de vacunación."""
    return {
        "cobertura_alta": colors["success"],         # Verde: >= 95%
        "cobertura_buena": colors["secondary"],      # Amarillo: 80-94%
        "cobertura_regular": colors["warning"],      # Naranja: 60-79%
        "cobertura_baja": colors["danger"],          # Rojo: 30-59%
        "cobertura_muy_baja": "#991B1B",            # Rojo oscuro: 1-29%
        "sin_datos": "#E5E7EB",                     # GRIS: 0% o sin datos
        "seleccionado": colors["primary"],
        "no_seleccionado": "#F3F4F6",
    }

def determine_feature_color_epidemiological(
    casos_count,
    epizootias_count,
    fallecidos_count,
    positivas_count,
    en_estudio_count,
    color_scheme,
):
    """Determina color según modo epidemiológico."""
    try:
        # Asegurar que todos los valores sean enteros
        casos_count = int(casos_count) if pd.notna(casos_count) else 0
        epizootias_count = int(epizootias_count) if pd.notna(epizootias_count) else 0

        if casos_count > 0 and epizootias_count > 0:
            return color_scheme["casos_y_epizootias"], "🔴 Casos + Epizootias"
        elif casos_count > 0 and epizootias_count == 0:
            return color_scheme["solo_casos"], "🟠 Solo casos"
        elif casos_count == 0 and epizootias_count > 0:
            return color_scheme["solo_epizootias"], "🟡 Solo epizootias"
        else:
            return color_scheme["sin_datos"], "⚪ Sin casos"

    except Exception as e:
        logger.warning(f"⚠️ Error determinando color: {str(e)}")
        return color_scheme["sin_datos"], "⚪ Error en coloreo"

# ===== FUNCIÓN PRINCIPAL =====

def show(data_filtered, filters, colors):
    """Vista principal de mapas."""
    logger.info("🗺️ INICIANDO VISTA DE MAPAS")

    apply_maps_css_optimized(colors)

    casos_filtrados = data_filtered["casos"]
    epizootias_filtradas = data_filtered["epizootias"]

    verify_filtered_data_usage(casos_filtrados, "vista_mapas")
    verify_filtered_data_usage(epizootias_filtradas, "vista_mapas")

    if not MAPS_AVAILABLE:
        show_maps_not_available()
        return

    if not check_data_availability():
        show_data_setup_instructions()
        return

    geo_data = load_geographic_data()
    if not geo_data:
        show_geographic_data_error()
        return

    active_filters = filters.get("active_filters", [])
    modo_mapa = filters.get("modo_mapa", "Epidemiológico")

    if active_filters:
        st.markdown(
            f"""
            <div class="filter-info-compact">
                🎯 Vista: <strong>{modo_mapa}</strong> | Ubicación: <strong>{' • '.join(active_filters[:2])}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    create_optimized_layout_50_25_25(
        casos_filtrados, epizootias_filtradas, geo_data, filters, colors, data_filtered
    )

# ===== LAYOUT =====

def create_optimized_layout_50_25_25(
    casos, epizootias, geo_data, filters, colors, data_filtered
):
    """Layout optimizado 50-25-25."""
    col_mapa, col_tarjetas1, col_tarjetas2 = st.columns([2, 1, 1], gap="medium")

    with col_mapa:
        create_map_system_simplified(
            casos, epizootias, geo_data, filters, colors, data_filtered
        )
        create_urban_data_card_simplified(filters, colors, data_filtered)

    with col_tarjetas1:
        create_cobertura_card_simplified(filters, colors, data_filtered)
        create_afectacion_card_simplified(casos, epizootias, filters, colors, data_filtered)
        
    with col_tarjetas2:
        create_casos_card_optimized(casos, filters, colors)
        create_epizootias_card_optimized(epizootias, filters, colors)

def create_map_system_simplified(
    casos, epizootias, geo_data, filters, colors, data_filtered
):
    """Sistema de mapas con fallback inteligente."""
    # Validar y corregir filtros antes de procesar
    filters_validated = validate_and_fix_filters_for_maps(filters)

    current_level = determine_map_level(filters_validated)
    modo_mapa = filters_validated.get("modo_mapa", "Epidemiológico")

    logger.info(f"🗺️ Nivel del mapa determinado: {current_level} | Modo: {modo_mapa}")

    # ===== FALLBACK INTELIGENTE PARA MÚLTIPLE =====
    if current_level == "multiple":
        # Verificar si realmente hay municipios seleccionados
        municipios_seleccionados = filters_validated.get("municipios_seleccionados", [])
        
        if municipios_seleccionados:
            logger.info(f"🗂️ Mostrando mapa múltiple: {len(municipios_seleccionados)} municipios")
            create_multiple_selection_map_simplified(
                casos, epizootias, geo_data, filters_validated, colors, modo_mapa, data_filtered
            )
        else:
            logger.info("🏛️ Fallback: Mostrando mapa departamental (sin municipios seleccionados)")
            # Mostrar mapa departamental con instrucciones
            create_departmental_map_with_multiple_instructions(
                casos, epizootias, geo_data, filters_validated, colors, modo_mapa, data_filtered
            )
    elif current_level == "departamento":
        create_departmental_map_simplified(
            casos,
            epizootias,
            geo_data,
            filters_validated,
            colors,
            modo_mapa,
            data_filtered,
        )
    elif current_level == "municipio":
        create_municipal_map_simplified(
            casos,
            epizootias,
            geo_data,
            filters_validated,
            colors,
            modo_mapa,
            data_filtered,
        )
    elif current_level == "vereda":
        create_vereda_map_simplified(
            casos,
            epizootias,
            geo_data,
            filters_validated,
            colors,
            modo_mapa,
            data_filtered,
        )
    else:
        logger.warning(f"⚠️ Nivel de mapa no reconocido: {current_level}")
        show_fallback_summary(
            casos, epizootias, current_level, filters_validated.get("municipio_display")
        )

def create_departmental_map_with_multiple_instructions(
    casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
):
    """Mapa departamental con instrucciones para modo múltiple."""
    
    # Mensaje de instrucciones
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']});
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        ">
            <h4 style="margin: 0 0 10px 0;">🗂️ Modo Selección Múltiple Activado</h4>
            <p style="margin: 0; font-size: 1rem; opacity: 0.95;">
                Use los filtros del sidebar para seleccionar <strong>municipios</strong> y/o <strong>veredas</strong>.<br>
                El mapa se actualizará automáticamente con su selección.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Mostrar mapa departamental normal
    create_departmental_map_simplified(
        casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
    )
    
    # Instrucciones adicionales
    create_multiple_mode_instructions(colors)

def create_multiple_mode_instructions(colors):
    """Instrucciones específicas para el modo múltiple."""
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            f"""
            <div style="
                background: {colors['light']};
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid {colors['success']};
            ">
                <h5 style="color: {colors['primary']}; margin: 0 0 10px 0;">✅ Cómo usar:</h5>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Use los <strong>botones de región</strong> para seleccionar grupos</li>
                    <li>O seleccione <strong>municipios específicos</strong> uno por uno</li>
                    <li>Opcionalmente, filtre <strong>veredas específicas</strong></li>
                    <li>El mapa se actualizará automáticamente</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="
                background: {colors['light']};
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid {colors['warning']};
            ">
                <h5 style="color: {colors['primary']}; margin: 0 0 10px 0;">💡 Sugerencias:</h5>
                <ul style="margin: 0; padding-left: 20px;">
                    <li><strong>Norte, Centro, Sur:</strong> Use botones de región</li>
                    <li><strong>Comparar municipios:</strong> Selección individual</li>
                    <li><strong>Análisis específico:</strong> Seleccione veredas</li>
                    <li><strong>Limpiar:</strong> Use el botón "🗑️ Limpiar"</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

def create_vereda_map_simplified(
    casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
):
    """Mapa específico para vereda seleccionada."""
    municipio_selected = filters.get("municipio_display")
    vereda_selected = filters.get("vereda_display")

    logger.info(
        f"🏘️ Creando mapa para vereda: {vereda_selected} en {municipio_selected}"
    )

    if not municipio_selected or municipio_selected == "Todos":
        st.error("No se pudo determinar el municipio para la vista de vereda")
        return

    if not vereda_selected or vereda_selected == "Todas":
        st.error("No se pudo determinar la vereda para la vista detallada")
        return

    # Usar el mismo sistema que para municipios, pero con veredas
    veredas = geo_data["veredas"].copy()

    # Buscar veredas del municipio con mapeo
    veredas_municipio = find_veredas_for_municipio_simplified(
        veredas, municipio_selected
    )

    if veredas_municipio.empty:
        st.warning(f"No se encontraron veredas para {municipio_selected}")
        show_available_municipios_in_shapefile(veredas, municipio_selected)
        return

    # Preparar datos de veredas (igual que en create_municipal_map_simplified)
    if modo_mapa == "Epidemiológico":
        veredas_data = prepare_vereda_data_epidemiological_simplified(
            casos, epizootias, veredas_municipio, municipio_selected, colors
        )
    else:
        veredas_data = prepare_vereda_data_coverage_simplified(
            veredas_municipio, municipio_selected, colors
        )

    # Filtrar para mostrar solo la vereda específica + contexto
    vereda_especifica, veredas_contexto = filter_veredas_for_detailed_view(
        veredas_data, vereda_selected
    )

    if vereda_especifica.empty:
        st.warning(f"No se encontró la vereda '{vereda_selected}' en el shapefile")
        st.info(f"Veredas disponibles en {municipio_selected}:")
        vereda_col = get_vereda_column(veredas_data)
        if vereda_col and vereda_col in veredas_data.columns:
            veredas_disponibles = veredas_data[vereda_col].unique()[
                :10
            ]  # Mostrar solo las primeras 10
            for vereda in veredas_disponibles:
                st.write(f"• {vereda}")
        return

    # Crear mapa enfocado en la vereda específica
    st.markdown(f"#### 📍 Vista Detallada: {vereda_selected}")
    st.markdown(
        f"📍 **Municipio:** {municipio_selected} | 🏘️ **Vereda:** {vereda_selected}"
    )

    # Crear mapa con zoom automático a la vereda
    m = create_folium_map_focused_on_vereda(vereda_especifica, zoom_start=12)

    # Agregar vereda específica (resaltada)
    add_vereda_highlighted_to_map(
        m, vereda_especifica, colors, modo_mapa, is_target=True
    )

    # Agregar veredas vecinas para contexto
    if len(veredas_contexto) > 0:
        add_veredas_context_to_map(
            m, veredas_contexto.head(20), colors, modo_mapa
        )  # Máximo 20 para no saturar

    # Mostrar mapa
    map_data = st_folium(
        m,
        width="100%",
        height=500,
        returned_objects=["last_object_clicked"],
        key=f"map_vereda_detail_{modo_mapa.lower()}",
    )

    # Información detallada de la vereda
    show_vereda_detailed_info(
        casos, epizootias, vereda_selected, municipio_selected, colors
    )

    # Navegación: Botones para volver
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(
            f"🏘️ Volver a {municipio_selected}", key="back_to_municipal_from_vereda"
        ):
            st.session_state["vereda_filter"] = "Todas"
            st.rerun()
    with col2:
        if st.button("🏛️ Vista Departamental", key="back_to_dept_from_vereda"):
            st.session_state["municipio_filter"] = "Todos"
            st.session_state["vereda_filter"] = "Todas"
            st.rerun()
    with col3:
        if st.button("🔄 Actualizar Vista", key="refresh_vereda_view"):
            st.rerun()


def filter_veredas_for_detailed_view(veredas_data, vereda_selected):
    """Filtra veredas para vista detallada: vereda específica + contexto."""
    vereda_col = get_vereda_column(veredas_data)

    if not vereda_col or vereda_col not in veredas_data.columns:
        return pd.DataFrame(), pd.DataFrame()

    try:
        # Vereda específica (exacta)
        mask_exacta = (
            veredas_data[vereda_col].astype(str).str.strip()
            == str(vereda_selected).strip()
        )
        vereda_especifica = veredas_data[mask_exacta]

        # Veredas de contexto (resto del municipio)
        veredas_contexto = veredas_data[~mask_exacta]

        logger.info(
            f"🎯 Vereda específica: {len(vereda_especifica)} | Contexto: {len(veredas_contexto)}"
        )

        return vereda_especifica, veredas_contexto

    except Exception as e:
        logger.error(f"❌ Error filtrando veredas para vista detallada: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()


def create_folium_map_focused_on_vereda(vereda_gdf, zoom_start=12):
    """Crea mapa enfocado en una vereda específica."""
    try:
        if vereda_gdf.empty:
            # Fallback: mapa genérico del Tolima
            return folium.Map(
                location=[4.2, -75.2],
                zoom_start=zoom_start,
                tiles="CartoDB positron",
                attributionControl=False,
                zoom_control=True,
                scrollWheelZoom=True,
            )

        # Obtener bounds de la vereda específica
        bounds = vereda_gdf.total_bounds  # [minx, miny, maxx, maxy]
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles="CartoDB positron",
            attributionControl=False,
            zoom_control=True,
            scrollWheelZoom=True,
        )

        # Ajustar vista a la vereda
        try:
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        except Exception as e:
            logger.warning(f"⚠️ Error ajustando bounds: {str(e)}")

        return m

    except Exception as e:
        logger.error(f"❌ Error creando mapa enfocado en vereda: {str(e)}")
        # Fallback
        return folium.Map(
            location=[4.2, -75.2],
            zoom_start=zoom_start,
            tiles="CartoDB positron",
        )


def add_vereda_highlighted_to_map(
    folium_map, vereda_gdf, colors, modo_mapa, is_target=True
):
    """Agrega vereda resaltada al mapa."""
    if vereda_gdf.empty:
        return

    vereda_col = get_vereda_column(vereda_gdf)

    for idx, row in vereda_gdf.iterrows():
        try:
            vereda_name = safe_get_feature_name(row, vereda_col) or "VEREDA DESCONOCIDA"
            color = row.get("color", colors["primary"])

            # Estilo especial para vereda objetivo
            if is_target:
                style_function = lambda x, color=color: {
                    "fillColor": color,
                    "color": colors["primary"],
                    "weight": 4,  # Borde más grueso
                    "fillOpacity": 0.8,  # Más opaco
                    "opacity": 1,
                    "dashArray": "5,5",  # Línea punteada para destacar
                }

                # Tooltip especial para vereda objetivo
                tooltip_text = f"""
                <div style="font-family: Arial; padding: 12px; max-width: 250px; text-align: center;">
                    <b style="color: {colors['primary']}; font-size: 1.2em;">🎯 {vereda_name}</b><br>
                    <div style="background: {colors['secondary']}; color: white; padding: 6px; border-radius: 4px; margin: 8px 0;">
                        <strong>VEREDA SELECCIONADA</strong>
                    </div>
                    <div style="margin: 8px 0; padding: 6px; background: #f8f9fa; border-radius: 4px;">
                        🦠 Casos: {row.get('casos', 0)}<br>
                        🐒 Epizootias: {row.get('epizootias', 0)}<br>
                    </div>
                    <div style="color: {colors['info']}; font-size: 0.9em;">
                        {row.get('descripcion_color', 'Sin clasificar')}
                    </div>
                </div>
                """
            else:
                style_function = lambda x, color=color: {
                    "fillColor": color,
                    "color": colors["accent"],
                    "weight": 1.5,
                    "fillOpacity": 0.6,
                    "opacity": 0.8,
                }
                tooltip_text = create_vereda_tooltip_simplified(
                    vereda_name, row, colors, modo_mapa
                )

            folium.GeoJson(
                row["geometry"],
                style_function=style_function,
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            ).add_to(folium_map)

        except Exception as e:
            logger.warning(
                f"⚠️ Error agregando vereda resaltada {vereda_name}: {str(e)}"
            )


def add_veredas_context_to_map(folium_map, veredas_contexto, colors, modo_mapa):
    """Agrega veredas de contexto al mapa (más transparentes)."""
    if veredas_contexto.empty:
        return

    vereda_col = get_vereda_column(veredas_contexto)

    for idx, row in veredas_contexto.iterrows():
        try:
            vereda_name = safe_get_feature_name(row, vereda_col) or "VEREDA CONTEXTO"
            color = row.get("color", colors["info"])

            # Estilo más transparente para contexto
            style_function = lambda x, color=color: {
                "fillColor": color,
                "color": "#888888",
                "weight": 1,
                "fillOpacity": 0.3,  # Muy transparente
                "opacity": 0.5,
            }

            # Tooltip simple para contexto
            tooltip_text = f"""
            <div style="font-family: Arial; padding: 8px; max-width: 180px;">
                <b style="color: {colors['accent']};">🏘️ {vereda_name}</b><br>
                <div style="font-size: 0.85em; margin: 4px 0;">
                    🦠 {row.get('casos', 0)} • 🐒 {row.get('epizootias', 0)}
                </div>
                <i style="color: #666; font-size: 0.75em;">👆 Clic para seleccionar</i>
            </div>
            """

            folium.GeoJson(
                row["geometry"],
                style_function=style_function,
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            ).add_to(folium_map)

        except Exception as e:
            logger.warning(f"⚠️ Error agregando vereda de contexto: {str(e)}")


def show_vereda_detailed_info(
    casos, epizootias, vereda_selected, municipio_selected, colors
):
    """Muestra información detallada de la vereda seleccionada."""
    st.markdown("---")

    # Filtrar datos específicos de la vereda
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""

    vereda_norm = normalize_name(vereda_selected)
    municipio_norm = normalize_name(municipio_selected)

    # Casos en esta vereda
    casos_vereda = pd.DataFrame()
    if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
        casos_vereda = casos[
            (casos["vereda"].apply(normalize_name) == vereda_norm)
            & (casos["municipio"].apply(normalize_name) == municipio_norm)
        ]

    # Epizootias en esta vereda
    epi_vereda = pd.DataFrame()
    if (
        not epizootias.empty
        and "vereda" in epizootias.columns
        and "municipio" in epizootias.columns
    ):
        epi_vereda = epizootias[
            (epizootias["vereda"].apply(normalize_name) == vereda_norm)
            & (epizootias["municipio"].apply(normalize_name) == municipio_norm)
        ]

    # Mostrar datos tabulares si hay información
    if not casos_vereda.empty or not epi_vereda.empty:
        col1, col2 = st.columns(2)

        with col1:
            if not casos_vereda.empty:
                st.markdown("##### 🦠 Casos en esta Vereda")
                casos_display = (
                    casos_vereda[
                        ["fecha_inicio_sintomas", "edad", "sexo", "condicion_final"]
                    ].copy()
                    if all(
                        col in casos_vereda.columns
                        for col in [
                            "fecha_inicio_sintomas",
                            "edad",
                            "sexo",
                            "condicion_final",
                        ]
                    )
                    else casos_vereda
                )
                st.dataframe(
                    casos_display, use_container_width=True, height=200, hide_index=True
                )

        with col2:
            if not epi_vereda.empty:
                st.markdown("##### 🐒 Epizootias en esta Vereda")
                epi_display = (
                    epi_vereda[
                        ["fecha_notificacion", "descripcion", "proveniente"]
                    ].copy()
                    if all(
                        col in epi_vereda.columns
                        for col in ["fecha_notificacion", "descripcion", "proveniente"]
                    )
                    else epi_vereda
                )
                st.dataframe(
                    epi_display, use_container_width=True, height=200, hide_index=True
                )
    else:
        st.info(f"📭 No hay casos ni epizootias registrados en {vereda_selected}")
        st.markdown(
            f"Esta vereda está incluida en el shapefile de {municipio_selected} pero no tiene eventos epidemiológicos registrados hasta la fecha."
        )

# ===== MAPAS SIMPLIFICADOS =====

def create_departmental_map_simplified(
    casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
):
    """Mapa departamental."""
    municipios = geo_data["municipios"].copy()
    logger.info(
        f"🏛️ Mapa departamental {modo_mapa}: {len(municipios)} municipios"
    )

    if modo_mapa == "Epidemiológico":
        municipios_data = prepare_municipal_data_epidemiological_simplified(
            casos, epizootias, municipios, colors
        )
    else:
        municipios_data = prepare_municipal_data_coverage_simplified(
            municipios, filters, colors
        )

    m = create_folium_map(municipios_data, zoom_start=8)
    add_municipios_to_map_simplified(m, municipios_data, colors, modo_mapa)

    map_data = st_folium(
        m,
        width="100%",
        height=500,
        returned_objects=["last_object_clicked"],
        key=f"map_dept_simple_{modo_mapa.lower()}",
    )

    # CORREGIDO: Manejo de clics simplificado
    handle_map_click_simplified(
        map_data, municipios_data, "municipio", filters, data_filtered
    )

def create_multiple_selection_map_simplified(
    casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
):
    """Mapa para selección múltiple."""
    municipios_seleccionados = filters.get("municipios_seleccionados", [])
    veredas_seleccionadas = filters.get("veredas_seleccionadas", [])

    logger.info(
        f"🗂️ Filtrado múltiple: {len(municipios_seleccionados)} municipios, {len(veredas_seleccionadas)} veredas"
    )

    # ===== VERIFICACIÓN ROBUSTA =====
    if not municipios_seleccionados and not veredas_seleccionadas:
        logger.warning("⚠️ create_multiple_selection_map_simplified llamado sin selecciones")
        st.warning("⚠️ Error interno: función múltiple llamada sin selecciones")
        return

    if not municipios_seleccionados:
        st.warning("⚠️ No hay municipios seleccionados para el análisis múltiple")
        return

    # ===== INFORMACIÓN DE SELECCIÓN =====
    st.markdown(f"#### 🗂️ Vista Múltiple: {len(municipios_seleccionados)} Municipios")

    municipios_texto = ", ".join(municipios_seleccionados[:3])
    if len(municipios_seleccionados) > 3:
        municipios_texto += f" y {len(municipios_seleccionados) - 3} más"

    st.markdown(f"📍 **Municipios:** {municipios_texto}")

    if veredas_seleccionadas:
        veredas_texto = ", ".join(veredas_seleccionadas[:3])
        if len(veredas_seleccionadas) > 3:
            veredas_texto += f" y {len(veredas_seleccionadas) - 3} más"
        st.markdown(f"🏘️ **Veredas:** {veredas_texto}")

    # ===== DECISIÓN DE TIPO DE MAPA =====
    if not veredas_seleccionadas:
        # Solo municipios → mapa de municipios
        logger.info("🏛️ Creando mapa de municipios múltiples")
        create_multiple_municipios_map(
            casos,
            epizootias,
            geo_data,
            municipios_seleccionados,
            filters,
            colors,
            modo_mapa,
        )
    else:
        # Veredas específicas → mapa de veredas
        logger.info("🏘️ Creando mapa de veredas múltiples")
        create_multiple_veredas_map(
            casos,
            epizootias,
            geo_data,
            municipios_seleccionados,
            veredas_seleccionadas,
            filters,
            colors,
            modo_mapa,
        )

    # ===== BOTONES DE NAVEGACIÓN =====
    create_multiple_selection_navigation_buttons(municipios_seleccionados, veredas_seleccionadas)

def create_multiple_selection_navigation_buttons(municipios_seleccionados, veredas_seleccionadas):
    """Botones de navegación para selección múltiple."""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏛️ Vista Departamental", key="multiple_to_dept"):
            # Limpiar filtros múltiples
            st.session_state["municipios_multiselect"] = []
            st.session_state["veredas_multiselect"] = []
            # Cambiar a modo único
            st.session_state["filtro_modo"] = "Único"
            st.session_state["municipio_filter"] = "Todos"
            st.session_state["vereda_filter"] = "Todas"
            st.rerun()
    
    with col2:
        if veredas_seleccionadas and st.button("🏘️ Solo Municipios", key="multiple_clear_veredas"):
            # Limpiar solo veredas, mantener municipios
            st.session_state["veredas_multiselect"] = []
            st.rerun()
    
    with col3:
        if st.button("🗑️ Limpiar Todo", key="multiple_clear_all"):
            # Limpiar toda la selección múltiple
            st.session_state["municipios_multiselect"] = []
            st.session_state["veredas_multiselect"] = []
            st.rerun()

def filter_shapefile_by_selected_municipios(municipios_gdf, municipios_seleccionados):
    """Filtra shapefile por municipios seleccionados."""
    municipio_col = get_municipio_column(municipios_gdf)

    if not municipio_col:
        return pd.DataFrame()

    municipios_filtrados = pd.DataFrame()

    for municipio_selected in municipios_seleccionados:
        # Buscar en shapefile usando mapeo bidireccional
        municipio_en_shapefile = find_municipio_name_in_shapefile(
            municipio_selected, municipios_gdf, municipio_col
        )

        if municipio_en_shapefile:
            mask = (
                municipios_gdf[municipio_col].astype(str).str.strip()
                == str(municipio_en_shapefile).strip()
            )
            municipio_match = municipios_gdf[mask]
            if not municipio_match.empty:
                municipios_filtrados = pd.concat(
                    [municipios_filtrados, municipio_match], ignore_index=True
                )

    return municipios_filtrados


def prepare_multiple_municipios_epidemiological(
    casos, epizootias, municipios_filtrados, municipios_seleccionados, colors
):
    """Prepara datos epidemiológicos para múltiples municipios."""
    # Usar la función existente pero solo para los municipios filtrados
    return prepare_municipal_data_epidemiological_simplified(
        casos, epizootias, municipios_filtrados, colors
    )


def show_municipios_mapping_info(municipios_seleccionados, municipios_gdf):
    """Muestra información de mapeo para municipios no encontrados."""
    municipio_col = get_municipio_column(municipios_gdf)

    if municipio_col:
        municipios_disponibles = sorted(municipios_gdf[municipio_col].dropna().unique())

        st.info(
            f"**Municipios seleccionados no encontrados en shapefile:**\n\n"
            f"{', '.join(municipios_seleccionados)}\n\n"
            f"**Municipios disponibles en shapefile:**\n\n"
            f"{', '.join(municipios_disponibles[:10])}"
            f"{f' y {len(municipios_disponibles)-10} más...' if len(municipios_disponibles) > 10 else ''}\n\n"
            f"**Sugerencia:** Verificar mapeo en MUNICIPIO_MAPPING"
        )


def create_multiple_municipios_map(
    casos, epizootias, geo_data, municipios_seleccionados, filters, colors, modo_mapa
):
    """Mapa para múltiples municipios seleccionados."""
    st.markdown("##### 🏛️ Mapa de Municipios Seleccionados")

    municipios_gdf = geo_data["municipios"].copy()

    # Filtrar solo los municipios seleccionados
    municipios_filtrados = filter_shapefile_by_selected_municipios(
        municipios_gdf, municipios_seleccionados
    )

    if municipios_filtrados.empty:
        st.warning("⚠️ No se encontraron los municipios seleccionados en el shapefile")
        show_municipios_mapping_info(municipios_seleccionados, municipios_gdf)
        return

    # Preparar datos según modo
    if modo_mapa == "Epidemiológico":
        municipios_data = prepare_multiple_municipios_epidemiological(
            casos, epizootias, municipios_filtrados, municipios_seleccionados, colors
        )
    else:
        municipios_data = prepare_municipal_data_coverage_simplified(
            municipios_filtrados, filters, colors
        )

    # Crear mapa
    m = create_folium_map(municipios_data, zoom_start=8)
    add_municipios_to_map_simplified(m, municipios_data, colors, modo_mapa)

    map_data = st_folium(
        m,
        width="100%",
        height=500,
        returned_objects=["last_object_clicked"],
        key=f"map_multiple_mun_{modo_mapa.lower()}",
    )


def filter_veredas_by_selected_names(veredas_gdf, veredas_seleccionadas):
    """Filtra veredas por nombres seleccionados."""
    vereda_col = get_vereda_column(veredas_gdf)

    if not vereda_col:
        return pd.DataFrame()

    veredas_filtradas = pd.DataFrame()

    for vereda_selected in veredas_seleccionadas:
        mask = (
            veredas_gdf[vereda_col].astype(str).str.strip()
            == str(vereda_selected).strip()
        )
        vereda_match = veredas_gdf[mask]
        if not vereda_match.empty:
            veredas_filtradas = pd.concat(
                [veredas_filtradas, vereda_match], ignore_index=True
            )

    return veredas_filtradas


def prepare_multiple_veredas_epidemiological(
    casos, epizootias, veredas_filtradas, municipios_seleccionados, colors
):
    """Prepara datos epidemiológicos para múltiples veredas."""
    veredas_data = veredas_filtradas.copy()
    color_scheme = get_color_scheme_epidemiological(colors)

    vereda_col = get_vereda_column(veredas_data)
    municipio_col = get_municipio_column(veredas_data)

    if not vereda_col or not municipio_col:
        return veredas_data

    # Procesar cada vereda individualmente
    for idx, row in veredas_data.iterrows():
        try:
            vereda_name = safe_get_feature_name(row, vereda_col)
            municipio_name = safe_get_feature_name(row, municipio_col)

            if not vereda_name or not municipio_name:
                continue

            # Mapear nombre de municipio del shapefile a datos
            municipio_en_datos = get_mapped_municipio(municipio_name)

            # Filtrar casos y epizootias para esta vereda específica
            casos_vereda = pd.DataFrame()
            epi_vereda = pd.DataFrame()

            if (
                not casos.empty
                and "vereda" in casos.columns
                and "municipio" in casos.columns
            ):
                mask_casos = (
                    casos["vereda"].astype(str).str.strip() == str(vereda_name).strip()
                ) & (
                    casos["municipio"].astype(str).str.strip()
                    == str(municipio_en_datos).strip()
                )
                casos_vereda = casos[mask_casos]

            if (
                not epizootias.empty
                and "vereda" in epizootias.columns
                and "municipio" in epizootias.columns
            ):
                mask_epi = (
                    epizootias["vereda"].astype(str).str.strip()
                    == str(vereda_name).strip()
                ) & (
                    epizootias["municipio"].astype(str).str.strip()
                    == str(municipio_en_datos).strip()
                )
                epi_vereda = epizootias[mask_epi]

            # Calcular métricas
            casos_count = len(casos_vereda)
            epizootias_count = len(epi_vereda)
            fallecidos_count = (
                len(casos_vereda[casos_vereda["condicion_final"] == "Fallecido"])
                if not casos_vereda.empty and "condicion_final" in casos_vereda.columns
                else 0
            )
            positivas_count = (
                len(epi_vereda[epi_vereda["descripcion"] == "POSITIVO FA"])
                if not epi_vereda.empty and "descripcion" in epi_vereda.columns
                else 0
            )
            en_estudio_count = (
                len(epi_vereda[epi_vereda["descripcion"] == "EN ESTUDIO"])
                if not epi_vereda.empty and "descripcion" in epi_vereda.columns
                else 0
            )

            # Determinar color
            color, descripcion = determine_feature_color_epidemiological(
                casos_count,
                epizootias_count,
                fallecidos_count,
                positivas_count,
                en_estudio_count,
                color_scheme,
            )

            # Asignar valores
            veredas_data.loc[idx, "color"] = color
            veredas_data.loc[idx, "descripcion_color"] = descripcion
            veredas_data.loc[idx, "casos"] = casos_count
            veredas_data.loc[idx, "fallecidos"] = fallecidos_count
            veredas_data.loc[idx, "epizootias"] = epizootias_count
            veredas_data.loc[idx, "positivas"] = positivas_count
            veredas_data.loc[idx, "en_estudio"] = en_estudio_count

        except Exception as e:
            logger.warning(
                f"⚠️ Error procesando vereda múltiple en fila {idx}: {str(e)}"
            )
            # Valores por defecto
            veredas_data.loc[idx, "color"] = color_scheme.get("sin_datos", "#E5E7EB")
            veredas_data.loc[idx, "descripcion_color"] = "Sin datos"
            veredas_data.loc[idx, "casos"] = 0
            veredas_data.loc[idx, "fallecidos"] = 0
            veredas_data.loc[idx, "epizootias"] = 0
            veredas_data.loc[idx, "positivas"] = 0
            veredas_data.loc[idx, "en_estudio"] = 0

    return veredas_data


def show_veredas_mapping_info(veredas_seleccionadas, veredas_gdf):
    """Muestra información de mapeo para veredas no encontradas."""
    vereda_col = get_vereda_column(veredas_gdf)

    if vereda_col:
        veredas_disponibles = sorted(veredas_gdf[vereda_col].dropna().unique())

        st.info(
            f"**Veredas seleccionadas no encontradas:**\n\n"
            f"{', '.join(veredas_seleccionadas[:10])}\n\n"
            f"**Veredas disponibles en shapefiles:**\n\n"
            f"{', '.join(veredas_disponibles[:15])}"
            f"{f' y {len(veredas_disponibles)-15} más...' if len(veredas_disponibles) > 15 else ''}"
        )

def verify_cobertura_dependencies():
    """
    ✅ NUEVA FUNCIÓN: Verifica que todas las dependencias de cobertura estén disponibles
    """
    try:
        from utils.cobertura_processor import (
            get_cobertura_for_vereda,
            get_cobertura_for_municipio,
            load_and_process_cobertura_data
        )
        return True
    except ImportError as e:
        logger.error(f"❌ Dependencias de cobertura faltantes: {str(e)}")
        return False

def safe_mode_multiple_fallback(veredas_filtradas, colors):
    """
    ✅ NUEVA FUNCIÓN: Fallback seguro cuando hay errores en modo múltiple
    """
    logger.info("🛡️ Usando fallback seguro para modo múltiple")
    
    veredas_data = veredas_filtradas.copy()
    color_scheme = get_color_scheme_coverage(colors)
    
    # Inicializar todas las columnas necesarias
    required_columns = ["color", "descripcion_color", "cobertura", "poblacion", "vacunados"]
    for col in required_columns:
        veredas_data[col] = color_scheme.get("sin_datos", "#E5E7EB") if col == "color" else (
            "Modo seguro - sin datos" if col == "descripcion_color" else 0
        )
    
    return veredas_data

def create_multiple_veredas_map(casos, epizootias, geo_data, municipios_seleccionados, veredas_seleccionadas, filters, colors, modo_mapa):
    """
    ✅ VERSIÓN COMPLETAMENTE CORREGIDA con manejo robusto de errores
    """
    st.markdown("##### 🏘️ Mapa de Veredas Seleccionadas")
    
    # ✅ VALIDACIONES INICIALES TEMPRANAS
    if not municipios_seleccionados:
        municipios_seleccionados = []
    if not veredas_seleccionadas:
        veredas_seleccionadas = []
        
    # Validaciones iniciales de datos
    if not geo_data or "veredas" not in geo_data:
        st.error("❌ No hay datos de veredas disponibles")
        return

    veredas_gdf = geo_data["veredas"].copy()

    # Recopilar veredas de todos los municipios seleccionados
    todas_las_veredas = pd.DataFrame()

    for municipio in municipios_seleccionados:
        try:
            veredas_municipio = find_veredas_for_municipio_simplified(veredas_gdf, municipio)
            if not veredas_municipio.empty:
                todas_las_veredas = pd.concat([todas_las_veredas, veredas_municipio], ignore_index=True)
        except Exception as e:
            logger.error(f"❌ Error obteniendo veredas para {municipio}: {str(e)}")
            continue

    if todas_las_veredas.empty:
        st.warning(f"⚠️ No se encontraron veredas para los municipios: {', '.join(municipios_seleccionados)}")
        return

    # Filtrar solo las veredas seleccionadas
    veredas_filtradas = filter_veredas_by_selected_names(todas_las_veredas, veredas_seleccionadas)

    if veredas_filtradas.empty:
        st.warning(f"⚠️ No se encontraron las veredas seleccionadas en los shapefiles")
        show_veredas_mapping_info(veredas_seleccionadas, todas_las_veredas)
        return

    # ===== PREPARAR DATOS SEGÚN MODO CON MANEJO DE ERRORES ROBUSTO =====
    try:
        if modo_mapa == "Epidemiológico":
            veredas_data = prepare_multiple_veredas_epidemiological(
                casos, epizootias, veredas_filtradas, municipios_seleccionados, colors
            )
        else:
            # ✅ USAR FUNCIÓN CORREGIDA
            veredas_data = prepare_multiple_veredas_coverage_fixed(
                veredas_filtradas, municipios_seleccionados, colors
            )
        
        if veredas_data.empty:
            st.error("❌ No se pudieron procesar los datos de veredas")
            return
            
    except Exception as e:
        error_msg = f"Error preparando datos de veredas: {str(e)}"
        logger.error(f"❌ {error_msg}")
        st.error(error_msg)
        
        # ✅ MOSTRAR DEBUG INFO MEJORADO
        with st.expander("🔧 Información de Debug", expanded=True):
            st.write(f"**Error específico:** {str(e)}")
            st.write(f"**Modo mapa:** {modo_mapa}")
            st.write(f"**Municipios seleccionados:** {municipios_seleccionados}")
            st.write(f"**Veredas seleccionadas:** {len(veredas_seleccionadas)}")
            st.write(f"**Veredas filtradas shape:** {veredas_filtradas.shape}")
            
            # Mostrar traceback si está disponible
            import traceback
            st.code(traceback.format_exc())
        return

    # Crear mapa solo si los datos están listos
    try:
        m = create_folium_map(veredas_data, zoom_start=9)
        add_veredas_to_map_simplified(m, veredas_data, colors, modo_mapa)

        map_data = st_folium(
            m,
            width="100%",
            height=500,
            returned_objects=["last_object_clicked"],
            key=f"map_multiple_ver_{modo_mapa.lower()}",
        )
        
    except Exception as e:
        error_msg = f"Error creando mapa: {str(e)}"
        logger.error(f"❌ {error_msg}")
        st.error(error_msg)
    
def prepare_multiple_veredas_coverage_fixed(veredas_filtradas, municipios_seleccionados, colors):
    """
    ✅ VERSIÓN COMPLETAMENTE CORREGIDA - Manejo robusto de errores
    """
    logger.info(f"🏘️ Preparando cobertura para {len(veredas_filtradas)} veredas múltiples")
    
    if veredas_filtradas.empty:
        logger.error("❌ veredas_filtradas está vacío")
        return pd.DataFrame()
    
    veredas_data = veredas_filtradas.copy()
    color_scheme = get_color_scheme_coverage(colors)
    
    # ✅ CORRECCIÓN CRÍTICA: INICIALIZAR TODAS LAS COLUMNAS REQUERIDAS
    required_columns = {
        "color": color_scheme.get("sin_datos", "#E5E7EB"),
        "descripcion_color": "Sin datos de cobertura",
        "cobertura": 0.0,
        "poblacion": 0,
        "vacunados": 0
    }
    
    for col, default_value in required_columns.items():
        veredas_data[col] = default_value
    
    logger.info(f"✅ Columnas inicializadas: {list(required_columns.keys())}")
    
    # ===== CARGAR DATOS DE COBERTURA CON MANEJO DE ERRORES =====
    try:
        cobertura_data = load_cobertura_data_with_fallback()
    except Exception as e:
        logger.error(f"❌ Error cargando datos de cobertura: {str(e)}")
        cobertura_data = None
    
    if not cobertura_data:
        logger.warning("⚠️ Sin datos de cobertura - usando valores por defecto")
        return veredas_data  # Ya está inicializado con valores por defecto
    
    # ===== PROCESAR CADA VEREDA CON MANEJO DE ERRORES ROBUSTO =====
    vereda_col = get_vereda_column(veredas_data)
    municipio_col = get_municipio_column(veredas_data)
    
    if not vereda_col or not municipio_col:
        logger.error("❌ No se encontraron columnas de vereda o municipio")
        return veredas_data  # Retornar con valores por defecto
    
    for idx in veredas_data.index:
        try:
            row = veredas_data.loc[idx]
            vereda_name = safe_get_feature_name(row, vereda_col)
            municipio_name_shapefile = safe_get_feature_name(row, municipio_col)
            
            if not vereda_name or not municipio_name_shapefile:
                continue  # Mantener valores por defecto
            
            # Mapear municipio del shapefile a datos
            municipio_en_datos = find_matching_municipio_for_multiple(
                municipio_name_shapefile, municipios_seleccionados
            )
            
            if not municipio_en_datos:
                continue  # Mantener valores por defecto
            
            # Buscar datos de cobertura con manejo de errores
            try:
                vereda_coverage = get_cobertura_for_vereda(
                    cobertura_data, municipio_en_datos, vereda_name
                )
                
                if vereda_coverage and isinstance(vereda_coverage, dict):
                    cobertura = safe_float_conversion(vereda_coverage.get("cobertura", 0.0))
                    poblacion = safe_int_conversion(vereda_coverage.get("poblacion", 0))
                    vacunados = safe_int_conversion(vereda_coverage.get("vacunados", 0))
                    
                    # Validar consistencia de datos
                    if poblacion <= 0 and vacunados > 0:
                        logger.warning(f"⚠️ {vereda_name}: datos inconsistentes")
                        continue  # Mantener valores por defecto
                    
                    if poblacion > 0:  # Solo asignar si hay población válida
                        color, descripcion = determine_feature_color_coverage_safe(
                            cobertura, poblacion, color_scheme
                        )
                        
                        veredas_data.loc[idx, "color"] = color
                        veredas_data.loc[idx, "descripcion_color"] = descripcion
                        veredas_data.loc[idx, "cobertura"] = cobertura
                        veredas_data.loc[idx, "poblacion"] = poblacion
                        veredas_data.loc[idx, "vacunados"] = vacunados
                        
                        logger.debug(f"  ✅ {vereda_name}: {cobertura:.1f}%")
                
            except Exception as e:
                logger.warning(f"⚠️ Error obteniendo cobertura para {vereda_name}: {str(e)}")
                # Mantener valores por defecto
                continue
        
        except Exception as e:
            logger.error(f"❌ Error procesando vereda en fila {idx}: {str(e)}")
            # Mantener valores por defecto
            continue
    
    logger.info(f"✅ Preparación múltiple completada: {len(veredas_data)} veredas procesadas")
    return veredas_data

def safe_float_conversion(value, default=0.0):
    """Convierte a float de manera segura."""
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int_conversion(value, default=0):
    """Convierte a int de manera segura."""
    try:
        if value is None or pd.isna(value):
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def load_cobertura_data_with_fallback():
    """Carga datos de cobertura con manejo robusto de errores."""
    try:
        from utils.cobertura_processor import load_and_process_cobertura_data
        return load_and_process_cobertura_data()
    except ImportError:
        logger.warning("⚠️ utils.cobertura_processor no disponible")
        return None
    except Exception as e:
        logger.error(f"❌ Error en load_and_process_cobertura_data: {str(e)}")
        return None

def find_matching_municipio_for_multiple(municipio_name_shapefile, municipios_seleccionados):
    """
    ✅ NUEVA FUNCIÓN: Encuentra municipio correspondiente en selección múltiple
    """
    try:
        # 1. Coincidencia directa
        for municipio_seleccionado in municipios_seleccionados:
            if simple_name_match(municipio_name_shapefile, municipio_seleccionado):
                return municipio_seleccionado
        
        # 2. Usando mapeo
        mapped_municipio = get_mapped_municipio(municipio_name_shapefile, "shapefile_to_data")
        for municipio_seleccionado in municipios_seleccionados:
            if simple_name_match(mapped_municipio, municipio_seleccionado):
                return municipio_seleccionado
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error mapeando {municipio_name_shapefile}: {str(e)}")
        return None

def determine_feature_color_coverage_safe(cobertura, poblacion, color_scheme):
    """
    ✅ NUEVA FUNCIÓN: Determina color de manera segura sin KeyError
    """
    try:
        # Validar entrada
        if pd.isna(cobertura) or cobertura is None or poblacion <= 0:
            return color_scheme.get("sin_datos", "#E5E7EB"), "Sin datos de población"
        
        cobertura = float(cobertura)
        
        if cobertura >= 95.0:
            return color_scheme.get("cobertura_alta", "#10B981"), f"Cobertura alta: {cobertura:.1f}%"
        elif cobertura >= 80.0:
            return color_scheme.get("cobertura_buena", "#F59E0B"), f"Cobertura buena: {cobertura:.1f}%"
        elif cobertura >= 60.0:
            return color_scheme.get("cobertura_regular", "#EF4444"), f"Cobertura regular: {cobertura:.1f}%"
        elif cobertura >= 30.0:
            return color_scheme.get("cobertura_baja", "#DC2626"), f"Cobertura baja: {cobertura:.1f}%"
        elif cobertura > 0.0:
            return color_scheme.get("cobertura_muy_baja", "#991B1B"), f"Cobertura muy baja: {cobertura:.1f}%"
        else:
            return color_scheme.get("sin_datos", "#E5E7EB"), "Sin cobertura de vacunación"
    
    except Exception as e:
        logger.error(f"❌ Error determinando color: {str(e)}")
        return color_scheme.get("sin_datos", "#E5E7EB"), "Error en coloreo"

def create_municipal_map_simplified(
    casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
):
    """Mapa municipal."""
    try:
        logger.info(f"🏘️ Iniciando mapa municipal - Modo: {modo_mapa}")

        # DEBUG: Verificar datos de entrada
        logger.info(
            f"📊 Datos de entrada - Casos: {len(casos)}, Epizootias: {len(epizootias) if epizootias is not None else 'None'}"
        )

        # Verificar y corregir epizootias si es necesario
        if epizootias is None:
            logger.warning("⚠️ Epizootias es None, creando DataFrame vacío")
            epizootias = pd.DataFrame()
        elif not isinstance(epizootias, pd.DataFrame):
            logger.warning(
                f"⚠️ Epizootias no es DataFrame ({type(epizootias)}), creando DataFrame vacío"
            )
            epizootias = pd.DataFrame()

        # Verificar el modo de filtrado
        filtro_modo = filters.get("modo", "unico")

        if filtro_modo == "multiple":
            logger.info("🗂️ Modo múltiple detectado")
            create_multiple_selection_map_simplified(
                casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
            )
            return

        # Filtrado único (código original)
        municipio_selected = filters.get("municipio_display")
        logger.info(f"📍 Municipio seleccionado: '{municipio_selected}'")

        if not municipio_selected or municipio_selected == "Todos":
            st.error("No se pudo determinar el municipio para la vista de veredas")
            return

        veredas = geo_data.get("veredas")
        if veredas is None or veredas.empty:
            st.error("No se pudieron cargar los datos de veredas")
            logger.error("❌ Datos de veredas no disponibles")
            return

        veredas = veredas.copy()

        # Buscar veredas del municipio con mapeo
        logger.info(f"🔍 Buscando veredas para municipio: {municipio_selected}")
        veredas_municipio = find_veredas_for_municipio_simplified(
            veredas, municipio_selected
        )

        if veredas_municipio.empty:
            st.warning(f"No se encontraron veredas para {municipio_selected}")
            show_available_municipios_in_shapefile(veredas, municipio_selected)
            return

        logger.info(
            f"✅ Encontradas {len(veredas_municipio)} veredas para {municipio_selected}"
        )

        # Preparar datos según modo - CON MANEJO DE ERRORES
        try:
            if modo_mapa == "Epidemiológico":
                logger.info("🔬 Preparando datos epidemiológicos")
                veredas_data = prepare_vereda_data_epidemiological_simplified(
                    casos, epizootias, veredas_municipio, municipio_selected, colors
                )
            else:
                logger.info("💉 Preparando datos de cobertura")
                veredas_data = prepare_vereda_data_coverage_simplified(
                    veredas_municipio, municipio_selected, colors
                )
        except Exception as e:
            logger.error(f"❌ Error preparando datos de veredas: {str(e)}")
            st.error(f"Error preparando datos de veredas: {str(e)}")

            # Mostrar información de debug
            st.expander("🔧 Información de Debug", expanded=False)
            with st.expander("🔧 Información de Debug"):
                st.write(f"**Municipio:** {municipio_selected}")
                st.write(f"**Modo mapa:** {modo_mapa}")
                st.write(
                    f"**Casos shape:** {casos.shape if not casos.empty else 'Vacío'}"
                )
                st.write(
                    f"**Epizootias shape:** {epizootias.shape if not epizootias.empty else 'Vacío'}"
                )
                st.write(f"**Veredas encontradas:** {len(veredas_municipio)}")
                st.write(f"**Error:** {str(e)}")
            return

        if veredas_data.empty:
            st.warning(
                f"No se pudieron procesar los datos de veredas para {municipio_selected}"
            )
            return

        # Crear mapa
        try:
            logger.info("🗺️ Creando mapa de Folium")
            m = create_folium_map(veredas_data, zoom_start=10)
            add_veredas_to_map_simplified(m, veredas_data, colors, modo_mapa)

            logger.info("🖥️ Mostrando mapa en Streamlit")
            map_data = st_folium(
                m,
                width="100%",
                height=500,
                returned_objects=["last_object_clicked"],
                key=f"map_mun_simple_{modo_mapa.lower()}_{municipio_selected}",
            )

            # Manejo de clics simplificado
            logger.info("👆 Configurando manejo de clics")
            handle_map_click_simplified(
                map_data, veredas_data, "vereda", filters, data_filtered
            )

        except Exception as e:
            logger.error(f"❌ Error creando o mostrando mapa: {str(e)}")
            st.error(f"Error creando mapa: {str(e)}")

            # Fallback: mostrar información tabular
            st.info("📊 Mostrando información tabular como alternativa:")
            show_veredas_table_fallback(veredas_data, municipio_selected, colors)
            
        st.markdown("---")
        create_municipal_navigation_buttons(municipio_selected)

    except Exception as e:
        logger.error(f"❌ Error general en create_municipal_map_simplified: {str(e)}")
        st.error(f"Error en mapa municipal: {str(e)}")

def create_municipal_navigation_buttons(municipio_actual):
    """Botones de navegación para vista municipal."""
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("🏛️ Vista Departamental", key="back_to_dept_from_municipal"):
            st.session_state["municipio_filter"] = "Todos"
            st.session_state["vereda_filter"] = "Todas"
            st.rerun()
    
    with col2:
        st.markdown(f"**📍 Ubicación actual:** {municipio_actual}")
    
    with col3:
        if st.button("🔄 Actualizar", key="refresh_municipal_view"):
            st.rerun()

def create_navigation_context_indicator(filters, colors):
    """Indicador visual del nivel de navegación actual."""
    municipio = filters.get("municipio_display", "Todos")
    vereda = filters.get("vereda_display", "Todas")
    
    if vereda != "Todas":
        nivel = f"📍 {vereda} ({municipio})"
        breadcrumb = f"Tolima → {municipio} → {vereda}"
    elif municipio != "Todos":
        nivel = f"🏘️ {municipio}"
        breadcrumb = f"Tolima → {municipio}"
    else:
        nivel = "🏛️ Tolima"
        breadcrumb = "Tolima"
    
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            text-align: center;
            margin: 10px 0;
            font-size: 0.9rem;
            font-weight: 600;
        ">
            📍 {breadcrumb}
        </div>
        """,
        unsafe_allow_html=True,
    )

def show_veredas_table_fallback(veredas_data, municipio_selected, colors):
    """Muestra tabla de veredas como fallback cuando el mapa falla."""
    try:
        vereda_col = get_vereda_column(veredas_data)

        if vereda_col and vereda_col in veredas_data.columns:
            st.markdown(f"#### 🏘️ Veredas de {municipio_selected}")

            # Crear tabla simple
            tabla_veredas = []
            for idx, row in veredas_data.iterrows():
                vereda_name = safe_get_feature_name(row, vereda_col) or f"Vereda_{idx}"
                casos = row.get("casos", 0)
                epizootias = row.get("epizootias", 0)
                descripcion = row.get("descripcion_color", "Sin datos")

                tabla_veredas.append(
                    {
                        "Vereda": vereda_name,
                        "Casos": casos,
                        "Epizootias": epizootias,
                        "Estado": descripcion,
                    }
                )

            if tabla_veredas:
                df_tabla = pd.DataFrame(tabla_veredas)
                st.dataframe(df_tabla, use_container_width=True, hide_index=True)
            else:
                st.info("No hay datos de veredas para mostrar")
        else:
            st.warning("No se pudo extraer información de veredas del shapefile")

    except Exception as e:
        logger.error(f"❌ Error en tabla fallback: {str(e)}")
        st.error(f"Error mostrando información de veredas: {str(e)}")


def debug_data_types_and_content(casos, epizootias, municipio_selected):
    """Función de debug para verificar tipos de datos y contenido."""
    logger.info("🔍 === DEBUG DATA TYPES ===")

    # Debug casos
    logger.info(f"CASOS:")
    logger.info(f"  - Tipo: {type(casos)}")
    logger.info(f"  - Shape: {casos.shape if hasattr(casos, 'shape') else 'No shape'}")
    logger.info(
        f"  - Vacío: {casos.empty if hasattr(casos, 'empty') else 'No empty attr'}"
    )
    if hasattr(casos, "columns"):
        logger.info(f"  - Columnas: {list(casos.columns)}")

    # Debug epizootias
    logger.info(f"EPIZOOTIAS:")
    logger.info(f"  - Tipo: {type(epizootias)}")
    if epizootias is not None:
        logger.info(
            f"  - Shape: {epizootias.shape if hasattr(epizootias, 'shape') else 'No shape'}"
        )
        logger.info(
            f"  - Vacío: {epizootias.empty if hasattr(epizootias, 'empty') else 'No empty attr'}"
        )
        if hasattr(epizootias, "columns"):
            logger.info(f"  - Columnas: {list(epizootias.columns)}")
    else:
        logger.info(f"  - Es None")

    # Debug municipio
    logger.info(f"MUNICIPIO: '{municipio_selected}' (tipo: {type(municipio_selected)})")

    logger.info("🔍 === FIN DEBUG ===")


def safe_data_preparation_with_debug(
    casos, epizootias, veredas_municipio, municipio_selected, colors, modo_mapa
):
    """Preparación de datos con debug y manejo de errores."""
    try:
        logger.info(f"🛠️ Preparación segura de datos para {municipio_selected}")

        # Debug de tipos de datos
        debug_data_types_and_content(casos, epizootias, municipio_selected)

        # Verificar y limpiar datos de entrada
        if casos is None:
            casos = pd.DataFrame()
        if epizootias is None:
            epizootias = pd.DataFrame()
        if not isinstance(casos, pd.DataFrame):
            casos = pd.DataFrame()
        if not isinstance(epizootias, pd.DataFrame):
            epizootias = pd.DataFrame()

        logger.info(
            f"📊 Datos limpiados - Casos: {len(casos)}, Epizootias: {len(epizootias)}"
        )

        # Preparar datos según modo
        if modo_mapa == "Epidemiológico":
            return prepare_vereda_data_epidemiological_simplified(
                casos, epizootias, veredas_municipio, municipio_selected, colors
            )
        else:
            return prepare_vereda_data_coverage_simplified(
                veredas_municipio, municipio_selected, colors
            )

    except Exception as e:
        logger.error(f"❌ Error en preparación segura: {str(e)}")

        # Retornar datos básicos con colores por defecto
        veredas_basic = veredas_municipio.copy()
        color_scheme = get_color_scheme_epidemiological(colors)

        for idx, row in veredas_basic.iterrows():
            veredas_basic.loc[idx, "color"] = color_scheme.get("sin_datos", "#E5E7EB")
            veredas_basic.loc[idx, "descripcion_color"] = "Error en procesamiento"
            veredas_basic.loc[idx, "casos"] = 0
            veredas_basic.loc[idx, "epizootias"] = 0

        return veredas_basic

# ===== PREPARACIÓN DE DATOS SIMPLIFICADA =====


def prepare_municipal_data_epidemiological_simplified(
    casos, epizootias, municipios, colors
):
    """Prepara datos municipales."""
    municipios = municipios.copy()
    color_scheme = get_color_scheme_epidemiological(colors)

    contadores_municipios = {}

    # Obtener nombres de municipios del shapefile
    municipio_col = get_municipio_column(municipios)

    if not municipio_col:
        logger.error("❌ No se encontró columna de municipios en shapefile")
        return municipios

    # Obtener lista de municipios únicos de manera segura
    try:
        municipios_unicos = municipios[municipio_col].dropna().unique()
        municipios_unicos = [str(m).strip() for m in municipios_unicos if pd.notna(m)]
        logger.info(f"📍 Procesando {len(municipios_unicos)} municipios únicos")
    except Exception as e:
        logger.error(f"❌ Error obteniendo municipios únicos: {str(e)}")
        return municipios

    # Procesar casos
    if not casos.empty and "municipio" in casos.columns:
        for shapefile_municipio in municipios_unicos:
            try:
                casos_mun = find_casos_for_shapefile_municipio(
                    casos, shapefile_municipio
                )
                fallecidos_mun = pd.DataFrame()

                if not casos_mun.empty and "condicion_final" in casos_mun.columns:
                    fallecidos_mun = casos_mun[
                        casos_mun["condicion_final"] == "Fallecido"
                    ]

                contadores_municipios[shapefile_municipio] = {
                    "casos": int(len(casos_mun)),  # Convertir a int explícitamente
                    "fallecidos": int(len(fallecidos_mun)),
                }
            except Exception as e:
                logger.warning(
                    f"⚠️ Error procesando casos para {shapefile_municipio}: {str(e)}"
                )
                contadores_municipios[shapefile_municipio] = {
                    "casos": 0,
                    "fallecidos": 0,
                }

    # Procesar epizootias
    if not epizootias.empty and "municipio" in epizootias.columns:
        for shapefile_municipio in municipios_unicos:
            try:
                if shapefile_municipio not in contadores_municipios:
                    contadores_municipios[shapefile_municipio] = {
                        "casos": 0,
                        "fallecidos": 0,
                    }

                epi_mun = find_epizootias_for_shapefile_municipio(
                    epizootias, shapefile_municipio
                )
                positivas_mun = pd.DataFrame()
                en_estudio_mun = pd.DataFrame()

                if not epi_mun.empty and "descripcion" in epi_mun.columns:
                    positivas_mun = epi_mun[epi_mun["descripcion"] == "POSITIVO FA"]
                    en_estudio_mun = epi_mun[epi_mun["descripcion"] == "EN ESTUDIO"]

                contadores_municipios[shapefile_municipio].update(
                    {
                        "epizootias": int(len(epi_mun)),
                        "positivas": int(len(positivas_mun)),
                        "en_estudio": int(len(en_estudio_mun)),
                    }
                )
            except Exception as e:
                logger.warning(
                    f"⚠️ Error procesando epizootias para {shapefile_municipio}: {str(e)}"
                )
                if shapefile_municipio in contadores_municipios:
                    contadores_municipios[shapefile_municipio].update(
                        {
                            "epizootias": 0,
                            "positivas": 0,
                            "en_estudio": 0,
                        }
                    )

    # Aplicar colores
    municipios_data = municipios.copy()

    for idx, row in municipios_data.iterrows():
        try:
            # Obtener nombre de manera segura
            shapefile_municipio = safe_get_feature_name(row, municipio_col)

            if not shapefile_municipio:
                logger.warning(f"⚠️ No se pudo obtener nombre para fila {idx}")
                continue

            # Obtener contadores de manera segura
            contadores = contadores_municipios.get(
                shapefile_municipio,
                {
                    "casos": 0,
                    "fallecidos": 0,
                    "epizootias": 0,
                    "positivas": 0,
                    "en_estudio": 0,
                },
            )

            # Asegurar que todos los valores sean enteros
            casos_count = int(contadores.get("casos", 0))
            epizootias_count = int(contadores.get("epizootias", 0))
            fallecidos_count = int(contadores.get("fallecidos", 0))
            positivas_count = int(contadores.get("positivas", 0))
            en_estudio_count = int(contadores.get("en_estudio", 0))

            color, descripcion = determine_feature_color_epidemiological(
                casos_count,
                epizootias_count,
                fallecidos_count,
                positivas_count,
                en_estudio_count,
                color_scheme,
            )

            # Asignar valores de manera segura
            municipios_data.loc[idx, "color"] = color
            municipios_data.loc[idx, "descripcion_color"] = descripcion
            municipios_data.loc[idx, "casos"] = casos_count
            municipios_data.loc[idx, "fallecidos"] = fallecidos_count
            municipios_data.loc[idx, "epizootias"] = epizootias_count
            municipios_data.loc[idx, "positivas"] = positivas_count
            municipios_data.loc[idx, "en_estudio"] = en_estudio_count

        except Exception as e:
            logger.error(f"❌ Error procesando fila {idx}: {str(e)}")
            # Asignar valores por defecto en caso de error
            municipios_data.loc[idx, "color"] = color_scheme["sin_datos"]
            municipios_data.loc[idx, "descripcion_color"] = "Error en procesamiento"
            municipios_data.loc[idx, "casos"] = 0
            municipios_data.loc[idx, "fallecidos"] = 0
            municipios_data.loc[idx, "epizootias"] = 0
            municipios_data.loc[idx, "positivas"] = 0
            municipios_data.loc[idx, "en_estudio"] = 0

    logger.info("✅ Datos municipales epidemiológicos preparados CORREGIDOS")
    return municipios_data


def find_casos_for_shapefile_municipio(casos, shapefile_municipio):
    """Encuentra casos para municipio del shapefile - CORREGIDO con mapeo bidireccional."""
    if casos.empty or "municipio" not in casos.columns:
        return pd.DataFrame()

    try:
        shapefile_municipio = str(shapefile_municipio).strip()

        # 1. Buscar coincidencia directa
        mask_directa = casos["municipio"].astype(str).str.strip() == shapefile_municipio
        casos_directos = casos[mask_directa]

        if not casos_directos.empty:
            logger.debug(
                f"✅ Casos encontrados por coincidencia directa: {shapefile_municipio}"
            )
            return casos_directos

        # 2. Buscar usando mapeo (shapefile → datos)
        mapped_municipio = get_mapped_municipio(
            shapefile_municipio, "shapefile_to_data"
        )
        if mapped_municipio != shapefile_municipio:
            mask_mapeada = (
                casos["municipio"].astype(str).str.strip() == mapped_municipio
            )
            casos_mapeados = casos[mask_mapeada]

            if not casos_mapeados.empty:
                logger.debug(
                    f"✅ Casos encontrados por mapeo: {shapefile_municipio} → {mapped_municipio}"
                )
                return casos_mapeados

        return pd.DataFrame()

    except Exception as e:
        logger.warning(f"⚠️ Error buscando casos para {shapefile_municipio}: {str(e)}")
        return pd.DataFrame()


def find_epizootias_for_shapefile_municipio(epizootias, shapefile_municipio):
    """Encuentra epizootias para municipio del shapefile - CORREGIDO con mapeo bidireccional."""
    if epizootias.empty or "municipio" not in epizootias.columns:
        return pd.DataFrame()

    try:
        shapefile_municipio = str(shapefile_municipio).strip()

        # 1. Buscar coincidencia directa
        mask_directa = (
            epizootias["municipio"].astype(str).str.strip() == shapefile_municipio
        )
        epi_directos = epizootias[mask_directa]

        if not epi_directos.empty:
            logger.debug(
                f"✅ Epizootias encontradas por coincidencia directa: {shapefile_municipio}"
            )
            return epi_directos

        # 2. Buscar usando mapeo (shapefile → datos)
        mapped_municipio = get_mapped_municipio(
            shapefile_municipio, "shapefile_to_data"
        )
        if mapped_municipio != shapefile_municipio:
            mask_mapeada = (
                epizootias["municipio"].astype(str).str.strip() == mapped_municipio
            )
            epi_mapeados = epizootias[mask_mapeada]

            if not epi_mapeados.empty:
                logger.debug(
                    f"✅ Epizootias encontradas por mapeo: {shapefile_municipio} → {mapped_municipio}"
                )
                return epi_mapeados

        return pd.DataFrame()

    except Exception as e:
        logger.warning(
            f"⚠️ Error buscando epizootias para {shapefile_municipio}: {str(e)}"
        )
        return pd.DataFrame()


def find_veredas_for_municipio_simplified(veredas_gdf, municipio_selected):
    """Encuentra veredas para municipio - CORREGIDO con mapeo bidireccional."""
    if veredas_gdf.empty:
        logger.error("❌ GeoDataFrame de veredas vacío")
        return pd.DataFrame()

    municipio_col = get_municipio_column(veredas_gdf)

    if not municipio_col:
        logger.error("❌ No se encontró columna de municipios en veredas shapefile")
        return pd.DataFrame()

    try:
        municipio_selected = str(municipio_selected).strip()
        logger.info(f"🔍 Buscando veredas para municipio: '{municipio_selected}'")

        # 1. Buscar veredas por coincidencia directa
        mask_directa = (
            veredas_gdf[municipio_col].astype(str).str.strip() == municipio_selected
        )
        veredas_directas = veredas_gdf[mask_directa]

        if not veredas_directas.empty:
            logger.info(
                f"✅ Encontradas {len(veredas_directas)} veredas para {municipio_selected} (coincidencia directa)"
            )
            return veredas_directas

        # 2. Buscar usando mapeo inverso (datos → shapefile)
        shapefile_municipio = get_mapped_municipio(
            municipio_selected, "data_to_shapefile"
        )

        if shapefile_municipio != municipio_selected:
            logger.info(
                f"🔗 Intentando mapeo inverso: '{municipio_selected}' → '{shapefile_municipio}'"
            )
            mask_mapeada = (
                veredas_gdf[municipio_col].astype(str).str.strip()
                == shapefile_municipio
            )
            veredas_mapeadas = veredas_gdf[mask_mapeada]

            if not veredas_mapeadas.empty:
                logger.info(
                    f"✅ Encontradas {len(veredas_mapeadas)} veredas para {municipio_selected} (mapeo inverso: {shapefile_municipio})"
                )
                return veredas_mapeadas

        # 3. Buscar usando mapeo directo (por compatibilidad)
        mapped_municipio = get_mapped_municipio(municipio_selected, "shapefile_to_data")

        if mapped_municipio != municipio_selected:
            logger.info(
                f"🔗 Intentando mapeo directo: '{municipio_selected}' → '{mapped_municipio}'"
            )
            mask_directo = (
                veredas_gdf[municipio_col].astype(str).str.strip() == mapped_municipio
            )
            veredas_directas_map = veredas_gdf[mask_directo]

            if not veredas_directas_map.empty:
                logger.info(
                    f"✅ Encontradas {len(veredas_directas_map)} veredas para {municipio_selected} (mapeo directo: {mapped_municipio})"
                )
                return veredas_directas_map

        # 4. Búsqueda insensible a mayúsculas/minúsculas
        municipio_upper = municipio_selected.upper()
        municipios_shapefile = (
            veredas_gdf[municipio_col].astype(str).str.strip().str.upper()
        )
        mask_insensitive = municipios_shapefile == municipio_upper
        veredas_insensitive = veredas_gdf[mask_insensitive]

        if not veredas_insensitive.empty:
            logger.info(
                f"✅ Encontradas {len(veredas_insensitive)} veredas para {municipio_selected} (búsqueda insensible)"
            )
            return veredas_insensitive

        # 5. Búsqueda parcial (contiene)
        mask_parcial = municipios_shapefile.str.contains(municipio_upper, na=False)
        veredas_parciales = veredas_gdf[mask_parcial]

        if not veredas_parciales.empty:
            logger.info(
                f"✅ Encontradas {len(veredas_parciales)} veredas para {municipio_selected} (búsqueda parcial)"
            )
            return veredas_parciales

        # 6. Si nada funciona, mostrar información de debug
        logger.warning(f"⚠️ No se encontraron veredas para '{municipio_selected}'")
        debug_municipios_en_shapefile(veredas_gdf, municipio_col, municipio_selected)

        return pd.DataFrame()

    except Exception as e:
        logger.error(f"❌ Error buscando veredas para {municipio_selected}: {str(e)}")
        return pd.DataFrame()

def validate_and_fix_filters_for_maps(filters):
    """Valida y corrige filtros para mapas múltiple."""
    try:
        # ✅ INICIALIZAR VARIABLES POR DEFECTO
        municipios_sel = []
        veredas_sel = []
        modo = "unico"  # Por defecto
        
        # ===== DETECTAR Y VALIDAR MODO MÚLTIPLE =====
        modo = filters.get("modo", "unico")

        if modo == "multiple":
            municipios_sel = filters.get("municipios_seleccionados", [])
            veredas_sel = filters.get("veredas_seleccionadas", [])

            # Asegurar que son listas
            if not isinstance(municipios_sel, list):
                municipios_sel = []
            if not isinstance(veredas_sel, list):
                veredas_sel = []

            logger.info(f"🔧 Modo múltiple validado: {len(municipios_sel)} municipios, {len(veredas_sel)} veredas")

            return {
                **filters,
                "modo": "multiple",
                "municipios_seleccionados": municipios_sel,
                "veredas_seleccionadas": veredas_sel,
                "municipio_display": "Multiple",
                "vereda_display": "Multiple" if veredas_sel else "Todas",
            }
        else:
            municipio = filters.get("municipio_display", "Todos")
            vereda = filters.get("vereda_display", "Todas")

            # Limpiar valores
            if pd.isna(municipio) or str(municipio).strip() == "":
                municipio = "Todos"
            if pd.isna(vereda) or str(vereda).strip() == "":
                vereda = "Todas"

            logger.info(f"🔧 Modo único validado: {municipio} | {vereda}")

            return {**filters, "municipio_display": municipio, "vereda_display": vereda}

    except Exception as e:
        logger.error(f"❌ Error validando filtros: {str(e)}")
        return filters

    except Exception as e:
        logger.error(f"❌ Error validando filtros: {str(e)}")
        return filters

def debug_map_flow_multiple(filters):
    """Debug específico para flujo de mapas múltiple."""
    logger.info("🔍 === DEBUG FLUJO MAPAS MÚLTIPLE ===")
    
    modo = filters.get("modo", "unknown")
    municipio_display = filters.get("municipio_display", "unknown")
    municipios_sel = filters.get("municipios_seleccionados", [])
    veredas_sel = filters.get("veredas_seleccionadas", [])
    
    logger.info(f"Modo: {modo}")
    logger.info(f"Municipio Display: '{municipio_display}'")
    logger.info(f"Municipios Seleccionados: {municipios_sel}")
    logger.info(f"Veredas Seleccionadas: {veredas_sel}")
    
    if modo == "multiple":
        level = "multiple"
    elif municipio_display and municipio_display != "Todos":
        level = "municipio"
    else:
        level = "departamento"
    
    logger.info(f"Nivel que se determinaría: {level}")
    logger.info("🔍 === FIN DEBUG ===")

def debug_municipios_en_shapefile(veredas_gdf, municipio_col, municipio_buscado):
    """Debug para mostrar municipios disponibles en shapefile."""
    try:
        municipios_unicos = sorted(veredas_gdf[municipio_col].dropna().unique())
        logger.info(
            f"📋 Municipios disponibles en shapefile ({len(municipios_unicos)}):"
        )
        for i, municipio in enumerate(
            municipios_unicos[:10]
        ):  # Mostrar solo los primeros 10
            logger.info(f"  {i+1:2d}. '{municipio}'")

        if len(municipios_unicos) > 10:
            logger.info(f"  ... y {len(municipios_unicos) - 10} más")

        # Mostrar mapeos relacionados
        mapeo_directo = get_mapped_municipio(municipio_buscado, "shapefile_to_data")
        mapeo_inverso = get_mapped_municipio(municipio_buscado, "data_to_shapefile")

        logger.info(f"🔗 Mapeos para '{municipio_buscado}':")
        logger.info(f"  → Directo (shapefile→data): '{mapeo_directo}'")
        logger.info(f"  → Inverso (data→shapefile): '{mapeo_inverso}'")

        # Buscar coincidencias parciales
        municipio_upper = municipio_buscado.upper()
        coincidencias = [
            m
            for m in municipios_unicos
            if municipio_upper in str(m).upper() or str(m).upper() in municipio_upper
        ]

        if coincidencias:
            logger.info(f"🎯 Posibles coincidencias parciales: {coincidencias}")

    except Exception as e:
        logger.error(f"❌ Error en debug de municipios: {str(e)}")


def prepare_vereda_data_epidemiological_simplified(
    casos, epizootias, veredas_gdf, municipio_selected, colors
):
    """Prepara datos de veredas."""
    logger.info(f"🔧 Preparando datos de veredas para {municipio_selected}")

    # Verificación inicial de datos
    if veredas_gdf.empty:
        logger.error("❌ GeoDataFrame de veredas vacío")
        return veredas_gdf

    # Verificar que epizootias no sea None o problemático
    if epizootias is None:
        logger.warning("⚠️ Epizootias es None, creando DataFrame vacío")
        epizootias = pd.DataFrame()
    elif not isinstance(epizootias, pd.DataFrame):
        logger.warning(
            f"⚠️ Epizootias no es DataFrame: {type(epizootias)}, creando DataFrame vacío"
        )
        epizootias = pd.DataFrame()

    # Verificar que casos no sea None o problemático
    if casos is None:
        logger.warning("⚠️ Casos es None, creando DataFrame vacío")
        casos = pd.DataFrame()
    elif not isinstance(casos, pd.DataFrame):
        logger.warning(
            f"⚠️ Casos no es DataFrame: {type(casos)}, creando DataFrame vacío"
        )
        casos = pd.DataFrame()

    veredas_gdf = veredas_gdf.copy()
    color_scheme = get_color_scheme_epidemiological(colors)

    vereda_col = get_vereda_column(veredas_gdf)
    contadores_veredas = {}

    if not vereda_col:
        logger.error("❌ No se encontró columna de veredas en shapefile")
        return veredas_gdf

    # Obtener lista de veredas únicas
    try:
        veredas_unicas = veredas_gdf[vereda_col].dropna().unique()
        veredas_unicas = [str(v).strip() for v in veredas_unicas if pd.notna(v)]
        logger.info(
            f"🏘️ Procesando {len(veredas_unicas)} veredas únicas para {municipio_selected}"
        )
    except Exception as e:
        logger.error(f"❌ Error obteniendo veredas únicas: {str(e)}")
        return veredas_gdf

    # Procesar casos por vereda
    if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
        try:
            casos_municipio = casos[
                casos["municipio"].astype(str).str.strip()
                == str(municipio_selected).strip()
            ]
            logger.info(
                f"📊 Casos del municipio {municipio_selected}: {len(casos_municipio)}"
            )

            for vereda_shapefile in veredas_unicas:
                try:
                    casos_ver = casos_municipio[
                        casos_municipio["vereda"].astype(str).str.strip()
                        == str(vereda_shapefile).strip()
                    ]
                    fallecidos_ver = pd.DataFrame()

                    if not casos_ver.empty and "condicion_final" in casos_ver.columns:
                        fallecidos_ver = casos_ver[
                            casos_ver["condicion_final"] == "Fallecido"
                        ]

                    contadores_veredas[vereda_shapefile] = {
                        "casos": int(len(casos_ver)),
                        "fallecidos": int(len(fallecidos_ver)),
                    }
                except Exception as e:
                    logger.warning(
                        f"⚠️ Error procesando casos para vereda {vereda_shapefile}: {str(e)}"
                    )
                    contadores_veredas[vereda_shapefile] = {"casos": 0, "fallecidos": 0}
        except Exception as e:
            logger.error(f"❌ Error general procesando casos por vereda: {str(e)}")
            # Inicializar contadores vacíos para todas las veredas
            for vereda_shapefile in veredas_unicas:
                contadores_veredas[vereda_shapefile] = {"casos": 0, "fallecidos": 0}

    # Procesar epizootias por vereda
    if (
        not epizootias.empty
        and "vereda" in epizootias.columns
        and "municipio" in epizootias.columns
    ):
        try:
            epi_municipio = epizootias[
                epizootias["municipio"].astype(str).str.strip()
                == str(municipio_selected).strip()
            ]
            logger.info(
                f"🐒 Epizootias del municipio {municipio_selected}: {len(epi_municipio)}"
            )

            for vereda_shapefile in veredas_unicas:
                try:
                    if vereda_shapefile not in contadores_veredas:
                        contadores_veredas[vereda_shapefile] = {
                            "casos": 0,
                            "fallecidos": 0,
                        }

                    epi_ver = epi_municipio[
                        epi_municipio["vereda"].astype(str).str.strip()
                        == str(vereda_shapefile).strip()
                    ]
                    positivas_ver = pd.DataFrame()
                    en_estudio_ver = pd.DataFrame()

                    if not epi_ver.empty and "descripcion" in epi_ver.columns:
                        positivas_ver = epi_ver[epi_ver["descripcion"] == "POSITIVO FA"]
                        en_estudio_ver = epi_ver[epi_ver["descripcion"] == "EN ESTUDIO"]

                    contadores_veredas[vereda_shapefile].update(
                        {
                            "epizootias": int(len(epi_ver)),
                            "positivas": int(len(positivas_ver)),
                            "en_estudio": int(len(en_estudio_ver)),
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"⚠️ Error procesando epizootias para vereda {vereda_shapefile}: {str(e)}"
                    )
                    if vereda_shapefile in contadores_veredas:
                        contadores_veredas[vereda_shapefile].update(
                            {
                                "epizootias": 0,
                                "positivas": 0,
                                "en_estudio": 0,
                            }
                        )
        except Exception as e:
            logger.error(f"❌ Error general procesando epizootias por vereda: {str(e)}")
            # Asegurar que todas las veredas tengan contadores de epizootias
            for vereda_shapefile in veredas_unicas:
                if vereda_shapefile not in contadores_veredas:
                    contadores_veredas[vereda_shapefile] = {"casos": 0, "fallecidos": 0}
                contadores_veredas[vereda_shapefile].update(
                    {
                        "epizootias": 0,
                        "positivas": 0,
                        "en_estudio": 0,
                    }
                )
    else:
        logger.info(f"📊 Sin epizootias para procesar en {municipio_selected}")
        # Asegurar que todas las veredas tengan contadores de epizootias en 0
        for vereda_shapefile in veredas_unicas:
            if vereda_shapefile not in contadores_veredas:
                contadores_veredas[vereda_shapefile] = {"casos": 0, "fallecidos": 0}
            contadores_veredas[vereda_shapefile].update(
                {
                    "epizootias": 0,
                    "positivas": 0,
                    "en_estudio": 0,
                }
            )

    # Aplicar colores
    veredas_data = veredas_gdf.copy()

    for idx, row in veredas_data.iterrows():
        try:
            vereda_shapefile = safe_get_feature_name(row, vereda_col)

            if not vereda_shapefile:
                logger.warning(f"⚠️ No se pudo obtener nombre de vereda para fila {idx}")
                continue

            # Obtener contadores de manera segura con valores por defecto
            contadores = contadores_veredas.get(
                vereda_shapefile,
                {
                    "casos": 0,
                    "fallecidos": 0,
                    "epizootias": 0,
                    "positivas": 0,
                    "en_estudio": 0,
                },
            )

            # Asegurar que todos los valores sean enteros
            casos_count = int(contadores.get("casos", 0))
            epizootias_count = int(contadores.get("epizootias", 0))
            fallecidos_count = int(contadores.get("fallecidos", 0))
            positivas_count = int(contadores.get("positivas", 0))
            en_estudio_count = int(contadores.get("en_estudio", 0))

            color, descripcion = determine_feature_color_epidemiological(
                casos_count,
                epizootias_count,
                fallecidos_count,
                positivas_count,
                en_estudio_count,
                color_scheme,
            )

            # Asignar valores de manera segura
            veredas_data.loc[idx, "color"] = color
            veredas_data.loc[idx, "descripcion_color"] = descripcion
            veredas_data.loc[idx, "casos"] = casos_count
            veredas_data.loc[idx, "fallecidos"] = fallecidos_count
            veredas_data.loc[idx, "epizootias"] = epizootias_count
            veredas_data.loc[idx, "positivas"] = positivas_count
            veredas_data.loc[idx, "en_estudio"] = en_estudio_count

        except Exception as e:
            logger.error(f"❌ Error procesando vereda en fila {idx}: {str(e)}")
            # Asignar valores por defecto en caso de error
            veredas_data.loc[idx, "color"] = color_scheme.get("sin_datos", "#E5E7EB")
            veredas_data.loc[idx, "descripcion_color"] = "Error en procesamiento"
            veredas_data.loc[idx, "casos"] = 0
            veredas_data.loc[idx, "fallecidos"] = 0
            veredas_data.loc[idx, "epizootias"] = 0
            veredas_data.loc[idx, "positivas"] = 0
            veredas_data.loc[idx, "en_estudio"] = 0

    logger.info(
        f"✅ Datos de veredas preparados para {municipio_selected}: {len(veredas_data)} veredas"
    )
    return veredas_data

def debug_cobertura_data_quality(cobertura_data):
    """
    Debug para entender por qué la cobertura parece alta.
    """
    if not cobertura_data or "municipios" not in cobertura_data:
        print("❌ No hay datos de cobertura")
        return
    
    print("🔍 === ANÁLISIS DE CALIDAD DE DATOS DE COBERTURA ===")
    
    municipios_con_datos = 0
    municipios_sin_datos = 0
    municipios_inconsistentes = 0
    total_poblacion = 0
    total_vacunados = 0
    coberturas = []
    
    for municipio_name, municipio_data in cobertura_data["municipios"].items():
        poblacion = municipio_data.get("total_poblacion", 0)
        vacunados = municipio_data.get("total_vacunados", 0)
        cobertura = municipio_data.get("cobertura_general", 0.0)
        
        if poblacion <= 0 and vacunados > 0:
            print(f"⚠️  INCONSISTENTE: {municipio_name} - Población: {poblacion}, Vacunados: {vacunados}")
            municipios_inconsistentes += 1
            continue
        
        if poblacion <= 0:
            print(f"📭 SIN DATOS: {municipio_name}")
            municipios_sin_datos += 1
            continue
        
        municipios_con_datos += 1
        total_poblacion += poblacion
        total_vacunados += vacunados
        coberturas.append(cobertura)
        
        if cobertura > 100:
            print(f"📈 ALTA: {municipio_name} - {cobertura:.1f}% ({vacunados:,}/{poblacion:,})")
        elif cobertura == 0:
            print(f"📉 CERO: {municipio_name} - {cobertura:.1f}% ({vacunados:,}/{poblacion:,})")
    
    # Estadísticas
    cobertura_promedio_valida = (total_vacunados / total_poblacion * 100) if total_poblacion > 0 else 0
    cobertura_mediana = sorted(coberturas)[len(coberturas)//2] if coberturas else 0
    
    print(f"\n📊 RESUMEN:")
    print(f"  - Municipios con datos válidos: {municipios_con_datos}")
    print(f"  - Municipios sin datos: {municipios_sin_datos}")
    print(f"  - Municipios inconsistentes: {municipios_inconsistentes}")
    print(f"  - Cobertura promedio (datos válidos): {cobertura_promedio_valida:.1f}%")
    print(f"  - Cobertura mediana: {cobertura_mediana:.1f}%")
    print(f"  - Total población válida: {total_poblacion:,}")
    print(f"  - Total vacunados válidos: {total_vacunados:,}")
    
    # Top 10 más altos y más bajos
    coberturas_municipios = [(municipio_data.get("cobertura_general", 0), name) 
                           for name, municipio_data in cobertura_data["municipios"].items()
                           if municipio_data.get("total_poblacion", 0) > 0]
    
    coberturas_municipios.sort(reverse=True)
    
    print(f"\n🔝 TOP 10 COBERTURAS MÁS ALTAS:")
    for cobertura, municipio in coberturas_municipios[:10]:
        print(f"  - {municipio}: {cobertura:.1f}%")
    
    print(f"\n🔻 TOP 10 COBERTURAS MÁS BAJAS:")
    for cobertura, municipio in coberturas_municipios[-10:]:
        print(f"  - {municipio}: {cobertura:.1f}%")
    
    print("🔍 === FIN ANÁLISIS ===")

def prepare_municipal_data_coverage_simplified(municipios, filters, colors):
    """
    Preparación.
    """
    municipios_data = municipios.copy()
    color_scheme = get_color_scheme_coverage(colors)
    
    # Cargar datos reales directamente
    cobertura_data = load_cobertura_data_direct()
    municipio_col = get_municipio_column(municipios)
    
    if not cobertura_data:
        logger.warning("⚠️ No hay datos de cobertura - mostrando todo en gris")
        # Si no hay datos, TODO en gris
        for idx, row in municipios_data.iterrows():
            municipios_data.loc[idx, "color"] = color_scheme.get("sin_datos", "#E5E7EB")
            municipios_data.loc[idx, "descripcion_color"] = "Sin datos de población"
            municipios_data.loc[idx, "cobertura"] = 0.0
            municipios_data.loc[idx, "poblacion"] = 0
            municipios_data.loc[idx, "vacunados"] = 0
        return municipios_data
    
    for idx, row in municipios_data.iterrows():
        municipio_name = safe_get_feature_name(row, municipio_col)
        
        if not municipio_name:
            municipio_name = "DESCONOCIDO"
        
        # Buscar datos de cobertura directamente
        from utils.cobertura_processor import (get_cobertura_for_municipio)
        municipio_cobertura = get_cobertura_for_municipio(cobertura_data, municipio_name)
        if municipio_cobertura:
            cobertura_base = municipio_cobertura.get("cobertura_general", 0.0)
            poblacion = municipio_cobertura.get("total_poblacion", 0)
            vacunados = municipio_cobertura.get("total_vacunados", 0)
            
            # Determinar color según cobertura REAL
            color, descripcion = determine_feature_color_coverage_unified(
                municipio_name, None, cobertura_data, color_scheme
            )
            
            municipios_data.loc[idx, "color"] = color
            municipios_data.loc[idx, "descripcion_color"] = descripcion
            municipios_data.loc[idx, "cobertura"] = cobertura_base
            municipios_data.loc[idx, "poblacion"] = poblacion
            municipios_data.loc[idx, "vacunados"] = vacunados
        else:
            # Sin datos = GRIS
            municipios_data.loc[idx, "color"] = color_scheme.get("sin_datos", "#E5E7EB")
            municipios_data.loc[idx, "descripcion_color"] = "Sin datos de población"
            municipios_data.loc[idx, "cobertura"] = 0.0
            municipios_data.loc[idx, "poblacion"] = 0
            municipios_data.loc[idx, "vacunados"] = 0
    
    return municipios_data

def determine_feature_color_coverage_unified(municipio_name, vereda_name, cobertura_data, color_scheme):
    """
    ✅ FUNCIÓN UNIFICADA SEGURA - Manejo defensivo de errores
    """
    try:
        from utils.cobertura_processor import get_cobertura_for_municipio, get_cobertura_for_vereda
        
        # Para municipios
        if municipio_name and not vereda_name:
            municipio_coverage = get_cobertura_for_municipio(cobertura_data, municipio_name)
            if not municipio_coverage:
                return color_scheme.get("sin_datos", "#E5E7EB"), "Sin datos de población"
            
            cobertura = municipio_coverage.get("cobertura_general", 0.0)
            poblacion = municipio_coverage.get("total_poblacion", 0)
            
            # Validar que tenga población
            if poblacion <= 0:
                return color_scheme.get("sin_datos", "#E5E7EB"), "Sin población registrada"
            
        # Para veredas
        elif vereda_name and municipio_name:
            vereda_coverage = get_cobertura_for_vereda(cobertura_data, municipio_name, vereda_name)
            if not vereda_coverage:
                return color_scheme.get("sin_datos", "#E5E7EB"), "Sin datos de población"
            
            cobertura = vereda_coverage.get("cobertura", 0.0)
            poblacion = vereda_coverage.get("poblacion", 0)
            
            # Validar que tenga población
            if poblacion <= 0:
                return color_scheme.get("sin_datos", "#E5E7EB"), "Sin población registrada"
        
        else:
            return color_scheme.get("sin_datos", "#E5E7EB"), "Sin datos de población"
        
        # ===== MANEJO DEFENSIVO DE COBERTURA =====
        if cobertura is None or pd.isna(cobertura):
            return color_scheme.get("sin_datos", "#E5E7EB"), "Sin datos de cobertura"
        
        try:
            cobertura = float(cobertura)
        except (ValueError, TypeError):
            return color_scheme.get("sin_datos", "#E5E7EB"), "Error en datos de cobertura"
        
        # Determinar color según cobertura REAL
        if cobertura >= 95.0:
            return color_scheme.get("cobertura_alta", "#10B981"), f"Cobertura alta: {cobertura:.1f}%"
        elif cobertura >= 80.0:
            return color_scheme.get("cobertura_buena", "#F59E0B"), f"Cobertura buena: {cobertura:.1f}%"
        elif cobertura >= 60.0:
            return color_scheme.get("cobertura_regular", "#EF4444"), f"Cobertura regular: {cobertura:.1f}%"
        elif cobertura >= 30.0:
            return color_scheme.get("cobertura_baja", "#DC2626"), f"Cobertura baja: {cobertura:.1f}%"
        elif cobertura > 0.0:
            return color_scheme.get("cobertura_muy_baja", "#991B1B"), f"Cobertura muy baja: {cobertura:.1f}%"
        else:
            # Cobertura = 0.0 también es GRIS (sin datos efectivos)
            return color_scheme.get("sin_datos", "#E5E7EB"), "Sin cobertura de vacunación"
            
    except ImportError:
        logger.warning("⚠️ Módulo cobertura_processor no disponible")
        return color_scheme.get("sin_datos", "#E5E7EB"), "Módulo no disponible"
    except KeyError as e:
        logger.error(f"❌ Error de clave en cobertura: {str(e)}")
        return color_scheme.get("sin_datos", "#E5E7EB"), "Error en estructura de datos"
    except Exception as e:
        logger.error(f"❌ Error inesperado en cobertura: {str(e)}")
        return color_scheme.get("sin_datos", "#E5E7EB"), "Error en procesamiento"

# ===== FUNCIONES DE APOYO =====

def get_municipio_column(gdf):
    """Detecta la columna de municipios en el shapefile."""
    if gdf is None or gdf.empty:
        logger.error("❌ GeoDataFrame vacío o None")
        return None

    try:
        possible_cols = ["municipi_1", "MpNombre", "NOMBRE_MUN", "municipio"]
        gdf_columns = list(gdf.columns)  # Convertir a lista explícitamente

        for col in possible_cols:
            if col in gdf_columns:
                logger.info(f"✅ Columna municipio encontrada: {col}")
                return col

        logger.warning(
            f"⚠️ No se encontró columna de municipios. Disponibles: {gdf_columns}"
        )
        return None

    except Exception as e:
        logger.error(f"❌ Error detectando columna municipio: {str(e)}")
        return None


def get_vereda_column(gdf):
    """Detecta la columna de veredas en el shapefile - CORREGIDO."""
    if gdf is None or gdf.empty:
        logger.error("❌ GeoDataFrame vacío o None")
        return None

    try:
        possible_cols = ["vereda_nor", "NOMBRE_VER", "vereda", "nombre_vereda"]
        gdf_columns = list(gdf.columns)  # Convertir a lista explícitamente

        for col in possible_cols:
            if col in gdf_columns:
                logger.info(f"✅ Columna vereda encontrada: {col}")
                return col

        logger.warning(
            f"⚠️ No se encontró columna de veredas. Disponibles: {gdf_columns}"
        )
        return None

    except Exception as e:
        logger.error(f"❌ Error detectando columna vereda: {str(e)}")
        return None


def safe_get_feature_name(row, col_name):
    """Obtiene nombre de feature de manera segura."""
    try:
        if col_name is None or col_name not in row:
            return None

        value = row[col_name]

        # Si es un array, tomar el primer elemento
        if hasattr(value, "__len__") and not isinstance(value, str):
            if len(value) > 0:
                return str(
                    value.iloc[0] if hasattr(value, "iloc") else value[0]
                ).strip()
            else:
                return None

        # Si es escalar
        return str(value).strip() if pd.notna(value) else None

    except Exception as e:
        logger.warning(f"⚠️ Error obteniendo feature name: {str(e)}")
        return None


def show_available_municipios_in_shapefile(veredas_gdf, municipio_selected):
    """Muestra municipios disponibles en shapefile para debug."""
    municipio_col = get_municipio_column(veredas_gdf)
    if municipio_col:
        municipios_disponibles = sorted(veredas_gdf[municipio_col].unique())
        logger.info(f"🏛️ Municipios disponibles en shapefile: {municipios_disponibles}")

        # Buscar coincidencias parciales o mapeos
        posibles_coincidencias = []
        municipio_upper = str(municipio_selected).upper()

        for municipio_shapefile in municipios_disponibles:
            municipio_shapefile_upper = str(municipio_shapefile).upper()

            # Coincidencia parcial
            if (
                municipio_upper in municipio_shapefile_upper
                or municipio_shapefile_upper in municipio_upper
            ):
                posibles_coincidencias.append(municipio_shapefile)

        # Verificar mapeos
        mapped_municipio = get_mapped_municipio(municipio_selected, "data_to_shapefile")
        if (
            mapped_municipio != municipio_selected
            and mapped_municipio in municipios_disponibles
        ):
            posibles_coincidencias.append(f"{mapped_municipio} (MAPEO)")

        st.info(
            f"**Municipios disponibles en shapefile de veredas:**\n\n"
            f"{', '.join(municipios_disponibles[:10])}"
            f"{f' y {len(municipios_disponibles)-10} más...' if len(municipios_disponibles) > 10 else ''}\n\n"
            f"**Buscado:** {municipio_selected}\n\n"
            f"**Posibles coincidencias:** {', '.join(posibles_coincidencias) if posibles_coincidencias else 'Ninguna'}\n\n"
            f"**Sugerencia:** Verificar mapeo en MUNICIPIO_MAPPING"
        )


# Inicializar mapeo bidireccional al cargar el módulo
initialize_bidirectional_mapping()


# ===== MANEJO DE CLICS SIMPLIFICADO =====


def handle_map_click_simplified(map_data, features_data, feature_type, filters, data_original):
    """
    Manejo de clics con validación de variables.
    """
    if not map_data or not map_data.get("last_object_clicked"):
        return

    try:
        clicked_object = map_data["last_object_clicked"]
        
        # ✅ INICIALIZAR VARIABLES POR DEFECTO
        clicked_lat = None
        clicked_lng = None
        shapefile_name = None
        data_name = None

        if isinstance(clicked_object, dict):
            clicked_lat = clicked_object.get("lat")
            clicked_lng = clicked_object.get("lng")

            if clicked_lat is not None and clicked_lng is not None:
                # Convertir a float explícitamente - CORREGIDO
                try:
                    clicked_lat = float(clicked_lat)
                    clicked_lng = float(clicked_lng)
                except (ValueError, TypeError) as e:
                    logger.error(f"❌ Error convirtiendo coordenadas: {str(e)}")
                    return

                # Obtener nombre del shapefile - CORREGIDO
                shapefile_name = find_closest_feature_simplified(
                    clicked_lat, clicked_lng, features_data, feature_type
                )

                if shapefile_name:
                    logger.info(f"🎯 Click en shapefile: '{shapefile_name}' (corregido)")

                    # Mapear a nombre de base de datos - CORREGIDO
                    data_name = map_shapefile_to_data_simplified(
                        shapefile_name, data_original, feature_type
                    )

                    if not data_name:
                        logger.error(f"❌ No se pudo mapear '{shapefile_name}' a base de datos")
                        st.error(f"Ubicación no encontrada en datos: {shapefile_name}")
                        return

                    logger.info(f"🔗 Mapeado: '{shapefile_name}' → '{data_name}'")

                    # Aplicar filtro - CORREGIDO
                    apply_filter_simplified(data_name, feature_type, filters)
                else:
                    logger.warning("⚠️ No se pudo identificar feature en clic")
                    st.warning("No se pudo identificar la ubicación del clic")

    except Exception as e:
        logger.error(f"❌ Error procesando clic corregido: {str(e)}")
        st.error(f"Error procesando clic en mapa: {str(e)}")

def find_closest_feature_simplified(lat, lng, features_data, feature_type):
    """Encuentra feature más cercano."""
    try:
        from shapely.geometry import Point

        click_point = Point(lng, lat)

        if feature_type == "municipio":
            col_name = get_municipio_column(features_data)
        else:
            col_name = get_vereda_column(features_data)

        if not col_name:
            logger.error(f"❌ No se encontró columna para {feature_type}")
            return None

        logger.info(
            f"🎯 Buscando {feature_type} más cercano usando columna '{col_name}'"
        )

        # Buscar dentro de geometrías primero
        for idx, row in features_data.iterrows():
            try:
                feature_name = safe_get_feature_name(row, col_name)
                if not feature_name:
                    continue

                geometry = row.get("geometry")
                if geometry is None:
                    continue

                # Verificar si está dentro
                if hasattr(geometry, "contains") and geometry.contains(click_point):
                    logger.info(f"✅ Clic dentro de {feature_name}")
                    return feature_name

            except Exception as e:
                logger.warning(f"⚠️ Error verificando geometría en fila {idx}: {str(e)}")
                continue

        # Si no está dentro de ninguno, buscar el más cercano
        min_distance = float("inf")
        closest_feature = None

        for idx, row in features_data.iterrows():
            try:
                feature_name = safe_get_feature_name(row, col_name)
                if not feature_name:
                    continue

                geometry = row.get("geometry")
                if geometry is None:
                    continue

                # Calcular distancia
                if hasattr(geometry, "distance"):
                    distance = click_point.distance(geometry)

                    # Asegurar que distance es un número, no un array
                    if hasattr(distance, "__len__") and len(distance) > 1:
                        distance = (
                            float(distance.min())
                            if hasattr(distance, "min")
                            else float(distance[0])
                        )
                    else:
                        distance = float(distance)

                    if distance < min_distance:
                        min_distance = distance
                        closest_feature = feature_name

            except Exception as e:
                logger.warning(f"⚠️ Error calculando distancia en fila {idx}: {str(e)}")
                continue

        if closest_feature:
            logger.info(
                f"✅ Feature más cercano: {closest_feature} (distancia: {min_distance:.6f})"
            )
        else:
            logger.warning("⚠️ No se encontró feature cercano")

        return closest_feature

    except ImportError:
        logger.warning("⚠️ Shapely no disponible, usando fallback")
        # Fallback sin shapely
        if not features_data.empty:
            if feature_type == "municipio":
                col_name = get_municipio_column(features_data)
            else:
                col_name = get_vereda_column(features_data)

            if col_name and col_name in features_data.columns:
                first_feature = safe_get_feature_name(features_data.iloc[0], col_name)
                logger.info(f"✅ Fallback: usando primer feature {first_feature}")
                return first_feature

        return None

    except Exception as e:
        logger.error(f"❌ Error general en find_closest_feature: {str(e)}")
        return None


def map_shapefile_to_data_simplified(shapefile_name, data_original, feature_type):
    """Mapea nombre de shapefile a nombre de base de datos con mapeo bidireccional."""
    try:
        shapefile_name = str(shapefile_name).strip()

        if feature_type == "municipio":
            # Para municipios, usar mapeo bidireccional
            mapped_name = get_mapped_municipio(shapefile_name, "shapefile_to_data")

            # Verificar que existe en datos
            municipios_disponibles = data_original.get("municipios_authoritativos", [])
            if not municipios_disponibles:
                municipios_disponibles = data_original.get(
                    "municipios_normalizados", []
                )

            # Convertir a lista si es necesario
            if hasattr(municipios_disponibles, "tolist"):
                municipios_disponibles = municipios_disponibles.tolist()
            elif not isinstance(municipios_disponibles, list):
                municipios_disponibles = list(municipios_disponibles)

            # Verificar mapeo
            if mapped_name in municipios_disponibles:
                logger.info(f"🔗 Mapeo exitoso: '{shapefile_name}' → '{mapped_name}'")
                return mapped_name

            # Si el mapeo no funciona, buscar coincidencia directa
            if shapefile_name in municipios_disponibles:
                logger.info(f"✅ Coincidencia directa: '{shapefile_name}'")
                return shapefile_name

            # Último intento: buscar parcialmente
            for municipio_data in municipios_disponibles:
                if str(municipio_data).strip().upper() == shapefile_name.upper():
                    logger.info(
                        f"✅ Coincidencia por normalización: '{shapefile_name}' → '{municipio_data}'"
                    )
                    return municipio_data

            logger.warning(
                f"⚠️ Municipio '{shapefile_name}' (→'{mapped_name}') no encontrado en datos"
            )
            logger.info(f"📋 Municipios disponibles: {municipios_disponibles[:5]}...")
            return None

        elif feature_type == "vereda":
            # Para veredas, retornar el nombre directamente (ya están estandarizados)
            return shapefile_name

        return None

    except Exception as e:
        logger.error(f"❌ Error mapeando {feature_type} '{shapefile_name}': {str(e)}")
        return None


def apply_filter_simplified(location_name, feature_type, filters):
    """Aplica filtro SIMPLIFICADO."""
    # Verificar si ya está seleccionado para evitar bucle
    if feature_type == "municipio":
        current_value = st.session_state.get("municipio_filter", "Todos")
        if current_value != location_name:
            st.session_state["municipio_filter"] = location_name
            st.session_state["vereda_filter"] = "Todas"  # Reset vereda
            st.success(f"✅ **{location_name}** seleccionado")
            st.rerun()
        else:
            st.info(f"📍 **{location_name}** ya estaba seleccionado")

    elif feature_type == "vereda":
        current_value = st.session_state.get("vereda_filter", "Todas")
        if current_value != location_name:
            st.session_state["vereda_filter"] = location_name
            st.success(f"✅ **{location_name}** seleccionado")
            st.rerun()
        else:
            st.info(f"🏘️ **{location_name}** ya estaba seleccionado")


# ===== TARJETAS =====

def create_afectacion_card_simplified(
    casos, epizootias, filters, colors, data_original
):
    """Tarjeta de afectación."""
    filter_context = get_filter_context_compact(filters)

    # Calcular afectación
    afectacion_info = calculate_afectacion_simplified(
        casos, epizootias, filters, data_original
    )

    st.markdown(
        f"""
        <div class="tarjeta-optimizada afectacion-card">
            <div class="tarjeta-header">
                <div class="tarjeta-icon">🏛️</div>
                <div class="tarjeta-info">
                    <div class="tarjeta-titulo">AFECTACIÓN</div>
                    <div class="tarjeta-subtitulo">{filter_context}</div>
                </div>
                <div class="tarjeta-valor">{afectacion_info['total']}</div>
            </div>
            <div class="tarjeta-contenido">
                <div class="afectacion-items">
                    <div class="afectacion-item">
                        <span class="afectacion-icono">📍</span>
                        <span class="afectacion-texto">{afectacion_info['casos_texto']}</span>
                    </div>
                    <div class="afectacion-item">
                        <span class="afectacion-icono">🐒</span>
                        <span class="afectacion-texto">{afectacion_info['epizootias_texto']}</span>
                    </div>
                    <div class="afectacion-item">
                        <span class="afectacion-icono">🔄</span>
                        <span class="afectacion-texto">{afectacion_info['ambos_texto']}</span>
                    </div>
                </div>
                <div class="tarjeta-footer">
                    {afectacion_info['descripcion']}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def calculate_afectacion_simplified(casos, epizootias, filters, data_original):
    """Calcula información de afectación."""

    # ===== DETECTAR MODO MÚLTIPLE =====
    if filters.get("modo") == "multiple":
        return calculate_afectacion_multiple(casos, epizootias, filters, data_original)

    # ===== PARA OTROS MODOS =====
    if filters.get("vereda_display") and filters.get("vereda_display") != "Todas":
        # Vista de vereda específica
        return {
            "total": "1/1",
            "casos_texto": f"{len(casos)} casos registrados",
            "epizootias_texto": f"{len(epizootias)} epizootias registradas",
            "ambos_texto": "Vista detallada activa",
            "descripcion": f"vereda {filters.get('vereda_display', '')}",
        }

    elif (
        filters.get("municipio_display") and filters.get("municipio_display") != "Todos"
    ):
        # Vista municipal
        municipio_actual = filters.get("municipio_display")

        veredas_con_casos = set()
        veredas_con_epizootias = set()

        if not casos.empty and "vereda" in casos.columns:
            veredas_con_casos = set(casos["vereda"].dropna())

        if not epizootias.empty and "vereda" in epizootias.columns:
            veredas_con_epizootias = set(epizootias["vereda"].dropna())

        veredas_con_ambos = veredas_con_casos.intersection(veredas_con_epizootias)
        veredas_afectadas = veredas_con_casos.union(veredas_con_epizootias)

        total_veredas_real = get_total_veredas_municipio_simplified(
            municipio_actual, data_original
        )

        return {
            "total": f"{len(veredas_afectadas)}/{total_veredas_real}",
            "casos_texto": f"{len(veredas_con_casos)}/{total_veredas_real} con casos",
            "epizootias_texto": f"{len(veredas_con_epizootias)}/{total_veredas_real} con epizootias",
            "ambos_texto": f"{len(veredas_con_ambos)}/{total_veredas_real} con ambos",
            "descripcion": f"veredas afectadas en {municipio_actual}",
        }

    else:
        # Vista departamental
        municipios_con_casos = set()
        municipios_con_epizootias = set()

        if not casos.empty and "municipio" in casos.columns:
            municipios_con_casos = set(casos["municipio"].dropna())

        if not epizootias.empty and "municipio" in epizootias.columns:
            municipios_con_epizootias = set(epizootias["municipio"].dropna())

        municipios_con_ambos = municipios_con_casos.intersection(
            municipios_con_epizootias
        )
        municipios_afectados = municipios_con_casos.union(municipios_con_epizootias)

        total_municipios_real = 47  # Tolima tiene 47 municipios

        return {
            "total": f"{len(municipios_afectados)}/{total_municipios_real}",
            "casos_texto": f"{len(municipios_con_casos)}/{total_municipios_real} con casos",
            "epizootias_texto": f"{len(municipios_con_epizootias)}/{total_municipios_real} con epizootias",
            "ambos_texto": f"{len(municipios_con_ambos)}/{total_municipios_real} con ambos",
            "descripcion": "Municipios afectados del Tolima",
        }

def calculate_afectacion_multiple(casos, epizootias, filters, data_original):
    """
    Calcula afectación para selección múltiple.
    """
    # ✅ INICIALIZAR VARIABLES TEMPRANO
    municipios_seleccionados = filters.get("municipios_seleccionados", [])
    veredas_seleccionadas = filters.get("veredas_seleccionadas", [])

    logger.info(f"🔢 Calculando afectación múltiple: {len(municipios_seleccionados)} municipios, {len(veredas_seleccionadas)} veredas")

    # ===== CASO 1: VEREDAS ESPECÍFICAS SELECCIONADAS =====
    if veredas_seleccionadas:
        logger.info("🏘️ Modo: veredas específicas seleccionadas")
        
        return calculate_afectacion_veredas_especificas(
            casos, epizootias, veredas_seleccionadas, municipios_seleccionados
        )

    # ===== CASO 2: SOLO MUNICIPIOS SELECCIONADOS =====
    elif municipios_seleccionados:
        logger.info("🏛️ Modo: solo municipios seleccionados")
        
        return calculate_afectacion_municipios_multiples(
            casos, epizootias, municipios_seleccionados, data_original
        )

    # ===== CASO 3: FALLBACK (no debería pasar) =====
    else:
        logger.warning("⚠️ Selección múltiple sin municipios ni veredas")
        return {
            "total": "0/0",
            "casos_texto": "Sin selección",
            "epizootias_texto": "Sin selección", 
            "ambos_texto": "Sin selección",
            "descripcion": "selección múltiple vacía",
        }

def calculate_afectacion_municipios_multiples(casos, epizootias, municipios_seleccionados, data_original):
    """Calcula afectación para múltiples municipios seleccionados."""
    
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""

    # ===== OBTENER TOTAL REAL DE VEREDAS =====
    total_veredas_real = get_total_veredas_multiples_municipios(
        municipios_seleccionados, data_original
    )
    
    logger.info(f"📊 Total veredas reales en {len(municipios_seleccionados)} municipios: {total_veredas_real}")

    # ===== CONTAR VEREDAS AFECTADAS =====
    veredas_con_casos = set()
    veredas_con_epizootias = set()

    # Casos: solo en municipios seleccionados
    if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
        casos_filtrados = casos[casos["municipio"].isin(municipios_seleccionados)]
        veredas_con_casos = set(casos_filtrados["vereda"].dropna())

    # Epizootias: solo en municipios seleccionados  
    if not epizootias.empty and "vereda" in epizootias.columns and "municipio" in epizootias.columns:
        epi_filtrados = epizootias[epizootias["municipio"].isin(municipios_seleccionados)]
        veredas_con_epizootias = set(epi_filtrados["vereda"].dropna())

    veredas_con_ambos = veredas_con_casos.intersection(veredas_con_epizootias)
    veredas_afectadas = veredas_con_casos.union(veredas_con_epizootias)

    logger.info(f"🎯 Veredas afectadas: {len(veredas_afectadas)}/{total_veredas_real}")

    return {
        "total": f"{len(veredas_afectadas)}/{total_veredas_real}",
        "casos_texto": f"{len(veredas_con_casos)}/{total_veredas_real} con casos",
        "epizootias_texto": f"{len(veredas_con_epizootias)}/{total_veredas_real} con epizootias", 
        "ambos_texto": f"{len(veredas_con_ambos)}/{total_veredas_real} con ambos",
        "descripcion": f"veredas en {len(municipios_seleccionados)} municipios seleccionados",
    }

def get_total_veredas_multiples_municipios(municipios_seleccionados, data_original):
    """
    Obtiene el total REAL de veredas de múltiples municipios.
    Suma las veredas de todos los municipios seleccionados desde la hoja VEREDAS.
    """
    total_veredas = 0
    veredas_por_municipio = data_original.get("veredas_por_municipio", {})

    logger.info(f"🔍 Contando veredas para {len(municipios_seleccionados)} municipios")

    for municipio in municipios_seleccionados:
        # Buscar coincidencia directa
        if municipio in veredas_por_municipio:
            veredas_municipio = len(veredas_por_municipio[municipio])
            total_veredas += veredas_municipio
            logger.info(f"  ✅ {municipio}: {veredas_municipio} veredas (directo)")
        else:
            # Buscar usando mapeo
            from vistas.mapas import get_mapped_municipio  # Import local para evitar circular
            mapped_municipio = get_mapped_municipio(municipio)
            if mapped_municipio != municipio and mapped_municipio in veredas_por_municipio:
                veredas_municipio = len(veredas_por_municipio[mapped_municipio])
                total_veredas += veredas_municipio
                logger.info(f"  ✅ {municipio} (como {mapped_municipio}): {veredas_municipio} veredas (mapeado)")
            else:
                # Estimado por defecto
                veredas_estimadas = 8  # Promedio estimado por municipio
                total_veredas += veredas_estimadas
                logger.warning(f"  ⚠️ {municipio}: {veredas_estimadas} veredas (estimado)")

    logger.info(f"📊 Total calculado: {total_veredas} veredas en {len(municipios_seleccionados)} municipios")
    return total_veredas


# ===== FUNCIÓN DE VALIDACIÓN Y DEBUG =====

def debug_afectacion_multiple(casos, epizootias, filters, data_original):
    """Función de debug para verificar cálculos de afectación múltiple."""
    logger.info("🔍 === DEBUG AFECTACIÓN MÚLTIPLE ===")
    
    municipios_sel = filters.get("municipios_seleccionados", [])
    veredas_sel = filters.get("veredas_seleccionadas", [])
    
    logger.info(f"Municipios seleccionados: {municipios_sel}")
    logger.info(f"Veredas seleccionadas: {veredas_sel}")
    logger.info(f"Casos shape: {casos.shape if not casos.empty else 'Vacío'}")
    logger.info(f"Epizootias shape: {epizootias.shape if not epizootias.empty else 'Vacío'}")
    
    if municipios_sel:
        total_veredas = get_total_veredas_multiples_municipios(municipios_sel, data_original)
        logger.info(f"Total veredas calculado: {total_veredas}")
        
        # Verificar datos por municipio
        for municipio in municipios_sel:
            casos_mun = casos[casos["municipio"] == municipio] if not casos.empty and "municipio" in casos.columns else pd.DataFrame()
            epi_mun = epizootias[epizootias["municipio"] == municipio] if not epizootias.empty and "municipio" in epizootias.columns else pd.DataFrame()
            
            veredas_casos = set(casos_mun["vereda"].dropna()) if not casos_mun.empty and "vereda" in casos_mun.columns else set()
            veredas_epi = set(epi_mun["vereda"].dropna()) if not epi_mun.empty and "vereda" in epi_mun.columns else set()
            
            logger.info(f"  {municipio}: {len(casos_mun)} casos, {len(epi_mun)} epizootias")
            logger.info(f"  {municipio}: {len(veredas_casos)} veredas con casos, {len(veredas_epi)} veredas con epizootias")
    
    logger.info("🔍 === FIN DEBUG ===")

def calculate_afectacion_veredas_especificas(casos, epizootias, veredas_seleccionadas, municipios_seleccionados):
    """Calcula afectación para veredas específicamente seleccionadas."""
    
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""

    total_veredas_seleccionadas = len(veredas_seleccionadas)
    veredas_con_casos = set()
    veredas_con_epizootias = set()

    # Para cada vereda seleccionada, verificar si tiene casos/epizootias
    for vereda in veredas_seleccionadas:
        vereda_norm = normalize_name(vereda)
        
        # Buscar casos en esta vereda (cualquier municipio de los seleccionados)
        if not casos.empty and "vereda" in casos.columns:
            if municipios_seleccionados:
                # Filtrar por municipios seleccionados también
                casos_vereda = casos[
                    (casos["vereda"].apply(normalize_name) == vereda_norm) &
                    (casos["municipio"].isin(municipios_seleccionados))
                ]
            else:
                casos_vereda = casos[casos["vereda"].apply(normalize_name) == vereda_norm]
            
            if not casos_vereda.empty:
                veredas_con_casos.add(vereda)

        # Buscar epizootias en esta vereda
        if not epizootias.empty and "vereda" in epizootias.columns:
            if municipios_seleccionados:
                epi_vereda = epizootias[
                    (epizootias["vereda"].apply(normalize_name) == vereda_norm) &
                    (epizootias["municipio"].isin(municipios_seleccionados))
                ]
            else:
                epi_vereda = epizootias[epizootias["vereda"].apply(normalize_name) == vereda_norm]
            
            if not epi_vereda.empty:
                veredas_con_epizootias.add(vereda)

    veredas_con_ambos = veredas_con_casos.intersection(veredas_con_epizootias)
    veredas_afectadas = veredas_con_casos.union(veredas_con_epizootias)

    return {
        "total": f"{len(veredas_afectadas)}/{total_veredas_seleccionadas}",
        "casos_texto": f"{len(veredas_con_casos)}/{total_veredas_seleccionadas} con casos",
        "epizootias_texto": f"{len(veredas_con_epizootias)}/{total_veredas_seleccionadas} con epizootias",
        "ambos_texto": f"{len(veredas_con_ambos)}/{total_veredas_seleccionadas} con ambos",
        "descripcion": f"veredas seleccionadas ({len(veredas_seleccionadas)} específicas)",
    }

def get_total_veredas_municipio_simplified(municipio, data_original):
    """Obtiene total REAL de veredas desde hoja VEREDAS SIMPLIFICADO."""
    veredas_por_municipio = data_original.get("veredas_por_municipio", {})

    # Buscar coincidencia directa
    if municipio in veredas_por_municipio:
        total_real = len(veredas_por_municipio[municipio])
        logger.info(f"📊 {municipio}: {total_real} veredas desde hoja VEREDAS")
        return total_real

    # Buscar usando mapeo
    mapped_municipio = get_mapped_municipio(municipio)
    if mapped_municipio != municipio and mapped_municipio in veredas_por_municipio:
        total_real = len(veredas_por_municipio[mapped_municipio])
        logger.info(
            f"📊 {municipio} (como {mapped_municipio}): {total_real} veredas desde hoja VEREDAS"
        )
        return total_real

    logger.warning(
        f"⚠️ Municipio '{municipio}' no encontrado en hoja VEREDAS, usando estimado"
    )
    return 5  # Estimado por defecto

def create_cobertura_card_simplified(filters, colors, data_filtered):
    """
    Tarjeta de cobertura
    """
    # ===== INICIALIZAR TODAS LAS VARIABLES POR DEFECTO =====
    cobertura_porcentaje = 0.0
    vacunados_total = 0
    poblacion_total = 0
    rechazos_total = 0
    calidad_datos = 0.0
    alertas = []
    ultima_actualizacion = datetime.now().strftime("%d/%m/%Y")
    display_context = get_filter_context_compact(filters)
    
    # ✅ INICIALIZAR VARIABLES DE SELECCIÓN MÚLTIPLE SIEMPRE
    municipios_sel = []
    veredas_sel = []
    
    # ===== CARGAR DATOS DE COBERTURA =====
    cobertura_data = load_cobertura_data_direct()
    
    # ===== MANEJO MODO MÚLTIPLE =====
    if filters.get("modo") == "multiple":
        municipios_sel = filters.get("municipios_seleccionados", [])
        veredas_sel = filters.get("veredas_seleccionadas", [])
        
        logger.info(f"🗂️ Procesando modo múltiple: {len(municipios_sel)} municipios, {len(veredas_sel)} veredas")
        
        if not municipios_sel:
            # Si no hay municipios seleccionados, usar valores por defecto
            cobertura_porcentaje = 0.0
            vacunados_total = 0
            poblacion_total = 0
            rechazos_total = 0
            calidad_datos = 0.0
            alertas = ["⚠️ No hay municipios seleccionados"]
            display_context = "Sin selección"
        else:
            try:
                from utils.cobertura_processor import validate_cobertura_multiple
                
                # ✅ LLAMAR A LA FUNCIÓN CORREGIDA
                validation_result = validate_cobertura_multiple(
                    cobertura_data, municipios_sel, veredas_sel
                )
                
                # ✅ EXTRAER DATOS CON LOGS DE DEBUG
                cobertura_porcentaje = validation_result.get("cobertura", 0.0)
                vacunados_total = validation_result.get("vacunados_total", 0)
                poblacion_total = validation_result.get("poblacion_total", 0)
                calidad_datos = validation_result.get("calidad", 0.0)
                alertas = validation_result.get("alertas", [])
                
                logger.info(f"📊 Resultado múltiple: cobertura={cobertura_porcentaje}%, vacunados={vacunados_total}, población={poblacion_total}")
                
                # ✅ CALCULAR RECHAZOS PARA MODO MÚLTIPLE
                try:
                    rechazos_total = calculate_rechazos_multiple_improved(cobertura_data, municipios_sel, veredas_sel)
                    logger.info(f"📊 Rechazos múltiple: {rechazos_total}")
                except Exception as e:
                    logger.warning(f"⚠️ Error calculando rechazos múltiples: {str(e)}")
                    rechazos_total = 0
                
                # ✅ CONTEXTO DESCRIPTIVO
                municipios_validos = validation_result.get("municipios_validos", 0)
                if veredas_sel:
                    display_context = f"{municipios_validos} municipios, {len(veredas_sel)} veredas"
                else:
                    display_context = f"{municipios_validos} municipios válidos"
                
                # ✅ VERIFICAR QUE LOS VALORES SEAN RAZONABLES
                if cobertura_porcentaje == 0.0 and vacunados_total == 0 and poblacion_total == 0:
                    logger.warning("⚠️ Todos los valores son 0 - verificando datos manualmente")
                    # Cálculo manual como fallback
                    cobertura_manual = calculate_cobertura_manual_fallback(cobertura_data, municipios_sel)
                    if cobertura_manual > 0:
                        logger.info(f"✅ Cálculo manual exitoso: {cobertura_manual:.1f}%")
                        cobertura_porcentaje = cobertura_manual
                
            except Exception as e:
                logger.error(f"❌ Error en modo múltiple: {str(e)}")
                # Fallback manual
                cobertura_porcentaje, vacunados_total, poblacion_total = calculate_cobertura_manual_fallback_full(
                    cobertura_data, municipios_sel, veredas_sel
                )
                rechazos_total = 0
                calidad_datos = 50.0
                alertas = [f"⚠️ Error en validación: {str(e)}", "ℹ️ Usando cálculo manual"]
                display_context = f"Cálculo manual ({len(municipios_sel)} municipios)"
    
    # ===== MANEJO OTROS MODOS =====
    elif cobertura_data:
        try:
            from utils.cobertura_processor import (
                validate_cobertura_data_quality_contextual,
                get_coverage_comparison_context
            )
            
            # ===== OBTENER CONTEXTO SEGÚN FILTROS =====
            context_data = get_coverage_comparison_context(cobertura_data, filters)
            
            # ✅ ACCESO SEGURO CON get()
            cobertura_porcentaje = context_data.get("cobertura", 0.0)
            vacunados_total = context_data.get("vacunados", 0)
            poblacion_total = context_data.get("poblacion", 0)
            filter_context = context_data.get("contexto", "Sin contexto")
            
            # ✅ CALCULAR RECHAZOS SEGÚN FILTROS
            try:
                rechazos_total = calculate_rechazos_by_filters_improved(cobertura_data, filters)
            except Exception as e:
                logger.warning(f"⚠️ Error calculando rechazos por filtros: {str(e)}")
                rechazos_total = 0
            
            # ✅ FECHA FIJA CONOCIDA
            ultima_actualizacion = "17/07/2025"  # Fecha fija para datos de cobertura
            
            # ===== VALIDACIONES CONTEXTUALES =====
            municipio_filter = filters.get("municipio_display", "Todos")
            vereda_filter = filters.get("vereda_display", "Todas")
            
            try:
                quality_report = validate_cobertura_data_quality_contextual(
                    cobertura_data, municipio_filter, vereda_filter
                )
                calidad_datos = quality_report.get("calidad", 0.0)
                alertas = quality_report.get("alertas", [])
            except Exception as e:
                logger.warning(f"⚠️ Error en validación contextual: {str(e)}")
                calidad_datos = 50.0  # Valor por defecto cuando hay error
                alertas = [f"⚠️ Error en validación: {str(e)}"]
            
            # Ajustar contexto para display
            if len(filter_context) > 15:
                display_context = filter_context[:12] + "..."
            else:
                display_context = filter_context
            
        except Exception as e:
            logger.warning(f"⚠️ Error en funciones contextuales: {str(e)}")
            # ✅ TODAS LAS VARIABLES YA ESTÁN INICIALIZADAS
            alertas = [f"⚠️ Error contextual: {str(e)}"]
            # display_context ya está inicializado
            
    else:
        # ===== FALLBACK: DATOS SIMULADOS =====
        logger.info("ℹ️ Usando datos simulados de cobertura")
        cobertura_porcentaje = 82.3
        vacunados_total = 45650
        poblacion_total = 55500
        rechazos_total = 2850  # Simulado
        calidad_datos = 85.0
        alertas = ["ℹ️ Datos simulados - archivo de cobertura no disponible"]
        # ultima_actualizacion y display_context ya están inicializados

    # ===== VALIDACIÓN FINAL DE VARIABLES =====
    # Asegurar que todas las variables son del tipo correcto
    try:
        cobertura_porcentaje = float(cobertura_porcentaje) if cobertura_porcentaje is not None else 0.0
        vacunados_total = int(vacunados_total) if vacunados_total is not None else 0
        poblacion_total = int(poblacion_total) if poblacion_total is not None else 0
        rechazos_total = int(rechazos_total) if rechazos_total is not None else 0
        calidad_datos = float(calidad_datos) if calidad_datos is not None else 0.0
    except (ValueError, TypeError) as e:
        logger.error(f"❌ Error convirtiendo tipos de datos: {str(e)}")
        # Usar valores seguros
        cobertura_porcentaje = 0.0
        vacunados_total = 0
        poblacion_total = 0
        rechazos_total = 0
        calidad_datos = 0.0

    # ===== DETERMINAR ESTADO DE COBERTURA =====
    if cobertura_porcentaje >= 95.0:
        estado_cobertura = "🟢 META ALCANZADA"
        color_estado = colors.get("success", "#10B981")
    elif cobertura_porcentaje >= 80.0:
        estado_cobertura = "🟡 CERCA DE META"
        color_estado = colors.get("warning", "#F59E0B")
    else:
        estado_cobertura = "🔴 BAJO META"
        color_estado = colors.get("danger", "#EF4444")

    # ===== CREAR HTML DE LA TARJETA =====
    try:
        st.markdown(
            f"""
            <div class="tarjeta-optimizada cobertura-card">
                <div class="tarjeta-header">
                    <div class="tarjeta-icon">💉</div>
                    <div class="tarjeta-info">
                        <div class="tarjeta-titulo">COBERTURA VACUNACIÓN</div>
                        <div class="tarjeta-subtitulo">{display_context}</div>
                    </div>
                    <div class="tarjeta-valor">{cobertura_porcentaje:.1f}%</div>
                </div>
                <div class="tarjeta-contenido">
                    <div class="cobertura-barra">
                        <div class="cobertura-progreso" style="width: {min(100, cobertura_porcentaje)}%; background: linear-gradient(135deg, {colors.get('success', '#10B981')}, {colors.get('secondary', '#F59E0B')})"></div>
                    </div>
                    <div class="tarjeta-estado" style="background: {color_estado}; color: white; padding: 6px 12px; border-radius: 6px; text-align: center; font-weight: 700; margin: 8px 0;">
                        {estado_cobertura}
                    </div>
                    <div class="tarjeta-metricas">
                        <div class="metrica-item success">
                            <div class="metrica-valor">{vacunados_total:,}</div>
                            <div class="metrica-etiqueta">Vacunados</div>
                        </div>
                        <div class="metrica-item danger">
                            <div class="metrica-valor">{rechazos_total:,}</div>
                            <div class="metrica-etiqueta">Rechazaron Vacuna</div>
                        </div>
                    </div>
                    <div class="tarjeta-poblacion" style="background: #f8fafc; padding: 8px 12px; border-radius: 6px; text-align: center; margin: 8px 0;">
                        👥 <strong>Población Total:</strong> {poblacion_total:,}
                    </div>
                    <div class="tarjeta-footer">
                        📅 Actualización: {ultima_actualizacion} | 📊 Calidad: {calidad_datos:.0f}%
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        logger.error(f"❌ Error creando HTML de tarjeta: {str(e)}")
        # Fallback simple
        st.error(f"Error mostrando tarjeta de cobertura: {str(e)}")
        return
    
    # ===== MOSTRAR ALERTAS CONTEXTUALES =====
    if alertas and len(alertas) > 0:
        try:
            with st.expander("⚠️ Alertas de Calidad de Datos", expanded=False):
                for alerta in alertas[:5]:  # Máximo 5 alertas para evitar saturación
                    if isinstance(alerta, str):
                        if "❌" in alerta:
                            st.error(alerta)
                        elif "📉" in alerta and ("crítica" in alerta or "muy baja" in alerta):
                            st.error(alerta)
                        elif "📈" in alerta and "muy alta" in alerta:
                            st.info(alerta)
                        elif "⚠️" in alerta:
                            st.warning(alerta)
                        else:
                            st.info(alerta)
                    else:
                        st.info(str(alerta))
        except Exception as e:
            logger.warning(f"⚠️ Error mostrando alertas: {str(e)}")
    
    # ✅ LLAMAR DEBUG SOLO EN MODO MÚLTIPLE Y CON MANEJO DE ERRORES        
    try:
        if filters.get("modo") == "multiple" and (municipios_sel or veredas_sel):
            debug_cobertura_multiple(cobertura_data, municipios_sel, veredas_sel)
    except Exception as e:
        logger.warning(f"⚠️ Error en debug de cobertura múltiple: {str(e)}")
            
def calculate_cobertura_manual_fallback(cobertura_data, municipios_seleccionados):
    """
    Cálculo manual de cobertura como fallback.
    """
    if not cobertura_data or not municipios_seleccionados:
        return 0.0
    
    try:
        from utils.cobertura_processor import get_cobertura_for_municipio
        
        total_poblacion = 0
        total_vacunados = 0
        municipios_procesados = 0
        
        for municipio in municipios_seleccionados:
            municipio_data = get_cobertura_for_municipio(cobertura_data, municipio)
            
            if municipio_data:
                poblacion = municipio_data.get("total_poblacion", 0)
                vacunados = municipio_data.get("total_vacunados", 0)
                
                if poblacion > 0:  # Solo incluir municipios con población válida
                    total_poblacion += poblacion
                    total_vacunados += vacunados
                    municipios_procesados += 1
                    logger.debug(f"  Manual: {municipio} - {vacunados}/{poblacion}")
        
        if total_poblacion > 0:
            cobertura_manual = (total_vacunados / total_poblacion) * 100
            logger.info(f"🔧 Cálculo manual: {cobertura_manual:.1f}% ({municipios_procesados} municipios)")
            return cobertura_manual
        else:
            return 0.0
            
    except Exception as e:
        logger.error(f"❌ Error en cálculo manual: {str(e)}")
        return 0.0
    
def calculate_cobertura_manual_fallback_full(cobertura_data, municipios_seleccionados, veredas_seleccionadas=None):
    """
    Cálculo manual completo (cobertura, vacunados, población).
    """
    if not cobertura_data or not municipios_seleccionados:
        return 0.0, 0, 0
    
    try:
        from utils.cobertura_processor import get_cobertura_for_municipio, get_cobertura_for_vereda
        
        total_poblacion = 0
        total_vacunados = 0
        
        if veredas_seleccionadas:
            # Calcular por veredas específicas
            for municipio in municipios_seleccionados:
                for vereda in veredas_seleccionadas:
                    vereda_data = get_cobertura_for_vereda(cobertura_data, municipio, vereda)
                    if vereda_data:
                        poblacion_ver = vereda_data.get("poblacion", 0)
                        vacunados_ver = vereda_data.get("vacunados", 0)
                        if poblacion_ver > 0:
                            total_poblacion += poblacion_ver
                            total_vacunados += vacunados_ver
        else:
            # Calcular por municipios completos
            for municipio in municipios_seleccionados:
                municipio_data = get_cobertura_for_municipio(cobertura_data, municipio)
                if municipio_data:
                    poblacion = municipio_data.get("total_poblacion", 0)
                    vacunados = municipio_data.get("total_vacunados", 0)
                    if poblacion > 0:
                        total_poblacion += poblacion
                        total_vacunados += vacunados
        
        cobertura = (total_vacunados / total_poblacion * 100) if total_poblacion > 0 else 0.0
        
        logger.info(f"🔧 Fallback completo: {cobertura:.1f}% ({total_vacunados:,}/{total_poblacion:,})")
        
        return cobertura, total_vacunados, total_poblacion
        
    except Exception as e:
        logger.error(f"❌ Error en fallback completo: {str(e)}")
        return 0.0, 0, 0
    
def debug_cobertura_multiple(cobertura_data, municipios_sel, veredas_sel=None):
    """
    Función de debug para verificar por qué la cobertura múltiple es 0%.
    """
    print("🧪 === DEBUG COBERTURA MÚLTIPLE ===")
    print(f"Municipios seleccionados: {municipios_sel}")
    print(f"Veredas seleccionadas: {veredas_sel}")
    
    if not cobertura_data:
        print("❌ No hay datos de cobertura")
        return
    
    if "municipios" not in cobertura_data:
        print("❌ No hay datos de municipios en cobertura_data")
        return
    
    print(f"📊 Municipios disponibles en datos: {len(cobertura_data['municipios'])}")
    print(f"📊 Primeros municipios: {list(cobertura_data['municipios'].keys())[:5]}")
    
    # Verificar cada municipio seleccionado
    for municipio in municipios_sel:
        print(f"\n🔍 Verificando: {municipio}")
        
        from utils.cobertura_processor import get_cobertura_for_municipio
        municipio_data = get_cobertura_for_municipio(cobertura_data, municipio)
        
        if municipio_data:
            poblacion = municipio_data.get("total_poblacion", 0)
            vacunados = municipio_data.get("total_vacunados", 0)
            cobertura = municipio_data.get("cobertura_general", 0.0)
            print(f"  ✅ Encontrado: {cobertura:.1f}% ({vacunados:,}/{poblacion:,})")
        else:
            print(f"  ❌ No encontrado")
            # Buscar nombres similares
            municipios_disponibles = list(cobertura_data['municipios'].keys())
            similares = [m for m in municipios_disponibles if municipio.upper() in m.upper() or m.upper() in municipio.upper()]
            if similares:
                print(f"  🎯 Similares: {similares}")
    
    print("🧪 === FIN DEBUG ===")

def calculate_rechazos_multiple_improved(cobertura_data, municipios_seleccionados, veredas_seleccionadas=None):
    """
    ✅ VERSIÓN SEGURA: Calcula rechazos para selección múltiple
    """
    if not cobertura_data:
        logger.warning("⚠️ No hay datos de cobertura para calcular rechazos")
        return 0
    
    total_rechazos = 0
    
    try:
        from utils.cobertura_processor import get_rechazos_for_municipio, get_rechazos_for_vereda
        
        if veredas_seleccionadas:
            # Rechazos por veredas específicas
            for municipio in municipios_seleccionados:
                for vereda in veredas_seleccionadas:
                    try:
                        rechazos_vereda = get_rechazos_for_vereda(cobertura_data, municipio, vereda)
                        if isinstance(rechazos_vereda, (int, float)) and rechazos_vereda > 0:
                            total_rechazos += int(rechazos_vereda)
                    except Exception as e:
                        logger.warning(f"⚠️ Error obteniendo rechazos para {vereda} en {municipio}: {str(e)}")
                        continue
        else:
            # Rechazos por municipios completos
            for municipio in municipios_seleccionados:
                try:
                    rechazos_municipio = get_rechazos_for_municipio(cobertura_data, municipio)
                    if isinstance(rechazos_municipio, (int, float)) and rechazos_municipio > 0:
                        total_rechazos += int(rechazos_municipio)
                except Exception as e:
                    logger.warning(f"⚠️ Error obteniendo rechazos para {municipio}: {str(e)}")
                    continue
                
    except ImportError:
        logger.warning("⚠️ Funciones de rechazos no disponibles")
        return 0
    except Exception as e:
        logger.error(f"❌ Error general calculando rechazos múltiples: {str(e)}")
        return 0
    
    return total_rechazos

def calculate_rechazos_by_filters_improved(cobertura_data, filters):
    """
    ✅ VERSIÓN SEGURA: Calcula rechazos según filtros aplicados
    """
    if not cobertura_data:
        logger.warning("⚠️ No hay datos de cobertura para calcular rechazos por filtros")
        return 0
    
    municipio_filter = filters.get("municipio_display", "Todos")
    vereda_filter = filters.get("vereda_display", "Todas")
    
    try:
        from utils.cobertura_processor import get_rechazos_for_municipio, get_rechazos_for_vereda
        
        if vereda_filter != "Todas" and municipio_filter != "Todos":
            # Vereda específica
            rechazos = get_rechazos_for_vereda(cobertura_data, municipio_filter, vereda_filter)
            return int(rechazos) if isinstance(rechazos, (int, float)) and rechazos >= 0 else 0
            
        elif municipio_filter != "Todos":
            # Municipio específico
            rechazos = get_rechazos_for_municipio(cobertura_data, municipio_filter)
            return int(rechazos) if isinstance(rechazos, (int, float)) and rechazos >= 0 else 0
            
        else:
            # Departamental - sumar todos los municipios con validación
            total_rechazos = 0
            
            municipios_data = cobertura_data.get("municipios", {})
            if not isinstance(municipios_data, dict):
                logger.warning("⚠️ Datos de municipios no válidos")
                return 0
            
            for municipio_name, municipio_data in municipios_data.items():
                try:
                    if isinstance(municipio_data, dict):
                        rechazos_mun = municipio_data.get("total_rechazos", 0)
                        if isinstance(rechazos_mun, (int, float)) and rechazos_mun >= 0:
                            total_rechazos += int(rechazos_mun)
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando rechazos de {municipio_name}: {str(e)}")
                    continue
            
            return total_rechazos
            
    except ImportError:
        logger.warning("⚠️ Funciones de rechazos no disponibles")
        return 0
    except Exception as e:
        logger.error(f"❌ Error calculando rechazos por filtros: {str(e)}")
        return 0

def load_cobertura_data_direct():
    """
    ✅ VERSIÓN MUY SEGURA: Carga directa de datos de cobertura
    """
    try:
        from utils.cobertura_processor import load_and_process_cobertura_data
        cobertura_data = load_and_process_cobertura_data()
        
        # Verificar que los datos están en el formato esperado
        if cobertura_data and isinstance(cobertura_data, dict):
            if "municipios" in cobertura_data:
                logger.info("✅ Datos de cobertura cargados correctamente")
                return cobertura_data
            else:
                logger.warning("⚠️ Datos de cobertura sin estructura 'municipios'")
                return None
        else:
            logger.warning("⚠️ load_and_process_cobertura_data retornó datos inválidos")
            return None
            
    except ImportError as e:
        logger.error(f"❌ ImportError cargando cobertura: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Error inesperado cargando cobertura: {str(e)}")
        return None

def create_urban_data_card_simplified(filters, colors, data_filtered):
    """Tarjeta para mostrar datos urbanos que no se visualizan en mapas."""
    cobertura_data = load_cobertura_data_direct()
    
    if not cobertura_data:
        return  # No mostrar si no hay datos
    
    try:
        from utils.cobertura_processor import (
            calculate_urban_data_not_visualized,
            get_cobertura_for_municipio
        )
        
        # Determinar datos urbanos según filtro
        municipio_filter = filters.get("municipio_display", "Todos")
        
        if municipio_filter != "Todos":
            # Datos urbanos del municipio específico
            municipio_data = get_cobertura_for_municipio(cobertura_data, municipio_filter)
            if municipio_data and municipio_data.get("urbano", {}).get("poblacion", 0) > 0:
                urbano_data = municipio_data["urbano"]
                contexto = f"Casco urbano de {municipio_filter}"
                show_card = True
            else:
                show_card = False
        else:
            # Datos urbanos departamentales
            urbano_data = calculate_urban_data_not_visualized(cobertura_data)
            contexto = f"Cascos urbanos ({urbano_data['municipios_con_urbano']} municipios)"
            show_card = urbano_data["poblacion"] > 0
        
        if not show_card:
            return
        
        poblacion_urbana = urbano_data["poblacion"]
        vacunados_urbanos = urbano_data["vacunados"]
        cobertura_urbana = urbano_data["cobertura"]
        
        # Determinar color según cobertura
        if cobertura_urbana >= 95:
            color_fondo = colors["success"]
            icono = "🟢"
        elif cobertura_urbana >= 80:
            color_fondo = colors["warning"]
            icono = "🟡"
        else:
            color_fondo = colors["danger"]
            icono = "🔴"
        
        st.markdown(
            f"""
            <div class="tarjeta-optimizada urban-data-card" style="border-left: 5px solid {color_fondo};">
                <div class="tarjeta-header">
                    <div class="tarjeta-icon">🏙️</div>
                    <div class="tarjeta-info">
                        <div class="tarjeta-titulo">DATOS URBANOS</div>
                        <div class="tarjeta-subtitulo">{contexto}</div>
                    </div>
                    <div class="tarjeta-valor">{icono}</div>
                </div>
                <div class="tarjeta-contenido">
                    <div class="tarjeta-metricas">
                        <div class="metrica-item info">
                            <div class="metrica-valor">{poblacion_urbana:,}</div>
                            <div class="metrica-etiqueta">Población</div>
                        </div>
                        <div class="metrica-item success">
                            <div class="metrica-valor">{cobertura_urbana:.1f}%</div>
                            <div class="metrica-etiqueta">Cobertura</div>
                        </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    except ImportError:
        pass  # No mostrar si las funciones no están disponibles

def prepare_vereda_data_coverage_simplified(veredas_gdf, municipio_selected, colors, cobertura_data=None):
    """
    Preparación de datos de cobertura con logging detallado
    """
    logger.info(f"🏘️ Preparando cobertura para {municipio_selected} (CON DEBUG)")
    
    veredas_data = veredas_gdf.copy()
    
    # Esquema de colores
    color_scheme = {
        "cobertura_alta": colors.get("success", "#10B981"),
        "cobertura_buena": colors.get("secondary", "#F59E0B"),
        "cobertura_regular": colors.get("warning", "#EF4444"),
        "cobertura_baja": colors.get("danger", "#DC2626"),
        "cobertura_muy_baja": "#991B1B",
        "sin_datos": "#E5E7EB",
    }
    
    # Cargar datos
    if cobertura_data is None:
        try:
            from utils.cobertura_processor import load_and_process_cobertura_data
            cobertura_data = load_and_process_cobertura_data()
            logger.info("✅ Datos de cobertura cargados")
        except Exception as e:
            logger.error(f"❌ Error cargando cobertura: {str(e)}")
            cobertura_data = None
    
    if not cobertura_data:
        logger.warning("⚠️ Sin datos de cobertura - todo en gris")
        # Aplicar gris a todo
        for idx, row in veredas_data.iterrows():
            veredas_data.loc[idx, "color"] = color_scheme["sin_datos"]
            veredas_data.loc[idx, "descripcion_color"] = "Sin datos de cobertura"
            veredas_data.loc[idx, "cobertura"] = 0.0
            veredas_data.loc[idx, "poblacion"] = 0
            veredas_data.loc[idx, "vacunados"] = 0
        return veredas_data
    
    # ✅ VERIFICAR MUNICIPIO PRIMERO
    municipio_cobertura = get_cobertura_for_municipio(cobertura_data, municipio_selected)
    if not municipio_cobertura:
        logger.error(f"❌ Municipio '{municipio_selected}' no encontrado en datos de cobertura")
        
        # Intentar con mapeo
        municipio_mapeado = get_mapped_municipio(municipio_selected, "data_to_shapefile")
        if municipio_mapeado != municipio_selected:
            logger.info(f"🔗 Intentando mapeo: '{municipio_selected}' → '{municipio_mapeado}'")
            municipio_cobertura = get_cobertura_for_municipio(cobertura_data, municipio_mapeado)
            if municipio_cobertura:
                logger.info(f"✅ Municipio encontrado con mapeo")
                municipio_selected = municipio_mapeado  # Usar nombre mapeado
        
        if not municipio_cobertura:
            logger.error(f"❌ Municipio no encontrado ni con mapeo - todo en gris")
            # Todo en gris
            for idx, row in veredas_data.iterrows():
                veredas_data.loc[idx, "color"] = color_scheme["sin_datos"]
                veredas_data.loc[idx, "descripcion_color"] = "Municipio no encontrado"
                veredas_data.loc[idx, "cobertura"] = 0.0
                veredas_data.loc[idx, "poblacion"] = 0
                veredas_data.loc[idx, "vacunados"] = 0
            return veredas_data
    
    logger.info(f"✅ Municipio encontrado: {municipio_selected}")
    
    # Procesar cada vereda
    vereda_col = get_vereda_column(veredas_data)
    if not vereda_col:
        logger.error("❌ No se encontró columna de veredas")
        return veredas_data
    
    veredas_procesadas = 0
    veredas_con_datos = 0
    veredas_sin_datos = 0
    
    for idx, row in veredas_data.iterrows():
        try:
            vereda_name = safe_get_feature_name(row, vereda_col)
            if not vereda_name:
                vereda_name = f"VEREDA_{idx}"
            
            veredas_procesadas += 1
            
            # ✅ BUSCAR DATOS CON DEBUG
            vereda_coverage = get_cobertura_for_vereda(cobertura_data, municipio_selected, vereda_name)
            
            if vereda_coverage:
                cobertura = vereda_coverage.get("cobertura", 0.0)
                poblacion = vereda_coverage.get("poblacion", 0)
                vacunados = vereda_coverage.get("vacunados", 0)
                
                if poblacion > 0:
                    veredas_con_datos += 1
                    
                    # Determinar color
                    if cobertura >= 95.0:
                        color = color_scheme["cobertura_alta"]
                        descripcion = f"Cobertura alta: {cobertura:.1f}%"
                    elif cobertura >= 80.0:
                        color = color_scheme["cobertura_buena"]
                        descripcion = f"Cobertura buena: {cobertura:.1f}%"
                    elif cobertura >= 60.0:
                        color = color_scheme["cobertura_regular"]
                        descripcion = f"Cobertura regular: {cobertura:.1f}%"
                    elif cobertura >= 40.0:
                        color = color_scheme["cobertura_baja"]
                        descripcion = f"Cobertura baja: {cobertura:.1f}%"
                    elif cobertura > 0.0:
                        color = color_scheme["cobertura_muy_baja"]
                        descripcion = f"Cobertura muy baja: {cobertura:.1f}%"
                    else:
                        color = color_scheme["sin_datos"]
                        descripcion = "Sin cobertura de vacunación"
                    
                    logger.debug(f"  ✅ {vereda_name}: {descripcion}")
                else:
                    # Datos inconsistentes
                    veredas_sin_datos += 1
                    color = color_scheme["sin_datos"]
                    descripcion = "Datos inconsistentes"
                    cobertura = 0.0
                    poblacion = 0
                    vacunados = 0
                    logger.warning(f"  ⚠️ {vereda_name}: población={poblacion}, vacunados={vacunados}")
            else:
                # Sin datos
                veredas_sin_datos += 1
                color = color_scheme["sin_datos"]
                descripcion = "Sin datos de cobertura"
                cobertura = 0.0
                poblacion = 0
                vacunados = 0
                logger.debug(f"  📭 {vereda_name}: sin datos")
                
                # DEBUG: Si es la primera vereda sin datos, hacer debug detallado
                if veredas_sin_datos == 1:
                    debug_vereda_mapping(cobertura_data, municipio_selected, vereda_name)
            
            # Asignar valores
            veredas_data.loc[idx, "color"] = color
            veredas_data.loc[idx, "descripcion_color"] = descripcion
            veredas_data.loc[idx, "cobertura"] = float(cobertura)
            veredas_data.loc[idx, "poblacion"] = int(poblacion)
            veredas_data.loc[idx, "vacunados"] = int(vacunados)
            
        except Exception as e:
            logger.error(f"❌ Error procesando vereda {vereda_name}: {str(e)}")
            veredas_data.loc[idx, "color"] = color_scheme["sin_datos"]
            veredas_data.loc[idx, "descripcion_color"] = "Error en procesamiento"
            veredas_data.loc[idx, "cobertura"] = 0.0
            veredas_data.loc[idx, "poblacion"] = 0
            veredas_data.loc[idx, "vacunados"] = 0
    
    # ✅ REPORTE FINAL
    logger.info(f"📊 RESUMEN {municipio_selected}:")
    logger.info(f"  - Veredas procesadas: {veredas_procesadas}")
    logger.info(f"  - Veredas con datos: {veredas_con_datos}")
    logger.info(f"  - Veredas sin datos: {veredas_sin_datos}")
    logger.info(f"  - Porcentaje éxito: {(veredas_con_datos/veredas_procesadas*100):.1f}%")
    
    return veredas_data

def load_geographic_data():
    """Carga datos geográficos."""
    if not SHAPEFILE_LOADER_AVAILABLE:
        return None

    try:
        return load_shapefile_data()
    except Exception as e:
        logger.error(f"❌ Error cargando datos geográficos: {str(e)}")
        return None

def determine_map_level(filters):
    """Determina el nivel del mapa según filtros."""

    if filters.get("modo") == "multiple":
        municipios_seleccionados = filters.get("municipios_seleccionados", [])
        veredas_seleccionadas = filters.get("veredas_seleccionadas", [])
        
        # Solo retornar "multiple" si realmente hay selecciones
        if municipios_seleccionados or veredas_seleccionadas:
            logger.info("🗂️ Nivel detectado: MÚLTIPLE (con selecciones)")
            return "multiple"
        else:
            logger.info("🏛️ Nivel detectado: DEPARTAMENTO (múltiple sin selecciones)")
            return "departamento"
    
    # ===== LÓGICA EXISTENTE PARA OTROS MODOS =====
    if filters.get("vereda_display") and filters.get("vereda_display") != "Todas":
        logger.info("🏘️ Nivel detectado: VEREDA")
        return "vereda"
    elif (
        filters.get("municipio_display") 
        and filters.get("municipio_display") != "Todos"
        and filters.get("municipio_display") != "Multiple"  # Evitar el marcador "Multiple"
    ):
        logger.info("🏛️ Nivel detectado: MUNICIPIO")
        return "municipio"
    else:
        logger.info("🗺️ Nivel detectado: DEPARTAMENTO")
        return "departamento"

def validate_multiple_selection_state(filters):
    """Valida el estado de la selección múltiple."""
    if filters.get("modo") != "multiple":
        return True
    
    municipios_sel = filters.get("municipios_seleccionados", [])
    veredas_sel = filters.get("veredas_seleccionadas", [])
    
    logger.info(f"🔍 Validando selección múltiple: {len(municipios_sel)} municipios, {len(veredas_sel)} veredas")
    
    # Casos válidos:
    # 1. Al menos un municipio seleccionado
    # 2. Al menos una vereda seleccionada
    # 3. Ambos
    
    is_valid = len(municipios_sel) > 0 or len(veredas_sel) > 0
    
    if not is_valid:
        logger.warning("⚠️ Selección múltiple sin elementos seleccionados")
    
    return is_valid

def show_multiple_selection_status(filters, colors):
    """Muestra el estado actual de la selección múltiple en el sidebar."""
    if filters.get("modo") != "multiple":
        return
    
    municipios_sel = filters.get("municipios_seleccionados", [])
    veredas_sel = filters.get("veredas_seleccionadas", [])
    
    if not municipios_sel and not veredas_sel:
        # Estado inicial - instrucciones
        st.sidebar.markdown(
            f"""
            <div style="
                background: {colors['light']};
                padding: 12px;
                border-radius: 8px;
                border-left: 4px solid {colors['info']};
                margin: 10px 0;
            ">
                <strong>🗂️ Modo Múltiple Activo</strong><br>
                <small>Seleccione municipios y/o veredas usando los controles de arriba.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Estado con selecciones - resumen
        total_elementos = len(municipios_sel) + len(veredas_sel)
        st.sidebar.markdown(
            f"""
            <div style="
                background: {colors['success']};
                color: white;
                padding: 12px;
                border-radius: 8px;
                margin: 10px 0;
                text-align: center;
            ">
                <strong>✅ {total_elementos} Elementos Seleccionados</strong><br>
                <small>{len(municipios_sel)} municipios • {len(veredas_sel)} veredas</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

def get_filter_context_compact(filters):
    """Contexto de filtrado compacto."""
    municipio = filters.get("municipio_display", "Todos")
    vereda = filters.get("vereda_display", "Todas")

    if vereda != "Todas":
        return f"{vereda[:12]}..."
    elif municipio != "Todos":
        return f"{municipio[:12]}..."
    else:
        return "Tolima"

def create_casos_card_optimized(casos, filters, colors):
    """Tarjeta de casos."""
    filter_context = get_filter_context_compact(filters)
    metrics = calculate_basic_metrics(casos, pd.DataFrame())

    total_casos = metrics["total_casos"]
    vivos = metrics["vivos"]
    fallecidos = metrics["fallecidos"]
    letalidad = metrics["letalidad"]
    ultimo_caso = metrics["ultimo_caso"]

    ultimo_caso_info = "Sin casos"
    if ultimo_caso["existe"]:
        ultimo_caso_info = (
            f"Ultimo caso confirmado:\n \n📍{ultimo_caso['ubicacion'][:50]} \n ⌚{ultimo_caso['tiempo_transcurrido']}"
        )

    st.markdown(
        f"""
        <div class="tarjeta-optimizada casos-card">
            <div class="tarjeta-header">
                <div class="tarjeta-icon">🦠</div>
                <div class="tarjeta-info">
                    <div class="tarjeta-titulo">CASOS</div>
                    <div class="tarjeta-subtitulo">{filter_context}</div>
                </div>
                <div class="tarjeta-valor">{total_casos}</div>
            </div>
            <div class="tarjeta-contenido">
                <div class="tarjeta-metricas">
                    <div class="metrica-item success">
                        <div class="metrica-valor">{vivos}</div>
                        <div class="metrica-etiqueta">Vivos</div>
                    </div>
                    <div class="metrica-item danger">
                        <div class="metrica-valor">{fallecidos}</div>
                        <div class="metrica-etiqueta">Fallecidos</div>
                    </div>
                </div>
                <div class="tarjeta-estadistica">
                    Letalidad: <strong>{letalidad:.1f}%</strong>
                </div>
                <div class="tarjeta-footer">
                    {ultimo_caso_info}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def create_epizootias_card_optimized(epizootias, filters, colors):
    """Tarjeta de epizootias optimizada."""
    filter_context = get_filter_context_compact(filters)
    metrics = calculate_basic_metrics(pd.DataFrame(), epizootias)

    total_epizootias = metrics["total_epizootias"]
    positivas = metrics["epizootias_positivas"]
    en_estudio = metrics["epizootias_en_estudio"]
    ultima_epizootia = metrics["ultima_epizootia_positiva"]

    ultima_epi_info = "Sin epizootias"
    if ultima_epizootia["existe"]:
        ultima_epi_info = f"Ultima epizootia positiva:\n \n📍{ultima_epizootia['ubicacion'][:50]} ⌚{ultima_epizootia['tiempo_transcurrido']}"
    st.markdown(
        f"""
        <div class="tarjeta-optimizada epizootias-card">
            <div class="tarjeta-header">
                <div class="tarjeta-icon">🐒</div>
                <div class="tarjeta-info">
                    <div class="tarjeta-titulo">EPIZOOTIAS</div>
                    <div class="tarjeta-subtitulo">{filter_context}</div>
                </div>
                <div class="tarjeta-valor">{total_epizootias}</div>
            </div>
            <div class="tarjeta-contenido">
                <div class="tarjeta-metricas">
                    <div class="metrica-item danger">
                        <div class="metrica-valor">{positivas}</div>
                        <div class="metrica-etiqueta">Positivas</div>
                    </div>
                    <div class="metrica-item info">
                        <div class="metrica-valor">{en_estudio}</div>
                        <div class="metrica-etiqueta">En Estudio</div>
                    </div>
                </div>
                <div class="tarjeta-footer">
                    {ultima_epi_info}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def create_folium_map(geo_data, zoom_start=8, max_height=500):
    """Crea mapa base de Folium."""
    if hasattr(geo_data, "total_bounds"):
        bounds = geo_data.total_bounds
    else:
        bounds = geo_data.bounds
        if len(bounds) > 0:
            bounds = [
                bounds.minx.min(),
                bounds.miny.min(),
                bounds.maxx.max(),
                bounds.maxy.max(),
            ]
        else:
            bounds = [-76.0, 3.5, -74.5, 5.5]

    center_lat, center_lon = (bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles="CartoDB positron",
        attributionControl=False,
        zoom_control=True,
        scrollWheelZoom=True,
        height=min(max_height, 500)  # Máximo 500px
    )

    if len(bounds) == 4:
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    return m


def add_municipios_to_map_simplified(folium_map, municipios_data, colors, modo_mapa):
    """Agrega municipios al mapa SIMPLIFICADO."""
    municipio_col = get_municipio_column(municipios_data)

    for idx, row in municipios_data.iterrows():
        municipio_name = row.get(municipio_col, "DESCONOCIDO")
        color = row["color"]

        tooltip_text = create_municipio_tooltip_simplified(
            municipio_name, row, colors, modo_mapa
        )

        folium.GeoJson(
            row["geometry"],
            style_function=lambda x, color=color: {
                "fillColor": color,
                "color": colors["primary"],
                "weight": 2,
                "fillOpacity": 0.7,
                "opacity": 1,
            },
            tooltip=folium.Tooltip(tooltip_text, sticky=True),
        ).add_to(folium_map)

def add_veredas_to_map_simplified(folium_map, veredas_data, colors, modo_mapa):
    """Agrega veredas al mapa COMPLETAMENTE SEGURO."""
    vereda_col = get_vereda_column(veredas_data)

    if not vereda_col:
        logger.error("❌ No se encontró columna de veredas")
        return

    for idx, row in veredas_data.iterrows():
        try:
            vereda_name = safe_get_feature_name(row, vereda_col) or f"VEREDA_{idx}"
            color = row.get("color", colors.get("sin_datos", "#E5E7EB"))

            # Usar tooltip seguro
            tooltip_text = create_vereda_tooltip_simplified(
                vereda_name, row, colors, modo_mapa
            )

            folium.GeoJson(
                row["geometry"],
                style_function=lambda x, color=color: {
                    "fillColor": color,
                    "color": colors.get("accent", "#5A4214"),
                    "weight": 1.5,
                    "fillOpacity": 0.6,
                    "opacity": 0.8,
                },
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            ).add_to(folium_map)
            
        except Exception as e:
            logger.warning(f"⚠️ Error agregando vereda {vereda_name}: {str(e)}")
            continue

def create_municipio_tooltip_simplified(name, row, colors, modo_mapa):
    """Tooltip para municipio."""
    if modo_mapa == "Epidemiológico":
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
    else:
        # Tooltip mejorado para cobertura con datos reales
        poblacion = row.get('poblacion', 0)
        vacunados = row.get('vacunados', 0)
        cobertura = row.get('cobertura', 0)
        
        # Información adicional si tenemos datos reales
        info_adicional = ""
        if poblacion > 0:
            info_adicional = f"<br>👥 Población: {poblacion:,}<br>💉 Vacunados: {vacunados:,}"
        
        return f"""
        <div style="font-family: Arial; padding: 10px; max-width: 250px;">
            <b style="color: {colors['primary']}; font-size: 1.1em;">🏛️ {name}</b><br>
            <div style="margin: 8px 0; padding: 6px; background: #f0f8ff; border-radius: 4px;">
                💉 Cobertura: {cobertura:.1f}%{info_adicional}<br>
                📊 {row.get('descripcion_color', 'Sin datos')}
            </div>
            <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
        </div>
        """

def create_vereda_tooltip_simplified(name, row, colors, modo_mapa):
    """Tooltip para vereda COMPLETAMENTE SEGURO."""
    try:
        if modo_mapa == "Epidemiológico":
            casos = safe_int_conversion(row.get('casos', 0))
            epizootias = safe_int_conversion(row.get('epizootias', 0))
            descripcion = str(row.get('descripcion_color', 'Sin datos'))
            
            return f"""
            <div style="font-family: Arial; padding: 8px; max-width: 200px;">
                <b style="color: {colors['primary']};">🏘️ {name}</b><br>
                <div style="margin: 6px 0; font-size: 0.9em;">
                    🦠 Casos: {casos}<br>
                    🐒 Epizootias: {epizootias}<br>
                </div>
                <div style="color: {colors['info']}; font-size: 0.8em;">
                    {descripcion}
                </div>
                <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
            </div>
            """
        else:
            # Modo cobertura - acceso seguro
            cobertura = safe_float_conversion(row.get('cobertura', 0))
            poblacion = safe_int_conversion(row.get('poblacion', 0))
            vacunados = safe_int_conversion(row.get('vacunados', 0))
            descripcion = str(row.get('descripcion_color', 'Sin datos'))
            
            # Información adicional solo si hay datos válidos
            info_adicional = ""
            if poblacion > 0:
                info_adicional = f"<br><span style='font-size: 0.8em;'>👥 {poblacion:,} | 💉 {vacunados:,}</span>"
            
            return f"""
            <div style="font-family: Arial; padding: 8px; max-width: 200px;">
                <b style="color: {colors['primary']};">🏘️ {name}</b><br>
                <div style="margin: 6px 0;">
                    💉 Cobertura: {cobertura:.1f}%{info_adicional}
                </div>
                <div style="color: {colors['info']}; font-size: 0.8em;">
                    {descripcion}
                </div>
                <i style="color: {colors['accent']}; font-size: 0.8em;">👆 Clic para filtrar</i>
            </div>
            """
            
    except Exception as e:
        logger.error(f"❌ Error creando tooltip para {name}: {str(e)}")
        return f"""
        <div style="font-family: Arial; padding: 8px;">
            <b>🏘️ {name}</b><br>
            <i style="color: red;">Error en tooltip</i>
        </div>
        """

def show_fallback_summary(casos, epizootias, level, location=None):
    """Resumen cuando no hay mapas."""
    st.info(f"📊 Vista tabular - {level} (mapas no disponibles)")


def show_maps_not_available():
    """Muestra mensaje cuando mapas no están disponibles."""
    st.error("🗺️ Los mapas no están disponibles")


def show_geographic_data_error():
    """Muestra error cuando no se pueden cargar datos geográficos."""
    st.error("❌ No se pudieron cargar los datos geográficos")

def apply_maps_css_optimized(colors):
    """CSS optimizado SIN duplicar estilos críticos que causan scroll infinito."""
    st.markdown(
        f"""
        <style>
        /* =============== INFO Y CONTEXTO =============== */
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
        
        /* =============== TARJETAS ESTÉTICAS =============== */
        .tarjeta-optimizada {{
            background: linear-gradient(135deg, white 0%, #f8fafc 50%, #f1f5f9 100%);
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.12);
            overflow: hidden;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.3);
            position: relative;
        }}
        
        .tarjeta-optimizada::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 60px;
            height: 60px;
            background: radial-gradient(circle, {colors['secondary']}30, transparent);
            border-radius: 50%;
            transform: translate(30%, -30%);
        }}
        
        .tarjeta-optimizada:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 48px rgba(0,0,0,0.18);
        }}
        
        /* TIPOS DE TARJETAS */
        .cobertura-card {{ border-left: 5px solid {colors['success']}; }}
        .casos-card {{ border-left: 5px solid {colors['danger']}; }}
        .epizootias-card {{ border-left: 5px solid {colors['warning']}; }}
        .afectacion-card {{ border-left: 5px solid {colors['primary']}; }}
        
        /* =============== CONTENIDO DE TARJETAS =============== */
        .tarjeta-header {{
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.95));
            padding: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            position: relative;
            z-index: 2;
        }}
        
        .tarjeta-icon {{
            font-size: 2rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }}
        
        .tarjeta-info {{
            flex: 1;
        }}
        
        .tarjeta-titulo {{
            color: {colors['primary']};
            font-size: 1rem;
            font-weight: 800;
            margin: 0;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }}
        
        .tarjeta-subtitulo {{
            color: {colors['accent']};
            font-size: 0.75rem;
            font-weight: 600;
            margin: 2px 0 0 0;
            opacity: 0.9;
        }}
        
        .tarjeta-valor {{
            font-size: 2rem;
            font-weight: 900;
            color: {colors['primary']};
            text-shadow: 2px 2px 4px rgba(0,0,0,0.15);
        }}
        
        .tarjeta-contenido {{
            padding: 16px;
            position: relative;
            z-index: 2;
        }}
        
        .tarjeta-metricas {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 12px;
        }}
        
        .metrica-item {{
            background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(248,250,252,0.9));
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            transition: all 0.3s ease;
            border: 2px solid transparent;
            backdrop-filter: blur(10px);
        }}
        
        .metrica-item:hover {{
            transform: scale(1.02);
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.95));
        }}
        
        .metrica-item.success {{ border-color: {colors['success']}; }}
        .metrica-item.danger {{ border-color: {colors['danger']}; }}
        .metrica-item.info {{ border-color: {colors['info']}; }}
        .metrica-item.warning {{ border-color: {colors['warning']}; }}
        
        .metrica-valor {{
            font-size: 1.3rem;
            font-weight: 800;
            color: {colors['primary']};
            margin-bottom: 4px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }}
        
        .metrica-etiqueta {{
            font-size: 0.7rem;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .tarjeta-estadistica {{
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']});
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            text-align: center;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        .tarjeta-footer {{
            background: linear-gradient(135deg, rgba(248,250,252,0.8), rgba(241,245,249,0.8));
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            border-left: 3px solid {colors['secondary']};
            color: #475569;
        }}
        
        /* =============== BARRA DE COBERTURA =============== */
        .cobertura-barra {{
            background: #e5e7eb;
            height: 8px;
            border-radius: 4px;
            margin: 10px 0;
            overflow: hidden;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .cobertura-progreso {{
            background: linear-gradient(135deg, {colors['success']}, {colors['secondary']});
            height: 100%;
            border-radius: 4px;
            transition: width 0.6s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }}
        
        /* =============== AFECTACIÓN =============== */
        .afectacion-items {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 12px;
        }}
        
        .afectacion-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 10px;
            background: linear-gradient(135deg, rgba(248,250,252,0.8), rgba(255,255,255,0.8));
            border-radius: 8px;
            font-size: 0.85rem;
            transition: all 0.3s ease;
        }}
        
        .afectacion-item:hover {{
            background: linear-gradient(135deg, rgba(241,245,249,0.9), rgba(248,250,252,0.9));
            transform: translateX(3px);
        }}
        
        .afectacion-icono {{
            font-size: 1.1rem;
            filter: drop-shadow(0 1px 2px rgba(0,0,0,0.2));
        }}
        
        .afectacion-texto {{
            color: {colors['dark']};
            font-weight: 600;
            flex: 1;
        }}
        
        /* =============== RESPONSIVE MOBILE =============== */
        @media (max-width: 768px) {{
            .tarjeta-header {{
                padding: 12px;
            }}
            
            .tarjeta-contenido {{
                padding: 12px;
            }}
            
            .tarjeta-metricas {{
                grid-template-columns: 1fr;
                gap: 8px;
            }}
            
            .tarjeta-valor {{
                font-size: 1.4rem;
            }}
            
            .metrica-valor {{
                font-size: 1rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )