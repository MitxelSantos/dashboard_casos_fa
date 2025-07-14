"""
Componente de filtros CORREGIDO con soporte para selección múltiple y regiones desde VEREDAS.
"""

import streamlit as st
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def apply_filters_css(colors):
    """CSS optimizado para filtros múltiples."""
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

def extract_regiones_from_veredas_data(data):
    """Extrae regiones desde la hoja VEREDAS de BD_positivos.xlsx."""
    regiones = {}
    
    # Intentar obtener desde veredas_completas
    if "veredas_completas" in data and not data["veredas_completas"].empty:
        veredas_df = data["veredas_completas"]
        
        if "region" in veredas_df.columns and "municipio" in veredas_df.columns:
            logger.info("🗂️ Cargando regiones desde hoja VEREDAS")
            
            for region in veredas_df["region"].dropna().unique():
                municipios_region = veredas_df[veredas_df["region"] == region]["municipio"].dropna().unique()
                # Normalizar nombres de municipios
                municipios_norm = [str(m).upper().strip() for m in municipios_region]
                regiones[region] = sorted(list(set(municipios_norm)))
            
            logger.info(f"✅ Regiones cargadas desde VEREDAS: {list(regiones.keys())}")
            return regiones
    
    # Fallback: regiones predefinidas si no hay datos
    logger.warning("⚠️ No se pudieron cargar regiones desde VEREDAS, usando fallback")
    return {
        "Norte": ["FALAN", "FRESNO", "HERVEO", "LERIDA", "LIBANO", "MURILLO", "PALOCABILDO", "SANTA ISABEL", "VILLAHERMOSA"],
        "Centro": ["ALVARADO", "IBAGUE", "CAJAMARCA", "COELLO", "ESPINAL", "FLANDES", "GUAMO", "PIEDRAS", "ROVIRA", "VALLE DE SAN JUAN"],
        "Sur": ["ALPUJARRA", "ATACO", "CHAPARRAL", "COYAIMA", "DOLORES", "NATAGAIMA", "ORTEGA", "PLANADAS", "RIOBLANCO", "RONCESVALLES", "SAN ANTONIO"],
        "Oriente": ["CUNDAY", "ICONONZO", "MELGAR", "CARMEN DE APICALA", "VENADILLO", "CASABIANCA"],
        "Magdalena": ["AMBALEMA", "ARMERO", "HONDA", "MARIQUITA", "SALDAÑA"],
        "Suarez": ["SUAREZ", "PURIFICACION", "PRADO", "SAN LUIS", "VILLARRICA"]
    }

def create_hierarchical_filters_with_multiselect(data):
    """Filtros jerárquicos CORREGIDOS con soporte para selección múltiple."""
    
    # Selector de modo de filtrado
    st.sidebar.markdown("### 🎯 Modo de Filtrado")
    
    filtro_modo = st.sidebar.radio(
        "Seleccione el tipo de filtrado:",
        ["Único", "Múltiple"],
        index=0,
        key="filtro_modo",
        help="Único: un municipio/vereda. Múltiple: varios a la vez."
    )
    
    if filtro_modo == "Único":
        return create_single_filters(data)
    else:
        return create_multiple_filters_corrected(data)

def create_single_filters(data):
    """Filtros únicos (lógica original)."""
    # Filtro de municipio
    municipio_options = ["Todos"] + data["municipios_normalizados"]
    municipio_selected = st.sidebar.selectbox(
        "📍 MUNICIPIO:",
        municipio_options,
        index=get_initial_index(municipio_options, "municipio_filter"),
        key="municipio_filter_widget",
        help="Seleccione un municipio para filtrar los datos"
    )
    st.session_state["municipio_filter"] = municipio_selected

    # Filtro de vereda (dinámico según municipio)
    vereda_options = ["Todas"]
    vereda_disabled = municipio_selected == "Todos"
    
    if not vereda_disabled:
        veredas = get_veredas_for_municipio(data, municipio_selected)
        vereda_options.extend(sorted(veredas))

    vereda_selected = st.sidebar.selectbox(
        "🏘️ VEREDA:",
        vereda_options,
        index=get_initial_index(vereda_options, "vereda_filter"),
        key="vereda_filter_widget",
        disabled=vereda_disabled,
        help="Las veredas se actualizan según el municipio"
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
        "municipios_seleccionados": [municipio_selected] if municipio_selected != "Todos" else [],
        "veredas_seleccionadas": [vereda_selected] if vereda_selected != "Todas" else [],
    }

