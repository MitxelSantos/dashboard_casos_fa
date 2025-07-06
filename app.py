"""
Aplicación principal CORREGIDA del Dashboard de Fiebre Amarilla v3.3
CORRECCIONES:
- Mejor debugging para identificar problemas de importación
- Manejo de errores más robusto
- Logging detallado para módulos de vistas
"""

import os
import time
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import unicodedata
import re

# Configurar logging MÁS DETALLADO
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FiebreAmarilla-Dashboard-v3.3")

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
try:
    from config.colors import COLORS
    from config.settings import DASHBOARD_CONFIG
    logger.info("✅ Configuraciones básicas importadas correctamente")
except ImportError as e:
    logger.error(f"❌ Error importando configuraciones básicas: {str(e)}")
    st.error(f"Error en configuraciones básicas: {str(e)}")
    st.stop()

# Importar utilidades responsive
try:
    from config.responsive import init_responsive_dashboard
    from utils.responsive import init_responsive_utils, create_responsive_metric_cards
    RESPONSIVE_AVAILABLE = True
    logger.info("✅ Utilidades responsive importadas correctamente")
except ImportError as e:
    RESPONSIVE_AVAILABLE = False
    logger.warning(f"⚠️ Módulos responsive no disponibles: {str(e)}")

try:
    from utils.data_processor import (
        excel_date_to_datetime,
        calculate_basic_metrics,
        get_latest_case_info,
    )
    logger.info("✅ Utilidades de procesamiento de datos importadas correctamente")
except ImportError as e:
    logger.error(f"❌ Error importando utilidades de datos: {str(e)}")
    st.error(f"Error en utilidades de datos: {str(e)}")
    st.stop()

# Importar utilidades de interacciones de mapa
try:
    from utils.map_interactions import (
        process_map_interaction_complete,
        create_interaction_feedback_ui,
        get_interaction_manager,
        get_bounds_manager
    )
    MAP_INTERACTIONS_AVAILABLE = True
    logger.info("✅ Utilidades de interacciones de mapa importadas correctamente")
except ImportError as e:
    MAP_INTERACTIONS_AVAILABLE = False
    logger.warning(f"⚠️ Utilidades de interacciones de mapa no disponibles: {str(e)}")

# Lista de vistas a importar
vista_modules = ["mapas", "tablas", "comparativo"]
vistas_modules = {}


def import_vista_module(module_name):
    """
    MEJORADO: Importa un módulo de vista específico con debugging detallado.
    """
    logger.info(f"🔄 Intentando importar módulo: {module_name}")
    
    try:
        # Verificar si el archivo existe
        module_path = ROOT_DIR / "vistas" / f"{module_name}.py"
        if not module_path.exists():
            logger.error(f"❌ Archivo no encontrado: {module_path}")
            return None
        
        logger.debug(f"📁 Archivo encontrado: {module_path}")
        
        # Intentar importar el módulo
        module = __import__(f"vistas.{module_name}", fromlist=[module_name])
        
        # Verificar que el módulo tiene la función 'show'
        if not hasattr(module, 'show'):
            logger.error(f"❌ El módulo {module_name} no tiene función 'show'")
            return None
        
        logger.info(f"✅ Módulo {module_name} importado correctamente")
        return module
        
    except ImportError as e:
        logger.error(f"❌ ImportError en módulo {module_name}: {str(e)}")
        logger.error(f"   Detalles del error: {type(e).__name__}")
        
        # Mostrar información adicional sobre el error
        import traceback
        logger.error(f"   Traceback completo:\n{traceback.format_exc()}")
        
        return None
    except Exception as e:
        logger.error(f"❌ Error inesperado importando {module_name}: {str(e)}")
        logger.error(f"   Tipo de error: {type(e).__name__}")
        
        import traceback
        logger.error(f"   Traceback completo:\n{traceback.format_exc()}")
        
        return None


