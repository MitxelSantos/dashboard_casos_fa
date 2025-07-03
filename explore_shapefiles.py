#!/usr/bin/env python3
"""
Script para explorar shapefiles de Tolima-Veredas
Ejecutar desde la terminal: python explore_shapefiles.py
"""

import os
import geopandas as gpd
import pandas as pd
from pathlib import Path

def explore_shapefiles(shapefile_directory):
    """
    Explora todos los shapefiles en un directorio y muestra información detallada.
    """
    print("🗺️  EXPLORADOR DE SHAPEFILES - TOLIMA VEREDAS")
    print("=" * 60)
    
    # Buscar todos los archivos .shp
    shp_files = list(Path(shapefile_directory).glob("*.shp"))
    
    if not shp_files:
        print("❌ No se encontraron archivos .shp en el directorio")
        return
    
    print(f"📁 Directorio: {shapefile_directory}")
    print(f"📄 Archivos .shp encontrados: {len(shp_files)}\n")
    
    for i, shp_file in enumerate(shp_files, 1):
        print(f"📋 ARCHIVO {i}: {shp_file.name}")
        print("-" * 40)
        
        try:
            # Leer el shapefile
            gdf = gpd.read_file(shp_file)
            
            # Información básica
            print(f"🔢 Número de registros: {len(gdf)}")
            print(f"🌍 Sistema de coordenadas: {gdf.crs}")
            print(f"📐 Tipo de geometría: {gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else 'N/A'}")
            
            # Límites geográficos
            bounds = gdf.total_bounds
            print(f"📍 Límites geográficos:")
            print(f"   - Oeste: {bounds[0]:.6f}")
            print(f"   - Sur: {bounds[1]:.6f}")
            print(f"   - Este: {bounds[2]:.6f}")
            print(f"   - Norte: {bounds[3]:.6f}")
            
            # Columnas disponibles
            print(f"\n📊 Columnas disponibles ({len(gdf.columns)} total):")
            for col in gdf.columns:
                if col != 'geometry':
                    dtype = str(gdf[col].dtype)
                    non_null = gdf[col].notna().sum()
                    print(f"   - {col} ({dtype}) - {non_null}/{len(gdf)} valores no nulos")
            
            # Mostrar algunos valores de ejemplo
            print(f"\n🔍 Primeros 3 registros (sin geometría):")
            sample_data = gdf.drop('geometry', axis=1).head(3)
            for idx, row in sample_data.iterrows():
                print(f"   Registro {idx + 1}:")
                for col, val in row.items():
                    print(f"      {col}: {val}")
                print()
            
            # Buscar columnas que podrían ser municipios/veredas
            print("🎯 Posibles columnas de interés:")
            possible_municipio_cols = [col for col in gdf.columns if any(word in col.upper() for word in ['MUNICIPIO', 'MPIO', 'MUN', 'CITY'])]
            possible_vereda_cols = [col for col in gdf.columns if any(word in col.upper() for word in ['VEREDA', 'VRDA', 'VER', 'VILLAGE', 'SECTOR'])]
            possible_name_cols = [col for col in gdf.columns if any(word in col.upper() for word in ['NOMBRE', 'NAME', 'NOM', 'CNMBR'])]
            
            if possible_municipio_cols:
                print(f"   🏛️  Posibles columnas de municipio: {possible_municipio_cols}")
            if possible_vereda_cols:
                print(f"   🏘️  Posibles columnas de vereda: {possible_vereda_cols}")
            if possible_name_cols:
                print(f"   📝 Posibles columnas de nombre: {possible_name_cols}")
            
            # Valores únicos en columnas importantes
            important_cols = possible_municipio_cols + possible_vereda_cols + possible_name_cols
            for col in important_cols[:3]:  # Solo las primeras 3 para no saturar
                unique_vals = gdf[col].unique()[:10]  # Primeros 10 valores únicos
                print(f"   📋 Valores únicos en '{col}' (primeros 10): {list(unique_vals)}")
            
        except Exception as e:
            print(f"❌ Error al leer {shp_file.name}: {str(e)}")
        
        print("\n" + "=" * 60 + "\n")
    
    # Archivos relacionados
    print("📁 ARCHIVOS RELACIONADOS EN EL DIRECTORIO:")
    print("-" * 40)
    all_files = list(Path(shapefile_directory).iterdir())
    extensions = {}
    for file in all_files:
        ext = file.suffix.lower()
        if ext not in extensions:
            extensions[ext] = []
        extensions[ext].append(file.name)
    
    for ext, files in sorted(extensions.items()):
        print(f"{ext.upper()}: {len(files)} archivo(s)")
        if ext in ['.shp', '.prj', '.dbf']:
            for file in files[:5]:  # Mostrar máximo 5 archivos por extensión
                print(f"   - {file}")

