"""
Componente de filtros del dashboard - BIDIRECCIONAL con mapas interactivos.
Sistema completamente integrado que sincroniza filtros con mapas.
VERSIÓN MEJORADA con sincronización bidireccional.
"""

import streamlit as st
import pandas as pd
from utils.data_processor import normalize_text

# Importar utilidades de estado del mapa
try:
    from utils.map_state import map_state, sync_sidebar_with_map
    MAP_STATE_AVAILABLE = True
except ImportError:
    MAP_STATE_AVAILABLE = False
    map_state = None


def create_responsive_filters_ui():
    """
    Agrega CSS específico para filtros responsive con integración de mapas.
    """
    st.markdown(
        """
        <style>
        /* =============== FILTROS BIDIRECCIONALES CSS =============== */
        
        .filter-section {
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 12px;
            padding: clamp(1rem, 3vw, 1.5rem);
            margin-bottom: clamp(0.75rem, 2vw, 1rem);
            border-left: 5px solid #7D0F2B;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .filter-section:hover {
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }
        
        .filter-header {
            color: #7D0F2B;
            font-size: clamp(1.1rem, 3vw, 1.2rem);
            font-weight: 700;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .filter-help {
            font-size: clamp(0.8rem, 2vw, 0.9rem);
            color: #666;
            margin-top: 0.5rem;
            line-height: 1.4;
            background: #f0f8ff;
            padding: 0.75rem;
            border-radius: 8px;
            border-left: 3px solid #4682B4;
        }
        
        /* Filtros primarios con iconos */
        .filter-primary {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 2px solid #7D0F2B;
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }
        
        .filter-primary:before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #7D0F2B, #F2A900);
        }
        
        .filter-primary .stSelectbox label {
            font-size: 1.1rem !important;
            font-weight: 800 !important;
            color: #7D0F2B !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
        
        /* Filtros secundarios */
        .filter-secondary {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .filter-secondary:hover {
            background: #e9ecef;
            border-color: #7D0F2B;
        }
        
        .filter-secondary .stSelectbox label,
        .filter-secondary .stMultiSelect label {
            font-size: 1rem !important;
            font-weight: 700 !important;
            color: #5A4214 !important;
        }
        
        /* Sincronización con mapas */
        .map-sync-indicator {
            background: linear-gradient(135deg, #4682B4, #F2A900);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            margin: 0.5rem 0;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            animation: pulse 2s infinite;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .filter-sync-status {
            background: #e8f5e8;
            color: #2d5a2d;
            padding: 0.75rem;
            border-radius: 8px;
            margin: 1rem 0;
            border-left: 4px solid #509E2F;
            font-size: 0.85rem;
            line-height: 1.4;
        }
        
        /* Responsive controls */
        .sidebar .stSelectbox > div > div,
        .sidebar .stMultiSelect > div > div,
        .sidebar .stDateInput > div > div {
            font-size: clamp(0.85rem, 2vw, 0.95rem) !important;
            min-height: 44px !important;
        }
        
        .sidebar .stSelectbox label,
        .sidebar .stMultiSelect label,
        .sidebar .stDateInput label,
        .sidebar .stSlider label,
        .sidebar .stCheckbox label {
            font-size: clamp(0.9rem, 2vw, 1rem) !important;
            font-weight: 600 !important;
            color: #2c2c2c !important;
        }
        
        /* Reset button con estilo mejorado */
        .reset-filters-btn {
            width: 100% !important;
            background: linear-gradient(135deg, #dc3545, #c82333) !important;
            color: white !important;
            border: none !important;
            border-radius: 25px !important;
            padding: 0.75rem 1.5rem !important;
            font-size: clamp(0.85rem, 2vw, 0.95rem) !important;
            font-weight: 700 !important;
            margin: 1.5rem 0 !important;
            transition: all 0.3s ease !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3) !important;
        }
        
        .reset-filters-btn:hover {
            background: linear-gradient(135deg, #c82333, #a71e2a) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(220, 53, 69, 0.4) !important;
        }
        
        /* Active filters display mejorado */
        .active-filters {
            background: linear-gradient(135deg, #7D0F2B, #5A4214);
            color: white;
            padding: clamp(0.75rem, 2vw, 1rem);
            border-radius: 12px;
            margin: 1rem 0;
            font-size: clamp(0.85rem, 2vw, 0.95rem);
            line-height: 1.5;
            box-shadow: 0 4px 15px rgba(125, 15, 43, 0.3);
        }
        
        .active-filters-title {
            font-weight: 700;
            margin-bottom: 0.75rem;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .active-filters-list {
            margin-left: 1rem;
        }
        
        .active-filters-list li {
            margin-bottom: 0.25rem;
            position: relative;
        }
        
        .active-filters-list li:before {
            content: '▶';
            position: absolute;
            left: -1rem;
            color: #F2A900;
            font-weight: bold;
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .filter-section {
                padding: 0.75rem;
                margin-bottom: 1rem;
            }
            
            .filter-header {
                font-size: 1rem;
                margin-bottom: 0.75rem;
            }
            
            .filter-primary {
                padding: 1rem;
                margin-bottom: 1rem;
            }
            
            .sidebar .stSelectbox > div > div,
            .sidebar .stMultiSelect > div > div {
                min-height: 48px !important; /* Más grande para touch */
            }
            
            .sidebar .stButton > button {
                min-height: 48px !important;
                font-size: 0.9rem !important;
            }
            
            .map-sync-indicator {
                font-size: 0.7rem;
                padding: 0.4rem 0.8rem;
            }
        }
        
        /* Indicadores de estado */
        .filter-connected {
            border-left-color: #509E2F !important;
        }
        
        .filter-disconnected {
            border-left-color: #dc3545 !important;
        }
        
        .sync-icon {
            animation: spin 2s linear infinite;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_hierarchical_filters_with_map_sync(data):
    """
    Crea filtros jerárquicos con sincronización bidireccional con mapas.

    Args:
        data (dict): Datos cargados con mapeos

    Returns:
        dict: Filtros seleccionados con sincronización
    """
    # Aplicar CSS responsive
    create_responsive_filters_ui()

    # Sincronizar con estado del mapa si está disponible
    if MAP_STATE_AVAILABLE and map_state:
        sync_sidebar_with_map(map_state)
    
    # Indicador de sincronización
    if MAP_STATE_AVAILABLE:
        st.sidebar.markdown(
            """
            <div class="map-sync-indicator">
                <span class="sync-icon">🔄</span>
                Sincronizado con mapas
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Sección de filtros primarios
    st.sidebar.markdown(
        """
        <div class="filter-section filter-primary">
            <div class="filter-header">
                🎯 Filtros Principales
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Filtro de municipio (PRIORIDAD MÁXIMA)
    municipio_options = ["Todos"] + [
        data["municipio_display_map"][norm] for norm in data["municipios_normalizados"]
    ]

    municipio_selected = st.sidebar.selectbox(
        "📍 **MUNICIPIO**:",
        municipio_options,
        key="municipio_filter",
        help="Seleccione un municipio. También puede hacer clic en el mapa.",
    )

    # Información del municipio seleccionado
    if municipio_selected != "Todos":
        st.sidebar.markdown(
            f"""
            <div class="filter-help">
                🏛️ <strong>{municipio_selected}</strong> seleccionado
                <br>💡 Haga clic en veredas del mapa para más detalles
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            """
            <div class="filter-help">
                💡 Seleccione un municipio aquí o haga clic en el mapa
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Determinar municipio normalizado seleccionado
    municipio_norm_selected = None
    if municipio_selected != "Todos":
        for norm, display in data["municipio_display_map"].items():
            if display == municipio_selected:
                municipio_norm_selected = norm
                break

    # Filtro de vereda (jerárquico - depende del municipio)
    vereda_options = ["Todas"]
    if (
        municipio_norm_selected
        and municipio_norm_selected in data["veredas_por_municipio"]
    ):
        veredas_norm = data["veredas_por_municipio"][municipio_norm_selected]
        if municipio_norm_selected in data["vereda_display_map"]:
            vereda_options.extend(
                [
                    data["vereda_display_map"][municipio_norm_selected].get(norm, norm)
                    for norm in veredas_norm
                ]
            )

    # Deshabilitar vereda si no hay municipio seleccionado
    vereda_disabled = municipio_selected == "Todos"

    if vereda_disabled:
        st.sidebar.markdown(
            """
            <div class="filter-help">
                💡 Primero seleccione un municipio para ver sus veredas
            </div>
            """,
            unsafe_allow_html=True,
        )

    vereda_selected = st.sidebar.selectbox(
        "🏘️ **VEREDA**:",
        vereda_options,
        key="vereda_filter",
        disabled=vereda_disabled,
        help="Las veredas se actualizan según el municipio. También puede hacer clic en el mapa.",
    )

    # Información de la vereda seleccionada
    if vereda_selected != "Todas" and not vereda_disabled:
        st.sidebar.markdown(
            f"""
            <div class="filter-help">
                📍 <strong>{vereda_selected}</strong> seleccionada
                <br>🔍 Vista detallada en el mapa
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Determinar vereda normalizada seleccionada
    vereda_norm_selected = None
    if vereda_selected != "Todas" and municipio_norm_selected:
        if municipio_norm_selected in data["vereda_display_map"]:
            for norm, display in data["vereda_display_map"][
                municipio_norm_selected
            ].items():
                if display == vereda_selected:
                    vereda_norm_selected = norm
                    break

    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    # Actualizar estado del mapa si hay cambios
    if MAP_STATE_AVAILABLE and map_state:
        update_map_state_from_filters(
            municipio_selected, municipio_norm_selected,
            vereda_selected, vereda_norm_selected
        )

    return {
        "municipio_display": municipio_selected,
        "municipio_normalizado": municipio_norm_selected,
        "vereda_display": vereda_selected,
        "vereda_normalizada": vereda_norm_selected,
    }


def update_map_state_from_filters(municipio_display, municipio_norm, vereda_display, vereda_norm):
    """Actualiza el estado del mapa basado en cambios en filtros."""
    
    # Evitar loops infinitos
    if st.session_state.get('map_filter_changed', False):
        return
    
    current_level = map_state.get_current_level()
    current_municipio = map_state.get_selected_municipio()
    current_vereda = map_state.get_selected_vereda()
    
    # Determinar si hay cambios que requieren actualización del mapa
    needs_update = False
    
    if vereda_display != "Todas":
        # Usuario seleccionó vereda específica
        if (not current_vereda or 
            current_vereda['display'] != vereda_display or
            current_level != 'vereda'):
            map_state.set_vereda_view(vereda_display, vereda_norm or vereda_display)
            needs_update = True
    
    elif municipio_display != "Todos":
        # Usuario seleccionó municipio específico
        if (not current_municipio or 
            current_municipio['display'] != municipio_display or
            current_level != 'municipio'):
            map_state.set_municipio_view(municipio_display, municipio_norm or municipio_display)
            needs_update = True
    
    else:
        # Usuario deseleccionó todo - vista departamental
        if current_level != 'departamento':
            map_state.set_departamento_view()
            needs_update = True


def create_content_filters(data):
    """
    Crea filtros de contenido responsive (fechas).

    Args:
        data (dict): Datos cargados

    Returns:
        dict: Filtros de contenido seleccionados
    """
    # Sección de filtros de contenido
    st.sidebar.markdown("---")
    
    st.sidebar.markdown(
        """
        <div class="filter-section filter-secondary">
            <div class="filter-header">
                📅 Filtros Temporales
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Filtro de rango de fechas con información contextual
    fechas_disponibles = []

    # Recopilar fechas de casos
    if not data["casos"].empty and "fecha_inicio_sintomas" in data["casos"].columns:
        fechas_casos = data["casos"]["fecha_inicio_sintomas"].dropna()
        fechas_disponibles.extend(fechas_casos.tolist())

    # Recopilar fechas de epizootias
    if (
        not data["epizootias"].empty
        and "fecha_recoleccion" in data["epizootias"].columns
    ):
        fechas_epi = data["epizootias"]["fecha_recoleccion"].dropna()
        fechas_disponibles.extend(fechas_epi.tolist())

    fecha_rango = None
    fecha_min = None
    fecha_max = None
    
    if fechas_disponibles:
        fecha_min = min(fechas_disponibles)
        fecha_max = max(fechas_disponibles)

        fecha_rango = st.sidebar.date_input(
            "📅 Rango de Fechas:",
            value=(fecha_min.date(), fecha_max.date()),
            min_value=fecha_min.date(),
            max_value=fecha_max.date(),
            key="fecha_filter",
            help="Seleccione el período temporal de interés",
        )
        
        # Información contextual de fechas
        st.sidebar.markdown(
            f"""
            <div class="filter-help">
                📊 Rango disponible: {fecha_min.strftime('%d/%m/%Y')} - {fecha_max.strftime('%d/%m/%Y')}
                <br>⏱️ Total: {(fecha_max - fecha_min).days} días de datos
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.warning("⚠️ No hay fechas disponibles en los datos")

    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    return {
        "tipo_datos": ["Casos Confirmados", "Epizootias"],  # Siempre ambos
        "fecha_rango": fecha_rango,
        "fecha_min": fecha_min,
        "fecha_max": fecha_max
    }


def create_advanced_filters(data):
    """
    Crea filtros avanzados responsive con mejor organización.

    Args:
        data (dict): Datos cargados

    Returns:
        dict: Filtros avanzados seleccionados
    """
    # Sección de filtros avanzados
    st.sidebar.markdown("---")

    # Expandir sección de filtros avanzados
    with st.sidebar.expander("🔧 Filtros Avanzados", expanded=False):
        st.markdown(
            """
            <div class="filter-sync-status">
                🎛️ <strong>Filtros complementarios</strong><br>
                Para análisis específicos y detallados
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Filtros para casos en dos columnas
        st.markdown("### 🦠 Casos Humanos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtro por condición final
            condicion_filter = "Todas"
            if not data["casos"].empty and "condicion_final" in data["casos"].columns:
                condiciones_disponibles = ["Todas"] + list(
                    data["casos"]["condicion_final"].dropna().unique()
                )
                condicion_filter = st.selectbox(
                    "⚰️ Condición:",
                    condiciones_disponibles,
                    key="condicion_filter",
                    help="Estado final del paciente",
                )

        with col2:
            # Filtro por sexo
            sexo_filter = "Todos"
            if not data["casos"].empty and "sexo" in data["casos"].columns:
                sexos_disponibles = ["Todos"] + list(
                    data["casos"]["sexo"].dropna().unique()
                )
                sexo_filter = st.selectbox(
                    "👤 Sexo:",
                    sexos_disponibles,
                    key="sexo_filter",
                    help="Género del paciente",
                )

        # Filtro por rango de edad (ancho completo)
        edad_rango = None
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
                    help="Seleccione el rango de edad de interés",
                )

        # Filtros para epizootias
        st.markdown("### 🐒 Epizootias")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtro por resultado de epizootia
            resultado_filter = "Todos"
            if not data["epizootias"].empty and "descripcion" in data["epizootias"].columns:
                resultados_disponibles = ["Todos"] + list(
                    data["epizootias"]["descripcion"].dropna().unique()
                )
                resultado_filter = st.selectbox(
                    "🔬 Resultado:",
                    resultados_disponibles,
                    key="resultado_filter",
                    help="Resultado del análisis",
                )

        with col2:
            # Filtro por fuente de epizootia
            fuente_filter = "Todas"
            if not data["epizootias"].empty and "proveniente" in data["epizootias"].columns:
                fuentes_disponibles = ["Todas"] + list(
                    data["epizootias"]["proveniente"].dropna().unique()
                )
                fuente_filter = st.selectbox(
                    "📋 Fuente:",
                    fuentes_disponibles,
                    key="fuente_filter",
                    help="Origen de la muestra",
                )

    return {
        "condicion_final": condicion_filter,
        "sexo": sexo_filter,
        "edad_rango": edad_rango,
        "resultado_epizootia": resultado_filter,
        "fuente_epizootia": fuente_filter,
    }


def create_filter_summary_with_map_info(filters_location, filters_content, filters_advanced, data):
    """
    Crea un resumen de filtros con información de sincronización con mapas.

    Args:
        filters_location (dict): Filtros de ubicación
        filters_content (dict): Filtros de contenido
        filters_advanced (dict): Filtros avanzados
        data (dict): Datos originales para comparar rangos

    Returns:
        list: Lista de filtros activos
    """
    active_filters = []

    # Filtros de ubicación (prioridad alta con iconos de mapa)
    if filters_location["municipio_display"] != "Todos":
        active_filters.append(f"🗺️ Municipio: {filters_location['municipio_display']}")

    if filters_location["vereda_display"] != "Todas":
        active_filters.append(f"📍 Vereda: {filters_location['vereda_display']}")

    # Agregar información de sincronización con mapa si está disponible
    if MAP_STATE_AVAILABLE and map_state:
        current_level = map_state.get_current_level()
        level_icons = {
            'departamento': '🏛️',
            'municipio': '🏘️', 
            'vereda': '📍'
        }
        active_filters.append(f"{level_icons[current_level]} Mapa: Vista {current_level}")

    # Filtros de contenido - SOLO si son diferentes del rango completo
    if filters_content["fecha_rango"] and len(filters_content["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters_content["fecha_rango"]
        
        # Comparar con el rango completo disponible
        fecha_min_original = filters_content.get("fecha_min")
        fecha_max_original = filters_content.get("fecha_max")
        
        # Solo agregar si es diferente del rango completo
        if (fecha_min_original and fecha_max_original and 
            (fecha_inicio != fecha_min_original.date() or fecha_fin != fecha_max_original.date())):
            active_filters.append(f"📅 Período: {fecha_inicio} - {fecha_fin}")

    # Filtros avanzados (menor prioridad)
    if filters_advanced["condicion_final"] != "Todas":
        active_filters.append(f"⚰️ Condición: {filters_advanced['condicion_final']}")

    if filters_advanced["sexo"] != "Todos":
        active_filters.append(f"👤 Sexo: {filters_advanced['sexo']}")

    # Edad - SOLO si es diferente del rango completo
    if filters_advanced["edad_rango"]:
        edad_min_sel, edad_max_sel = filters_advanced["edad_rango"]
        
        # Obtener rango completo de edad de los datos
        edad_min_original = 0
        edad_max_original = 100
        
        if not data["casos"].empty and "edad" in data["casos"].columns:
            edad_min_original = int(data["casos"]["edad"].min()) if not data["casos"]["edad"].isna().all() else 0
            edad_max_original = int(data["casos"]["edad"].max()) if not data["casos"]["edad"].isna().all() else 100
        
        # Solo agregar si es diferente del rango completo
        if edad_min_sel != edad_min_original or edad_max_sel != edad_max_original:
            active_filters.append(f"🎂 Edad: {edad_min_sel}-{edad_max_sel} años")

    if filters_advanced["resultado_epizootia"] != "Todos":
        resultado_short = (
            filters_advanced["resultado_epizootia"][:20] + "..."
            if len(filters_advanced["resultado_epizootia"]) > 20
            else filters_advanced["resultado_epizootia"]
        )
        active_filters.append(f"🔬 Resultado: {resultado_short}")

    if filters_advanced["fuente_epizootia"] != "Todas":
        fuente_short = (
            filters_advanced["fuente_epizootia"][:20] + "..."
            if len(filters_advanced["fuente_epizootia"]) > 20
            else filters_advanced["fuente_epizootia"]
        )
        active_filters.append(f"📋 Fuente: {fuente_short}")

    return active_filters


def show_active_filters_sidebar_with_map_sync(active_filters):
    """
    Muestra los filtros activos con información de sincronización con mapas.

    Args:
        active_filters (list): Lista de filtros activos
    """
    if not active_filters:
        return

    st.sidebar.markdown("---")

    # Título con contador y estado de sincronización
    filter_count = len(active_filters)
    sync_status = "🔗 Sincronizado" if MAP_STATE_AVAILABLE else "⚠️ Sin mapas"
    
    st.sidebar.markdown(
        f"""
        <div class="active-filters">
            <div class="active-filters-title">
                🎯 Filtros Activos ({filter_count}) | {sync_status}
            </div>
            <ul class="active-filters-list">
        """,
        unsafe_allow_html=True,
    )

    # Mostrar filtros con prioridad (mapas primero)
    for filter_desc in active_filters[:8]:  # Máximo 8 filtros visibles
        st.sidebar.markdown(f"<li>{filter_desc}</li>", unsafe_allow_html=True)

    # Si hay más filtros, mostrar indicador
    if len(active_filters) > 8:
        remaining = len(active_filters) - 8
        st.sidebar.markdown(f"<li>... y {remaining} filtro(s) más</li>", unsafe_allow_html=True)

    st.sidebar.markdown(
        """
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_all_filters(data, filters_location, filters_content, filters_advanced):
    """
    Aplica todos los filtros a los datos de manera eficiente.
    Versión optimizada para trabajar con mapas.

    Args:
        data (dict): Datos originales
        filters_location (dict): Filtros de ubicación
        filters_content (dict): Filtros de contenido
        filters_advanced (dict): Filtros avanzados

    Returns:
        dict: Datos filtrados
    """
    casos_filtrados = data["casos"].copy()
    epizootias_filtradas = data["epizootias"].copy()

    # =============== APLICAR FILTROS DE UBICACIÓN (PRIORIDAD MÁXIMA) ===============
    if filters_location["municipio_normalizado"]:
        municipio_norm = filters_location["municipio_normalizado"]

        if "municipio_normalizado" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["municipio_normalizado"] == municipio_norm
            ]

        if "municipio_normalizado" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["municipio_normalizado"] == municipio_norm
            ]

    if filters_location["vereda_normalizada"]:
        vereda_norm = filters_location["vereda_normalizada"]

        if "vereda_normalizada" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["vereda_normalizada"] == vereda_norm
            ]

        if "vereda_normalizada" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["vereda_normalizada"] == vereda_norm
            ]

    # =============== APLICAR FILTROS DE CONTENIDO ===============
    if filters_content["fecha_rango"] and len(filters_content["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters_content["fecha_rango"]
        fecha_inicio = pd.Timestamp(fecha_inicio)
        fecha_fin = pd.Timestamp(fecha_fin)

        # Filtrar casos por fecha de inicio de síntomas
        if "fecha_inicio_sintomas" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                (casos_filtrados["fecha_inicio_sintomas"] >= fecha_inicio)
                & (casos_filtrados["fecha_inicio_sintomas"] <= fecha_fin)
            ]

        # Filtrar epizootias por fecha de recolección
        if "fecha_recoleccion" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                (epizootias_filtradas["fecha_recoleccion"] >= fecha_inicio)
                & (epizootias_filtradas["fecha_recoleccion"] <= fecha_fin)
            ]

    # =============== APLICAR FILTROS AVANZADOS PARA CASOS ===============
    if filters_advanced["condicion_final"] != "Todas":
        if "condicion_final" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["condicion_final"]
                == filters_advanced["condicion_final"]
            ]

    if filters_advanced["sexo"] != "Todos":
        if "sexo" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["sexo"] == filters_advanced["sexo"]
            ]

    if filters_advanced["edad_rango"]:
        edad_min, edad_max = filters_advanced["edad_rango"]
        if "edad" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                (casos_filtrados["edad"] >= edad_min)
                & (casos_filtrados["edad"] <= edad_max)
            ]

    # =============== APLICAR FILTROS AVANZADOS PARA EPIZOOTIAS ===============
    if filters_advanced["resultado_epizootia"] != "Todos":
        if "descripcion" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["descripcion"]
                == filters_advanced["resultado_epizootia"]
            ]

    if filters_advanced["fuente_epizootia"] != "Todas":
        if "proveniente" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["proveniente"]
                == filters_advanced["fuente_epizootia"]
            ]

    # Retornar datos filtrados con metadatos preservados
    return {
        "casos": casos_filtrados,
        "epizootias": epizootias_filtradas,
        **{k: v for k, v in data.items() if k not in ["casos", "epizootias"]},
    }


