"""
Sistema para carga de shapefiles con fallback Google Drive → Local
"""

import os
import tempfile
import streamlit as st
import geopandas as gpd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Rutas locales para desarrollo
LOCAL_SHAPEFILES_DIR = Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed")
LOCAL_FALLBACK_DIRS = [
    Path("shapefiles"),
    Path("data/shapefiles"),
    Path("../shapefiles"),
]

def load_tolima_shapefiles():
    """
    FUNCIÓN PRINCIPAL: Carga shapefiles con estrategia híbrida Google Drive → Local
    
    Returns:
        dict: {'municipios': GeoDataFrame, 'veredas': GeoDataFrame} o None
    """
    logger.info("🗺️ Iniciando carga híbrida de shapefiles")
    
    # ESTRATEGIA 1: Google Drive (Prioridad)
    if is_google_drive_available():
        logger.info("🌐 Intentando Google Drive")
        geo_data = load_from_google_drive()
        if geo_data:
            logger.info("✅ Shapefiles desde Google Drive")
            return geo_data
        logger.warning("⚠️ Google Drive falló")
    
    # ESTRATEGIA 2: Archivos locales (Fallback)
    logger.info("📁 Intentando archivos locales")
    geo_data = load_from_local_files()
    if geo_data:
        logger.info("✅ Shapefiles desde archivos locales")
        return geo_data
    
    # ESTRATEGIA 3: Error final
    logger.error("❌ No se pudieron cargar shapefiles")
    return None

def is_google_drive_available():
    """Verifica si Google Drive está disponible y configurado."""
    try:
        from gdrive_utils import check_google_drive_availability
        
        if not check_google_drive_availability():
            return False
        
        if not hasattr(st.secrets, "drive_files"):
            return False
        
        # Verificar IDs críticos
        required_files = ["municipios_shp", "municipios_dbf", "veredas_shp", "veredas_dbf"]
        drive_files = st.secrets.drive_files
        
        missing = [f for f in required_files if f not in drive_files]
        if missing:
            logger.error(f"❌ IDs faltantes: {missing}")
            return False
        
        return True
        
    except ImportError:
        return False
    except Exception as e:
        logger.error(f"❌ Error verificando Google Drive: {str(e)}")
        return False

def load_from_google_drive():
    """Carga shapefiles desde Google Drive."""
    try:
        from gdrive_utils import get_gdrive_manager
        
        manager = get_gdrive_manager()
        
        # Mostrar progreso
        with st.container():
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        status_text.text("📥 Descargando archivos de mapas...")
        shapefiles_result = manager.download_shapefiles()
        
        if not shapefiles_result:
            progress_bar.empty()
            status_text.empty()
            return None
        
        progress_bar.progress(50)
        status_text.text("🗺️ Procesando mapas...")
        
        # Procesar archivos descargados
        geo_data = process_downloaded_shapefiles(shapefiles_result)
        
        progress_bar.progress(100)
        progress_bar.empty()
        status_text.empty()
        
        return geo_data
        
    except Exception as e:
        logger.error(f"❌ Error Google Drive: {str(e)}")
        return None

def process_downloaded_shapefiles(shapefiles_result):
    """Procesa shapefiles descargados desde Google Drive."""
    try:
        downloaded_files = shapefiles_result["files"]
        geo_data = {}
        
        # Cargar municipios
        municipios_shp = downloaded_files.get("municipios_shp")
        if municipios_shp and all(downloaded_files.get(f"municipios_{ext}") for ext in ["shx", "dbf", "prj"]):
            geo_data['municipios'] = gpd.read_file(municipios_shp)
            logger.info(f"✅ Municipios: {len(geo_data['municipios'])}")
        
        # Cargar veredas
        veredas_shp = downloaded_files.get("veredas_shp")
        if veredas_shp and all(downloaded_files.get(f"veredas_{ext}") for ext in ["shx", "dbf", "prj"]):
            geo_data['veredas'] = gpd.read_file(veredas_shp)
            logger.info(f"✅ Veredas: {len(geo_data['veredas'])}")
        
        return geo_data if geo_data else None
        
    except Exception as e:
        logger.error(f"❌ Error procesando: {str(e)}")
        return None

