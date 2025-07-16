"""
Componente de filtros.
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta

from utils.name_normalizer import (
    normalize_name_robust,
    normalize_name_with_accents,
    normalize_name_for_display,
    match_name_fuzzy,
    validate_municipio_name,
    get_canonical_municipio_name,
    find_equivalent_names,
    debug_name_matching,
)

logger = logging.getLogger(__name__)


def apply_filters_css(colors):
    """CSS para filtros múltiples."""
    st.markdown(
        f"""
        <style>
        .filter-section {{
            background: white;
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            border-left: 4px solid {colors['primary']};
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .multiselect-section {{
            background: linear-gradient(135deg, {colors['light']}, #ffffff);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            border: 2px solid {colors['secondary']};
        }}
        
        .grupo-btn {{
            background: linear-gradient(135deg, {colors['info']}, {colors['primary']});
            color: white;
            border: none;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            margin: 0.2rem;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .grupo-btn:hover {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
            transform: translateY(-1px);
        }}
        
        .contadores-afectacion {{
            background: linear-gradient(135deg, {colors['warning']}, {colors['secondary']});
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            text-align: center;
        }}
        
        .contador-item {{
            display: inline-block;
            margin: 0.3rem 0.5rem;
            font-weight: 600;
        }}
        
        .active-filters {{
            background: {colors['primary']};
            color: white;
            padding: 0.75rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
            .filter-section {{ padding: 0.8rem; }}
            .multiselect-section {{ padding: 0.8rem; }}
            .grupo-btn {{ 
                display: block; 
                width: 100%; 
                margin: 0.3rem 0; 
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def extract_regiones_from_veredas_data_authoritative(data):
    """
    Extrae regiones desde hoja VEREDAS AUTORITATIVA con normalización robusta.
    """
    regiones = {}

    # Intentar obtener desde veredas_completas (hoja VEREDAS)
    if "veredas_completas" in data and not data["veredas_completas"].empty:
        veredas_df = data["veredas_completas"]

        if "region" in veredas_df.columns and "municipi_1" in veredas_df.columns:
            logger.info(
                "🗂️ Cargando regiones desde hoja VEREDAS AUTORITATIVA con normalización"
            )

            for region in veredas_df["region"].dropna().unique():
                municipios_region = (
                    veredas_df[veredas_df["region"] == region]["municipi_1"]
                    .dropna()
                    .unique()
                )

                # Normalizar nombres de municipios para display
                municipios_normalizados = []
                for municipio in municipios_region:
                    canonical = get_canonical_municipio_name(municipio)
                    municipios_normalizados.append(canonical or municipio)

                regiones[region] = sorted(list(set(municipios_normalizados)))

            logger.info(
                f"✅ Regiones cargadas con normalización: {list(regiones.keys())}"
            )
            return regiones

    # Si hay regiones en data directamente
    if "regiones" in data and data["regiones"]:
        logger.info("🗂️ Usando regiones desde data procesada")
        return data["regiones"]

    # Fallback: regiones predefinidas con normalización
    logger.warning(
        "⚠️ No se pudieron cargar regiones desde hoja VEREDAS, usando fallback normalizado"
    )

    return create_regiones_fallback_normalized(data)


def debug_filter_issue(municipio_input, vereda_input, data):
    """
    Función específica para debugging problemas de filtrado.
    """
    logger.info(
        f"🔍 DEBUGGING FILTRO: municipio='{municipio_input}', vereda='{vereda_input}'"
    )

    # Debug municipio
    if municipio_input and municipio_input != "Todos":
        logger.info(f"🔍 Analizando municipio: '{municipio_input}'")

        # Verificar si es válido
        is_valid = validate_municipio_name(municipio_input)
        canonical = get_canonical_municipio_name(municipio_input)

        logger.info(f"  ✅ Válido: {is_valid}")
        logger.info(f"  📝 Canónico: {canonical}")

        # Verificar veredas disponibles
        veredas_disponibles = get_veredas_for_municipio_authoritative(
            data, municipio_input
        )
        logger.info(f"  🏘️ Veredas disponibles: {len(veredas_disponibles)}")

        if veredas_disponibles:
            logger.info(f"    Primeras 5: {veredas_disponibles[:5]}")

        # Debug vereda si se proporciona
        if vereda_input and vereda_input != "Todas":
            logger.info(
                f"🔍 Analizando vereda: '{vereda_input}' en municipio '{municipio_input}'"
            )

            vereda_match = match_name_fuzzy(vereda_input, veredas_disponibles)
            logger.info(f"  ✅ Coincidencia vereda: {vereda_match}")

            if not vereda_match:
                # Mostrar debug detallado
                for vereda_disponible in veredas_disponibles[:3]:  # Solo las primeras 3
                    debug_info = debug_name_matching(vereda_input, vereda_disponible)
                    logger.info(
                        f"  🔍 Debug vs '{vereda_disponible}': {debug_info['match_fuzzy']}"
                    )

    return {
        "municipio_analysis": {
            "valid": (
                validate_municipio_name(municipio_input) if municipio_input else True
            ),
            "canonical": (
                get_canonical_municipio_name(municipio_input)
                if municipio_input
                else None
            ),
            "veredas_count": (
                len(get_veredas_for_municipio_authoritative(data, municipio_input))
                if municipio_input
                else 0
            ),
        },
        "vereda_analysis": {
            "found": (
                match_name_fuzzy(
                    vereda_input,
                    get_veredas_for_municipio_authoritative(data, municipio_input),
                )
                if vereda_input and municipio_input
                else None
            )
        },
    }


def create_regiones_fallback_normalized(data):
    """
    Crea regiones fallback usando normalización robusta.
    """
    municipios_disponibles = data.get(
        "municipios_authoritativos", data.get("municipios_normalizados", [])
    )

    # Mapeo básico de regiones con nombres canónicos
    regiones_fallback = {
        "Norte": [
            "Falán",
            "Fresno",
            "Herveo",
            "Lérida",
            "Líbano",
            "Murillo",
            "Palocabildo",
            "Santa Isabel",
            "Villahermosa",
        ],
        "Centro": [
            "Alvarado",
            "Ibagué",
            "Cajamarca",
            "Coello",
            "Espinal",
            "Flandes",
            "Guamo",
            "Piedras",
            "Rovira",
            "Valle de San Juan",
        ],
        "Sur": [
            "Alpujarra",
            "Ataco",
            "Chaparral",
            "Coyaima",
            "Dolores",
            "Natagaima",
            "Ortega",
            "Planadas",
            "Rioblanco",
            "Roncesvalles",
            "San Antonio",
        ],
        "Oriente": [
            "Cunday",
            "Icononzo",
            "Melgar",
            "Carmen de Apicalá",
            "Venadillo",
            "Casabianca",
        ],
        "Magdalena": ["Ambalema", "Armero", "Honda", "Mariquita", "Saldaña"],
        "Suárez": ["Suárez", "Purificación", "Prado", "San Luis", "Villarrica"],
    }

    # Filtrar usando normalización robusta
    regiones_filtradas = {}
    for region, municipios in regiones_fallback.items():
        municipios_existentes = []
        for municipio in municipios:
            # Buscar coincidencia usando normalización robusta
            match = match_name_fuzzy(municipio, municipios_disponibles)
            if match:
                municipios_existentes.append(match)

        if municipios_existentes:
            regiones_filtradas[region] = sorted(list(set(municipios_existentes)))

    logger.info(
        f"📊 Regiones fallback creadas con normalización: {len(regiones_filtradas)} regiones"
    )

    return regiones_filtradas


def create_regiones_fallback(data):
    """Crea regiones fallback usando municipios disponibles."""
    municipios_disponibles = data.get(
        "municipios_authoritativos", data.get("municipios_normalizados", [])
    )

    # Mapeo básico de regiones (ajustar según nombres exactos en hoja VEREDAS)
    regiones_fallback = {
        "Norte": [
            "Falan",
            "Fresno",
            "Herveo",
            "Lerida",
            "Libano",
            "Murillo",
            "Palocabildo",
            "Santa Isabel",
            "Villahermosa",
        ],
        "Centro": [
            "Alvarado",
            "Ibague",
            "Cajamarca",
            "Coello",
            "Espinal",
            "Flandes",
            "Guamo",
            "Piedras",
            "Rovira",
            "Valle de San Juan",
        ],
        "Sur": [
            "Alpujarra",
            "Ataco",
            "Chaparral",
            "Coyaima",
            "Dolores",
            "Natagaima",
            "Ortega",
            "Planadas",
            "Rioblanco",
            "Roncesvalles",
            "San Antonio",
        ],
        "Oriente": [
            "Cunday",
            "Icononzo",
            "Melgar",
            "Carmen de Apicala",
            "Venadillo",
            "Casabianca",
        ],
        "Magdalena": ["Ambalema", "Armero", "Honda", "Mariquita", "Saldaña"],
        "Suarez": ["Suarez", "Purificacion", "Prado", "San Luis", "Villarrica"],
    }

    # Filtrar solo municipios que existen en los datos
    regiones_filtradas = {}
    for region, municipios in regiones_fallback.items():
        municipios_existentes = [m for m in municipios if m in municipios_disponibles]
        if municipios_existentes:
            regiones_filtradas[region] = municipios_existentes

    return regiones_filtradas


def create_hierarchical_filters_with_multiselect_authoritative(data):
    """
    Filtros jerárquicos usando hoja VEREDAS como fuente AUTORITATIVA con normalización robusta.
    """

    # Selector de modo de filtrado
    st.sidebar.markdown("### 🎯 Modo de Filtrado")

    # Mostrar información sobre fuente de datos
    if data.get("data_source") == "hoja_veredas_autoritativa_normalized":
        st.sidebar.markdown(
            "✅ **Fuente:** Hoja VEREDAS (Normalizada)",
            help="Datos tomados de la hoja VEREDAS con normalización robusta para tildes",
        )
    else:
        st.sidebar.markdown(
            "⚠️ **Fuente:** Fallback",
            help="Hoja VEREDAS no disponible, usando datos alternativos",
        )

    filtro_modo = st.sidebar.radio(
        "Seleccione el tipo de filtrado:",
        ["Único", "Múltiple"],
        index=0,
        key="filtro_modo",
        help="Único: un municipio/vereda. Múltiple: varios a la vez. Normalización robusta activa para ambos.",
    )

    if filtro_modo == "Único":
        return create_single_filters_authoritative_normalized(data)
    else:
        return create_multiple_filters_corrected_authoritative_normalized(data)


def create_multiple_filters_corrected_authoritative_normalized(data):
    """
    Filtros múltiples usando hoja VEREDAS como fuente AUTORITATIVA con normalización robusta.
    """

    st.sidebar.markdown('<div class="multiselect-section">', unsafe_allow_html=True)
    st.sidebar.markdown("#### 🗂️ Selección Múltiple (Normalizada)")

    if "municipios_authoritativos" in data and data["municipios_authoritativos"]:
        logger.info("✅ Usando municipios authoritativos de hoja VEREDAS (normalizado)")
        municipios_options = data["municipios_authoritativos"]
    else:
        logger.warning("⚠️ Usando municipios_normalizados como fallback")
        municipios_options = data["municipios_normalizados"]

    # USAR HOJA VEREDAS para regiones con normalización
    regiones_tolima = extract_regiones_from_veredas_data_authoritative(data)

    # Mostrar grupos predefinidos de municipios
    st.sidebar.markdown("**Grupos por Región (Normalizada):**")

    # Crear botones para cada región
    cols = st.sidebar.columns(2)
    region_names = list(regiones_tolima.keys())

    for i, region in enumerate(region_names):
        col_idx = i % 2
        with cols[col_idx]:
            if st.button(
                f"{region} ({len(regiones_tolima[region])})",
                key=f"btn_region_{region.lower().replace(' ', '_')}",
                use_container_width=True,
                help=f"Seleccionar todos los municipios de {region} (normalización robusta activa)",
            ):
                # Inicializar si no existe
                if "municipios_multiselect" not in st.session_state:
                    st.session_state.municipios_multiselect = []

                # Agregar municipios de la región sin sobrescribir
                current_selection = list(st.session_state.municipios_multiselect)
                for municipio in regiones_tolima[region]:
                    if municipio not in current_selection:
                        current_selection.append(municipio)

                # Actualizar session_state ANTES del widget
                st.session_state.municipios_multiselect = current_selection
                st.rerun()

    # Validar valores por defecto usando normalización robusta
    raw_default_municipios = st.session_state.get("municipios_multiselect", [])
    default_municipios = []

    for municipio in raw_default_municipios:
        match = match_name_fuzzy(municipio, municipios_options)
        if match:
            default_municipios.append(match)

    # Si hubo valores inválidos, limpiar el session_state y reportar
    if len(default_municipios) != len(raw_default_municipios):
        invalid_values = [
            m
            for m in raw_default_municipios
            if not match_name_fuzzy(m, municipios_options)
        ]
        st.session_state.municipios_multiselect = default_municipios
        logger.warning(
            f"🔧 Valores inválidos removidos con normalización: {invalid_values}"
        )
        logger.info(f"✅ Valores válidos mantenidos: {default_municipios}")

    # Selector múltiple de municipios
    municipios_selected = st.sidebar.multiselect(
        "📍 MUNICIPIOS:",
        municipios_options,
        default=default_municipios,
        key="municipios_multiselect_widget",
        help="Seleccione uno o más municipios (normalización robusta para tildes activa)",
    )

    # Sincronizar con session_state
    st.session_state["municipios_multiselect"] = municipios_selected

    # Si hay municipios seleccionados, mostrar selector de veredas
    veredas_selected = []
    if municipios_selected:
        # USAR HOJA VEREDAS para obtener veredas con normalización robusta
        todas_las_veredas = get_veredas_for_municipios_authoritative(
            municipios_selected, data
        )

        if todas_las_veredas:
            # Validar valores por defecto para veredas también
            veredas_options = sorted(set(todas_las_veredas))
            raw_default_veredas = st.session_state.get("veredas_multiselect", [])
            default_veredas = []

            for vereda in raw_default_veredas:
                match = match_name_fuzzy(vereda, veredas_options)
                if match:
                    default_veredas.append(match)

            # Si hubo valores inválidos, limpiar el session_state
            if len(default_veredas) != len(raw_default_veredas):
                invalid_veredas = [
                    v
                    for v in raw_default_veredas
                    if not match_name_fuzzy(v, veredas_options)
                ]
                st.session_state.veredas_multiselect = default_veredas
                logger.warning(
                    f"🔧 Veredas inválidas removidas con normalización: {invalid_veredas}"
                )
                logger.info(f"✅ Veredas válidas mantenidas: {default_veredas}")

            veredas_selected = st.sidebar.multiselect(
                "🏘️ VEREDAS:",
                veredas_options,
                default=default_veredas,
                key="veredas_multiselect_widget",
                help="Veredas de los municipios seleccionados (normalización robusta activa)",
            )

            # Sincronizar con session_state
            st.session_state["veredas_multiselect"] = veredas_selected

    # Botón para limpiar selección
    if municipios_selected or veredas_selected:
        if st.sidebar.button("🗑️ Limpiar Selección", use_container_width=True):
            st.session_state.municipios_multiselect = []
            st.session_state.veredas_multiselect = []
            st.rerun()

    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    return {
        "modo": "multiple",
        "municipio_display": (
            f"{len(municipios_selected)} municipios" if municipios_selected else "Todos"
        ),
        "municipio_normalizado": "Multiple",
        "vereda_display": (
            f"{len(veredas_selected)} veredas" if veredas_selected else "Todas"
        ),
        "vereda_normalizada": "Multiple",
        "municipios_seleccionados": municipios_selected,
        "veredas_seleccionadas": veredas_selected,
        "regiones_disponibles": regiones_tolima,
        "normalization": "robust",
    }


def create_single_filters_authoritative_normalized(data):
    """
    Filtros únicos usando hoja VEREDAS como fuente AUTORITATIVA con normalización robusta.
    """

    # USAR HOJA VEREDAS para opciones de municipios
    if "municipios_authoritativos" in data and data["municipios_authoritativos"]:
        logger.info(
            "✅ Usando municipios authoritativos de hoja VEREDAS para filtro único (normalizado)"
        )
        municipio_options = ["Todos"] + data["municipios_authoritativos"]
    else:
        logger.warning(
            "⚠️ Hoja VEREDAS no disponible para filtro único, usando fallback"
        )
        municipio_options = ["Todos"] + data.get("municipios_normalizados", [])

    # Filtro de municipio
    municipio_selected = st.sidebar.selectbox(
        "📍 MUNICIPIO:",
        municipio_options,
        index=get_initial_index(municipio_options, "municipio_filter"),
        key="municipio_filter_widget",
        help="Seleccione un municipio (normalización robusta para tildes activa)",
    )
    st.session_state["municipio_filter"] = municipio_selected

    # Filtro de vereda (dinámico según municipio)
    vereda_options = ["Todas"]
    vereda_disabled = municipio_selected == "Todos"

    if not vereda_disabled:
        # USAR HOJA VEREDAS para obtener veredas del municipio con normalización robusta
        veredas = get_veredas_for_municipio_authoritative(data, municipio_selected)
        if veredas:
            vereda_options.extend(sorted(veredas))
        else:
            # Debug si no se encuentran veredas
            logger.warning(
                f"🔍 No se encontraron veredas para '{municipio_selected}' - iniciando debug"
            )
            debug_info = debug_filter_issue(municipio_selected, None, data)
            logger.warning(f"🔍 Debug resultado: {debug_info}")

    vereda_selected = st.sidebar.selectbox(
        "🏘️ VEREDA:",
        vereda_options,
        index=get_initial_index(vereda_options, "vereda_filter"),
        key="vereda_filter_widget",
        disabled=vereda_disabled,
        help="Las veredas se actualizan según el municipio (normalización robusta activa)",
    )

    if not vereda_disabled:
        st.session_state["vereda_filter"] = vereda_selected
    else:
        st.session_state["vereda_filter"] = "Todas"
        vereda_selected = "Todas"

    return {
        "modo": "unico",
        "municipio_display": municipio_selected,
        "municipio_normalizado": municipio_selected,
        "vereda_display": vereda_selected,
        "vereda_normalizada": vereda_selected,
        "municipios_seleccionados": (
            [municipio_selected] if municipio_selected != "Todos" else []
        ),
        "veredas_seleccionadas": (
            [vereda_selected] if vereda_selected != "Todas" else []
        ),
        "normalization": "robust",
    }


def create_single_filters_authoritative(data):
    """Filtros únicos usando hoja VEREDAS como fuente AUTORITATIVA."""

    # USAR HOJA VEREDAS para opciones de municipios
    if "municipios_authoritativos" in data and data["municipios_authoritativos"]:
        logger.info(
            "✅ Usando municipios authoritativos de hoja VEREDAS para filtro único"
        )
        municipio_options = ["Todos"] + data["municipios_authoritativos"]
    else:
        logger.warning(
            "⚠️ Hoja VEREDAS no disponible para filtro único, usando fallback"
        )
        municipio_options = ["Todos"] + data.get("municipios_normalizados", [])

    # Filtro de municipio
    municipio_selected = st.sidebar.selectbox(
        "📍 MUNICIPIO:",
        municipio_options,
        index=get_initial_index(municipio_options, "municipio_filter"),
        key="municipio_filter_widget",
        help="Seleccione un municipio (fuente: hoja VEREDAS)",
    )
    st.session_state["municipio_filter"] = municipio_selected

    # Filtro de vereda (dinámico según municipio)
    vereda_options = ["Todas"]
    vereda_disabled = municipio_selected == "Todos"

    if not vereda_disabled:
        # USAR HOJA VEREDAS para obtener veredas del municipio
        veredas = get_veredas_for_municipio_authoritative(data, municipio_selected)
        vereda_options.extend(sorted(veredas))

    vereda_selected = st.sidebar.selectbox(
        "🏘️ VEREDA:",
        vereda_options,
        index=get_initial_index(vereda_options, "vereda_filter"),
        key="vereda_filter_widget",
        disabled=vereda_disabled,
        help="Las veredas se actualizan según el municipio (fuente: hoja VEREDAS)",
    )

    if not vereda_disabled:
        st.session_state["vereda_filter"] = vereda_selected
    else:
        st.session_state["vereda_filter"] = "Todas"
        vereda_selected = "Todas"

    return {
        "modo": "unico",
        "municipio_display": municipio_selected,
        "municipio_normalizado": municipio_selected,
        "vereda_display": vereda_selected,
        "vereda_normalizada": vereda_selected,
        "municipios_seleccionados": (
            [municipio_selected] if municipio_selected != "Todos" else []
        ),
        "veredas_seleccionadas": (
            [vereda_selected] if vereda_selected != "Todas" else []
        ),
    }


def create_multiple_filters_corrected_authoritative(data):
    """Filtros múltiples usando hoja VEREDAS como fuente AUTORITATIVA."""

    st.sidebar.markdown('<div class="multiselect-section">', unsafe_allow_html=True)
    st.sidebar.markdown("#### 🗂️ Selección Múltiple")

    if "municipios_authoritativos" in data and data["municipios_authoritativos"]:
        logger.info("✅ Usando municipios authoritativos de hoja VEREDAS")
        municipios_options = data["municipios_authoritativos"]
    else:
        logger.warning("⚠️ Usando municipios_normalizados como fallback")
        municipios_options = data["municipios_normalizados"]

    # USAR HOJA VEREDAS para regiones
    regiones_tolima = extract_regiones_from_veredas_data_authoritative(data)

    # Mostrar grupos predefinidos de municipios
    st.sidebar.markdown("**Grupos por Región:**")

    # Crear botones para cada región
    cols = st.sidebar.columns(2)
    region_names = list(regiones_tolima.keys())

    for i, region in enumerate(region_names):
        col_idx = i % 2
        with cols[col_idx]:
            if st.button(
                f"{region} ({len(regiones_tolima[region])})",
                key=f"btn_region_{region.lower().replace(' ', '_')}",
                use_container_width=True,
                help=f"Seleccionar todos los municipios de {region}",
            ):
                # Inicializar si no existe
                if "municipios_multiselect" not in st.session_state:
                    st.session_state.municipios_multiselect = []

                # Agregar municipios de la región sin sobrescribir
                current_selection = list(st.session_state.municipios_multiselect)
                for municipio in regiones_tolima[region]:
                    if municipio not in current_selection:
                        current_selection.append(municipio)

                # Actualizar session_state ANTES del widget
                st.session_state.municipios_multiselect = current_selection
                st.rerun()

    # USAR HOJA VEREDAS como fuente autoritativa para opciones
    if "municipios_authoritativos" in data and data["municipios_authoritativos"]:
        logger.info("✅ Usando municipios authoritativos de hoja VEREDAS")
        municipios_options = data.get(
            "municipios_authoritativos", data["municipios_normalizados"]
        )
    else:
        logger.warning("⚠️ Hoja VEREDAS no disponible, usando fallback")
        municipios_options = data.get("municipios_normalizados", [])

    # Validar valores por defecto para asegurar que estén en opciones AUTORITATIVAS
    raw_default_municipios = st.session_state.get("municipios_multiselect", [])
    default_municipios = [m for m in raw_default_municipios if m in municipios_options]

    # Si hubo valores inválidos, limpiar el session_state y reportar
    if len(default_municipios) != len(raw_default_municipios):
        invalid_values = [
            m for m in raw_default_municipios if m not in municipios_options
        ]
        st.session_state.municipios_multiselect = default_municipios
        logger.warning(f"🔧 Valores inválidos removidos: {invalid_values}")
        logger.info(f"✅ Valores válidos mantenidos: {default_municipios}")

    # Selector múltiple de municipios
    municipios_selected = st.sidebar.multiselect(
        "📍 MUNICIPIOS:",
        municipios_options,
        default=default_municipios,
        key="municipios_multiselect_widget",
        help="Seleccione uno o más municipios (fuente: hoja VEREDAS)",
    )

    # Sincronizar con session_state
    st.session_state["municipios_multiselect"] = municipios_selected

    # Si hay municipios seleccionados, mostrar selector de veredas
    veredas_selected = []
    if municipios_selected:
        # USAR HOJA VEREDAS para obtener veredas
        todas_las_veredas = get_veredas_for_municipios_authoritative(
            municipios_selected, data
        )

        if todas_las_veredas:
            # Validar valores por defecto para veredas también
            veredas_options = sorted(set(todas_las_veredas))
            raw_default_veredas = st.session_state.get("veredas_multiselect", [])
            default_veredas = [v for v in raw_default_veredas if v in veredas_options]

            # Si hubo valores inválidos, limpiar el session_state
            if len(default_veredas) != len(raw_default_veredas):
                invalid_veredas = [
                    v for v in raw_default_veredas if v not in veredas_options
                ]
                st.session_state.veredas_multiselect = default_veredas
                logger.warning(f"🔧 Veredas inválidas removidas: {invalid_veredas}")
                logger.info(f"✅ Veredas válidas mantenidas: {default_veredas}")

            veredas_selected = st.sidebar.multiselect(
                "🏘️ VEREDAS:",
                veredas_options,
                default=default_veredas,
                key="veredas_multiselect_widget",
                help="Veredas de los municipios seleccionados (fuente: hoja VEREDAS)",
            )

            # Sincronizar con session_state
            st.session_state["veredas_multiselect"] = veredas_selected

    # Botón para limpiar selección
    if municipios_selected or veredas_selected:
        if st.sidebar.button("🗑️ Limpiar Selección", use_container_width=True):
            st.session_state.municipios_multiselect = []
            st.session_state.veredas_multiselect = []
            st.rerun()

    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    return {
        "modo": "multiple",
        "municipio_display": (
            f"{len(municipios_selected)} municipios" if municipios_selected else "Todos"
        ),
        "municipio_normalizado": "Multiple",
        "vereda_display": (
            f"{len(veredas_selected)} veredas" if veredas_selected else "Todas"
        ),
        "vereda_normalizada": "Multiple",
        "municipios_seleccionados": municipios_selected,
        "veredas_seleccionadas": veredas_selected,
        "regiones_disponibles": regiones_tolima,
    }


def get_veredas_for_municipios_authoritative(municipios_selected, data):
    """Obtiene veredas para múltiples municipios usando hoja VEREDAS AUTORITATIVA."""
    todas_las_veredas = []

    for municipio in municipios_selected:
        veredas_municipio = get_veredas_for_municipio_authoritative(data, municipio)
        todas_las_veredas.extend(veredas_municipio)

    return todas_las_veredas


def create_map_mode_selector(colors):
    """Selector de modo del mapa: epidemiológico vs cobertura."""
    st.sidebar.markdown("### 🗺️ Modo de Visualización")

    modo_mapa = st.sidebar.radio(
        "Colorear mapa según:",
        ["Epidemiológico", "Cobertura de Vacunación"],
        index=0,
        key="modo_mapa",
        help="Epidemiológico: casos y epizootias. Cobertura: porcentaje de vacunación.",
    )

    # Información del modo seleccionado
    if modo_mapa == "Epidemiológico":
        st.sidebar.markdown(
            f"""
            <div style="background: {colors['info']}; color: white; padding: 0.5rem; border-radius: 6px; font-size: 0.8rem;">
                🔴 Rojo: Casos + Epizootias + Fallecidos<br>
                🟠 Naranja: Solo casos<br>
                🟡 Amarillo: Solo epizootias<br>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            f"""
            <div style="background: {colors['success']}; color: white; padding: 0.5rem; border-radius: 6px; font-size: 0.8rem;">
                🟢 Verde intenso: >95% cobertura<br>
                🟡 Amarillo: 80-95% cobertura<br>
                🟠 Naranja: 60-80% cobertura<br>
                🔴 Rojo: &lt;60% cobertura<br>
                ⚪ Gris: Sin datos de cobertura
            </div>
            """,
            unsafe_allow_html=True,
        )

    return modo_mapa


def apply_all_filters_multiple(
    data, filters_location, filters_temporal, filters_advanced
):
    """
    Aplica filtros con soporte para selección múltiple y normalización robusta.
    """
    casos_filtrados = data["casos"].copy()
    epizootias_filtradas = data["epizootias"].copy()

    initial_casos = len(casos_filtrados)
    initial_epizootias = len(epizootias_filtradas)

    # Filtros de ubicación según modo
    if filters_location.get("modo") == "multiple":
        # Filtrado múltiple con normalización robusta
        municipios_seleccionados = filters_location.get("municipios_seleccionados", [])
        veredas_seleccionadas = filters_location.get("veredas_seleccionadas", [])

        if municipios_seleccionados:
            # Normalizar municipios seleccionados
            municipios_norm = [
                normalize_name_robust(m) for m in municipios_seleccionados
            ]

            if "municipio" in casos_filtrados.columns:
                casos_filtrados = casos_filtrados[
                    casos_filtrados["municipio"]
                    .apply(normalize_name_robust)
                    .isin(municipios_norm)
                ]

            if "municipio" in epizootias_filtradas.columns:
                epizootias_filtradas = epizootias_filtradas[
                    epizootias_filtradas["municipio"]
                    .apply(normalize_name_robust)
                    .isin(municipios_norm)
                ]

        if veredas_seleccionadas:
            # Normalizar veredas seleccionadas
            veredas_norm = [normalize_name_robust(v) for v in veredas_seleccionadas]

            if "vereda" in casos_filtrados.columns:
                casos_filtrados = casos_filtrados[
                    casos_filtrados["vereda"]
                    .apply(normalize_name_robust)
                    .isin(veredas_norm)
                ]

            if "vereda" in epizootias_filtradas.columns:
                epizootias_filtradas = epizootias_filtradas[
                    epizootias_filtradas["vereda"]
                    .apply(normalize_name_robust)
                    .isin(veredas_norm)
                ]

    else:
        # Filtrado único con normalización robusta
        if filters_location["municipio_display"] != "Todos":
            municipio_norm = normalize_name_robust(
                filters_location["municipio_display"]
            )

            if "municipio" in casos_filtrados.columns:
                casos_filtrados = casos_filtrados[
                    casos_filtrados["municipio"].apply(normalize_name_robust)
                    == municipio_norm
                ]

            if "municipio" in epizootias_filtradas.columns:
                epizootias_filtradas = epizootias_filtradas[
                    epizootias_filtradas["municipio"].apply(normalize_name_robust)
                    == municipio_norm
                ]

        if filters_location["vereda_display"] != "Todas":
            vereda_norm = normalize_name_robust(filters_location["vereda_display"])

            if "vereda" in casos_filtrados.columns:
                casos_filtrados = casos_filtrados[
                    casos_filtrados["vereda"].apply(normalize_name_robust)
                    == vereda_norm
                ]

            if "vereda" in epizootias_filtradas.columns:
                epizootias_filtradas = epizootias_filtradas[
                    epizootias_filtradas["vereda"].apply(normalize_name_robust)
                    == vereda_norm
                ]

    # Filtros temporales (sin cambios)
    if filters_temporal["fecha_rango"] and len(filters_temporal["fecha_rango"]) == 2:
        fecha_inicio = pd.Timestamp(filters_temporal["fecha_rango"][0])
        fecha_fin = pd.Timestamp(filters_temporal["fecha_rango"][1]) + pd.Timedelta(
            hours=23, minutes=59
        )

        if "fecha_inicio_sintomas" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                (casos_filtrados["fecha_inicio_sintomas"] >= fecha_inicio)
                & (casos_filtrados["fecha_inicio_sintomas"] <= fecha_fin)
            ]

        if "fecha_recoleccion" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                (epizootias_filtradas["fecha_recoleccion"] >= fecha_inicio)
                & (epizootias_filtradas["fecha_recoleccion"] <= fecha_fin)
            ]

    # Filtros avanzados (sin cambios)
    if (
        filters_advanced["condicion_final"] != "Todas"
        and "condicion_final" in casos_filtrados.columns
    ):
        casos_filtrados = casos_filtrados[
            casos_filtrados["condicion_final"] == filters_advanced["condicion_final"]
        ]

    if filters_advanced["sexo"] != "Todos" and "sexo" in casos_filtrados.columns:
        casos_filtrados = casos_filtrados[
            casos_filtrados["sexo"] == filters_advanced["sexo"]
        ]

    if filters_advanced["edad_rango"] and "edad" in casos_filtrados.columns:
        edad_min, edad_max = filters_advanced["edad_rango"]
        casos_filtrados = casos_filtrados[
            (casos_filtrados["edad"] >= edad_min)
            & (casos_filtrados["edad"] <= edad_max)
        ]

    # Log del resultado
    final_casos = len(casos_filtrados)
    final_epizootias = len(epizootias_filtradas)

    logger.info(
        f"Filtrado con normalización robusta - Casos: {initial_casos}→{final_casos}, Epizootias: {initial_epizootias}→{final_epizootias}"
    )

    return {
        "casos": casos_filtrados,
        "epizootias": epizootias_filtradas,
        **{k: v for k, v in data.items() if k not in ["casos", "epizootias"]},
    }


def create_unified_filter_system(data):
    """Sistema unificado de filtros OPTIMIZADO."""
    # Aplicar CSS
    try:
        from config.colors import COLORS

        apply_filters_css(COLORS)
    except ImportError:
        default_colors = {
            "primary": "#7D0F2B",
            "secondary": "#F2A900",
            "info": "#4682B4",
        }
        apply_filters_css(default_colors)
        COLORS = default_colors

    # Selector de modo de mapa
    modo_mapa = create_map_mode_selector(COLORS)

    # Crear filtros según tipo
    filters_location = create_hierarchical_filters_with_multiselect_authoritative(data)
    filters_temporal = create_temporal_filters_optimized(data)  # OPTIMIZADO
    filters_advanced = create_advanced_filters_optimized(data)  # OPTIMIZADO

    # Aplicar filtros
    data_filtered = apply_all_filters_multiple(
        data, filters_location, filters_temporal, filters_advanced
    )

    # Crear resumen de filtros activos OPTIMIZADO
    active_filters = create_filter_summary_multiple_optimized(
        filters_location, filters_temporal, filters_advanced
    )

    # Mostrar filtros activos
    show_active_filters(active_filters)

    # Botones de control
    st.sidebar.markdown("---")

    col1, col2 = st.sidebar.columns([3, 1])

    with col1:
        if st.button(
            "🔄 Restablecer Todo", key="reset_all_filters", use_container_width=True
        ):
            reset_all_filters()
            st.rerun()

    with col2:
        if active_filters:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #7D0F2B, #F2A900); 
                    color: white; 
                    padding: 0.4rem; 
                    border-radius: 50%; 
                    text-align: center; 
                    font-size: 0.8rem; 
                    font-weight: 700;
                    min-width: 30px;
                    min-height: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    {len(active_filters)}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Agregar copyright
    try:
        from components.sidebar import add_copyright

        add_copyright()
    except ImportError:
        pass

    # Combinar filtros
    all_filters = {
        **filters_location,
        **filters_temporal,
        **filters_advanced,
        "active_filters": active_filters,
        "modo_mapa": modo_mapa,
    }

    return {"filters": all_filters, "data_filtered": data_filtered}


def create_temporal_filters_optimized(data):
    """Filtros temporales OPTIMIZADOS - fecha actual como máximo."""
    st.sidebar.markdown("---")
    fechas_disponibles = get_available_dates(data)

    if not fechas_disponibles:
        return {"fecha_rango": None, "fecha_min": None, "fecha_max": None}

    fecha_min = min(fechas_disponibles)
    # OPTIMIZADO: Fecha máxima siempre es HOY
    fecha_max_datos = max(fechas_disponibles)
    fecha_max = datetime.now()  # CORREGIDO: Siempre usar fecha actual como máximo

    fecha_rango = st.sidebar.date_input(
        "📅 Rango de Fechas:",
        value=(fecha_min.date(), fecha_max_datos.date()),  # Default hasta último dato
        min_value=fecha_min.date(),
        max_value=fecha_max.date(),  # Máximo siempre hoy
        key="fecha_filter_widget",
        help="Seleccione el período temporal de interés. Máximo: fecha actual",
    )
    st.session_state["fecha_filter"] = fecha_rango

    if fecha_rango and len(fecha_rango) == 2:
        dias_seleccionados = (fecha_rango[1] - fecha_rango[0]).days
        st.sidebar.markdown(
            f'<div class="filter-help">📊 Período: {dias_seleccionados} días seleccionados</div>',
            unsafe_allow_html=True,
        )

    return {
        "fecha_rango": fecha_rango,
        "fecha_min": fecha_min,
        "fecha_max": fecha_max,  # Devolver fecha actual como máximo
        "fecha_max_datos": fecha_max_datos,  # Mantener referencia al último dato
    }


def create_advanced_filters_optimized(data):
    """Filtros avanzados OPTIMIZADOS - edad no cuenta como filtro aplicado."""
    with st.sidebar.expander("🔧 Filtros Avanzados", expanded=False):
        condicion_filter = "Todas"
        if not data["casos"].empty and "condicion_final" in data["casos"].columns:
            condiciones = ["Todas"] + list(
                data["casos"]["condicion_final"].dropna().unique()
            )
            condicion_filter = st.selectbox(
                "⚰️ Condición Final:", condiciones, key="condicion_filter"
            )

        sexo_filter = "Todos"
        if not data["casos"].empty and "sexo" in data["casos"].columns:
            sexos = ["Todos"] + list(data["casos"]["sexo"].dropna().unique())
            sexo_filter = st.selectbox("👤 Sexo:", sexos, key="sexo_filter")

        edad_rango = None
        edad_es_filtro_real = False  # OPTIMIZADO: Rastrear si edad es filtro real
        if not data["casos"].empty and "edad" in data["casos"].columns:
            edad_min = (
                int(data["casos"]["edad"].min())
                if not data["casos"]["edad"].isna().all()
                else 0
            )
            edad_max = (
                int(data["casos"]["edad"].max())
                if not data["casos"]["edad"].isna().all()
                else 100
            )

            if edad_min < edad_max:
                edad_rango = st.slider(
                    "🎂 Rango de Edad:",
                    min_value=edad_min,
                    max_value=edad_max,
                    value=(edad_min, edad_max),
                    key="edad_filter",
                )

                # OPTIMIZADO: Solo es filtro si NO es el rango completo
                edad_es_filtro_real = edad_rango != (edad_min, edad_max)

    return {
        "condicion_final": condicion_filter,
        "sexo": sexo_filter,
        "edad_rango": edad_rango,
        "edad_es_filtro_real": edad_es_filtro_real,  # NUEVO: Indica si edad es realmente un filtro
    }


def create_filter_summary_multiple_optimized(
    filters_location, filters_temporal, filters_advanced
):
    """Crea resumen de filtros activos OPTIMIZADO - sin mostrar edad y fecha por defecto."""
    active_filters = []

    # Filtros de ubicación
    if filters_location.get("modo") == "multiple":
        municipios_sel = filters_location.get("municipios_seleccionados", [])
        veredas_sel = filters_location.get("veredas_seleccionadas", [])

        if municipios_sel:
            if len(municipios_sel) == 1:
                active_filters.append(f"📍 {municipios_sel[0]}")
            else:
                active_filters.append(f"📍 {len(municipios_sel)} municipios")

        if veredas_sel:
            if len(veredas_sel) == 1:
                active_filters.append(f"🏘️ {veredas_sel[0]}")
            else:
                active_filters.append(f"🏘️ {len(veredas_sel)} veredas")
    else:
        # Modo único
        if filters_location["municipio_display"] != "Todos":
            active_filters.append(f"📍 {filters_location['municipio_display']}")

        if filters_location["vereda_display"] != "Todas":
            active_filters.append(f"🏘️ {filters_location['vereda_display']}")

    # OPTIMIZADO: Filtros temporales - solo si NO es el rango por defecto
    if (
        filters_temporal["fecha_rango"]
        and len(filters_temporal["fecha_rango"]) == 2
        and filters_temporal.get("fecha_min")
        and filters_temporal.get("fecha_max_datos")
    ):

        fecha_inicio, fecha_fin = filters_temporal["fecha_rango"]
        fecha_min_default = filters_temporal["fecha_min"].date()
        fecha_max_default = filters_temporal["fecha_max_datos"].date()

        # Solo agregar si NO es el rango completo por defecto
        if fecha_inicio != fecha_min_default or fecha_fin != fecha_max_default:
            active_filters.append(
                f"📅 {fecha_inicio.strftime('%m/%y')}-{fecha_fin.strftime('%m/%y')}"
            )

    # Filtros avanzados
    if filters_advanced["condicion_final"] != "Todas":
        active_filters.append(f"⚰️ {filters_advanced['condicion_final']}")

    if filters_advanced["sexo"] != "Todos":
        active_filters.append(f"👤 {filters_advanced['sexo']}")

    # OPTIMIZADO: Edad solo si es realmente un filtro (no el rango completo)
    if filters_advanced.get("edad_es_filtro_real", False):
        edad_min, edad_max = filters_advanced["edad_rango"]
        active_filters.append(f"🎂 {edad_min}-{edad_max}")

    return active_filters


# ===== FUNCIONES DE APOYO =====


def normalize_name(name):
    """
    Función de compatibilidad que usa el nuevo normalizador robusto.
    """
    return normalize_name_robust(name)


def get_initial_index(options, session_key):
    if session_key in st.session_state:
        current_value = st.session_state[session_key]
        if current_value in options:
            return options.index(current_value)
    return 0


def get_veredas_for_municipio_authoritative(data, municipio_selected):
    """
    Obtiene veredas para un municipio usando hoja VEREDAS AUTORITATIVA con normalización robusta.
    """
    logger.info(
        f"🏘️ Buscando veredas para: '{municipio_selected}' (normalización robusta)"
    )

    veredas_por_municipio = data.get("veredas_por_municipio", {})

    # Buscar coincidencia directa primero
    if municipio_selected in veredas_por_municipio:
        logger.info(
            f"✅ Coincidencia directa: {len(veredas_por_municipio[municipio_selected])} veredas"
        )
        return veredas_por_municipio[municipio_selected]

    # Buscar usando normalización robusta
    municipios_disponibles = list(veredas_por_municipio.keys())
    municipio_match = match_name_fuzzy(municipio_selected, municipios_disponibles)

    if municipio_match:
        logger.info(
            f"✅ Coincidencia con normalización: '{municipio_selected}' → '{municipio_match}'"
        )
        return veredas_por_municipio[municipio_match]

    # Debug adicional para casos problemáticos
    if municipio_selected.lower() in [
        "ibague",
        "ibagué",
        "purificacion",
        "purificación",
    ]:
        logger.warning(f"🔍 Caso problemático detectado: '{municipio_selected}'")

        # Mostrar debug detallado
        for municipio_disponible in municipios_disponibles:
            debug_info = debug_name_matching(municipio_selected, municipio_disponible)
            if debug_info["match_fuzzy"]:
                logger.info(f"🔍 Debug match encontrado: {debug_info}")
                return veredas_por_municipio[municipio_disponible]

    logger.warning(
        f"⚠️ No se encontraron veredas para '{municipio_selected}' en hoja VEREDAS"
    )
    logger.info(f"📋 Municipios disponibles: {municipios_disponibles}")

    return []


def get_veredas_for_municipios_authoritative(municipios_selected, data):
    """
    Obtiene veredas para múltiples municipios usando hoja VEREDAS AUTORITATIVA con normalización robusta.
    """
    logger.info(
        f"🏘️ Buscando veredas para {len(municipios_selected)} municipios (normalización robusta)"
    )

    todas_las_veredas = []

    for municipio in municipios_selected:
        veredas_municipio = get_veredas_for_municipio_authoritative(data, municipio)
        todas_las_veredas.extend(veredas_municipio)

        if veredas_municipio:
            logger.info(f"  ✅ {municipio}: {len(veredas_municipio)} veredas")
        else:
            logger.warning(f"  ⚠️ {municipio}: Sin veredas encontradas")

    logger.info(
        f"📊 Total: {len(todas_las_veredas)} veredas para {len(municipios_selected)} municipios"
    )

    return todas_las_veredas


def get_available_dates(data):
    fechas = []
    if not data["casos"].empty and "fecha_inicio_sintomas" in data["casos"].columns:
        fechas.extend(data["casos"]["fecha_inicio_sintomas"].dropna().tolist())
    if (
        not data["epizootias"].empty
        and "fecha_recoleccion" in data["epizootias"].columns
    ):
        fechas.extend(data["epizootias"]["fecha_recoleccion"].dropna().tolist())
    return fechas


def show_active_filters(active_filters):
    if not active_filters:
        return

    st.sidebar.markdown("---")

    filters_text = " • ".join(active_filters[:3])
    if len(active_filters) > 3:
        filters_text += f" • +{len(active_filters) - 3} más"

    st.sidebar.markdown(
        f"""
        <div class="active-filters">
            <strong>🎯 Filtros Activos ({len(active_filters)}):</strong><br>
            {filters_text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def reset_all_filters():
    filter_keys = [
        "municipio_filter",
        "vereda_filter",
        "fecha_filter",
        "condicion_filter",
        "sexo_filter",
        "edad_filter",
        "municipios_multiselect",
        "veredas_multiselect",
        "filtro_modo",
    ]

    reset_count = 0
    for key in filter_keys:
        if key in st.session_state:
            if (
                "municipio" in key
                or "condicion" in key
                or "sexo" in key
                or "filtro_modo" in key
            ):
                if key == "filtro_modo":
                    st.session_state[key] = "Único"
                else:
                    st.session_state[key] = "Todos"
            elif "vereda" in key:
                st.session_state[key] = "Todas"
            elif "multiselect" in key:
                st.session_state[key] = []
            else:
                del st.session_state[key]
            reset_count += 1

    if reset_count > 0:
        st.sidebar.success(f"✅ {reset_count} filtros restablecidos")
