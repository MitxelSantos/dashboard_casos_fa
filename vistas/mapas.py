"""
Vista de mapas SIMPLIFICADA - Sin normalización compleja
Soluciona: Error Ibagué, MARIQUITA vs SAN SEBASTIAN, clics departamental→municipal, afectación
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

from utils.data_processor import calculate_basic_metrics, verify_filtered_data_usage

# Sistema híbrido de shapefiles
try:
    from utils.shapefile_loader import (
        load_tolima_shapefiles,
        check_shapefiles_availability,
        show_shapefile_setup_instructions,
    )

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

# ===== FUNCIONES DE MAPEO SIMPLIFICADAS =====


def simple_name_match(name1: str, name2: str) -> bool:
    """Comparación simple con mapeo de inconsistencias conocidas."""
    if not name1 or not name2:
        return False

    name1_clean = str(name1).strip()
    name2_clean = str(name2).strip()

    # Comparación directa
    if name1_clean == name2_clean:
        return True

    # Verificar mapeos conocidos
    mapped_name1 = MUNICIPIO_MAPPING.get(name1_clean, name1_clean)
    mapped_name2 = MUNICIPIO_MAPPING.get(name2_clean, name2_clean)

    return mapped_name1 == mapped_name2


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
        "casos_epizootias_fallecidos": colors["danger"],
        "solo_casos": colors["warning"],
        "solo_epizootias": colors["secondary"],
        "sin_datos": "#E5E7EB",
        "seleccionado": colors["primary"],
        "no_seleccionado": "#F3F4F6",
    }


def get_color_scheme_coverage(colors):
    """Esquema de colores por cobertura de vacunación."""
    return {
        "cobertura_alta": colors["success"],
        "cobertura_buena": colors["secondary"],
        "cobertura_regular": colors["warning"],
        "cobertura_baja": colors["danger"],
        "sin_datos": "#E5E7EB",
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
    """Determina color según modo epidemiológico - CORREGIDO."""
    try:
        # Asegurar que todos los valores sean enteros
        casos_count = int(casos_count) if pd.notna(casos_count) else 0
        epizootias_count = int(epizootias_count) if pd.notna(epizootias_count) else 0
        fallecidos_count = int(fallecidos_count) if pd.notna(fallecidos_count) else 0
        positivas_count = int(positivas_count) if pd.notna(positivas_count) else 0
        en_estudio_count = int(en_estudio_count) if pd.notna(en_estudio_count) else 0

        # Lógica de coloreo corregida
        if casos_count > 0 and epizootias_count > 0 and fallecidos_count > 0:
            return (
                color_scheme["casos_epizootias_fallecidos"],
                "🔴 Casos + Epizootias + Fallecidos",
            )
        elif casos_count > 0 and epizootias_count == 0:
            return color_scheme["solo_casos"], "🟠 Solo casos"
        elif casos_count == 0 and epizootias_count > 0:
            return color_scheme["solo_epizootias"], "🟡 Solo epizootias"
        else:
            return color_scheme["sin_datos"], "⚪ Sin datos"

    except Exception as e:
        logger.warning(f"⚠️ Error determinando color: {str(e)}")
        return color_scheme["sin_datos"], "⚪ Error en coloreo"


# ===== FUNCIÓN PRINCIPAL =====


def show(data_filtered, filters, colors):
    """Vista principal de mapas."""
    logger.info("🗺️ INICIANDO VISTA DE MAPAS CON DEBUG COMPLETO")

    # Debug de entradas
    debug_show_function_inputs(data_filtered, filters, colors)

    apply_maps_css_optimized(colors)

    casos_filtrados = data_filtered["casos"]
    epizootias_filtradas = data_filtered["epizootias"]

    verify_filtered_data_usage(casos_filtrados, "vista_mapas")
    verify_filtered_data_usage(epizootias_filtradas, "vista_mapas")

    if not MAPS_AVAILABLE:
        show_maps_not_available()
        return

    if not check_shapefiles_availability():
        show_shapefile_setup_instructions()
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
                🎯 Vista: <strong>{modo_mapa}</strong> | Filtros: <strong>{' • '.join(active_filters[:2])}</strong>
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

    with col_tarjetas1:
        create_cobertura_card_simplified(filters, colors, data_filtered)
        create_casos_card_optimized(casos, filters, colors)

    with col_tarjetas2:
        create_epizootias_card_optimized(epizootias, filters, colors)
        create_afectacion_card_simplified(
            casos, epizootias, filters, colors, data_filtered
        )


def create_map_system_simplified(
    casos, epizootias, geo_data, filters, colors, data_filtered
):
    """Sistema de mapas SIMPLIFICADO - CORREGIDO con validación de filtros."""
    # Validar y corregir filtros antes de procesar
    filters_validated = validate_and_fix_filters_for_maps(filters)

    current_level = determine_map_level(filters_validated)
    modo_mapa = filters_validated.get("modo_mapa", "Epidemiológico")

    logger.info(f"🗺️ Nivel del mapa determinado: {current_level} | Modo: {modo_mapa}")

    if current_level == "departamento":
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


def create_vereda_map_simplified(
    casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
):
    """Mapa específico para vereda seleccionada - NUEVO."""
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

    # Agregar veredas vecinas para contexto (opcional)
    if len(veredas_contexto) > 0:
        add_veredas_context_to_map(
            m, veredas_contexto.head(20), colors, modo_mapa
        )  # Máximo 20 para no saturar

    # Mostrar mapa
    map_data = st_folium(
        m,
        width="100%",
        height=600,
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
    st.markdown(f"### 📊 Información Detallada: {vereda_selected}")

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

    # Métricas en columnas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🦠 Casos", len(casos_vereda))

    with col2:
        fallecidos = (
            len(casos_vereda[casos_vereda["condicion_final"] == "Fallecido"])
            if not casos_vereda.empty and "condicion_final" in casos_vereda.columns
            else 0
        )
        st.metric("⚰️ Fallecidos", fallecidos)

    with col3:
        st.metric("🐒 Epizootias", len(epi_vereda))

    with col4:
        positivas = (
            len(epi_vereda[epi_vereda["descripcion"] == "POSITIVO FA"])
            if not epi_vereda.empty and "descripcion" in epi_vereda.columns
            else 0
        )
        st.metric("🔴 Positivas", positivas)

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
                        ["fecha_recoleccion", "descripcion", "proveniente"]
                    ].copy()
                    if all(
                        col in epi_vereda.columns
                        for col in ["fecha_recoleccion", "descripcion", "proveniente"]
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
    """Mapa departamental SIMPLIFICADO."""
    municipios = geo_data["municipios"].copy()
    logger.info(
        f"🏛️ Mapa departamental simplificado {modo_mapa}: {len(municipios)} municipios"
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
        height=600,
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
    """Mapa para selección múltiple - NUEVO."""
    municipios_seleccionados = filters.get("municipios_seleccionados", [])
    veredas_seleccionadas = filters.get("veredas_seleccionadas", [])

    logger.info(
        f"🗂️ Filtrado múltiple: {len(municipios_seleccionados)} municipios, {len(veredas_seleccionadas)} veredas"
    )

    if not municipios_seleccionados:
        st.warning("⚠️ No hay municipios seleccionados en el filtrado múltiple")
        return

    # Mostrar información de selección
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

    # Si solo municipios seleccionados, mostrar mapa de municipios
    if municipios_seleccionados and not veredas_seleccionadas:
        create_multiple_municipios_map(
            casos,
            epizootias,
            geo_data,
            municipios_seleccionados,
            filters,
            colors,
            modo_mapa,
        )

    # Si hay veredas seleccionadas, mostrar mapa de veredas
    elif veredas_seleccionadas:
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
        height=600,
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


def create_multiple_veredas_map(
    casos,
    epizootias,
    geo_data,
    municipios_seleccionados,
    veredas_seleccionadas,
    filters,
    colors,
    modo_mapa,
):
    """Mapa para múltiples veredas seleccionadas."""
    st.markdown("##### 🏘️ Mapa de Veredas Seleccionadas")

    veredas_gdf = geo_data["veredas"].copy()

    # Recopilar veredas de todos los municipios seleccionados
    todas_las_veredas = pd.DataFrame()

    for municipio in municipios_seleccionados:
        veredas_municipio = find_veredas_for_municipio_simplified(
            veredas_gdf, municipio
        )
        if not veredas_municipio.empty:
            todas_las_veredas = pd.concat(
                [todas_las_veredas, veredas_municipio], ignore_index=True
            )

    if todas_las_veredas.empty:
        st.warning(
            f"⚠️ No se encontraron veredas para los municipios: {', '.join(municipios_seleccionados)}"
        )
        return

    # Filtrar solo las veredas seleccionadas
    veredas_filtradas = filter_veredas_by_selected_names(
        todas_las_veredas, veredas_seleccionadas
    )

    if veredas_filtradas.empty:
        st.warning(f"⚠️ No se encontraron las veredas seleccionadas en los shapefiles")
        show_veredas_mapping_info(veredas_seleccionadas, todas_las_veredas)
        return

    # Preparar datos de veredas
    if modo_mapa == "Epidemiológico":
        veredas_data = prepare_multiple_veredas_epidemiological(
            casos, epizootias, veredas_filtradas, municipios_seleccionados, colors
        )
    else:
        veredas_data = prepare_multiple_veredas_coverage(veredas_filtradas, colors)

    # Crear mapa
    m = create_folium_map(veredas_data, zoom_start=9)
    add_veredas_to_map_simplified(m, veredas_data, colors, modo_mapa)

    map_data = st_folium(
        m,
        width="100%",
        height=600,
        returned_objects=["last_object_clicked"],
        key=f"map_multiple_ver_{modo_mapa.lower()}",
    )


def prepare_multiple_veredas_coverage(veredas_filtradas, colors):
    """Prepara datos de cobertura para múltiples veredas."""
    # Usar la función existente como base
    return prepare_vereda_data_coverage_simplified(
        veredas_filtradas, "MULTIPLE", colors
    )


def create_municipal_map_simplified(
    casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
):
    """Mapa municipal CORREGIDO - con manejo robusto de errores."""
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
                height=600,
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

    except Exception as e:
        logger.error(f"❌ Error general en create_municipal_map_simplified: {str(e)}")
        st.error(f"Error en mapa municipal: {str(e)}")


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


def debug_show_function_inputs(data_filtered, filters, colors):
    """Debug para la función show principal."""
    logger.info("🔍 === DEBUG SHOW FUNCTION ===")

    # Debug data_filtered
    logger.info("DATA_FILTERED:")
    if isinstance(data_filtered, dict):
        for key, value in data_filtered.items():
            if isinstance(value, pd.DataFrame):
                logger.info(f"  - {key}: DataFrame({value.shape})")
            else:
                logger.info(f"  - {key}: {type(value)}")
    else:
        logger.info(f"  - Tipo: {type(data_filtered)}")

    # Debug filters
    logger.info("FILTERS:")
    if isinstance(filters, dict):
        for key, value in filters.items():
            logger.info(f"  - {key}: {value} ({type(value)})")
    else:
        logger.info(f"  - Tipo: {type(filters)}")

    # Debug colors
    logger.info(f"COLORS: {type(colors)}")

    logger.info("🔍 === FIN DEBUG SHOW ===")


# ===== PREPARACIÓN DE DATOS SIMPLIFICADA =====


def prepare_municipal_data_epidemiological_simplified(
    casos, epizootias, municipios, colors
):
    """Prepara datos municipales CORREGIDO - evita error de arrays."""
    municipios = municipios.copy()
    color_scheme = get_color_scheme_epidemiological(colors)

    contadores_municipios = {}

    # Obtener nombres de municipios del shapefile - CORREGIDO
    municipio_col = get_municipio_column(municipios)

    if not municipio_col:
        logger.error("❌ No se encontró columna de municipios en shapefile")
        return municipios

    # Obtener lista de municipios únicos de manera segura - CORREGIDO
    try:
        municipios_unicos = municipios[municipio_col].dropna().unique()
        municipios_unicos = [str(m).strip() for m in municipios_unicos if pd.notna(m)]
        logger.info(f"📍 Procesando {len(municipios_unicos)} municipios únicos")
    except Exception as e:
        logger.error(f"❌ Error obteniendo municipios únicos: {str(e)}")
        return municipios

    # Procesar casos - CORREGIDO
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

    # Procesar epizootias - CORREGIDO
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

    # Aplicar colores - CORREGIDO
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
    """Valida y corrige filtros para mapas."""
    try:
        # Verificar modo de filtrado
        modo = filters.get("modo", "unico")

        if modo == "multiple":
            municipios_sel = filters.get("municipios_seleccionados", [])
            veredas_sel = filters.get("veredas_seleccionadas", [])

            # Asegurar que son listas
            if not isinstance(municipios_sel, list):
                municipios_sel = []
            if not isinstance(veredas_sel, list):
                veredas_sel = []

            logger.info(
                f"🔧 Modo múltiple validado: {len(municipios_sel)} municipios, {len(veredas_sel)} veredas"
            )

            return {
                **filters,
                "municipios_seleccionados": municipios_sel,
                "veredas_seleccionadas": veredas_sel,
                "municipio_display": (
                    f"{len(municipios_sel)} municipios" if municipios_sel else "Todos"
                ),
                "vereda_display": (
                    f"{len(veredas_sel)} veredas" if veredas_sel else "Todas"
                ),
            }
        else:
            # Modo único - validar valores
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
    """Prepara datos de veredas CORREGIDO - maneja epizootias vacías."""
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

    # Obtener lista de veredas únicas de manera segura
    try:
        veredas_unicas = veredas_gdf[vereda_col].dropna().unique()
        veredas_unicas = [str(v).strip() for v in veredas_unicas if pd.notna(v)]
        logger.info(
            f"🏘️ Procesando {len(veredas_unicas)} veredas únicas para {municipio_selected}"
        )
    except Exception as e:
        logger.error(f"❌ Error obteniendo veredas únicas: {str(e)}")
        return veredas_gdf

    # Procesar casos por vereda - CORREGIDO
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

    # Procesar epizootias por vereda - CORREGIDO CON VERIFICACIONES ADICIONALES
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

    # Aplicar colores - CORREGIDO
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


def prepare_municipal_data_coverage_simplified(municipios, filters, colors):
    """Preparación de cobertura SIMPLIFICADA."""
    municipios_data = municipios.copy()
    color_scheme = get_color_scheme_coverage(colors)

    # Cobertura base simulada
    import random

    random.seed(42)

    municipio_col = get_municipio_column(municipios)

    for idx, row in municipios_data.iterrows():
        municipio_name = row.get(municipio_col, "DESCONOCIDO")
        cobertura_base = random.uniform(75, 95)

        color, descripcion = determine_feature_color_coverage(
            cobertura_base, color_scheme
        )

        municipios_data.loc[idx, "color"] = color
        municipios_data.loc[idx, "descripcion_color"] = descripcion
        municipios_data.loc[idx, "cobertura"] = cobertura_base

    return municipios_data


def prepare_vereda_data_coverage_simplified(veredas_gdf, municipio_selected, colors):
    """Prepara datos de veredas para modo cobertura SIMPLIFICADO."""
    veredas_data = veredas_gdf.copy()
    color_scheme = get_color_scheme_coverage(colors)

    import random

    random.seed(42)

    for idx, row in veredas_data.iterrows():
        cobertura_base = random.uniform(70, 95)

        color, descripcion = determine_feature_color_coverage(
            cobertura_base, color_scheme
        )

        veredas_data.loc[idx, "color"] = color
        veredas_data.loc[idx, "descripcion_color"] = descripcion
        veredas_data.loc[idx, "cobertura"] = cobertura_base

    return veredas_data


def determine_feature_color_coverage(cobertura_porcentaje, color_scheme):
    """Determina color según cobertura de vacunación."""
    if pd.isna(cobertura_porcentaje):
        return color_scheme["sin_datos"], "Sin datos de cobertura"

    if cobertura_porcentaje > 95:
        return (
            color_scheme["cobertura_alta"],
            f"Cobertura alta: {cobertura_porcentaje:.1f}%",
        )
    elif cobertura_porcentaje >= 80:
        return (
            color_scheme["cobertura_buena"],
            f"Cobertura buena: {cobertura_porcentaje:.1f}%",
        )
    elif cobertura_porcentaje >= 60:
        return (
            color_scheme["cobertura_regular"],
            f"Cobertura regular: {cobertura_porcentaje:.1f}%",
        )
    else:
        return (
            color_scheme["cobertura_baja"],
            f"Cobertura baja: {cobertura_porcentaje:.1f}%",
        )


# ===== FUNCIONES DE APOYO =====


def get_municipio_column(gdf):
    """Detecta la columna de municipios en el shapefile - CORREGIDO."""
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
    """Obtiene nombre de feature de manera segura - NUEVO."""
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
    """Muestra municipios disponibles en shapefile para debug - MEJORADO."""
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


def handle_map_click_simplified(
    map_data, features_data, feature_type, filters, data_original
):
    """Manejo de clics - CORREGIDO."""
    if not map_data or not map_data.get("last_object_clicked"):
        return

    try:
        clicked_object = map_data["last_object_clicked"]

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
                    logger.info(
                        f"🎯 Click en shapefile: '{shapefile_name}' (corregido)"
                    )

                    # Mapear a nombre de base de datos - CORREGIDO
                    data_name = map_shapefile_to_data_simplified(
                        shapefile_name, data_original, feature_type
                    )

                    if not data_name:
                        logger.error(
                            f"❌ No se pudo mapear '{shapefile_name}' a base de datos"
                        )
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
    """Encuentra feature más cercano - CORREGIDO."""
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

        # Buscar dentro de geometrías primero - CORREGIDO
        for idx, row in features_data.iterrows():
            try:
                feature_name = safe_get_feature_name(row, col_name)
                if not feature_name:
                    continue

                geometry = row.get("geometry")
                if geometry is None:
                    continue

                # Verificar si está dentro - CORREGIDO
                if hasattr(geometry, "contains") and geometry.contains(click_point):
                    logger.info(f"✅ Clic dentro de {feature_name}")
                    return feature_name

            except Exception as e:
                logger.warning(f"⚠️ Error verificando geometría en fila {idx}: {str(e)}")
                continue

        # Si no está dentro de ninguno, buscar el más cercano - CORREGIDO
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

                # Calcular distancia - CORREGIDO
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
        # Fallback sin shapely - CORREGIDO
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
    """Mapea nombre de shapefile a nombre de base de datos - CORREGIDO con mapeo bidireccional."""
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


# ===== TARJETAS SIMPLIFICADAS =====


def create_afectacion_card_simplified(
    casos, epizootias, filters, colors, data_original
):
    """Tarjeta de afectación SIMPLIFICADA - CON CONTEO CORRECTO."""
    filter_context = get_filter_context_compact(filters)

    # Calcular afectación CORREGIDA
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
    """Calcula información de afectación SIMPLIFICADA CON CONTEO CORRECTO."""

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
        # Vista municipal - CORREGIDO: Contar veredas reales
        municipio_actual = filters.get("municipio_display")

        veredas_con_casos = set()
        veredas_con_epizootias = set()

        if not casos.empty and "vereda" in casos.columns:
            veredas_con_casos = set(casos["vereda"].dropna())

        if not epizootias.empty and "vereda" in epizootias.columns:
            veredas_con_epizootias = set(epizootias["vereda"].dropna())

        veredas_con_ambos = veredas_con_casos.intersection(veredas_con_epizootias)
        veredas_afectadas = veredas_con_casos.union(veredas_con_epizootias)

        # CORREGIDO: Contar veredas totales del municipio desde hoja VEREDAS
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

        # CORREGIDO: Total real de municipios del Tolima
        total_municipios_real = 47  # Tolima tiene 47 municipios

        return {
            "total": f"{len(municipios_afectados)}/{total_municipios_real}",
            "casos_texto": f"{len(municipios_con_casos)}/{total_municipios_real} con casos",
            "epizootias_texto": f"{len(municipios_con_epizootias)}/{total_municipios_real} con epizootias",
            "ambos_texto": f"{len(municipios_con_ambos)}/{total_municipios_real} con ambos",
            "descripcion": "municipios afectados del Tolima",
        }


def get_total_veredas_municipio_simplified(municipio, data_original):
    """Obtiene total REAL de veredas desde hoja VEREDAS SIMPLIFICADO."""
    veredas_por_municipio = data_original.get("veredas_por_municipio", {})

    # ===== DEBUG TEMPORAL =====
    logger.info(f"🔍 DEBUG VERIFICACIÓN PARA: {municipio}")
    logger.info(f"📊 data_original keys: {list(data_original.keys())}")

    veredas_por_municipio = data_original.get("veredas_por_municipio", {})
    logger.info(f"📊 veredas_por_municipio tipo: {type(veredas_por_municipio)}")
    logger.info(f"📊 veredas_por_municipio len: {len(veredas_por_municipio)}")
    logger.info(
        f"📊 veredas_por_municipio keys: {list(veredas_por_municipio.keys())[:5]}"
    )

    data_source = data_original.get("data_source", "unknown")
    logger.info(f"📊 data_source: {data_source}")

    if hasattr(st, "write"):
        st.write(f"**DEBUG {municipio}:**")
        st.write(f"- Data source: `{data_source}`")
        st.write(f"- Veredas_por_municipio length: `{len(veredas_por_municipio)}`")
        st.write(
            f"- Municipality keys (first 5): `{list(veredas_por_municipio.keys())[:5]}`"
        )
        st.write(
            f"- Target municipality in keys: `{municipio in veredas_por_municipio}`"
        )
    # ===== FIN DEBUG =====

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
    """Tarjeta de cobertura SIMPLIFICADA."""
    filter_context = get_filter_context_compact(filters)

    # Cobertura simulada
    cobertura_simulada = 82.3
    dosis_aplicadas = 45650
    gap_cobertura = 95.0 - cobertura_simulada
    ultima_actualizacion = datetime.now().strftime("%d/%m/%Y")

    st.markdown(
        f"""
        <div class="tarjeta-optimizada cobertura-card">
            <div class="tarjeta-header">
                <div class="tarjeta-icon">💉</div>
                <div class="tarjeta-info">
                    <div class="tarjeta-titulo">COBERTURA</div>
                    <div class="tarjeta-subtitulo">{filter_context}</div>
                </div>
                <div class="tarjeta-valor">{cobertura_simulada:.1f}%</div>
            </div>
            <div class="tarjeta-contenido">
                <div class="cobertura-barra">
                    <div class="cobertura-progreso" style="width: {cobertura_simulada}%"></div>
                </div>
                <div class="tarjeta-metricas">
                    <div class="metrica-item warning">
                        <div class="metrica-valor">{dosis_aplicadas:,}</div>
                        <div class="metrica-etiqueta">Dosis</div>
                    </div>
                    <div class="metrica-item danger">
                        <div class="metrica-valor">{gap_cobertura:.1f}%</div>
                        <div class="metrica-etiqueta">GAP</div>
                    </div>
                </div>
                <div class="tarjeta-footer">
                    📅 {ultima_actualizacion}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===== FUNCIONES EXISTENTES MANTENIDAS =====


