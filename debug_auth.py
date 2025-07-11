#!/usr/bin/env python3
"""
Script de debugging detallado para problemas de autenticación de Google Drive
"""

import os
import sys
import json
import re
from pathlib import Path

def verify_private_key_format(private_key):
    """Verifica que el private_key tenga el formato correcto."""
    print("🔑 Verificando formato del private_key...")
    
    if not private_key:
        print("❌ private_key está vacío")
        return False
    
    if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
        print("❌ private_key no comienza con '-----BEGIN PRIVATE KEY-----'")
        return False
    
    if not private_key.endswith('-----END PRIVATE KEY-----'):
        print("❌ private_key no termina con '-----END PRIVATE KEY-----'")
        return False
    
    # Verificar que tenga \n correctos
    if '\\n' not in private_key:
        print("❌ private_key no tiene caracteres de nueva línea (\\n)")
        return False
    
    # Contar líneas aproximadas
    lines = private_key.split('\\n')
    if len(lines) < 25:  # Una clave RSA típica tiene ~27 líneas
        print(f"⚠️ private_key parece tener pocas líneas: {len(lines)}")
        print("   Una clave RSA típica tiene ~27 líneas")
    
    print("✅ Formato del private_key parece correcto")
    return True

def test_secrets_file():
    """Prueba el archivo secrets.toml"""
    print("📂 Verificando archivo secrets.toml...")
    
    secrets_path = Path(".streamlit/secrets.toml")
    if not secrets_path.exists():
        print("❌ No se encuentra .streamlit/secrets.toml")
        return False
    
    try:
        import toml
        with open(secrets_path, 'r') as f:
            secrets = toml.load(f)
        
        print("✅ secrets.toml se puede leer correctamente")
        
        # Verificar estructura
        if 'gcp_service_account' not in secrets:
            print("❌ Falta sección [gcp_service_account]")
            return False
        
        gcp_config = secrets['gcp_service_account']
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        
        for field in required_fields:
            if field not in gcp_config:
                print(f"❌ Falta campo: {field}")
                return False
            else:
                print(f"✅ Campo presente: {field}")
        
        # Verificar private_key específicamente
        private_key = gcp_config['private_key']
        verify_private_key_format(private_key)
        
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo secrets.toml: {e}")
        return False

def test_google_auth():
    """Prueba la autenticación con Google"""
    print("🔐 Probando autenticación con Google...")
    
    try:
        from google.oauth2 import service_account
        import toml
        
        with open('.streamlit/secrets.toml', 'r') as f:
            secrets = toml.load(f)
        
        gcp_config = secrets['gcp_service_account']
        
        # Crear credenciales
        credentials = service_account.Credentials.from_service_account_info(
            gcp_config,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        print("✅ Credenciales creadas exitosamente")
        
        # Probar API
        from googleapiclient.discovery import build
        service = build('drive', 'v3', credentials=credentials)
        
        print("✅ Servicio de Google Drive creado")
        
        # Hacer una consulta de prueba
        results = service.files().list(pageSize=1).execute()
        print("✅ Consulta de prueba exitosa")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        
        # Sugerencias específicas según el error
        error_str = str(e).lower()
        if 'invalid jwt signature' in error_str:
            print("\n💡 SOLUCIÓN:")
            print("   El private_key está mal formateado.")
            print("   1. Ejecuta: python extract.py dashboard-vacunacion-460015-4c87557e04b6.json")
            print("   2. Copia la línea exacta al secrets.toml")
            print("   3. Asegúrate de que no haya espacios extra")
        elif 'invalid_grant' in error_str:
            print("\n💡 SOLUCIÓN:")
            print("   1. Verifica que el archivo JSON sea válido")
            print("   2. El service account puede estar deshabilitado")
            print("   3. Genera un nuevo archivo JSON desde Google Cloud Console")
        
        return False

def main():
    print("🛠️  Verificador Detallado de Autenticación Google Drive")
    print("=" * 60)
    
    # Verificar dependencias
    try:
        import toml
        import google.oauth2.service_account
        import googleapiclient.discovery
        print("✅ Todas las dependencias están instaladas")
    except ImportError as e:
        print(f"❌ Falta dependencia: {e}")
        print("💡 Instala con: pip install toml google-auth google-api-python-client")
        return
    
    print("\n" + "="*60)
    
    # Paso 1: Verificar archivo secrets
    if not test_secrets_file():
        print("\n❌ Problema con el archivo secrets.toml")
        return
    
    print("\n" + "="*60)
    
    # Paso 2: Probar autenticación
    if test_google_auth():
        print("\n🎉 ¡TODO FUNCIONA CORRECTAMENTE!")
        print("✅ Tu configuración está lista para Streamlit Cloud")
    else:
        print("\n❌ Hay problemas con la autenticación")
        print("👆 Revisa las sugerencias arriba")

if __name__ == "__main__":
    main()