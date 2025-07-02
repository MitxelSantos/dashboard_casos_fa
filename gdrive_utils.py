"""
Utilidades para interactuar con Google Drive desde Streamlit.
Este módulo maneja la autenticación y descarga de datos desde Google Drive.
"""

import os
import tempfile
import streamlit as st

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


def check_google_drive_availability():
    """
    Verifica si Google Drive está disponible y configurado.
    
    Returns:
        bool: True si está disponible, False en caso contrario.
    """
    return GOOGLE_AVAILABLE and hasattr(st.secrets, "gcp_service_account")