def load_geographic_data():
    """Carga datos geográficos."""
    if not SHAPEFILE_LOADER_AVAILABLE:
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
    elif (
        filters.get("municipio_display") and filters.get("municipio_display") != "Todos"
    ):
        return "municipio"
    else:
        return "departamento"


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
    """Tarjeta de casos optimizada."""
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
            f"{ultimo_caso['ubicacion'][:20]}... • {ultimo_caso['tiempo_transcurrido']}"
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
                    📍 {ultimo_caso_info}
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
        ultima_epi_info = f"{ultima_epizootia['ubicacion'][:20]}... • {ultima_epizootia['tiempo_transcurrido']}"

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
                    🔴 {ultima_epi_info}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_folium_map(geo_data, zoom_start=8):
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
    """Agrega veredas al mapa SIMPLIFICADO."""
    vereda_col = get_vereda_column(veredas_data)

    for idx, row in veredas_data.iterrows():
        vereda_name = row.get(vereda_col, "DESCONOCIDA")
        color = row["color"]

        tooltip_text = create_vereda_tooltip_simplified(
            vereda_name, row, colors, modo_mapa
        )

        try:
            folium.GeoJson(
                row["geometry"],
                style_function=lambda x, color=color: {
                    "fillColor": color,
                    "color": colors["accent"],
                    "weight": 1.5,
                    "fillOpacity": 0.6,
                    "opacity": 0.8,
                },
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
            ).add_to(folium_map)
        except Exception as e:
            logger.warning(f"⚠️ Error agregando vereda {vereda_name}: {str(e)}")


