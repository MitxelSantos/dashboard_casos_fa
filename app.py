"""
Aplicación principal ACTUALIZADA del Dashboard de Fiebre Amarilla v3.1
NUEVAS FUNCIONALIDADES:
- Vista de mapas con TODAS las tarjetas informativas trasladadas
- Mapas fijos sin zoom/panning, limitados al Tolima
- Interacciones: 1 clic = popup, 2 clics = filtrar automáticamente
- Sincronización bidireccional entre mapas y filtros
- Vista de información principal simplificada (solo gráficos y tablas)
"""

import os
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import unicodedata
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FiebreAmarilla-Dashboard-v3.1")

# Deshabilitar detección automática de páginas de Streamlit
os.environ["STREAMLIT_PAGES_ENABLED"] = "false"

# Definir rutas
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Asegurar que las carpetas existan
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# Agregar rutas al path para importar módulos
import sys
sys.path.insert(0, str(ROOT_DIR))

# Importar configuraciones y utilidades
from config.colors import COLORS
from config.settings import DASHBOARD_CONFIG

# Importar utilidades responsive
try:
    from config.responsive import init_responsive_dashboard
    from utils.responsive import init_responsive_utils, create_responsive_metric_cards
    RESPONSIVE_AVAILABLE = True
except ImportError:
    RESPONSIVE_AVAILABLE = False
    logger.warning("Módulos responsive no disponibles, usando versión básica")

from utils.data_processor import (
    normalize_text,
    excel_date_to_datetime,
    capitalize_names,
)

# NUEVA: Importar utilidades de interacciones de mapa
try:
    from utils.map_interactions import (
        process_map_interaction_complete,
        create_interaction_feedback_ui,
        get_interaction_manager,
        get_bounds_manager
    )
    MAP_INTERACTIONS_AVAILABLE = True
except ImportError:
    MAP_INTERACTIONS_AVAILABLE = False
    logger.warning("Utilidades de interacciones de mapa no disponibles")

# Lista de vistas a importar
vista_modules = ["mapas", "tablas", "comparativo"]
vistas_modules = {}


def import_vista_module(module_name):
    """
    Importa un módulo de vista específico con manejo de errores mejorado.
    """
    try:
        module = __import__(f"vistas.{module_name}", fromlist=[module_name])
        logger.info(f"✅ Módulo {module_name} importado correctamente")
        return module
    except ImportError as e:
        logger.error(f"❌ No se pudo importar el módulo {module_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Error inesperado importando {module_name}: {str(e)}")
        return None


# Importar módulos de vistas
for module_name in vista_modules:
    vistas_modules[module_name] = import_vista_module(module_name)


