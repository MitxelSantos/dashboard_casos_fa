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
logger = logging.getLogger("FiebreAmarilla-Dashboard")

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

from utils.data_processor import normalize_text, excel_date_to_datetime, capitalize_names

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
    Carga los nuevos datasets de casos confirmados y epizootias con normalización robusta.
    Busca primero en carpeta data/, luego en directorio raíz, y finalmente en Google Drive.
    
    Returns:
        dict: Diccionario con los dataframes cargados.
    """
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("🔄 Inicializando carga de datos...")
        
        # ==================== CONFIGURACIÓN DE RUTAS ====================
        # Definir nombres de archivos
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
        
        # Estrategia 1: Intentar cargar desde carpeta data/ (PRIORIDAD MÁXIMA)
        if data_casos_path.exists() and data_epizootias_path.exists():
            try:
                status_text.text("📂 Cargando desde carpeta data/ (recomendado)...")
                casos_df = pd.read_excel(data_casos_path, sheet_name="ACUMU", engine="openpyxl")
                epizootias_df = pd.read_excel(data_epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
                data_source = "data_folder"
                logger.info("✅ Datos cargados exitosamente desde carpeta data/")
                st.success("✅ Archivos cargados desde data/ (recomendado)")
            except Exception as e:
                logger.warning(f"⚠️ Error al cargar desde carpeta data/: {str(e)}")
                casos_df = None
                epizootias_df = None
        
        # Estrategia 2: Intentar cargar desde directorio raíz
        if casos_df is None and root_casos_path.exists() and root_epizootias_path.exists():
            try:
                status_text.text("📁 Cargando desde directorio raíz...")
                casos_df = pd.read_excel(root_casos_path, sheet_name="ACUMU", engine="openpyxl")
                epizootias_df = pd.read_excel(root_epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
                data_source = "root_folder"
                logger.info("✅ Datos cargados exitosamente desde directorio raíz")
            except Exception as e:
                logger.warning(f"⚠️ Error al cargar desde directorio raíz: {str(e)}")
                casos_df = None
                epizootias_df = None
        
        # Estrategia 3: Intentar cargar desde Google Drive (FALLBACK)
        if casos_df is None:
            try:
                # Importar utilidades de Google Drive
                from gdrive_utils import get_file_from_drive, check_google_drive_availability
                
                if check_google_drive_availability():
                    status_text.text("☁️ Archivos locales no encontrados. Intentando cargar desde Google Drive...")
                    progress_bar.progress(20)
                    
                    # Verificar si están configurados los IDs de Google Drive
                    if hasattr(st.secrets, "drive_files"):
                        drive_files = st.secrets.drive_files
                        
                        # Cargar casos desde Google Drive
                        if "casos_confirmados" in drive_files:
                            casos_path = get_file_from_drive(
                                drive_files["casos_confirmados"], 
                                casos_filename
                            )
                            if casos_path and Path(casos_path).exists():
                                casos_df = pd.read_excel(casos_path, sheet_name="ACUMU", engine="openpyxl")
                                logger.info("✅ Casos cargados desde Google Drive")
                        
                        # Cargar epizootias desde Google Drive
                        if "epizootias" in drive_files:
                            epi_path = get_file_from_drive(
                                drive_files["epizootias"], 
                                epizootias_filename
                            )
                            if epi_path and Path(epi_path).exists():
                                epizootias_df = pd.read_excel(epi_path, sheet_name="Base de Datos", engine="openpyxl")
                                logger.info("✅ Epizootias cargadas desde Google Drive")
                        
                        if casos_df is not None and epizootias_df is not None:
                            data_source = "google_drive"
                            st.success("☁️ Archivos cargados desde Google Drive")
                        else:
                            st.warning("⚠️ No se pudieron cargar todos los archivos desde Google Drive")
                    else:
                        st.warning("⚠️ Google Drive no está configurado (falta drive_files en secrets)")
                else:
                    st.warning("⚠️ Google Drive no está disponible")
                    
            except ImportError:
                st.warning("⚠️ Utilidades de Google Drive no disponibles")
            except Exception as e:
                logger.error(f"❌ Error al cargar desde Google Drive: {str(e)}")
                st.error(f"❌ Error al cargar desde Google Drive: {str(e)}")
        
        # ==================== VALIDACIÓN Y MENSAJE DE ERROR RESPONSIVE ====================
        if casos_df is None or epizootias_df is None:
            # Mostrar información sobre ubicaciones esperadas de manera responsive
            st.error("❌ No se pudieron cargar los archivos de datos")
            
            # Crear UI responsive para mostrar instrucciones
            with st.expander("📁 Instrucciones de Setup", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(
                        """
                        ### 🎯 Estructura Recomendada (data/)
                        ```
                        proyecto/
                        ├── data/                          ← CREAR ESTA CARPETA
                        │   ├── BD_positivos.xlsx         ← Casos confirmados
                        │   ├── Información_Datos_FA.xlsx ← Epizootias  
                        │   └── Gobernacion.png           ← Logo (opcional)
                        └── app.py
                        ```
                        
                        ### ⚠️ Estructura Alternativa (raíz)
                        ```
                        proyecto/
                        ├── BD_positivos.xlsx
                        ├── Información_Datos_FA.xlsx
                        ├── Gobernacion.png
                        └── app.py
                        ```
                        """
                    )
                
                with col2:
                    st.markdown(
                        """
                        ### 📋 Archivos Requeridos
                        
                        **Excel con hojas específicas:**
                        - `BD_positivos.xlsx` 
                          - Hoja: "ACUMU"
                        - `Información_Datos_FA.xlsx`
                          - Hoja: "Base de Datos"
                        
                        **Logo (opcional):**
                        - `Gobernacion.png`
                        """
                    )
            
            return {
                "casos": pd.DataFrame(),
                "epizootias": pd.DataFrame(),
                "municipios_normalizados": [],
                "municipio_display_map": {},
                "veredas_por_municipio": {},
                "vereda_display_map": {},
                "condicion_map": {},
                "descripcion_map": {},
                "data_source": "none"
            }
        
        progress_bar.progress(30)
        status_text.text("🔧 Limpiando y procesando datos...")
        
        # ==================== PROCESAMIENTO DE DATOS ====================
        # Limpiar datos de casos
        casos_df = casos_df.dropna(how='all')
        
        # Mapear columnas de casos
        casos_columns_map = {
            'edad_': 'edad',
            'sexo_': 'sexo', 
            'vereda_': 'vereda',
            'nmun_proce': 'municipio',
            'cod_ase_': 'eps',
            'Condición Final': 'condicion_final',
            'Inicio de sintomas': 'fecha_inicio_sintomas'
        }
        
        # Renombrar columnas existentes
        existing_casos_columns = {k: v for k, v in casos_columns_map.items() if k in casos_df.columns}
        casos_df = casos_df.rename(columns=existing_casos_columns)
        
        # Normalizar municipios y veredas en casos
        if 'municipio' in casos_df.columns:
            casos_df['municipio_normalizado'] = casos_df['municipio'].apply(normalize_text)
            casos_df['municipio'] = casos_df['municipio'].apply(capitalize_names)
        if 'vereda' in casos_df.columns:
            casos_df['vereda_normalizada'] = casos_df['vereda'].apply(normalize_text)
            casos_df['vereda'] = casos_df['vereda'].apply(capitalize_names)
        
        # Convertir fechas de casos
        if 'fecha_inicio_sintomas' in casos_df.columns:
            casos_df['fecha_inicio_sintomas'] = casos_df['fecha_inicio_sintomas'].apply(excel_date_to_datetime)
        
        progress_bar.progress(50)
        status_text.text("🐒 Procesando datos de epizootias...")
        
        # ==================== PROCESAR EPIZOOTIAS ====================
        # Limpiar datos de epizootias
        epizootias_df = epizootias_df.dropna(how='all')
        
        # Mapear columnas de epizootias
        epizootias_columns_map = {
            'MUNICIPIO': 'municipio',
            'VEREDA': 'vereda',
            'FECHA RECOLECCIÓN ': 'fecha_recoleccion',
            'PROVENIENTE ': 'proveniente',
            'DESCRIPCIÓN': 'descripcion'
        }
        
        # Renombrar columnas existentes
        existing_epi_columns = {k: v for k, v in epizootias_columns_map.items() if k in epizootias_df.columns}
        epizootias_df = epizootias_df.rename(columns=existing_epi_columns)
        
        # Normalizar municipios y veredas en epizootias
        if 'municipio' in epizootias_df.columns:
            epizootias_df['municipio_normalizado'] = epizootias_df['municipio'].apply(normalize_text)
            epizootias_df['municipio'] = epizootias_df['municipio'].apply(capitalize_names)
        if 'vereda' in epizootias_df.columns:
            epizootias_df['vereda_normalizada'] = epizootias_df['vereda'].apply(normalize_text)
            epizootias_df['vereda'] = epizootias_df['vereda'].apply(capitalize_names)
        
        # Convertir fechas de epizootias
        if 'fecha_recoleccion' in epizootias_df.columns:
            epizootias_df['fecha_recoleccion'] = epizootias_df['fecha_recoleccion'].apply(excel_date_to_datetime)
        
        progress_bar.progress(70)
        status_text.text("🗺️ Creando mapeos maestros...")
        
        # ==================== CREAR MAPEOS MAESTROS ====================
        
        # Obtener todos los municipios únicos (normalizados)
        municipios_casos = set(casos_df['municipio_normalizado'].dropna())
        municipios_epizootias = set(epizootias_df['municipio_normalizado'].dropna())
        municipios_normalizados = sorted(municipios_casos.union(municipios_epizootias))
        
        # Crear mapeo de municipios (normalizado -> original más común)
        municipio_display_map = {}
        for municipio_norm in municipios_normalizados:
            # Buscar la versión original más común para mostrar
            opciones_casos = casos_df[casos_df['municipio_normalizado'] == municipio_norm]['municipio'].dropna().unique()
            opciones_epi = epizootias_df[epizootias_df['municipio_normalizado'] == municipio_norm]['municipio'].dropna().unique()
            
            todas_opciones = list(opciones_casos) + list(opciones_epi)
            if todas_opciones:
                municipio_display_map[municipio_norm] = todas_opciones[0]
            else:
                municipio_display_map[municipio_norm] = municipio_norm
        
        # Crear diccionario de veredas por municipio (normalizado)
        veredas_por_municipio = {}
        for municipio_norm in municipios_normalizados:
            # Obtener veredas de casos
            veredas_casos = casos_df[casos_df['municipio_normalizado'] == municipio_norm]['vereda_normalizada'].dropna().unique()
            # Obtener veredas de epizootias
            veredas_epi = epizootias_df[epizootias_df['municipio_normalizado'] == municipio_norm]['vereda_normalizada'].dropna().unique()
            
            # Combinar y ordenar
            todas_veredas = sorted(set(list(veredas_casos) + list(veredas_epi)))
            veredas_por_municipio[municipio_norm] = todas_veredas
        
        # Crear mapeo de veredas para display
        vereda_display_map = {}
        for municipio_norm in municipios_normalizados:
            vereda_display_map[municipio_norm] = {}
            for vereda_norm in veredas_por_municipio[municipio_norm]:
                # Buscar versión original de la vereda
                opciones_casos = casos_df[
                    (casos_df['municipio_normalizado'] == municipio_norm) & 
                    (casos_df['vereda_normalizada'] == vereda_norm)
                ]['vereda'].dropna().unique()
                
                opciones_epi = epizootias_df[
                    (epizootias_df['municipio_normalizado'] == municipio_norm) & 
                    (epizootias_df['vereda_normalizada'] == vereda_norm)
                ]['vereda'].dropna().unique()
                
                todas_opciones = list(opciones_casos) + list(opciones_epi)
                if todas_opciones:
                    vereda_display_map[municipio_norm][vereda_norm] = todas_opciones[0]
                else:
                    vereda_display_map[municipio_norm][vereda_norm] = vereda_norm
        
        progress_bar.progress(90)
        status_text.text("📊 Finalizando carga...")
        
        # ==================== MAPEOS DE VALORES ====================
        
        # Mapeo de condición final
        condicion_map = {
            'Fallecido': {'color': COLORS['danger'], 'icon': '⚰️', 'categoria': 'Crítico'},
            'Vivo': {'color': COLORS['success'], 'icon': '💚', 'categoria': 'Bueno'}
        }
        
        # Mapeo de descripción de epizootias
        descripcion_map = {
            'POSITIVO FA': {'color': COLORS['danger'], 'icon': '🔴', 'categoria': 'Positivo'},
            'NEGATIVO FA': {'color': COLORS['success'], 'icon': '🟢', 'categoria': 'Negativo'},
            'NO APTA': {'color': COLORS['warning'], 'icon': '🟡', 'categoria': 'No apta'},
            'EN ESTUDIO': {'color': COLORS['info'], 'icon': '🔵', 'categoria': 'En estudio'}
        }
        
        progress_bar.progress(100)
        
        # Mostrar información sobre la fuente de datos utilizada
        source_messages = {
            "data_folder": "✅ Datos cargados desde carpeta data/ (recomendado)",
            "root_folder": "✅ Datos cargados desde directorio raíz",
            "google_drive": "☁️ Datos cargados desde Google Drive"
        }
        
        if data_source:
            status_text.text(source_messages.get(data_source, "✅ Datos cargados correctamente"))
        else:
            status_text.text("✅ Datos cargados correctamente")
        
        # Limpiar elementos de UI con delay para legibilidad
        import time
        time.sleep(1.5)
        status_text.empty()
        progress_bar.empty()
        
        # Log final con estadísticas
        logger.info(f"✅ Datos cargados exitosamente desde: {data_source}")
        logger.info(f"📊 Casos cargados: {len(casos_df)}")
        logger.info(f"🐒 Epizootias cargadas: {len(epizootias_df)}")
        logger.info(f"🗺️ Municipios únicos: {len(municipios_normalizados)}")
        
        return {
            "casos": casos_df,
            "epizootias": epizootias_df,
            "municipios_normalizados": municipios_normalizados,
            "municipio_display_map": municipio_display_map,
            "veredas_por_municipio": veredas_por_municipio,
            "vereda_display_map": vereda_display_map,
            "condicion_map": condicion_map,
            "descripcion_map": descripcion_map,
            "data_source": data_source
        }
        
    except Exception as e:
        logger.error(f"💥 Error crítico al cargar los datos: {str(e)}")
        st.error(f"❌ Error crítico al cargar los datos: {str(e)}")
        
        return {
            "casos": pd.DataFrame(),
            "epizootias": pd.DataFrame(),
            "municipios_normalizados": [],
            "municipio_display_map": {},
            "veredas_por_municipio": {},
            "vereda_display_map": {},
            "condicion_map": {},
            "descripcion_map": {},
            "data_source": "error"
        }

def create_filters_responsive(data):
    """
    Crea sistema de filtros completamente responsive usando el nuevo componente.
    """
    # Importar el sistema de filtros responsive
    try:
        from components.filters import create_complete_filter_system
        
        # Usar el sistema completo de filtros responsive
        filter_result = create_complete_filter_system(data)
        return filter_result["filters"], filter_result["data_filtered"]
        
    except ImportError:
        # Fallback al sistema básico si no está disponible
        st.sidebar.subheader("🔍 Filtros Básicos")
        
        # Filtro de municipio básico
        municipio_options = ["Todos"] + [
            data["municipio_display_map"][norm] for norm in data["municipios_normalizados"]
        ]
        
        municipio_selected = st.sidebar.selectbox(
            "📍 Municipio:",
            municipio_options,
            key="municipio_filter"
        )
        
        # Determinar municipio normalizado seleccionado
        municipio_norm_selected = None
        if municipio_selected != "Todos":
            for norm, display in data["municipio_display_map"].items():
                if display == municipio_selected:
                    municipio_norm_selected = norm
                    break
        
        # Filtro de tipo de datos
        tipo_datos = st.sidebar.multiselect(
            "📋 Mostrar:",
            ["Casos Confirmados", "Epizootias"],
            default=["Casos Confirmados", "Epizootias"],
            key="tipo_datos_filter"
        )
        
        # Aplicar filtros básicos
        casos_filtrados = data["casos"].copy()
        epizootias_filtradas = data["epizootias"].copy()
        
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
            **{k: v for k, v in data.items() if k not in ["casos", "epizootias"]}
        }
        
        filters = {
            "municipio_display": municipio_selected,
            "municipio_normalizado": municipio_norm_selected,
            "tipo_datos": tipo_datos,
            "active_filters": [f"Municipio: {municipio_selected}"] if municipio_selected != "Todos" else []
        }
        
        return filters, data_filtered

def show_active_filters_responsive(filters):
    """
    Muestra los filtros activos de manera completamente responsive.
    """
    if not filters.get("active_filters"):
        return
    
    active_filters = filters["active_filters"]
    
    # Crear banner responsive con filtros activos
    filters_text = ' | '.join(active_filters[:3])  # Máximo 3 filtros visibles
    if len(active_filters) > 3:
        filters_text += f" | +{len(active_filters) - 3} más"
    
    # Truncar para móviles
    if len(filters_text) > 100:
        filters_text = filters_text[:97] + "..."
    
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
            color: white; 
            padding: clamp(8px, 2vw, 12px); 
            border-radius: 8px; 
            margin-bottom: clamp(12px, 3vw, 20px);
            font-size: clamp(0.8rem, 2vw, 0.9rem);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            border-left: 4px solid {COLORS['secondary']};
        ">
            <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                <span style="font-weight: 600;">🔍 Filtros aplicados:</span>
                <span style="opacity: 0.95;">{filters_text}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def configure_page_responsive():
    """
    Configura la página de Streamlit con máxima responsividad.
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
    
    # CSS responsive principal
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
        
        /* Títulos responsive principales */
        .main-title {{
            color: var(--primary-color);
            font-size: clamp(1.8rem, 6vw, 2.8rem);
            font-weight: 700;
            margin-bottom: clamp(0.5rem, 2vw, 1rem);
            text-align: center;
            padding-bottom: clamp(0.5rem, 2vw, 1rem);
            border-bottom: 3px solid var(--secondary-color);
            line-height: 1.2;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .subtitle {{
            color: var(--accent-color);
            font-size: clamp(1rem, 4vw, 1.4rem);
            text-align: center;
            margin-bottom: clamp(1rem, 3vw, 2rem);
            line-height: 1.4;
            font-weight: 500;
        }}
        
        /* Contenedor principal responsive */
        .block-container {{
            padding-top: clamp(1rem, 3vw, 2rem) !important;
            padding-bottom: clamp(1rem, 3vw, 2rem) !important;
            padding-left: clamp(0.5rem, 2vw, 1.5rem) !important;
            padding-right: clamp(0.5rem, 2vw, 1.5rem) !important;
            max-width: 100% !important;
        }}
        
        /* Métricas responsive mejoradas */
        [data-testid="metric-container"] {{
            background: linear-gradient(135deg, white 0%, #f8f9fa 100%) !important;
            border-radius: 12px !important;
            padding: clamp(1rem, 3vw, 1.5rem) !important;
            text-align: center !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
            border-top: 4px solid var(--primary-color) !important;
            transition: all 0.3s ease !important;
            margin-bottom: clamp(0.5rem, 2vw, 1rem) !important;
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
        
        /* Pestañas responsive mejoradas */
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
        
        /* Columnas responsive */
        .css-1r6slb0 {{
            flex: 1 1 auto !important;
            min-width: 200px !important;
            margin-bottom: clamp(0.75rem, 2vw, 1rem) !important;
        }}
        
        /* Optimizaciones móviles específicas */
        @media (max-width: 768px) {{
            .main-title {{
                font-size: 1.8rem !important;
                margin-bottom: 0.75rem !important;
            }}
            
            .subtitle {{
                font-size: 1rem !important;
                margin-bottom: 1rem !important;
            }}
            
            .css-1r6slb0 {{
                flex: 1 1 100% !important;
                min-width: 100% !important;
                margin-bottom: 1rem !important;
            }}
            
            .stTabs [data-baseweb="tab"] {{
                font-size: 0.75rem !important;
                padding: 0.5rem 0.8rem !important;
            }}
            
            [data-testid="metric-container"] {{
                margin-bottom: 0.75rem !important;
            }}
        }}
        
        /* Tablet adjustments */
        @media (min-width: 769px) and (max-width: 1024px) {{
            .css-1r6slb0 {{
                flex: 1 1 45% !important;
                min-width: 300px !important;
            }}
        }}
        
        /* Desktop optimizations */
        @media (min-width: 1025px) {{
            .css-1r6slb0 {{
                flex: 1 1 22% !important;
                min-width: 200px !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def create_responsive_metrics_display(data_filtered, colors):
    """
    Crea visualización de métricas usando métricas nativas de Streamlit.
    CORREGIDO: Ya no usa HTML/CSS que causaba problemas de renderizado.
    """
    total_casos = len(data_filtered["casos"])
    total_epizootias = len(data_filtered["epizootias"])
    
    # Calcular métricas adicionales de manera segura
    fallecidos = 0
    letalidad = 0
    if total_casos > 0 and 'condicion_final' in data_filtered["casos"].columns:
        fallecidos = (data_filtered["casos"]["condicion_final"] == "Fallecido").sum()
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
    
    positivos = 0
    tasa_positividad = 0
    if total_epizootias > 0 and 'descripcion' in data_filtered["epizootias"].columns:
        positivos = (data_filtered["epizootias"]["descripcion"] == "POSITIVO FA").sum()
        tasa_positividad = (positivos / total_epizootias * 100) if total_epizootias > 0 else 0
    
    # Calcular veredas afectadas
    veredas_afectadas = 0
    if 'vereda_normalizada' in data_filtered["casos"].columns:
        veredas_casos = set(data_filtered["casos"]['vereda_normalizada'].dropna())
    else:
        veredas_casos = set()
    
    if 'vereda_normalizada' in data_filtered["epizootias"].columns:
        veredas_epi = set(data_filtered["epizootias"]['vereda_normalizada'].dropna())
    else:
        veredas_epi = set()
    
    veredas_afectadas = len(veredas_casos.union(veredas_epi))
    
    # Usar métricas nativas de Streamlit - SIEMPRE FUNCIONAN
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="🦠 Casos Confirmados",
            value=f"{total_casos:,}",
            delta=f"{fallecidos} fallecidos" if fallecidos > 0 else "Sin fallecidos",
            help="Total de casos confirmados de fiebre amarilla"
        )
    
    with col2:
        st.metric(
            label="🐒 Epizootias",
            value=f"{total_epizootias:,}",
            delta=f"{positivos} positivas" if positivos > 0 else "Sin positivas",
            help="Total de epizootias registradas"
        )
    
    with col3:
        st.metric(
            label="🏘️ Veredas Afectadas",
            value=f"{veredas_afectadas:,}",
            delta=None,
            help="Número de veredas con casos o epizootias"
        )
    
    with col4:
        st.metric(
            label="⚰️ Tasa Letalidad",
            value=f"{letalidad:.1f}%",
            delta=None,
            help="Porcentaje de casos que resultaron en fallecimiento"
        )
    
    with col5:
        st.metric(
            label="🔴 Positividad",
            value=f"{tasa_positividad:.1f}%",
            delta=None,
            help="Porcentaje de epizootias positivas para fiebre amarilla"
        )
    
    # Información de fechas de última actualización
    st.markdown("---")
    
    # Calcular fechas importantes
    ultima_fecha_caso = None
    ultima_fecha_epi_positiva = None
    
    if not data_filtered["casos"].empty and 'fecha_inicio_sintomas' in data_filtered["casos"].columns:
        fechas_casos = data_filtered["casos"]['fecha_inicio_sintomas'].dropna()
        if not fechas_casos.empty:
            ultima_fecha_caso = fechas_casos.max()
    
    if not data_filtered["epizootias"].empty and 'fecha_recoleccion' in data_filtered["epizootias"].columns:
        epi_positivas = data_filtered["epizootias"][data_filtered["epizootias"]['descripcion'] == 'POSITIVO FA']
        if not epi_positivas.empty:
            fechas_positivas = epi_positivas['fecha_recoleccion'].dropna()
            if not fechas_positivas.empty:
                ultima_fecha_epi_positiva = fechas_positivas.max()
    
    # Mostrar información de fechas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if ultima_fecha_caso:
            st.metric(
                label="📅 Último Caso",
                value=ultima_fecha_caso.strftime("%Y-%m-%d"),
                help="Fecha del último caso confirmado"
            )
        else:
            st.metric(
                label="📅 Último Caso",
                value="Sin datos",
                help="No hay fechas de casos disponibles"
            )
    
    with col2:
        if ultima_fecha_epi_positiva:
            st.metric(
                label="🔴 Última Epizootia +",
                value=ultima_fecha_epi_positiva.strftime("%Y-%m-%d"),
                help="Fecha de la última epizootia positiva"
            )
        else:
            st.metric(
                label="🔴 Última Epizootia +",
                value="Sin datos",
                help="No hay epizootias positivas registradas"
            )
    
    with col3:
        # Fecha de actualización del dashboard
        st.metric(
            label="🔄 Actualización",
            value=datetime.now().strftime("%Y-%m-%d"),
            help="Fecha de última actualización del dashboard"
        )

def main():
    """Aplicación principal del dashboard médico simplificado."""
    # Configurar página con responsividad máxima
    configure_page_responsive()

    # Barra lateral responsive
    from components.sidebar import init_responsive_sidebar
    try:
        init_responsive_sidebar()
    except ImportError:
        # Fallback básico
        with st.sidebar:
            st.title("Dashboard Tolima")

    # Cargar datos con indicadores responsive
    data = load_new_datasets()

    if data["casos"].empty and data["epizootias"].empty:
        # Error responsive con instrucciones claras
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.error("❌ No se pudieron cargar los datos")
            st.markdown(
                """
                **🎯 Pasos para solucionar:**
                1. Crear carpeta `data/` en el directorio del proyecto
                2. Colocar archivos Excel en `data/`:
                   - `BD_positivos.xlsx` (con hoja 'ACUMU')
                   - `Información_Datos_FA.xlsx` (con hoja 'Base de Datos')
                3. Opcionalmente: agregar `Gobernacion.png` para el logo
                4. Recargar la página
                """
            )
        
        with col2:
            st.info("💡 **Ayuda**\n\nEjecute `python install_dependencies.py` para verificar la instalación")
        
        return

    # Crear filtros responsive
    filters, data_filtered = create_filters_responsive(data)

    # Banner principal responsive
    st.markdown(
        '<h1 class="main-title">Dashboard Fiebre Amarilla - Tolima</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="subtitle">Vigilancia Epidemiológica para Profesionales de la Salud</p>',
        unsafe_allow_html=True,
    )

    # Mostrar filtros activos de manera responsive
    show_active_filters_responsive(filters)

    # Métricas principales responsive
    create_responsive_metrics_display(data_filtered, COLORS)

    # Pestañas principales CORREGIDAS - CAMBIO AQUÍ
    tab1, tab2, tab3 = st.tabs([
        "🗺️ Mapas", 
        "🏥 Información Principal",  # CAMBIADO de "📋 Tablas Detalladas"
        "📊 Análisis Comparativo"
    ])

    with tab1:
        if "mapas" in vistas_modules and vistas_modules["mapas"]:
            try:
                vistas_modules["mapas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                st.error(f"Error en módulo de mapas: {str(e)}")
                st.info("🗺️ Vista de mapas en desarrollo.")
        else:
            st.info("🗺️ Vista de mapas en desarrollo.")

    with tab2:
        if "tablas" in vistas_modules and vistas_modules["tablas"]:
            try:
                vistas_modules["tablas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                st.error(f"Error en módulo de información principal: {str(e)}")
                st.info("🔧 Vista de información principal en desarrollo.")
        else:
            st.info("🔧 Módulo de información principal en desarrollo.")

    with tab3:
        if "comparativo" in vistas_modules and vistas_modules["comparativo"]:
            try:
                vistas_modules["comparativo"].show(data_filtered, filters, COLORS)
            except Exception as e:
                st.error(f"Error en módulo comparativo: {str(e)}")
                st.info("🔧 Vista comparativa simplificada en desarrollo.")
        else:
            st.info("🔧 Módulo comparativo en desarrollo.")

    # Footer responsive médico
    st.markdown("---")
    st.markdown(
        f"""
        <div style="
            text-align: center; 
            color: #666; 
            font-size: clamp(0.7rem, 2vw, 0.85rem);
            padding: clamp(1rem, 3vw, 1.5rem) 0;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            margin-top: clamp(1rem, 3vw, 2rem);
        ">
            <div style="margin-bottom: 0.5rem;">
                <strong>🏥 Dashboard Fiebre Amarilla - Secretaría de Salud del Tolima</strong>
            </div>
            <div style="opacity: 0.8;">
                Información epidemiológica para profesionales de la salud |
                Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')} 
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