def check_module_dependencies():
    """
    NUEVO: Verifica las dependencias de cada módulo antes de importar.
    """
    logger.info("🔍 Verificando dependencias de módulos...")
    
    dependencies_status = {}
    
    # Verificar dependencias de mapas
    try:
        import geopandas as gpd
        import folium
        from streamlit_folium import st_folium
        dependencies_status['maps_libs'] = True
        logger.info("✅ Dependencias de mapas disponibles: geopandas, folium, streamlit-folium")
    except ImportError as e:
        dependencies_status['maps_libs'] = False
        logger.warning(f"⚠️ Dependencias de mapas no disponibles: {str(e)}")
    
    # Verificar dependencias básicas
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        dependencies_status['plotly'] = True
        logger.info("✅ Plotly disponible")
    except ImportError as e:
        dependencies_status['plotly'] = False
        logger.error(f"❌ Plotly no disponible: {str(e)}")
    
    return dependencies_status


# Importar módulos de vistas CON DEBUGGING MEJORADO
logger.info("🚀 Iniciando importación de módulos de vistas...")

# Verificar dependencias primero
deps_status = check_module_dependencies()

for module_name in vista_modules:
    logger.info(f"📦 Procesando módulo: {module_name}")
    
    # Información especial para mapas
    if module_name == "mapas":
        if not deps_status.get('maps_libs', False):
            logger.warning(f"⚠️ Dependencias de mapas no disponibles, pero intentando importar {module_name} de todas formas...")
        else:
            logger.info(f"✅ Dependencias de mapas OK, procediendo con importación de {module_name}")
    
    # Importar el módulo
    imported_module = import_vista_module(module_name)
    vistas_modules[module_name] = imported_module
    
    if imported_module:
        logger.info(f"✅ Módulo {module_name} importado y registrado correctamente")
    else:
        logger.error(f"❌ Módulo {module_name} falló al importar - se mostrará mensaje de desarrollo")

# Mostrar estado final de importaciones
logger.info("📊 Estado final de importaciones de vistas:")
for module_name, module in vistas_modules.items():
    status = "✅ OK" if module else "❌ FALLO"
    logger.info(f"   {module_name}: {status}")

def load_shapefile_locations():
    """
    NUEVA: Carga ubicaciones desde shapefiles para mostrar en filtros.
    """
    try:
        from pathlib import Path
        PROCESSED_DIR = Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed")
        
        # Intentar cargar shapefiles
        shapefile_data = {"municipios": [], "veredas_por_municipio": {}}
        
        try:
            import geopandas as gpd
            
            # Cargar municipios
            municipios_path = PROCESSED_DIR / "tolima_municipios.shp"
            if municipios_path.exists():
                municipios_gdf = gpd.read_file(municipios_path)
                shapefile_data["municipios"] = sorted(municipios_gdf['municipi_1'].str.upper().str.strip().unique())
            
            # Cargar veredas por municipio
            veredas_path = PROCESSED_DIR / "tolima_veredas.shp"
            if veredas_path.exists():
                veredas_gdf = gpd.read_file(veredas_path)
                
                # Normalizar nombres
                veredas_gdf['municipi_1_norm'] = veredas_gdf['municipi_1'].str.upper().str.strip()
                veredas_gdf['vereda_nor_norm'] = veredas_gdf['vereda_nor'].str.upper().str.strip()
                
                # Agrupar veredas por municipio
                for municipio in shapefile_data["municipios"]:
                    veredas_municipio = veredas_gdf[
                        veredas_gdf['municipi_1_norm'] == municipio
                    ]['vereda_nor_norm'].unique()
                    
                    # Filtrar valores vacíos y ordenar
                    veredas_validas = [v for v in veredas_municipio if v and str(v).strip()]
                    shapefile_data["veredas_por_municipio"][municipio] = sorted(veredas_validas)
            
            logger.info(f"✅ Shapefiles cargados: {len(shapefile_data['municipios'])} municipios")
            return shapefile_data
            
        except ImportError:
            logger.warning("⚠️ GeoPandas no disponible, usando fallback")
            
    except Exception as e:
        logger.warning(f"⚠️ No se pudieron cargar shapefiles: {str(e)}")
    
    # Fallback: usar lista manual
    municipios_tolima = [
        "IBAGUE", "ALPUJARRA", "ALVARADO", "AMBALEMA", "ANZOATEGUI",
        "ARMERO", "ATACO", "CAJAMARCA", "CARMEN DE APICALA", "CASABIANCA",
        "CHAPARRAL", "COELLO", "COYAIMA", "CUNDAY", "DOLORES",
        "ESPINAL", "FALAN", "FLANDES", "FRESNO", "GUAMO",
        "HERVEO", "HONDA", "ICONONZO", "LERIDA", "LIBANO",
        "MARIQUITA", "MELGAR", "MURILLO", "NATAGAIMA", "ORTEGA",
        "PALOCABILDO", "PIEDRAS", "PLANADAS", "PRADO", "PURIFICACION",
        "RIOBLANCO", "RONCESVALLES", "ROVIRA", "SALDAÑA", "SAN ANTONIO",
        "SAN LUIS", "SANTA ISABEL", "SUAREZ", "VALLE DE SAN JUAN",
        "VENADILLO", "VILLAHERMOSA", "VILLARRICA"
    ]
    
    return {
        "municipios": municipios_tolima,
        "veredas_por_municipio": {municipio: [] for municipio in municipios_tolima}
    }