def load_new_datasets():
    """
    ACTUALIZADA: Carga los datasets y filtra solo epizootias positivas desde el inicio.
    NUEVA: Inicialización mejorada para soporte de mapas interactivos.
    """
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("🔄 Inicializando carga de datos v3.1...")

        # ==================== CONFIGURACIÓN DE RUTAS ====================
        casos_filename = "BD_positivos.xlsx"
        epizootias_filename = "Información_Datos_FA.xlsx"

        # Rutas primarias (carpeta data) - RECOMENDADA
        data_casos_path = DATA_DIR / casos_filename
        data_epizootias_path = DATA_DIR / epizootias_filename

        # Rutas de respaldo (directorio raíz)
        root_casos_path = ROOT_DIR / casos_filename
        root_epizootias_path = ROOT_DIR / epizootias_filename

        progress_bar.progress(10)
        status_text.text("📁 Verificando disponibilidad de archivos...")

        # ==================== ESTRATEGIA DE CARGA INTELIGENTE ====================
        casos_df = None
        epizootias_df = None
        data_source = None

        # Estrategia 1: Intentar cargar desde carpeta data/
        if data_casos_path.exists() and data_epizootias_path.exists():
            try:
                status_text.text("📂 Cargando desde carpeta data/...")
                casos_df = pd.read_excel(
                    data_casos_path, sheet_name="ACUMU", engine="openpyxl"
                )
                epizootias_df = pd.read_excel(
                    data_epizootias_path, sheet_name="Base de Datos", engine="openpyxl"
                )
                data_source = "data_folder"
                logger.info("✅ Datos cargados exitosamente desde carpeta data/")
            except Exception as e:
                logger.warning(f"⚠️ Error al cargar desde carpeta data/: {str(e)}")
                casos_df = None
                epizootias_df = None

        # Estrategia 2: Intentar cargar desde directorio raíz
        if (
            casos_df is None
            and root_casos_path.exists()
            and root_epizootias_path.exists()
        ):
            try:
                status_text.text("📁 Cargando desde directorio raíz...")
                casos_df = pd.read_excel(
                    root_casos_path, sheet_name="ACUMU", engine="openpyxl"
                )
                epizootias_df = pd.read_excel(
                    root_epizootias_path, sheet_name="Base de Datos", engine="openpyxl"
                )
                data_source = "root_folder"
                logger.info("✅ Datos cargados exitosamente desde directorio raíz")
            except Exception as e:
                logger.warning(f"⚠️ Error al cargar desde directorio raíz: {str(e)}")
                casos_df = None
                epizootias_df = None

        # Estrategia 3: Intentar cargar desde Google Drive (FALLBACK)
        if casos_df is None:
            try:
                from gdrive_utils import (
                    get_file_from_drive,
                    check_google_drive_availability,
                )

                if check_google_drive_availability():
                    status_text.text("☁️ Intentando cargar desde Google Drive...")
                    progress_bar.progress(20)

                    if hasattr(st.secrets, "drive_files"):
                        drive_files = st.secrets.drive_files

                        # Cargar casos desde Google Drive
                        if "casos_confirmados" in drive_files:
                            casos_path = get_file_from_drive(
                                drive_files["casos_confirmados"], casos_filename
                            )
                            if casos_path and Path(casos_path).exists():
                                casos_df = pd.read_excel(
                                    casos_path, sheet_name="ACUMU", engine="openpyxl"
                                )
                                logger.info("✅ Casos cargados desde Google Drive")

                        # Cargar epizootias desde Google Drive
                        if "epizootias" in drive_files:
                            epi_path = get_file_from_drive(
                                drive_files["epizootias"], epizootias_filename
                            )
                            if epi_path and Path(epi_path).exists():
                                epizootias_df = pd.read_excel(
                                    epi_path,
                                    sheet_name="Base de Datos",
                                    engine="openpyxl",
                                )
                                logger.info("✅ Epizootias cargadas desde Google Drive")

                        if casos_df is not None and epizootias_df is not None:
                            data_source = "google_drive"

            except ImportError:
                pass
            except Exception as e:
                logger.error(f"❌ Error al cargar desde Google Drive: {str(e)}")

        # ==================== VALIDACIÓN Y MENSAJE DE ERROR ====================
        if casos_df is None or epizootias_df is None:
            st.error("❌ No se pudieron cargar los archivos de datos")
            return create_empty_data_structure()

        progress_bar.progress(30)
        status_text.text("🔧 Procesando datos para mapas interactivos...")

        # ==================== PROCESAMIENTO DE DATOS MEJORADO ====================
        # Limpiar datos de casos
        casos_df = casos_df.dropna(how="all")

        # Mapear columnas de casos
        casos_columns_map = {
            "edad_": "edad",
            "sexo_": "sexo",
            "vereda_": "vereda",
            "nmun_proce": "municipio",
            "cod_ase_": "eps",
            "Condición Final": "condicion_final",
            "Inicio de sintomas": "fecha_inicio_sintomas",
        }

        # Renombrar columnas existentes
        existing_casos_columns = {
            k: v for k, v in casos_columns_map.items() if k in casos_df.columns
        }
        casos_df = casos_df.rename(columns=existing_casos_columns)

        # Normalizar municipios y veredas en casos
        if "municipio" in casos_df.columns:
            casos_df["municipio_normalizado"] = casos_df["municipio"].apply(
                normalize_text
            )
            casos_df["municipio"] = casos_df["municipio"].apply(capitalize_names)
        if "vereda" in casos_df.columns:
            casos_df["vereda_normalizada"] = casos_df["vereda"].apply(normalize_text)
            casos_df["vereda"] = casos_df["vereda"].apply(capitalize_names)

        # Convertir fechas de casos
        if "fecha_inicio_sintomas" in casos_df.columns:
            casos_df["fecha_inicio_sintomas"] = casos_df["fecha_inicio_sintomas"].apply(
                excel_date_to_datetime
            )

        progress_bar.progress(50)
        status_text.text("🔴 Procesando epizootias y filtrando solo positivas...")

        # ==================== PROCESAR EPIZOOTIAS Y FILTRAR SOLO POSITIVAS ====================
        # Limpiar datos de epizootias
        epizootias_df = epizootias_df.dropna(how="all")

        # Mapear columnas de epizootias
        epizootias_columns_map = {
            "MUNICIPIO": "municipio",
            "VEREDA": "vereda",
            "FECHA RECOLECCIÓN ": "fecha_recoleccion",
            "PROVENIENTE ": "proveniente",
            "DESCRIPCIÓN": "descripcion",
        }

        # Renombrar columnas existentes
        existing_epi_columns = {
            k: v
            for k, v in epizootias_columns_map.items()
            if k in epizootias_df.columns
        }
        epizootias_df = epizootias_df.rename(columns=existing_epi_columns)

        # CAMBIO IMPORTANTE: Filtrar solo epizootias positivas desde el inicio
        if "descripcion" in epizootias_df.columns:
            # Normalizar descripciones primero
            epizootias_df["descripcion"] = epizootias_df["descripcion"].str.upper().str.strip()
            
            # Filtrar solo las positivas
            total_original = len(epizootias_df)
            epizootias_df = epizootias_df[epizootias_df["descripcion"] == "POSITIVO FA"]
            total_positivas = len(epizootias_df)
            
            logger.info(f"🔴 Filtro aplicado: {total_positivas} epizootias positivas de {total_original} totales")
            status_text.text(f"🔴 Filtradas {total_positivas} epizootias positivas de {total_original} totales")

        # Normalizar municipios y veredas en epizootias (solo las positivas)
        if "municipio" in epizootias_df.columns:
            epizootias_df["municipio_normalizado"] = epizootias_df["municipio"].apply(
                normalize_text
            )
            epizootias_df["municipio"] = epizootias_df["municipio"].apply(
                capitalize_names
            )
        if "vereda" in epizootias_df.columns:
            epizootias_df["vereda_normalizada"] = epizootias_df["vereda"].apply(
                normalize_text
            )
            epizootias_df["vereda"] = epizootias_df["vereda"].apply(capitalize_names)

        # Convertir fechas de epizootias
        if "fecha_recoleccion" in epizootias_df.columns:
            epizootias_df["fecha_recoleccion"] = epizootias_df[
                "fecha_recoleccion"
            ].apply(excel_date_to_datetime)

        progress_bar.progress(70)
        status_text.text("🗺️ Creando mapeos maestros para mapas interactivos...")

        # ==================== CREAR MAPEOS MAESTROS MEJORADOS ====================

        # Obtener todos los municipios únicos (normalizados)
        municipios_casos = set(casos_df["municipio_normalizado"].dropna())
        municipios_epizootias = set(epizootias_df["municipio_normalizado"].dropna())
        municipios_normalizados = sorted(municipios_casos.union(municipios_epizootias))

        # Crear mapeo de municipios (normalizado -> original más común)
        municipio_display_map = {}
        for municipio_norm in municipios_normalizados:
            # Buscar la versión original más común para mostrar
            opciones_casos = (
                casos_df[casos_df["municipio_normalizado"] == municipio_norm][
                    "municipio"
                ]
                .dropna()
                .unique()
            )
            opciones_epi = (
                epizootias_df[epizootias_df["municipio_normalizado"] == municipio_norm][
                    "municipio"
                ]
                .dropna()
                .unique()
            )

            todas_opciones = list(opciones_casos) + list(opciones_epi)
            if todas_opciones:
                municipio_display_map[municipio_norm] = todas_opciones[0]
            else:
                municipio_display_map[municipio_norm] = municipio_norm

        # Crear diccionario de veredas por municipio (normalizado)
        veredas_por_municipio = {}
        for municipio_norm in municipios_normalizados:
            # Obtener veredas de casos
            veredas_casos = (
                casos_df[casos_df["municipio_normalizado"] == municipio_norm][
                    "vereda_normalizada"
                ]
                .dropna()
                .unique()
            )
            # Obtener veredas de epizootias (solo positivas)
            veredas_epi = (
                epizootias_df[epizootias_df["municipio_normalizado"] == municipio_norm][
                    "vereda_normalizada"
                ]
                .dropna()
                .unique()
            )

            # Combinar y ordenar
            todas_veredas = sorted(set(list(veredas_casos) + list(veredas_epi)))
            veredas_por_municipio[municipio_norm] = todas_veredas

        # Crear mapeo de veredas para display
        vereda_display_map = {}
        for municipio_norm in municipios_normalizados:
            vereda_display_map[municipio_norm] = {}
            for vereda_norm in veredas_por_municipio[municipio_norm]:
                # Buscar versión original de la vereda
                opciones_casos = (
                    casos_df[
                        (casos_df["municipio_normalizado"] == municipio_norm)
                        & (casos_df["vereda_normalizada"] == vereda_norm)
                    ]["vereda"]
                    .dropna()
                    .unique()
                )

                opciones_epi = (
                    epizootias_df[
                        (epizootias_df["municipio_normalizado"] == municipio_norm)
                        & (epizootias_df["vereda_normalizada"] == vereda_norm)
                    ]["vereda"]
                    .dropna()
                    .unique()
                )

                todas_opciones = list(opciones_casos) + list(opciones_epi)
                if todas_opciones:
                    vereda_display_map[municipio_norm][vereda_norm] = todas_opciones[0]
                else:
                    vereda_display_map[municipio_norm][vereda_norm] = vereda_norm

        progress_bar.progress(90)
        status_text.text("📊 Finalizando carga con mapeos de interacción...")

        # ==================== MAPEOS DE VALORES ACTUALIZADOS ====================

        # Mapeo de condición final
        condicion_map = {
            "Fallecido": {
                "color": COLORS["danger"],
                "icon": "⚰️",
                "categoria": "Crítico",
            },
            "Vivo": {"color": COLORS["success"], "icon": "💚", "categoria": "Bueno"},
        }

        # ACTUALIZADO: Mapeo de descripción (solo positivas ahora)
        descripcion_map = {
            "POSITIVO FA": {
                "color": COLORS["danger"],
                "icon": "🔴",
                "categoria": "Positivo",
                "descripcion": "Confirma circulación viral activa"
            },
        }

        progress_bar.progress(100)

        # Limpiar elementos de UI con delay para legibilidad
        import time
        time.sleep(1.5)
        status_text.empty()
        progress_bar.empty()

        # NUEVA: Inicializar sistema de interacciones de mapa si está disponible
        if MAP_INTERACTIONS_AVAILABLE:
            interaction_manager = get_interaction_manager()
            bounds_manager = get_bounds_manager()
            logger.info("✅ Sistema de interacciones de mapa inicializado")

        # Log final con estadísticas ACTUALIZADAS
        logger.info(f"✅ Datos cargados exitosamente desde: {data_source}")
        logger.info(f"📊 Casos cargados: {len(casos_df)}")
        logger.info(f"🔴 Epizootias POSITIVAS cargadas: {len(epizootias_df)}")
        logger.info(f"🗺️ Municipios únicos: {len(municipios_normalizados)}")

        return {
            "casos": casos_df,
            "epizootias": epizootias_df,  # Ya solo contiene positivas
            "municipios_normalizados": municipios_normalizados,
            "municipio_display_map": municipio_display_map,
            "veredas_por_municipio": veredas_por_municipio,
            "vereda_display_map": vereda_display_map,
            "condicion_map": condicion_map,
            "descripcion_map": descripcion_map,
            "data_source": data_source,
        }

    except Exception as e:
        logger.error(f"💥 Error crítico al cargar los datos: {str(e)}")
        st.error(f"❌ Error crítico al cargar los datos: {str(e)}")
        return create_empty_data_structure()


