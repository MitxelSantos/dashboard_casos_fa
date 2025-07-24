"""
Utilidades OPTIMIZADAS para Google Drive - Versión Streamlit Cloud
CORREGIDO: Mensaje de carga se limpia correctamente
"""

import os
import tempfile
import streamlit as st
import pandas as pd
import logging
from pathlib import Path
import time
from datetime import datetime, timezone

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
    logger.warning("⚠️ Google Drive no disponible")


class GoogleDriveManager:
    """Gestor optimizado para Google Drive."""

    def __init__(self):
        self.service = None
        self.cache_dir = self._setup_cache()

    def _setup_cache(self):
        """Configura directorio de caché."""
        try:
            cache_dir = tempfile.mkdtemp(prefix="gdrive_cache_")
            logger.info(f"📁 Cache: {cache_dir}")
            return cache_dir
        except Exception as e:
            logger.error(f"❌ Error cache: {e}")
            return None

    def authenticate(self):
        """Autenticación optimizada - probada y funcional."""
        if self.service:
            return True

        try:
            if not GOOGLE_AVAILABLE:
                return False

            if not hasattr(st.secrets, "gcp_service_account"):
                return False

            # Usar configuración directamente como funcionaba antes
            gcp_config = st.secrets["gcp_service_account"]
            required = ["type", "project_id", "private_key", "client_email"]

            if not all(field in gcp_config for field in required):
                return False

            # Crear credenciales sin modificar el private_key
            credentials = service_account.Credentials.from_service_account_info(
                gcp_config, scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )

            self.service = build("drive", "v3", credentials=credentials)

            # Test simple de conectividad
            self.service.files().list(pageSize=1).execute()
            logger.info("✅ Google Drive autenticado")
            return True

        except Exception as e:
            logger.error(f"❌ Error autenticación: {str(e)}")

            # Hint para problemas comunes
            if "invalid_grant" in str(e).lower():
                logger.error("💡 TIP: Verificar sincronización de tiempo del sistema")

            return False

    def download_file(self, file_id, file_name, timeout=30):
        """Descarga archivo optimizada."""
        if not self.cache_dir:
            return None

        # Verificar caché
        cache_path = os.path.join(self.cache_dir, file_name)
        if os.path.exists(cache_path):
            logger.info(f"📋 Cache hit: {file_name}")
            return cache_path

        if not self.authenticate():
            return None

        try:
            logger.info(f"📥 Descargando: {file_name}")

            # Verificar que el archivo existe
            try:
                self.service.files().get(fileId=file_id).execute()
            except Exception as e:
                logger.error(f"❌ Archivo no accesible {file_id}: {str(e)}")
                return None

            # Descargar archivo
            request = self.service.files().get_media(fileId=file_id)

            with open(cache_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                start_time = time.time()

                while not done:
                    if time.time() - start_time > timeout:
                        logger.error(f"❌ Timeout: {file_name}")
                        if os.path.exists(cache_path):
                            os.remove(cache_path)
                        return None

                    try:
                        status, done = downloader.next_chunk()
                    except Exception as e:
                        logger.error(f"❌ Error descarga: {str(e)}")
                        if os.path.exists(cache_path):
                            os.remove(cache_path)
                        return None

            # Verificar descarga exitosa
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                logger.info(
                    f"✅ Descargado: {file_name} ({os.path.getsize(cache_path)} bytes)"
                )
                return cache_path
            else:
                logger.error(f"❌ Archivo vacío: {file_name}")
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                return None

        except Exception as e:
            logger.error(f"❌ Error descarga {file_name}: {str(e)}")
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return None

    def download_shapefiles(self):
        """Descarga shapefiles optimizada."""
        if not hasattr(st.secrets, "drive_files"):
            logger.error("❌ drive_files no configurado")
            return None

        drive_files = st.secrets.drive_files

        # Archivos shapefile críticos
        shapefile_files = {
            "municipios_shp": "tolima_municipios.shp",
            "municipios_shx": "tolima_municipios.shx",
            "municipios_dbf": "tolima_municipios.dbf",
            "municipios_prj": "tolima_municipios.prj",
            "veredas_shp": "tolima_veredas.shp",
            "veredas_shx": "tolima_veredas.shx",
            "veredas_dbf": "tolima_veredas.dbf",
            "veredas_prj": "tolima_veredas.prj",
        }

        downloaded_files = {}
        success_count = 0

        logger.info(f"🗺️ Descargando {len(shapefile_files)} archivos shapefile")

        for key, filename in shapefile_files.items():
            if key in drive_files:
                file_id = drive_files[key]
                downloaded_path = self.download_file(file_id, filename)

                if downloaded_path:
                    downloaded_files[key] = downloaded_path
                    success_count += 1
                else:
                    logger.warning(f"⚠️ Fallo: {filename}")
            else:
                logger.warning(f"⚠️ ID no configurado: {key}")

        if success_count >= 4:  # Al menos municipios completos
            logger.info(
                f"✅ Shapefiles descargados: {success_count}/{len(shapefile_files)}"
            )
            return {"files": downloaded_files, "cache_dir": self.cache_dir}
        else:
            logger.error(
                f"❌ Shapefiles insuficientes: {success_count}/{len(shapefile_files)}"
            )
            return None


# Instancia global del gestor
_gdrive_manager = None


def check_system_time():
    """Verifica que el tiempo del sistema esté sincronizado."""
    try:
        # Método simple: verificar que el tiempo esté en un rango razonable
        now = datetime.now(timezone.utc)
        year = now.year

        # Verificar que el año esté en un rango razonable (2020-2030)
        if 2020 <= year <= 2030:
            logger.info(f"✅ Tiempo del sistema parece correcto: {now}")
            return True
        else:
            logger.warning(f"⚠️ Tiempo del sistema sospechoso: {now}")
            return False

    except Exception as e:
        logger.warning(f"⚠️ No se pudo verificar tiempo: {str(e)}")
        return True  # Asumir que está bien si no se puede verificar


def get_gdrive_manager():
    """Singleton del gestor de Google Drive."""
    global _gdrive_manager
    if _gdrive_manager is None:
        _gdrive_manager = GoogleDriveManager()
    return _gdrive_manager


def check_google_drive_availability():
    """Verifica disponibilidad de Google Drive - LÓGICA SIMPLIFICADA."""
    try:
        if not GOOGLE_AVAILABLE:
            logger.warning("⚠️ Google libraries no disponibles")
            return False

        if not hasattr(st.secrets, "gcp_service_account"):
            logger.warning("⚠️ gcp_service_account no encontrado")
            return False

        if not hasattr(st.secrets, "drive_files"):
            logger.warning("⚠️ drive_files no encontrado")
            return False

        # Verificar archivos mínimos ÚNICAMENTE
        drive_files = st.secrets.drive_files
        required_files = ["casos_excel", "epizootias_excel"]

        if not all(f in drive_files for f in required_files):
            logger.warning("⚠️ Archivos requeridos faltantes en drive_files")
            return False

        # Test de autenticación SIN verificaciones adicionales
        manager = get_gdrive_manager()
        return manager.authenticate()

    except Exception as e:
        logger.error(f"❌ Error verificación: {str(e)}")
        return False

def load_data_from_google_drive():
    """Carga datos optimizada con UI CORREGIDA + HOJA VEREDAS."""
    if not check_google_drive_availability():
        return None

    manager = get_gdrive_manager()
    drive_files = st.secrets.drive_files

    # UI de progreso CORREGIDA
    progress_container = st.container()

    try:
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("🔐 Autenticando...")
            if not manager.authenticate():
                raise Exception("Autenticación fallida")

            progress_bar.progress(20)
            status_text.text("📥 Descargando archivo único...")

            # CAMBIO: Solo descargar un archivo
            casos_path = manager.download_file(
                drive_files["casos_excel"], "BD_positivos.xlsx"
            )

            if not casos_path:
                raise Exception("Error descargando archivo principal")

            progress_bar.progress(50)
            status_text.text("🔧 Procesando datos...")

            # CAMBIO: Cargar todas las hojas del mismo archivo
            casos_df = pd.read_excel(casos_path, sheet_name="ACUMU", engine="openpyxl")
            epizootias_df = pd.read_excel(casos_path, sheet_name="EPIZOOTIAS", engine="openpyxl")

            # Cargar hoja VEREDAS
            veredas_df = None
            try:
                veredas_df = pd.read_excel(
                    casos_path, sheet_name="VEREDAS", engine="openpyxl"
                )
                logger.info(
                    f"✅ Hoja VEREDAS cargada desde Google Drive: {len(veredas_df)} registros"
                )
            except Exception as e:
                logger.warning(f"⚠️ No se pudo cargar hoja VEREDAS: {str(e)}")

            progress_bar.progress(90)
            status_text.text("🔧 Procesando estructura completa...")

            # ✅ PROCESAR CON HOJA VEREDAS
            processed_data = process_data_with_veredas_sheet(
                casos_df, epizootias_df, veredas_df
            )

            progress_bar.progress(100)
            status_text.text("✅ Completado!")

            # CORREGIDO: Limpiar UI de progreso después de delay
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()

            # CORREGIDO: Limpiar el contenedor completo
            progress_container.empty()

            if processed_data:
                return processed_data
            else:
                raise Exception("Error procesando datos")

    except Exception as e:
        # CORREGIDO: Limpiar UI en caso de error también
        if "progress_container" in locals():
            progress_container.empty()

        logger.error(f"❌ Error carga: {str(e)}")
        st.error(f"❌ Error: {str(e)}")

        with st.expander("🔧 Soluciones", expanded=False):
            st.markdown(
                """
            **Posibles soluciones:**
            1. Verifica `private_key` en secrets.toml
            2. Asegúrate de que archivo sea accesible en Google Drive
            3. Revisa logs de Streamlit Cloud
            4. Verifica que BD_positivos.xlsx tenga las hojas "ACUMU", "EPIZOOTIAS" y "VEREDAS"
            """
            )

        return None

def process_data_with_veredas_sheet(casos_df, epizootias_df, veredas_df=None):
    """
    NUEVA FUNCIÓN: Procesa datos incluyendo hoja VEREDAS desde Google Drive
    """
    try:
        # Importar función existente para no duplicar
        from utils.data_processor import (
            excel_date_to_datetime,
            process_complete_data_structure_authoritative,
        )

        # Limpiar datos básico
        for df in [casos_df, epizootias_df]:
            df.drop(
                columns=[col for col in df.columns if "Unnamed" in col],
                inplace=True,
                errors="ignore",
            )

        casos_df = casos_df.dropna(how="all")
        epizootias_df = epizootias_df.dropna(how="all")

        # CAMBIO: Usar configuración centralizada
        from config.settings import CASOS_COLUMNS_MAP, EPIZOOTIAS_COLUMNS_MAP

        # Aplicar mapeos solo a columnas existentes
        casos_df = casos_df.rename(
            columns={k: v for k, v in CASOS_COLUMNS_MAP.items() if k in casos_df.columns}
        )
        epizootias_df = epizootias_df.rename(
            columns={
                k: v for k, v in EPIZOOTIAS_COLUMNS_MAP.items() if k in epizootias_df.columns
            }
        )

        # Procesar fechas
        if "fecha_inicio_sintomas" in casos_df.columns:
            casos_df["fecha_inicio_sintomas"] = casos_df["fecha_inicio_sintomas"].apply(
                excel_date_to_datetime
            )

        if "fecha_recoleccion" in epizootias_df.columns:
            epizootias_df["fecha_recoleccion"] = epizootias_df[
                "fecha_recoleccion"
            ].apply(excel_date_to_datetime)

        # Filtrar epizootias (solo positivas + en estudio)
        if "descripcion" in epizootias_df.columns:
            total_original = len(epizootias_df)
            epizootias_df["descripcion"] = (
                epizootias_df["descripcion"].str.upper().str.strip()
            )
            epizootias_df = epizootias_df[
                epizootias_df["descripcion"].isin(["POSITIVO FA", "EN ESTUDIO"])
            ]
            logger.info(
                f"🔵 Epizootias filtradas: {len(epizootias_df)} de {total_original}"
            )

        # ✅ PROCESAR HOJA VEREDAS SI ESTÁ DISPONIBLE
        if veredas_df is not None and not veredas_df.empty:
            logger.info("✅ Procesando con hoja VEREDAS desde Google Drive")

            # Procesar hoja VEREDAS usando función existente
            from utils.data_processor import process_veredas_dataframe_simple

            veredas_processed = process_veredas_dataframe_simple(veredas_df)

            # Usar función completa con hoja VEREDAS
            return process_complete_data_structure_authoritative(
                casos_df, epizootias_df, data_dir=None, veredas_data=veredas_processed
            )
        else:
            logger.warning("⚠️ Hoja VEREDAS no disponible, usando procesamiento básico")

            # Usar función completa SIN hoja VEREDAS (fallback)
            return process_complete_data_structure_authoritative(
                casos_df, epizootias_df, data_dir=None
            )

    except Exception as e:
        logger.error(f"❌ Error procesando datos con hoja VEREDAS: {str(e)}")
        return None

def process_data_optimized(casos_df, epizootias_df):
    """Procesamiento de datos optimizado CON HOJA VEREDAS."""
    try:
        # Importar función existente para no duplicar
        from utils.data_processor import excel_date_to_datetime

        # Limpiar datos básico
        for df in [casos_df, epizootias_df]:
            df.drop(
                columns=[col for col in df.columns if "Unnamed" in col],
                inplace=True,
                errors="ignore",
            )

        casos_df = casos_df.dropna(how="all")
        epizootias_df = epizootias_df.dropna(how="all")

        # Mapear columnas críticas
        casos_map = {
            "edad_": "edad",
            "sexo_": "sexo",
            "vereda_": "vereda",
            "nmun_proce": "municipio",
            "Condición Final": "condicion_final",
            "Inicio de sintomas": "fecha_inicio_sintomas",
        }

        epizootias_map = {
            "MUNICIPIO": "municipio",
            "VEREDA": "vereda",
            "FECHA RECOLECCIÓN ": "fecha_recoleccion",
            "PROVENIENTE ": "proveniente",
            "DESCRIPCIÓN": "descripcion",
        }

        # Aplicar mapeos solo a columnas existentes
        casos_df = casos_df.rename(
            columns={k: v for k, v in casos_map.items() if k in casos_df.columns}
        )
        epizootias_df = epizootias_df.rename(
            columns={
                k: v for k, v in epizootias_map.items() if k in epizootias_df.columns
            }
        )

        # Procesar fechas
        if "fecha_inicio_sintomas" in casos_df.columns:
            casos_df["fecha_inicio_sintomas"] = casos_df["fecha_inicio_sintomas"].apply(
                excel_date_to_datetime
            )

        if "fecha_recoleccion" in epizootias_df.columns:
            epizootias_df["fecha_recoleccion"] = epizootias_df[
                "fecha_recoleccion"
            ].apply(excel_date_to_datetime)

        # Filtrar epizootias (solo positivas + en estudio)
        if "descripcion" in epizootias_df.columns:
            total_original = len(epizootias_df)
            epizootias_df["descripcion"] = (
                epizootias_df["descripcion"].str.upper().str.strip()
            )
            epizootias_df = epizootias_df[
                epizootias_df["descripcion"].isin(["POSITIVO FA", "EN ESTUDIO"])
            ]
            logger.info(
                f"🔵 Epizootias filtradas: {len(epizootias_df)} de {total_original}"
            )

        # ===== NUEVA SECCIÓN: CARGAR HOJA VEREDAS =====
        # ESTA ES LA CORRECCIÓN PRINCIPAL
        veredas_data = load_veredas_from_google_drive()

        if veredas_data:
            logger.info("✅ Hoja VEREDAS cargada desde Google Drive")

            # Procesar estructura completa con hoja VEREDAS
            from utils.data_processor import (
                process_complete_data_structure_authoritative,
            )

            return process_complete_data_structure_authoritative(
                casos_df, epizootias_df, data_dir=None, veredas_data=veredas_data
            )
        else:
            logger.warning("⚠️ No se pudo cargar hoja VEREDAS desde Google Drive")
            # Continuar con procesamiento básico

        # Crear estructura de datos BÁSICA (sin hoja VEREDAS)
        municipios_casos = (
            set(casos_df["municipio"].dropna())
            if "municipio" in casos_df.columns
            else set()
        )
        municipios_epizootias = (
            set(epizootias_df["municipio"].dropna())
            if "municipio" in epizootias_df.columns
            else set()
        )
        municipios_con_datos = sorted(municipios_casos.union(municipios_epizootias))

        # Lista completa municipios Tolima
        municipios_tolima = [
            "IBAGUE",
            "ALPUJARRA",
            "ALVARADO",
            "AMBALEMA",
            "ANZOATEGUI",
            "ARMERO",
            "ATACO",
            "CAJAMARCA",
            "CARMEN DE APICALA",
            "CASABIANCA",
            "CHAPARRAL",
            "COELLO",
            "COYAIMA",
            "CUNDAY",
            "DOLORES",
            "ESPINAL",
            "FALAN",
            "FLANDES",
            "FRESNO",
            "GUAMO",
            "HERVEO",
            "HONDA",
            "ICONONZO",
            "LERIDA",
            "LIBANO",
            "MARIQUITA",
            "MELGAR",
            "MURILLO",
            "NATAGAIMA",
            "ORTEGA",
            "PALOCABILDO",
            "PIEDRAS",
            "PLANADAS",
            "PRADO",
            "PURIFICACION",
            "RIOBLANCO",
            "RONCESVALLES",
            "ROVIRA",
            "SALDAÑA",
            "SAN ANTONIO",
            "SAN LUIS",
            "SANTA ISABEL",
            "SUAREZ",
            "VALLE DE SAN JUAN",
            "VENADILLO",
            "VILLAHERMOSA",
            "VILLARRICA",
        ]

        todos_municipios = sorted(set(municipios_con_datos + municipios_tolima))

        return {
            "casos": casos_df,
            "epizootias": epizootias_df,
            "municipios_normalizados": todos_municipios,
            "municipio_display_map": {
                municipio: municipio for municipio in todos_municipios
            },
            "veredas_por_municipio": {},  # ❌ Esto queda vacío sin hoja VEREDAS
            "vereda_display_map": {},
            "veredas_completas": pd.DataFrame(),  # ❌ Esto también
            "regiones": {},
            "data_source": "google_drive_sin_veredas",  # Indicar que falta hoja VEREDAS
        }

    except Exception as e:
        logger.error(f"❌ Error procesando: {str(e)}")
        return None


def load_veredas_from_google_drive():
    """
    NUEVA FUNCIÓN: Carga específicamente la hoja VEREDAS desde Google Drive
    """
    try:
        manager = get_gdrive_manager()

        if not manager.authenticate():
            logger.error("❌ No se pudo autenticar Google Drive para hoja VEREDAS")
            return None

        # Verificar que tenemos el ID del archivo de casos
        if (
            not hasattr(st.secrets, "drive_files")
            or "casos_excel" not in st.secrets.drive_files
        ):
            logger.error("❌ No se encontró ID de casos_excel en secrets")
            return None

        casos_file_id = st.secrets.drive_files["casos_excel"]

        # Descargar archivo temporalmente
        temp_path = manager.download_file(casos_file_id, "BD_positivos_temp.xlsx")

        if not temp_path or not os.path.exists(temp_path):
            logger.error(
                "❌ No se pudo descargar BD_positivos.xlsx para leer hoja VEREDAS"
            )
            return None

        # Intentar leer hoja VEREDAS
        try:
            veredas_df = pd.read_excel(
                temp_path, sheet_name="VEREDAS", engine="openpyxl"
            )
            logger.info(f"✅ Hoja VEREDAS leída: {len(veredas_df)} registros")

            # Procesar hoja VEREDAS
            from utils.data_processor import process_veredas_dataframe_simple

            veredas_processed = process_veredas_dataframe_simple(veredas_df)

            return veredas_processed

        except Exception as e:
            logger.warning(f"⚠️ No se pudo leer hoja VEREDAS: {str(e)}")

            # Verificar qué hojas están disponibles
            try:
                excel_file = pd.ExcelFile(temp_path)
                logger.info(f"📋 Hojas disponibles: {excel_file.sheet_names}")
            except:
                pass

            return None

        finally:
            # Limpiar archivo temporal
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass

    except Exception as e:
        logger.error(f"❌ Error cargando hoja VEREDAS desde Google Drive: {str(e)}")
        return None


# Funciones de compatibilidad (mantener para imports existentes)
def get_file_from_drive(file_id, file_name, cache_ttl=3600):
    """Compatibilidad."""
    manager = get_gdrive_manager()
    return manager.download_file(file_id, file_name, timeout=30)


def download_file_from_drive(file_id, output_path):
    """Compatibilidad."""
    manager = get_gdrive_manager()
    temp_path = manager.download_file(file_id, os.path.basename(output_path))

    if temp_path and os.path.exists(temp_path):
        import shutil

        shutil.copy2(temp_path, output_path)
        return True
    return False


def get_drive_service():
    """Compatibilidad."""
    manager = get_gdrive_manager()
    manager.authenticate()
    return manager.service