def create_multiple_filters_corrected(data):
    """Filtros múltiples CORREGIDOS con agrupación."""
    
    st.sidebar.markdown('<div class="multiselect-section">', unsafe_allow_html=True)
    st.sidebar.markdown("#### 🗂️ Selección Múltiple")
    
    # Obtener regiones desde datos VEREDAS
    regiones_tolima = extract_regiones_from_veredas_data(data)
    
    # Mostrar grupos predefinidos de municipios
    st.sidebar.markdown("**Grupos por Región:**")
    
    # Crear botones para cada región CORREGIDO
    cols = st.sidebar.columns(2)
    region_names = list(regiones_tolima.keys())
    
    for i, region in enumerate(region_names):
        col_idx = i % 2
        with cols[col_idx]:
            if st.button(
                f"{region} ({len(regiones_tolima[region])})", 
                key=f"btn_region_{region.lower().replace(' ', '_')}", 
                use_container_width=True,
                help=f"Seleccionar todos los municipios de {region}"
            ):
                # CORREGIDO: Inicializar si no existe
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
    
    # Inicializar default para multiselect
    default_municipios = st.session_state.get("municipios_multiselect", [])
    
    # Selector múltiple de municipios
    municipios_options = data["municipios_normalizados"]
    municipios_selected = st.sidebar.multiselect(
        "📍 MUNICIPIOS:",
        municipios_options,
        default=default_municipios,
        key="municipios_multiselect_widget",
        help="Seleccione uno o más municipios"
    )
    
    # Sincronizar con session_state
    st.session_state["municipios_multiselect"] = municipios_selected
    
    # Si hay municipios seleccionados, mostrar selector de veredas
    veredas_selected = []
    if municipios_selected:
        todas_las_veredas = []
        for municipio in municipios_selected:
            veredas_municipio = get_veredas_for_municipio(data, municipio)
            todas_las_veredas.extend(veredas_municipio)
        
        if todas_las_veredas:
            # Inicializar default para veredas
            default_veredas = st.session_state.get("veredas_multiselect", [])
            
            veredas_selected = st.sidebar.multiselect(
                "🏘️ VEREDAS:",
                sorted(set(todas_las_veredas)),
                default=default_veredas,
                key="veredas_multiselect_widget",
                help="Veredas de los municipios seleccionados"
            )
            
            # Sincronizar con session_state
            st.session_state["veredas_multiselect"] = veredas_selected
    
    # Botón para limpiar selección
    if municipios_selected or veredas_selected:
        if st.sidebar.button("🗑️ Limpiar Selección", use_container_width=True):
            st.session_state.municipios_multiselect = []
            st.session_state.veredas_multiselect = []
            st.rerun()
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    return {
        "modo": "multiple",
        "municipio_display": f"{len(municipios_selected)} municipios" if municipios_selected else "Todos",
        "municipio_normalizado": "Multiple",
        "vereda_display": f"{len(veredas_selected)} veredas" if veredas_selected else "Todas",
        "vereda_normalizada": "Multiple",
        "municipios_seleccionados": municipios_selected,
        "veredas_seleccionadas": veredas_selected,
        "regiones_disponibles": regiones_tolima,
    }

