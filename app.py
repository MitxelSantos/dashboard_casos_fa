"""
app.py CORREGIDO - Flujo de datos unificado con DEBUGGING COMPLETO
ELIMINADOS: Múltiples sistemas de filtrado
CORREGIDO: Solo datos filtrados pasan a las vistas + logging detallado
AGREGADO: Verificación explícita de que las vistas reciben datos filtrados
"""

import os
import time
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FiebreAmarilla-Dashboard-v3.4-DEBUG")

# Configuraciones
os.environ["STREAMLIT_PAGES_ENABLED"] = "false"

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Crear directorios
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# Agregar rutas al path
import sys
sys.path.insert(0, str(ROOT_DIR))

# Importar configuraciones
try:
    from config.colors import COLORS
    from config.settings import DASHBOARD_CONFIG
    logger.info("✅ Configuraciones importadas")
except ImportError as e:
    logger.error(f"❌ Error importando configuraciones: {str(e)}")
    st.error(f"Error en configuraciones: {str(e)}")
    st.stop()

# Importar utilidades
try:
    from utils.data_processor import (
        excel_date_to_datetime,
        calculate_basic_metrics,
        get_latest_case_info,
        debug_data_flow,
        log_filter_application
    )
    logger.info("✅ Utilidades importadas")
except ImportError as e:
    logger.error(f"❌ Error importando utilidades: {str(e)}")
    st.error(f"Error en utilidades: {str(e)}")
    st.stop()

# Importar sistema de filtros UNIFICADO
try:
    from components.filters import create_unified_filter_system
    logger.info("✅ Sistema de filtros unificado importado")
except ImportError as e:
    logger.error(f"❌ Error importando filtros: {str(e)}")
    st.error(f"Error en sistema de filtros: {str(e)}")
    st.stop()

# Importar vistas con manejo de errores
vista_modules = ["mapas", "tablas", "comparativo"]
vistas_modules = {}

def import_vista_safely(module_name):
    """Importa una vista de manera segura."""
    try:
        module = __import__(f"vistas.{module_name}", fromlist=[module_name])
        if hasattr(module, 'show'):
            logger.info(f"✅ Vista {module_name} importada correctamente")
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

def debug_filter_application_ENHANCED(data, data_filtered, filters, stage):
    """
    DEBUG SÚPER DETALLADO para verificar aplicación de filtros
    """
    logger.info(f"🔧 DEBUG DETALLADO {stage}:")
    logger.info(f"   📊 Datos originales: {len(data.get('casos', []))} casos, {len(data.get('epizootias', []))} epizootias")
    logger.info(f"   🎯 Datos filtrados: {len(data_filtered.get('casos', []))} casos, {len(data_filtered.get('epizootias', []))} epizootias")
    
    active_filters = filters.get("active_filters", [])
    logger.info(f"   🎛️ Filtros activos: {len(active_filters)} - {active_filters[:3] if active_filters else 'Ninguno'}")
    
    # VERIFICAR SI REALMENTE HAY FILTRADO
    casos_orig = len(data.get('casos', []))
    casos_filt = len(data_filtered.get('casos', []))
    epi_orig = len(data.get('epizootias', []))
    epi_filt = len(data_filtered.get('epizootias', []))
    
    if casos_filt == casos_orig and epi_filt == epi_orig:
        if active_filters:
            logger.error(f"   ❌ CRÍTICO: Hay filtros activos pero no se aplicaron!")
            logger.error(f"      🎛️ Filtros reportados: {active_filters}")
            logger.error(f"      📊 Datos iguales: casos {casos_orig}={casos_filt}, epi {epi_orig}={epi_filt}")
            return False
        else:
            logger.info(f"   ℹ️ Sin filtros activos, datos completos correctos")
    else:
        logger.info(f"   ✅ Filtrado aplicado correctamente")
        casos_reduction = ((casos_orig - casos_filt) / casos_orig * 100) if casos_orig > 0 else 0
        epi_reduction = ((epi_orig - epi_filt) / epi_orig * 100) if epi_orig > 0 else 0
        logger.info(f"   📊 Reducción: {casos_reduction:.1f}% casos, {epi_reduction:.1f}% epizootias")
    
    # VERIFICAR CONSISTENCIA DE FILTROS
    municipio_filter = filters.get("municipio_display", "Todos")
    vereda_filter = filters.get("vereda_display", "Todas")
    
    if municipio_filter != "Todos":
        logger.info(f"   📍 Filtro municipio aplicado: {municipio_filter}")
        # Verificar que los datos filtrados realmente corresponden
        if not data_filtered["casos"].empty and "municipio" in data_filtered["casos"].columns:
            municipios_en_casos = data_filtered["casos"]["municipio"].unique()
            logger.info(f"   📊 Municipios en casos filtrados: {list(municipios_en_casos)}")
            if len(municipios_en_casos) > 1:
                logger.warning(f"   ⚠️ ADVERTENCIA: Múltiples municipios en datos 'filtrados'")
    
    if vereda_filter != "Todas":
        logger.info(f"   🏘️ Filtro vereda aplicado: {vereda_filter}")
        # Verificar que los datos filtrados realmente corresponden
        if not data_filtered["casos"].empty and "vereda" in data_filtered["casos"].columns:
            veredas_en_casos = data_filtered["casos"]["vereda"].unique()
            logger.info(f"   📊 Veredas en casos filtrados: {list(veredas_en_casos)}")
            if len(veredas_en_casos) > 1:
                logger.warning(f"   ⚠️ ADVERTENCIA: Múltiples veredas en datos 'filtrados'")
    
    return True