def analyze_coordinate_system(shapefile_path):
    """
    Analiza el sistema de coordenadas del shapefile.
    """
    try:
        gdf = gpd.read_file(shapefile_path)
        
        print("🌍 ANÁLISIS DEL SISTEMA DE COORDENADAS")
        print("-" * 40)
        print(f"CRS actual: {gdf.crs}")
        
        if gdf.crs:
            print(f"Nombre: {gdf.crs.name if hasattr(gdf.crs, 'name') else 'N/A'}")
            print(f"Tipo: {'Proyectado' if gdf.crs.is_projected else 'Geográfico'}")
            
            # Verificar si es MAGNA-SIRGAS (común en Colombia)
            crs_string = str(gdf.crs)
            if any(keyword in crs_string.upper() for keyword in ['MAGNA', 'SIRGAS', '4686', '3116']):
                print("✅ Parece usar sistema colombiano (MAGNA-SIRGAS)")
            else:
                print("⚠️  Sistema de coordenadas no estándar para Colombia")
        
        return gdf.crs
    except Exception as e:
        print(f"❌ Error al analizar CRS: {e}")
        return None

def suggest_next_steps(shapefile_directory):
    """
    Sugiere próximos pasos basado en los archivos encontrados.
    """
    print("🚀 PRÓXIMOS PASOS RECOMENDADOS:")
    print("-" * 30)
    print("1. 📋 Revisar la salida anterior e identificar:")
    print("   - ¿Cuál shapefile contiene veredas?")
    print("   - ¿Cuál contiene municipios?")
    print("   - ¿Qué columnas usar para nombres?")
    print()
    print("2. 🗺️  Probar visualización básica:")
    print("   - Usar QGIS, ArcGIS, o Python para ver los mapas")
    print()
    print("3. 🔗 Mapear nombres con tu dashboard:")
    print("   - Comparar nombres con archivos Excel")
    print("   - Crear función de normalización específica")
    print()
    print("4. 🛠️  Integrar en el dashboard:")
    print("   - Actualizar requirements.txt")
    print("   - Implementar en vistas/mapas.py")

if __name__ == "__main__":
    # CONFIGURACIÓN - Cambiar esta ruta por la tuya
    SHAPEFILE_DIR = r"C:\Users\Miguel Santos\Desktop\Tolima-Veredas"
    
    # Si estás en Windows y tienes problemas con la ruta, prueba estas alternativas:
    # SHAPEFILE_DIR = r"C:/Users/TuUsuario/Desktop/Tolima-Veredas"
    # SHAPEFILE_DIR = Path.home() / "Desktop" / "Tolima-Veredas"
    
    print("🔧 INSTRUCCIONES DE USO:")
    print("1. Instalar dependencias: pip install geopandas")
    print("2. Cambiar SHAPEFILE_DIR por tu ruta real")
    print("3. Ejecutar: python explore_shapefiles.py")
    print()
    
    if os.path.exists(SHAPEFILE_DIR):
        explore_shapefiles(SHAPEFILE_DIR)
        
        # Análisis adicional del primer shapefile encontrado
        shp_files = list(Path(SHAPEFILE_DIR).glob("*.shp"))
        if shp_files:
            print("\n" + "=" * 60)
            analyze_coordinate_system(shp_files[0])
        
        print("\n" + "=" * 60)
        suggest_next_steps(SHAPEFILE_DIR)
    else:
        print(f"❌ Directorio no encontrado: {SHAPEFILE_DIR}")
        print("📝 Actualiza la variable SHAPEFILE_DIR con la ruta correcta")