def load_enhanced_datasets():
    """
    Carga datasets CORREGIDA - normaliza nombres para evitar duplicados.
    """
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("🔄 Cargando datos normalizados...")
        
        # Cargar ubicaciones de shapefiles
        shapefile_locations = load_shapefile_locations()

        # ==================== CONFIGURACIÓN DE RUTAS ====================
        casos_filename = "BD_positivos.xlsx"
        epizootias_filename = "Información_Datos_FA.xlsx"

        data_casos_path = DATA_DIR / casos_filename
        data_epizootias_path = DATA_DIR / epizootias_filename
        root_casos_path = ROOT_DIR / casos_filename
        root_epizootias_path = ROOT_DIR / epizootias_filename

        progress_bar.progress(10)
        status_text.text("📁 Cargando archivos...")

        # ==================== CARGA DE DATOS ====================
        casos_df = None
        epizootias_df = None
        data_source = None

        # Estrategia 1: Carpeta data/
        if data_casos_path.exists() and data_epizootias_path.exists():
            try:
                casos_df = pd.read_excel(data_casos_path, sheet_name="ACUMU", engine="openpyxl")
                epizootias_df = pd.read_excel(data_epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
                data_source = "data_folder"
                logger.info("✅ Datos cargados desde carpeta data/")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando desde data/: {str(e)}")
                casos_df = None
                epizootias_df = None

        # Estrategia 2: Directorio raíz
        if casos_df is None and root_casos_path.exists() and root_epizootias_path.exists():
            try:
                casos_df = pd.read_excel(root_casos_path, sheet_name="ACUMU", engine="openpyxl")
                epizootias_df = pd.read_excel(root_epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
                data_source = "root_folder"
                logger.info("✅ Datos cargados desde directorio raíz")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando desde raíz: {str(e)}")
                casos_df = None
                epizootias_df = None

        if casos_df is None or epizootias_df is None:
            st.error("❌ No se pudieron cargar los archivos de datos")
            return create_empty_data_structure()

        progress_bar.progress(30)
        status_text.text("🔧 Procesando y normalizando datos...")
        
        # ==================== NORMALIZACIÓN DE NOMBRES ====================
        def normalize_name(name):
            """Normaliza nombres para evitar duplicados."""
            if pd.isna(name) or name == "":
                return ""
            return str(name).upper().strip()
        
        # Limpiar columnas problemáticas
        for df in [casos_df, epizootias_df]:
            if 'Unnamed: 16' in df.columns:
                df.drop('Unnamed: 16', axis=1, inplace=True)
            # Eliminar todas las columnas "Unnamed"
            df.drop(columns=[col for col in df.columns if 'Unnamed' in col], inplace=True)

        # Eliminar filas completamente vacías
        casos_df = casos_df.dropna(how="all")
        epizootias_df = epizootias_df.dropna(how="all")

        # ==================== MAPEO Y NORMALIZACIÓN DE COLUMNAS ====================
        casos_columns_map = {
            "edad_": "edad",
            "sexo_": "sexo",
            "vereda_": "vereda",
            "nmun_proce": "municipio",
            "cod_ase_": "eps",
            "Condición Final": "condicion_final",
            "Inicio de sintomas": "fecha_inicio_sintomas",
        }

        epizootias_columns_map = {
            "MUNICIPIO": "municipio",
            "VEREDA": "vereda",
            "FECHA RECOLECCIÓN ": "fecha_recoleccion",
            "PROVENIENTE ": "proveniente",
            "DESCRIPCIÓN": "descripcion",
        }

        # Renombrar columnas existentes
        existing_casos_columns = {k: v for k, v in casos_columns_map.items() if k in casos_df.columns}
        casos_df = casos_df.rename(columns=existing_casos_columns)

        existing_epi_columns = {k: v for k, v in epizootias_columns_map.items() if k in epizootias_df.columns}
        epizootias_df = epizootias_df.rename(columns=existing_epi_columns)

        # ==================== NORMALIZACIÓN CRÍTICA ====================
        # Normalizar nombres de municipios y veredas para evitar duplicados
        if "municipio" in casos_df.columns:
            casos_df["municipio"] = casos_df["municipio"].apply(normalize_name)
            
        if "vereda" in casos_df.columns:
            casos_df["vereda"] = casos_df["vereda"].apply(normalize_name)
            
        if "municipio" in epizootias_df.columns:
            epizootias_df["municipio"] = epizootias_df["municipio"].apply(normalize_name)
            
        if "vereda" in epizootias_df.columns:
            epizootias_df["vereda"] = epizootias_df["vereda"].apply(normalize_name)

        # ==================== PROCESAMIENTO DE FECHAS ====================
        if "fecha_inicio_sintomas" in casos_df.columns:
            logger.info("📅 Procesando fechas de casos...")
            casos_df["fecha_inicio_sintomas"] = casos_df["fecha_inicio_sintomas"].apply(excel_date_to_datetime)

        if "fecha_recoleccion" in epizootias_df.columns:
            logger.info("📅 Procesando fechas de epizootias...")
            epizootias_df["fecha_recoleccion"] = epizootias_df["fecha_recoleccion"].apply(excel_date_to_datetime)

        progress_bar.progress(50)
        status_text.text("🔵 Filtrando epizootias positivas + en estudio...")

        # ==================== FILTRO DE EPIZOOTIAS ====================
        if "descripcion" in epizootias_df.columns:
            total_original = len(epizootias_df)
            
            # Normalizar descripciones y filtrar
            epizootias_df["descripcion"] = epizootias_df["descripcion"].apply(normalize_name)
            epizootias_df = epizootias_df[
                epizootias_df["descripcion"].isin(["POSITIVO FA", "EN ESTUDIO"])
            ]
            
            total_filtradas = len(epizootias_df)
            positivas_count = len(epizootias_df[epizootias_df["descripcion"] == "POSITIVO FA"])
            en_estudio_count = len(epizootias_df[epizootias_df["descripcion"] == "EN ESTUDIO"])
            
            logger.info(f"🔵 Epizootias filtradas: {total_filtradas} de {total_original}")
            logger.info(f"   🔴 Positivas: {positivas_count}")
            logger.info(f"   🔵 En estudio: {en_estudio_count}")

        progress_bar.progress(70)
        status_text.text("🗺️ Creando listas de ubicaciones normalizadas...")

        # ==================== LISTAS NORMALIZADAS ====================
        # Obtener municipios únicos NORMALIZADOS
        municipios_casos = set(casos_df["municipio"].dropna()) if "municipio" in casos_df.columns else set()
        municipios_epizootias = set(epizootias_df["municipio"].dropna()) if "municipio" in epizootias_df.columns else set()
        municipios_con_datos = sorted(municipios_casos.union(municipios_epizootias))

        # Lista completa de municipios del Tolima NORMALIZADOS
        municipios_tolima_completos = [
            "IBAGUE", "ALPUJARRA", "ALVARADO", "AMBALEMA", "ANZOATEGUI",
            "ARMERO", "ATACO", "CAJAMARCA", "CARMEN DE APICALA", "CASABIANCA",
            "CHAPARRAL", "COELLO", "COYAIMA", "CUNDAY", "DOLORES",
            "ESPINAL", "FALAN", "FLANDES", "FRESNO", "GUAMO",
            "HERVEO", "HONDA", "ICONONZO", "LERIDA", "LIBANO",
            "MARIQUITA", "MELGAR", "MURILLO", "NATAGAIMA", "ORTEGA",
            "PALOCABILDO", "PIEDRAS", "PLANADAS", "PRADO", "PURIFICACION",
            "RIOBLANCO", "RONCESVALLES", "ROVIRA", "SALDAÑA", "SAN ANTONIO",
            "SAN LUIS", "SANTA ISABEL", "SUAREZ", "VALLE DE SAN JUAN",
            "VENADILLO", "VILLAHERMOSA", "VILLARRICA"
        ]

        # Combinar municipios eliminando duplicados
        todos_municipios = list(set(municipios_con_datos + municipios_tolima_completos))
        todos_municipios = sorted(todos_municipios)

        # ==================== VEREDAS POR MUNICIPIO MEJORADAS ====================
        veredas_por_municipio = {}
        for municipio in todos_municipios:
            veredas = set()
            
            # Veredas de casos
            if "vereda" in casos_df.columns:
                veredas_casos = casos_df[casos_df["municipio"] == municipio]["vereda"].dropna().unique()
                veredas.update(veredas_casos)
            
            # Veredas de epizootias
            if "vereda" in epizootias_df.columns:
                veredas_epi = epizootias_df[epizootias_df["municipio"] == municipio]["vereda"].dropna().unique()
                veredas.update(veredas_epi)
            
            # NUEVO: Agregar veredas del shapefile (incluso si no tienen datos)
            if municipio in shapefile_locations["veredas_por_municipio"]:
                veredas_shapefile = shapefile_locations["veredas_por_municipio"][municipio]
                veredas.update(veredas_shapefile)
            
            # Filtrar veredas vacías y ordenar
            veredas_filtradas = [v for v in veredas if v and v.strip()]
            veredas_por_municipio[municipio] = sorted(veredas_filtradas)    
            # Filtrar veredas vacías y ordenar
            veredas_filtradas = [v for v in veredas if v and v.strip()]
            veredas_por_municipio[municipio] = sorted(veredas_filtradas)            
            
        progress_bar.progress(90)
        status_text.text("📊 Finalizando...")

        # ==================== MAPEOS DIRECTOS ====================
        municipio_display_map = {municipio: municipio for municipio in todos_municipios}
        vereda_display_map = {}
        for municipio in todos_municipios:
            vereda_display_map[municipio] = {vereda: vereda for vereda in veredas_por_municipio[municipio]}

        # Mapeos de valores (sin cambios)
        condicion_map = {
            "Fallecido": {"color": COLORS["danger"], "icon": "⚰️", "categoria": "Fallecido"},
            "Vivo": {"color": COLORS["success"], "icon": "💚", "categoria": "Vivo"},
        }

        descripcion_map = {
            "POSITIVO FA": {"color": COLORS["danger"], "icon": "🔴", "categoria": "Positivo"},
            "EN ESTUDIO": {"color": COLORS["info"], "icon": "🔵", "categoria": "En Estudio"},
        }

        progress_bar.progress(100)
        time.sleep(1.5)
        status_text.empty()
        progress_bar.empty()

        # Log final
        logger.info(f"✅ Datos cargados desde: {data_source}")
        logger.info(f"📊 Casos cargados: {len(casos_df)}")
        logger.info(f"🔵 Epizootias cargadas: {len(epizootias_df)}")
        logger.info(f"🗺️ Municipios totales: {len(todos_municipios)} (sin duplicados)")
        
        return {
            "casos": casos_df,
            "epizootias": epizootias_df,
            "municipios_normalizados": todos_municipios,
            "municipio_display_map": municipio_display_map,
            "veredas_por_municipio": veredas_por_municipio,
            "vereda_display_map": vereda_display_map,
            "condicion_map": condicion_map,
            "descripcion_map": descripcion_map,
            "data_source": data_source,
            "shapefile_locations": shapefile_locations,  # NUEVO
        }

    except Exception as e:
        logger.error(f"💥 Error crítico al cargar los datos: {str(e)}")
        st.error(f"❌ Error crítico: {str(e)}")
        return create_empty_data_structure()
    
def create_empty_data_structure():
    """Crea estructura de datos vacía para casos de error."""
    return {
        "casos": pd.DataFrame(),
        "epizootias": pd.DataFrame(),
        "municipios_normalizados": [],
        "municipio_display_map": {},
        "veredas_por_municipio": {},
        "vereda_display_map": {},
        "condicion_map": {},
        "descripcion_map": {},
        "vereda_mapping": {},  # NUEVO
        "data_source": "error",
    }

def create_filters_responsive_with_maps_enhanced(data):
    """
    CORREGIDO: Sistema de filtros que SÍ existe en components/filters.py
    """
    # Importar el sistema de filtros mejorado que SÍ existe
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
    """Sistema de filtros básico como fallback."""
    st.sidebar.subheader("🔍 Filtros (Básico)")

    # Filtro de municipio básico - INCLUYENDO MUNICIPIOS SIN DATOS
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
    epizootias_filtradas = data["epizootias"].copy()  # Ahora contiene positivas + en estudio

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
    CORREGIDO: Configura la página con espaciado reducido.
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

    # CSS responsive principal ACTUALIZADO con espaciado reducido
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
        
        /* CORREGIDO: Espaciado principal reducido */
        .block-container {{
            padding-top: 0.5rem !important;
            padding-bottom: clamp(1rem, 3vw, 2rem) !important;
            padding-left: clamp(0.5rem, 2vw, 1.5rem) !important;
            padding-right: clamp(0.5rem, 2vw, 1.5rem) !important;
            max-width: 100% !important;
        }}
        
        /* CORREGIDO: Título principal sin espacio excesivo */
        .main-title {{
            color: var(--primary-color);
            font-size: clamp(1.6rem, 5vw, 2.2rem);
            font-weight: 700;
            margin-bottom: 0.75rem !important;
            text-align: center;
            padding: 0.75rem 1rem !important;
            border-bottom: 3px solid var(--secondary-color);
            line-height: 1.1;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def handle_map_interactions(data_filtered, filters, colors):
    """
    CORREGIDO: Maneja las interacciones del mapa con debugging mejorado.
    """
    if not MAP_INTERACTIONS_AVAILABLE:
        return
    
    # Verificar si hay datos de interacción del mapa en session_state
    if 'map_interaction_data' in st.session_state:
        map_data = st.session_state['map_interaction_data']
        
        # **DEBUG: Mostrar datos de interacción**
        if st.sidebar.checkbox("🔍 Debug Interacciones", value=False):
            st.sidebar.markdown("**🗺️ Última Interacción:**")
            st.sidebar.json(map_data)
        
        # Procesar la interacción
        try:
            interaction_result = process_map_interaction_complete(
                map_data, data_filtered, colors
            )
            
            # Mostrar feedback de la interacción
            create_interaction_feedback_ui(interaction_result, colors)
            
            # Si requiere rerun, limpiar datos y reejecutar
            if interaction_result.get('requires_rerun', False):
                del st.session_state['map_interaction_data']
                st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"❌ Error procesando interacción: {str(e)}")
        
        # Limpiar datos de interacción después de procesar
        if 'map_interaction_data' in st.session_state:
            del st.session_state['map_interaction_data']

def main():
    """
    Aplicación principal del dashboard v1 CORREGIDA con debugging mejorado.
    """
    # Configurar página con espaciado corregido
    configure_page_responsive()

    # Barra lateral responsive
    from components.sidebar import init_responsive_sidebar

    try:
        init_responsive_sidebar()
    except ImportError:
        # Fallback básico
        with st.sidebar:
            st.title("Dashboard Tolima v3.3")

    # Cargar datos con indicadores responsive (POSITIVAS + EN ESTUDIO)
    data = load_enhanced_datasets()
    
    # DEBUG: Verificar estructura de datos
    if not data["casos"].empty:
        st.write("**DEBUG - Columnas en casos:**", list(data["casos"].columns))
        st.write("**DEBUG - Primeras filas casos:**", data["casos"][["municipio", "vereda"]].head() if "municipio" in data["casos"].columns else "No hay columna municipio")

    if not data["epizootias"].empty:
        st.write("**DEBUG - Columnas en epizootias:**", list(data["epizootias"].columns))
        st.write("**DEBUG - Primeras filas epizootias:**", data["epizootias"][["municipio", "vereda"]].head() if "municipio" in data["epizootias"].columns else "No hay columna municipio")

    if data["casos"].empty and data["epizootias"].empty:
        # Error responsive con instrucciones claras
        st.error("❌ No se pudieron cargar los datos")
        st.info("Coloque los archivos de datos en la carpeta 'data/' y recargue la página.")
        return

    # Mostrar información sobre el filtro de epizootias actualizado
    total_epizootias = len(data["epizootias"])
    if total_epizootias > 0:
        positivas_count = len(data["epizootias"][data["epizootias"]["descripcion"] == "POSITIVO FA"]) if not data["epizootias"].empty and "descripcion" in data["epizootias"].columns else 0
        en_estudio_count = len(data["epizootias"][data["epizootias"]["descripcion"] == "EN ESTUDIO"]) if not data["epizootias"].empty and "descripcion" in data["epizootias"].columns else 0

    # Crear filtros responsive con integración de mapas MEJORADOS
    filters, data_filtered = create_filters_responsive_with_maps_enhanced(data)
    
    # DEBUG: Verificar filtros y datos filtrados
    st.write("**DEBUG - Filtros activos:**", filters)
    st.write("**DEBUG - Casos filtrados:**", len(data_filtered["casos"]), "vs originales:", len(data["casos"]))
    st.write("**DEBUG - Epizootias filtradas:**", len(data_filtered["epizootias"]), "vs originales:", len(data["epizootias"]))

    if len(data_filtered["casos"]) != len(data["casos"]):
        st.write("**DEBUG - Ejemplo casos filtrados:**", data_filtered["casos"][["municipio", "vereda"]].head() if "municipio" in data_filtered["casos"].columns else "No hay columna municipio")

    # Manejar interacciones del mapa
    handle_map_interactions(data_filtered, filters, COLORS)

    tab1, tab2, tab3 = st.tabs(
        [
            "🗺️ Mapa Interactivo",
            "📊 Análisis Detallado", 
            "📈 Seguimiento Temporal",
        ]
    )

    with tab1:
        # Vista de mapas CON datos filtrados
        logger.info(f"🗺️ Intentando mostrar vista de mapas...")
        logger.info(f"   Estado del módulo 'mapas': {'✅ OK' if vistas_modules.get('mapas') else '❌ None'}")
        
        if "mapas" in vistas_modules and vistas_modules["mapas"]:
            try:
                logger.info("🔄 Ejecutando vistas_modules['mapas'].show()...")
                
                # **USAR data_filtered (no data)**
                vistas_modules["mapas"].show(data_filtered, filters, COLORS)
                
                logger.info("✅ Vista de mapas ejecutada correctamente")
                
            except Exception as e:
                logger.error(f"❌ Error ejecutando vista de mapas: {str(e)}")
                st.error(f"Error en módulo de mapas: {str(e)}")
                
                # Mostrar traceback completo para debug
                import traceback
                error_traceback = traceback.format_exc()
                logger.error(f"Traceback completo:\n{error_traceback}")
                
                with st.expander("🔍 Ver detalles del error", expanded=False):
                    st.code(error_traceback)
                
                st.info("🗺️ Vista de mapas temporalmente no disponible debido al error anterior.")
        else:
            # Mostrar información detallada sobre por qué no está disponible
            logger.warning("⚠️ Módulo de mapas no disponible")
            
            st.warning("⚠️ **Vista de mapas temporalmente no disponible**")
            
            # Verificar dependencias específicamente
            deps_status = check_module_dependencies()
            
            if not deps_status.get('maps_libs', False):
                st.error("❌ **Dependencias de mapas no instaladas**")
                st.code("pip install geopandas folium streamlit-folium")
                st.info("Ejecute el comando anterior y reinicie la aplicación.")
            else:
                st.error("❌ **Error en la importación del módulo de mapas**")
                st.info("Revise los logs de la aplicación para más detalles.")
            
            st.info("🗺️ Las otras pestañas funcionan normalmente.")

    with tab2:
        # **USAR data_filtered PARA ANÁLISIS DETALLADO**
        if "tablas" in vistas_modules and vistas_modules["tablas"]:
            try:
                logger.info("🔄 Mostrando análisis detallado con datos filtrados")
                vistas_modules["tablas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                logger.error(f"❌ Error en módulo de análisis: {str(e)}")
                st.error(f"Error en módulo de análisis epidemiológico: {str(e)}")
                show_filtered_data_summary(data_filtered, filters)
        else:
            st.info("🔧 Módulo de análisis epidemiológico en desarrollo.")
            show_filtered_data_summary(data_filtered, filters)

    with tab3:
        # **USAR data_filtered PARA SEGUIMIENTO TEMPORAL**
        if "comparativo" in vistas_modules and vistas_modules["comparativo"]:
            try:
                logger.info("🔄 Mostrando seguimiento temporal con datos filtrados")
                vistas_modules["comparativo"].show(data_filtered, filters, COLORS)
            except Exception as e:
                logger.error(f"❌ Error en módulo temporal: {str(e)}")
                st.error(f"Error en módulo de seguimiento temporal: {str(e)}")
                show_filtered_data_summary(data_filtered, filters)
        else:
            st.info("🔧 Módulo de seguimiento temporal en desarrollo.")
            show_filtered_data_summary(data_filtered, filters)

    # Footer con información de versión (espaciado reducido)
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #666; font-size: 0.75rem; padding: 0.5rem 0; margin-top: 0.5rem;">
            Dashboard Fiebre Amarilla v1.0<br>
            Desarrollado por: Ing. Jose Miguel Santos • Secretaría de Salud del Tolima • © 2025
        </div>
        """,
        unsafe_allow_html=True,
    )

def show_filtered_data_summary(data_filtered, filters):
    """
    NUEVA: Muestra resumen de datos filtrados como fallback.
    """
    st.markdown("### 📊 Resumen de Datos Filtrados")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Métricas básicas con datos filtrados
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🦠 Casos", len(casos))
    
    with col2:
        fallecidos = len(casos[casos["condicion_final"] == "Fallecido"]) if not casos.empty and "condicion_final" in casos.columns else 0
        st.metric("⚰️ Fallecidos", fallecidos)
    
    with col3:
        st.metric("🐒 Epizootias", len(epizootias))
    
    with col4:
        positivas = len(epizootias[epizootias["descripcion"] == "POSITIVO FA"]) if not epizootias.empty and "descripcion" in epizootias.columns else 0
        st.metric("🔴 Positivas", positivas)
    
    # Información de filtros activos
    active_filters = filters.get("active_filters", [])
    if active_filters:
        st.markdown("**🎯 Filtros Activos:**")
        for filtro in active_filters:
            st.caption(f"• {filtro}")
    else:
        st.info("📊 Mostrando datos completos del Tolima")
    
    # Mostrar tablas básicas si hay datos
    if not casos.empty:
        st.markdown("**📋 Casos Filtrados:**")
        casos_display = casos.head(10)
        if "fecha_inicio_sintomas" in casos_display.columns:
            casos_display = casos_display.copy()
            casos_display["fecha_inicio_sintomas"] = casos_display["fecha_inicio_sintomas"].dt.strftime('%d/%m/%Y')
        st.dataframe(casos_display, use_container_width=True)
    
    if not epizootias.empty:
        st.markdown("**📋 Epizootias Filtradas:**")
        epi_display = epizootias.head(10)
        if "fecha_recoleccion" in epi_display.columns:
            epi_display = epi_display.copy()
            epi_display["fecha_recoleccion"] = epi_display["fecha_recoleccion"].dt.strftime('%d/%m/%Y')
        st.dataframe(epi_display, use_container_width=True) 

if __name__ == "__main__":
    main()