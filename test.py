#!/usr/bin/env python3
"""
Script para verificar la configuración de Google Drive para Streamlit Cloud
Simula el entorno de Streamlit para debugging
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Simular secrets de Streamlit
class MockSecrets:
    def __init__(self, secrets_file):
        import toml
        with open(secrets_file, 'r') as f:
            self.data = toml.load(f)
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __getattr__(self, key):
        return self.data.get(key, {})

def test_google_drive_connection(secrets_file=".streamlit/secrets.toml"):
    """
    Prueba la conexión a Google Drive usando las credenciales del secrets.toml
    """
    print("🔍 Verificando configuración de Google Drive...")
    print("=" * 60)
    
    # 1. Verificar que existe el archivo secrets
    if not os.path.exists(secrets_file):
        print(f"❌ Error: No se encontró {secrets_file}")
        return False
    
    try:
        # 2. Cargar secrets
        secrets = MockSecrets(secrets_file)
        print("✅ Archivo secrets.toml cargado correctamente")
        
        # 3. Verificar estructura de gcp_service_account
        gcp_config = secrets.gcp_service_account
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in gcp_config:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Faltan campos en gcp_service_account: {missing_fields}")
            return False
        
        print("✅ Configuración gcp_service_account completa")
        
        # 4. Verificar formato del private_key
        private_key = gcp_config['private_key']
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ Error: private_key no tiene el formato correcto")
            print("💡 Debe empezar con '-----BEGIN PRIVATE KEY-----'")
            return False
        
        print("✅ Formato de private_key correcto")
        
        # 5. Probar autenticación con Google
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            credentials = service_account.Credentials.from_service_account_info(
                dict(gcp_config),
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Probar listando archivos (limitado)
            results = service.files().list(pageSize=1).execute()
            print("✅ Autenticación con Google Drive exitosa")
            
        except Exception as e:
            print(f"❌ Error de autenticación: {str(e)}")
            return False
        
        # 6. Verificar IDs de archivos
        drive_files = secrets.drive_files
        required_files = ['casos_excel', 'epizootias_excel']
        
        print("\n📂 Verificando archivos requeridos...")
        for file_key in required_files:
            if file_key in drive_files:
                file_id = drive_files[file_key]
                print(f"✅ {file_key}: {file_id}")
                
                # Intentar acceder al archivo
                try:
                    file_info = service.files().get(fileId=file_id).execute()
                    print(f"   📄 Nombre: {file_info.get('name', 'Sin nombre')}")
                    print(f"   📊 Tamaño: {file_info.get('size', 'Desconocido')} bytes")
                except Exception as e:
                    print(f"   ❌ Error accediendo al archivo: {str(e)}")
                    return False
            else:
                print(f"❌ Falta {file_key} en drive_files")
                return False
        
        # 7. Verificar shapefiles (opcionales)
        shapefile_keys = ['municipios_shp', 'municipios_shx', 'municipios_dbf', 'municipios_prj']
        available_shapefiles = 0
        
        print("\n🗺️ Verificando shapefiles (opcionales)...")
        for file_key in shapefile_keys:
            if file_key in drive_files:
                print(f"✅ {file_key}: {drive_files[file_key]}")
                available_shapefiles += 1
            else:
                print(f"⚠️ {file_key}: No configurado")
        
        if available_shapefiles >= 4:
            print("✅ Shapefiles de municipios disponibles")
        else:
            print("⚠️ Shapefiles incompletos - los mapas pueden no funcionar")
        
        print("\n" + "=" * 60)
        print("🎉 ¡Configuración de Google Drive CORRECTA!")
        print("✅ Tu dashboard debería funcionar en Streamlit Cloud")
        return True
        
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def fix_common_issues():
    """Muestra soluciones para problemas comunes"""
    print("\n🔧 SOLUCIONES PARA PROBLEMAS COMUNES:")
    print("=" * 60)
    
    print("\n1️⃣ **Error 'Invalid JWT Signature':**")
    print("   • El private_key está mal formateado")
    print("   • Ejecuta: python get_private_key.py tu_archivo.json")
    print("   • Copia el resultado a secrets.toml")
    
    print("\n2️⃣ **Error 'File not found':**")
    print("   • Los IDs de archivos son incorrectos")
    print("   • Verifica que los archivos sean públicos o compartidos")
    print("   • Ejecuta: python get_shapefiles_ids.py")
    
    print("\n3️⃣ **Error de permisos:**")
    print("   • El service account no tiene acceso")
    print("   • Comparte los archivos con el client_email")
    print("   • O haz los archivos públicos")
    
    print("\n4️⃣ **Timeout de descarga:**")
    print("   • Los archivos son muy grandes")
    print("   • Aumenta download_timeout_seconds en secrets.toml")
    print("   • Verifica tu conexión de red")

def main():
    """Función principal"""
    print("🔍 Verificador de Configuración Google Drive")
    print("Para Dashboard Fiebre Amarilla - Streamlit Cloud")
    print("=" * 60)
    
    # Verificar dependencias
    try:
        import toml
        import google.oauth2.service_account
        import googleapiclient.discovery
    except ImportError as e:
        print(f"❌ Falta dependencia: {e}")
        print("💡 Instala con: pip install toml google-auth google-api-python-client")
        sys.exit(1)
    
    # Buscar archivo secrets
    possible_paths = [
        ".streamlit/secrets.toml",
        "secrets.toml",
        "../.streamlit/secrets.toml"
    ]
    
    secrets_file = None
    for path in possible_paths:
        if os.path.exists(path):
            secrets_file = path
            break
    
    if not secrets_file:
        print("❌ No se encontró secrets.toml en las ubicaciones esperadas:")
        for path in possible_paths:
            print(f"   • {path}")
        print("\n💡 Crea el archivo secrets.toml con la configuración correcta")
        sys.exit(1)
    
    print(f"📂 Usando: {secrets_file}")
    
    # Ejecutar verificación
    success = test_google_drive_connection(secrets_file)
    
    if not success:
        fix_common_issues()
        sys.exit(1)

if __name__ == "__main__":
    main()