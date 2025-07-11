#!/usr/bin/env python3
"""
Script para obtener IDs de archivos de Google Drive
Útil para configurar el dashboard en Streamlit Cloud
"""

import json
import sys
from pathlib import Path

def get_file_id_from_url(url):
    """
    Extrae el ID del archivo desde una URL de Google Drive.
    
    Formatos soportados:
    - https://drive.google.com/file/d/FILE_ID/view
    - https://drive.google.com/open?id=FILE_ID
    - https://docs.google.com/spreadsheets/d/FILE_ID/edit
    """
    if '/file/d/' in url:
        return url.split('/file/d/')[1].split('/')[0]
    elif 'open?id=' in url:
        return url.split('open?id=')[1].split('&')[0]
    elif '/spreadsheets/d/' in url:
        return url.split('/spreadsheets/d/')[1].split('/')[0]
    elif '/document/d/' in url:
        return url.split('/document/d/')[1].split('/')[0]
    else:
        # Asumir que ya es un ID
        return url.strip()

def main():
    print("🔗 Extractor de IDs de Google Drive")
    print("=" * 50)
    
    print("""
📋 **Instrucciones:**
1. Sube tus archivos a Google Drive
2. Haz clic derecho → Obtener enlace → Asegúrate que sea público o compartido
3. Copia el enlace aquí
4. O simplemente pega el ID del archivo si ya lo tienes

📂 **Archivos necesarios:**
- BD_positivos.xlsx (casos confirmados)
- Información_Datos_FA.xlsx (epizootias)
""")
    
    # Recopilar IDs de archivos principales
    file_ids = {}
    
    # Archivo de casos
    print("\n🦠 ARCHIVO DE CASOS:")
    casos_input = input("Pega el enlace o ID de 'BD_positivos.xlsx': ").strip()
    if casos_input:
        file_ids['casos_excel'] = get_file_id_from_url(casos_input)
        print(f"✅ ID extraído: {file_ids['casos_excel']}")
    
    # Archivo de epizootias  
    print("\n🐒 ARCHIVO DE EPIZOOTIAS:")
    epizootias_input = input("Pega el enlace o ID de 'Información_Datos_FA.xlsx': ").strip()
    if epizootias_input:
        file_ids['epizootias_excel'] = get_file_id_from_url(epizootias_input)
        print(f"✅ ID extraído: {file_ids['epizootias_excel']}")
    
    # Logo (opcional)
    print("\n🏛️ LOGO DE GOBERNACIÓN (opcional):")
    logo_input = input("Pega el enlace o ID de 'Gobernacion.png' (Enter para omitir): ").strip()
    if logo_input:
        file_ids['logo_gobernacion'] = get_file_id_from_url(logo_input)
        print(f"✅ ID extraído: {file_ids['logo_gobernacion']}")
    
    # Generar configuración para secrets.toml
    if file_ids:
        print("\n" + "=" * 60)
        print("📋 COPIA ESTA SECCIÓN A TU secrets.toml:")
        print("=" * 60)
        print("\n[drive_files]")
        
        for key, file_id in file_ids.items():
            print(f'{key} = "{file_id}"')
        
        print("\n" + "=" * 60)
        print("✅ Configuración lista para Streamlit Cloud")
        
        # Guardar en archivo
        with open('drive_file_ids.txt', 'w') as f:
            f.write("[drive_files]\n")
            for key, file_id in file_ids.items():
                f.write(f'{key} = "{file_id}"\n')
        
        print(f"💾 También guardado en: drive_file_ids.txt")
        
    else:
        print("❌ No se proporcionaron archivos")

if __name__ == "__main__":
    main()