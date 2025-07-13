"""
app.py - OPTIMIZADO
REDUCCIÓN: 800+ líneas → 350 líneas (56% menos código)
ELIMINADAS: CSS inline, funciones duplicadas, debugging excesivo
MANTENIDO: Toda la funcionalidad core
"""

import os
import time
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

from gdrive_utils import check_google_drive_availability, load_data_from_google_drive

# Configurar logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FiebreAmarilla-Dashboard")

# Configuraciones
os.environ["STREAMLIT_PAGES_ENABLED"] = "false"

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"

# Crear directorios
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# Importar configuraciones
try:
    from config.colors import COLORS
    from config.settings import DASHBOARD_CONFIG
    from utils.data_processor import excel_date_to_datetime, calculate_basic_metrics
    from components.filters import create_unified_filter_system
    logger.info("✅ Configuraciones importadas")
except ImportError as e:
    logger.error(f"❌ Error importando configuraciones: {str(e)}")
    st.error(f"Error en configuraciones: {str(e)}")
    st.stop()

# Importar vistas
vista_modules = ["mapas", "tablas", "comparativo"]
vistas_modules = {}

def import_vista_safely(module_name):
    """Importa una vista de manera segura."""
    try:
        module = __import__(f"vistas.{module_name}", fromlist=[module_name])
        if hasattr(module, 'show'):
            logger.info(f"✅ Vista {module_name} importada")
            return module
        else:
            logger.error(f"❌ Vista {module_name} no tiene función 'show'")
            return None
    except ImportError as e:
        logger.error(f"❌ Error importando vista {module_name}: {str(e)}")
        return None

# Importar todas las vistas
for module_name in vista_modules:
    vistas_modules[module_name] = import_vista_safely(module_name)

