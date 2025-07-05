"""
Aplicación principal ACTUALIZADA del Dashboard de Fiebre Amarilla v3.2
MEJORAS:
- Carga epizootias POSITIVAS + EN ESTUDIO
- Sistema inteligente de mapeo de veredas
- Manejo mejorado de municipios sin datos
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
logger = logging.getLogger("FiebreAmarilla-Dashboard-v3.2")

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
    create_intelligent_vereda_mapping,  # NUEVO
)

# Importar utilidades de interacciones de mapa
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


def load_enhanced_datasets():
    """
    ACTUALIZADO: Carga datasets con epizootias positivas + en estudio y mapeo inteligente de veredas.
    """
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("🔄 Inicializando carga de datos v3.2...")

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
        status_text.text("🔵 Procesando epizootias: positivas + en estudio...")

        # ==================== NUEVO: PROCESAR EPIZOOTIAS (POSITIVAS + EN ESTUDIO) ====================
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

        if "descripcion" in epizootias_df.columns:
            # **DEBUG: Mostrar valores únicos ANTES del filtrado**
            unique_descriptions = epizootias_df["descripcion"].dropna().unique()
            logger.info("🔍 DEBUG - Valores únicos en 'descripcion' (RAW):")
            for desc in unique_descriptions:
                logger.info(f"   '{desc}' (tipo: {type(desc)})")
            
            # **NORMALIZACIÓN MEJORADA** - Más robusta
            epizootias_df["descripcion"] = (
                epizootias_df["descripcion"]
                .astype(str)
                .str.upper()
                .str.strip()
                .str.replace(r'\s+', ' ', regex=True)  # Normalizar espacios múltiples
            )
            
            # **DEBUG: Después de normalización**
            unique_descriptions_norm = epizootias_df["descripcion"].dropna().unique()
            logger.info("🔍 DEBUG - Valores únicos en 'descripcion' (NORMALIZADO):")
            for desc in unique_descriptions_norm:
                logger.info(f"   '{desc}'")
            
            # **FILTRADO MÁS FLEXIBLE** - Múltiples patrones
            total_original = len(epizootias_df)
            
            # Patrones flexibles para coincidencias
            patrones_positivo = ["POSITIVO FA", "POSITIVO", "POSITIVA FA", "POSITIVA"]
            patrones_estudio = ["EN ESTUDIO", "ESTUDIO", "EN ANALISIS", "ANALISIS"]
            
            # Crear máscara de filtrado
            mask_positivo = epizootias_df["descripcion"].isin(patrones_positivo)
            mask_estudio = epizootias_df["descripcion"].isin(patrones_estudio)
            
            # **FILTRADO POR CONTENIDO** si no hay coincidencias exactas
            if not mask_positivo.any():
                logger.info("⚠️ Sin coincidencias exactas para POSITIVO, probando por contenido...")
                mask_positivo = epizootias_df["descripcion"].str.contains("POSITIV", na=False)
            
            if not mask_estudio.any():
                logger.info("⚠️ Sin coincidencias exactas para ESTUDIO, probando por contenido...")
                mask_estudio = epizootias_df["descripcion"].str.contains("ESTUDIO", na=False)
            
            # Combinar máscaras
            mask_final = mask_positivo | mask_estudio
            
            # Aplicar filtro
            epizootias_df = epizootias_df[mask_final]
            total_filtradas = len(epizootias_df)
            
            # **CONTEO DETALLADO**
            positivas_count = mask_positivo.sum()
            en_estudio_count = mask_estudio.sum()
            
            # **LOG DETALLADO**
            logger.info(f"🔵 FILTRO EPIZOOTIAS APLICADO:")
            logger.info(f"   📊 Total original: {total_original}")
            logger.info(f"   ✅ Total filtradas: {total_filtradas}")
            logger.info(f"   🔴 Positivas: {positivas_count}")
            logger.info(f"   🔵 En estudio: {en_estudio_count}")
            
            status_text.text(f"🔵 Epizootias procesadas: {total_filtradas} ({positivas_count} positivas + {en_estudio_count} en estudio)")
            
            # **GUARDAR PARA DEBUGGING**
            st.session_state["epizootias_debug"] = {
                "total_original": total_original,
                "total_filtradas": total_filtradas,
                "positivas": positivas_count,
                "en_estudio": en_estudio_count,
                "valores_originales": unique_descriptions.tolist(),
                "valores_normalizados": unique_descriptions_norm.tolist(),
                "patrones_usados": {
                    "positivo": patrones_positivo,
                    "estudio": patrones_estudio
                }
            }
            
            # **VALIDACIÓN FINAL**
            if total_filtradas == 0:
                logger.warning("⚠️ ADVERTENCIA: Después del filtrado no quedaron epizootias")
                status_text.text("⚠️ Sin epizootias después del filtrado - verificar datos")

        # Normalizar municipios y veredas en epizootias (solo las filtradas)
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
        status_text.text("🗺️ Creando mapeos maestros con sistema inteligente...")

        # ==================== NUEVO: SISTEMA INTELIGENTE DE MAPEO DE VEREDAS ====================
        # Crear mapeo inteligente de veredas
        try:
            vereda_mapping = create_intelligent_vereda_mapping(casos_df, epizootias_df)
            logger.info(f"✅ Sistema de mapeo inteligente creado: {len(vereda_mapping)} mapeos")
        except Exception as e:
            logger.warning(f"⚠️ Error en mapeo inteligente: {str(e)}")
            vereda_mapping = {}
            
        # ==================== APLICAR MAPEO INTELIGENTE ====================
        # Aplicar mapeo a casos
        if vereda_mapping and not casos_df.empty and "vereda" in casos_df.columns:
            from utils.data_processor import apply_vereda_mapping
            casos_df = apply_vereda_mapping(casos_df, "vereda", vereda_mapping)
            logger.info("✅ Mapeo aplicado a casos")

        # Aplicar mapeo a epizootias  
        if vereda_mapping and not epizootias_df.empty and "vereda" in epizootias_df.columns:
            from utils.data_processor import apply_vereda_mapping
            epizootias_df = apply_vereda_mapping(epizootias_df, "vereda", vereda_mapping)
            logger.info("✅ Mapeo aplicado a epizootias")

        # Obtener todos los municipios únicos (normalizados)
        municipios_casos = set(casos_df["municipio_normalizado"].dropna()) if not casos_df.empty else set()
        municipios_epizootias = set(epizootias_df["municipio_normalizado"].dropna()) if not epizootias_df.empty else set()
        municipios_normalizados = sorted(municipios_casos.union(municipios_epizootias))

        # NUEVO: Crear lista completa de municipios del Tolima para manejar clics en grises
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

        # Agregar municipios sin datos a la lista (para manejar clics en grises)
        for municipio_tolima in municipios_tolima_completos:
            if municipio_tolima not in municipios_normalizados:
                municipios_normalizados.append(municipio_tolima)

        municipios_normalizados = sorted(municipios_normalizados)

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
            ) if not casos_df.empty else []
            opciones_epi = (
                epizootias_df[epizootias_df["municipio_normalizado"] == municipio_norm][
                    "municipio"
                ]
                .dropna()
                .unique()
            ) if not epizootias_df.empty else []

            todas_opciones = list(opciones_casos) + list(opciones_epi)
            if todas_opciones:
                municipio_display_map[municipio_norm] = todas_opciones[0]
            else:
                # Para municipios sin datos, usar versión capitalizada
                municipio_display_map[municipio_norm] = capitalize_names(municipio_norm)

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
            ) if not casos_df.empty else []
            # Obtener veredas de epizootias (positivas + en estudio)
            veredas_epi = (
                epizootias_df[epizootias_df["municipio_normalizado"] == municipio_norm][
                    "vereda_normalizada"
                ]
                .dropna()
                .unique()
            ) if not epizootias_df.empty else []

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
                ) if not casos_df.empty else []

                opciones_epi = (
                    epizootias_df[
                        (epizootias_df["municipio_normalizado"] == municipio_norm)
                        & (epizootias_df["vereda_normalizada"] == vereda_norm)
                    ]["vereda"]
                    .dropna()
                    .unique()
                ) if not epizootias_df.empty else []

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
                "categoria": "Fallecido",
            },
            "Vivo": {"color": COLORS["success"], "icon": "💚", "categoria": "Vivo"},
        }

        # NUEVO: Mapeo de descripción (positivas + en estudio)
        descripcion_map = {
            "POSITIVO FA": {
                "color": COLORS["danger"],
                "icon": "🔴",
                "categoria": "Positivo",
                "descripcion": "Confirma circulación viral activa"
            },
            "EN ESTUDIO": {
                "color": COLORS["info"],
                "icon": "🔵",
                "categoria": "En Estudio",
                "descripcion": "Muestra en proceso de análisis laboratorial"
            },
        }

        progress_bar.progress(100)

        # Limpiar elementos de UI con delay para legibilidad
        import time
        time.sleep(1.5)
        status_text.empty()
        progress_bar.empty()

        # Inicializar sistema de interacciones de mapa si está disponible
        if MAP_INTERACTIONS_AVAILABLE:
            interaction_manager = get_interaction_manager()
            bounds_manager = get_bounds_manager()
            logger.info("✅ Sistema de interacciones de mapa inicializado")

        # Log final con estadísticas ACTUALIZADAS
        logger.info(f"✅ Datos cargados exitosamente desde: {data_source}")
        logger.info(f"📊 Casos cargados: {len(casos_df)}")
        
        # Estadísticas detalladas de epizootias
        positivas_count = len(epizootias_df[epizootias_df["descripcion"] == "POSITIVO FA"]) if not epizootias_df.empty else 0
        en_estudio_count = len(epizootias_df[epizootias_df["descripcion"] == "EN ESTUDIO"]) if not epizootias_df.empty else 0
        logger.info(f"🔵 Epizootias cargadas: {len(epizootias_df)} total ({positivas_count} positivas + {en_estudio_count} en estudio)")
        logger.info(f"🗺️ Municipios únicos: {len(municipios_normalizados)} (incluyendo {len(municipios_tolima_completos)} del Tolima)")

        return {
            "casos": casos_df,
            "epizootias": epizootias_df,  # Ahora contiene positivas + en estudio
            "municipios_normalizados": municipios_normalizados,
            "municipio_display_map": municipio_display_map,
            "veredas_por_municipio": veredas_por_municipio,
            "vereda_display_map": vereda_display_map,
            "condicion_map": condicion_map,
            "descripcion_map": descripcion_map,
            "vereda_mapping": vereda_mapping,  # NUEVO
            "data_source": data_source,
        }

    except Exception as e:
        logger.error(f"💥 Error crítico al cargar los datos: {str(e)}")
        st.error(f"❌ Error crítico al cargar los datos: {str(e)}")
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

def show_epizootias_debug_info():
    """
    NUEVA: Función para mostrar información de debug de epizootias en el sidebar.
    """
    if "epizootias_debug" in st.session_state:
        debug_info = st.session_state["epizootias_debug"]
        
        with st.sidebar.expander("🔍 Debug Epizootias", expanded=False):
            st.markdown("**📊 Estadísticas de Filtrado:**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Original", debug_info['total_original'])
                st.metric("Positivas", debug_info['positivas'])
            with col2:
                st.metric("Filtradas", debug_info['total_filtradas'])
                st.metric("En Estudio", debug_info['en_estudio'])
            
            st.markdown("**🔍 Valores Encontrados (Raw):**")
            for i, val in enumerate(debug_info.get('valores_originales', [])[:5]):
                st.code(f"{i+1}. '{val}'")
            
            if len(debug_info.get('valores_originales', [])) > 5:
                st.caption(f"... y {len(debug_info['valores_originales']) - 5} más")
            
            st.markdown("**✅ Valores Normalizados:**")
            for i, val in enumerate(debug_info.get('valores_normalizados', [])[:5]):
                st.code(f"{i+1}. '{val}'")
            
            st.markdown("**🎯 Patrones de Búsqueda:**")
            patrones = debug_info.get('patrones_usados', {})
            st.json(patrones)

def create_filters_responsive_with_maps_enhanced(data):
    """Crea sistema de filtros MEJORADO con sincronización bidireccional completa."""
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
    Aplicación principal del dashboard v3.2 ACTUALIZADA.
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
            st.title("Dashboard Tolima v3.2")

    # Cargar datos con indicadores responsive (POSITIVAS + EN ESTUDIO)
    data = load_enhanced_datasets()
    
    show_epizootias_debug_info()

    if data["casos"].empty and data["epizootias"].empty:
        # Error responsive con instrucciones claras
        st.error("❌ No se pudieron cargar los datos")
        st.info("Coloque los archivos de datos en la carpeta 'data/' y recargue la página.")
        return

    # Mostrar información sobre el filtro de epizootias actualizado
    total_epizootias = len(data["epizootias"])
    if total_epizootias > 0:
        positivas_count = len(data["epizootias"][data["epizootias"]["descripcion"] == "POSITIVO FA"]) if not data["epizootias"].empty else 0
        en_estudio_count = len(data["epizootias"][data["epizootias"]["descripcion"] == "EN ESTUDIO"]) if not data["epizootias"].empty else 0
        st.success(f"✅ Dashboard v3.2 - Datos cargados: {len(data['casos'])} casos confirmados y {total_epizootias} epizootias ({positivas_count} positivas + {en_estudio_count} en estudio)")

    # Crear filtros responsive con integración de mapas MEJORADOS
    filters, data_filtered = create_filters_responsive_with_maps_enhanced(data)

    # Manejar interacciones del mapa
    handle_map_interactions(data_filtered, filters, COLORS)

    # **TÍTULO PRINCIPAL CORREGIDO** - Sin espaciado excesivo
    st.markdown(
        '<h1 class="main-title">🗺️ Dashboard Fiebre Amarilla v3.2</h1>',
        unsafe_allow_html=True,
    )

    # Mostrar indicador de sincronización si está activa
    if filters.get("active_filters"):
        filter_count = len(filters["active_filters"])
        st.markdown(
            f"""
            <div class="sync-indicator">
                🔄 Filtros activos: {filter_count}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # PESTAÑAS PRINCIPALES ACTUALIZADAS v3.2
    tab1, tab2, tab3 = st.tabs(
        [
            "🗺️ Mapas Interactivos",      # Mapas CON todas las tarjetas mejoradas
            "📊 Análisis Epidemiológico", # Tablas detalladas e interactivas
            "📈 Seguimiento Temporal",
        ]
    )

    with tab1:
        # Vista de mapas CON todas las tarjetas informativas MEJORADAS
        if "mapas" in vistas_modules and vistas_modules["mapas"]:
            try:
                # Pasar data filtrada para que los mapas trabajen con positivas + en estudio
                vistas_modules["mapas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                st.error(f"Error en módulo de mapas: {str(e)}")
                st.exception(e)  # Mostrar traceback completo para debug
                st.info("🗺️ Vista de mapas en desarrollo.")
        else:
            st.info("🗺️ Vista de mapas en desarrollo.")

    with tab2:
        # NUEVO: Análisis epidemiológico con tablas detalladas e interactivas
        if "tablas" in vistas_modules and vistas_modules["tablas"]:
            try:
                vistas_modules["tablas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                st.error(f"Error en módulo de análisis epidemiológico: {str(e)}")
                st.info("🔧 Vista de análisis epidemiológico en desarrollo.")
        else:
            st.info("🔧 Módulo de análisis epidemiológico en desarrollo.")

    with tab3:
        # Seguimiento temporal (actualizado para manejar positivas + en estudio)
        if "comparativo" in vistas_modules and vistas_modules["comparativo"]:
            try:
                vistas_modules["comparativo"].show(data_filtered, filters, COLORS)
            except Exception as e:
                st.error(f"Error en módulo de seguimiento temporal: {str(e)}")
                st.info("🔧 Vista de seguimiento temporal en desarrollo.")
        else:
            st.info("🔧 Módulo de seguimiento temporal en desarrollo.")

    # Footer con información de versión (espaciado reducido)
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #666; font-size: 0.75rem; padding: 0.5rem 0; margin-top: 0.5rem;">
            Dashboard Fiebre Amarilla v3.2 - Sistema Inteligente de Mapeo<br>
            Desarrollado para la Secretaría de Salud del Tolima • © 2025
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()