def verify_vista_receives_filtered_data(vista_name, data_filtered, filters):
    """
    NUEVA: Verifica específicamente que la vista reciba datos filtrados
    """
    logger.info(f"🎯 VERIFICACIÓN PRE-VISTA {vista_name.upper()}:")
    
    # Verificar estructura de data_filtered
    if not isinstance(data_filtered, dict):
        logger.error(f"   ❌ data_filtered no es dict: {type(data_filtered)}")
        return False
    
    if "casos" not in data_filtered or "epizootias" not in data_filtered:
        logger.error(f"   ❌ data_filtered falta claves: {list(data_filtered.keys())}")
        return False
    
    casos_count = len(data_filtered["casos"])
    epi_count = len(data_filtered["epizootias"])
    
    logger.info(f"   📦 Enviando a {vista_name}: {casos_count} casos, {epi_count} epizootias")
    
    # Verificar consistencia con filtros
    active_filters = filters.get("active_filters", [])
    if active_filters:
        logger.info(f"   🎛️ Con filtros: {' • '.join(active_filters[:2])}")
        
        # Verificar específicamente filtro de municipio
        municipio_filter = filters.get("municipio_display", "Todos")
        if municipio_filter != "Todos":
            if not data_filtered["casos"].empty and "municipio" in data_filtered["casos"].columns:
                municipios_unicos = data_filtered["casos"]["municipio"].unique()
                if municipio_filter not in municipios_unicos:
                    logger.error(f"   ❌ INCONSISTENCIA: Filtro {municipio_filter} pero casos tienen {list(municipios_unicos)}")
                    return False
                else:
                    logger.info(f"   ✅ Consistencia verificada: {municipio_filter} en datos")
    else:
        logger.info(f"   📊 Sin filtros activos, datos completos")
    
    return True