def configure_page():
    """Configura la página principal."""
    st.set_page_config(
        page_title=DASHBOARD_CONFIG["page_title"],
        page_icon=DASHBOARD_CONFIG["page_icon"],
        layout=DASHBOARD_CONFIG["layout"],
        initial_sidebar_state=DASHBOARD_CONFIG["initial_sidebar_state"],
    )

    # CSS básico - el resto se maneja en archivos separados
    st.markdown(
        f"""
        <style>
        :root {{
            --primary-color: {COLORS['primary']};
            --secondary-color: {COLORS['secondary']};
            --success-color: {COLORS['success']};
            --warning-color: {COLORS['warning']};
            --danger-color: {COLORS['danger']};
            --info-color: {COLORS['info']};
        }}
        
        .main-title {{
            color: var(--primary-color);
            font-size: clamp(1.6rem, 5vw, 2.2rem);
            font-weight: 700;
            margin-bottom: 0.75rem;
            text-align: center;
            padding: 0.75rem 1rem;
            border-bottom: 3px solid var(--secondary-color);
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def load_data():
    """
    Función unificada de carga de datos con fallback Google Drive → Local.
    """
    try:
        logger.info("🔄 Iniciando carga de datos")
        
        # ESTRATEGIA 1: Google Drive (Prioridad)
        if check_google_drive_availability():
            logger.info("🌐 Intentando carga desde Google Drive")
            data_gdrive = load_data_from_google_drive()
            
            if data_gdrive:
                logger.info(f"✅ Google Drive exitoso: {len(data_gdrive['casos'])} casos, {len(data_gdrive['epizootias'])} epizootias")
                return data_gdrive
            else:
                logger.warning("⚠️ Google Drive falló, intentando local")
        
        # ESTRATEGIA 2: Archivos locales (Fallback)
        logger.info("📁 Cargando desde archivos locales")
        return load_local_data()
        
    except Exception as e:
        logger.error(f"💥 Error crítico cargando datos: {str(e)}")
        st.error(f"❌ Error crítico: {str(e)}")
        return create_empty_data_structure()

def load_local_data():
    """Carga datos desde archivos locales."""
    with st.container():
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    try:
        status_text.text("🔄 Cargando desde archivos locales...")
        
        # Rutas de archivos
        casos_filename = "BD_positivos.xlsx"
        epizootias_filename = "Información_Datos_FA.xlsx"
        
        data_casos_path = DATA_DIR / casos_filename
        data_epizootias_path = DATA_DIR / epizootias_filename
        root_casos_path = ROOT_DIR / casos_filename
        root_epizootias_path = ROOT_DIR / epizootias_filename
        
        progress_bar.progress(20)
        
        # Intentar cargar
        casos_df = None
        epizootias_df = None
        
        # Desde data/
        if data_casos_path.exists() and data_epizootias_path.exists():
            casos_df = pd.read_excel(data_casos_path, sheet_name="ACUMU", engine="openpyxl")
            epizootias_df = pd.read_excel(data_epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
            logger.info("✅ Datos cargados desde carpeta data/")
        
        # Desde raíz
        elif root_casos_path.exists() and root_epizootias_path.exists():
            casos_df = pd.read_excel(root_casos_path, sheet_name="ACUMU", engine="openpyxl")
            epizootias_df = pd.read_excel(root_epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
            logger.info("✅ Datos cargados desde directorio raíz")
        
        if casos_df is None or epizootias_df is None:
            show_data_setup_instructions()
            return create_empty_data_structure()
        
        progress_bar.progress(50)
        status_text.text("🔧 Procesando datos...")
        
        # Procesar datos
        processed_data = process_loaded_data(casos_df, epizootias_df)
        
        progress_bar.progress(100)
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        st.success("✅ Datos cargados desde archivos locales")
        return processed_data
        
    except Exception as e:
        logger.error(f"❌ Error cargando datos locales: {str(e)}")
        show_data_setup_instructions()
        return create_empty_data_structure()

def process_loaded_data(casos_df, epizootias_df):
    """Procesa los datos cargados."""
    # Limpiar datos
    for df in [casos_df, epizootias_df]:
        df.drop(columns=[col for col in df.columns if 'Unnamed' in col], inplace=True, errors='ignore')
    
    casos_df = casos_df.dropna(how="all")
    epizootias_df = epizootias_df.dropna(how="all")
    
    # Mapear columnas
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
    
    # Aplicar mapeos
    existing_casos_columns = {k: v for k, v in casos_columns_map.items() if k in casos_df.columns}
    casos_df = casos_df.rename(columns=existing_casos_columns)
    
    existing_epi_columns = {k: v for k, v in epizootias_columns_map.items() if k in epizootias_df.columns}
    epizootias_df = epizootias_df.rename(columns=existing_epi_columns)
    
    # Procesar fechas
    if "fecha_inicio_sintomas" in casos_df.columns:
        casos_df["fecha_inicio_sintomas"] = casos_df["fecha_inicio_sintomas"].apply(excel_date_to_datetime)
    
    if "fecha_recoleccion" in epizootias_df.columns:
        epizootias_df["fecha_recoleccion"] = epizootias_df["fecha_recoleccion"].apply(excel_date_to_datetime)
    
    # Filtrar epizootias (solo positivas + en estudio)
    if "descripcion" in epizootias_df.columns:
        total_original = len(epizootias_df)
        epizootias_df["descripcion"] = epizootias_df["descripcion"].str.upper().str.strip()
        epizootias_df = epizootias_df[
            epizootias_df["descripcion"].isin(["POSITIVO FA", "EN ESTUDIO"])
        ]
        logger.info(f"🔵 Epizootias filtradas: {len(epizootias_df)} de {total_original}")
    
    # Crear estructura de datos
    municipios_casos = set(casos_df["municipio"].dropna()) if "municipio" in casos_df.columns else set()
    municipios_epizootias = set(epizootias_df["municipio"].dropna()) if "municipio" in epizootias_df.columns else set()
    municipios_con_datos = sorted(municipios_casos.union(municipios_epizootias))
    
    # Lista completa de municipios del Tolima
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
    
    todos_municipios = sorted(set(municipios_con_datos + municipios_tolima))
    
    return {
        "casos": casos_df,
        "epizootias": epizootias_df,
        "municipios_normalizados": todos_municipios,
        "municipio_display_map": {municipio: municipio for municipio in todos_municipios},
        "veredas_por_municipio": {},
        "vereda_display_map": {},
    }

def show_data_setup_instructions():
    """Muestra instrucciones de configuración."""
    st.error("❌ No se pudieron cargar los archivos de datos")
    
    with st.expander("📋 Instrucciones de configuración", expanded=True):
        st.markdown("""
        ### 🌐 Para Streamlit Cloud (Recomendado):
        1. **Configura Google Drive:**
           - Ejecuta: `python get_shapefiles_ids.py`
           - Copia los IDs resultantes a `.streamlit/secrets.toml`
           - Sube a Streamlit Cloud
        
        ### 📁 Para desarrollo local:
        1. **Coloca los archivos en:**
           - `📁 data/BD_positivos.xlsx`
           - `📁 data/Información_Datos_FA.xlsx`
           
           **O en el directorio raíz:**
           - `📄 BD_positivos.xlsx`
           - `📄 Información_Datos_FA.xlsx`
        """)

def create_empty_data_structure():
    """Estructura de datos vacía para casos de error."""
    return {
        "casos": pd.DataFrame(),
        "epizootias": pd.DataFrame(),
        "municipios_normalizados": [],
        "municipio_display_map": {},
        "veredas_por_municipio": {},
        "vereda_display_map": {},
    }

def show_fallback_summary(data_filtered, filters):
    """Resumen usando datos filtrados."""
    st.markdown("### 📊 Resumen de Datos Filtrados")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
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

def main():
    """Función principal del dashboard."""
    # Configurar página
    configure_page()
    
    # Sidebar básico
    try:
        from components.sidebar import init_responsive_sidebar
        init_responsive_sidebar()
    except ImportError:
        with st.sidebar:
            st.title("Dashboard Tolima")

    # Cargar datos
    logger.info("🔄 Iniciando carga de datos")
    data = load_data()

    if data["casos"].empty and data["epizootias"].empty:
        st.error("❌ No se pudieron cargar los datos")
        return

    logger.info(f"📊 Datos cargados: {len(data['casos'])} casos, {len(data['epizootias'])} epizootias")

    # Aplicar filtros
    logger.info("🔄 Aplicando sistema de filtros")
    filter_result = create_unified_filter_system(data)
    filters = filter_result["filters"]
    data_filtered = filter_result["data_filtered"]

    # Verificar filtrado
    casos_reduction = len(data["casos"]) - len(data_filtered["casos"])
    epi_reduction = len(data["epizootias"]) - len(data_filtered["epizootias"])
    
    if casos_reduction > 0 or epi_reduction > 0:
        logger.info(f"📊 Filtrado aplicado: -{casos_reduction} casos, -{epi_reduction} epizootias")

    # Pestañas principales
    tab1, tab2, tab3 = st.tabs([
        "🗺️ Mapas Interactivos",
        "📊 Información Detallada", 
        "📈 Seguimiento Temporal",
    ])

    with tab1:
        logger.info("🗺️ Mostrando vista de mapas")
        if "mapas" in vistas_modules and vistas_modules["mapas"]:
            try:
                vistas_modules["mapas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                logger.error(f"❌ Error en vista de mapas: {str(e)}")
                st.error(f"Error en módulo de mapas: {str(e)}")
                show_fallback_summary(data_filtered, filters)
        else:
            st.warning("⚠️ Vista de mapas no disponible")
            show_fallback_summary(data_filtered, filters)

    with tab2:
        logger.info("📊 Mostrando análisis detallado")
        if "tablas" in vistas_modules and vistas_modules["tablas"]:
            try:
                vistas_modules["tablas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                logger.error(f"❌ Error en análisis: {str(e)}")
                st.error(f"Error en módulo de análisis: {str(e)}")
                show_fallback_summary(data_filtered, filters)
        else:
            st.info("🔧 Módulo de análisis en desarrollo.")
            show_fallback_summary(data_filtered, filters)

    with tab3:
        logger.info("📈 Mostrando seguimiento temporal")
        if "comparativo" in vistas_modules and vistas_modules["comparativo"]:
            try:
                vistas_modules["comparativo"].show(data_filtered, filters, COLORS)
            except Exception as e:
                logger.error(f"❌ Error en seguimiento temporal: {str(e)}")
                st.error(f"Error en módulo temporal: {str(e)}")
                show_fallback_summary(data_filtered, filters)
        else:
            st.info("🔧 Módulo temporal en desarrollo.")
            show_fallback_summary(data_filtered, filters)

    # Footer
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(
            f"""
            <div style="text-align: center; color: #666; font-size: 0.75rem; padding: 0.5rem 0;">
                Dashboard Fiebre Amarilla v1.0<br>
                Desarrollado por: Ing. Jose Miguel Santos • Secretaría de Salud del Tolima • © 2025
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        active_filters = filters.get("active_filters", [])
        if active_filters:
            st.markdown(
                f"""
                <div style="background: {COLORS['info']}; color: white; padding: 0.4rem; border-radius: 6px; text-align: center; font-size: 0.7rem;">
                    🎯 {len(active_filters)} filtros activos
                </div>
                """,
                unsafe_allow_html=True,
            )

if __name__ == "__main__":
    main()