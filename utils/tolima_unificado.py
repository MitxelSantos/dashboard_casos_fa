#!/usr/bin/env python3
"""
Script para generar archivo unificado de unidades territoriales del Tolima
Incluye 3 niveles: departamento, municipios y veredas
Autor: Tu proyecto epidemiológico
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def crear_unidades_tolima_completo(ruta_veredas_nacional, ruta_municipios_nacional, ruta_salida="tolima_unificado_completo"):
    """
    Crea archivo unificado de unidades territoriales del Tolima
    con 3 niveles: departamento, municipios y veredas
    
    Args:
        ruta_veredas_nacional: Ruta al shapefile CRVeredas_2020.shp
        ruta_municipios_nacional: Ruta al shapefile de municipios IGAC
        ruta_salida: Nombre base para archivos de salida
    """
    
    print("🗺️  Cargando shapefiles nacionales...")
    
    # Cargar veredas
    print("   📁 Cargando veredas...")
    veredas_nacional = gpd.read_file(ruta_veredas_nacional)
    print(f"      Total veredas nacionales: {len(veredas_nacional):,}")
    
    # Cargar municipios
    print("   📁 Cargando municipios...")
    municipios_nacional = gpd.read_file(ruta_municipios_nacional)
    print(f"      Total municipios nacionales: {len(municipios_nacional):,}")
    
    # Filtrar solo Tolima
    print("🎯 Filtrando datos del Tolima...")
    
    # Veredas del Tolima
    tolima_veredas = veredas_nacional[
        veredas_nacional['COD_DPTO'] == '73'
    ].copy()
    print(f"   📊 Veredas del Tolima: {len(tolima_veredas):,}")
    
    # Municipios del Tolima
    tolima_municipios = municipios_nacional[
        municipios_nacional['MpCodigo'].str.startswith('73')
    ].copy()
    print(f"   📊 Municipios del Tolima: {len(tolima_municipios):,}")
    
    # Verificar sistemas de coordenadas y unificar
    print("🔄 Unificando sistemas de coordenadas...")
    
    if tolima_veredas.crs != 'EPSG:4326':
        print(f"   🔄 Convirtiendo veredas de {tolima_veredas.crs} a EPSG:4326...")
        tolima_veredas = tolima_veredas.to_crs('EPSG:4326')
    
    if tolima_municipios.crs != 'EPSG:4326':
        print(f"   🔄 Convirtiendo municipios de {tolima_municipios.crs} a EPSG:4326...")
        tolima_municipios = tolima_municipios.to_crs('EPSG:4326')
    
    # Crear estructura unificada
    print("🔧 Creando estructuras unificadas...")
    
    # 1. NIVEL DEPARTAMENTAL
    print("   🏛️  Generando nivel departamental...")
    departamento_geom = tolima_municipios.dissolve().geometry.iloc[0]
    area_total_km2 = tolima_veredas['AREA_HA'].sum() / 100  # Convertir ha a km²
    
    departamento = gpd.GeoDataFrame({
        'tipo': ['departamento'],
        'codigo_divipola': ['73'],
        'codigo_dpto': ['73'],
        'codigo_municipio': [None],
        'nombre': ['TOLIMA'],
        'municipio': [None],
        'area_km2': [area_total_km2],
        'geometry': [departamento_geom]
    }, crs='EPSG:4326')
    
    # 2. NIVEL MUNICIPAL
    print("   🏘️  Generando nivel municipal...")
    municipios = gpd.GeoDataFrame({
        'tipo': 'municipio',
        'codigo_divipola': tolima_municipios['MpCodigo'],
        'codigo_dpto': '73',
        'codigo_municipio': tolima_municipios['MpCodigo'],
        'nombre': tolima_municipios['MpNombre'],
        'municipio': tolima_municipios['MpNombre'],
        'area_km2': tolima_municipios['MpArea'],  # Ya en km²
        'geometry': tolima_municipios['geometry']
    }, crs='EPSG:4326')
    
    # 3. NIVEL VEREDAL
    print("   🌾 Generando nivel veredal...")
    veredas = gpd.GeoDataFrame({
        'tipo': 'vereda',
        'codigo_divipola': tolima_veredas['CODIGO_VER'],
        'codigo_dpto': tolima_veredas['COD_DPTO'],
        'codigo_municipio': tolima_veredas['DPTOMPIO'],
        'nombre': tolima_veredas['NOMBRE_VER'],
        'municipio': tolima_veredas['NOMB_MPIO'],
        'area_km2': tolima_veredas['AREA_HA'] / 100,  # Convertir ha a km²
        'geometry': tolima_veredas['geometry']
    }, crs='EPSG:4326')
    
    # Unificar todos los niveles
    print("🔗 Unificando todos los niveles...")
    
    unidades_unificadas = pd.concat([
        departamento,
        municipios.reset_index(drop=True),
        veredas.reset_index(drop=True)
    ], ignore_index=True)
    
    # Convertir a GeoDataFrame
    unidades_unificadas = gpd.GeoDataFrame(unidades_unificadas, crs='EPSG:4326')
    
    # Limpiar datos
    print("🧹 Limpiando datos...")
    
    # Resetear índice y limpiar
    unidades_unificadas = unidades_unificadas.reset_index(drop=True)
    
    # Ordenar por tipo y código para mejor organización
    orden_tipos = {'departamento': 1, 'municipio': 2, 'vereda': 3}
    unidades_unificadas['orden'] = unidades_unificadas['tipo'].map(orden_tipos)
    unidades_unificadas = unidades_unificadas.sort_values(['orden', 'codigo_divipola']).drop('orden', axis=1)
    unidades_unificadas = unidades_unificadas.reset_index(drop=True)
    
    # Estadísticas finales
    print("📊 Estadísticas finales:")
    conteos = unidades_unificadas['tipo'].value_counts()
    for tipo, count in conteos.items():
        print(f"   • {tipo.capitalize()}: {count:,}")
    
    print(f"   • Total unidades: {len(unidades_unificadas):,}")
    print(f"   • Área total: {unidades_unificadas[unidades_unificadas['tipo'] == 'departamento']['area_km2'].iloc[0]:,.2f} km²")
    print(f"   • Sistema coordenadas: {unidades_unificadas.crs}")
    
    # Verificar calidad de datos
    print("🔍 Verificando calidad de datos...")
    nulos = unidades_unificadas.isnull().sum()
    if nulos.sum() > 0:
        print("   ⚠️  Valores nulos encontrados:")
        for col, count in nulos[nulos > 0].items():
            print(f"      {col}: {count} nulos")
    else:
        print("   ✅ Sin valores nulos críticos")
    
    # Guardar en múltiples formatos
    print("💾 Guardando archivos...")
    
    # 1. GeoJSON (mejor para web)
    ruta_geojson = f"{ruta_salida}.geojson"
    unidades_unificadas.to_file(ruta_geojson, driver='GeoJSON')
    print(f"   ✅ GeoJSON: {ruta_geojson}")
    
    # 2. Shapefile (compatible con todo)
    ruta_shapefile = f"{ruta_salida}.shp"
    # Truncar nombres de columnas para shapefile
    columnas_shp = unidades_unificadas.copy()
    columnas_shp = columnas_shp.rename(columns={
        'codigo_divipola': 'cod_divipo',
        'codigo_dpto': 'cod_dpto',
        'codigo_municipio': 'cod_munic',
        'municipio': 'municipio'
    })
    columnas_shp.to_file(ruta_shapefile, driver='ESRI Shapefile')
    print(f"   ✅ Shapefile: {ruta_shapefile}")
    
    # 3. GeoParquet (eficiente para Python/SQL)
    try:
        ruta_parquet = f"{ruta_salida}.parquet"
        unidades_unificadas.to_parquet(ruta_parquet)
        print(f"   ✅ GeoParquet: {ruta_parquet}")
    except ImportError:
        print("   ⚠️  GeoParquet no disponible (instalar: pip install pyarrow)")
    
    # Mostrar muestra de datos por tipo
    print("\n📋 Muestra de datos por tipo:")
    for tipo in ['departamento', 'municipio', 'vereda']:
        muestra = unidades_unificadas[unidades_unificadas['tipo'] == tipo].head(3)
        print(f"\n{tipo.upper()}:")
        print(muestra[['tipo', 'codigo_divipola', 'nombre', 'municipio', 'area_km2']].to_string(index=False))
    
    return unidades_unificadas

def mostrar_resumen_completo(gdf):
    """Muestra resumen estadístico completo del GeoDataFrame"""
    print("\n📊 RESUMEN FINAL COMPLETO")
    print("=" * 60)
    
    # Estadísticas por tipo
    print("📈 Estadísticas por tipo:")
    for tipo in ['departamento', 'municipio', 'vereda']:
        subset = gdf[gdf['tipo'] == tipo]
        if len(subset) > 0:
            area_total = subset['area_km2'].sum()
            print(f"   {tipo.capitalize()}:")
            print(f"      • Cantidad: {len(subset):,}")
            print(f"      • Área total: {area_total:,.2f} km²")
            if tipo != 'departamento':
                print(f"      • Área promedio: {subset['area_km2'].mean():.2f} km²")
    
    # Top municipios por número de veredas
    if 'vereda' in gdf['tipo'].values:
        print("\n🏘️  Municipios con más veredas:")
        veredas_por_municipio = gdf[gdf['tipo'] == 'vereda']['municipio'].value_counts().head()
        for municipio, count in veredas_por_municipio.items():
            area_total = gdf[(gdf['tipo'] == 'vereda') & (gdf['municipio'] == municipio)]['area_km2'].sum()
            print(f"   {municipio}: {count} veredas ({area_total:.2f} km²)")
    
    # Rangos de área
    veredas_subset = gdf[gdf['tipo'] == 'vereda']
    if len(veredas_subset) > 0:
        print("\n📏 Rangos de área (veredas):")
        print(f"   Más grande: {veredas_subset['area_km2'].max():.2f} km² ({veredas_subset.loc[veredas_subset['area_km2'].idxmax(), 'nombre']})")
        print(f"   Más pequeña: {veredas_subset['area_km2'].min():.2f} km² ({veredas_subset.loc[veredas_subset['area_km2'].idxmin(), 'nombre']})")
        print(f"   Promedio: {veredas_subset['area_km2'].mean():.2f} km²")

def validar_estructura_sql(gdf):
    """Valida que la estructura sea compatible con PostgreSQL"""
    print("\n🔧 VALIDACIÓN PARA POSTGRESQL")
    print("=" * 40)
    
    # Verificar tipos de datos
    print("📋 Tipos de datos:")
    for col in gdf.columns:
        if col != 'geometry':
            dtype = gdf[col].dtype
            print(f"   {col}: {dtype}")
    
    # Verificar unicidad de códigos por tipo
    print("\n🔑 Verificación de claves únicas:")
    duplicados = gdf.groupby(['tipo', 'codigo_divipola']).size()
    duplicados = duplicados[duplicados > 1]
    
    if len(duplicados) == 0:
        print("   ✅ Sin duplicados en (tipo + codigo_divipola)")
    else:
        print("   ⚠️  Duplicados encontrados:")
        print(duplicados)
    
    # Sugerir DDL para PostgreSQL
    print("\n💾 DDL sugerido para PostgreSQL:")
    print("""
    CREATE TABLE unidades_territoriales_tolima (
        id SERIAL PRIMARY KEY,
        tipo VARCHAR(20) CHECK (tipo IN ('departamento', 'municipio', 'vereda')),
        codigo_divipola VARCHAR(15) NOT NULL,
        codigo_dpto VARCHAR(2) NOT NULL,
        codigo_municipio VARCHAR(5),
        nombre VARCHAR(200) NOT NULL,
        municipio VARCHAR(100),
        area_km2 DECIMAL(12,6),
        geometry GEOMETRY(POLYGON, 4326),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT uk_tipo_codigo UNIQUE (tipo, codigo_divipola)
    );
    
    -- Índices recomendados
    CREATE INDEX idx_unidades_tipo ON unidades_territoriales_tolima(tipo);
    CREATE INDEX idx_unidades_municipio ON unidades_territoriales_tolima(codigo_municipio);
    CREATE INDEX idx_unidades_spatial ON unidades_territoriales_tolima USING GIST(geometry);
    """)

if __name__ == "__main__":
    # Configuración - AJUSTAR RUTAS
    RUTA_VEREDAS = "CRVeredas_2020.shp"
    RUTA_MUNICIPIOS = "Municipio, Distrito y Area no municipalizada.shp"
    RUTA_SALIDA = "tolima_completo"
    
    try:
        # Verificar archivos
        for archivo in [RUTA_VEREDAS, RUTA_MUNICIPIOS]:
            if not Path(archivo).exists():
                raise FileNotFoundError(f"No se encontró: {archivo}")
        
        # Crear archivo unificado completo
        print("🚀 Iniciando proceso de unificación completa...")
        unidades = crear_unidades_tolima_completo(RUTA_VEREDAS, RUTA_MUNICIPIOS, RUTA_SALIDA)
        
        # Mostrar resúmenes
        mostrar_resumen_completo(unidades)
        validar_estructura_sql(unidades)
        
        print("\n🎉 ¡Proceso completado exitosamente!")
        print(f"📁 Archivos generados con prefijo: {RUTA_SALIDA}")
        print("\n📋 Archivos listos para:")
        print("   🌐 Mapas web: .geojson")
        print("   🗺️  GIS software: .shp") 
        print("   🐘 PostgreSQL: .parquet o .geojson")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("💡 Verifica las rutas de los shapefiles:")
        print(f"   • Veredas: {RUTA_VEREDAS}")
        print(f"   • Municipios: {RUTA_MUNICIPIOS}")
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print("💡 Verifica que todos los paquetes estén instalados:")
        print("   pip install geopandas pandas pyarrow")