# ===== get_gdrive_ids.py =====
# Script para obtener IDs de archivos en Google Drive

import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_drive_service():
    """Crear servicio de Google Drive"""
    # Coloca aquí la ruta a tu archivo JSON de service account
    SERVICE_ACCOUNT_FILE = 'path/to/your/service-account-key.json'
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    
    return build('drive', 'v3', credentials=credentials)

def list_files_in_folder(service, folder_name):
    """Listar archivos en una carpeta específica"""
    try:
        # Buscar la carpeta
        folder_query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        folder_results = service.files().list(q=folder_query).execute()
        folders = folder_results.get('files', [])
        
        if not folders:
            print(f"❌ No se encontró la carpeta: {folder_name}")
            return []
            
        folder_id = folders[0]['id']
        print(f"✅ Carpeta encontrada: {folder_name} (ID: {folder_id})")
        
        # Listar archivos en la carpeta
        files_query = f"'{folder_id}' in parents"
        files_results = service.files().list(
            q=files_query,
            fields='files(id, name, mimeType)'
        ).execute()
        
        return files_results.get('files', [])
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    """Función principal"""
    print("🔍 Obteniendo IDs de archivos de Google Drive...")
    
    try:
        service = get_drive_service()
        
        # Estructura de carpetas
        folders_to_check = {
            'Dashboard_Fiebre_Amarilla/datos': ['BD_positivos.xlsx', 'Información_Datos_FA.xlsx'],
            'Dashboard_Fiebre_Amarilla/shapefiles': [
                'tolima_municipios.shp', 'tolima_municipios.shx', 
                'tolima_municipios.dbf', 'tolima_municipios.prj',
                'tolima_veredas.shp', 'tolima_veredas.shx',
                'tolima_veredas.dbf', 'tolima_veredas.prj'
            ]
        }
        
        file_ids = {}
        
        for folder_path, expected_files in folders_to_check.items():
            print(f"\n📁 Revisando carpeta: {folder_path}")
            
            # Simplificar - buscar archivos por nombre directamente
            for file_name in expected_files:
                try:
                    query = f"name='{file_name}'"
                    results = service.files().list(q=query, fields='files(id, name)').execute()
                    files = results.get('files', [])
                    
                    if files:
                        file_id = files[0]['id']
                        file_ids[file_name] = file_id
                        print(f"  ✅ {file_name}: {file_id}")
                    else:
                        print(f"  ❌ No encontrado: {file_name}")
                        
                except Exception as e:
                    print(f"  ❌ Error buscando {file_name}: {e}")
        
        # Generar configuración para Streamlit Cloud
        print("\n" + "="*60)
        print("📋 CONFIGURACIÓN PARA STREAMLIT CLOUD SECRETS:")
        print("="*60)
        
        print("\n# Copia esto en tu archivo .streamlit/secrets.toml para testing local:")
        print("[drive_files]")
        
        # Mapeo específico para tu aplicación
        file_mapping = {
            'BD_positivos.xlsx': 'casos_excel',
            'Información_Datos_FA.xlsx': 'epizootias_excel',
            'tolima_municipios.shp': 'municipios_shp',
            'tolima_municipios.shx': 'municipios_shx', 
            'tolima_municipios.dbf': 'municipios_dbf',
            'tolima_municipios.prj': 'municipios_prj',
            'tolima_veredas.shp': 'veredas_shp',
            'tolima_veredas.shx': 'veredas_shx',
            'tolima_veredas.dbf': 'veredas_dbf',
            'tolima_veredas.prj': 'veredas_prj'
        }
        
        for file_name, key_name in file_mapping.items():
            if file_name in file_ids:
                print(f'{key_name} = "{file_ids[file_name]}"')
            else:
                print(f'# {key_name} = "ID_NO_ENCONTRADO"  # Archivo: {file_name}')
        
        print(f"\n📊 Total archivos encontrados: {len(file_ids)}/{len(file_mapping)}")
        
        if len(file_ids) < len(file_mapping):
            print("\n⚠️ FALTAN ARCHIVOS:")
            missing = set(file_mapping.keys()) - set(file_ids.keys())
            for missing_file in missing:
                print(f"  ❌ {missing_file}")
                
        print(f"\n💡 Para usar en Streamlit Cloud, copia la configuración [drive_files] completa a tus secrets.")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        print("\n💡 Verifica que:")
        print("  1. El archivo JSON de service account esté en la ruta correcta")
        print("  2. La service account tenga permisos de lectura en Google Drive")
        print("  3. Los archivos estén compartidos con la service account")

if __name__ == "__main__":
    main()


# ===== Ejemplo de uso =====
"""
Para usar este script:

1. Instala las dependencias:
   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

2. Descarga el archivo JSON de tu service account

3. Modifica la variable SERVICE_ACCOUNT_FILE con la ruta correcta

4. Ejecuta:
   python get_gdrive_ids.py

5. Copia la salida a tu archivo .streamlit/secrets.toml
"""