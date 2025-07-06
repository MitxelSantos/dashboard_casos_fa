"""
Componente de filtros MEJORADO del dashboard.
NUEVA FUNCIONALIDAD: Sincronización bidireccional con mapas interactivos
Soporte para doble clic en mapas → actualización automática de filtros
"""

import streamlit as st
import pandas as pd


def create_responsive_filters_ui():
    """
    CSS mejorado para filtros con indicadores de sincronización.
    """
    st.markdown(
        """
        <style>
        /* =============== FILTROS CSS MEJORADO =============== */
        
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
            transform: translateY(-2px);
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
        
        /* NUEVO: Indicador de sincronización con mapa */
        .map-sync-indicator {
            background: linear-gradient(45deg, #4CAF50, #8BC34A);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            margin: 0.5rem 0;
            text-align: center;
            animation: pulse-sync 2s infinite;
            box-shadow: 0 3px 10px rgba(76, 175, 80, 0.3);
        }
        
        @keyframes pulse-sync {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.02); }
            100% { opacity: 1; transform: scale(1); }
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
            position: relative;
            overflow: hidden;
        }
        
        .active-filters::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shimmer 3s infinite;
        }
        
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
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
        
        /* Reset button mejorado */
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
        
        /* NUEVO: Indicador de cambios desde mapa */
        .map-update-indicator {
            background: linear-gradient(45deg, #FF9800, #FFC107);
            color: white;
            padding: 0.4rem 0.8rem;
            border-radius: 15px;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 0.3rem 0;
            text-align: center;
            animation: blink 1s ease-in-out 3;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
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
            
            .sidebar .stSelectbox > div > div,
            .sidebar .stMultiSelect > div > div {
                min-height: 48px !important;
            }
            
            .sidebar .stButton > button {
                min-height: 48px !important;
                font-size: 0.9rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def detect_map_interaction():
    """
    NUEVO: Detecta si hubo una interacción desde el mapa.
    """
    return st.session_state.get('map_filter_updated', False)


def clear_map_interaction_flag():
    """
    NUEVO: Limpia la bandera de actualización desde mapa.
    """
    if 'map_filter_updated' in st.session_state:
        st.session_state['map_filter_updated'] = False


def show_map_sync_indicator():
    """
    NUEVO: Muestra indicador de sincronización con mapa.
    """
    if detect_map_interaction():
        st.sidebar.markdown(
            """
            <div class="map-update-indicator">
                🗺️ Actualizado desde mapa
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Auto-limpiar después de mostrar
        clear_map_interaction_flag()

def create_hierarchical_filters_enhanced(data):
    """
    SIMPLIFICADO: Filtros jerárquicos usando nombres directos de shapefiles.
    ELIMINADA toda la lógica de normalización.
    """
    # Aplicar CSS responsive
    create_responsive_filters_ui()
    
    # Mostrar indicador de sincronización si aplica
    show_map_sync_indicator()
    
    # FILTRO DE MUNICIPIO SIMPLIFICADO
    municipio_options = ["Todos"] + list(data["municipios_normalizados"])  # Nombres directos

    # Detectar valor inicial
    initial_municipio_index = 0
    if "municipio_filter" in st.session_state:
        current_municipio = st.session_state["municipio_filter"]
        if current_municipio in municipio_options:
            initial_municipio_index = municipio_options.index(current_municipio)

    municipio_selected = st.sidebar.selectbox(
        "📍 **MUNICIPIO**:",
        municipio_options,
        index=initial_municipio_index,
        key="municipio_filter_widget",
        help="Seleccione un municipio para filtrar los datos. También puede hacer doble clic en el mapa.",
    )

    # Sincronizar con session_state
    if "municipio_filter" not in st.session_state or st.session_state["municipio_filter"] != municipio_selected:
        st.session_state["municipio_filter"] = municipio_selected

    # FILTRO DE VEREDA SIMPLIFICADO
    vereda_options = ["Todas"]
    vereda_disabled = municipio_selected == "Todos"
    
    if not vereda_disabled and municipio_selected in data["veredas_por_municipio"]:
        veredas_disponibles = data["veredas_por_municipio"][municipio_selected]
        vereda_options.extend(veredas_disponibles)

    # Detectar valor inicial de vereda
    initial_vereda_index = 0
    if not vereda_disabled and "vereda_filter" in st.session_state:
        current_vereda = st.session_state["vereda_filter"]
        if current_vereda in vereda_options:
            initial_vereda_index = vereda_options.index(current_vereda)

    if vereda_disabled:
        st.sidebar.markdown(
            """
            <div class="filter-help">
                💡 Primero seleccione un municipio para ver sus veredas
                <br>🖱️ O haga doble clic en un municipio del mapa
            </div>
            """,
            unsafe_allow_html=True,
        )

    vereda_selected = st.sidebar.selectbox(
        "🏘️ **VEREDA**:",
        vereda_options,
        index=initial_vereda_index,
        key="vereda_filter_widget",
        disabled=vereda_disabled,
        help="Las veredas se actualizan según el municipio. También puede hacer doble clic en veredas del mapa.",
    )

    # Sincronizar vereda con session_state
    if not vereda_disabled:
        if "vereda_filter" not in st.session_state or st.session_state["vereda_filter"] != vereda_selected:
            st.session_state["vereda_filter"] = vereda_selected
    else:
        # Resetear vereda si no hay municipio seleccionado
        if "vereda_filter" in st.session_state:
            st.session_state["vereda_filter"] = "Todas"
        vereda_selected = "Todas"

    # Información contextual
    if municipio_selected != "Todos":
        veredas_count = len(vereda_options) - 1  # -1 por "Todas"
        info_color = "🟢" if vereda_selected != "Todas" else "🟡"
        st.sidebar.markdown(
            f"""
            <div class="filter-help">
                {info_color} <strong>{municipio_selected}</strong><br>
                🏘️ {veredas_count} veredas disponibles<br>
                🗺️ Nivel: {'Vereda específica' if vereda_selected != 'Todas' else 'Vista municipal'}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            """
            <div class="filter-help">
                🗺️ Vista departamental del Tolima<br>
                📍 Seleccione un municipio para ver sus veredas<br>
                📊 Mostrando datos de todo el departamento
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "municipio_display": municipio_selected,
        "municipio_normalizado": municipio_selected,  # Ahora es lo mismo
        "vereda_display": vereda_selected,
        "vereda_normalizada": vereda_selected,  # Ahora es lo mismo
    }


def apply_all_filters_enhanced(data, filters_location, filters_content, filters_advanced):
    """
    SIMPLIFICADO: Aplica filtros usando nombres directos sin normalización.
    """
    casos_filtrados = data["casos"].copy()
    epizootias_filtradas = data["epizootias"].copy()

    # Contador de registros para logging
    initial_casos = len(casos_filtrados)
    initial_epizootias = len(epizootias_filtradas)

    # PASO 1: Aplicar filtros de ubicación DIRECTOS
    if filters_location["municipio_display"] != "Todos":
        municipio_selected = filters_location["municipio_display"]

        if "municipio" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[casos_filtrados["municipio"] == municipio_selected]

        if "municipio" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[epizootias_filtradas["municipio"] == municipio_selected]

    if filters_location["vereda_display"] != "Todas":
        vereda_selected = filters_location["vereda_display"]

        if "vereda" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[casos_filtrados["vereda"] == vereda_selected]

        if "vereda" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[epizootias_filtradas["vereda"] == vereda_selected]

    # PASO 2: Aplicar filtros de contenido (temporales) - SIN CAMBIOS
    if filters_content["fecha_rango"] and len(filters_content["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters_content["fecha_rango"]
        fecha_inicio = pd.Timestamp(fecha_inicio)
        fecha_fin = pd.Timestamp(fecha_fin) + pd.Timedelta(hours=23, minutes=59, seconds=59)

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

    # PASO 3: Aplicar filtros avanzados para casos - SIN CAMBIOS
    if filters_advanced["condicion_final"] != "Todas":
        if "condicion_final" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["condicion_final"] == filters_advanced["condicion_final"]
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

    # PASO 4: Aplicar filtros avanzados para epizootias - SIN CAMBIOS
    if filters_advanced["fuente_epizootia"] != "Todas":
        if "proveniente" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["proveniente"] == filters_advanced["fuente_epizootia"]
            ]

    # LOGGING: Almacenar estadísticas de filtrado
    final_casos = len(casos_filtrados)
    final_epizootias = len(epizootias_filtradas)
    
    st.session_state["filter_stats"] = {
        "initial_casos": initial_casos,
        "final_casos": final_casos,
        "casos_filtered_out": initial_casos - final_casos,
        "initial_epizootias": initial_epizootias,
        "final_epizootias": final_epizootias,
        "epizootias_filtered_out": initial_epizootias - final_epizootias,
    }

    # Retornar datos filtrados con metadatos preservados
    return {
        "casos": casos_filtrados,
        "epizootias": epizootias_filtradas,
        **{k: v for k, v in data.items() if k not in ["casos", "epizootias"]},
    }


def update_filters_from_map(municipio=None, vereda=None):
    """
    SIMPLIFICADO: Actualiza filtros desde interacciones del mapa usando nombres directos.
    """
    updated = False
    
    if municipio and municipio != "Todos":
        if "municipio_filter" not in st.session_state or st.session_state["municipio_filter"] != municipio:
            st.session_state["municipio_filter"] = municipio
            st.session_state["map_filter_updated"] = True
            updated = True
    
    if vereda and vereda != "Todas":
        if "vereda_filter" not in st.session_state or st.session_state["vereda_filter"] != vereda:
            st.session_state["vereda_filter"] = vereda
            st.session_state["map_filter_updated"] = True
            updated = True
    elif vereda == "Todas" and "vereda_filter" in st.session_state:
        st.session_state["vereda_filter"] = "Todas"
        st.session_state["map_filter_updated"] = True
        updated = True
    
    return updated

def create_content_filters_enhanced(data):
    """
    MEJORADO: Filtros de contenido con mejor UX.
    """
    # Sección de filtros de contenido
    st.sidebar.markdown("---")

    # Filtro de rango de fechas con información contextual mejorada
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

        # Valor inicial del rango (completo por defecto)
        initial_range = (fecha_min.date(), fecha_max.date())
        
        # Detectar si hay un rango personalizado en session_state
        if "fecha_filter" in st.session_state and st.session_state["fecha_filter"]:
            stored_range = st.session_state["fecha_filter"]
            if isinstance(stored_range, (list, tuple)) and len(stored_range) == 2:
                initial_range = stored_range

        fecha_rango = st.sidebar.date_input(
            "📅 Rango de Fechas:",
            value=initial_range,
            min_value=fecha_min.date(),
            max_value=fecha_max.date(),
            key="fecha_filter_widget",
            help="Seleccione el período temporal de interés. Afecta casos y epizootias.",
        )
        
        # Sincronizar con session_state
        st.session_state["fecha_filter"] = fecha_rango
        
        # Información contextual mejorada
        total_dias = (fecha_max - fecha_min).days
        
        if fecha_rango and len(fecha_rango) == 2:
            dias_seleccionados = (pd.Timestamp(fecha_rango[1]) - pd.Timestamp(fecha_rango[0])).days
            porcentaje_periodo = (dias_seleccionados / total_dias * 100) if total_dias > 0 else 0
            
            st.sidebar.markdown(
                f"""
                <div class="filter-help">
                    📊 Rango disponible: {fecha_min.strftime('%d/%m/%Y')} - {fecha_max.strftime('%d/%m/%Y')}
                    <br>🎯 Seleccionado: {dias_seleccionados} días ({porcentaje_periodo:.1f}% del período)
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.sidebar.markdown(
                f"""
                <div class="filter-help">
                    📊 Rango disponible: {fecha_min.strftime('%d/%m/%Y')} - {fecha_max.strftime('%d/%m/%Y')}
                    <br>⏱️ Total: {total_dias} días de datos
                    <br>💡 Seleccione ambas fechas para filtrar
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.sidebar.warning("⚠️ No hay fechas disponibles en los datos")

    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    return {
        "tipo_datos": ["Casos Confirmados", "Epizootias Positivas"],
        "fecha_rango": fecha_rango,
        "fecha_min": fecha_min,
        "fecha_max": fecha_max
    }


def create_advanced_filters_enhanced(data):
    """
    MEJORADO: Filtros avanzados con mejor organización.
    """
    # Sección de filtros avanzados
    st.sidebar.markdown("---")

    # Expandir sección de filtros avanzados
    with st.sidebar.expander("🔧 Filtros Avanzados", expanded=False):
        st.markdown(
            """
            <div style="background: #e8f4fd; padding: 10px; border-radius: 6px; margin-bottom: 15px;">
                🎛️ <strong>Filtros complementarios</strong><br>
                Para análisis específicos y detallados
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Pestañas para organizar filtros avanzados
        tab1, tab2 = st.tabs(["🦠 Casos", "🐒 Epizootias"])
        
        with tab1:
            st.markdown("**Filtros para Casos Humanos**")
            
            # Filtro por condición final
            condicion_filter = "Todas"
            if not data["casos"].empty and "condicion_final" in data["casos"].columns:
                condiciones_disponibles = ["Todas"] + list(
                    data["casos"]["condicion_final"].dropna().unique()
                )
                condicion_filter = st.selectbox(
                    "⚰️ Condición Final:",
                    condiciones_disponibles,
                    key="condicion_filter",
                    help="Estado final del paciente",
                )

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

            # Filtro por rango de edad
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
        
        with tab2:
            st.markdown("**Filtros para Epizootias**")
            
            # Filtrar solo epizootias positivas para los filtros
            epi_positivas = data["epizootias"]
            if not epi_positivas.empty and "descripcion" in epi_positivas.columns:
                epi_positivas = epi_positivas[epi_positivas["descripcion"] == "POSITIVO FA"]
            
            # Filtro por fuente de epizootia (solo positivas)
            fuente_filter = "Todas"
            if not epi_positivas.empty and "proveniente" in epi_positivas.columns:
                fuentes_disponibles = ["Todas"] + list(
                    epi_positivas["proveniente"].dropna().unique()
                )
                fuente_filter = st.selectbox(
                    "📋 Fuente:",
                    fuentes_disponibles,
                    key="fuente_filter",
                    help="Origen de la muestra (solo epizootias positivas)",
                )
            
            # Información adicional sobre epizootias
            if not epi_positivas.empty:
                total_epi = len(epi_positivas)
                fuentes_unicas = epi_positivas["proveniente"].nunique() if "proveniente" in epi_positivas.columns else 0
                
                st.markdown(
                    f"""
                    <div style="background: #fff3e0; padding: 8px; border-radius: 4px; font-size: 0.8rem; margin-top: 10px;">
                        📊 <strong>{total_epi}</strong> epizootias positivas<br>
                        📋 <strong>{fuentes_unicas}</strong> fuentes diferentes
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    return {
        "condicion_final": condicion_filter,
        "sexo": sexo_filter,
        "edad_rango": edad_rango,
        "fuente_epizootia": fuente_filter,
    }


def create_filter_summary_enhanced(filters_location, filters_content, filters_advanced, data):
    """
    MEJORADO: Resumen de filtros activos con categorización.
    """
    active_filters = []
    
    # CATEGORÍA: Filtros de ubicación (prioridad alta)
    if filters_location["municipio_display"] != "Todos":
        active_filters.append(f"🗺️ Municipio: {filters_location['municipio_display']}")

    if filters_location["vereda_display"] != "Todas":
        active_filters.append(f"📍 Vereda: {filters_location['vereda_display']}")

    # CATEGORÍA: Filtros temporales
    if filters_content["fecha_rango"] and len(filters_content["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters_content["fecha_rango"]
        
        # Comparar con el rango completo disponible
        fecha_min_original = filters_content.get("fecha_min")
        fecha_max_original = filters_content.get("fecha_max")
        
        # Solo agregar si es diferente del rango completo
        if (fecha_min_original and fecha_max_original and 
            (fecha_inicio != fecha_min_original.date() or fecha_fin != fecha_max_original.date())):
            
            # Formato de fecha más compacto
            fecha_inicio_str = fecha_inicio.strftime("%m/%y")
            fecha_fin_str = fecha_fin.strftime("%m/%y")
            active_filters.append(f"📅 Período: {fecha_inicio_str}-{fecha_fin_str}")

    # CATEGORÍA: Filtros demográficos
    if filters_advanced["condicion_final"] != "Todas":
        condicion_short = filters_advanced["condicion_final"][:10] + "..." if len(filters_advanced["condicion_final"]) > 10 else filters_advanced["condicion_final"]
        active_filters.append(f"⚰️ Condición: {condicion_short}")

    if filters_advanced["sexo"] != "Todos":
        active_filters.append(f"👤 {filters_advanced['sexo']}")

    # CATEGORÍA: Filtros numéricos
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
            active_filters.append(f"🎂 {edad_min_sel}-{edad_max_sel} años")

    # CATEGORÍA: Filtros de fuente
    if filters_advanced["fuente_epizootia"] != "Todas":
        fuente_short = (
            filters_advanced["fuente_epizootia"][:15] + "..."
            if len(filters_advanced["fuente_epizootia"]) > 15
            else filters_advanced["fuente_epizootia"]
        )
        active_filters.append(f"📋 {fuente_short}")

    return active_filters


def show_active_filters_sidebar_enhanced(active_filters):
    """
    MEJORADO: Muestra filtros activos con categorización y animaciones.
    """
    if not active_filters:
        return

    st.sidebar.markdown("---")

    # Categorizar filtros
    geographic_filters = [f for f in active_filters if any(icon in f for icon in ["🗺️", "📍"])]
    temporal_filters = [f for f in active_filters if "📅" in f]
    demographic_filters = [f for f in active_filters if any(icon in f for icon in ["⚰️", "👤", "🎂"])]
    other_filters = [f for f in active_filters if f not in geographic_filters + temporal_filters + demographic_filters]

    # Título con contador y categorías
    filter_count = len(active_filters)
    categories_count = sum([
        1 if geographic_filters else 0,
        1 if temporal_filters else 0,
        1 if demographic_filters else 0,
        1 if other_filters else 0
    ])
    
    st.sidebar.markdown(
        f"""
        <div class="active-filters">
            <div class="active-filters-title">
                🎯 Filtros Activos ({filter_count}) - {categories_count} Categorías
            </div>
            <ul class="active-filters-list">
        """,
        unsafe_allow_html=True,
    )

    # Mostrar filtros por categoría
    all_categorized_filters = []
    
    if geographic_filters:
        all_categorized_filters.append("🌍 GEOGRÁFICOS:")
        all_categorized_filters.extend(geographic_filters)
    
    if temporal_filters:
        all_categorized_filters.append("⏰ TEMPORALES:")
        all_categorized_filters.extend(temporal_filters)
    
    if demographic_filters:
        all_categorized_filters.append("👥 DEMOGRÁFICOS:")
        all_categorized_filters.extend(demographic_filters)
    
    if other_filters:
        all_categorized_filters.append("🔧 OTROS:")
        all_categorized_filters.extend(other_filters)

    # Mostrar máximo 8 elementos (incluyendo headers)
    for filter_desc in all_categorized_filters[:8]:
        if filter_desc.endswith(":"):
            # Es un header de categoría
            st.sidebar.markdown(f"<li style='font-weight: bold; color: #F2A900; margin-top: 0.5rem;'>{filter_desc}</li>", unsafe_allow_html=True)
        else:
            # Es un filtro normal
            st.sidebar.markdown(f"<li>{filter_desc}</li>", unsafe_allow_html=True)

    # Si hay más filtros, mostrar indicador
    if len(all_categorized_filters) > 8:
        remaining = len(all_categorized_filters) - 8
        st.sidebar.markdown(f"<li style='opacity: 0.7;'>... y {remaining} filtro(s) más</li>", unsafe_allow_html=True)

    st.sidebar.markdown(
        """
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

def reset_all_filters_enhanced():
    """
    CORREGIDO: Reset completo con limpieza de estado de mapas y confirmación.
    """
    # Lista completa de claves a resetear
    filter_keys = [
        "municipio_filter", "vereda_filter", "fecha_filter",
        "condicion_filter", "sexo_filter", "edad_filter", "fuente_filter",
        "map_filter_updated", "filter_stats_detailed", "show_filter_help"
    ]
    
    # Guardar estado anterior para logging
    previous_state = {}
    for key in filter_keys:
        if key in st.session_state:
            previous_state[key] = st.session_state.get(key)
    
    # Resetear cada clave según su tipo
    reset_count = 0
    for key in filter_keys:
        if key in st.session_state:
            try:
                if "municipio" in key:
                    st.session_state[key] = "Todos"
                elif "vereda" in key:
                    st.session_state[key] = "Todas"
                elif key in ["condicion_filter", "sexo_filter", "fuente_filter"]:
                    st.session_state[key] = "Todas" if "fuente" in key else "Todos"
                else:
                    del st.session_state[key]
                reset_count += 1
            except:
                continue
    
    # Mensaje de confirmación con estadísticas
    if reset_count > 0:
        st.sidebar.success(f"✅ {reset_count} filtros restablecidos", icon="🧹")
    else:
        st.sidebar.info("ℹ️ No había filtros para restablecer", icon="🔄")

def create_complete_filter_system_enhanced(data):
    """
    MEJORADO: Sistema completo de filtros con sincronización bidireccional.
    """
    # Crear diferentes tipos de filtros con versiones mejoradas
    filters_location = create_hierarchical_filters_enhanced(data)
    filters_content = create_content_filters_enhanced(data)
    filters_advanced = create_advanced_filters_enhanced(data)

    # Crear resumen de filtros activos mejorado
    active_filters = create_filter_summary_enhanced(
        filters_location, filters_content, filters_advanced, data
    )

    # Mostrar filtros activos en sidebar con categorización
    show_active_filters_sidebar_enhanced(active_filters)

    # SECCIÓN DE CONTROL: Botones de gestión de filtros
    st.sidebar.markdown("---")
    
    # Mostrar estadísticas de filtrado si están disponibles
    if "filter_stats" in st.session_state:
        stats = st.session_state["filter_stats"]
        casos_reduction = ((stats["initial_casos"] - stats["final_casos"]) / stats["initial_casos"] * 100) if stats["initial_casos"] > 0 else 0
        epi_reduction = ((stats["initial_epizootias"] - stats["final_epizootias"]) / stats["initial_epizootias"] * 100) if stats["initial_epizootias"] > 0 else 0
        
        if casos_reduction > 0 or epi_reduction > 0:
            st.sidebar.markdown(
                f"""
                <div style="background: #e8f5e8; padding: 8px; border-radius: 6px; font-size: 0.8rem; margin-bottom: 10px;">
                    📊 <strong>Filtrado aplicado:</strong><br>
                    🦠 Casos: {stats["final_casos"]}/{stats["initial_casos"]} ({casos_reduction:.1f}% filtrado)<br>
                    🐒 Epizootias: {stats["final_epizootias"]}/{stats["initial_epizootias"]} ({epi_reduction:.1f}% filtrado)
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Botones de control
    col1, col2 = st.sidebar.columns([3, 1])

    with col1:
        if st.button(
            "🔄 Restablecer Todo",
            key="reset_all_filters_btn_enhanced",
            help="Limpiar todos los filtros y volver a vista completa",
        ):
            reset_all_filters_enhanced()
            st.rerun()

    with col2:
        # Contador de filtros activos con diseño mejorado
        filter_count = len(active_filters)
        if filter_count > 0:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #7D0F2B, #F2A900); 
                    color: white; 
                    padding: 0.4rem 0.6rem; 
                    border-radius: 50%; 
                    text-align: center; 
                    font-size: 0.8rem; 
                    font-weight: 700;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.3);
                    min-width: 30px;
                    min-height: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    {filter_count}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Aplicar todos los filtros con versión mejorada
    data_filtered = apply_all_filters_enhanced(
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

def create_complete_filter_system_with_maps(data):
    """
    CORREGIDO: Sistema completo con sincronización bidireccional mapas-filtros.
    """
    # Aplicar CSS responsive
    create_responsive_filters_ui()
    
    # **PASO 1: Detectar cambios desde mapa**
    map_changed = detect_and_process_map_changes()
    
    # **PASO 2: Crear filtros jerárquicos con valores sincronizados**
    filters_location = create_hierarchical_filters_with_map_sync(data, map_changed)
    
    # **PASO 3: Crear filtros de contenido**
    filters_content = create_content_filters_enhanced(data)
    
    # **PASO 4: Crear filtros avanzados**
    filters_advanced = create_advanced_filters_enhanced(data)

    # **PASO 5: Crear resumen de filtros activos mejorado**
    active_filters = create_filter_summary_enhanced(
        filters_location, filters_content, filters_advanced, data
    )

    # **PASO 6: Mostrar filtros activos en sidebar**
    show_active_filters_sidebar_enhanced(active_filters)

    # **PASO 7: Controles de gestión**
    show_filter_management_controls(active_filters)
    
    # **PASO 8: Aplicar filtros con logging detallado**
    data_filtered = apply_all_filters_with_logging(
        data, filters_location, filters_content, filters_advanced
    )
    
    # **PASO 9: Mostrar estadísticas de filtrado**
    show_filtering_statistics(data, data_filtered)
    
    # Combinar todos los filtros
    all_filters = {
        **filters_location,
        **filters_content,
        **filters_advanced,
        "active_filters": active_filters,
        "map_synchronized": map_changed,
    }

    return {"filters": all_filters, "data_filtered": data_filtered}


def get_current_filter_state():
    """
    NUEVO: Obtiene el estado actual de todos los filtros.
    """
    return {
        "municipio": st.session_state.get("municipio_filter", "Todos"),
        "vereda": st.session_state.get("vereda_filter", "Todas"),
        "fecha": st.session_state.get("fecha_filter", None),
        "condicion": st.session_state.get("condicion_filter", "Todas"),
        "sexo": st.session_state.get("sexo_filter", "Todos"),
        "edad": st.session_state.get("edad_filter", None),
        "fuente": st.session_state.get("fuente_filter", "Todas"),
    }


def validate_filter_sync():
    """
    NUEVO: Valida que los filtros estén sincronizados correctamente.
    """
    issues = []
    
    # Verificar coherencia municipio-vereda
    municipio = st.session_state.get("municipio_filter", "Todos")
    vereda = st.session_state.get("vereda_filter", "Todas")
    
    if vereda != "Todas" and municipio == "Todos":
        issues.append("Vereda seleccionada sin municipio")
    
    # Verificar fechas válidas
    fecha_rango = st.session_state.get("fecha_filter", None)
    if fecha_rango and len(fecha_rango) == 2:
        if fecha_rango[0] > fecha_rango[1]:
            issues.append("Rango de fechas inválido")
    
    return issues

def detect_and_process_map_changes():
    """
    NUEVA: Detección mejorada de cambios desde el mapa.
    """
    map_changed = False
    
    # Verificar si hay cambios pendientes desde el mapa
    if st.session_state.get('map_filter_updated', False):
        map_changed = True
        
        # Mostrar notificación de sincronización
        st.sidebar.success("🗺️ Sincronizado desde mapa", icon="🔄")
        
        # Limpiar bandera después de procesar
        st.session_state['map_filter_updated'] = False
    
    return map_changed


def create_hierarchical_filters_with_map_sync(data, map_changed):
    """
    NUEVA: Filtros jerárquicos con sincronización perfecta con mapas.
    """
    
    # **SINCRONIZACIÓN: Detectar fuente del cambio**
    if map_changed:
        st.sidebar.markdown(
            """
            <div class="map-sync-indicator">
                🗺️ ✅ Actualizado desde mapa
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # **FILTRO DE MUNICIPIO CON SINCRONIZACIÓN PERFECTA**
    municipio_options = ["Todos"] + [
        data["municipio_display_map"][norm] for norm in data["municipios_normalizados"]
    ]

    # Valor inicial desde session_state o por defecto
    municipio_inicial = st.session_state.get("municipio_filter", "Todos")
    
    # Validar que el valor inicial esté en las opciones
    if municipio_inicial not in municipio_options:
        municipio_inicial = "Todos"
        st.session_state["municipio_filter"] = "Todos"

    municipio_selected = st.sidebar.selectbox(
        "📍 **MUNICIPIO**:",
        municipio_options,
        index=municipio_options.index(municipio_inicial),
        key="municipio_filter_widget",
        help="🗺️ Seleccione un municipio o haga clic en el mapa",
    )

    # **ACTUALIZACIÓN BIDIRECCIONAL**
    if municipio_selected != st.session_state.get("municipio_filter", "Todos"):
        st.session_state["municipio_filter"] = municipio_selected
        # Si el cambio viene del sidebar (no del mapa), resetear vereda
        if not map_changed:
            st.session_state["vereda_filter"] = "Todas"

    # Determinar municipio normalizado
    municipio_norm_selected = None
    if municipio_selected != "Todos":
        for norm, display in data["municipio_display_map"].items():
            if display == municipio_selected:
                municipio_norm_selected = norm
                break

    # **FILTRO DE VEREDA CON DEPENDENCIA DEL MUNICIPIO**
    vereda_options = ["Todas"]
    vereda_disabled = municipio_selected == "Todos"
    
    if not vereda_disabled and municipio_norm_selected in data["veredas_por_municipio"]:
        veredas_norm = data["veredas_por_municipio"][municipio_norm_selected]
        if municipio_norm_selected in data["vereda_display_map"]:
            vereda_options.extend([
                data["vereda_display_map"][municipio_norm_selected].get(norm, norm)
                for norm in veredas_norm
            ])

    # Valor inicial de vereda con validación
    vereda_inicial = st.session_state.get("vereda_filter", "Todas")
    if vereda_disabled or vereda_inicial not in vereda_options:
        vereda_inicial = "Todas"
        st.session_state["vereda_filter"] = "Todas"

    vereda_selected = st.sidebar.selectbox(
        "🏘️ **VEREDA**:",
        vereda_options,
        index=vereda_options.index(vereda_inicial),
        key="vereda_filter_widget",
        disabled=vereda_disabled,
        help="🏘️ Las veredas se actualizan según el municipio seleccionado",
    )

    # **ACTUALIZACIÓN DE VEREDA**
    if not vereda_disabled and vereda_selected != st.session_state.get("vereda_filter", "Todas"):
        st.session_state["vereda_filter"] = vereda_selected

    # Determinar vereda normalizada
    vereda_norm_selected = None
    if vereda_selected != "Todas" and municipio_norm_selected:
        if municipio_norm_selected in data["vereda_display_map"]:
            for norm, display in data["vereda_display_map"][municipio_norm_selected].items():
                if display == vereda_selected:
                    vereda_norm_selected = norm
                    break

    # **INFORMACIÓN CONTEXTUAL MEJORADA**
    if municipio_selected != "Todos":
        veredas_count = len(vereda_options) - 1  # -1 por "Todas"
        info_color = "🟢" if vereda_selected != "Todas" else "🟡"
        st.sidebar.markdown(
            f"""
            <div class="filter-help">
                {info_color} <strong>{municipio_selected}</strong><br>
                🏘️ {veredas_count} veredas disponibles<br>
                🗺️ Nivel: {'Vereda' if vereda_selected != 'Todas' else 'Municipal'}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            """
            <div class="filter-help">
                🗺️ Vista departamental del Tolima<br>
                📍 Seleccione un municipio<br>
                📊 Mostrando datos de todo el departamento
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    return {
        "municipio_display": municipio_selected,
        "municipio_normalizado": municipio_norm_selected,
        "vereda_display": vereda_selected,
        "vereda_normalizada": vereda_norm_selected,
    }

def create_hierarchical_filters_with_map_sync_enhanced(data, map_changed):
    """
    CORREGIDO: Filtros jerárquicos con sincronización perfecta mejorada.
    """
    
    # **PREVENIR LOOPS INFINITOS**: Detectar fuente del cambio
    if map_changed:
        st.sidebar.markdown(
            """
            <div class="map-sync-indicator">
                🗺️ ✅ Actualizado desde mapa
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Limpiar bandera inmediatamente para prevenir loops
        if 'map_filter_updated' in st.session_state:
            st.session_state['map_filter_updated'] = False
    
    # **FILTRO DE MUNICIPIO CON SINCRONIZACIÓN ROBUSTA**
    municipio_options = ["Todos"] + [
        data["municipio_display_map"][norm] for norm in data["municipios_normalizados"]
    ]

    # Valor inicial desde session_state con validación
    municipio_inicial = st.session_state.get("municipio_filter", "Todos")
    
    # VALIDACIÓN CRÍTICA: Asegurar que el valor esté en las opciones
    if municipio_inicial not in municipio_options:
        municipio_inicial = "Todos"
        st.session_state["municipio_filter"] = "Todos"
        logger.warning(f"⚠️ Municipio '{municipio_inicial}' no encontrado en opciones, reseteando a 'Todos'")

    # Widget con key único para evitar conflictos
    municipio_selected = st.sidebar.selectbox(
        "📍 **MUNICIPIO**:",
        municipio_options,
        index=municipio_options.index(municipio_inicial),
        key="municipio_filter_widget_main",  # Key único
        help="🗺️ Seleccione un municipio o haga doble clic en el mapa",
    )

    # **SINCRONIZACIÓN BIDIRECCIONAL MEJORADA**
    # Solo actualizar si hay cambio real y no viene del mapa
    if municipio_selected != st.session_state.get("municipio_filter", "Todos"):
        if not map_changed:  # Solo si NO viene del mapa
            st.session_state["municipio_filter"] = municipio_selected
            # Si el cambio viene del sidebar, resetear vereda
            st.session_state["vereda_filter"] = "Todas"
            logger.info(f"🔄 Municipio actualizado desde sidebar: {municipio_selected}")

    # Determinar municipio normalizado
    municipio_norm_selected = None
    if municipio_selected != "Todos":
        for norm, display in data["municipio_display_map"].items():
            if display == municipio_selected:
                municipio_norm_selected = norm
                break

    # **FILTRO DE VEREDA CON VALIDACIÓN MEJORADA**
    vereda_options = ["Todas"]
    vereda_disabled = municipio_selected == "Todos"
    
    if not vereda_disabled and municipio_norm_selected in data["veredas_por_municipio"]:
        veredas_norm = data["veredas_por_municipio"][municipio_norm_selected]
        if municipio_norm_selected in data["vereda_display_map"]:
            vereda_options.extend([
                data["vereda_display_map"][municipio_norm_selected].get(norm, norm)
                for norm in veredas_norm
            ])

    # Valor inicial de vereda con validación robusta
    vereda_inicial = st.session_state.get("vereda_filter", "Todas")
    if vereda_disabled:
        vereda_inicial = "Todas"
        st.session_state["vereda_filter"] = "Todas"
    elif vereda_inicial not in vereda_options:
        vereda_inicial = "Todas"
        st.session_state["vereda_filter"] = "Todas"
        logger.warning(f"⚠️ Vereda '{vereda_inicial}' no encontrada en opciones del municipio, reseteando")

    vereda_selected = st.sidebar.selectbox(
        "🏘️ **VEREDA**:",
        vereda_options,
        index=vereda_options.index(vereda_inicial),
        key="vereda_filter_widget_main",  # Key único
        disabled=vereda_disabled,
        help="🏘️ Las veredas se actualizan según el municipio seleccionado",
    )

    # **SINCRONIZACIÓN DE VEREDA**
    if not vereda_disabled and vereda_selected != st.session_state.get("vereda_filter", "Todas"):
        if not map_changed:  # Solo si NO viene del mapa
            st.session_state["vereda_filter"] = vereda_selected
            logger.info(f"🔄 Vereda actualizada desde sidebar: {vereda_selected}")

    # Determinar vereda normalizada
    vereda_norm_selected = None
    if vereda_selected != "Todas" and municipio_norm_selected:
        if municipio_norm_selected in data["vereda_display_map"]:
            for norm, display in data["vereda_display_map"][municipio_norm_selected].items():
                if display == vereda_selected:
                    vereda_norm_selected = norm
                    break

    # **INFORMACIÓN CONTEXTUAL DETALLADA**
    if municipio_selected != "Todos":
        veredas_count = len(vereda_options) - 1  # -1 por "Todas"
        info_color = "🟢" if vereda_selected != "Todas" else "🟡"
        st.sidebar.markdown(
            f"""
            <div class="filter-help">
                {info_color} <strong>{municipio_selected}</strong><br>
                🏘️ {veredas_count} veredas disponibles<br>
                🗺️ Nivel: {'Vereda específica' if vereda_selected != 'Todas' else 'Vista municipal'}<br>
                🔄 Sincronizado con mapa interactivo
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            """
            <div class="filter-help">
                🗺️ Vista departamental completa del Tolima<br>
                📍 Seleccione un municipio para ver sus veredas<br>
                🖱️ O haga clic en cualquier municipio del mapa<br>
                📊 Mostrando datos de todo el departamento
            </div>
            """,
            unsafe_allow_html=True,
        )

    # **BOTÓN DE DEBUG** (opcional, solo en desarrollo)
    if st.sidebar.checkbox("🔧 Modo Debug", value=False, key="debug_mode_checkbox"):
        st.session_state['debug_mode'] = True
        st.sidebar.markdown("**🔧 Estado de Filtros:**")
        st.sidebar.code(f"""
        municipio_filter: {st.session_state.get('municipio_filter')}
        vereda_filter: {st.session_state.get('vereda_filter')}
        map_changed: {map_changed}
        municipio_selected: {municipio_selected}
        vereda_selected: {vereda_selected}
                """)
    else:
        st.session_state['debug_mode'] = False

    return {
        "municipio_display": municipio_selected,
        "municipio_normalizado": municipio_norm_selected,
        "vereda_display": vereda_selected,
        "vereda_normalizada": vereda_norm_selected,
    }
    
def verify_filter_sync():
    """
    NUEVA: Función de utilidad para verificar que la sincronización funcione.
    Usar solo para debugging.
    """
    if st.session_state.get('debug_mode', False):
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🔍 Verificación de Sincronización:**")
        
        # Obtener todos los valores relacionados con filtros
        filters_state = {}
        for key in st.session_state.keys():
            if 'filter' in key.lower():
                filters_state[key] = st.session_state[key]
        
        if filters_state:
            st.sidebar.json(filters_state)
        else:
            st.sidebar.info("No hay filtros activos")
        
        # Botón para limpiar todo (para testing)
        if st.sidebar.button("🧹 Limpiar Todo (Testing)", key="clear_all_debug"):
            keys_to_clear = [key for key in st.session_state.keys() if 'filter' in key.lower()]
            for key in keys_to_clear:
                del st.session_state[key]
            st.sidebar.success("✅ Todos los filtros limpiados")
            st.rerun()

def show_filter_management_controls(active_filters):
    """
    NUEVA: Controles de gestión de filtros con estadísticas.
    """
    st.sidebar.markdown("---")

    # Botones de control
    col1, col2 = st.sidebar.columns([3, 1])

    with col1:
        if st.button(
            "🔄 Restablecer Todo",
            key="reset_all_filters_enhanced",
            help="Limpiar todos los filtros y volver a vista completa",
            use_container_width=True
        ):
            reset_all_filters_enhanced()
            st.rerun()


def apply_all_filters_with_logging(data, filters_location, filters_content, filters_advanced):
    """
    NUEVA: Aplicación de filtros con logging detallado para debugging.
    """
    casos_filtrados = data["casos"].copy()
    epizootias_filtradas = data["epizootias"].copy()

    # Logging inicial
    initial_casos = len(casos_filtrados)
    initial_epizootias = len(epizootias_filtradas)
    
    filtros_aplicados = []

    # **APLICAR FILTROS DE UBICACIÓN CON LOGGING**
    if filters_location["municipio_normalizado"]:
        municipio_norm = filters_location["municipio_normalizado"]
        
        if "municipio_normalizado" in casos_filtrados.columns:
            casos_antes = len(casos_filtrados)
            casos_filtrados = casos_filtrados[
                casos_filtrados["municipio_normalizado"] == municipio_norm
            ]
            casos_despues = len(casos_filtrados)
            if casos_antes != casos_despues:
                filtros_aplicados.append(f"📍 Municipio: {casos_antes} → {casos_despues} casos")

        if "municipio_normalizado" in epizootias_filtradas.columns:
            epi_antes = len(epizootias_filtradas)
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["municipio_normalizado"] == municipio_norm
            ]
            epi_despues = len(epizootias_filtradas)
            if epi_antes != epi_despues:
                filtros_aplicados.append(f"📍 Municipio: {epi_antes} → {epi_despues} epizootias")

    if filters_location["vereda_normalizada"]:
        vereda_norm = filters_location["vereda_normalizada"]
        
        if "vereda_normalizada" in casos_filtrados.columns:
            casos_antes = len(casos_filtrados)
            casos_filtrados = casos_filtrados[
                casos_filtrados["vereda_normalizada"] == vereda_norm
            ]
            casos_despues = len(casos_filtrados)
            if casos_antes != casos_despues:
                filtros_aplicados.append(f"🏘️ Vereda: {casos_antes} → {casos_despues} casos")

        if "vereda_normalizada" in epizootias_filtradas.columns:
            epi_antes = len(epizootias_filtradas)
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["vereda_normalizada"] == vereda_norm
            ]
            epi_despues = len(epizootias_filtradas)
            if epi_antes != epi_despues:
                filtros_aplicados.append(f"🏘️ Vereda: {epi_antes} → {epi_despues} epizootias")

    # **APLICAR FILTROS TEMPORALES**
    if filters_content["fecha_rango"] and len(filters_content["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters_content["fecha_rango"]
        fecha_inicio = pd.Timestamp(fecha_inicio)
        fecha_fin = pd.Timestamp(fecha_fin) + pd.Timedelta(hours=23, minutes=59, seconds=59)

        if "fecha_inicio_sintomas" in casos_filtrados.columns:
            casos_antes = len(casos_filtrados)
            casos_filtrados = casos_filtrados[
                (casos_filtrados["fecha_inicio_sintomas"] >= fecha_inicio)
                & (casos_filtrados["fecha_inicio_sintomas"] <= fecha_fin)
            ]
            casos_despues = len(casos_filtrados)
            if casos_antes != casos_despues:
                filtros_aplicados.append(f"📅 Fecha casos: {casos_antes} → {casos_despues}")

        if "fecha_recoleccion" in epizootias_filtradas.columns:
            epi_antes = len(epizootias_filtradas)
            epizootias_filtradas = epizootias_filtradas[
                (epizootias_filtradas["fecha_recoleccion"] >= fecha_inicio)
                & (epizootias_filtradas["fecha_recoleccion"] <= fecha_fin)
            ]
            epi_despues = len(epizootias_filtradas)
            if epi_antes != epi_despues:
                filtros_aplicados.append(f"📅 Fecha epizootias: {epi_antes} → {epi_despues}")

    # **APLICAR FILTROS AVANZADOS**
    if filters_advanced["condicion_final"] != "Todas" and not casos_filtrados.empty:
        if "condicion_final" in casos_filtrados.columns:
            casos_antes = len(casos_filtrados)
            casos_filtrados = casos_filtrados[
                casos_filtrados["condicion_final"] == filters_advanced["condicion_final"]
            ]
            casos_despues = len(casos_filtrados)
            if casos_antes != casos_despues:
                filtros_aplicados.append(f"⚰️ Condición: {casos_antes} → {casos_despues} casos")

    # **GUARDAR ESTADÍSTICAS PARA DEBUGGING**
    final_casos = len(casos_filtrados)
    final_epizootias = len(epizootias_filtradas)
    
    st.session_state["filter_stats_detailed"] = {
        "initial_casos": initial_casos,
        "final_casos": final_casos,
        "initial_epizootias": initial_epizootias,
        "final_epizootias": final_epizootias,
        "filtros_aplicados": filtros_aplicados,
        "reduction_casos_pct": ((initial_casos - final_casos) / initial_casos * 100) if initial_casos > 0 else 0,
        "reduction_epi_pct": ((initial_epizootias - final_epizootias) / initial_epizootias * 100) if initial_epizootias > 0 else 0,
    }

    return {
        "casos": casos_filtrados,
        "epizootias": epizootias_filtradas,
        **{k: v for k, v in data.items() if k not in ["casos", "epizootias"]},
    }


def show_filtering_statistics(data_original, data_filtered):
    """
    NUEVA: Muestra estadísticas detalladas del filtrado en sidebar.
    """
    if "filter_stats_detailed" in st.session_state:
        stats = st.session_state["filter_stats_detailed"]
        
        # Solo mostrar si hay alguna reducción
        if stats['reduction_casos_pct'] > 0 or stats['reduction_epi_pct'] > 0:
            
            if st.sidebar.checkbox("📊 Ver Estadísticas Filtrado", value=False):
                st.sidebar.markdown("**📈 Impacto del Filtrado:**")
                
                # Métricas de casos
                st.sidebar.metric(
                    "🦠 Casos Filtrados",
                    f"{stats['final_casos']}/{stats['initial_casos']}",
                    delta=f"-{stats['reduction_casos_pct']:.1f}%" if stats['reduction_casos_pct'] > 0 else "Sin cambio",
                    delta_color="inverse"
                )
                
                # Métricas de epizootias
                st.sidebar.metric(
                    "🐒 Epizootias Filtradas", 
                    f"{stats['final_epizootias']}/{stats['initial_epizootias']}",
                    delta=f"-{stats['reduction_epi_pct']:.1f}%" if stats['reduction_epi_pct'] > 0 else "Sin cambio",
                    delta_color="inverse"
                )
                
                # Lista de filtros aplicados
                if stats["filtros_aplicados"]:
                    st.sidebar.markdown("**🔍 Filtros Aplicados:**")
                    for filtro in stats["filtros_aplicados"][:4]:  # Máximo 4
                        st.sidebar.caption(f"• {filtro}")
                    
                    if len(stats["filtros_aplicados"]) > 4:
                        st.sidebar.caption(f"... y {len(stats['filtros_aplicados']) - 4} más")