def create_empty_data_structure():
    """
    NUEVA: Crea estructura de datos vacía para casos de error.
    """
    return {
        "casos": pd.DataFrame(),
        "epizootias": pd.DataFrame(),
        "municipios_normalizados": [],
        "municipio_display_map": {},
        "veredas_por_municipio": {},
        "vereda_display_map": {},
        "condicion_map": {},
        "descripcion_map": {},
        "data_source": "error",
    }


def create_filters_responsive_with_maps_enhanced(data):
    """
    NUEVA: Crea sistema de filtros MEJORADO con sincronización bidireccional completa.
    """
    # Importar el sistema de filtros mejorado
    try:
        from components.filters import create_complete_filter_system_with_maps

        # Usar el sistema completo de filtros mejorado con sincronización
        filter_result = create_complete_filter_system_with_maps(data)
        return filter_result["filters"], filter_result["data_filtered"]

    except ImportError as e:
        logger.error(f"Error importando filtros mejorados: {str(e)}")
        # Fallback al sistema básico si no está disponible
        return create_basic_fallback_filters(data)


def create_basic_fallback_filters(data):
    """
    NUEVA: Sistema de filtros básico como fallback.
    """
    st.sidebar.subheader("🔍 Filtros (Básico)")

    # Filtro de municipio básico
    municipio_options = ["Todos"] + [
        data["municipio_display_map"][norm]
        for norm in data["municipios_normalizados"]
    ]

    municipio_selected = st.sidebar.selectbox(
        "📍 Municipio:", municipio_options, key="municipio_filter"
    )

    # Determinar municipio normalizado seleccionado
    municipio_norm_selected = None
    if municipio_selected != "Todos":
        for norm, display in data["municipio_display_map"].items():
            if display == municipio_selected:
                municipio_norm_selected = norm
                break

    # Aplicar filtros básicos
    casos_filtrados = data["casos"].copy()
    epizootias_filtradas = data["epizootias"].copy()  # Ya solo son positivas

    if municipio_norm_selected:
        casos_filtrados = casos_filtrados[
            casos_filtrados["municipio_normalizado"] == municipio_norm_selected
        ]
        epizootias_filtradas = epizootias_filtradas[
            epizootias_filtradas["municipio_normalizado"] == municipio_norm_selected
        ]

    data_filtered = {
        "casos": casos_filtrados,
        "epizootias": epizootias_filtradas,
        **{k: v for k, v in data.items() if k not in ["casos", "epizootias"]},
    }

    filters = {
        "municipio_display": municipio_selected,
        "municipio_normalizado": municipio_norm_selected,
        "vereda_display": "Todas",
        "vereda_normalizada": None,
        "active_filters": (
            [f"Municipio: {municipio_selected}"]
            if municipio_selected != "Todos"
            else []
        ),
    }

    return filters, data_filtered