def create_map_mode_selector(colors):
    """Selector de modo del mapa: epidemiológico vs cobertura."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗺️ Modo de Visualización")
    
    modo_mapa = st.sidebar.radio(
        "Colorear mapa según:",
        ["Epidemiológico", "Cobertura de Vacunación"],
        index=0,
        key="modo_mapa",
        help="Epidemiológico: casos y epizootias. Cobertura: porcentaje de vacunación."
    )
    
    # Información del modo seleccionado CORREGIDA
    if modo_mapa == "Epidemiológico":
        st.sidebar.markdown(
            f"""
            <div style="background: {colors['info']}; color: white; padding: 0.5rem; border-radius: 6px; font-size: 0.8rem;">
                🔴 Rojo: Casos + Epizootias + Fallecidos<br>
                🟠 Naranja: Solo casos<br>
                🟡 Amarillo: Solo epizootias<br>
                ⚪ Gris claro: Sin datos
            </div>
            """,
            unsafe_allow_html=True
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
            unsafe_allow_html=True
        )
    
    return modo_mapa

def create_affectation_counters(data_filtered, filters, colors):
    """Crea contadores de afectación geográfica."""
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Determinar nivel actual
    if filters.get("modo") == "multiple":
        # Modo múltiple
        municipios_sel = filters.get("municipios_seleccionados", [])
        if len(municipios_sel) > 1:
            nivel = "multiple_municipios"
            total_ubicaciones = len(municipios_sel)
        else:
            nivel = "departamento"
            total_ubicaciones = 47  # Total municipios Tolima
    else:
        # Modo único
        if filters.get("vereda_display") != "Todas":
            nivel = "vereda"
            total_ubicaciones = 1
        elif filters.get("municipio_display") != "Todos":
            nivel = "municipio"
            municipio_actual = filters.get("municipio_display")
            veredas_municipio = get_veredas_for_municipio(data_filtered, municipio_actual)
            total_ubicaciones = len(veredas_municipio) if veredas_municipio else 0
        else:
            nivel = "departamento"
            total_ubicaciones = 47
    
    # Calcular contadores según nivel
    if nivel == "departamento":
        contadores = calculate_departmental_counters(casos, epizootias, total_ubicaciones)
        titulo = "🏛️ AFECTACIÓN TOLIMA"
    elif nivel == "municipio":
        contadores = calculate_municipal_counters(casos, epizootias, filters.get("municipio_display"), data_filtered, total_ubicaciones)
        titulo = f"🏘️ AFECTACIÓN {filters.get('municipio_display', 'MUNICIPIO')}"
    elif nivel == "multiple_municipios":
        contadores = calculate_multiple_counters(casos, epizootias, filters.get("municipios_seleccionados"))
        titulo = f"🗂️ AFECTACIÓN MÚLTIPLE ({len(filters.get('municipios_seleccionados', []))} MUNICIPIOS)"
    else:
        # Nivel vereda - sin contadores
        return None
    
    # Mostrar contadores
    st.markdown(
        f"""
        <div class="contadores-afectacion">
            <div style="font-weight: 800; font-size: 1rem; margin-bottom: 0.5rem;">{titulo}</div>
            <div class="contador-item">📍 {contadores['casos']} con casos</div>
            <div class="contador-item">🐒 {contadores['epizootias']} con epizootias</div>
            <div class="contador-item">🔄 {contadores['ambos']} con ambos</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    return contadores

def calculate_departmental_counters(casos, epizootias, total_municipios):
    """Calcula contadores departamentales."""
    municipios_con_casos = set()
    municipios_con_epizootias = set()
    
    if not casos.empty and "municipio" in casos.columns:
        municipios_con_casos = set(casos["municipio"].dropna())
    
    if not epizootias.empty and "municipio" in epizootias.columns:
        municipios_con_epizootias = set(epizootias["municipio"].dropna())
    
    municipios_con_ambos = municipios_con_casos.intersection(municipios_con_epizootias)
    
    return {
        "casos": f"{len(municipios_con_casos)}/{total_municipios} municipios",
        "epizootias": f"{len(municipios_con_epizootias)}/{total_municipios} municipios",
        "ambos": f"{len(municipios_con_ambos)}/{total_municipios} municipios"
    }

def calculate_municipal_counters(casos, epizootias, municipio_actual, data_filtered, total_veredas):
    """Calcula contadores municipales."""
    veredas_con_casos = set()
    veredas_con_epizootias = set()
    
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipio_norm = normalize_name(municipio_actual)
    
    if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
        casos_municipio = casos[casos["municipio"].apply(normalize_name) == municipio_norm]
        veredas_con_casos = set(casos_municipio["vereda"].dropna())
    
    if not epizootias.empty and "vereda" in epizootias.columns and "municipio" in epizootias.columns:
        epi_municipio = epizootias[epizootias["municipio"].apply(normalize_name) == municipio_norm]
        veredas_con_epizootias = set(epi_municipio["vereda"].dropna())
    
    veredas_con_ambos = veredas_con_casos.intersection(veredas_con_epizootias)
    
    return {
        "casos": f"{len(veredas_con_casos)}/{total_veredas} veredas",
        "epizootias": f"{len(veredas_con_epizootias)}/{total_veredas} veredas", 
        "ambos": f"{len(veredas_con_ambos)}/{total_veredas} veredas"
    }

