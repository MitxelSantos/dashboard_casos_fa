"""
Utilidades para interactuar con Google Drive desde Streamlit.
Este módulo maneja la autenticación y descarga de datos desde Google Drive.
"""

import os
import tempfile
import streamlit as st
import logging

# Importaciones opcionales de Google
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    #st.warning("⚠️ Las dependencias de Google Drive no están instaladas. Funciones de Google Drive deshabilitadas.")
def process_downloaded_data(casos_df, epizootias_df, shapefiles_data):
    """
    Procesa datos descargados usando la lógica existente.
    """

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

    # Filtrar epizootias
    if "descripcion" in epizootias_df.columns:
        total_original = len(epizootias_df)
        epizootias_df["descripcion"] = epizootias_df["descripcion"].str.upper().str.strip()
        epizootias_df = epizootias_df[
            epizootias_df["descripcion"].isin(["POSITIVO FA", "EN ESTUDIO"])
        ]
        total_filtradas = len(epizootias_df)
        logging.info(f"🔵 Epizootias filtradas: {total_filtradas} de {total_original}")

    # Crear listas de ubicaciones
    municipios_casos = set(casos_df["municipio"].dropna()) if "municipio" in casos_df.columns else set()
    municipios_epizootias = set(epizootias_df["municipio"].dropna()) if "municipio" in epizootias_df.columns else set()
    municipios_con_datos = sorted(municipios_casos.union(municipios_epizootias))

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

    # Estructura final
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
        geo_data = load_geographic_data_from_drive(shapefiles_data)
        if geo_data:
            result_data["geo_data"] = geo_data

    logging.info(f"✅ Datos procesados: {len(casos_df)} casos, {len(epizootias_df)} epizootias")
    return result_data

def download_shapefiles_from_drive(drive_files):
    """
    NUEVA: Descarga shapefiles desde Google Drive.
    """
    try:
        import tempfile
        import os
        import shutil
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Crear directorio temporal para shapefiles
        temp_dir = tempfile.mkdtemp()
        shapefiles_dir = os.path.join(temp_dir, "processed")
        os.makedirs(shapefiles_dir, exist_ok=True)
        
        logger.info(f"📁 Directorio temporal creado: {shapefiles_dir}")
        
        # Mapeo de claves a nombres de archivo
        file_mapping = {
            'municipios_shp': 'tolima_municipios.shp',
            'municipios_shx': 'tolima_municipios.shx',
            'municipios_dbf': 'tolima_municipios.dbf',
            'municipios_prj': 'tolima_municipios.prj',
            'veredas_shp': 'tolima_veredas.shp',
            'veredas_shx': 'tolima_veredas.shx',
            'veredas_dbf': 'tolima_veredas.dbf',
            'veredas_prj': 'tolima_veredas.prj'
        }
        
        downloaded_count = 0
        total_files = len(file_mapping)
        
        # Descargar cada archivo
        for file_key, file_name in file_mapping.items():
            try:
                if file_key in drive_files:
                    file_id = drive_files[file_key]
                    logger.info(f"📥 Descargando {file_name}...")
                    
                    # Descargar archivo
                    downloaded_path = get_file_from_drive(file_id, file_name)
                    
                    if downloaded_path and os.path.exists(downloaded_path):
                        # Copiar al directorio de shapefiles
                        dest_path = os.path.join(shapefiles_dir, file_name)
                        shutil.copy2(downloaded_path, dest_path)
                        downloaded_count += 1
                        logger.info(f"✅ {file_name} descargado y copiado")
                    else:
                        logger.warning(f"⚠️ No se pudo descargar: {file_name}")
                else:
                    logger.warning(f"⚠️ ID no encontrado para: {file_key}")
                    
            except Exception as e:
                logger.error(f"❌ Error descargando {file_name}: {str(e)}")
                continue
        
        logger.info(f"📊 Descarga completada: {downloaded_count}/{total_files} archivos")
        
        if downloaded_count >= 4:  # Al menos un shapefile completo
            return {"shapefiles_dir": shapefiles_dir}
        else:
            logger.error(f"❌ No se descargaron suficientes archivos shapefile")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error general descargando shapefiles: {str(e)}")
        return None


def check_google_drive_availability():
    """
    CORREGIDA: Verifica si Google Drive está disponible y configurado correctamente.
    """
    try:
        import streamlit as st
        
        # Verificar dependencias
        if not GOOGLE_AVAILABLE:
            return False
        
        # Verificar secrets de Streamlit
        if not hasattr(st.secrets, "gcp_service_account"):
            return False
            
        if not hasattr(st.secrets, "drive_files"):
            return False
            
        # Verificar que tenemos al menos los archivos Excel básicos
        required_files = ["casos_excel", "epizootias_excel"]
        drive_files = st.secrets.drive_files
        
        for required_file in required_files:
            if required_file not in drive_files:
                return False
                
        return True
        
    except Exception as e:
        return False