def reset_all_filters():
    """
    Resetea todos los filtros y el estado del mapa.
    """
    # Lista de todas las claves de filtros
    filter_keys = [
        "municipio_filter",
        "vereda_filter", 
        "fecha_filter",
        "condicion_filter",
        "sexo_filter",
        "edad_filter",
        "resultado_filter",
        "fuente_filter",
    ]

    # Resetear cada filtro en session_state de manera segura
    for key in filter_keys:
        if key in st.session_state:
            try:
                del st.session_state[key]
            except Exception:
                continue
    
    # Resetear estado del mapa si está disponible
    if MAP_STATE_AVAILABLE and map_state:
        map_state.set_departamento_view()


def create_complete_filter_system_with_maps(data):
    """
    Crea el sistema completo de filtros con integración bidireccional de mapas.

    Args:
        data (dict): Datos cargados

    Returns:
        dict: Todos los filtros aplicados y datos filtrados
    """
    # Crear diferentes tipos de filtros con jerarquía clara
    filters_location = create_hierarchical_filters_with_map_sync(data)  # PRIORIDAD MÁXIMA con mapas
    filters_content = create_content_filters(data)  # PRIORIDAD MEDIA
    filters_advanced = create_advanced_filters(data)  # PRIORIDAD BAJA

    # Crear resumen de filtros activos con información de mapas
    active_filters = create_filter_summary_with_map_info(
        filters_location, filters_content, filters_advanced, data
    )

    # Mostrar filtros activos en sidebar con sincronización
    show_active_filters_sidebar_with_map_sync(active_filters)

    # Botón para resetear filtros con estilo responsive mejorado
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns([3, 1])

    with col1:
        if st.button(
            "🔄 Restablecer Todo",
            key="reset_all_filters_btn",
            help="Limpiar todos los filtros y resetear mapa",
        ):
            reset_all_filters()
            st.rerun()

    with col2:
        # Contador de filtros activos con mejor estilo
        filter_count = len(active_filters)
        if filter_count > 0:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #7D0F2B, #F2A900); 
                    color: white; 
                    padding: 0.4rem 0.8rem; 
                    border-radius: 20px; 
                    text-align: center; 
                    font-size: 0.8rem; 
                    font-weight: 700;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.3);
                ">
                    {filter_count}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Aplicar todos los filtros
    data_filtered = apply_all_filters(
        data, filters_location, filters_content, filters_advanced
    )
    
    # Agregar copyright al final
    from components.sidebar import add_copyright
    add_copyright()
    
    # Combinar todos los filtros en un solo diccionario
    all_filters = {
        **filters_location,
        **filters_content,
        **filters_advanced,
        "active_filters": active_filters,
    }

    return {"filters": all_filters, "data_filtered": data_filtered}


# Función principal exportada para compatibilidad
def create_complete_filter_system(data):
    """Función de compatibilidad que llama al sistema completo con mapas."""
    return create_complete_filter_system_with_maps(data)