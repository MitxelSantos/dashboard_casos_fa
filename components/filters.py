"""
Componente de filtros.
"""

import streamlit as st
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# ===== CONFIGURACIÓN Y CSS SIMPLIFICADO =====

def apply_filters_css(colors):
    """CSS minimalista para filtros."""
    st.markdown(
        f"""
        <style>
        .filter-section {{
            background: white;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid {colors['primary']};
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .active-filters {{
            background: {colors['primary']};
            color: white;
            padding: 0.75rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-size: 0.9rem;
        }}
        
        .filter-help {{
            background: #f0f8ff;
            padding: 0.5rem;
            border-radius: 6px;
            font-size: 0.8rem;
            color: #1565c0;
            margin-top: 0.5rem;
        }}
        
        @media (max-width: 768px) {{
            .filter-section {{ padding: 0.75rem; }}
            .sidebar .stSelectbox > div > div {{ min-height: 44px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ===== FUNCIONES CORE =====

def normalize_name(name):
    """Normaliza nombres para comparación consistente."""
    if pd.isna(name) or name == "":
        return ""
    return str(name).upper().strip()

def create_hierarchical_filters(data):
    """
    Filtros jerárquicos principales: Municipio → Vereda.
    """
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

    # Información contextual
    show_location_context(municipio_selected, vereda_selected, data)

    return {
        "municipio_display": municipio_selected,
        "municipio_normalizado": municipio_selected,
        "vereda_display": vereda_selected,
        "vereda_normalizada": vereda_selected,
    }

def create_temporal_filters(data):
    """
    Filtros temporales simplificados.
    """
    st.sidebar.markdown("---")
    
    # Obtener rango de fechas disponibles
    fechas_disponibles = get_available_dates(data)
    
    if not fechas_disponibles:
        return {"fecha_rango": None, "fecha_min": None, "fecha_max": None}
    
    fecha_min = min(fechas_disponibles)
    fecha_max = max(fechas_disponibles)
    
    # Input de rango de fechas
    fecha_rango = st.sidebar.date_input(
        "📅 Rango de Fechas:",
        value=(fecha_min.date(), fecha_max.date()),
        min_value=fecha_min.date(),
        max_value=fecha_max.date(),
        key="fecha_filter_widget",
        help="Seleccione el período temporal de interés"
    )
    st.session_state["fecha_filter"] = fecha_rango

    # Información del período
    if fecha_rango and len(fecha_rango) == 2:
        dias_seleccionados = (fecha_rango[1] - fecha_rango[0]).days
        st.sidebar.markdown(
            f'<div class="filter-help">📊 Período: {dias_seleccionados} días seleccionados</div>',
            unsafe_allow_html=True
        )

    return {
        "fecha_rango": fecha_rango,
        "fecha_min": fecha_min,
        "fecha_max": fecha_max
    }

def create_advanced_filters(data):
    """
    Filtros avanzados opcionales.
    """
    with st.sidebar.expander("🔧 Filtros Avanzados", expanded=False):
        # Filtro por condición final (casos)
        condicion_filter = "Todas"
        if not data["casos"].empty and "condicion_final" in data["casos"].columns:
            condiciones = ["Todas"] + list(data["casos"]["condicion_final"].dropna().unique())
            condicion_filter = st.selectbox(
                "⚰️ Condición Final:",
                condiciones,
                key="condicion_filter"
            )

        # Filtro por sexo
        sexo_filter = "Todos"
        if not data["casos"].empty and "sexo" in data["casos"].columns:
            sexos = ["Todos"] + list(data["casos"]["sexo"].dropna().unique())
            sexo_filter = st.selectbox(
                "👤 Sexo:",
                sexos,
                key="sexo_filter"
            )

        # Filtro por edad
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

    return {
        "condicion_final": condicion_filter,
        "sexo": sexo_filter,
        "edad_rango": edad_rango,
    }

def apply_all_filters(data, filters_location, filters_temporal, filters_advanced):
    """
    Aplica todos los filtros a los datos.
    """
    casos_filtrados = data["casos"].copy()
    epizootias_filtradas = data["epizootias"].copy()

    initial_casos = len(casos_filtrados)
    initial_epizootias = len(epizootias_filtradas)

    # Filtros de ubicación
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

    # Filtros temporales
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

    # Filtros avanzados
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
    
    if initial_casos != final_casos or initial_epizootias != final_epizootias:
        logger.info(f"Filtrado aplicado - Casos: {initial_casos}→{final_casos}, Epizootias: {initial_epizootias}→{final_epizootias}")

    return {
        "casos": casos_filtrados,
        "epizootias": epizootias_filtradas,
        **{k: v for k, v in data.items() if k not in ["casos", "epizootias"]},
    }

def create_filter_summary(filters_location, filters_temporal, filters_advanced):
    """
    Crea resumen de filtros activos.
    """
    active_filters = []
    
    if filters_location["municipio_display"] != "Todos":
        active_filters.append(f"📍 {filters_location['municipio_display']}")

    if filters_location["vereda_display"] != "Todas":
        active_filters.append(f"🏘️ {filters_location['vereda_display']}")

    if filters_temporal["fecha_rango"] and len(filters_temporal["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters_temporal["fecha_rango"]
        if (filters_temporal.get("fecha_min") and filters_temporal.get("fecha_max") and 
            (fecha_inicio != filters_temporal["fecha_min"].date() or 
             fecha_fin != filters_temporal["fecha_max"].date())):
            active_filters.append(f"📅 {fecha_inicio.strftime('%m/%y')}-{fecha_fin.strftime('%m/%y')}")

    if filters_advanced["condicion_final"] != "Todas":
        active_filters.append(f"⚰️ {filters_advanced['condicion_final']}")

    if filters_advanced["sexo"] != "Todos":
        active_filters.append(f"👤 {filters_advanced['sexo']}")

    if filters_advanced["edad_rango"]:
        edad_min, edad_max = filters_advanced["edad_rango"]
        active_filters.append(f"🎂 {edad_min}-{edad_max}")

    return active_filters

def show_active_filters(active_filters):
    """
    Muestra filtros activos en el sidebar.
    """
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
    """
    Resetea todos los filtros.
    """
    filter_keys = [
        "municipio_filter", "vereda_filter", "fecha_filter",
        "condicion_filter", "sexo_filter", "edad_filter"
    ]
    
    reset_count = 0
    for key in filter_keys:
        if key in st.session_state:
            if "municipio" in key or "condicion" in key or "sexo" in key:
                st.session_state[key] = "Todos"
            elif "vereda" in key:
                st.session_state[key] = "Todas"
            else:
                del st.session_state[key]
            reset_count += 1
    
    if reset_count > 0:
        st.sidebar.success(f"✅ {reset_count} filtros restablecidos")

# ===== FUNCIONES DE APOYO =====

def get_initial_index(options, session_key):
    """Obtiene índice inicial para selectbox basado en session_state."""
    if session_key in st.session_state:
        current_value = st.session_state[session_key]
        if current_value in options:
            return options.index(current_value)
    return 0

def get_veredas_for_municipio(data, municipio_selected):
    """Obtiene veredas para un municipio específico."""
    municipio_norm = normalize_name(municipio_selected)
    veredas = set()
    
    # Buscar en casos
    if not data["casos"].empty and "vereda" in data["casos"].columns and "municipio" in data["casos"].columns:
        casos_municipio = data["casos"][
            data["casos"]["municipio"].apply(normalize_name) == municipio_norm
        ]
        veredas.update(casos_municipio["vereda"].dropna().unique())
    
    # Buscar en epizootias
    if not data["epizootias"].empty and "vereda" in data["epizootias"].columns and "municipio" in data["epizootias"].columns:
        epi_municipio = data["epizootias"][
            data["epizootias"]["municipio"].apply(normalize_name) == municipio_norm
        ]
        veredas.update(epi_municipio["vereda"].dropna().unique())
    
    # Filtrar valores vacíos
    return [v for v in veredas if v and str(v).strip()]

def get_available_dates(data):
    """Obtiene todas las fechas disponibles en los datos."""
    fechas = []
    
    if not data["casos"].empty and "fecha_inicio_sintomas" in data["casos"].columns:
        fechas.extend(data["casos"]["fecha_inicio_sintomas"].dropna().tolist())
    
    if not data["epizootias"].empty and "fecha_recoleccion" in data["epizootias"].columns:
        fechas.extend(data["epizootias"]["fecha_recoleccion"].dropna().tolist())
    
    return fechas

def show_location_context(municipio, vereda, data):
    """Muestra información contextual de la ubicación seleccionada."""
    if municipio != "Todos":
        # Contar datos en el municipio
        municipio_norm = normalize_name(municipio)
        casos_count = 0
        epi_count = 0
        
        if not data["casos"].empty and "municipio" in data["casos"].columns:
            casos_count = len(data["casos"][
                data["casos"]["municipio"].apply(normalize_name) == municipio_norm
            ])
        
        if not data["epizootias"].empty and "municipio" in data["epizootias"].columns:
            epi_count = len(data["epizootias"][
                data["epizootias"]["municipio"].apply(normalize_name) == municipio_norm
            ])
        
        level_text = f"Vereda: {vereda}" if vereda != "Todas" else "Vista municipal"
        
        st.sidebar.markdown(
            f"""
            <div class="filter-help">
                📍 <strong>{municipio}</strong><br>
                📊 {casos_count} casos, {epi_count} epizootias<br>
                🗺️ {level_text}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ===== FUNCIÓN PRINCIPAL =====

def create_unified_filter_system(data):
    """
    Sistema unificado de filtros - FUNCIÓN PRINCIPAL.
    """
    # Aplicar CSS (importar dentro de la función para evitar errores)
    try:
        from config.colors import COLORS
        apply_filters_css(COLORS)
    except ImportError:
        # Fallback con colores básicos
        default_colors = {
            'primary': '#7D0F2B',
            'secondary': '#F2A900', 
            'info': '#4682B4'
        }
        apply_filters_css(default_colors)

    # Crear filtros
    filters_location = create_hierarchical_filters(data)
    filters_temporal = create_temporal_filters(data)
    filters_advanced = create_advanced_filters(data)

    # Crear resumen de filtros activos
    active_filters = create_filter_summary(filters_location, filters_temporal, filters_advanced)
    
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

    # Aplicar filtros
    data_filtered = apply_all_filters(data, filters_location, filters_temporal, filters_advanced)
    
    # Agregar copyright (con import seguro)
    try:
        from components.sidebar import add_copyright
        add_copyright()
    except ImportError:
        pass  # No es crítico si no se puede importar
    
    # Combinar filtros
    all_filters = {
        **filters_location,
        **filters_temporal,
        **filters_advanced,
        "active_filters": active_filters,
    }

    return {"filters": all_filters, "data_filtered": data_filtered}


create_complete_filter_system_with_maps = create_unified_filter_system
create_complete_filter_system = create_unified_filter_system