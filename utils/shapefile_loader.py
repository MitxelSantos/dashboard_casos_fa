"""
Sistema unificado para carga de shapefiles con fallback Google Drive → Local
PRIORIDAD: Google Drive para Streamlit Cloud, local para desarrollo
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

class ShapefileLoader:
    """Carga shapefiles con estrategia híbrida Google Drive → Local"""
    
    def __init__(self):
        self.cache_dir = None
        self.loaded_shapefiles = {}
        self.setup_cache()
    
    def setup_cache(self):
        """Configura directorio de caché temporal"""
        try:
            self.cache_dir = tempfile.mkdtemp(prefix="tolima_shapefiles_")
            logger.info(f"📁 Cache shapefiles: {self.cache_dir}")
        except Exception as e:
            logger.error(f"❌ Error configurando caché: {e}")
    
    def load_all_shapefiles(self):
        """
        FUNCIÓN PRINCIPAL: Carga todos los shapefiles con estrategia híbrida
        
        Returns:
            dict: {'municipios': GeoDataFrame, 'veredas': GeoDataFrame} o None
        """
        logger.info("🗺️ INICIANDO CARGA HÍBRIDA DE SHAPEFILES")
        
        # ESTRATEGIA 1: Google Drive (Prioridad para Streamlit Cloud)
        if self._is_google_drive_available():
            logger.info("🌐 Google Drive disponible - intentando carga remota")
            shapefiles_data = self._load_from_google_drive()
            
            if shapefiles_data:
                logger.info("✅ Shapefiles cargados desde Google Drive")
                return shapefiles_data
            else:
                logger.warning("⚠️ Google Drive falló, intentando carga local")
        
        # ESTRATEGIA 2: Archivos locales (Fallback para desarrollo)
        logger.info("📁 Intentando carga desde archivos locales")
        shapefiles_data = self._load_from_local_files()
        
        if shapefiles_data:
            logger.info("✅ Shapefiles cargados desde archivos locales")
            return shapefiles_data
        
        # ESTRATEGIA 3: Error final
        logger.error("❌ No se pudieron cargar shapefiles desde ninguna fuente")
        return None
    
    def _is_google_drive_available(self):
        """Verifica si Google Drive está disponible y configurado"""
        try:
            # Verificar que las librerías estén disponibles
            from gdrive_utils import check_google_drive_availability
            
            if not check_google_drive_availability():
                logger.info("📁 Google Drive no configurado")
                return False
            
            # Verificar que los IDs de shapefiles estén configurados
            if not hasattr(st.secrets, "drive_files"):
                logger.error("❌ drive_files no configurado en secrets")
                return False
            
            drive_files = st.secrets.drive_files
            required_shapefiles = [
                "municipios_shp", "municipios_shx", "municipios_dbf", "municipios_prj",
                "veredas_shp", "veredas_shx", "veredas_dbf", "veredas_prj"
            ]
            
            missing_files = [f for f in required_shapefiles if f not in drive_files]
            if missing_files:
                logger.error(f"❌ IDs de shapefiles faltantes: {missing_files}")
                return False
            
            logger.info("✅ Google Drive configurado para shapefiles")
            return True
            
        except ImportError:
            logger.warning("⚠️ gdrive_utils no disponible")
            return False
        except Exception as e:
            logger.error(f"❌ Error verificando Google Drive: {str(e)}")
            return False
    
    def _load_from_google_drive(self):
        """Carga shapefiles desde Google Drive"""
        try:
            from gdrive_utils import get_gdrive_manager
            
            manager = get_gdrive_manager()
            
            # Mostrar progreso al usuario
            with st.container():
                st.info("🌐 Descargando mapas desde Google Drive...")
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            # Descargar shapefiles
            status_text.text("📥 Descargando archivos de mapas...")
            shapefiles_result = manager.download_shapefiles()
            
            if not shapefiles_result:
                st.error("❌ Error descargando shapefiles desde Google Drive")
                return None
            
            progress_bar.progress(50)
            status_text.text("🗺️ Procesando archivos de mapas...")
            
            # Procesar shapefiles descargados
            geo_data = self._process_downloaded_shapefiles(shapefiles_result)
            
            progress_bar.progress(100)
            st.success("✅ Mapas cargados desde Google Drive")
            
            # Limpiar UI
            progress_bar.empty()
            status_text.empty()
            
            return geo_data
            
        except Exception as e:
            logger.error(f"❌ Error cargando desde Google Drive: {str(e)}")
            st.error(f"❌ Error cargando mapas desde Google Drive: {str(e)}")
            return None
    
    def _process_downloaded_shapefiles(self, shapefiles_result):
        """Procesa shapefiles descargados desde Google Drive"""
        try:
            downloaded_files = shapefiles_result["files"]
            cache_dir = shapefiles_result["cache_dir"]
            
            geo_data = {}
            
            # Cargar municipios
            municipios_files = {
                "shp": downloaded_files.get("municipios_shp"),
                "shx": downloaded_files.get("municipios_shx"), 
                "dbf": downloaded_files.get("municipios_dbf"),
                "prj": downloaded_files.get("municipios_prj")
            }
            
            if all(municipios_files.values()):
                municipios_shp_path = municipios_files["shp"]
                geo_data['municipios'] = gpd.read_file(municipios_shp_path)
                logger.info(f"✅ Municipios cargados: {len(geo_data['municipios'])} features")
            else:
                logger.warning("⚠️ Archivos de municipios incompletos")
            
            # Cargar veredas
            veredas_files = {
                "shp": downloaded_files.get("veredas_shp"),
                "shx": downloaded_files.get("veredas_shx"),
                "dbf": downloaded_files.get("veredas_dbf"), 
                "prj": downloaded_files.get("veredas_prj")
            }
            
            if all(veredas_files.values()):
                veredas_shp_path = veredas_files["shp"]
                geo_data['veredas'] = gpd.read_file(veredas_shp_path)
                logger.info(f"✅ Veredas cargadas: {len(geo_data['veredas'])} features")
            else:
                logger.warning("⚠️ Archivos de veredas incompletos")
            
            if geo_data:
                logger.info(f"✅ Shapefiles procesados: {list(geo_data.keys())}")
                return geo_data
            else:
                logger.error("❌ No se pudo procesar ningún shapefile")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error procesando shapefiles: {str(e)}")
            return None
    
    def _load_from_local_files(self):
        """Carga shapefiles desde archivos locales"""
        geo_data = {}
        
        # Lista de directorios a verificar en orden de prioridad
        search_dirs = [LOCAL_SHAPEFILES_DIR] + LOCAL_FALLBACK_DIRS
        
        for search_dir in search_dirs:
            logger.info(f"🔍 Buscando en: {search_dir}")
            
            if not search_dir.exists():
                logger.info(f"📂 Directorio no existe: {search_dir}")
                continue
            
            try:
                # Buscar municipios
                municipios_path = search_dir / "tolima_municipios.shp"
                if municipios_path.exists():
                    geo_data['municipios'] = gpd.read_file(municipios_path)
                    logger.info(f"✅ Municipios locales: {len(geo_data['municipios'])} features")
                
                # Buscar veredas
                veredas_path = search_dir / "tolima_veredas.shp"
                if veredas_path.exists():
                    geo_data['veredas'] = gpd.read_file(veredas_path)
                    logger.info(f"✅ Veredas locales: {len(geo_data['veredas'])} features")
                
                # Si encontramos algo, salir del loop
                if geo_data:
                    logger.info(f"✅ Shapefiles encontrados en: {search_dir}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ Error cargando desde {search_dir}: {str(e)}")
                continue
        
        return geo_data if geo_data else None
    
    def get_loading_instructions(self):
        """Retorna instrucciones para configurar shapefiles"""
        instructions = """
        ### 🗺️ Configuración de Mapas
        
        **Para Streamlit Cloud:**
        1. Configura Google Drive con los IDs de shapefiles en `.streamlit/secrets.toml`
        2. Asegúrate de que `gcp_service_account` esté correctamente configurado
        3. Los shapefiles se descargarán automáticamente
        
        **Para desarrollo local:**
        1. Coloca los shapefiles en una de estas ubicaciones:
           - `C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed/`
           - `./shapefiles/`
           - `./data/shapefiles/`
        
        **Archivos necesarios:**
        - `tolima_municipios.shp` (+ .shx, .dbf, .prj)
        - `tolima_veredas.shp` (+ .shx, .dbf, .prj)
        """
        return instructions


# Instancia global del loader
_shapefile_loader = None

def get_shapefile_loader():
    """Singleton para el loader de shapefiles"""
    global _shapefile_loader
    if _shapefile_loader is None:
        _shapefile_loader = ShapefileLoader()
    return _shapefile_loader

def load_tolima_shapefiles():
    """
    FUNCIÓN PRINCIPAL para cargar shapefiles del Tolima
    Usar esta función en lugar de las antiguas funciones de carga
    
    Returns:
        dict: {'municipios': GeoDataFrame, 'veredas': GeoDataFrame} o None
    """
    loader = get_shapefile_loader()
    return loader.load_all_shapefiles()

def check_shapefiles_availability():
    """
    Verifica disponibilidad de shapefiles (local O Google Drive)
    
    Returns:
        bool: True si hay shapefiles disponibles desde alguna fuente
    """
    loader = get_shapefile_loader()
    
    # Verificar Google Drive
    if loader._is_google_drive_available():
        logger.info("✅ Shapefiles disponibles desde Google Drive")
        return True
    
    # Verificar archivos locales
    search_dirs = [LOCAL_SHAPEFILES_DIR] + LOCAL_FALLBACK_DIRS
    
    for search_dir in search_dirs:
        municipios_path = search_dir / "tolima_municipios.shp"
        veredas_path = search_dir / "tolima_veredas.shp"
        
        if municipios_path.exists() or veredas_path.exists():
            logger.info(f"✅ Shapefiles locales disponibles en: {search_dir}")
            return True
    
    logger.warning("⚠️ No se encontraron shapefiles desde ninguna fuente")
    return False

def show_shapefile_setup_instructions():
    """Muestra instrucciones de configuración para shapefiles"""
    loader = get_shapefile_loader()
    instructions = loader.get_loading_instructions()
    
    st.error("🗺️ Mapas no disponibles")
    
    with st.expander("📋 Instrucciones de Configuración", expanded=True):
        st.markdown(instructions)
        
        # Estado actual
        st.markdown("### 🔍 Estado Actual")
        
        # Google Drive
        if loader._is_google_drive_available():
            st.success("✅ Google Drive configurado")
        else:
            st.error("❌ Google Drive no configurado")
            st.markdown("""
            **Para configurar Google Drive:**
            1. Agrega `gcp_service_account` a `.streamlit/secrets.toml`
            2. Agrega los IDs de shapefiles bajo `[drive_files]`
            3. Reinicia la aplicación
            """)
        
        # Archivos locales
        local_found = False
        search_dirs = [LOCAL_SHAPEFILES_DIR] + LOCAL_FALLBACK_DIRS
        
        for search_dir in search_dirs:
            municipios_exists = (search_dir / "tolima_municipios.shp").exists()
            veredas_exists = (search_dir / "tolima_veredas.shp").exists()
            
            if municipios_exists or veredas_exists:
                st.success(f"✅ Archivos locales encontrados en: {search_dir}")
                local_found = True
                break
        
        if not local_found:
            st.warning("⚠️ No se encontraron archivos locales")