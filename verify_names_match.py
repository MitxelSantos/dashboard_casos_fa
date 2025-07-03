#!/usr/bin/env python3
"""
Script para verificar correspondencia entre nombres del dashboard y shapefiles.
Ejecutar después de preparar los shapefiles.
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import unicodedata
import re

def normalize_text_dashboard(text):
    """
    Función de normalización copiada del dashboard.
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""

    # Remover tildes y diacríticos
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")

    # Convertir a mayúsculas y limpiar espacios
    text = text.upper().strip()
    text = re.sub(r"\s+", " ", text)

    # Reemplazos específicos
    replacements = {
        "VILLARICA": "VILLARRICA",
        "PURIFICACION": "PURIFICACION",
    }

    for old, new in replacements.items():
        if text == old:
            text = new
            break

    return text

def load_dashboard_data():
    """
    Carga datos del dashboard (simula la carga de Excel).
    """
    print("📊 CARGANDO DATOS DEL DASHBOARD...")
    
    # Rutas de los archivos Excel - buscar en diferentes ubicaciones
    possible_locations = [
        Path("data"),
        Path("."),  # Directorio actual
        Path("../")  # Directorio padre
    ]
    
    casos_file = None
    epizootias_file = None
    
    # Buscar archivos en diferentes ubicaciones
    for location in possible_locations:
        casos_candidate = location / "BD_positivos.xlsx"
        epizootias_candidate = location / "Información_Datos_FA.xlsx"
        
        if casos_candidate.exists():
            casos_file = casos_candidate
        if epizootias_candidate.exists():
            epizootias_file = epizootias_candidate
        
        if casos_file and epizootias_file:
            break
    
    print(f"   📁 Buscando archivos en: {[str(p) for p in possible_locations]}")
    
    casos_municipios = set()
    casos_veredas = set()
    epi_municipios = set()
    epi_veredas = set()
    
    # Cargar casos si existe
    if casos_file.exists():
        try:
            casos_df = pd.read_excel(casos_file, sheet_name="ACUMU", engine="openpyxl")
            print(f"   ✅ Casos cargados: {len(casos_df)} registros")
            
            # Mapear columnas (del dashboard)
            casos_columns_map = {
                "nmun_proce": "municipio",
                "vereda_": "vereda",
            }
            
            for old_col, new_col in casos_columns_map.items():
                if old_col in casos_df.columns:
                    casos_df[new_col] = casos_df[old_col]
            
            # Normalizar nombres
            if "municipio" in casos_df.columns:
                casos_df["municipio_normalizado"] = casos_df["municipio"].apply(normalize_text_dashboard)
                casos_municipios = set(casos_df["municipio_normalizado"].dropna())
            
            if "vereda" in casos_df.columns:
                casos_df["vereda_normalizada"] = casos_df["vereda"].apply(normalize_text_dashboard)
                casos_veredas = set(casos_df["vereda_normalizada"].dropna())
                
        except Exception as e:
            print(f"   ⚠️ Error cargando casos: {e}")
    else:
        print(f"   ⚠️ Archivo de casos no encontrado: {casos_file}")
    
    # Cargar epizootias si existe
    if epizootias_file.exists():
        try:
            epi_df = pd.read_excel(epizootias_file, sheet_name="Base de Datos", engine="openpyxl")
            print(f"   ✅ Epizootias cargadas: {len(epi_df)} registros")
            
            # Mapear columnas
            epizootias_columns_map = {
                "MUNICIPIO": "municipio",
                "VEREDA": "vereda",
            }
            
            for old_col, new_col in epizootias_columns_map.items():
                if old_col in epi_df.columns:
                    epi_df[new_col] = epi_df[old_col]
            
            # Normalizar nombres
            if "municipio" in epi_df.columns:
                epi_df["municipio_normalizado"] = epi_df["municipio"].apply(normalize_text_dashboard)
                epi_municipios = set(epi_df["municipio_normalizado"].dropna())
            
            if "vereda" in epi_df.columns:
                epi_df["vereda_normalizada"] = epi_df["vereda"].apply(normalize_text_dashboard)
                epi_veredas = set(epi_df["vereda_normalizada"].dropna())
                
        except Exception as e:
            print(f"   ⚠️ Error cargando epizootias: {e}")
    else:
        print(f"   ⚠️ Archivo de epizootias no encontrado: {epizootias_file}")
    
    # Combinar datos
    all_municipios = casos_municipios.union(epi_municipios)
    all_veredas = casos_veredas.union(epi_veredas)
    
    print(f"   📋 Municipios únicos en dashboard: {len(all_municipios)}")
    print(f"   📋 Veredas únicas en dashboard: {len(all_veredas)}")
    
    return {
        "municipios": sorted(all_municipios),
        "veredas": sorted(all_veredas)
    }

