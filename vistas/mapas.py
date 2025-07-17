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


def get_mapped_municipio(municipio_name: str) -> str:
    """Obtiene el nombre mapeado de un municipio."""
    if not municipio_name:
        return ""

    municipio_clean = str(municipio_name).strip()
    return MUNICIPIO_MAPPING.get(municipio_clean, municipio_clean)


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
    """Vista principal de mapas SIMPLIFICADA."""
    logger.info("🗺️ INICIANDO VISTA DE MAPAS SIMPLIFICADA")

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
    """Sistema de mapas SIMPLIFICADO - CORREGIDO para nivel vereda."""
    current_level = determine_map_level(filters)
    modo_mapa = filters.get("modo_mapa", "Epidemiológico")

    logger.info(f"🗺️ Nivel del mapa determinado: {current_level}")

    if current_level == "departamento":
        create_departmental_map_simplified(
            casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
        )
    elif current_level == "municipio":
        create_municipal_map_simplified(
            casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
        )
    elif current_level == "vereda":
        # NUEVO: Manejo específico para nivel vereda
        create_vereda_map_simplified(
            casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
        )
    else:
        logger.warning(f"⚠️ Nivel de mapa no reconocido: {current_level}")
        show_fallback_summary(
            casos, epizootias, current_level, filters.get("municipio_display")
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


def create_municipal_map_simplified(
    casos, epizootias, geo_data, filters, colors, modo_mapa, data_filtered
):
    """Mapa municipal SIMPLIFICADO."""
    municipio_selected = filters.get("municipio_display")
    if not municipio_selected or municipio_selected == "Todos":
        st.error("No se pudo determinar el municipio para la vista de veredas")
        return

    veredas = geo_data["veredas"].copy()

    # Buscar veredas del municipio con mapeo
    veredas_municipio = find_veredas_for_municipio_simplified(
        veredas, municipio_selected
    )

    if veredas_municipio.empty:
        st.warning(f"No se encontraron veredas para {municipio_selected}")
        show_available_municipios_in_shapefile(veredas, municipio_selected)
        return

    if modo_mapa == "Epidemiológico":
        veredas_data = prepare_vereda_data_epidemiological_simplified(
            casos, epizootias, veredas_municipio, municipio_selected, colors
        )
    else:
        veredas_data = prepare_vereda_data_coverage_simplified(
            veredas_municipio, municipio_selected, colors
        )

    m = create_folium_map(veredas_data, zoom_start=10)
    add_veredas_to_map_simplified(m, veredas_data, colors, modo_mapa)

    map_data = st_folium(
        m,
        width="100%",
        height=600,
        returned_objects=["last_object_clicked"],
        key=f"map_mun_simple_{modo_mapa.lower()}",
    )

    # Manejo de clics simplificado
    handle_map_click_simplified(
        map_data, veredas_data, "vereda", filters, data_filtered
    )


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
    """Encuentra casos para municipio del shapefile - CORREGIDO."""
    if casos.empty or "municipio" not in casos.columns:
        return pd.DataFrame()

    try:
        shapefile_municipio = str(shapefile_municipio).strip()

        # Buscar coincidencia directa - CORREGIDO
        mask_directa = casos["municipio"].astype(str).str.strip() == shapefile_municipio
        casos_directos = casos[mask_directa]

        if not casos_directos.empty:
            return casos_directos

        # Buscar usando mapeo - CORREGIDO
        mapped_municipio = get_mapped_municipio(shapefile_municipio)
        if mapped_municipio != shapefile_municipio:
            mask_mapeada = (
                casos["municipio"].astype(str).str.strip() == mapped_municipio
            )
            casos_mapeados = casos[mask_mapeada]
            return casos_mapeados

        return pd.DataFrame()

    except Exception as e:
        logger.warning(f"⚠️ Error buscando casos para {shapefile_municipio}: {str(e)}")
        return pd.DataFrame()


def find_epizootias_for_shapefile_municipio(epizootias, shapefile_municipio):
    """Encuentra epizootias para municipio del shapefile - CORREGIDO."""
    if epizootias.empty or "municipio" not in epizootias.columns:
        return pd.DataFrame()

    try:
        shapefile_municipio = str(shapefile_municipio).strip()

        # Buscar coincidencia directa - CORREGIDO
        mask_directa = (
            epizootias["municipio"].astype(str).str.strip() == shapefile_municipio
        )
        epi_directos = epizootias[mask_directa]

        if not epi_directos.empty:
            return epi_directos

        # Buscar usando mapeo - CORREGIDO
        mapped_municipio = get_mapped_municipio(shapefile_municipio)
        if mapped_municipio != shapefile_municipio:
            mask_mapeada = (
                epizootias["municipio"].astype(str).str.strip() == mapped_municipio
            )
            epi_mapeados = epizootias[mask_mapeada]
            return epi_mapeados

        return pd.DataFrame()

    except Exception as e:
        logger.warning(
            f"⚠️ Error buscando epizootias para {shapefile_municipio}: {str(e)}"
        )
        return pd.DataFrame()


def find_veredas_for_municipio_simplified(veredas_gdf, municipio_selected):
    """Encuentra veredas para municipio - CORREGIDO."""
    if veredas_gdf.empty:
        logger.error("❌ GeoDataFrame de veredas vacío")
        return pd.DataFrame()

    municipio_col = get_municipio_column(veredas_gdf)

    if not municipio_col:
        logger.error("❌ No se encontró columna de municipios en veredas shapefile")
        return pd.DataFrame()

    try:
        municipio_selected = str(municipio_selected).strip()

        # Buscar veredas por coincidencia directa - CORREGIDO
        mask_directa = (
            veredas_gdf[municipio_col].astype(str).str.strip() == municipio_selected
        )
        veredas_directas = veredas_gdf[mask_directa]

        if not veredas_directas.empty:
            logger.info(
                f"✅ Encontradas {len(veredas_directas)} veredas para {municipio_selected} (directo)"
            )
            return veredas_directas

        # Buscar usando mapeo inverso - CORREGIDO
        reverse_mapping = {v: k for k, v in MUNICIPIO_MAPPING.items()}
        shapefile_municipio = reverse_mapping.get(
            municipio_selected, municipio_selected
        )

        if shapefile_municipio != municipio_selected:
            mask_mapeada = (
                veredas_gdf[municipio_col].astype(str).str.strip()
                == shapefile_municipio
            )
            veredas_mapeadas = veredas_gdf[mask_mapeada]

            if not veredas_mapeadas.empty:
                logger.info(
                    f"✅ Encontradas {len(veredas_mapeadas)} veredas para {municipio_selected} (mapeado como {shapefile_municipio})"
                )
                return veredas_mapeadas

        logger.warning(f"⚠️ No se encontraron veredas para {municipio_selected}")
        return pd.DataFrame()

    except Exception as e:
        logger.error(f"❌ Error buscando veredas para {municipio_selected}: {str(e)}")
        return pd.DataFrame()


def prepare_vereda_data_epidemiological_simplified(
    casos, epizootias, veredas_gdf, municipio_selected, colors
):
    """Prepara datos de veredas SIMPLIFICADOS."""
    veredas_gdf = veredas_gdf.copy()
    color_scheme = get_color_scheme_epidemiological(colors)

    vereda_col = get_vereda_column(veredas_gdf)
    contadores_veredas = {}

    if not vereda_col:
        logger.error("❌ No se encontró columna de veredas en shapefile")
        return veredas_gdf

    # Procesar casos por vereda
    if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
        casos_municipio = casos[casos["municipio"] == municipio_selected]

        for vereda_shapefile in veredas_gdf[vereda_col].unique():
            casos_ver = casos_municipio[casos_municipio["vereda"] == vereda_shapefile]
            fallecidos_ver = (
                casos_ver[casos_ver["condicion_final"] == "Fallecido"]
                if "condicion_final" in casos_ver.columns
                else pd.DataFrame()
            )

            contadores_veredas[vereda_shapefile] = {
                "casos": len(casos_ver),
                "fallecidos": len(fallecidos_ver),
            }

    # Procesar epizootias por vereda
    if (
        not epizootias.empty
        and "vereda" in epizootias.columns
        and "municipio" in epizootias.columns
    ):
        epi_municipio = epizootias[epizootias["municipio"] == municipio_selected]

        for vereda_shapefile in veredas_gdf[vereda_col].unique():
            if vereda_shapefile not in contadores_veredas:
                contadores_veredas[vereda_shapefile] = {"casos": 0, "fallecidos": 0}

            epi_ver = epi_municipio[epi_municipio["vereda"] == vereda_shapefile]
            positivas_ver = (
                epi_ver[epi_ver["descripcion"] == "POSITIVO FA"]
                if "descripcion" in epi_ver.columns
                else pd.DataFrame()
            )
            en_estudio_ver = (
                epi_ver[epi_ver["descripcion"] == "EN ESTUDIO"]
                if "descripcion" in epi_ver.columns
                else pd.DataFrame()
            )

            contadores_veredas[vereda_shapefile].update(
                {
                    "epizootias": len(epi_ver),
                    "positivas": len(positivas_ver),
                    "en_estudio": len(en_estudio_ver),
                }
            )

    # Aplicar colores
    veredas_data = veredas_gdf.copy()

    for idx, row in veredas_data.iterrows():
        vereda_shapefile = row[vereda_col]
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

        color, descripcion = determine_feature_color_epidemiological(
            contadores["casos"],
            contadores["epizootias"],
            contadores["fallecidos"],
            contadores["positivas"],
            contadores["en_estudio"],
            color_scheme,
        )

        veredas_data.loc[idx, "color"] = color
        veredas_data.loc[idx, "descripcion_color"] = descripcion

        for key, value in contadores.items():
            veredas_data.loc[idx, key] = value

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
    """Muestra municipios disponibles en shapefile para debug."""
    municipio_col = get_municipio_column(veredas_gdf)
    if municipio_col:
        municipios_disponibles = sorted(veredas_gdf[municipio_col].unique())
        logger.info(f"🏛️ Municipios disponibles en shapefile: {municipios_disponibles}")

        st.info(
            f"**Municipios disponibles en shapefile de veredas:**\n\n"
            f"{', '.join(municipios_disponibles[:10])}"
            f"{f' y {len(municipios_disponibles)-10} más...' if len(municipios_disponibles) > 10 else ''}\n\n"
            f"**Buscado:** {municipio_selected}\n\n"
            f"**Sugerencia:** Verificar mapeo en MUNICIPIO_MAPPING"
        )


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
    """Mapea nombre de shapefile a nombre de base de datos - CORREGIDO."""
    try:
        shapefile_name = str(shapefile_name).strip()

        if feature_type == "municipio":
            # Para municipios, usar mapeo directo - CORREGIDO
            mapped_name = get_mapped_municipio(shapefile_name)

            # Verificar que existe en datos - CORREGIDO
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

            if mapped_name in municipios_disponibles:
                return mapped_name

            # Si no se encuentra, buscar coincidencia directa
            if shapefile_name in municipios_disponibles:
                return shapefile_name

            logger.warning(
                f"⚠️ Municipio '{shapefile_name}' (→'{mapped_name}') no encontrado en datos"
            )
            return None

        elif feature_type == "vereda":
            # Para veredas, retornar el nombre directamente
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