def create_municipio_tooltip_simplified(name, row, colors, modo_mapa):
    """Tooltip para municipio SIMPLIFICADO."""
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


def create_vereda_tooltip_simplified(name, row, colors, modo_mapa):
    """Tooltip para vereda SIMPLIFICADO."""
    if modo_mapa == "Epidemiológico":
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
    else:
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
    """CSS optimizado para layout 50-25-25 y tarjetas mejoradas."""
    st.markdown(
        f"""
        <style>
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
        
        iframe[title="st_folium.st_folium"] {{
            width: 100% !important;
            height: 600px !important;
            border-radius: 12px !important;
            border: 2px solid #e2e8f0 !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
        }}
        
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
        
        .cobertura-card {{ border-left: 5px solid {colors['success']}; }}
        .casos-card {{ border-left: 5px solid {colors['danger']}; }}
        .epizootias-card {{ border-left: 5px solid {colors['warning']}; }}
        .afectacion-card {{ border-left: 5px solid {colors['primary']}; }}
        
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
        
        @media (max-width: 1200px) {{
            iframe[title="st_folium.st_folium"] {{
                height: 500px !important;
            }}
            
            .tarjeta-valor {{
                font-size: 1.6rem;
            }}
            
            .metrica-valor {{
                font-size: 1.1rem;
            }}
        }}
        
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
            
            iframe[title="st_folium.st_folium"] {{
                height: 400px !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
