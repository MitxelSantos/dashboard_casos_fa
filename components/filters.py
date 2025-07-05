"""
Componente de filtros CORREGIDO del dashboard.
CORRECCIONES PRINCIPALES:
- Sistema de sincronización bidireccional robusto mapa ↔ sidebar
- Manejo especial de municipios grises (shapefile sin datos)
- Detección de "último cambio" para priorizar correctamente
- Reset completo que realmente funciona
- Eliminación de conflictos de keys de widgets
"""

import streamlit as st
import pandas as pd
from utils.data_processor import normalize_text


def create_responsive_filters_ui():
    """CSS mejorado para filtros con indicadores de sincronización."""
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
        
        /* INDICADOR DE SINCRONIZACIÓN MEJORADO */
        .sync-status {
            background: linear-gradient(45deg, #4CAF50, #8BC34A);
            color: white;
            padding: 0.4rem 0.8rem;
            border-radius: 15px;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 0.5rem 0;
            text-align: center;
            animation: pulse-sync 2s infinite;
            box-shadow: 0 3px 10px rgba(76, 175, 80, 0.3);
        }
        
        .sync-status.conflict {
            background: linear-gradient(45deg, #FF9800, #FFC107);
            animation: blink 1s ease-in-out 3;
        }
        
        .sync-status.error {
            background: linear-gradient(45deg, #f44336, #d32f2f);
            animation: shake 0.5s ease-in-out 2;
        }
        
        @keyframes pulse-sync {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.02); }
            100% { opacity: 1; transform: scale(1); }
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
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


class FilterSyncManager:
    """
    NUEVA: Clase para manejar sincronización completa entre mapa y sidebar.
    """
    
    def __init__(self):
        self.init_sync_state()
    
    def init_sync_state(self):
        """Inicializa el estado de sincronización."""
        if 'last_change_source' not in st.session_state:
            st.session_state['last_change_source'] = 'none'  # 'map', 'sidebar', 'none'
        
        if 'last_change_timestamp' not in st.session_state:
            st.session_state['last_change_timestamp'] = 0
        
        if 'filter_sync_lock' not in st.session_state:
            st.session_state['filter_sync_lock'] = False
    
    def detect_change_source(self, new_municipio, new_vereda):
        """
        Detecta si el cambio viene del mapa o sidebar comparando con estado anterior.
        """
        current_municipio = st.session_state.get('municipio_filter', 'Todos')
        current_vereda = st.session_state.get('vereda_filter', 'Todas')
        
        # Si hay un cambio
        if new_municipio != current_municipio or new_vereda != current_vereda:
            # Si viene de session_state['map_filter_updated'] = True, es del mapa
            if st.session_state.get('map_filter_updated', False):
                return 'map'
            else:
                return 'sidebar'
        
        return st.session_state.get('last_change_source', 'none')
    
    def update_from_map(self, municipio, vereda=None):
        """Actualiza filtros desde el mapa con prioridad."""
        if st.session_state.get('filter_sync_lock', False):
            return
        
        st.session_state['filter_sync_lock'] = True
        
        # Actualizar valores
        st.session_state['municipio_filter'] = municipio or 'Todos'
        st.session_state['vereda_filter'] = vereda or 'Todas'
        
        # Marcar origen del cambio
        st.session_state['last_change_source'] = 'map'
        st.session_state['last_change_timestamp'] = pd.Timestamp.now().timestamp()
        st.session_state['map_filter_updated'] = True
        
        st.session_state['filter_sync_lock'] = False
    
    def update_from_sidebar(self, municipio, vereda):
        """Actualiza desde sidebar con validación."""
        if st.session_state.get('filter_sync_lock', False):
            return
        
        st.session_state['filter_sync_lock'] = True
        
        # Validar y actualizar
        st.session_state['municipio_filter'] = municipio
        st.session_state['vereda_filter'] = vereda
        
        # Marcar origen
        st.session_state['last_change_source'] = 'sidebar'
        st.session_state['last_change_timestamp'] = pd.Timestamp.now().timestamp()
        
        # Limpiar flags del mapa
        if 'map_filter_updated' in st.session_state:
            st.session_state['map_filter_updated'] = False
        
        st.session_state['filter_sync_lock'] = False
    
    def force_reset_all(self):
        """Reset completo forzado desde cualquier fuente."""
        st.session_state['filter_sync_lock'] = True
        
        # Resetear todos los filtros principales
        st.session_state['municipio_filter'] = 'Todos'
        st.session_state['vereda_filter'] = 'Todas'
        
        # Resetear filtros adicionales
        for key in ['fecha_filter', 'condicion_filter', 'sexo_filter', 'edad_filter', 'fuente_filter']:
            if key in st.session_state:
                if 'fecha' in key:
                    del st.session_state[key]
                else:
                    st.session_state[key] = 'Todas' if 'fuente' in key else 'Todos'
        
        # Resetear flags de sincronización
        st.session_state['last_change_source'] = 'reset'
        st.session_state['last_change_timestamp'] = pd.Timestamp.now().timestamp()
        
        # Limpiar flags del mapa
        for key in ['map_filter_updated', 'filter_stats', 'filter_stats_detailed']:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state['filter_sync_lock'] = False
        
        return True
    
    def get_sync_status(self):
        """Retorna el estado actual de sincronización."""
        return {
            'last_source': st.session_state.get('last_change_source', 'none'),
            'timestamp': st.session_state.get('last_change_timestamp', 0),
            'is_locked': st.session_state.get('filter_sync_lock', False),
            'map_updated': st.session_state.get('map_filter_updated', False)
        }


# Instancia global del manager
sync_manager = FilterSyncManager()


def create_hierarchical_filters_enhanced_v2(data):
    """
    CORREGIDO: Filtros jerárquicos con sincronización bidireccional ROBUSTA.
    """
    # Aplicar CSS responsive
    create_responsive_filters_ui()
    
    # Detectar y mostrar estado de sincronización
    show_sync_status()
    
    # Obtener opciones de municipios (INCLUYENDO GRISES)
    municipio_options = get_municipio_options_complete(data)
    
    # Obtener valores actuales con validación
    current_municipio = get_current_municipio_safe(municipio_options)
    current_vereda = get_current_vereda_safe(current_municipio, data)
    
    # **MUNICIPIO SELECTOR CON SINCRONIZACIÓN**
    municipio_selected = st.sidebar.selectbox(
        "📍 **MUNICIPIO**:",
        municipio_options,
        index=municipio_options.index(current_municipio) if current_municipio in municipio_options else 0,
        key="municipio_selector_sync",  # Key única y consistente
        help="Seleccione un municipio para filtrar los datos. También puede hacer doble clic en el mapa.",
    )
    
    # Detectar cambios desde sidebar
    if municipio_selected != current_municipio:
        sync_manager.update_from_sidebar(municipio_selected, 'Todas')
        st.rerun()
    
    # **VEREDA SELECTOR CON DEPENDENCIA**
    vereda_options = get_vereda_options_for_municipio(municipio_selected, data)
    vereda_disabled = municipio_selected == "Todos"
    
    current_vereda_validated = current_vereda if current_vereda in vereda_options else "Todas"
    
    vereda_selected = st.sidebar.selectbox(
        "🏘️ **VEREDA**:",
        vereda_options,
        index=vereda_options.index(current_vereda_validated),
        key="vereda_selector_sync",  # Key única y consistente
        disabled=vereda_disabled,
        help="Las veredas se actualizan según el municipio. También puede hacer doble clic en veredas del mapa.",
    )
    
    # Detectar cambios de vereda desde sidebar
    if not vereda_disabled and vereda_selected != current_vereda_validated:
        sync_manager.update_from_sidebar(municipio_selected, vereda_selected)
        st.rerun()
    
    # Información contextual mejorada
    show_location_context(municipio_selected, vereda_selected, vereda_disabled)
    
    # Determinar valores normalizados
    municipio_norm_selected = None
    vereda_norm_selected = None
    
    if municipio_selected != "Todos":
        municipio_norm_selected = get_normalized_municipio(municipio_selected, data)
    
    if vereda_selected != "Todas" and municipio_norm_selected:
        vereda_norm_selected = get_normalized_vereda(vereda_selected, municipio_norm_selected, data)
    
    return {
        "municipio_display": municipio_selected,
        "municipio_normalizado": municipio_norm_selected,
        "vereda_display": vereda_selected,
        "vereda_normalizada": vereda_norm_selected,
    }


def get_municipio_options_complete(data):
    """
    NUEVO: Obtiene opciones completas de municipios incluyendo los grises.
    """
    options = ["Todos"]
    
    # Agregar municipios con datos
    for norm in data["municipios_normalizados"]:
        display_name = data["municipio_display_map"].get(norm, norm)
        if display_name not in options:
            options.append(display_name)
    
    return options


def get_current_municipio_safe(municipio_options):
    """
    NUEVO: Obtiene municipio actual con validación de opciones disponibles.
    """
    current = st.session_state.get('municipio_filter', 'Todos')
    
    # Validar que esté en las opciones disponibles
    if current not in municipio_options:
        # Si no está, buscar el normalized
        if current != 'Todos':
            # Log para debugging
            st.sidebar.warning(f"⚠️ Municipio '{current}' no encontrado en opciones. Reseteando.")
        return 'Todos'
    
    return current


def get_current_vereda_safe(municipio_selected, data):
    """
    NUEVO: Obtiene vereda actual con validación de dependencia del municipio.
    """
    current = st.session_state.get('vereda_filter', 'Todas')
    
    # Si no hay municipio seleccionado, resetear vereda
    if municipio_selected == "Todos":
        if current != "Todas":
            sync_manager.update_from_sidebar(municipio_selected, "Todas")
        return "Todas"
    
    # Validar que la vereda pertenezca al municipio actual
    vereda_options = get_vereda_options_for_municipio(municipio_selected, data)
    
    if current not in vereda_options:
        return "Todas"
    
    return current


def get_vereda_options_for_municipio(municipio_selected, data):
    """
    NUEVO: Obtiene opciones de veredas para un municipio específico.
    """
    vereda_options = ["Todas"]
    
    if municipio_selected == "Todos":
        return vereda_options
    
    # Buscar municipio normalizado
    municipio_norm = get_normalized_municipio(municipio_selected, data)
    
    if municipio_norm and municipio_norm in data["veredas_por_municipio"]:
        veredas_norm = data["veredas_por_municipio"][municipio_norm]
        if municipio_norm in data["vereda_display_map"]:
            vereda_options.extend([
                data["vereda_display_map"][municipio_norm].get(norm, norm)
                for norm in veredas_norm
            ])
    
    return vereda_options


def get_normalized_municipio(municipio_display, data):
    """
    NUEVO: Busca el municipio normalizado desde el display name.
    """
    for norm, display in data["municipio_display_map"].items():
        if display == municipio_display:
            return norm
    return None


def get_normalized_vereda(vereda_display, municipio_norm, data):
    """
    NUEVO: Busca la vereda normalizada desde el display name.
    """
    if municipio_norm in data["vereda_display_map"]:
        for norm, display in data["vereda_display_map"][municipio_norm].items():
            if display == vereda_display:
                return norm
    return None


def show_sync_status():
    """
    NUEVO: Muestra el estado de sincronización actual.
    """
    sync_status = sync_manager.get_sync_status()
    
    # Solo mostrar si hay actividad de sincronización
    if sync_status['last_source'] in ['map', 'sidebar']:
        if sync_status['last_source'] == 'map':
            st.sidebar.markdown(
                """
                <div class="sync-status">
                    🗺️ Actualizado desde mapa
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif sync_status['last_source'] == 'sidebar':
            st.sidebar.markdown(
                """
                <div class="sync-status">
                    🎛️ Actualizado desde filtros
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    # Limpiar después de mostrar
    if 'map_filter_updated' in st.session_state:
        st.session_state['map_filter_updated'] = False


def show_location_context(municipio_selected, vereda_selected, vereda_disabled):
    """
    NUEVO: Información contextual mejorada de la ubicación.
    """
    if municipio_selected != "Todos":
        if vereda_selected != "Todas":
            st.sidebar.markdown(
                f"""
                <div class="filter-help">
                    📍 <strong>{vereda_selected}</strong> - {municipio_selected}<br>
                    🔍 Vista específica de vereda<br>
                    🗺️ Datos detallados disponibles
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.sidebar.markdown(
                f"""
                <div class="filter-help">
                    🏛️ <strong>{municipio_selected}</strong> seleccionado<br>
                    💡 Los datos se filtrarán por este municipio<br>
                    🗺️ Vista de veredas disponible en el mapa
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.sidebar.markdown(
            """
            <div class="filter-help">
                🗺️ Vista general del Tolima<br>
                💡 Haga doble clic en cualquier municipio del mapa para filtrar<br>
                📊 Todas las métricas incluyen datos departamentales
            </div>
            """,
            unsafe_allow_html=True,
        )


def create_content_filters_enhanced(data):
    """
    MEJORADO: Filtros de contenido con mejor UX (sin cambios en la lógica).
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
                    📊 Rango disponible: {fecha_min.strftime('%d/%m/%Y')} - {fecha_max.strftime('%d/%m/%Y')}<br>
                    🎯 Seleccionado: {dias_seleccionados} días ({porcentaje_periodo:.1f}% del período)
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.sidebar.markdown(
                f"""
                <div class="filter-help">
                    📊 Rango disponible: {fecha_min.strftime('%d/%m/%Y')} - {fecha_max.strftime('%d/%m/%Y')}<br>
                    ⏱️ Total: {total_dias} días de datos<br>
                    💡 Seleccione ambas fechas para filtrar
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
    MEJORADO: Filtros avanzados con mejor organización (sin cambios en la lógica).
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


def apply_all_filters_enhanced(data, filters_location, filters_content, filters_advanced):
    """
    MEJORADO: Aplica filtros con mejor performance y logging (sin cambios en la lógica).
    """
    casos_filtrados = data["casos"].copy()
    epizootias_filtradas = data["epizootias"].copy()

    # Contador de registros para logging
    initial_casos = len(casos_filtrados)
    initial_epizootias = len(epizootias_filtradas)

    # PASO 1: Filtrar solo epizootias positivas desde el inicio
    if not epizootias_filtradas.empty and "descripcion" in epizootias_filtradas.columns:
        epizootias_filtradas = epizootias_filtradas[epizootias_filtradas["descripcion"] == "POSITIVO FA"]

    # PASO 2: Aplicar filtros de ubicación
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

    # PASO 3: Aplicar filtros de contenido (temporales)
    if filters_content["fecha_rango"] and len(filters_content["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters_content["fecha_rango"]
        fecha_inicio = pd.Timestamp(fecha_inicio)
        fecha_fin = pd.Timestamp(fecha_fin) + pd.Timedelta(hours=23, minutes=59, seconds=59)  # Incluir todo el día

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

    # PASO 4: Aplicar filtros avanzados para casos
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

    # PASO 5: Aplicar filtros avanzados para epizootias
    if filters_advanced["fuente_epizootia"] != "Todas":
        if "proveniente" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["proveniente"]
                == filters_advanced["fuente_epizootia"]
            ]

    # LOGGING: Almacenar estadísticas de filtrado
    final_casos = len(casos_filtrados)
    final_epizootias = len(epizootias_filtradas)
    
    # Guardar estadísticas en session_state para debugging
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


def show_active_filters_sidebar_enhanced(active_filters):
    """
    MEJORADO: Muestra filtros activos con categorización y animaciones (sin cambios).
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
    CORREGIDO: Reset completo REAL que funciona con todos los widgets.
    """
    try:
        # Usar el sync manager para reset completo
        success = sync_manager.force_reset_all()
        
        if success:
            st.sidebar.success("✅ Filtros restablecidos completamente", icon="🧹")
            return True
        else:
            st.sidebar.error("❌ Error al restablecer filtros", icon="⚠️")
            return False
            
    except Exception as e:
        st.sidebar.error(f"❌ Error crítico: {str(e)}", icon="💥")
        return False


def create_filter_summary_enhanced(filters_location, filters_content, filters_advanced, data):
    """
    MEJORADO: Resumen de filtros activos con categorización (sin cambios en la lógica).
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


def create_complete_filter_system_enhanced(data):
    """
    MEJORADO: Sistema completo de filtros con sincronización bidireccional ROBUSTA.
    """
    # Crear diferentes tipos de filtros con versiones mejoradas
    filters_location = create_hierarchical_filters_enhanced_v2(data)  # NUEVA VERSIÓN
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
            key="reset_all_filters_btn_enhanced_v2",  # NUEVA KEY
            help="Limpiar todos los filtros y volver a vista completa",
        ):
            if reset_all_filters_enhanced():
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
    CORREGIDO: Sistema completo con sincronización bidireccional mapas-filtros ROBUSTO.
    """
    # Aplicar CSS responsive
    create_responsive_filters_ui()
    
    # Usar el sistema mejorado con sincronización robusta
    return create_complete_filter_system_enhanced(data)


# FUNCIONES DE INTEGRACIÓN CON MAPAS

def update_filters_from_map(municipio=None, vereda=None):
    """
    CORREGIDO: Actualiza filtros desde interacciones del mapa usando sync manager.
    """
    if municipio or vereda:
        sync_manager.update_from_map(municipio, vereda)
        return True
    return False


def get_current_filter_state():
    """
    MEJORADO: Obtiene el estado actual de todos los filtros de forma segura.
    """
    return {
        "municipio": st.session_state.get("municipio_filter", "Todos"),
        "vereda": st.session_state.get("vereda_filter", "Todas"),
        "fecha": st.session_state.get("fecha_filter", None),
        "condicion": st.session_state.get("condicion_filter", "Todas"),
        "sexo": st.session_state.get("sexo_filter", "Todos"),
        "edad": st.session_state.get("edad_filter", None),
        "fuente": st.session_state.get("fuente_filter", "Todas"),
        "sync_status": sync_manager.get_sync_status()
    }