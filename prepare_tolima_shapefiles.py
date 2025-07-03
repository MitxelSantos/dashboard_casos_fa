#!/usr/bin/env python3
"""
Script para preparar shapefiles del Tolima para el dashboard de fiebre amarilla.
Filtra, reproyecta y valida los datos geográficos.
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import os

def prepare_tolima_shapefiles(shapefile_dir, output_dir=None):
    """
    Prepara los shapefiles específicamente para el dashboard del Tolima.
    """
    print("🗺️  PREPARANDO SHAPEFILES PARA DASHBOARD TOLIMA")
    print("=" * 60)
    
    shapefile_dir = Path(shapefile_dir)
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    else:
        output_dir = shapefile_dir / "processed"
        output_dir.mkdir(exist_ok=True)
    
    # ===================== PROCESAR MUNICIPIOS =====================
    print("🏛️  Procesando municipios del Tolima...")
    
    municipios_path = shapefile_dir / "Municipios.shp"
    if municipios_path.exists():
        municipios = gpd.read_file(municipios_path)
        
        # Reproyectar a WGS84 para web maps
        if municipios.crs != 'EPSG:4326':
            print(f"   Reproyectando municipios de {municipios.crs} a EPSG:4326")
            municipios = municipios.to_crs('EPSG:4326')
        
        # Limpiar y normalizar nombres
        municipios['municipio_original'] = municipios['MpNombre']
        municipios['municipio_normalizado'] = municipios['MpNombre'].apply(normalize_name)
        
        print(f"   ✅ {len(municipios)} municipios procesados")
        print(f"   📋 Municipios encontrados: {municipios['MpNombre'].head(10).tolist()}")
        
        # Guardar municipios procesados
        municipios_output = output_dir / "tolima_municipios.shp"
        municipios.to_file(municipios_output)
        print(f"   💾 Guardado en: {municipios_output}")
        
    else:
        print("   ❌ Archivo Municipios.shp no encontrado")
        municipios = None
    
    # ===================== PROCESAR VEREDAS DEL TOLIMA =====================
    print("\n🏘️  Procesando veredas del Tolima...")
    
    veredas_path = shapefile_dir / "Veredas.shp"
    if veredas_path.exists():
        # Leer todas las veredas
        veredas_all = gpd.read_file(veredas_path)
        print(f"   📊 Total veredas en archivo: {len(veredas_all)}")
        
        # FILTRAR SOLO TOLIMA (código departamento 73)
        veredas_tolima = veredas_all[veredas_all['COD_DPTO'] == '73'].copy()
        print(f"   🎯 Veredas del Tolima: {len(veredas_tolima)}")
        
        if len(veredas_tolima) == 0:
            print("   ⚠️  No se encontraron veredas del Tolima con COD_DPTO='73'")
            print("   🔍 Verificando otros códigos de departamento...")
            
            # Buscar códigos alternativos para Tolima
            cod_deptos = veredas_all['COD_DPTO'].unique()
            print(f"   📋 Códigos de departamento disponibles: {cod_deptos}")
            
            # Buscar por nombre de departamento
            tolima_by_name = veredas_all[veredas_all['NOM_DEP'].str.contains('TOLIMA', case=False, na=False)]
            if len(tolima_by_name) > 0:
                print(f"   🎯 Encontradas {len(tolima_by_name)} veredas buscando por nombre 'TOLIMA'")
                veredas_tolima = tolima_by_name.copy()
        
        if len(veredas_tolima) > 0:
            # Reprojectar a WGS84 si es necesario
            if veredas_tolima.crs != 'EPSG:4326':
                print(f"   🌍 Reproyectando veredas de {veredas_tolima.crs} a EPSG:4326")
                veredas_tolima = veredas_tolima.to_crs('EPSG:4326')
            
            # Limpiar y normalizar nombres
            veredas_tolima['municipio_original'] = veredas_tolima['NOMB_MPIO']
            veredas_tolima['vereda_original'] = veredas_tolima['NOMBRE_VER']
            veredas_tolima['municipio_normalizado'] = veredas_tolima['NOMB_MPIO'].apply(normalize_name)
            veredas_tolima['vereda_normalizada'] = veredas_tolima['NOMBRE_VER'].apply(normalize_name)
            
            print(f"   ✅ {len(veredas_tolima)} veredas del Tolima procesadas")
            
            # Mostrar municipios únicos en veredas
            municipios_en_veredas = sorted(veredas_tolima['NOMB_MPIO'].unique())
            print(f"   🏛️  Municipios con veredas: {len(municipios_en_veredas)}")
            print(f"   📋 Algunos municipios: {municipios_en_veredas[:10]}")
            
            # Guardar veredas procesadas
            veredas_output = output_dir / "tolima_veredas.shp"
            veredas_tolima.to_file(veredas_output)
            print(f"   💾 Guardado en: {veredas_output}")
            
        else:
            print("   ❌ No se pudieron filtrar veredas del Tolima")
            veredas_tolima = None
    else:
        print("   ❌ Archivo Veredas.shp no encontrado")
        veredas_tolima = None
    
    # ===================== LÍMITES DEPARTAMENTALES =====================
    print("\n🗺️  Procesando límites departamentales...")
    
    tolima_path = shapefile_dir / "Tolima_.shp"
    if tolima_path.exists():
        tolima_limite = gpd.read_file(tolima_path)
        
        # Reproyectar si es necesario
        if tolima_limite.crs != 'EPSG:4326':
            print(f"   🌍 Reproyectando límite de {tolima_limite.crs} a EPSG:4326")
            tolima_limite = tolima_limite.to_crs('EPSG:4326')
        
        limite_output = output_dir / "tolima_limite.shp"
        tolima_limite.to_file(limite_output)
        print(f"   ✅ Límite departamental guardado en: {limite_output}")
    
    # ===================== VALIDACIÓN CRUZADA =====================
    print("\n🔍 VALIDACIÓN DE NOMBRES CON DASHBOARD...")
    
    if municipios is not None and veredas_tolima is not None:
        validate_names_with_dashboard(municipios, veredas_tolima)
    
    # ===================== RESUMEN FINAL =====================
    print("\n📊 RESUMEN DE ARCHIVOS PROCESADOS:")
    print("=" * 50)
    
    processed_files = list(output_dir.glob("*.shp"))
    for file in processed_files:
        gdf = gpd.read_file(file)
        print(f"📄 {file.name}: {len(gdf)} registros, CRS: {gdf.crs}")
    
    return output_dir

def normalize_name(name):
    """
    Normaliza nombres para coincidir con la función del dashboard.
    """
    if pd.isna(name):
        return ""
    
    import unicodedata
    import re
    
    # Remover tildes y diacríticos
    name = unicodedata.normalize('NFD', str(name))
    name = ''.join(char for char in name if unicodedata.category(char) != 'Mn')
    
    # Convertir a mayúsculas y limpiar espacios
    name = name.upper().strip()
    name = re.sub(r'\s+', ' ', name)
    
    # Correcciones específicas
    replacements = {
        'VILLARICA': 'VILLARRICA',
        'PURIFICACION': 'PURIFICACION',
    }
    
    return replacements.get(name, name)

def validate_names_with_dashboard(municipios, veredas):
    """
    Valida los nombres de los shapefiles contra los datos del dashboard.
    """
    print("🔗 Validando correspondencia de nombres...")
    
    # Nombres de municipios en shapefiles
    municipios_shp = set(municipios['municipio_normalizado'].unique())
    municipios_veredas_shp = set(veredas['municipio_normalizado'].unique())
    
    print(f"   🏛️  Municipios en shapefile de municipios: {len(municipios_shp)}")
    print(f"   🏛️  Municipios en shapefile de veredas: {len(municipios_veredas_shp)}")
    
    # Comparar
    municipios_comunes = municipios_shp.intersection(municipios_veredas_shp)
    municipios_solo_mpio = municipios_shp - municipios_veredas_shp
    municipios_solo_veredas = municipios_veredas_shp - municipios_shp
    
    print(f"   ✅ Municipios en ambos archivos: {len(municipios_comunes)}")
    if municipios_solo_mpio:
        print(f"   ⚠️  Solo en municipios.shp: {list(municipios_solo_mpio)}")
    if municipios_solo_veredas:
        print(f"   ⚠️  Solo en veredas.shp: {list(municipios_solo_veredas)}")
    
    # Mostrar algunos ejemplos para comparar con Excel
    print("\n📋 EJEMPLOS DE NOMBRES PARA COMPARAR CON DASHBOARD:")
    print("   Municipios (primeros 10):")
    for mpio in sorted(municipios_comunes)[:10]:
        print(f"      - {mpio}")
    
    if len(veredas) > 0:
        print("   Veredas (primeras 10):")
        sample_veredas = veredas.head(10)
        for _, row in sample_veredas.iterrows():
            print(f"      - {row['vereda_normalizada']} ({row['municipio_normalizado']})")

def create_test_map(processed_dir):
    """
    Crea un mapa de prueba para verificar que los datos se ven correctamente.
    """
    try:
        import folium
        
        processed_dir = Path(processed_dir)
        
        # Leer archivos procesados
        municipios_path = processed_dir / "tolima_municipios.shp"
        veredas_path = processed_dir / "tolima_veredas.shp"
        
        if municipios_path.exists():
            municipios = gpd.read_file(municipios_path)
            
            # Crear mapa centrado en Tolima
            center_lat = municipios.geometry.centroid.y.mean()
            center_lon = municipios.geometry.centroid.x.mean()
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
            
            # Agregar municipios
            folium.GeoJson(
                municipios,
                style_function=lambda x: {
                    'fillColor': '#7D0F2B',
                    'color': 'black',
                    'weight': 2,
                    'fillOpacity': 0.3,
                },
                popup=folium.GeoJsonPopup(fields=['MpNombre'])
            ).add_to(m)
            
            # Guardar mapa
            map_output = processed_dir / "test_map.html"
            m.save(map_output)
            print(f"🗺️  Mapa de prueba guardado en: {map_output}")
            
    except ImportError:
        print("⚠️  folium no instalado. Instalar con: pip install folium")

if __name__ == "__main__":
    # Configurar rutas
    SHAPEFILE_DIR = r"C:\Users\Miguel Santos\Desktop\Tolima-Veredas"
    
    print("🚀 INICIANDO PROCESAMIENTO DE SHAPEFILES")
    print("=" * 50)
    
    if os.path.exists(SHAPEFILE_DIR):
        processed_dir = prepare_tolima_shapefiles(SHAPEFILE_DIR)
        
        print(f"\n✅ PROCESAMIENTO COMPLETADO")
        print(f"📁 Archivos procesados en: {processed_dir}")
        
        # Crear mapa de prueba
        create_test_map(processed_dir)
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("1. 🔍 Revisar archivos en la carpeta 'processed'")
        print("2. 🗺️  Abrir test_map.html para ver el mapa")
        print("3. 📋 Comparar nombres con datos del dashboard")
        print("4. 🛠️  Integrar en el dashboard (siguiente script)")
        
    else:
        print(f"❌ Directorio no encontrado: {SHAPEFILE_DIR}")