def configure_page_responsive():
    """
    ACTUALIZADA: Configura la página de Streamlit con máxima responsividad y soporte para mapas.
    """
    st.set_page_config(
        page_title=DASHBOARD_CONFIG["page_title"],
        page_icon=DASHBOARD_CONFIG["page_icon"],
        layout=DASHBOARD_CONFIG["layout"],
        initial_sidebar_state=DASHBOARD_CONFIG["initial_sidebar_state"],
    )

    # Inicializar configuraciones responsive
    if RESPONSIVE_AVAILABLE:
        init_responsive_dashboard()
        init_responsive_utils()

    # CSS responsive principal ACTUALIZADO para v3.1
    st.markdown(
        f"""
        <style>
        /* Import responsive configuration */
        :root {{
            --primary-color: {COLORS['primary']};
            --secondary-color: {COLORS['secondary']};
            --accent-color: {COLORS['accent']};
            --success-color: {COLORS['success']};
            --warning-color: {COLORS['warning']};
            --danger-color: {COLORS['danger']};
            --info-color: {COLORS['info']};
        }}
        
        /* NUEVO: Títulos principales v3.1 */
        .main-title {{
            color: var(--primary-color);
            font-size: clamp(1.8rem, 6vw, 2.8rem);
            font-weight: 700;
            margin-bottom: clamp(1rem, 3vw, 2rem);
            text-align: center;
            padding-bottom: clamp(0.5rem, 2vw, 1rem);
            border-bottom: 3px solid var(--secondary-color);
            line-height: 1.2;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        /* NUEVO: Contenedor principal responsive para mapas */
        .block-container {{
            padding-top: clamp(1rem, 3vw, 2rem) !important;
            padding-bottom: clamp(1rem, 3vw, 2rem) !important;
            padding-left: clamp(0.5rem, 2vw, 1.5rem) !important;
            padding-right: clamp(0.5rem, 2vw, 1.5rem) !important;
            max-width: 100% !important;
        }}
        
        /* MEJORADO: Métricas responsive con soporte para mapas */
        [data-testid="metric-container"] {{
            background: linear-gradient(135deg, white 0%, #f8f9fa 100%) !important;
            border-radius: 12px !important;
            padding: clamp(1rem, 3vw, 1.5rem) !important;
            text-align: center !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
            border-top: 4px solid var(--primary-color) !important;
            transition: all 0.3s ease !important;
            margin-bottom: clamp(0.5rem, 2vw, 1rem) !important;
            min-height: 120px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
        }}
        
        [data-testid="metric-container"]:hover {{
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
        }}
        
        [data-testid="metric-container"] [data-testid="metric-value"] {{
            font-size: clamp(1.5rem, 5vw, 2.2rem) !important;
            font-weight: 700 !important;
            color: var(--primary-color) !important;
        }}
        
        [data-testid="metric-container"] [data-testid="metric-label"] {{
            font-size: clamp(0.8rem, 2vw, 0.95rem) !important;
            font-weight: 600 !important;
            color: #666 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }}
        
        /* NUEVO: Pestañas responsive mejoradas para v3.1 */
        .stTabs [data-baseweb="tab-list"] {{
            gap: clamp(0.25rem, 1vw, 0.75rem) !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            white-space: nowrap !important;
            padding: 0 0 0.75rem 0 !important;
            margin: 0 0 1.5rem 0 !important;
            -webkit-overflow-scrolling: touch !important;
            scrollbar-width: thin !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            font-size: clamp(0.8rem, 2vw, 0.95rem) !important;
            padding: clamp(0.6rem, 2vw, 0.8rem) clamp(1rem, 3vw, 1.2rem) !important;
            border-radius: 8px 8px 0 0 !important;
            white-space: nowrap !important;
            min-width: max-content !important;
            transition: all 0.3s ease !important;
            border: 2px solid #dee2e6 !important;
            border-bottom: none !important;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
            font-weight: 600 !important;
        }}
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%) !important;
            color: white !important;
            border-color: var(--primary-color) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(125, 15, 43, 0.3) !important;
        }}
        
        .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {{
            background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        }}
        
        /* NUEVO: Columnas responsive mejoradas para layout de mapas */
        .css-1r6slb0 {{
            flex: 1 1 auto !important;
            min-width: 200px !important;
            margin-bottom: clamp(0.75rem, 2vw, 1rem) !important;
        }}
        
        /* NUEVO: Optimizaciones específicas para vista de mapas */
        @media (max-width: 768px) {{
            /* En móviles, apilar columnas verticalmente */
            .css-1r6slb0 {{
                flex: 1 1 100% !important;
                min-width: 100% !important;
                margin-bottom: 1rem !important;
            }}
            
            /* Ajustar pestañas para móvil */
            .stTabs [data-baseweb="tab"] {{
                font-size: 0.75rem !important;
                padding: 0.5rem 0.8rem !important;
            }}
            
            /* Métricas más compactas en móvil */
            [data-testid="metric-container"] {{
                margin-bottom: 0.75rem !important;
                min-height: 100px !important;
            }}
        }}
        
        /* NUEVO: Tablet adjustments para mapas */
        @media (min-width: 769px) and (max-width: 1024px) {{
            .css-1r6slb0 {{
                flex: 1 1 45% !important;
                min-width: 300px !important;
            }}
        }}
        
        /* NUEVO: Desktop optimizations para mapas */
        @media (min-width: 1025px) {{
            .css-1r6slb0 {{
                flex: 1 1 auto !important;
                min-width: 250px !important;
            }}
        }}
        
        /* NUEVO: Estilos para indicadores de sincronización */
        .sync-indicator {{
            background: linear-gradient(45deg, var(--success-color), var(--info-color));
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            margin: 0.5rem 0;
            text-align: center;
            animation: pulse-sync 2s infinite;
        }}
        
        @keyframes pulse-sync {{
            0% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.8; transform: scale(1.02); }}
            100% {{ opacity: 1; transform: scale(1); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def handle_map_interactions(data_filtered, filters, colors):
    """
    NUEVA: Maneja las interacciones del mapa si están disponibles.
    """
    if not MAP_INTERACTIONS_AVAILABLE:
        return
    
    # Verificar si hay datos de interacción del mapa en session_state
    if 'map_interaction_data' in st.session_state:
        map_data = st.session_state['map_interaction_data']
        
        # Procesar la interacción
        interaction_result = process_map_interaction_complete(
            map_data, data_filtered, colors
        )
        
        # Mostrar feedback de la interacción
        create_interaction_feedback_ui(interaction_result, colors)
        
        # Si requiere rerun, limpiar datos y reejecutar
        if interaction_result.get('requires_rerun', False):
            del st.session_state['map_interaction_data']
            st.rerun()
        
        # Limpiar datos de interacción después de procesar
        if 'map_interaction_data' in st.session_state:
            del st.session_state['map_interaction_data']


def main():
    """
    ACTUALIZADA: Aplicación principal del dashboard v3.1 con mapas interactivos y sincronización bidireccional.
    """
    # Configurar página con responsividad máxima y soporte para mapas
    configure_page_responsive()

    # Barra lateral responsive
    from components.sidebar import init_responsive_sidebar

    try:
        init_responsive_sidebar()
    except ImportError:
        # Fallback básico
        with st.sidebar:
            st.title("Dashboard Tolima v3.1")

    # Cargar datos con indicadores responsive (SOLO EPIZOOTIAS POSITIVAS)
    data = load_new_datasets()

    if data["casos"].empty and data["epizootias"].empty:
        # Error responsive con instrucciones claras
        st.error("❌ No se pudieron cargar los datos")
        st.info("Coloque los archivos de datos en la carpeta 'data/' y recargue la página.")
        return

    # NUEVA: Mostrar información sobre el filtro de epizootias positivas con indicador de versión
    total_epizootias_positivas = len(data["epizootias"])
    if total_epizootias_positivas > 0:
        st.success(f"✅ Dashboard v3.1 - Datos cargados: {len(data['casos'])} casos confirmados y {total_epizootias_positivas} epizootias positivas")

    # Crear filtros responsive con integración de mapas MEJORADOS
    filters, data_filtered = create_filters_responsive_with_maps_enhanced(data)

    # NUEVA: Manejar interacciones del mapa
    handle_map_interactions(data_filtered, filters, COLORS)

    # TÍTULO PRINCIPAL ACTUALIZADO v3.1
    st.markdown(
        '<h1 class="main-title">🗺️ Dashboard Fiebre Amarilla v3.1 - Mapas Interactivos</h1>',
        unsafe_allow_html=True,
    )

    # NUEVA: Mostrar indicador de sincronización si está activa
    if filters.get("active_filters"):
        filter_count = len(filters["active_filters"])
        st.markdown(
            f"""
            <div class="sync-indicator">
                🔄 Sincronización activa: {filter_count} filtro(s) aplicado(s)
            </div>
            """,
            unsafe_allow_html=True,
        )

    # PESTAÑAS PRINCIPALES ACTUALIZADAS v3.1
    tab1, tab2, tab3 = st.tabs(
        [
            "🗺️ Mapas + Métricas",      # NUEVA: Mapas CON todas las tarjetas
            "📊 Análisis Epidemiológico", # ACTUALIZADA: Solo gráficos y tablas
            "📈 Seguimiento Temporal",
        ]
    )

    with tab1:
        # NUEVA: Vista de mapas CON todas las tarjetas informativas
        if "mapas" in vistas_modules and vistas_modules["mapas"]:
            try:
                # Pasar data filtrada para que los mapas trabajen solo con epizootias positivas
                vistas_modules["mapas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                st.error(f"Error en módulo de mapas: {str(e)}")
                st.exception(e)  # Mostrar traceback completo para debug
                st.info("🗺️ Vista de mapas en desarrollo.")
        else:
            st.info("🗺️ Vista de mapas en desarrollo.")

    with tab2:
        # ACTUALIZADA: Solo análisis epidemiológico (sin tarjetas métricas)
        if "tablas" in vistas_modules and vistas_modules["tablas"]:
            try:
                vistas_modules["tablas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                st.error(f"Error en módulo de análisis epidemiológico: {str(e)}")
                st.info("🔧 Vista de análisis epidemiológico en desarrollo.")
        else:
            st.info("🔧 Módulo de análisis epidemiológico en desarrollo.")

    with tab3:
        # Seguimiento temporal (sin cambios)
        if "comparativo" in vistas_modules and vistas_modules["comparativo"]:
            try:
                vistas_modules["comparativo"].show(data_filtered, filters, COLORS)
            except Exception as e:
                st.error(f"Error en módulo de seguimiento temporal: {str(e)}")
                st.info("🔧 Vista de seguimiento temporal en desarrollo.")
        else:
            st.info("🔧 Módulo de seguimiento temporal en desarrollo.")

    # NUEVA: Footer con información de versión
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #666; font-size: 0.8rem; padding: 1rem 0;">
            Dashboard Fiebre Amarilla v3.1 - Mapas Interactivos con Sincronización Bidireccional<br>
            Desarrollado para la Secretaría de Salud del Tolima • © 2025
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()