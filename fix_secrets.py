#!/usr/bin/env python3
"""
Script para reparar automáticamente el private_key en secrets.toml
"""

import json
import toml
import os
from pathlib import Path

def fix_secrets_toml(json_file_path):
    """
    Repara el archivo secrets.toml usando el archivo JSON original
    """
    print("🔧 Reparando secrets.toml...")
    
    # 1. Leer el archivo JSON original
    try:
        with open(json_file_path, 'r') as f:
            credentials = json.load(f)
        print("✅ Archivo JSON leído correctamente")
    except Exception as e:
        print(f"❌ Error leyendo {json_file_path}: {e}")
        return False
    
    # 2. Leer el archivo secrets.toml actual
    secrets_path = Path(".streamlit/secrets.toml")
    try:
        with open(secrets_path, 'r') as f:
            secrets = toml.load(f)
        print("✅ Archivo secrets.toml leído correctamente")
    except Exception as e:
        print(f"❌ Error leyendo secrets.toml: {e}")
        return False
    
    # 3. Actualizar solo el private_key
    if 'gcp_service_account' not in secrets:
        secrets['gcp_service_account'] = {}
    
    # Extraer private_key del JSON y formatearlo correctamente
    private_key = credentials.get('private_key')
    if not private_key:
        print("❌ No se encontró private_key en el archivo JSON")
        return False
    
    # Asegurar formato correcto (con escape de comillas si es necesario)
    formatted_key = private_key.replace('"', '\\"')
    
    # Actualizar el secrets
    secrets['gcp_service_account']['private_key'] = formatted_key
    
    # 4. Escribir el archivo reparado
    try:
        with open(secrets_path, 'w') as f:
            toml.dump(secrets, f)
        print("✅ secrets.toml reparado exitosamente")
        
        # 5. Verificar el resultado
        print("\n🔍 Verificando el resultado...")
        
        # Verificar que empiece y termine correctamente
        if formatted_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("✅ private_key comienza correctamente")
        else:
            print("❌ private_key NO comienza correctamente")
        
        if formatted_key.endswith('-----END PRIVATE KEY-----'):
            print("✅ private_key termina correctamente")
        else:
            print("❌ private_key NO termina correctamente")
        
        # Mostrar primeras y últimas líneas (sin mostrar la clave completa)
        lines = formatted_key.split('\\n')
        print(f"\n📋 Estructura del private_key:")
        print(f"   Primera línea: {lines[0]}")
        print(f"   Total líneas: {len(lines)}")
        print(f"   Última línea: {lines[-1] if lines else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error escribiendo secrets.toml: {e}")
        return False

def verify_fixed_auth():
    """
    Verifica que la autenticación funcione después de la reparación
    """
    print("\n🔐 Verificando autenticación reparada...")
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        with open('.streamlit/secrets.toml', 'r') as f:
            secrets = toml.load(f)
        
        gcp_config = secrets['gcp_service_account']
        
        # Crear credenciales
        credentials = service_account.Credentials.from_service_account_info(
            gcp_config,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        # Probar servicio
        service = build('drive', 'v3', credentials=credentials)
        
        # Hacer consulta de prueba
        results = service.files().list(pageSize=1).execute()
        
        print("✅ ¡Autenticación EXITOSA después de la reparación!")
        return True
        
    except Exception as e:
        print(f"❌ Autenticación falló después de reparación: {e}")
        return False

def main():
    print("🛠️  Reparador Automático de secrets.toml")
    print("=" * 50)
    
    # Buscar archivo JSON
    json_files = [
        "dashboard-vacunacion-460015-4c87557e04b6.json",
        "credentials.json",
        "service-account.json"
    ]
    
    json_file = None
    for filename in json_files:
        if Path(filename).exists():
            json_file = filename
            break
    
    if not json_file:
        print("❌ No se encontró archivo JSON de credenciales")
        print("💡 Archivos buscados:")
        for filename in json_files:
            print(f"   - {filename}")
        return
    
    print(f"📂 Usando archivo JSON: {json_file}")
    
    # Reparar secrets.toml
    if fix_secrets_toml(json_file):
        print("\n" + "="*50)
        
        # Verificar que funcione
        if verify_fixed_auth():
            print("\n🎉 ¡REPARACIÓN EXITOSA!")
            print("✅ Tu secrets.toml está corregido y funcional")
            print("\n📋 Próximos pasos:")
            print("1. Ejecuta: python test.py")
            print("2. Si funciona, sube a Streamlit Cloud")
        else:
            print("\n⚠️ Reparación completada pero persisten problemas")
            print("💡 Puede ser necesario:")
            print("1. Generar nuevo archivo JSON en Google Cloud Console")
            print("2. Verificar permisos del service account")
    else:
        print("\n❌ No se pudo reparar el archivo")

if __name__ == "__main__":
    main()