def calculate_multiple_counters(casos, epizootias, municipios_seleccionados):
    """Calcula contadores para selección múltiple."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipios_norm = [normalize_name(m) for m in municipios_seleccionados]
    municipios_con_casos = set()
    municipios_con_epizootias = set()
    
    if not casos.empty and "municipio" in casos.columns:
        for municipio in municipios_norm:
            if len(casos[casos["municipio"].apply(normalize_name) == municipio]) > 0:
                municipios_con_casos.add(municipio)
    
    if not epizootias.empty and "municipio" in epizootias.columns:
        for municipio in municipios_norm:
            if len(epizootias[epizootias["municipio"].apply(normalize_name) == municipio]) > 0:
                municipios_con_epizootias.add(municipio)
    
    municipios_con_ambos = municipios_con_casos.intersection(municipios_con_epizootias)
    
    return {
        "casos": f"{len(municipios_con_casos)}/{len(municipios_seleccionados)} seleccionados",
        "epizootias": f"{len(municipios_con_epizootias)}/{len(municipios_seleccionados)} seleccionados",
        "ambos": f"{len(municipios_con_ambos)}/{len(municipios_seleccionados)} seleccionados"
    }

def apply_all_filters_multiple(data, filters_location, filters_temporal, filters_advanced):
    """Aplica filtros con soporte para selección múltiple."""
    casos_filtrados = data["casos"].copy()
    epizootias_filtradas = data["epizootias"].copy()

    initial_casos = len(casos_filtrados)
    initial_epizootias = len(epizootias_filtradas)

    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""

    # Filtros de ubicación según modo
    if filters_location.get("modo") == "multiple":
        # Filtrado múltiple
        municipios_seleccionados = filters_location.get("municipios_seleccionados", [])
        veredas_seleccionadas = filters_location.get("veredas_seleccionadas", [])
        
        if municipios_seleccionados:
            municipios_norm = [normalize_name(m) for m in municipios_seleccionados]
            
            if "municipio" in casos_filtrados.columns:
                casos_filtrados = casos_filtrados[
                    casos_filtrados["municipio"].apply(normalize_name).isin(municipios_norm)
                ]
            
            if "municipio" in epizootias_filtradas.columns:
                epizootias_filtradas = epizootias_filtradas[
                    epizootias_filtradas["municipio"].apply(normalize_name).isin(municipios_norm)
                ]
        
        if veredas_seleccionadas:
            veredas_norm = [normalize_name(v) for v in veredas_seleccionadas]
            
            if "vereda" in casos_filtrados.columns:
                casos_filtrados = casos_filtrados[
                    casos_filtrados["vereda"].apply(normalize_name).isin(veredas_norm)
                ]
            
            if "vereda" in epizootias_filtradas.columns:
                epizootias_filtradas = epizootias_filtradas[
                    epizootias_filtradas["vereda"].apply(normalize_name).isin(veredas_norm)
                ]
    
    else:
        # Filtrado único (lógica original)
        if filters_location["municipio_display"] != "Todos":
            municipio_norm = normalize_name(filters_location["municipio_display"])
            
            if "municipio" in casos_filtrados.columns:
                casos_filtrados = casos_filtrados[
                    casos_filtrados["municipio"].apply(normalize_name) == municipio_norm
                ]
            
            if "municipio" in epizootias_filtradas.columns:
                epizootias_filtradas = epizootias_filtradas[
                    epizootias_filtradas["municipio"].apply(normalize_name) == municipio_norm
                ]

        if filters_location["vereda_display"] != "Todas":
            vereda_norm = normalize_name(filters_location["vereda_display"])
            
            if "vereda" in casos_filtrados.columns:
                casos_filtrados = casos_filtrados[
                    casos_filtrados["vereda"].apply(normalize_name) == vereda_norm
                ]
            
            if "vereda" in epizootias_filtradas.columns:
                epizootias_filtradas = epizootias_filtradas[
                    epizootias_filtradas["vereda"].apply(normalize_name) == vereda_norm
                ]

    # Filtros temporales (sin cambios)
    if filters_temporal["fecha_rango"] and len(filters_temporal["fecha_rango"]) == 2:
        fecha_inicio = pd.Timestamp(filters_temporal["fecha_rango"][0])
        fecha_fin = pd.Timestamp(filters_temporal["fecha_rango"][1]) + pd.Timedelta(hours=23, minutes=59)

        if "fecha_inicio_sintomas" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                (casos_filtrados["fecha_inicio_sintomas"] >= fecha_inicio) &
                (casos_filtrados["fecha_inicio_sintomas"] <= fecha_fin)
            ]

        if "fecha_recoleccion" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                (epizootias_filtradas["fecha_recoleccion"] >= fecha_inicio) &
                (epizootias_filtradas["fecha_recoleccion"] <= fecha_fin)
            ]

    # Filtros avanzados (sin cambios)
    if filters_advanced["condicion_final"] != "Todas" and "condicion_final" in casos_filtrados.columns:
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
            (casos_filtrados["edad"] >= edad_min) & (casos_filtrados["edad"] <= edad_max)
        ]

    # Log del resultado
    final_casos = len(casos_filtrados)
    final_epizootias = len(epizootias_filtradas)
    
    logger.info(f"Filtrado aplicado - Casos: {initial_casos}→{final_casos}, Epizootias: {initial_epizootias}→{final_epizootias}")

    return {
        "casos": casos_filtrados,
        "epizootias": epizootias_filtradas,
        **{k: v for k, v in data.items() if k not in ["casos", "epizootias"]},
    }

def create_unified_filter_system(data):
    """Sistema unificado de filtros CORREGIDO."""
    # Aplicar CSS
    try:
        from config.colors import COLORS
        apply_filters_css(COLORS)
    except ImportError:
        default_colors = {'primary': '#7D0F2B', 'secondary': '#F2A900', 'info': '#4682B4'}
        apply_filters_css(default_colors)

    # Selector de modo de mapa
    modo_mapa = create_map_mode_selector(COLORS if 'COLORS' in locals() else default_colors)

    # Crear filtros según tipo
    filters_location = create_hierarchical_filters_with_multiselect(data)
    filters_temporal = create_temporal_filters(data)
    filters_advanced = create_advanced_filters(data)

    # Aplicar filtros
    data_filtered = apply_all_filters_multiple(data, filters_location, filters_temporal, filters_advanced)
    
    # Crear contadores de afectación
    contadores = create_affectation_counters(data_filtered, filters_location, COLORS if 'COLORS' in locals() else default_colors)

    # Crear resumen de filtros activos
    active_filters = create_filter_summary_multiple(filters_location, filters_temporal, filters_advanced)
    
    # Mostrar filtros activos
    show_active_filters(active_filters)

    # Botones de control
    st.sidebar.markdown("---")
    
    col1, col2 = st.sidebar.columns([3, 1])
    
    with col1:
        if st.button("🔄 Restablecer Todo", key="reset_all_filters", use_container_width=True):
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
        "contadores": contadores,
    }

    return {"filters": all_filters, "data_filtered": data_filtered}

def create_filter_summary_multiple(filters_location, filters_temporal, filters_advanced):
    """Crea resumen de filtros activos para modo múltiple."""
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

    # Filtros temporales (sin cambios)
    if filters_temporal["fecha_rango"] and len(filters_temporal["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters_temporal["fecha_rango"]
        if (filters_temporal.get("fecha_min") and filters_temporal.get("fecha_max") and 
            (fecha_inicio != filters_temporal["fecha_min"].date() or 
             fecha_fin != filters_temporal["fecha_max"].date())):
            active_filters.append(f"📅 {fecha_inicio.strftime('%m/%y')}-{fecha_fin.strftime('%m/%y')}")

    # Filtros avanzados (sin cambios)
    if filters_advanced["condicion_final"] != "Todas":
        active_filters.append(f"⚰️ {filters_advanced['condicion_final']}")

    if filters_advanced["sexo"] != "Todos":
        active_filters.append(f"👤 {filters_advanced['sexo']}")

    if filters_advanced["edad_rango"]:
        edad_min, edad_max = filters_advanced["edad_rango"]
        active_filters.append(f"🎂 {edad_min}-{edad_max}")

    return active_filters

# ===== FUNCIONES DE APOYO (mantener las existentes) =====

def normalize_name(name):
    if pd.isna(name) or name == "":
        return ""
    return str(name).upper().strip()

def get_initial_index(options, session_key):
    if session_key in st.session_state:
        current_value = st.session_state[session_key]
        if current_value in options:
            return options.index(current_value)
    return 0

def get_veredas_for_municipio(data, municipio_selected):
    municipio_norm = normalize_name(municipio_selected)
    veredas = set()
    
    if not data["casos"].empty and "vereda" in data["casos"].columns and "municipio" in data["casos"].columns:
        casos_municipio = data["casos"][
            data["casos"]["municipio"].apply(normalize_name) == municipio_norm
        ]
        veredas.update(casos_municipio["vereda"].dropna().unique())
    
    if not data["epizootias"].empty and "vereda" in data["epizootias"].columns and "municipio" in data["epizootias"].columns:
        epi_municipio = data["epizootias"][
            data["epizootias"]["municipio"].apply(normalize_name) == municipio_norm
        ]
        veredas.update(epi_municipio["vereda"].dropna().unique())
    
    return [v for v in veredas if v and str(v).strip()]

def create_temporal_filters(data):
    st.sidebar.markdown("---")
    fechas_disponibles = get_available_dates(data)
    
    if not fechas_disponibles:
        return {"fecha_rango": None, "fecha_min": None, "fecha_max": None}
    
    fecha_min = min(fechas_disponibles)
    fecha_max = max(fechas_disponibles)
    
    fecha_rango = st.sidebar.date_input(
        "📅 Rango de Fechas:",
        value=(fecha_min.date(), fecha_max.date()),
        min_value=fecha_min.date(),
        max_value=fecha_max.date(),
        key="fecha_filter_widget",
        help="Seleccione el período temporal de interés"
    )
    st.session_state["fecha_filter"] = fecha_rango

    if fecha_rango and len(fecha_rango) == 2:
        dias_seleccionados = (fecha_rango[1] - fecha_rango[0]).days
        st.sidebar.markdown(
            f'<div class="filter-help">📊 Período: {dias_seleccionados} días seleccionados</div>',
            unsafe_allow_html=True
        )

    return {"fecha_rango": fecha_rango, "fecha_min": fecha_min, "fecha_max": fecha_max}

def create_advanced_filters(data):
    with st.sidebar.expander("🔧 Filtros Avanzados", expanded=False):
        condicion_filter = "Todas"
        if not data["casos"].empty and "condicion_final" in data["casos"].columns:
            condiciones = ["Todas"] + list(data["casos"]["condicion_final"].dropna().unique())
            condicion_filter = st.selectbox("⚰️ Condición Final:", condiciones, key="condicion_filter")

        sexo_filter = "Todos"
        if not data["casos"].empty and "sexo" in data["casos"].columns:
            sexos = ["Todos"] + list(data["casos"]["sexo"].dropna().unique())
            sexo_filter = st.selectbox("👤 Sexo:", sexos, key="sexo_filter")

        edad_rango = None
        if not data["casos"].empty and "edad" in data["casos"].columns:
            edad_min = int(data["casos"]["edad"].min()) if not data["casos"]["edad"].isna().all() else 0
            edad_max = int(data["casos"]["edad"].max()) if not data["casos"]["edad"].isna().all() else 100
            
            if edad_min < edad_max:
                edad_rango = st.slider(
                    "🎂 Rango de Edad:",
                    min_value=edad_min,
                    max_value=edad_max,
                    value=(edad_min, edad_max),
                    key="edad_filter"
                )

    return {"condicion_final": condicion_filter, "sexo": sexo_filter, "edad_rango": edad_rango}

def get_available_dates(data):
    fechas = []
    if not data["casos"].empty and "fecha_inicio_sintomas" in data["casos"].columns:
        fechas.extend(data["casos"]["fecha_inicio_sintomas"].dropna().tolist())
    if not data["epizootias"].empty and "fecha_recoleccion" in data["epizootias"].columns:
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
        "municipio_filter", "vereda_filter", "fecha_filter",
        "condicion_filter", "sexo_filter", "edad_filter",
        "municipios_multiselect", "veredas_multiselect", "filtro_modo"
    ]
    
    reset_count = 0
    for key in filter_keys:
        if key in st.session_state:
            if "municipio" in key or "condicion" in key or "sexo" in key or "filtro_modo" in key:
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