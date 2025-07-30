"""
Sistema Consolidado de Carga de Datos - Google Drive First
Archivo único que maneja toda la carga de datos y shapefiles desde Google Drive
"""

import os
import time
import tempfile
import logging
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
import geopandas as gpd

logger = logging.getLogger(__name__)

# Importaciones opcionales de Google
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("⚠️ Google Drive libraries no disponibles")


class ConsolidatedDataLoader:
    """
    Gestor consolidado para carga de datos y shapefiles desde Google Drive
    """
    
    def __init__(self):
        self.service = None
        self.cache_dir = self._setup_cache()
        self._authenticated = False
        
    def _setup_cache(self):
        """Configura directorio de caché temporal."""
        try:
            cache_dir = tempfile.mkdtemp(prefix="tolima_data_cache_")
            logger.info(f"📁 Cache directory: {cache_dir}")
            return cache_dir
        except Exception as e:
            logger.error(f"❌ Error setting up cache: {e}")
            return None

    def _authenticate(self):
        """Autenticación con Google Drive."""
        if self._authenticated and self.service:
            return True

        try:
            if not GOOGLE_AVAILABLE:
                logger.error("❌ Google libraries not available")
                return False

            if not hasattr(st.secrets, "gcp_service_account"):
                logger.error("❌ gcp_service_account not found in secrets")
                return False

            gcp_config = st.secrets["gcp_service_account"]
            required_fields = ["type", "project_id", "private_key", "client_email"]

            if not all(field in gcp_config for field in required_fields):
                logger.error(f"❌ Missing required fields in gcp_service_account")
                return False

            # Crear credenciales
            credentials = service_account.Credentials.from_service_account_info(
                gcp_config, 
                scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )

            self.service = build("drive", "v3", credentials=credentials)

            # Test de conectividad
            self.service.files().list(pageSize=1).execute()
            
            self._authenticated = True
            logger.info("✅ Google Drive authenticated successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            if "invalid_grant" in str(e).lower():
                logger.error("💡 TIP: Check system time synchronization")
            return False

    def _download_file(self, file_id, filename, timeout=30):
        """Descarga un archivo desde Google Drive con caché."""
        if not self.cache_dir:
            return None

        # Verificar caché
        cache_path = os.path.join(self.cache_dir, filename)
        if os.path.exists(cache_path):
            logger.info(f"📋 Cache hit: {filename}")
            return cache_path

        if not self._authenticate():
            return None

        try:
            logger.info(f"📥 Downloading: {filename}")

            # Verificar que el archivo existe
            try:
                self.service.files().get(fileId=file_id).execute()
            except Exception as e:
                logger.error(f"❌ File not accessible {file_id}: {str(e)}")
                return None

            # Descargar archivo
            request = self.service.files().get_media(fileId=file_id)

            with open(cache_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                start_time = time.time()

                while not done:
                    if time.time() - start_time > timeout:
                        logger.error(f"❌ Download timeout: {filename}")
                        if os.path.exists(cache_path):
                            os.remove(cache_path)
                        return None

                    try:
                        status, done = downloader.next_chunk()
                    except Exception as e:
                        logger.error(f"❌ Download error: {str(e)}")
                        if os.path.exists(cache_path):
                            os.remove(cache_path)
                        return None

            # Verificar descarga exitosa
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                logger.info(f"✅ Downloaded: {filename} ({os.path.getsize(cache_path)} bytes)")
                return cache_path
            else:
                logger.error(f"❌ Empty file: {filename}")
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                return None

        except Exception as e:
            logger.error(f"❌ Download error {filename}: {str(e)}")
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return None

    def check_availability(self):
        """Verifica la disponibilidad completa del sistema."""
        try:
            # Verificar Google libraries
            if not GOOGLE_AVAILABLE:
                logger.warning("⚠️ Google libraries not available")
                return False

            # Verificar secrets
            if not hasattr(st.secrets, "gcp_service_account"):
                logger.warning("⚠️ gcp_service_account not found")
                return False

            if not hasattr(st.secrets, "drive_files"):
                logger.warning("⚠️ drive_files not found")
                return False

            # Verificar archivos requeridos
            drive_files = st.secrets.drive_files
            required_files = ["casos_excel"]  # Archivo principal obligatorio
            
            missing_files = [f for f in required_files if f not in drive_files]
            if missing_files:
                logger.warning(f"⚠️ Missing required files: {missing_files}")
                return False

            # Log archivos opcionales disponibles
            optional_files = ["cobertura", "logo"]
            for opt_file in optional_files:
                if opt_file in drive_files:
                    logger.info(f"✅ Optional file '{opt_file}' available")
                else:
                    logger.info(f"ℹ️ Optional file '{opt_file}' not configured")

            # Test de autenticación
            if not self._authenticate():
                return False

            logger.info("✅ All systems available")
            return True

        except Exception as e:
            logger.error(f"❌ Availability check error: {str(e)}")
            return False

    def load_excel_data(self):
        """
        Carga los datos principales desde el archivo Excel en Google Drive.
        
        Returns:
            dict: Estructura de datos procesada o None si falla
        """
        if not self.check_availability():
            return None

        drive_files = st.secrets.drive_files
        progress_container = st.container()

        try:
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("🔐 Autenticando con Google Drive...")
                if not self._authenticate():
                    raise Exception("Authentication failed")

                progress_bar.progress(20)
                status_text.text("📥 Descargando archivo principal...")

                # Descargar archivo Excel principal
                excel_path = self._download_file(
                    drive_files["casos_excel"], 
                    "BD_positivos.xlsx"
                )

                if not excel_path:
                    raise Exception("Error downloading main Excel file")

                progress_bar.progress(40)
                status_text.text("🔍 Verificando estructura del archivo...")

                # Verificar estructura del archivo
                excel_file = pd.ExcelFile(excel_path)
                available_sheets = excel_file.sheet_names
                logger.info(f"📋 Available sheets: {available_sheets}")
                
                required_sheets = ["ACUMU", "EPIZOOTIAS"]
                missing_sheets = [s for s in required_sheets if s not in available_sheets]
                
                if missing_sheets:
                    raise Exception(f"Missing required sheets: {missing_sheets}")

                progress_bar.progress(60)
                status_text.text("📊 Cargando datos...")

                # Cargar hojas principales
                casos_df = pd.read_excel(excel_path, sheet_name="ACUMU", engine="openpyxl")
                epizootias_df = pd.read_excel(excel_path, sheet_name="EPIZOOTIAS", engine="openpyxl")
                
                logger.info(f"✅ Casos loaded: {len(casos_df)} records")
                logger.info(f"✅ Epizootias loaded: {len(epizootias_df)} records")

                # Cargar hoja VEREDAS si existe
                veredas_df = None
                if "VEREDAS" in available_sheets:
                    try:
                        veredas_df = pd.read_excel(excel_path, sheet_name="VEREDAS", engine="openpyxl")
                        logger.info(f"✅ Veredas loaded: {len(veredas_df)} records")
                    except Exception as e:
                        logger.warning(f"⚠️ Error loading VEREDAS sheet: {str(e)}")

                progress_bar.progress(80)
                status_text.text("🔧 Procesando datos...")

                # Procesar datos
                processed_data = self._process_excel_data(casos_df, epizootias_df, veredas_df)

                progress_bar.progress(100)
                status_text.text("✅ Datos cargados exitosamente!")

                # Limpiar UI
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()
                progress_container.empty()

                logger.info("✅ Excel data loaded successfully from Google Drive")
                return processed_data

        except Exception as e:
            if "progress_container" in locals():
                progress_container.empty()

            logger.error(f"❌ Excel data loading error: {str(e)}")
            st.error(f"❌ Error cargando datos: {str(e)}")
            return None

    def load_shapefiles(self):
        """
        Carga los shapefiles desde Google Drive.
        
        Returns:
            dict: {'municipios': GeoDataFrame, 'veredas': GeoDataFrame} o None
        """
        if not self.check_availability():
            return None

        drive_files = st.secrets.drive_files

        # Verificar IDs de shapefiles
        shapefile_ids = {
            "municipios_shp": "tolima_municipios.shp",
            "municipios_shx": "tolima_municipios.shx", 
            "municipios_dbf": "tolima_municipios.dbf",
            "municipios_prj": "tolima_municipios.prj",
            "veredas_shp": "tolima_veredas.shp",
            "veredas_shx": "tolima_veredas.shx",
            "veredas_dbf": "tolima_veredas.dbf", 
            "veredas_prj": "tolima_veredas.prj"
        }

        # Verificar qué archivos están configurados
        available_files = {k: v for k, v in shapefile_ids.items() if k in drive_files}
        
        if len(available_files) < 4:  # Mínimo para un shapefile completo
            logger.warning(f"⚠️ Insufficient shapefile IDs configured: {len(available_files)}/8")
            return None

        try:
            with st.container():
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("📥 Descargando archivos de mapas...")
                
                downloaded_files = {}
                total_files = len(available_files)
                
                for i, (key, filename) in enumerate(available_files.items()):
                    file_id = drive_files[key]
                    downloaded_path = self._download_file(file_id, filename)
                    
                    if downloaded_path:
                        downloaded_files[key] = downloaded_path
                        progress = int((i + 1) / total_files * 70)
                        progress_bar.progress(progress)
                    else:
                        logger.warning(f"⚠️ Failed to download: {filename}")

                progress_bar.progress(80)
                status_text.text("🗺️ Procesando mapas...")

                # Procesar shapefiles descargados
                geo_data = self._process_shapefiles(downloaded_files)

                progress_bar.progress(100)
                progress_bar.empty()
                status_text.empty()

                if geo_data:
                    logger.info("✅ Shapefiles loaded successfully")
                    return geo_data
                else:
                    logger.error("❌ Failed to process shapefiles")
                    return None

        except Exception as e:
            logger.error(f"❌ Shapefile loading error: {str(e)}")
            return None

    def load_cobertura_data(self):
        """
        Carga datos de cobertura desde Google Drive.
        
        Returns:
            pandas.DataFrame: Datos de cobertura o None si falla
        """
        if not self.check_availability():
            logger.warning("⚠️ Google Drive not available for cobertura")
            return None

        drive_files = st.secrets.drive_files
        
        # Verificar si existe el archivo de cobertura
        if "cobertura" not in drive_files:
            logger.warning("⚠️ Cobertura file ID not configured")
            return None

        try:
            logger.info("📊 Loading cobertura data from Google Drive")
            
            # Descargar archivo de cobertura
            cobertura_path = self._download_file(
                drive_files["cobertura"], 
                "cobertura_data.xlsx"
            )

            if not cobertura_path:
                logger.error("❌ Failed to download cobertura file")
                return None

            # Cargar datos de cobertura
            cobertura_df = pd.read_excel(cobertura_path, engine="openpyxl")
            logger.info(f"✅ Cobertura data loaded: {len(cobertura_df)} records")
            
            return cobertura_df

        except Exception as e:
            logger.error(f"❌ Error loading cobertura data: {str(e)}")
            return None

    def load_logo_image(self):
        """
        Carga imagen de logo desde Google Drive.
        
        Returns:
            str: Path al archivo de imagen o None si falla
        """
        if not self.check_availability():
            logger.warning("⚠️ Google Drive not available for logo")
            return None

        drive_files = st.secrets.drive_files
        
        # Verificar si existe el archivo de logo
        if "logo_gobernacion" not in drive_files:
            logger.warning("⚠️ Logo file ID not configured")
            return None

        try:
            logger.info("🖼️ Loading logo image from Google Drive")
            
            # Descargar imagen de logo
            logo_path = self._download_file(
                drive_files["logo_gobernacion"], 
                "logo.png"
            )

            if logo_path:
                logger.info("✅ Logo image loaded successfully")
                return logo_path
            else:
                logger.error("❌ Failed to download logo file")
                return None

        except Exception as e:
            logger.error(f"❌ Error loading logo image: {str(e)}")
            return None

    def _process_excel_data(self, casos_df, epizootias_df, veredas_df=None):
        """Procesa los datos del Excel cargado."""
        try:
            # Importar funciones de procesamiento existentes
            from utils.data_processor import (
                excel_date_to_datetime,
                process_complete_data_structure_authoritative,
                process_veredas_dataframe_simple
            )
            from config.settings import CASOS_COLUMNS_MAP, EPIZOOTIAS_COLUMNS_MAP

            # Limpiar datos básicos
            for df in [casos_df, epizootias_df]:
                df.drop(
                    columns=[col for col in df.columns if "Unnamed" in col],
                    inplace=True,
                    errors="ignore",
                )

            casos_df = casos_df.dropna(how="all")
            epizootias_df = epizootias_df.dropna(how="all")

            # Aplicar mapeos de columnas
            casos_df = casos_df.rename(
                columns={k: v for k, v in CASOS_COLUMNS_MAP.items() if k in casos_df.columns}
            )
            epizootias_df = epizootias_df.rename(
                columns={k: v for k, v in EPIZOOTIAS_COLUMNS_MAP.items() if k in epizootias_df.columns}
            )

            # Procesar fechas
            if "fecha_inicio_sintomas" in casos_df.columns:
                casos_df["fecha_inicio_sintomas"] = casos_df["fecha_inicio_sintomas"].apply(
                    excel_date_to_datetime
                )

            if "fecha_notificacion" in epizootias_df.columns:
                epizootias_df["fecha_notificacion"] = epizootias_df["fecha_notificacion"].apply(
                    excel_date_to_datetime
                )

            # Filtrar epizootias (solo positivas + en estudio)
            if "descripcion" in epizootias_df.columns:
                total_original = len(epizootias_df)
                epizootias_df["descripcion"] = (
                    epizootias_df["descripcion"].str.upper().str.strip()
                )
                epizootias_df = epizootias_df[
                    epizootias_df["descripcion"].isin(["POSITIVO FA", "EN ESTUDIO"])
                ]
                logger.info(f"🔵 Filtered epizootias: {len(epizootias_df)} of {total_original}")

            # Procesar con o sin hoja VEREDAS
            if veredas_df is not None and not veredas_df.empty:
                logger.info("✅ Processing with VEREDAS sheet")
                veredas_processed = process_veredas_dataframe_simple(veredas_df)
                return process_complete_data_structure_authoritative(
                    casos_df, epizootias_df, data_dir=None, veredas_data=veredas_processed
                )
            else:
                logger.warning("⚠️ Processing without VEREDAS sheet")
                return process_complete_data_structure_authoritative(
                    casos_df, epizootias_df, data_dir=None
                )

        except Exception as e:
            logger.error(f"❌ Data processing error: {str(e)}")
            return None

    def _process_shapefiles(self, downloaded_files):
        """Procesa los shapefiles descargados."""
        try:
            geo_data = {}

            # Procesar municipios
            municipios_shp = downloaded_files.get("municipios_shp")
            if municipios_shp and all(
                downloaded_files.get(f"municipios_{ext}") 
                for ext in ["shx", "dbf", "prj"]
            ):
                geo_data['municipios'] = gpd.read_file(municipios_shp)
                logger.info(f"✅ Municipios processed: {len(geo_data['municipios'])}")

            # Procesar veredas
            veredas_shp = downloaded_files.get("veredas_shp")
            if veredas_shp and all(
                downloaded_files.get(f"veredas_{ext}") 
                for ext in ["shx", "dbf", "prj"]
            ):
                geo_data['veredas'] = gpd.read_file(veredas_shp)
                logger.info(f"✅ Veredas processed: {len(geo_data['veredas'])}")

            return geo_data if geo_data else None

        except Exception as e:
            logger.error(f"❌ Shapefile processing error: {str(e)}")
            return None

    def get_empty_data_structure(self):
        """Retorna estructura de datos vacía para casos de error."""
        return {
            "casos": pd.DataFrame(),
            "epizootias": pd.DataFrame(),
            "municipios_normalizados": [],
            "veredas_por_municipio": {},
            "municipio_display_map": {},
            "vereda_display_map": {},
            "veredas_completas": pd.DataFrame(),
            "regiones": {},
            "data_source": "empty",
        }

    def get_empty_geo_data(self):
        """Retorna estructura de geodatos vacía."""
        return {
            "municipios": gpd.GeoDataFrame(),
            "veredas": gpd.GeoDataFrame()
        }

    def show_setup_instructions(self):
        """Muestra instrucciones de configuración completas."""
        st.error("🚫 Sistema de datos no disponible")
        
        with st.expander("📋 Configuración Requerida", expanded=True):
            st.markdown("""
            ### 🔧 Configuración de Google Drive
            
            **1. Archivo `.streamlit/secrets.toml`:**
            ```toml
            [gcp_service_account]
            type = "service_account"
            project_id = "your-project-id"
            private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
            client_email = "your-service-account@project.iam.gserviceaccount.com"
            
            [drive_files]
            # OBLIGATORIO:
            casos_excel = "FILE_ID_OF_EXCEL_FILE"
            
            # OPCIONAL (Mapas):
            municipios_shp = "FILE_ID_OF_MUNICIPIOS_SHP"
            municipios_shx = "FILE_ID_OF_MUNICIPIOS_SHX" 
            municipios_dbf = "FILE_ID_OF_MUNICIPIOS_DBF"
            municipios_prj = "FILE_ID_OF_MUNICIPIOS_PRJ"
            veredas_shp = "FILE_ID_OF_VEREDAS_SHP"
            veredas_shx = "FILE_ID_OF_VEREDAS_SHX"
            veredas_dbf = "FILE_ID_OF_VEREDAS_DBF"
            veredas_prj = "FILE_ID_OF_VEREDAS_PRJ"
            
            # OPCIONAL (Recursos):
            cobertura = "FILE_ID_OF_COBERTURA_EXCEL"
            logo = "FILE_ID_OF_LOGO_IMAGE"
            ```
            
            **2. Estructura del archivo Excel:**
            - Hoja `ACUMU`: Datos de casos
            - Hoja `EPIZOOTIAS`: Datos de epizootias  
            - Hoja `VEREDAS`: Datos de veredas (opcional)
            
            **3. Archivos Shapefile requeridos:**
            - `tolima_municipios.shp` (+ .shx, .dbf, .prj)
            - `tolima_veredas.shp` (+ .shx, .dbf, .prj)
            
            **4. Archivos adicionales opcionales:**
            - `cobertura_data.xlsx`: Datos de cobertura de vacunación
            - `logo.png`: Logo institucional para el dashboard
            """)
            
            # Estado actual del sistema
            st.markdown("### 🔍 Estado Actual del Sistema")
            
            # Verificar Google libraries
            if GOOGLE_AVAILABLE:
                st.success("✅ Google libraries disponibles")
            else:
                st.error("❌ Google libraries no disponibles")
            
            # Verificar secrets
            if hasattr(st.secrets, "gcp_service_account"):
                st.success("✅ gcp_service_account configurado")
            else:
                st.error("❌ gcp_service_account no configurado")
                
            if hasattr(st.secrets, "drive_files"):
                drive_files = st.secrets.drive_files
                required_files = ["casos_excel"]
                map_files = [
                    "municipios_shp", "municipios_shx", "municipios_dbf", "municipios_prj",
                    "veredas_shp", "veredas_shx", "veredas_dbf", "veredas_prj"
                ]
                optional_files = ["cobertura", "logo_gobernacion"]
                
                # Verificar archivos requeridos
                missing_required = [f for f in required_files if f not in drive_files]
                if not missing_required:
                    st.success("✅ drive_files configurado (archivo principal)")
                else:
                    st.error(f"❌ drive_files faltantes: {missing_required}")
                
                # Verificar archivos de mapas
                missing_maps = [f for f in map_files if f not in drive_files]
                if not missing_maps:
                    st.success("✅ Todos los archivos de mapas configurados")
                elif len(missing_maps) < len(map_files):
                    st.warning(f"⚠️ Archivos de mapas faltantes: {len(missing_maps)}/{len(map_files)}")
                else:
                    st.info("ℹ️ Archivos de mapas no configurados (mapas no disponibles)")
                
                # Verificar archivos opcionales
                for opt_file in optional_files:
                    if opt_file in drive_files:
                        st.success(f"✅ Archivo opcional '{opt_file}' configurado")
                    else:
                        st.info(f"ℹ️ Archivo opcional '{opt_file}' no configurado")
                        
            else:
                st.error("❌ drive_files no configurado")


# Instancia global del loader
_data_loader_instance = None

def get_data_loader():
    """Singleton del cargador de datos consolidado."""
    global _data_loader_instance
    if _data_loader_instance is None:
        _data_loader_instance = ConsolidatedDataLoader()
    return _data_loader_instance


# Funciones de interfaz simplificadas para compatibilidad

def load_main_data():
    """
    Función principal para cargar datos desde Google Drive.
    
    Returns:
        dict: Estructura de datos completa o vacía si falla
    """
    logger.info("🔄 Starting consolidated data loading")
    
    loader = get_data_loader()
    
    # Intentar cargar datos
    data = loader.load_excel_data()
    
    if data:
        logger.info(f"✅ Data loaded: {len(data['casos'])} casos, {len(data['epizootias'])} epizootias")
        return data
    else:
        logger.warning("⚠️ Failed to load data, returning empty structure")
        return loader.get_empty_data_structure()

def load_shapefile_data():
    """
    Función para cargar shapefiles desde Google Drive.
    
    Returns:
        dict: Geodatos o estructura vacía si falla
    """
    logger.info("🗺️ Starting shapefile loading")
    
    loader = get_data_loader()
    
    # Intentar cargar shapefiles
    geo_data = loader.load_shapefiles()
    
    if geo_data and (len(geo_data.get('municipios', [])) > 0 or len(geo_data.get('veredas', [])) > 0):
        logger.info("✅ Shapefiles loaded successfully")
        return geo_data
    else:
        logger.warning("⚠️ Failed to load shapefiles, returning empty structure")
        return loader.get_empty_geo_data()

def load_cobertura_from_google_drive():
    """
    Función para cargar datos de cobertura desde Google Drive.
    
    Returns:
        pandas.DataFrame: Datos de cobertura o None si falla
    """
    logger.info("📊 Starting cobertura loading")
    
    loader = get_data_loader()
    cobertura_data = loader.load_cobertura_data()
    
    if cobertura_data is not None and not cobertura_data.empty:
        logger.info(f"✅ Cobertura loaded: {len(cobertura_data)} records")
        return cobertura_data
    else:
        logger.warning("⚠️ Failed to load cobertura data")
        return None

def load_logo_from_google_drive():
    """
    Función para cargar logo desde Google Drive.
    
    Returns:
        str: Path al logo o None si falla
    """
    logger.info("🖼️ Starting logo loading")
    
    loader = get_data_loader()
    logo_path = loader.load_logo_image()
    
    if logo_path:
        logger.info("✅ Logo loaded successfully")
        return logo_path
    else:
        logger.warning("⚠️ Failed to load logo")
        return None

def check_data_availability():
    """
    Verifica si el sistema de datos está disponible.
    
    Returns:
        bool: True si está disponible
    """
    loader = get_data_loader()
    return loader.check_availability()

def show_data_setup_instructions():
    """Muestra instrucciones de configuración del sistema."""
    loader = get_data_loader()
    loader.show_setup_instructions()


# Funciones de compatibilidad con el código existente

def check_google_drive_availability():
    """Función de compatibilidad."""
    return check_data_availability()

def load_data_from_google_drive():
    """Función de compatibilidad."""
    return load_main_data()

def load_tolima_shapefiles():
    """Función de compatibilidad para shapefile_loader.py."""
    return load_shapefile_data()

def check_shapefiles_availability():
    """Función de compatibilidad."""
    loader = get_data_loader()
    return loader.check_availability()

def show_shapefile_setup_instructions():
    """Función de compatibilidad."""
    show_data_setup_instructions()

# Función para obtener el loader de shapefiles (compatibilidad)
def get_shapefile_loader():
    """Función de compatibilidad para mantener imports existentes."""
    class CompatibilityLoader:
        def load_all_shapefiles(self):
            return load_shapefile_data()
        
        def get_loading_instructions(self):
            return "Use show_data_setup_instructions() for complete setup guide."
    
    return CompatibilityLoader()

# Funciones específicas de compatibilidad para gdrive_utils.py
def get_gdrive_manager():
    """Función de compatibilidad para gdrive_utils."""
    return get_data_loader()

class GoogleDriveManager:
    """Clase de compatibilidad para mantener el código existente."""
    
    def __init__(self):
        self.loader = get_data_loader()
    
    def authenticate(self):
        return self.loader._authenticate()
    
    def download_file(self, file_id, filename, timeout=30):
        return self.loader._download_file(file_id, filename, timeout)
    
    def download_shapefiles(self):
        geo_data = self.loader.load_shapefiles()
        if geo_data:
            return {"files": geo_data, "cache_dir": self.loader.cache_dir}
        return None