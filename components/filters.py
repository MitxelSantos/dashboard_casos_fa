"""
Componente de filtros SIMPLIFICADO - sin normalización compleja
Los nombres ya coinciden exactamente entre shapefiles y bases de datos
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ===== FUNCIONES DE COMPARACIÓN SIMPLIFICADAS =====


def simple_name_clean(name):
    """Limpieza MÍNIMA - solo espacios."""
    if not name:
        return ""
    return str(name).strip()


def names_match(name1, name2):
    """Comparación directa - sin normalización compleja."""
    return simple_name_clean(name1) == simple_name_clean(name2)


# ===== CSS PARA FILTROS =====


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


# ===== EXTRACCIÓN DE REGIONES SIMPLIFICADA =====


def extract_regiones_from_veredas_data_simple(data):
    """Extrae regiones desde hoja VEREDAS SIMPLIFICADO."""
    regiones = {}

    # Intentar obtener desde veredas_completas (hoja VEREDAS)
    if "veredas_completas" in data and not data["veredas_completas"].empty:
        veredas_df = data["veredas_completas"]

        if "region" in veredas_df.columns and "municipi_1" in veredas_df.columns:
            logger.info("🗂️ Cargando regiones desde hoja VEREDAS SIMPLIFICADO")

            for region in veredas_df["region"].dropna().unique():
                municipios_region = (
                    veredas_df[veredas_df["region"] == region]["municipi_1"]
                    .dropna()
                    .unique()
                )
                regiones[region] = sorted(list(set(municipios_region)))

            logger.info(f"✅ Regiones cargadas SIMPLIFICADO: {list(regiones.keys())}")
            return regiones

    # Si hay regiones en data directamente
    if "regiones" in data and data["regiones"]:
        logger.info("🗂️ Usando regiones desde data procesada")
        return data["regiones"]

    # Fallback: regiones predefinidas
    logger.warning(
        "⚠️ No se pudieron cargar regiones desde hoja VEREDAS, usando fallback"
    )
    return create_regiones_fallback_simple(data)


def create_regiones_fallback_simple(data):
    """Crea regiones fallback SIMPLIFICADO."""
    municipios_disponibles = data.get(
        "municipios_authoritativos", data.get("municipios_normalizados", [])
    )

    # Mapeo básico de regiones con nombres exactos
    regiones_fallback = {
        "Norte": [
            "FALAN",
            "FRESNO",
            "HERVEO",
            "LERIDA",
            "LIBANO",
            "MURILLO",
            "PALOCABILDO",
            "SANTA ISABEL",
            "VILLAHERMOSA",
        ],
        "Centro": [
            "ALVARADO",
            "IBAGUE",
            "CAJAMARCA",
            "COELLO",
            "ESPINAL",
            "FLANDES",
            "GUAMO",
            "PIEDRAS",
            "ROVIRA",
            "VALLE DE SAN JUAN",
        ],
        "Sur": [
            "ALPUJARRA",
            "ATACO",
            "CHAPARRAL",
            "COYAIMA",
            "DOLORES",
            "NATAGAIMA",
            "ORTEGA",
            "PLANADAS",
            "RIOBLANCO",
            "RONCESVALLES",
            "SAN ANTONIO",
        ],
        "Oriente": [
            "CUNDAY",
            "ICONONZO",
            "MELGAR",
            "CARMEN DE APICALA",
            "VENADILLO",
            "CASABIANCA",
        ],
        "Magdalena": ["AMBALEMA", "ARMERO", "HONDA", "MARIQUITA", "SALDANA"],
        "Suarez": ["SUAREZ", "PURIFICACION", "PRADO", "SAN LUIS", "VILLARRICA"],
    }

    # Filtrar solo municipios que existen en los datos
    regiones_filtradas = {}
    for region, municipios in regiones_fallback.items():
        municipios_existentes = [m for m in municipios if m in municipios_disponibles]
        if municipios_existentes:
            regiones_filtradas[region] = municipios_existentes

    return regiones_filtradas


# ===== FILTROS JERÁRQUICOS SIMPLIFICADOS =====


def create_hierarchical_filters_with_multiselect_authoritative(data):
    """Filtros jerárquicos SIMPLIFICADO."""
    # Selector de modo de filtrado
    st.sidebar.markdown("### 🎯 Modo de Filtrado")

    filtro_modo = st.sidebar.radio(
        "Seleccione el tipo de filtrado:",
        ["Único", "Múltiple"],
        index=0,
        key="filtro_modo",
        help="Único: un municipio/vereda. Múltiple: varios a la vez.",
    )

    if filtro_modo == "Único":
        return create_single_filters_simple(data)
    else:
        return create_multiple_filters_simple(data)


def create_single_filters_simple(data):
    """Filtros únicos SIMPLIFICADO - CORREGIDO con manejo de reset."""
    # Usar hoja VEREDAS para opciones de municipios
    if "municipios_authoritativos" in data and data["municipios_authoritativos"]:
        logger.info("✅ Usando municipios authoritativos de hoja VEREDAS para filtro único")
        municipio_options = ["Todos"] + data["municipios_authoritativos"]
    else:
        logger.warning("⚠️ Hoja VEREDAS no disponible para filtro único, usando fallback")
        municipio_options = ["Todos"] + data.get("municipios_normalizados", [])

    # CORREGIDO: Obtener valor por defecto con manejo de reset
    municipio_default = get_default_filter_value("municipio_filter", "selectbox")
    if municipio_default is None:
        municipio_default = st.session_state.get("municipio_filter", "Todos")
    
    # Validar que el valor por defecto esté en las opciones
    if municipio_default not in municipio_options:
        municipio_default = "Todos"

    # Filtro de municipio
    municipio_selected = st.sidebar.selectbox(
        "📍 MUNICIPIO:",
        municipio_options,
        index=municipio_options.index(municipio_default),
        key="municipio_filter_widget",
        help="Seleccione un municipio (fuente: hoja VEREDAS)",
    )
    st.session_state["municipio_filter"] = municipio_selected

    # Filtro de vereda (dinámico según municipio)
    vereda_options = ["Todas"]
    vereda_disabled = municipio_selected == "Todos"

    if not vereda_disabled:
        # Usar hoja VEREDAS para obtener veredas del municipio
        veredas = get_veredas_for_municipio_simple(data, municipio_selected)
        if veredas:
            vereda_options.extend(sorted(veredas))
        else:
            logger.warning(f"🔍 No se encontraron veredas para '{municipio_selected}'")

    # CORREGIDO: Obtener valor por defecto para vereda
    vereda_default = get_default_filter_value("vereda_filter", "selectbox")
    if vereda_default is None:
        vereda_default = st.session_state.get("vereda_filter", "Todas")
    
    # Validar que el valor por defecto esté en las opciones
    if vereda_default not in vereda_options:
        vereda_default = "Todas"

    vereda_selected = st.sidebar.selectbox(
        "🏘️ VEREDA:",
        vereda_options,
        index=vereda_options.index(vereda_default),
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

def create_multiple_filters_simple(data):
    """Filtros múltiples."""

    if "municipios_authoritativos" in data and data["municipios_authoritativos"]:
        logger.info("✅ Usando municipios authoritativos de hoja VEREDAS")
        municipios_options = data["municipios_authoritativos"]
    else:
        logger.warning("⚠️ Usando municipios_normalizados como fallback")
        municipios_options = data["municipios_normalizados"]

    # Usar hoja VEREDAS para regiones
    regiones_tolima = extract_regiones_from_veredas_data_simple(data)

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

                # Actualizar session_state del widget
                st.session_state.municipios_multiselect = current_selection
                st.rerun()

    # Validar valores por defecto - comparación directa
    raw_default_municipios = st.session_state.get("municipios_multiselect", [])
    default_municipios = [m for m in raw_default_municipios if m in municipios_options]

    # Si hubo valores inválidos, limpiar el session_state
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
        # Usar hoja VEREDAS para obtener veredas
        todas_las_veredas = get_veredas_for_municipios_simple(municipios_selected, data)

        if todas_las_veredas:
            # Validar valores por defecto para veredas - comparación directa
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


def get_veredas_for_municipio_simple(data, municipio_selected):
    """Obtiene veredas para un municipio SIMPLIFICADO."""
    logger.info(f"🏘️ Buscando veredas para: '{municipio_selected}' (SIMPLIFICADO)")

    veredas_por_municipio = data.get("veredas_por_municipio", {})

    # Buscar coincidencia directa
    if municipio_selected in veredas_por_municipio:
        logger.info(
            f"✅ Coincidencia directa: {len(veredas_por_municipio[municipio_selected])} veredas"
        )
        return veredas_por_municipio[municipio_selected]

    logger.warning(
        f"⚠️ No se encontraron veredas para '{municipio_selected}' en hoja VEREDAS"
    )
    return []


def get_veredas_for_municipios_simple(municipios_selected, data):
    """Obtiene veredas para múltiples municipios SIMPLIFICADO."""
    logger.info(
        f"🏘️ Buscando veredas para {len(municipios_selected)} municipios (SIMPLIFICADO)"
    )

    todas_las_veredas = []

    for municipio in municipios_selected:
        veredas_municipio = get_veredas_for_municipio_simple(data, municipio)
        todas_las_veredas.extend(veredas_municipio)

        if veredas_municipio:
            logger.info(f"  ✅ {municipio}: {len(veredas_municipio)} veredas")
        else:
            logger.warning(f"  ⚠️ {municipio}: Sin veredas encontradas")

    logger.info(
        f"📊 Total: {len(todas_las_veredas)} veredas para {len(municipios_selected)} municipios"
    )
    return todas_las_veredas


# ===== SELECTOR DE MODO DE MAPA =====

def create_map_mode_selector(colors):
    """Selector de modo del mapa: epidemiológico vs cobertura - CORREGIDO."""
    st.sidebar.markdown("### 🗺️ Modo de Visualización")

    # Obtener valor por defecto con manejo de reset
    modo_default = get_default_filter_value("modo_mapa", "radio")
    if modo_default is None:
        modo_default = st.session_state.get("modo_mapa", "Epidemiológico")
    
    modos_disponibles = ["Epidemiológico", "Cobertura de Vacunación"]
    if modo_default not in modos_disponibles:
        modo_default = "Epidemiológico"

    modo_mapa = st.sidebar.radio(
        "Colorear mapa según:",
        modos_disponibles,
        index=modos_disponibles.index(modo_default),
        key="modo_mapa_widget",
        help="Epidemiológico: casos y epizootias. Cobertura: porcentaje de vacunación.",
    )
    st.session_state["modo_mapa"] = modo_mapa

    # Información del modo seleccionado (resto del código igual...)
    if modo_mapa == "Epidemiológico":
        st.sidebar.markdown(
            f"""
            <div style="background: {colors['info']}; color: white; padding: 0.5rem; border-radius: 6px; font-size: 0.8rem;">
                🔴 Rojo: Casos + Epizootias<br>
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
                ⚪ Gris: Sin datos de población
            </div>
            """,
            unsafe_allow_html=True,
        )

    return modo_mapa

# ===== APLICACIÓN DE FILTROS =====

def apply_all_filters_multiple(
    data, filters_location, filters_temporal, filters_advanced
):
    """Aplica filtros SIMPLIFICADO - CON DEBUG para casos perdidos."""
    casos_filtrados = data["casos"].copy()
    epizootias_filtradas = data["epizootias"].copy()

    initial_casos = len(casos_filtrados)
    initial_epizootias = len(epizootias_filtradas)

    # ===== DEBUG: LOGGING INICIAL =====
    logger.info(f"🔄 INICIO FILTRADO: {initial_casos} casos, {initial_epizootias} epizootias")

    # Filtros de ubicación según modo (sin cambios)
    if filters_location.get("modo") == "multiple":
        # ... código de filtrado múltiple ...
        pass
    else:
        # Filtrado único
        if filters_location["municipio_display"] != "Todos":
            municipio_target = filters_location["municipio_display"]

            if "municipio" in casos_filtrados.columns:
                antes_municipio = len(casos_filtrados)
                casos_filtrados = casos_filtrados[
                    casos_filtrados["municipio"] == municipio_target
                ]
                despues_municipio = len(casos_filtrados)
                if antes_municipio != despues_municipio:
                    logger.info(f"📍 Filtro municipio: {antes_municipio}→{despues_municipio} casos")

            if "municipio" in epizootias_filtradas.columns:
                epizootias_filtradas = epizootias_filtradas[
                    epizootias_filtradas["municipio"] == municipio_target
                ]

        if filters_location["vereda_display"] != "Todas":
            vereda_target = filters_location["vereda_display"]

            if "vereda" in casos_filtrados.columns:
                antes_vereda = len(casos_filtrados)
                casos_filtrados = casos_filtrados[
                    casos_filtrados["vereda"] == vereda_target
                ]
                despues_vereda = len(casos_filtrados)
                if antes_vereda != despues_vereda:
                    logger.info(f"🏘️ Filtro vereda: {antes_vereda}→{despues_vereda} casos")

            if "vereda" in epizootias_filtradas.columns:
                epizootias_filtradas = epizootias_filtradas[
                    epizootias_filtradas["vereda"] == vereda_target
                ]

    # ===== FILTROS TEMPORALES CON DEBUG =====
    if filters_temporal["fecha_rango"] and len(filters_temporal["fecha_rango"]) == 2:
        fecha_inicio = pd.Timestamp(filters_temporal["fecha_rango"][0])
        fecha_fin = pd.Timestamp(filters_temporal["fecha_rango"][1]) + pd.Timedelta(
            hours=23, minutes=59
        )

        logger.info(f"📅 Aplicando filtro temporal: {fecha_inicio.date()} a {fecha_fin.date()}")

        # FILTRO TEMPORAL PARA CASOS CON DEBUG
        if "fecha_inicio_sintomas" in casos_filtrados.columns:
            antes_temporal_casos = len(casos_filtrados)
            
            # ✅ DEBUG: Verificar casos con fechas problemáticas
            casos_sin_fecha = casos_filtrados["fecha_inicio_sintomas"].isna().sum()
            if casos_sin_fecha > 0:
                logger.warning(f"⚠️ {casos_sin_fecha} casos SIN fecha_inicio_sintomas")
            
            # ✅ DEBUG: Verificar casos fuera del rango
            casos_antes_rango = (casos_filtrados["fecha_inicio_sintomas"] < fecha_inicio).sum()
            casos_despues_rango = (casos_filtrados["fecha_inicio_sintomas"] > fecha_fin).sum()
            
            if casos_antes_rango > 0:
                logger.warning(f"📅 {casos_antes_rango} casos ANTES del rango temporal")
            if casos_despues_rango > 0:
                logger.warning(f"📅 {casos_despues_rango} casos DESPUÉS del rango temporal")
            
            # Aplicar filtro temporal
            casos_filtrados = casos_filtrados[
                (casos_filtrados["fecha_inicio_sintomas"] >= fecha_inicio)
                & (casos_filtrados["fecha_inicio_sintomas"] <= fecha_fin)
            ]
            
            despues_temporal_casos = len(casos_filtrados)
            casos_perdidos = antes_temporal_casos - despues_temporal_casos
            
            if casos_perdidos > 0:
                logger.warning(f"🚨 FILTRO TEMPORAL eliminó {casos_perdidos} casos: {antes_temporal_casos}→{despues_temporal_casos}")
                
                # ✅ DEBUG: Mostrar fechas extremas de los casos restantes
                if not casos_filtrados.empty:
                    fecha_min_restante = casos_filtrados["fecha_inicio_sintomas"].min()
                    fecha_max_restante = casos_filtrados["fecha_inicio_sintomas"].max()
                    logger.info(f"📊 Casos restantes: fechas de {fecha_min_restante.date()} a {fecha_max_restante.date()}")

        # FILTRO TEMPORAL PARA EPIZOOTIAS (sin cambios)
        if "fecha_notificacion" in epizootias_filtradas.columns:
            antes_temporal_epi = len(epizootias_filtradas)
            
            epizootias_filtradas = epizootias_filtradas[
                (epizootias_filtradas["fecha_notificacion"] >= fecha_inicio)
                & (epizootias_filtradas["fecha_notificacion"] <= fecha_fin)
            ]
            
            despues_temporal_epi = len(epizootias_filtradas)
            if antes_temporal_epi != despues_temporal_epi:
                logger.info(f"📅 Filtro temporal epizootias: {antes_temporal_epi}→{despues_temporal_epi}")

    # ===== FILTROS AVANZADOS CON DEBUG =====
    if (
        filters_advanced["condicion_final"] != "Todas"
        and "condicion_final" in casos_filtrados.columns
    ):
        antes_condicion = len(casos_filtrados)
        casos_filtrados = casos_filtrados[
            casos_filtrados["condicion_final"] == filters_advanced["condicion_final"]
        ]
        despues_condicion = len(casos_filtrados)
        if antes_condicion != despues_condicion:
            logger.info(f"⚰️ Filtro condición: {antes_condicion}→{despues_condicion} casos")

    if filters_advanced["sexo"] != "Todos" and "sexo" in casos_filtrados.columns:
        antes_sexo = len(casos_filtrados)
        casos_filtrados = casos_filtrados[
            casos_filtrados["sexo"] == filters_advanced["sexo"]
        ]
        despues_sexo = len(casos_filtrados)
        if antes_sexo != despues_sexo:
            logger.info(f"👤 Filtro sexo: {antes_sexo}→{despues_sexo} casos")

    if filters_advanced["edad_rango"] and "edad" in casos_filtrados.columns:
        edad_min, edad_max = filters_advanced["edad_rango"]
        antes_edad = len(casos_filtrados)
        casos_filtrados = casos_filtrados[
            (casos_filtrados["edad"] >= edad_min)
            & (casos_filtrados["edad"] <= edad_max)
        ]
        despues_edad = len(casos_filtrados)
        if antes_edad != despues_edad:
            logger.info(f"🎂 Filtro edad: {antes_edad}→{despues_edad} casos")

    # ===== LOG FINAL =====
    final_casos = len(casos_filtrados)
    final_epizootias = len(epizootias_filtradas)

    logger.info(
        f"✅ FILTRADO FINAL - Casos: {initial_casos}→{final_casos}, Epizootias: {initial_epizootias}→{final_epizootias}"
    )

    return {
        "casos": casos_filtrados,
        "epizootias": epizootias_filtradas,
        **{k: v for k, v in data.items() if k not in ["casos", "epizootias"]},
    }

# ===== SISTEMA UNIFICADO DE FILTROS =====


def create_unified_filter_system(data):
    """Sistema unificado de filtros SIMPLIFICADO."""
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
    filters_temporal = create_temporal_filters_optimized(data)
    filters_advanced = create_advanced_filters_optimized(data)

    # Aplicar filtros
    data_filtered = apply_all_filters_multiple(
        data, filters_location, filters_temporal, filters_advanced
    )

    # Crear resumen de filtros activos
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


# ===== FILTROS TEMPORALES Y AVANZADOS =====

def create_temporal_filters_optimized(data):
    """Filtros temporales OPTIMIZADOS - CORREGIDO para incluir fechas nuevas."""
    st.sidebar.markdown("---")
    fechas_disponibles = get_available_dates(data)

    if not fechas_disponibles:
        return {"fecha_rango": None, "fecha_min": None, "fecha_max": None}

    fecha_min = min(fechas_disponibles)
    fecha_max_datos = max(fechas_disponibles)
    fecha_max = datetime.now()  # Siempre usar fecha actual como máximo

    # ✅ CORRECCIÓN: Extender el rango por defecto para incluir casos nuevos
    # Si hay casos con fechas muy recientes, incluirlos por defecto
    fecha_fin_default = max(fecha_max_datos.date(), fecha_max.date())
    
    # ✅ OPCIONAL: Agregar buffer de días para casos futuros
    from datetime import timedelta
    fecha_fin_default = fecha_fin_default + timedelta(days=7)  # Buffer de 7 días

    fecha_rango = st.sidebar.date_input(
        "📅 Rango de Fechas:",
        value=(fecha_min.date(), fecha_fin_default),  # ← CORREGIDO
        min_value=fecha_min.date(),
        max_value=fecha_max.date() + timedelta(days=30),  # Permitir fechas futuras
        key="fecha_filter_widget",
        help="Seleccione el período temporal de interés. Incluye buffer para casos nuevos.",
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
        "fecha_max": fecha_max,
        "fecha_max_datos": fecha_max_datos,
    }

def create_advanced_filters_optimized(data):
    """Filtros avanzados OPTIMIZADOS - CORREGIDO con manejo de reset."""
    with st.sidebar.expander("🔧 Filtros Avanzados", expanded=False):
        
        # CORRECCIÓN: Condición Final
        condicion_filter = "Todas"
        if not data["casos"].empty and "condicion_final" in data["casos"].columns:
            condiciones = ["Todas"] + list(data["casos"]["condicion_final"].dropna().unique())
            
            # Obtener valor por defecto con manejo de reset
            condicion_default = get_default_filter_value("condicion_filter", "selectbox")
            if condicion_default is None:
                condicion_default = st.session_state.get("condicion_filter", "Todas")
            
            if condicion_default not in condiciones:
                condicion_default = "Todas"
                
            condicion_filter = st.selectbox(
                "⚰️ Condición Final:", 
                condiciones, 
                index=condiciones.index(condicion_default),
                key="condicion_filter_widget"
            )
            st.session_state["condicion_filter"] = condicion_filter

        # CORRECCIÓN: Sexo
        sexo_filter = "Todos"
        if not data["casos"].empty and "sexo" in data["casos"].columns:
            sexos = ["Todos"] + list(data["casos"]["sexo"].dropna().unique())
            
            sexo_default = get_default_filter_value("sexo_filter", "selectbox")
            if sexo_default is None:
                sexo_default = st.session_state.get("sexo_filter", "Todos")
            
            if sexo_default not in sexos:
                sexo_default = "Todos"
                
            sexo_filter = st.selectbox(
                "👤 Sexo:", 
                sexos, 
                index=sexos.index(sexo_default),
                key="sexo_filter_widget"
            )
            st.session_state["sexo_filter"] = sexo_filter

        # CORRECCIÓN: Edad (slider no tiene el mismo problema, pero por consistencia)
        edad_rango = None
        edad_es_filtro_real = False
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
                # Para sliders, verificamos si hay reset
                edad_default = get_default_filter_value("edad_filter", "slider")
                if edad_default is None:
                    edad_default = st.session_state.get("edad_filter", (edad_min, edad_max))
                else:
                    edad_default = (edad_min, edad_max)  # Valor por defecto en reset
                
                edad_rango = st.slider(
                    "🎂 Rango de Edad:",
                    min_value=edad_min,
                    max_value=edad_max,
                    value=edad_default,
                    key="edad_filter_widget",
                )
                st.session_state["edad_filter"] = edad_rango
                edad_es_filtro_real = edad_rango != (edad_min, edad_max)

    return {
        "condicion_final": condicion_filter,
        "sexo": sexo_filter,
        "edad_rango": edad_rango,
        "edad_es_filtro_real": edad_es_filtro_real,
    }

def create_filter_summary_multiple_optimized(
    filters_location, filters_temporal, filters_advanced
):
    """Crea resumen de filtros activos OPTIMIZADO."""
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

    # Filtros temporales - solo si NO es el rango por defecto
    if (
        filters_temporal["fecha_rango"]
        and len(filters_temporal["fecha_rango"]) == 2
        and filters_temporal.get("fecha_min")
        and filters_temporal.get("fecha_max_datos")
    ):
        fecha_inicio, fecha_fin = filters_temporal["fecha_rango"]
        fecha_min_default = filters_temporal["fecha_min"].date()
        fecha_max_default = filters_temporal["fecha_max_datos"].date()

        if fecha_inicio != fecha_min_default or fecha_fin != fecha_max_default:
            active_filters.append(
                f"📅 {fecha_inicio.strftime('%m/%y')}-{fecha_fin.strftime('%m/%y')}"
            )

    # Filtros avanzados
    if filters_advanced["condicion_final"] != "Todas":
        active_filters.append(f"⚰️ {filters_advanced['condicion_final']}")

    if filters_advanced["sexo"] != "Todos":
        active_filters.append(f"👤 {filters_advanced['sexo']}")

    # Edad solo si es realmente un filtro
    if filters_advanced.get("edad_es_filtro_real", False):
        edad_min, edad_max = filters_advanced["edad_rango"]
        active_filters.append(f"🎂 {edad_min}-{edad_max}")

    return active_filters


# ===== FUNCIONES DE APOYO =====

def get_initial_index(options, session_key):
    """Obtiene índice inicial para selectbox."""
    if session_key in st.session_state:
        current_value = st.session_state[session_key]
        if current_value in options:
            return options.index(current_value)
    return 0


def get_available_dates(data):
    """Obtiene fechas disponibles en los datos."""
    fechas = []
    if not data["casos"].empty and "fecha_inicio_sintomas" in data["casos"].columns:
        fechas.extend(data["casos"]["fecha_inicio_sintomas"].dropna().tolist())
    if (
        not data["epizootias"].empty
        and "fecha_notificacion" in data["epizootias"].columns
    ):
        fechas.extend(data["epizootias"]["fecha_notificacion"].dropna().tolist())
    return fechas


def show_active_filters(active_filters):
    """Muestra filtros activos en sidebar."""
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
    """Resetea todos los filtros."""
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
        # Agregar keys de widgets específicos
        "municipio_filter_widget",
        "vereda_filter_widget",
        "municipios_multiselect_widget", 
        "veredas_multiselect_widget",
        "condicion_filter_widget",
        "sexo_filter_widget",
        "edad_filter_widget",
        "fecha_filter_widget",
        "filtro_modo_widget",
    ]

    reset_count = 0
    
    for key in filter_keys:
        if key in st.session_state:
            try:
                del st.session_state[key]
                reset_count += 1
                logger.info(f"🗑️ Eliminado: {key}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar {key}: {str(e)}")

    # Establecer flag de reset para que los widgets se reconstruyan con valores por defecto
    st.session_state["filters_reset_flag"] = True
    
    if reset_count > 0:
        st.sidebar.success(f"✅ {reset_count} filtros restablecidos")
        logger.info(f"✅ Reset completado: {reset_count} filtros eliminados")
        
        # Forzar recarga de la página
        st.rerun()
    else:
        st.sidebar.info("ℹ️ No había filtros para restablecer")
        
def get_default_filter_value(filter_key, filter_type="selectbox"):
    """
    Obtiene valor por defecto para un filtro específico.
    
    Args:
        filter_key: Key del filtro
        filter_type: Tipo de widget (selectbox, multiselect, etc.)
    
    Returns:
        Valor por defecto apropiado
    """
    # Verificar si hay flag de reset activo
    if st.session_state.get("filters_reset_flag", False):
        # Limpiar flag después del primer uso
        if "filters_reset_flag" in st.session_state:
            del st.session_state["filters_reset_flag"]
        
        # Retornar valores por defecto según el tipo de filtro
        if filter_type == "multiselect":
            return []
        elif "municipio" in filter_key:
            return "Todos"
        elif "vereda" in filter_key:
            return "Todas"
        elif "condicion" in filter_key:
            return "Todas"
        elif "sexo" in filter_key:
            return "Todos"
        elif "filtro_modo" in filter_key:
            return "Único"
        else:
            return None
    
    # Si no hay flag de reset, retornar el valor actual del session_state
    return st.session_state.get(filter_key)