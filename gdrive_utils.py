"""
Utilidades optimizadas para Google Drive - Versión Streamlit Cloud
Integración completa con el flujo principal del dashboard.
"""

import os
import tempfile
import streamlit as st
import pandas as pd
import logging
from pathlib import Path
import time

# Configurar logging
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
    logger.warning("⚠️ Dependencias de Google Drive no disponibles")

class GoogleDriveManager:
    """Gestor optimizado para Google Drive con caché y fallbacks."""
    
    def __init__(self):
        self.service = None
        self.cache_dir = None
        self.setup_cache()
        
    def setup_cache(self):
        """Configura directorio de caché para archivos descargados."""
        try:
            # Crear directorio de caché temporal
            self.cache_dir = tempfile.mkdtemp(prefix="gdrive_cache_")
            logger.info(f"📁 Cache configurado en: {self.cache_dir}")
        except Exception as e:
            logger.error(f"❌ Error configurando caché: {e}")
            self.cache_dir = None
    
    def get_service(self):
        """Obtiene servicio de Google Drive autenticado."""
        if self.service:
            return self.service
            
        if not GOOGLE_AVAILABLE:
            logger.error("❌ Dependencias de Google Drive no disponibles")
            return None
            
        try:
            # Usar credenciales de Streamlit secrets
            if hasattr(st.secrets, "gcp_service_account"):
                credentials = service_account.Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"],
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                self.service = build('drive', 'v3', credentials=credentials)
                logger.info("✅ Servicio Google Drive autenticado")
                return self.service
            else:
                logger.error("❌ Credenciales GCP no encontradas en secrets")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error autenticando Google Drive: {e}")
            return None
    
    def download_file(self, file_id, file_name, timeout=30):
        """
        Descarga un archivo desde Google Drive con caché y timeout.
        
        Args:
            file_id (str): ID del archivo en Google Drive
            file_name (str): Nombre para guardar el archivo
            timeout (int): Timeout en segundos
            
        Returns:
            str: Ruta local del archivo descargado o None
        """
        if not self.cache_dir:
            logger.error("❌ Directorio de caché no disponible")
            return None
            
        # Verificar caché
        cache_path = os.path.join(self.cache_dir, file_name)
        if os.path.exists(cache_path):
            logger.info(f"📋 Usando archivo en caché: {file_name}")
            return cache_path
        
        service = self.get_service()
        if not service:
            return None
            
        try:
            logger.info(f"📥 Descargando {file_name} desde Google Drive...")
            
            # Obtener archivo
            request = service.files().get_media(fileId=file_id)
            
            # Descargar con timeout
            with open(cache_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                start_time = time.time()
                
                while not done:
                    if time.time() - start_time > timeout:
                        logger.error(f"❌ Timeout descargando {file_name}")
                        if os.path.exists(cache_path):
                            os.remove(cache_path)
                        return None
                        
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        if progress % 20 == 0:  # Log cada 20%
                            logger.info(f"📥 Progreso {file_name}: {progress}%")
            
            logger.info(f"✅ {file_name} descargado exitosamente")
            return cache_path
            
        except Exception as e:
            logger.error(f"❌ Error descargando {file_name}: {e}")
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return None
    
    def download_shapefiles(self):
        """
        Descarga todos los shapefiles necesarios desde Google Drive.
        
        Returns:
            dict: Rutas de shapefiles descargados o None
        """
        if not hasattr(st.secrets, "drive_files"):
            logger.error("❌ IDs de shapefiles no configurados")
            return None
            
        drive_files = st.secrets.drive_files
        
        # Archivos shapefile requeridos
        shapefile_mapping = {
            'municipios_shp': 'tolima_municipios.shp',
            'municipios_shx': 'tolima_municipios.shx',
            'municipios_dbf': 'tolima_municipios.dbf',
            'municipios_prj': 'tolima_municipios.prj',
            'veredas_shp': 'tolima_veredas.shp',
            'veredas_shx': 'tolima_veredas.shx',
            'veredas_dbf': 'tolima_veredas.dbf',
            'veredas_prj': 'tolima_veredas.prj'
        }
        
        downloaded_files = {}
        success_count = 0
        
        for key, filename in shapefile_mapping.items():
            if key in drive_files:
                file_id = drive_files[key]
                downloaded_path = self.download_file(file_id, filename)
                
                if downloaded_path:
                    downloaded_files[key] = downloaded_path
                    success_count += 1
                else:
                    logger.warning(f"⚠️ No se pudo descargar: {filename}")
            else:
                logger.warning(f"⚠️ ID no configurado para: {key}")
        
        if success_count >= 4:  # Al menos un shapefile completo
            logger.info(f"✅ Shapefiles descargados: {success_count}/{len(shapefile_mapping)}")
            return {"files": downloaded_files, "cache_dir": self.cache_dir}
        else:
            logger.error(f"❌ Faltan demasiados archivos shapefile: {success_count}/{len(shapefile_mapping)}")
            return None

# Instancia global del gestor
_gdrive_manager = None

def get_gdrive_manager():
    """Obtiene instancia singleton del gestor de Google Drive."""
    global _gdrive_manager
    if _gdrive_manager is None:
        _gdrive_manager = GoogleDriveManager()
    return _gdrive_manager

def check_google_drive_availability():
    """
    Verifica si Google Drive está disponible y configurado.
    
    Returns:
        bool: True si está disponible y configurado
    """
    try:
        if not GOOGLE_AVAILABLE:
            return False
            
        if not hasattr(st.secrets, "gcp_service_account"):
            return False
            
        if not hasattr(st.secrets, "drive_files"):
            return False
            
        # Verificar archivos mínimos requeridos
        drive_files = st.secrets.drive_files
        required_files = ["casos_excel", "epizootias_excel"]
        
        return all(key in drive_files for key in required_files)
        
    except Exception as e:
        logger.error(f"❌ Error verificando Google Drive: {e}")
        return False

def load_data_from_google_drive():
    """
    Función principal para cargar todos los datos desde Google Drive.
    Optimizada para integración con app.py
    
    Returns:
        dict: Datos cargados o None si hay error
    """
    if not check_google_drive_availability():
        logger.warning("⚠️ Google Drive no disponible o mal configurado")
        return None
    
    manager = get_gdrive_manager()
    drive_files = st.secrets.drive_files
    
    # Crear progress bar
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    try:
        # PASO 1: Descargar archivos Excel (20-60%)
        status_text.text("📥 Descargando archivos de datos desde Google Drive...")
        progress_bar.progress(20)
        
        casos_path = manager.download_file(
            drive_files["casos_excel"],
            "BD_positivos.xlsx"
        )
        
        progress_bar.progress(40)
        
        epizootias_path = manager.download_file(
            drive_files["epizootias_excel"],
            "Información_Datos_FA.xlsx"
        )
        
        progress_bar.progress(60)
        
        if not casos_path or not epizootias_path:
            raise Exception("No se pudieron descargar archivos Excel principales")
        
        # PASO 2: Cargar DataFrames (60-75%)
        status_text.text("📊 Procesando archivos Excel...")
        
        casos_df = pd.read_excel(casos_path, sheet_name="ACUMU", engine="openpyxl")
        epizootias_df = pd.read_excel(epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
        
        progress_bar.progress(75)
        
        # PASO 3: Intentar descargar shapefiles (75-90%)
        status_text.text("🗺️ Descargando datos geográficos...")
        
        shapefiles_data = manager.download_shapefiles()
        
        progress_bar.progress(90)
        
        # PASO 4: Procesar datos (90-100%)
        status_text.text("🔧 Procesando y organizando datos...")
        
        processed_data = process_gdrive_data(casos_df, epizootias_df, shapefiles_data)
        
        progress_bar.progress(100)
        
        # Limpiar UI
        time.sleep(1)
        progress_container.empty()
        
        if processed_data:
            logger.info("✅ Datos cargados exitosamente desde Google Drive")
            st.success("✅ Datos cargados desde Google Drive")
            return processed_data
        else:
            raise Exception("Error procesando datos descargados")
            
    except Exception as e:
        progress_container.empty()
        logger.error(f"❌ Error cargando desde Google Drive: {e}")
        st.error(f"❌ Error cargando desde Google Drive: {e}")
        return None

def process_gdrive_data(casos_df, epizootias_df, shapefiles_data):
    """
    Procesa datos descargados de Google Drive usando la lógica existente.
    
    Args:
        casos_df (pd.DataFrame): DataFrame de casos
        epizootias_df (pd.DataFrame): DataFrame de epizootias  
        shapefiles_data (dict): Datos de shapefiles descargados
        
    Returns:
        dict: Estructura de datos procesada
    """
    try:
        # Importar funciones de procesamiento existentes
        from utils.data_processor import excel_date_to_datetime
        
        # Limpiar datos
        for df in [casos_df, epizootias_df]:
            df.drop(columns=[col for col in df.columns if 'Unnamed' in col], 
                    inplace=True, errors='ignore')

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
            total_filtradas = len(epizootias_df)
            logger.info(f"🔵 Epizootias filtradas: {total_filtradas} de {total_original}")

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

        # Estructura base
        result_data = {
            "casos": casos_df,
            "epizootias": epizootias_df,
            "municipios_normalizados": todos_municipios,
            "municipio_display_map": {municipio: municipio for municipio in todos_municipios},
            "veredas_por_municipio": {},
            "vereda_display_map": {},
        }
        
        # Agregar datos geográficos si están disponibles
        if shapefiles_data:
            geo_data = load_geographic_data_from_gdrive(shapefiles_data)
            if geo_data:
                result_data["geo_data"] = geo_data
                logger.info("✅ Datos geográficos incluidos")

        logger.info(f"✅ Datos procesados: {len(casos_df)} casos, {len(epizootias_df)} epizootias")
        return result_data
        
    except Exception as e:
        logger.error(f"❌ Error procesando datos de Google Drive: {e}")
        return None

def load_geographic_data_from_gdrive(shapefiles_data):
    """
    Carga datos geográficos desde shapefiles descargados de Google Drive.
    
    Args:
        shapefiles_data (dict): Datos de shapefiles con rutas locales
        
    Returns:
        dict: Datos geográficos cargados o None
    """
    if not shapefiles_data or 'files' not in shapefiles_data:
        return None
        
    try:
        import geopandas as gpd
        
        files = shapefiles_data['files']
        geo_data = {}
        
        # Cargar municipios si están disponibles
        if 'municipios_shp' in files:
            municipios_path = files['municipios_shp']
            if os.path.exists(municipios_path):
                geo_data['municipios'] = gpd.read_file(municipios_path)
                logger.info(f"✅ Municipios cargados: {len(geo_data['municipios'])} registros")
        
        # Cargar veredas si están disponibles
        if 'veredas_shp' in files:
            veredas_path = files['veredas_shp']
            if os.path.exists(veredas_path):
                geo_data['veredas'] = gpd.read_file(veredas_path)
                logger.info(f"✅ Veredas cargadas: {len(geo_data['veredas'])} registros")
        
        return geo_data if geo_data else None
        
    except Exception as e:
        logger.error(f"❌ Error cargando geodatos: {e}")
        return None

# Funciones de compatibilidad con el código existente
def get_file_from_drive(file_id, file_name, cache_ttl=3600):
    """Función de compatibilidad con el código existente."""
    manager = get_gdrive_manager()
    return manager.download_file(file_id, file_name, timeout=30)

def download_file_from_drive(file_id, output_path):
    """Función de compatibilidad con el código existente."""
    manager = get_gdrive_manager()
    temp_path = manager.download_file(file_id, os.path.basename(output_path))
    
    if temp_path and os.path.exists(temp_path):
        import shutil
        shutil.copy2(temp_path, output_path)
        return True
    return False

def get_drive_service():
    """Función de compatibilidad con el código existente."""
    manager = get_gdrive_manager()
    return manager.get_service()