def load_data_from_google_drive_complete(progress_bar, status_text):
    """
    Función completa para cargar todos los datos desde Google Drive.
    """
    try:
        import streamlit as st
        import pandas as pd
        import logging
        from utils.data_processor import excel_date_to_datetime
        
        logger = logging.getLogger(__name__)
        
        # Verificar configuración
        if not hasattr(st.secrets, "drive_files"):
            logger.error("❌ No se encontraron IDs de archivos en secrets")
            return None
            
        drive_files = st.secrets.drive_files
        
        # PASO 1: Descargar archivos Excel
        status_text.text("📥 Descargando archivos Excel desde Google Drive...")
        progress_bar.progress(20)
        
        casos_path = get_file_from_drive(
            drive_files["casos_excel"], 
            "BD_positivos.xlsx"
        )
        
        epizootias_path = get_file_from_drive(
            drive_files["epizootias_excel"], 
            "Información_Datos_FA.xlsx"
        )
        
        if not casos_path or not epizootias_path:
            logger.error("❌ No se pudieron descargar archivos Excel")
            return None
            
        # PASO 2: Cargar DataFrames
        status_text.text("📊 Procesando archivos Excel...")
        progress_bar.progress(40)
        
        try:
            casos_df = pd.read_excel(casos_path, sheet_name="ACUMU", engine="openpyxl")
            epizootias_df = pd.read_excel(epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
            logger.info(f"✅ Excel cargados: {len(casos_df)} casos, {len(epizootias_df)} epizootias")
        except Exception as e:
            logger.error(f"❌ Error cargando Excel: {str(e)}")
            return None
        
        # PASO 3: Descargar shapefiles (opcional)
        status_text.text("🗺️ Descargando shapefiles...")
        progress_bar.progress(60)
        
        shapefiles_data = None
        try:
            # Verificar si tenemos IDs de shapefiles
            shapefile_keys = ['municipios_shp', 'veredas_shp']
            has_shapefiles = all(key in drive_files for key in shapefile_keys)
            
            if has_shapefiles:
                shapefiles_data = download_shapefiles_from_drive(drive_files)
                if shapefiles_data:
                    logger.info("✅ Shapefiles descargados correctamente")
                else:
                    logger.warning("⚠️ Error descargando shapefiles, continuando sin mapas")
            else:
                logger.info("ℹ️ IDs de shapefiles no configurados, continuando sin mapas")
                
        except Exception as e:
            logger.warning(f"⚠️ Error con shapefiles (continuando): {str(e)}")
            shapefiles_data = None
        
        # PASO 4: Procesar datos
        status_text.text("🔧 Procesando datos...")
        progress_bar.progress(80)
        
        try:
            processed_data = process_downloaded_data_complete(casos_df, epizootias_df, shapefiles_data)
            
            if processed_data:
                logger.info("✅ Datos procesados exitosamente desde Google Drive")
                return processed_data
            else:
                logger.error("❌ Error procesando datos descargados")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error procesando datos: {str(e)}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error general en load_data_from_google_drive_complete: {str(e)}")
        return None

def load_geographic_data_from_drive(shapefiles_data):
    """
    NUEVA: Cargar datos geográficos desde archivos descargados de Google Drive.
    """
    if not shapefiles_data or 'shapefiles_dir' not in shapefiles_data:
        return None
        
    try:
        import geopandas as gpd
        from pathlib import Path
        import logging
        
        logger = logging.getLogger(__name__)
        shapefiles_dir = Path(shapefiles_data['shapefiles_dir'])
        geo_data = {}
        
        # Cargar municipios
        municipios_path = shapefiles_dir / "tolima_municipios.shp"
        if municipios_path.exists():
            geo_data['municipios'] = gpd.read_file(municipios_path)
            logger.info(f"✅ Municipios cargados desde GDrive: {len(geo_data['municipios'])} registros")
        else:
            logger.warning(f"⚠️ No se encontró: {municipios_path}")
        
        # Cargar veredas
        veredas_path = shapefiles_dir / "tolima_veredas.shp"
        if veredas_path.exists():
            geo_data['veredas'] = gpd.read_file(veredas_path)
            logger.info(f"✅ Veredas cargadas desde GDrive: {len(geo_data['veredas'])} registros")
        else:
            logger.warning(f"⚠️ No se encontró: {veredas_path}")
        
        return geo_data if geo_data else None
        
    except Exception as e:
        logger.error(f"❌ Error cargando geodatos desde GDrive: {str(e)}")
        return None
    
def download_multiple_files_from_drive(file_ids_dict, cache_ttl=3600):
    """
    NUEVA: Descarga múltiples archivos desde Google Drive.
    
    Args:
        file_ids_dict (dict): {file_name: file_id, ...}
        cache_ttl (int): Tiempo de vida del caché
        
    Returns:
        dict: {file_name: local_path, ...}
    """
    if not GOOGLE_AVAILABLE:
        return {}
        
    downloaded_files = {}
    
    for file_name, file_id in file_ids_dict.items():
        try:
            local_path = get_file_from_drive(file_id, file_name, cache_ttl)
            if local_path:
                downloaded_files[file_name] = local_path
                logging.info(f"✅ Descargado: {file_name}")
            else:
                logging.warning(f"⚠️ No se pudo descargar: {file_name}")
                
        except Exception as e:
            logging.error(f"❌ Error descargando {file_name}: {str(e)}")
            continue
            
    return downloaded_files

def get_drive_service():
    """
    Crea y retorna un servicio autenticado para interactuar con Google Drive.
    Utiliza los secretos de Streamlit para la autenticación.

    Returns:
        Un servicio de Google Drive autenticado o None si no está disponible.
    """
    if not GOOGLE_AVAILABLE:
        st.error("Las dependencias de Google Drive no están instaladas.")
        return None
        
    try:
        # Verificar si estamos en Streamlit Cloud con secretos configurados
        if hasattr(st.secrets, "gcp_service_account"):
            # Crear credenciales desde los secretos de Streamlit
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            # Crear un servicio de Drive autenticado
            drive_service = build('drive', 'v3', credentials=credentials)
            return drive_service
        else:
            st.error("No se encontraron credenciales de Google Drive en los secretos de Streamlit.")
            st.info("""
            Para configurar la autenticación con Google Drive:
            1. Crea una cuenta de servicio en la consola de Google Cloud
            2. Genera una clave JSON para esta cuenta
            3. Agrega los contenidos de este JSON en Streamlit Cloud bajo Secretos
            """)
            return None
    except Exception as e:
        st.error(f"Error al autenticar con Google Drive: {str(e)}")
        return None


def download_file_from_drive(file_id, output_path):
    """
    Descarga un archivo específico desde Google Drive a la ruta local especificada.
    
    Args:
        file_id (str): ID del archivo en Google Drive.
        output_path (str): Ruta local donde se guardará el archivo.
        
    Returns:
        bool: True si la descarga fue exitosa, False en caso contrario.
    """
    if not GOOGLE_AVAILABLE:
        st.error("Las dependencias de Google Drive no están instaladas.")
        return False
        
    try:
        # Obtener servicio de Drive
        drive_service = get_drive_service()
        if not drive_service:
            return False
            
        # Solicitar el archivo
        request = drive_service.files().get_media(fileId=file_id)
        
        # Descargar el archivo
        with open(output_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        
        return True
    except Exception as e:
        st.error(f"Error al descargar archivo de Google Drive: {str(e)}")
        return False


def get_file_from_drive(file_id, file_name, cache_ttl=3600):
    """
    Obtiene un archivo desde Google Drive, con caché para mejorar rendimiento.
    
    Args:
        file_id (str): ID del archivo en Google Drive.
        file_name (str): Nombre que se le dará al archivo descargado.
        cache_ttl (int): Tiempo de vida del caché en segundos.
        
    Returns:
        str: Ruta local al archivo descargado, o None si hay error.
    """
    if not GOOGLE_AVAILABLE:
        return None
        
    # Crear clave para cache
    cache_key = f"gdrive_file_{file_id}"
    
    # Verificar si tenemos el archivo en caché
    if cache_key in st.session_state and os.path.exists(st.session_state[cache_key]):
        return st.session_state[cache_key]
    
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    local_path = os.path.join(temp_dir, file_name)
    
    # Descargar el archivo
    if download_file_from_drive(file_id, local_path):
        # Guardar en caché
        st.session_state[cache_key] = local_path
        return local_path
    
    return None


def get_files_list(query="", page_size=10):
    """
    Obtiene una lista de archivos desde Google Drive.
    
    Args:
        query (str): Consulta para filtrar archivos.
        page_size (int): Número máximo de resultados a devolver.
        
    Returns:
        list: Lista de archivos con sus metadatos.
    """
    if not GOOGLE_AVAILABLE:
        return []
        
    try:
        drive_service = get_drive_service()
        if not drive_service:
            return []
            
        results = drive_service.files().list(
            q=query,
            pageSize=page_size,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        st.error(f"Error al listar archivos de Google Drive: {str(e)}")
        return []