def load_shapefile_data():
    """
    Carga datos de shapefiles procesados.
    """
    print("\n🗺️ CARGANDO DATOS DE SHAPEFILES...")
    
    processed_dir = Path(r"C:\Users\Miguel Santos\Desktop\Tolima-Veredas\processed")
    
    shp_municipios = set()
    shp_veredas = set()
    
    # Cargar municipios
    municipios_path = processed_dir / "tolima_municipios.shp"
    if municipios_path.exists():
        try:
            municipios_gdf = gpd.read_file(municipios_path)
            print(f"   ✅ Municipios shapefile: {len(municipios_gdf)} registros")
            print(f"   📋 Columnas disponibles: {list(municipios_gdf.columns)}")
            
            # Usar columnas truncadas que vimos en el output
            if 'municipi_1' in municipios_gdf.columns:
                shp_municipios = set(municipios_gdf["municipi_1"].dropna())
            elif 'municipio_normalizado' in municipios_gdf.columns:
                shp_municipios = set(municipios_gdf["municipio_normalizado"].dropna())
            elif 'MpNombre' in municipios_gdf.columns:
                shp_municipios = set(municipios_gdf["MpNombre"].apply(normalize_text_dashboard).dropna())
            else:
                print(f"   ⚠️ No se encontró columna de municipio esperada")
                
        except Exception as e:
            print(f"   ⚠️ Error cargando municipios shapefile: {e}")
    else:
        print(f"   ⚠️ Shapefile de municipios no encontrado: {municipios_path}")
    
    # Cargar veredas
    veredas_path = processed_dir / "tolima_veredas.shp"
    if veredas_path.exists():
        try:
            veredas_gdf = gpd.read_file(veredas_path)
            print(f"   ✅ Veredas shapefile: {len(veredas_gdf)} registros")
            print(f"   📋 Columnas disponibles: {list(veredas_gdf.columns)}")
            
            # Usar columnas truncadas que vimos en el output
            if 'vereda_nor' in veredas_gdf.columns:
                shp_veredas = set(veredas_gdf["vereda_nor"].dropna())
            elif 'vereda_normalizada' in veredas_gdf.columns:
                shp_veredas = set(veredas_gdf["vereda_normalizada"].dropna())
            elif 'NOMBRE_VER' in veredas_gdf.columns:
                shp_veredas = set(veredas_gdf["NOMBRE_VER"].apply(normalize_text_dashboard).dropna())
            else:
                print(f"   ⚠️ No se encontró columna de vereda esperada")
                
        except Exception as e:
            print(f"   ⚠️ Error cargando veredas shapefile: {e}")
    else:
        print(f"   ⚠️ Shapefile de veredas no encontrado: {veredas_path}")
    
    print(f"   📋 Municipios únicos en shapefiles: {len(shp_municipios)}")
    print(f"   📋 Veredas únicas en shapefiles: {len(shp_veredas)}")
    
    return {
        "municipios": sorted(shp_municipios),
        "veredas": sorted(shp_veredas)
    }