def load_from_local_files():
    """Carga shapefiles desde archivos locales."""
    geo_data = {}
    
    # Buscar en directorios en orden de prioridad
    search_dirs = [LOCAL_SHAPEFILES_DIR] + LOCAL_FALLBACK_DIRS
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        try:
            # Buscar municipios
            municipios_path = search_dir / "tolima_municipios.shp"
            if municipios_path.exists():
                geo_data['municipios'] = gpd.read_file(municipios_path)
                logger.info(f"✅ Municipios locales: {len(geo_data['municipios'])}")
            
            # Buscar veredas
            veredas_path = search_dir / "tolima_veredas.shp"
            if veredas_path.exists():
                geo_data['veredas'] = gpd.read_file(veredas_path)
                logger.info(f"✅ Veredas locales: {len(geo_data['veredas'])}")
            
            # Si encontramos algo, salir del loop
            if geo_data:
                logger.info(f"✅ Encontrados en: {search_dir}")
                break
                
        except Exception as e:
            logger.error(f"❌ Error en {search_dir}: {str(e)}")
            continue
    
    return geo_data if geo_data else None

def check_shapefiles_availability():
    """
    Verifica disponibilidad de shapefiles (Google Drive O Local).
    
    Returns:
        bool: True si hay shapefiles disponibles
    """
    # Verificar Google Drive
    if is_google_drive_available():
        logger.info("✅ Shapefiles disponibles desde Google Drive")
        return True
    
    # Verificar archivos locales
    search_dirs = [LOCAL_SHAPEFILES_DIR] + LOCAL_FALLBACK_DIRS
    
    for search_dir in search_dirs:
        municipios_path = search_dir / "tolima_municipios.shp"
        veredas_path = search_dir / "tolima_veredas.shp"
        
        if municipios_path.exists() or veredas_path.exists():
            logger.info(f"✅ Shapefiles locales en: {search_dir}")
            return True
    
    logger.warning("⚠️ No se encontraron shapefiles")
    return False

def show_shapefile_setup_instructions():
    """Muestra instrucciones de configuración."""
    st.error("🗺️ Mapas no disponibles")
    
    with st.expander("📋 Configuración de Mapas", expanded=True):
        st.markdown("""
        ### 🌐 Para Streamlit Cloud (Recomendado)
        1. Configura Google Drive con los IDs de shapefiles en `.streamlit/secrets.toml`
        2. Asegúrate de que `gcp_service_account` esté configurado correctamente
        3. Los mapas se descargarán automáticamente
        
        ### 📁 Para desarrollo local
        Coloca los shapefiles en una de estas ubicaciones:
        - `C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed/`
        - `./shapefiles/`
        - `./data/shapefiles/`
        
        ### 📄 Archivos necesarios
        - `tolima_municipios.shp` (+ .shx, .dbf, .prj)
        - `tolima_veredas.shp` (+ .shx, .dbf, .prj)
        """)
        
        # Estado actual
        st.markdown("### 🔍 Estado Actual")
        
        # Google Drive
        if is_google_drive_available():
            st.success("✅ Google Drive configurado")
        else:
            st.error("❌ Google Drive no configurado")
        
        # Archivos locales
        local_found = False
        search_dirs = [LOCAL_SHAPEFILES_DIR] + LOCAL_FALLBACK_DIRS
        
        for search_dir in search_dirs:
            municipios_exists = (search_dir / "tolima_municipios.shp").exists()
            veredas_exists = (search_dir / "tolima_veredas.shp").exists()
            
            if municipios_exists or veredas_exists:
                st.success(f"✅ Archivos locales: {search_dir}")
                local_found = True
                break
        
        if not local_found:
            st.warning("⚠️ No se encontraron archivos locales")

# Funciones de compatibilidad (mantener para no romper imports existentes)
def get_shapefile_loader():
    """Función de compatibilidad - mantener para imports existentes."""
    class SimpleLoader:
        def load_all_shapefiles(self):
            return load_tolima_shapefiles()
        
        def get_loading_instructions(self):
            return """
            ### 🗺️ Instrucciones de Mapas
            
            **Para Streamlit Cloud:** Configura Google Drive en secrets.toml
            **Para desarrollo local:** Coloca shapefiles en las rutas especificadas
            
            Usa `show_shapefile_setup_instructions()` para ver detalles completos.
            """
    
    return SimpleLoader()

# Aliases para compatibilidad
load_all_shapefiles = load_tolima_shapefiles