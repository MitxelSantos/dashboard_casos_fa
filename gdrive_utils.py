"""
Utilidades CORREGIDAS para Google Drive - Versión Streamlit Cloud
SOLUCIONADO: Problemas de autenticación y debugging mejorado
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
    """Gestor mejorado para Google Drive con debugging detallado."""
    
    def __init__(self):
        self.service = None
        self.cache_dir = None
        self.auth_tested = False
        self.setup_cache()
        
    def setup_cache(self):
        """Configura directorio de caché para archivos descargados."""
        try:
            self.cache_dir = tempfile.mkdtemp(prefix="gdrive_cache_")
            logger.info(f"📁 Cache configurado en: {self.cache_dir}")
        except Exception as e:
            logger.error(f"❌ Error configurando caché: {e}")
            self.cache_dir = None
    
    def test_authentication(self):
        """NUEVO: Prueba la autenticación antes de usarla."""
        if self.auth_tested:
            return self.service is not None
        
        try:
            logger.info("🔐 Probando autenticación Google Drive...")
            
            if not GOOGLE_AVAILABLE:
                logger.error("❌ Librerías de Google no disponibles")
                return False
            
            if not hasattr(st.secrets, "gcp_service_account"):
                logger.error("❌ No se encontró gcp_service_account en secrets")
                return False
            
            # Verificar campos requeridos
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            gcp_config = st.secrets["gcp_service_account"]
            
            for field in required_fields:
                if field not in gcp_config:
                    logger.error(f"❌ Campo faltante en gcp_service_account: {field}")
                    return False
            
            logger.info(f"✅ Configuración básica correcta para proyecto: {gcp_config['project_id']}")
            logger.info(f"✅ Service account: {gcp_config['client_email']}")
            
            # Probar creación de credenciales
            try:
                credentials = service_account.Credentials.from_service_account_info(
                    gcp_config,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                logger.info("✅ Credenciales creadas exitosamente")
            except Exception as e:
                logger.error(f"❌ Error creando credenciales: {str(e)}")
                if "Invalid key format" in str(e):
                    logger.error("💡 El private_key tiene formato incorrecto")
                elif "Invalid JWT Signature" in str(e):
                    logger.error("💡 El private_key no es válido o está corrupto")
                return False
            
            # Probar creación del servicio
            try:
                self.service = build('drive', 'v3', credentials=credentials)
                logger.info("✅ Servicio Google Drive creado")
            except Exception as e:
                logger.error(f"❌ Error creando servicio Drive: {str(e)}")
                return False
            
            # Probar una llamada real a la API
            try:
                # Test con una query simple
                results = self.service.files().list(pageSize=1, fields="files(id, name)").execute()
                logger.info("✅ Conexión con Google Drive API exitosa")
                
                files = results.get('files', [])
                if files:
                    logger.info(f"✅ Prueba exitosa - encontrado archivo: {files[0]['name']}")
                else:
                    logger.info("ℹ️ Conexión exitosa pero no se encontraron archivos accesibles")
                
                self.auth_tested = True
                return True
                
            except Exception as e:
                logger.error(f"❌ Error en llamada de prueba a la API: {str(e)}")
                if "invalid_grant" in str(e).lower():
                    logger.error("💡 Token inválido - verifica el private_key")
                elif "insufficient permissions" in str(e).lower():
                    logger.error("💡 Permisos insuficientes - verifica los scopes")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error inesperado en test de autenticación: {str(e)}")
            return False
        finally:
            self.auth_tested = True
    
    def get_service(self):
        """Obtiene servicio de Google Drive con verificación mejorada."""
        if self.service and self.auth_tested:
            return self.service
        
        if not self.test_authentication():
            logger.error("❌ Falló la prueba de autenticación")
            return None
        
        return self.service
    
    def download_file(self, file_id, file_name, timeout=30):
        """
        Descarga un archivo con debugging detallado.
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
            logger.error("❌ No se pudo obtener servicio de Google Drive")
            return None
        
        try:
            logger.info(f"📥 Descargando {file_name} (ID: {file_id}) desde Google Drive...")
            
            # Verificar que el archivo existe y es accesible
            try:
                file_metadata = service.files().get(fileId=file_id, fields='id,name,size,mimeType').execute()
                logger.info(f"✅ Archivo encontrado: {file_metadata.get('name', 'Sin nombre')}")
                logger.info(f"📊 Tamaño: {file_metadata.get('size', 'Desconocido')} bytes")
                logger.info(f"📄 Tipo: {file_metadata.get('mimeType', 'Desconocido')}")
            except Exception as e:
                logger.error(f"❌ Error accediendo a metadata del archivo {file_id}: {str(e)}")
                if "not found" in str(e).lower():
                    logger.error("💡 El archivo no existe o no es accesible")
                elif "permission" in str(e).lower():
                    logger.error("💡 Sin permisos para acceder al archivo")
                return None
            
            # Obtener archivo
            request = service.files().get_media(fileId=file_id)
            
            # Descargar con timeout y progreso
            with open(cache_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                start_time = time.time()
                
                while not done:
                    if time.time() - start_time > timeout:
                        logger.error(f"❌ Timeout descargando {file_name} después de {timeout}s")
                        if os.path.exists(cache_path):
                            os.remove(cache_path)
                        return None
                    
                    try:
                        status, done = downloader.next_chunk()
                        if status:
                            progress = int(status.progress() * 100)
                            if progress % 25 == 0:  # Log cada 25%
                                logger.info(f"📥 Progreso {file_name}: {progress}%")
                    except Exception as e:
                        logger.error(f"❌ Error durante descarga de {file_name}: {str(e)}")
                        if os.path.exists(cache_path):
                            os.remove(cache_path)
                        return None
            
            # Verificar que el archivo se descargó correctamente
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                logger.info(f"✅ {file_name} descargado exitosamente ({os.path.getsize(cache_path)} bytes)")
                return cache_path
            else:
                logger.error(f"❌ Archivo {file_name} descargado pero está vacío o corrupto")
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                return None
            
        except Exception as e:
            logger.error(f"❌ Error inesperado descargando {file_name}: {str(e)}")
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return None
    
    def download_shapefiles(self):
        """Descarga shapefiles con verificación mejorada."""
        if not hasattr(st.secrets, "drive_files"):
            logger.error("❌ IDs de shapefiles no configurados en drive_files")
            return None
        
        drive_files = st.secrets.drive_files
        
        # Archivos shapefile críticos
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
        
        logger.info(f"🗺️ Iniciando descarga de {len(shapefile_mapping)} archivos shapefile...")
        
        for key, filename in shapefile_mapping.items():
            if key in drive_files:
                file_id = drive_files[key]
                logger.info(f"📥 Descargando {filename}...")
                downloaded_path = self.download_file(file_id, filename)
                
                if downloaded_path:
                    downloaded_files[key] = downloaded_path
                    success_count += 1
                    logger.info(f"✅ {filename} descargado exitosamente")
                else:
                    logger.warning(f"⚠️ No se pudo descargar: {filename}")
            else:
                logger.warning(f"⚠️ ID no configurado para: {key}")
        
        if success_count >= 4:  # Al menos municipios completos
            logger.info(f"✅ Shapefiles descargados exitosamente: {success_count}/{len(shapefile_mapping)}")
            return {"files": downloaded_files, "cache_dir": self.cache_dir}
        else:
            logger.error(f"❌ Faltan demasiados archivos shapefile: solo {success_count}/{len(shapefile_mapping)} descargados")
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
    MEJORADO: Verifica disponibilidad y autenticación de Google Drive.
    """
    try:
        logger.info("🔍 Verificando disponibilidad de Google Drive...")
        
        if not GOOGLE_AVAILABLE:
            logger.error("❌ Librerías de Google Drive no están instaladas")
            return False
        
        if not hasattr(st.secrets, "gcp_service_account"):
            logger.error("❌ Configuración gcp_service_account no encontrada en secrets")
            return False
        
        if not hasattr(st.secrets, "drive_files"):
            logger.error("❌ Configuración drive_files no encontrada en secrets")
            return False
        
        # Verificar archivos mínimos requeridos
        drive_files = st.secrets.drive_files
        required_files = ["casos_excel", "epizootias_excel"]
        
        missing_files = [f for f in required_files if f not in drive_files]
        if missing_files:
            logger.error(f"❌ Archivos faltantes en drive_files: {missing_files}")
            return False
        
        # Probar autenticación
        manager = get_gdrive_manager()
        if not manager.test_authentication():
            logger.error("❌ Falló la prueba de autenticación")
            return False
        
        logger.info("✅ Google Drive disponible y configurado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando Google Drive: {str(e)}")
        return False

def load_data_from_google_drive():
    """
    MEJORADO: Carga datos con verificación paso a paso y mejor debugging.
    """
    if not check_google_drive_availability():
        logger.warning("⚠️ Google Drive no disponible")
        return None
    
    manager = get_gdrive_manager()
    drive_files = st.secrets.drive_files
    
    # Crear progress bar
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    try:        
        if not manager.test_authentication():
            raise Exception("Falló la autenticación con Google Drive")
               
        casos_path = manager.download_file(
            drive_files["casos_excel"],
            "BD_positivos.xlsx"
        )
               
        if not casos_path:
            raise Exception("No se pudo descargar BD_positivos.xlsx")
        
        epizootias_path = manager.download_file(
            drive_files["epizootias_excel"],
            "Información_Datos_FA.xlsx"
        )
        
        if not epizootias_path:
            raise Exception("No se pudo descargar Información_Datos_FA.xlsx")
        
        casos_df = pd.read_excel(casos_path, sheet_name="ACUMU", engine="openpyxl")
        epizootias_df = pd.read_excel(epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
        
        processed_data = process_gdrive_data(casos_df, epizootias_df, None)
        
        # Limpiar UI
        time.sleep(1)
        progress_container.empty()
        
        if processed_data:
            logger.info("✅ Datos cargados exitosamente desde Google Drive")
            return processed_data
        else:
            raise Exception("Error procesando datos descargados")
            
    except Exception as e:
        progress_container.empty()
        logger.error(f"❌ Error cargando desde Google Drive: {str(e)}")
        
        # Mostrar error detallado al usuario
        st.error(f"❌ Error cargando desde Google Drive")
        with st.expander("🔧 Detalles del error", expanded=False):
            st.error(f"**Error:** {str(e)}")
            st.markdown("""
            **Posibles soluciones:**
            1. Verifica que el `private_key` esté correctamente configurado en secrets.toml
            2. Asegúrate de que los archivos en Google Drive sean accesibles
            3. Revisa los logs de Streamlit Cloud para más detalles
            4. Ejecuta `python verify_gdrive_config.py` localmente para debugging
            """)
        
        return None

def process_gdrive_data(casos_df, epizootias_df, shapefiles_data):
    """
    MEJORADO: Procesa datos con logging detallado.
    """
    try:
        logger.info(f"🔧 Procesando datos: {len(casos_df)} casos, {len(epizootias_df)} epizootias")
        
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

        # Estructura de resultado
        result_data = {
            "casos": casos_df,
            "epizootias": epizootias_df,
            "municipios_normalizados": todos_municipios,
            "municipio_display_map": {municipio: municipio for municipio in todos_municipios},
            "veredas_por_municipio": {},
            "vereda_display_map": {},
        }

        logger.info(f"✅ Datos procesados: {len(casos_df)} casos, {len(epizootias_df)} epizootias")
        return result_data
        
    except Exception as e:
        logger.error(f"❌ Error procesando datos de Google Drive: {str(e)}")
        return None

# Funciones de compatibilidad (sin cambios)
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