def compare_names(dashboard_data, shapefile_data):
    """
    Compara nombres entre dashboard y shapefiles.
    """
    print("\n🔍 COMPARANDO NOMBRES...")
    print("=" * 60)
    
    # Comparar municipios
    print("\n🏛️ MUNICIPIOS:")
    print("-" * 30)
    
    dash_municipios = set(dashboard_data["municipios"])
    shp_municipios = set(shapefile_data["municipios"])
    
    # Estadísticas
    comunes_mpio = dash_municipios.intersection(shp_municipios)
    solo_dashboard_mpio = dash_municipios - shp_municipios
    solo_shapefile_mpio = shp_municipios - dash_municipios
    
    print(f"📊 Dashboard: {len(dash_municipios)} municipios únicos")
    print(f"📊 Shapefiles: {len(shp_municipios)} municipios únicos")
    print(f"✅ Coincidentes: {len(comunes_mpio)} municipios")
    print(f"⚠️ Solo en dashboard: {len(solo_dashboard_mpio)} municipios")
    print(f"⚠️ Solo en shapefiles: {len(solo_shapefile_mpio)} municipios")
    
    # Mostrar detalles
    if comunes_mpio:
        print(f"\n✅ MUNICIPIOS COINCIDENTES (primeros 10):")
        for mpio in sorted(comunes_mpio)[:10]:
            print(f"   - {mpio}")
    
    if solo_dashboard_mpio:
        print(f"\n⚠️ SOLO EN DASHBOARD:")
        for mpio in sorted(solo_dashboard_mpio):
            print(f"   - {mpio}")
    
    if solo_shapefile_mpio:
        print(f"\n⚠️ SOLO EN SHAPEFILES:")
        for mpio in sorted(solo_shapefile_mpio):
            print(f"   - {mpio}")
    
    # Comparar veredas (muestra limitada)
    print("\n🏘️ VEREDAS:")
    print("-" * 30)
    
    dash_veredas = set(dashboard_data["veredas"])
    shp_veredas = set(shapefile_data["veredas"])
    
    comunes_veredas = dash_veredas.intersection(shp_veredas)
    solo_dashboard_veredas = dash_veredas - shp_veredas
    solo_shapefile_veredas = shp_veredas - dash_veredas
    
    print(f"📊 Dashboard: {len(dash_veredas)} veredas únicas")
    print(f"📊 Shapefiles: {len(shp_veredas)} veredas únicas")
    print(f"✅ Coincidentes: {len(comunes_veredas)} veredas")
    print(f"⚠️ Solo en dashboard: {len(solo_dashboard_veredas)} veredas")
    print(f"⚠️ Solo en shapefiles: {len(solo_shapefile_veredas)} veredas")
    
    # Mostrar ejemplos limitados
    if comunes_veredas:
        print(f"\n✅ VEREDAS COINCIDENTES (primeras 10):")
        for vereda in sorted(comunes_veredas)[:10]:
            print(f"   - {vereda}")
    
    if solo_dashboard_veredas:
        print(f"\n⚠️ VEREDAS SOLO EN DASHBOARD (primeras 10):")
        for vereda in sorted(solo_dashboard_veredas)[:10]:
            print(f"   - {vereda}")
    
    return {
        "municipios_match_rate": len(comunes_mpio) / len(dash_municipios) * 100 if dash_municipios else 0,
        "veredas_match_rate": len(comunes_veredas) / len(dash_veredas) * 100 if dash_veredas else 0,
        "comunes_municipios": comunes_mpio,
        "comunes_veredas": comunes_veredas
    }

def generate_recommendations(comparison_results):
    """
    Genera recomendaciones basadas en la comparación.
    """
    print("\n🚀 RECOMENDACIONES:")
    print("=" * 40)
    
    mpio_match = comparison_results["municipios_match_rate"]
    veredas_match = comparison_results["veredas_match_rate"]
    
    print(f"📊 Tasa de coincidencia municipios: {mpio_match:.1f}%")
    print(f"📊 Tasa de coincidencia veredas: {veredas_match:.1f}%")
    
    if mpio_match >= 80:
        print("✅ MUNICIPIOS: Excelente coincidencia - Los mapas funcionarán bien")
    elif mpio_match >= 60:
        print("⚠️ MUNICIPIOS: Buena coincidencia - Algunos municipios no se mostrarán")
    else:
        print("❌ MUNICIPIOS: Baja coincidencia - Revisar normalización de nombres")
    
    if veredas_match >= 50:
        print("✅ VEREDAS: Coincidencia aceptable para mapas detallados")
    elif veredas_match >= 25:
        print("⚠️ VEREDAS: Coincidencia parcial - Mapas funcionales pero incompletos")
    else:
        print("❌ VEREDAS: Baja coincidencia - Considerar revisión manual")
    
    print("\n🛠️ PRÓXIMAS ACCIONES:")
    if mpio_match < 80:
        print("1. 🔧 Revisar función normalize_text() en utils/data_processor.py")
        print("2. 🔍 Agregar más reemplazos específicos para municipios")
    
    if veredas_match < 50:
        print("3. 📝 Considerar mapeo manual de veredas problemáticas")
        print("4. 🗺️ Usar principalmente mapas de municipios")
    
    print("5. ▶️ Probar dashboard con: streamlit run app.py")
    print("6. 🗺️ Verificar pestaña de mapas")

def main():
    """
    Función principal de verificación.
    """
    print("🔍 VERIFICADOR DE CORRESPONDENCIA DE NOMBRES")
    print("Dashboard Fiebre Amarilla vs Shapefiles Tolima")
    print("=" * 60)
    
    # Cargar datos
    dashboard_data = load_dashboard_data()
    shapefile_data = load_shapefile_data()
    
    # Verificar que tengamos datos
    if not dashboard_data["municipios"] and not dashboard_data["veredas"]:
        print("❌ No se pudieron cargar datos del dashboard")
        return
    
    if not shapefile_data["municipios"] and not shapefile_data["veredas"]:
        print("❌ No se pudieron cargar datos de shapefiles")
        print("💡 Ejecute primero: python prepare_tolima_shapefiles.py")
        return
    
    # Comparar
    comparison_results = compare_names(dashboard_data, shapefile_data)
    
    # Generar recomendaciones
    generate_recommendations(comparison_results)
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("📋 Revise las recomendaciones anteriores antes de proceder")

if __name__ == "__main__":
    main()