#!/usr/bin/env python3
"""
Script para extraer el private_key del archivo JSON de Google Cloud
y formatearlo correctamente para secrets.toml de Streamlit
"""

import json
import sys

def extract_private_key_for_streamlit(json_file_path):
    """
    Extrae el private_key del archivo JSON y lo formatea para Streamlit secrets.toml
    
    Args:
        json_file_path (str): Ruta al archivo JSON de credenciales de Google Cloud
    """
    try:
        # Leer el archivo JSON
        with open(json_file_path, 'r') as f:
            credentials = json.load(f)
        
        # Extraer el private_key
        private_key = credentials.get('private_key')
        
        if not private_key:
            print("❌ Error: No se encontró 'private_key' en el archivo JSON")
            return None
        
        # El private_key ya viene en formato correcto con \n
        # Solo necesitamos escapar las comillas si las hay
        formatted_key = private_key.replace('"', '\\"')
        
        print("✅ Private key extraído exitosamente!")
        print("\n" + "="*60)
        print("📋 COPIA ESTA LÍNEA A TU secrets.toml:")
        print("="*60)
        print(f'private_key = "{formatted_key}"')
        print("="*60)
        
        # También mostrar información adicional
        print(f"\n📊 Información adicional:")
        print(f"• Project ID: {credentials.get('project_id', 'No encontrado')}")
        print(f"• Client Email: {credentials.get('client_email', 'No encontrado')}")
        print(f"• Private Key ID: {credentials.get('private_key_id', 'No encontrado')}")
        
        return formatted_key
        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {json_file_path}")
        print("💡 Asegúrate de que la ruta del archivo sea correcta")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: El archivo {json_file_path} no es un JSON válido")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return None

def main():
    """Función principal"""
    print("🔑 Extractor de Private Key para Streamlit Cloud")
    print("=" * 50)
    
    if len(sys.argv) != 2:
        print("📝 Uso: python get_private_key.py <ruta_al_archivo.json>")
        print("\n📋 Ejemplo:")
        print("python get_private_key.py credentials.json")
        print("python get_private_key.py dashboard-vacunacion-460015-4c87557e04b6.json")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    print(f"📂 Procesando archivo: {json_file_path}")
    
    private_key = extract_private_key_for_streamlit(json_file_path)
    
    if private_key:
        print("\n✅ ¡Proceso completado exitosamente!")
        print("\n📝 Próximos pasos:")
        print("1. Copia la línea 'private_key = ...' mostrada arriba")
        print("2. Pégala en tu archivo .streamlit/secrets.toml")
        print("3. Sube los cambios a Streamlit Cloud")
        print("4. Reinicia tu aplicación")
    else:
        print("\n❌ No se pudo extraer el private_key")
        print("\n🔧 Solución alternativa:")
        print("1. Ve a Google Cloud Console")
        print("2. IAM & Admin > Service Accounts")
        print("3. Encuentra tu service account")
        print("4. Genera una nueva clave JSON")
        print("5. Descárgala y ejecuta este script nuevamente")

if __name__ == "__main__":
    main()