def load_enhanced_datasets():
    """
    CORREGIDO: Carga de datos con estructura simplificada y consistente.
    """
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("🔄 Cargando datos...")
        
        # Configuración de rutas
        casos_filename = "BD_positivos.xlsx"
        epizootias_filename = "Información_Datos_FA.xlsx"

        data_casos_path = DATA_DIR / casos_filename
        data_epizootias_path = DATA_DIR / epizootias_filename
        root_casos_path = ROOT_DIR / casos_filename
        root_epizootias_path = ROOT_DIR / epizootias_filename

        progress_bar.progress(20)
        
        # Estrategia de carga de archivos
        casos_df = None
        epizootias_df = None

        # Intentar cargar desde data/
        if data_casos_path.exists() and data_epizootias_path.exists():
            try:
                casos_df = pd.read_excel(data_casos_path, sheet_name="ACUMU", engine="openpyxl")
                epizootias_df = pd.read_excel(data_epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
                logger.info("✅ Datos cargados desde carpeta data/")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando desde data/: {str(e)}")

        # Fallback a directorio raíz
        if casos_df is None and root_casos_path.exists() and root_epizootias_path.exists():
            try:
                casos_df = pd.read_excel(root_casos_path, sheet_name="ACUMU", engine="openpyxl")
                epizootias_df = pd.read_excel(root_epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
                logger.info("✅ Datos cargados desde directorio raíz")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando desde raíz: {str(e)}")

        if casos_df is None or epizootias_df is None:
            st.error("❌ No se pudieron cargar los archivos de datos")
            return create_empty_data_structure()

        progress_bar.progress(50)
        status_text.text("🔧 Procesando datos...")

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

        # Renombrar columnas existentes
        existing_casos_columns = {k: v for k, v in casos_columns_map.items() if k in casos_df.columns}
        casos_df = casos_df.rename(columns=existing_casos_columns)

        existing_epi_columns = {k: v for k, v in epizootias_columns_map.items() if k in epizootias_df.columns}
        epizootias_df = epizootias_df.rename(columns=existing_epi_columns)

        progress_bar.progress(70)
        status_text.text("📅 Procesando fechas...")

        # Procesar fechas
        if "fecha_inicio_sintomas" in casos_df.columns:
            casos_df["fecha_inicio_sintomas"] = casos_df["fecha_inicio_sintomas"].apply(excel_date_to_datetime)

        if "fecha_recoleccion" in epizootias_df.columns:
            epizootias_df["fecha_recoleccion"] = epizootias_df["fecha_recoleccion"].apply(excel_date_to_datetime)

        progress_bar.progress(80)
        status_text.text("🔵 Filtrando epizootias positivas + en estudio...")

        # FILTRO CRÍTICO: Solo epizootias positivas + en estudio
        if "descripcion" in epizootias_df.columns:
            total_original = len(epizootias_df)
            epizootias_df["descripcion"] = epizootias_df["descripcion"].str.upper().str.strip()
            epizootias_df = epizootias_df[
                epizootias_df["descripcion"].isin(["POSITIVO FA", "EN ESTUDIO"])
            ]
            total_filtradas = len(epizootias_df)
            logger.info(f"🔵 Epizootias filtradas: {total_filtradas} de {total_original}")

        progress_bar.progress(90)
        status_text.text("🗺️ Creando estructura de datos...")

        # Crear listas de ubicaciones
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

        progress_bar.progress(100)
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()

        logger.info(f"✅ Datos cargados: {len(casos_df)} casos, {len(epizootias_df)} epizootias")
        logger.info(f"🗺️ Municipios: {len(todos_municipios)}")

        return {
            "casos": casos_df,
            "epizootias": epizootias_df,
            "municipios_normalizados": todos_municipios,
            "municipio_display_map": {municipio: municipio for municipio in todos_municipios},
            "veredas_por_municipio": {},  # Se llena dinámicamente
            "vereda_display_map": {},
        }

    except Exception as e:
        logger.error(f"💥 Error crítico cargando datos: {str(e)}")
        st.error(f"❌ Error crítico: {str(e)}")
        return create_empty_data_structure()

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

def configure_page():
    """Configura la página con espaciado optimizado y SIN scroll infinito."""
    st.set_page_config(
        page_title=DASHBOARD_CONFIG["page_title"],
        page_icon=DASHBOARD_CONFIG["page_icon"],
        layout=DASHBOARD_CONFIG["layout"],
        initial_sidebar_state=DASHBOARD_CONFIG["initial_sidebar_state"],
    )

    # CSS optimizado - CORREGIDO para evitar scroll infinito
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
        
        /* CORRECCIÓN CRÍTICA: Prevenir scroll infinito */
        html, body, [data-testid="stApp"] {{
            height: 100vh !important;
            max-height: 100vh !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }}
        
        .block-container {{
            padding-top: 0.5rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
            max-height: calc(100vh - 2rem) !important;
            overflow-y: auto !important;
        }}
        
        /* Limitar altura de gráficos */
        .js-plotly-plot {{
            max-height: 500px !important;
            overflow: hidden !important;
        }}
        
        /* Limitar altura de dataframes */
        .stDataFrame {{
            max-height: 400px !important;
            overflow-y: auto !important;
        }}
        
        /* Asegurar que las tabs no crezcan infinitamente */
        .stTabs [data-baseweb="tab-panel"] {{
            max-height: calc(100vh - 200px) !important;
            overflow-y: auto !important;
        }}
        
        .main-title {{
            color: var(--primary-color);
            font-size: clamp(1.6rem, 5vw, 2.2rem);
            font-weight: 700;
            margin-bottom: 0.75rem !important;
            text-align: center;
            padding: 0.75rem 1rem !important;
            border-bottom: 3px solid var(--secondary-color);
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def main():
    """
    FUNCIÓN PRINCIPAL CORREGIDA - Flujo de datos unificado CON DEBUG COMPLETO
    """
    # Configurar página
    configure_page()

    # Sidebar básico
    try:
        from components.sidebar import init_responsive_sidebar
        init_responsive_sidebar()
    except ImportError:
        with st.sidebar:
            st.title("Dashboard Tolima v3.4")

    # Cargar datos
    logger.info("🔄 INICIANDO CARGA DE DATOS ORIGINALES")
    data = load_enhanced_datasets()

    if data["casos"].empty and data["epizootias"].empty:
        st.error("❌ No se pudieron cargar los datos")
        st.info("Coloque los archivos de datos en la carpeta 'data/' y recargue la página.")
        return

    logger.info(f"📊 Datos originales cargados: {len(data['casos'])} casos, {len(data['epizootias'])} epizootias")

    # **APLICAR FILTROS - SISTEMA UNIFICADO CON DEBUG**
    logger.info("🔄 APLICANDO SISTEMA DE FILTROS UNIFICADO...")
    filter_result = create_unified_filter_system(data)
    filters = filter_result["filters"]
    data_filtered = filter_result["data_filtered"]

    # **DEBUG DETALLADO DEL FILTRADO**
    filter_success = debug_filter_application_ENHANCED(data, data_filtered, filters, "POST_FILTRADO_PRINCIPAL")
    
    if not filter_success:
        st.error("❌ CRÍTICO: Sistema de filtrado no funcionó correctamente")
        st.info("Revise el sidebar para filtros activos vs datos mostrados")
        
        # Debug para el usuario
        with st.expander("🔧 Debug de Filtrado", expanded=True):
            st.write("**Filtros reportados:**", filters.get("active_filters", []))
            st.write("**Datos originales:**", f"{len(data['casos'])} casos, {len(data['epizootias'])} epizootias")
            st.write("**Datos filtrados:**", f"{len(data_filtered['casos'])} casos, {len(data_filtered['epizootias'])} epizootias")

    # **LOGGING DE VERIFICACIÓN**
    logger.info(f"📊 RESULTADO FILTRADO FINAL:")
    logger.info(f"   🦠 Casos: {len(data['casos'])} → {len(data_filtered['casos'])}")
    logger.info(f"   🐒 Epizootias: {len(data['epizootias'])} → {len(data_filtered['epizootias'])}")
    logger.info(f"   🎯 Filtros activos: {len(filters.get('active_filters', []))}")

    # Mostrar información de filtrado si hay filtros activos
    active_filters = filters.get("active_filters", [])
    if active_filters:
        reduction_casos = len(data["casos"]) - len(data_filtered["casos"])
        reduction_epi = len(data["epizootias"]) - len(data_filtered["epizootias"])
        
        if reduction_casos > 0 or reduction_epi > 0:
            st.info(f"🎯 Filtros aplicados: {' • '.join(active_filters[:2])} {'• +' + str(len(active_filters)-2) + ' más' if len(active_filters) > 2 else ''}")
            st.caption(f"📊 Reducción: {reduction_casos} casos, {reduction_epi} epizootias filtradas")

    # **PESTAÑAS PRINCIPALES CON VERIFICACIÓN**
    tab1, tab2, tab3 = st.tabs([
        "🗺️ Mapas Interactivos",
        "📊 Análisis Detallado", 
        "📈 Seguimiento Temporal",
    ])

    with tab1:
        logger.info("🗺️ INICIANDO VISTA DE MAPAS...")
        
        # **VERIFICACIÓN PRE-VISTA**
        if verify_vista_receives_filtered_data("MAPAS", data_filtered, filters):
            
            if "mapas" in vistas_modules and vistas_modules["mapas"]:
                try:
                    # **PASAR SOLO DATOS FILTRADOS VERIFICADOS**
                    logger.info("🚀 Llamando vistas_modules['mapas'].show() con datos verificados")
                    vistas_modules["mapas"].show(data_filtered, filters, COLORS)
                    logger.info("✅ Vista de mapas completada exitosamente")
                    
                except Exception as e:
                    logger.error(f"❌ Error CRÍTICO en vista de mapas: {str(e)}")
                    st.error(f"Error en módulo de mapas: {str(e)}")
                    show_fallback_summary(data_filtered, filters)
            else:
                st.warning("⚠️ **Vista de mapas no disponible**")
                st.info("Las dependencias de mapas pueden no estar instaladas.")
                show_fallback_summary(data_filtered, filters)
        else:
            st.error("❌ Datos para vista de mapas no válidos")
            show_fallback_summary(data_filtered, filters)

    with tab2:
        logger.info("📊 INICIANDO ANÁLISIS DETALLADO...")
        
        # **VERIFICACIÓN PRE-VISTA**
        if verify_vista_receives_filtered_data("TABLAS", data_filtered, filters):
            
            if "tablas" in vistas_modules and vistas_modules["tablas"]:
                try:
                    # **PASAR SOLO DATOS FILTRADOS VERIFICADOS**
                    logger.info("🚀 Llamando vistas_modules['tablas'].show() con datos verificados")
                    vistas_modules["tablas"].show(data_filtered, filters, COLORS)
                    logger.info("✅ Vista de análisis completada exitosamente")
                    
                except Exception as e:
                    logger.error(f"❌ Error CRÍTICO en análisis: {str(e)}")
                    st.error(f"Error en módulo de análisis: {str(e)}")
                    show_fallback_summary(data_filtered, filters)
            else:
                st.info("🔧 Módulo de análisis en desarrollo.")
                show_fallback_summary(data_filtered, filters)
        else:
            st.error("❌ Datos para vista de análisis no válidos")
            show_fallback_summary(data_filtered, filters)

    with tab3:
        logger.info("📈 INICIANDO SEGUIMIENTO TEMPORAL...")
        
        # **VERIFICACIÓN PRE-VISTA**
        if verify_vista_receives_filtered_data("COMPARATIVO", data_filtered, filters):
            
            if "comparativo" in vistas_modules and vistas_modules["comparativo"]:
                try:
                    # **PASAR SOLO DATOS FILTRADOS VERIFICADOS**
                    logger.info("🚀 Llamando vistas_modules['comparativo'].show() con datos verificados")
                    vistas_modules["comparativo"].show(data_filtered, filters, COLORS)
                    logger.info("✅ Vista temporal completada exitosamente")
                    
                except Exception as e:
                    logger.error(f"❌ Error CRÍTICO en seguimiento temporal: {str(e)}")
                    st.error(f"Error en módulo temporal: {str(e)}")
                    show_fallback_summary(data_filtered, filters)
            else:
                st.info("🔧 Módulo de seguimiento temporal en desarrollo.")
                show_fallback_summary(data_filtered, filters)
        else:
            st.error("❌ Datos para vista temporal no válidos")
            show_fallback_summary(data_filtered, filters)

    # Footer con información de debug
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(
            f"""
            <div style="text-align: center; color: #666; font-size: 0.75rem; padding: 0.5rem 0;">
                Dashboard Fiebre Amarilla v3.4-DEBUG - Flujo Verificado<br>
                Desarrollado por: Ing. Jose Miguel Santos • Secretaría de Salud del Tolima • © 2025
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        # Mostrar estado del filtrado
        if active_filters:
            st.markdown(
                f"""
                <div style="background: {COLORS['info']}; color: white; padding: 0.4rem; border-radius: 6px; text-align: center; font-size: 0.7rem;">
                    🎯 {len(active_filters)} filtros activos
                </div>
                """,
                unsafe_allow_html=True,
            )

def show_fallback_summary(data_filtered, filters):
    """
    CORREGIDO: Resumen usando DATOS FILTRADOS con verificación explícita.
    """
    logger.info("📋 Mostrando resumen fallback con datos filtrados")
    
    st.markdown("### 📊 Resumen de Datos Filtrados")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # **LOG DE VERIFICACIÓN**
    logger.info(f"📊 Fallback summary: {len(casos)} casos filtrados, {len(epizootias)} epizootias filtradas")
    
    # **MÉTRICAS CON DATOS FILTRADOS VERIFICADOS**
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🦠 Casos (Filtrados)", len(casos))
    
    with col2:
        fallecidos = len(casos[casos["condicion_final"] == "Fallecido"]) if not casos.empty and "condicion_final" in casos.columns else 0
        st.metric("⚰️ Fallecidos (Filtrados)", fallecidos)
    
    with col3:
        st.metric("🐒 Epizootias (Filtradas)", len(epizootias))
    
    with col4:
        positivas = len(epizootias[epizootias["descripcion"] == "POSITIVO FA"]) if not epizootias.empty and "descripcion" in epizootias.columns else 0
        st.metric("🔴 Positivas (Filtradas)", positivas)
    
    # Información de filtros activos
    active_filters = filters.get("active_filters", [])
    if active_filters:
        st.markdown("**🎯 Filtros Activos:**")
        for filtro in active_filters:
            st.caption(f"• {filtro}")
    else:
        st.info("📊 Mostrando datos completos del Tolima")

if __name__ == "__main__":
    main()