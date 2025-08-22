#!/usr/bin/env python3
"""
Script para generar archivo unificado de unidades territoriales del Tolima
Incluye 4 niveles: departamento, municipios, veredas y cabeceras municipales
Autor: Tu proyecto epidemiológico
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Mapeo municipio -> región (usando nombres exactos del shapefile de municipios)
MUNICIPIO_REGION = {
    'Ibagué': 'CENTRO',
    'Villarrica': 'ORIENTE',
    'Venadillo': 'NEVADOS',
    'Valle De San Juan': 'CENTRO',
    'Suárez': 'SUR ORIENTE',
    'Santa Isabel': 'NEVADOS',
    'San Luis': 'CENTRO',
    'San Antonio': 'SUR',
    'Saldaña': 'SUR ORIENTE',
    'Rovira': 'CENTRO',
    'Roncesvalles': 'SUR',
    'Rioblanco': 'SUR',
    'Purificación': 'SUR ORIENTE',
    'Prado': 'SUR ORIENTE',
    'Planadas': 'SUR',
    'Piedras': 'CENTRO',
    'Palocabildo': 'NORTE',
    'Natagaima': 'SUR',
    'Murillo': 'NEVADOS',
    'Melgar': 'ORIENTE',
    'Mariquita': 'NORTE',
    'Líbano': 'NEVADOS',
    'Lérida': 'NEVADOS',
    'Icononzo': 'ORIENTE',
    'Honda': 'NORTE',
    'Herveo': 'NEVADOS',
    'Guamo': 'SUR ORIENTE',
    'Fresno': 'NORTE',
    'Flandes': 'CENTRO',
    'Falan': 'NORTE',
    'Espinal': 'CENTRO',
    'Dolores': 'SUR ORIENTE',
    'Cunday': 'ORIENTE',
    'Coyaima': 'SUR',
    'Coello': 'CENTRO',
    'Chaparral': 'SUR',
    'Casabianca': 'NEVADOS',
    'Carmen De Apicalá': 'ORIENTE',
    'Cajamarca': 'CENTRO',
    'Ataco': 'SUR',
    'Anzoátegui': 'CENTRO',
    'Ambalema': 'NEVADOS',
    'Alvarado': 'CENTRO',
    'Alpujarra': 'SUR ORIENTE',
    'Villahermosa': 'NEVADOS',
    'Ortega': 'SUR',
    'Armero': 'NORTE'
}

def to_title_case(text):
    """Convierte texto a Title Case respetando preposiciones"""
    if not text:
        return text
    
    # Palabras que deben permanecer en minúsculas (preposiciones, artículos)
    lowercase_words = {'de', 'del', 'la', 'las', 'el', 'los', 'y', 'e', 'o', 'u'}
    
    words = str(text).split()
    result = []
    
    for i, word in enumerate(words):
        # Primera palabra siempre en Title Case
        if i == 0:
            result.append(word.capitalize())
        # Preposiciones en minúsculas (excepto si es la primera palabra)
        elif word.lower() in lowercase_words:
            result.append(word.lower())
        # Resto en Title Case
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)

def crear_mapeo_municipio_codigo(municipios_gdf):
    """Crear mapeo de código municipio -> nombre para asignar regiones a cabeceras"""
    mapeo = {}
    for _, row in municipios_gdf.iterrows():
        codigo = row['MpCodigo']
        nombre = row['MpNombre']
        mapeo[codigo] = nombre
    return mapeo

def crear_unidades_tolima_urbano_rural(ruta_municipios, ruta_veredas, ruta_cabeceras, ruta_salida="tolima_cabeceras_veredas"):
    """
    Crea archivo unificado de unidades territoriales del Tolima
    con 4 niveles: departamento, municipios, veredas y cabeceras municipales
    
    Args:
        ruta_municipios: Ruta al shapefile Municipios.shp
        ruta_veredas: Ruta al shapefile Veredas.shp  
        ruta_cabeceras: Ruta al shapefile Cabeceras_Municipales.shp
        ruta_salida: Nombre base para archivos de salida
    """
    
    print("🗺️  Cargando shapefiles...")
    
    # Cargar municipios
    print("   📁 Cargando municipios...")
    municipios_nacional = gpd.read_file(ruta_municipios)
    tolima_municipios = municipios_nacional[
        municipios_nacional['MpCodigo'].str.startswith('73')
    ].copy()
    print(f"      Municipios del Tolima: {len(tolima_municipios)}")
    
    # Cargar veredas
    print("   📁 Cargando veredas...")
    veredas_nacional = gpd.read_file(ruta_veredas)
    tolima_veredas = veredas_nacional[
        veredas_nacional['COD_DPTO'] == '73'
    ].copy()
    print(f"      Veredas del Tolima: {len(tolima_veredas)}")
    
    # Cargar cabeceras (solo COD_CLAS = 1)
    print("   📁 Cargando cabeceras municipales...")
    cabeceras_nacional = gpd.read_file(ruta_cabeceras)
    tolima_cabeceras = cabeceras_nacional[
        (cabeceras_nacional['COD_DPTO'] == '73') &
        (cabeceras_nacional['COD_CLAS'] == '1')
    ].copy()
    print(f"      Cabeceras municipales del Tolima: {len(tolima_cabeceras)}")
    
    # Verificar sistemas de coordenadas y unificar
    print("🔄 Unificando sistemas de coordenadas...")
    
    if tolima_municipios.crs != 'EPSG:4326':
        print(f"   🔄 Convirtiendo municipios de {tolima_municipios.crs} a EPSG:4326...")
        tolima_municipios = tolima_municipios.to_crs('EPSG:4326')
    
    if tolima_veredas.crs != 'EPSG:4326':
        print(f"   🔄 Convirtiendo veredas de {tolima_veredas.crs} a EPSG:4326...")
        tolima_veredas = tolima_veredas.to_crs('EPSG:4326')
        
    if tolima_cabeceras.crs != 'EPSG:4326':
        print(f"   🔄 Convirtiendo cabeceras de {tolima_cabeceras.crs} a EPSG:4326...")
        tolima_cabeceras = tolima_cabeceras.to_crs('EPSG:4326')
    
    # Crear mapeo código -> nombre de municipio para cabeceras
    mapeo_codigo_municipio = crear_mapeo_municipio_codigo(tolima_municipios)
    
    # Asignar regiones
    print("🏷️  Asignando regiones...")
    
    # Asignar regiones a municipios
    tolima_municipios['region'] = tolima_municipios['MpNombre'].map(MUNICIPIO_REGION)
    
    # Para veredas: resolver inconsistencia de nombres (mayúsculas vs title case)
    # Crear diccionario de región basado en nombres normalizados
    municipio_region_normalizado = {}
    for nombre_title, region in MUNICIPIO_REGION.items():
        municipio_region_normalizado[nombre_title.upper()] = region
    
    # Mapeo especial para nombres que difieren
    MAPEO_NOMBRES_VEREDAS = {
        'SAN SEBASTIÁN DE MARIQUITA': 'MARIQUITA'
    }
    
    # Asignar regiones a veredas
    def asignar_region_vereda(nombre_municipio):
        # Aplicar mapeo de nombres especiales
        nombre_normalizado = MAPEO_NOMBRES_VEREDAS.get(nombre_municipio, nombre_municipio)
        return municipio_region_normalizado.get(nombre_normalizado.upper())
    
    tolima_veredas['region'] = tolima_veredas['NOMB_MPIO'].apply(asignar_region_vereda)
    
    # Estandarizar nombres de municipios en veredas
    def estandarizar_nombre_municipio_vereda(nombre_municipio):
        nombre_normalizado = MAPEO_NOMBRES_VEREDAS.get(nombre_municipio, nombre_municipio)
        # Buscar correspondencia en el diccionario de regiones
        for nombre_title in MUNICIPIO_REGION.keys():
            if nombre_title.upper() == nombre_normalizado.upper():
                return nombre_title
        return nombre_municipio
    
    tolima_veredas['municipio_estandarizado'] = tolima_veredas['NOMB_MPIO'].apply(estandarizar_nombre_municipio_vereda)
    
    # Estandarizar nombres de veredas a Title Case
    tolima_veredas['vereda_estandarizada'] = tolima_veredas['NOMBRE_VER'].apply(to_title_case)
    
    # Asignar regiones y municipios a cabeceras
    tolima_cabeceras['municipio_nombre'] = tolima_cabeceras['COD_MPIO'].map(mapeo_codigo_municipio)
    tolima_cabeceras['region'] = tolima_cabeceras['municipio_nombre'].map(MUNICIPIO_REGION)
    tolima_cabeceras['cabecera_estandarizada'] = tolima_cabeceras['NOM_CPOB'].apply(to_title_case)
    
    # Verificar asignación de regiones
    municipios_sin_region = tolima_municipios[tolima_municipios['region'].isna()]
    veredas_sin_region = tolima_veredas[tolima_veredas['region'].isna()]
    cabeceras_sin_region = tolima_cabeceras[tolima_cabeceras['region'].isna()]
    
    print(f"   ✅ Municipios con región: {len(tolima_municipios) - len(municipios_sin_region)}/{len(tolima_municipios)}")
    print(f"   ✅ Veredas con región: {len(tolima_veredas) - len(veredas_sin_region)}/{len(tolima_veredas)}")
    print(f"   ✅ Cabeceras con región: {len(tolima_cabeceras) - len(cabeceras_sin_region)}/{len(tolima_cabeceras)}")
    
    if len(municipios_sin_region) > 0:
        print(f"   ⚠️  Municipios sin región: {list(municipios_sin_region['MpNombre'])}")
    if len(veredas_sin_region) > 0:
        print(f"   ⚠️  Veredas sin región: {len(veredas_sin_region)} (municipios: {list(veredas_sin_region['NOMB_MPIO'].unique())})")
    if len(cabeceras_sin_region) > 0:
        print(f"   ⚠️  Cabeceras sin región: {len(cabeceras_sin_region)}")
    
    # Crear estructura unificada
    print("🔧 Creando estructuras unificadas...")
    
    # 1. NIVEL DEPARTAMENTAL
    print("   🏛️  Generando nivel departamental...")
    departamento_geom = tolima_municipios.dissolve().geometry.iloc[0]
    area_total_km2 = tolima_veredas['AREA_HA'].sum() / 100  # Convertir ha a km²
    
    # Calcular perímetro departamental aproximado
    departamento_temp = tolima_municipios.dissolve().to_crs('EPSG:3857')
    perimetro_total_km = departamento_temp.geometry.length.iloc[0] / 1000
    
    departamento = gpd.GeoDataFrame({
        'tipo': ['departamento'],
        'codigo_divipola': ['73'],
        'codigo_dpto': ['73'],
        'codigo_municipio': [None],
        'nombre': ['TOLIMA'],
        'municipio': [None],
        'region': ['TODAS'],
        'area_oficial_km2': [area_total_km2],
        'area_geometrica_km2': [area_total_km2],
        'perimetro_km': [perimetro_total_km],
        'geometry': [departamento_geom]
    }, crs='EPSG:4326')
    
    # 2. NIVEL MUNICIPAL
    print("   🏘️  Generando nivel municipal...")
    
    # Calcular áreas geométricas reales
    municipios_temp = tolima_municipios.to_crs('EPSG:3857')
    area_geometrica_municipios_km2 = municipios_temp.geometry.area / 1_000_000
    perimetro_municipios_km = municipios_temp.geometry.length / 1_000
    
    municipios = gpd.GeoDataFrame({
        'tipo': 'municipio',
        'codigo_divipola': tolima_municipios['MpCodigo'],
        'codigo_dpto': '73',
        'codigo_municipio': tolima_municipios['MpCodigo'],
        'nombre': tolima_municipios['MpNombre'],
        'municipio': tolima_municipios['MpNombre'],
        'region': tolima_municipios['region'],
        'area_oficial_km2': tolima_municipios['MpArea'],
        'area_geometrica_km2': area_geometrica_municipios_km2,
        'perimetro_km': perimetro_municipios_km,
        'geometry': tolima_municipios['geometry']
    }, crs='EPSG:4326')
    
    # 3. NIVEL VEREDAL (RURAL)
    print("   🌾 Generando nivel veredal (rural)...")
    
    # Calcular áreas geométricas de veredas
    veredas_temp = tolima_veredas.to_crs('EPSG:3857')
    area_geometrica_veredas_km2 = veredas_temp.geometry.area / 1_000_000
    perimetro_veredas_km = veredas_temp.geometry.length / 1_000
    
    veredas = gpd.GeoDataFrame({
        'tipo': 'vereda',
        'codigo_divipola': tolima_veredas['CODIGO_VER'],
        'codigo_dpto': tolima_veredas['COD_DPTO'],
        'codigo_municipio': tolima_veredas['DPTOMPIO'],
        'nombre': tolima_veredas['vereda_estandarizada'],
        'municipio': tolima_veredas['municipio_estandarizado'],
        'region': tolima_veredas['region'],
        'area_oficial_km2': tolima_veredas['AREA_HA'] / 100,
        'area_geometrica_km2': area_geometrica_veredas_km2,
        'perimetro_km': perimetro_veredas_km,
        'geometry': tolima_veredas['geometry']
    }, crs='EPSG:4326')
    
    # 4. NIVEL CABECERAS (URBANO)
    print("   🏛️  Generando nivel cabeceras (urbano)...")
    
    # Calcular áreas geométricas de cabeceras
    cabeceras_temp = tolima_cabeceras.to_crs('EPSG:3857')
    area_geometrica_cabeceras_km2 = cabeceras_temp.geometry.area / 1_000_000
    perimetro_cabeceras_km = cabeceras_temp.geometry.length / 1_000
    
    cabeceras = gpd.GeoDataFrame({
        'tipo': 'cabecera',
        'codigo_divipola': tolima_cabeceras['COD_DANE'],
        'codigo_dpto': tolima_cabeceras['COD_DPTO'],
        'codigo_municipio': tolima_cabeceras['COD_MPIO'],
        'nombre': tolima_cabeceras['cabecera_estandarizada'],
        'municipio': tolima_cabeceras['municipio_nombre'],
        'region': tolima_cabeceras['region'],
        'area_oficial_km2': tolima_cabeceras['CPOB_AREA'],
        'area_geometrica_km2': area_geometrica_cabeceras_km2,
        'perimetro_km': perimetro_cabeceras_km,
        'geometry': tolima_cabeceras['geometry']
    }, crs='EPSG:4326')
    
    # Unificar todos los niveles
    print("🔗 Unificando todos los niveles...")
    
    unidades_unificadas = pd.concat([
        departamento,
        municipios.reset_index(drop=True),
        veredas.reset_index(drop=True),
        cabeceras.reset_index(drop=True)
    ], ignore_index=True)
    
    # Convertir a GeoDataFrame
    unidades_unificadas = gpd.GeoDataFrame(unidades_unificadas, crs='EPSG:4326')
    
    # Limpiar datos
    print("🧹 Limpiando datos...")
    unidades_unificadas = unidades_unificadas.reset_index(drop=True)
    
    # Ordenar por tipo y código
    orden_tipos = {'departamento': 1, 'municipio': 2, 'vereda': 3, 'cabecera': 4}
    unidades_unificadas['orden'] = unidades_unificadas['tipo'].map(orden_tipos)
    unidades_unificadas = unidades_unificadas.sort_values(['orden', 'codigo_divipola']).drop('orden', axis=1)
    unidades_unificadas = unidades_unificadas.reset_index(drop=True)
    
    # Estadísticas finales
    print("📊 Estadísticas finales:")
    conteos = unidades_unificadas['tipo'].value_counts()
    for tipo, count in conteos.items():
        print(f"   • {tipo.capitalize()}: {count:,}")
    
    print(f"   • Total unidades: {len(unidades_unificadas):,}")
    area_total = unidades_unificadas[unidades_unificadas['tipo'] == 'departamento']['area_oficial_km2'].iloc[0]
    print(f"   • Área total: {area_total:,.2f} km²")
    print(f"   • Sistema coordenadas: {unidades_unificadas.crs}")
    
    # Estadísticas urbano/rural
    print(f"\n🏙️  Estadísticas urbano/rural:")
    rural_count = len(unidades_unificadas[unidades_unificadas['tipo'] == 'vereda'])
    urbano_count = len(unidades_unificadas[unidades_unificadas['tipo'] == 'cabecera'])
    print(f"   • Rural (veredas): {rural_count:,}")
    print(f"   • Urbano (cabeceras): {urbano_count:,}")
    
    area_rural = unidades_unificadas[unidades_unificadas['tipo'] == 'vereda']['area_oficial_km2'].sum()
    area_urbana = unidades_unificadas[unidades_unificadas['tipo'] == 'cabecera']['area_oficial_km2'].sum()
    print(f"   • Área rural: {area_rural:,.2f} km² ({area_rural/area_total*100:.1f}%)")
    print(f"   • Área urbana: {area_urbana:,.2f} km² ({area_urbana/area_total*100:.1f}%)")
    
    # Estadísticas por región
    print(f"\n📍 Estadísticas por región:")
    regiones_stats = unidades_unificadas[unidades_unificadas['tipo'].isin(['vereda', 'cabecera'])]['region'].value_counts()
    for region, count in regiones_stats.items():
        if region != 'TODAS':
            veredas_region = len(unidades_unificadas[(unidades_unificadas['tipo'] == 'vereda') & (unidades_unificadas['region'] == region)])
            cabeceras_region = len(unidades_unificadas[(unidades_unificadas['tipo'] == 'cabecera') & (unidades_unificadas['region'] == region)])
            area_region = unidades_unificadas[unidades_unificadas['region'] == region]['area_oficial_km2'].sum()
            print(f"   • {region}: {veredas_region} veredas + {cabeceras_region} cabeceras ({area_region:,.2f} km²)")
    
    # Verificar calidad de datos
    print(f"\n🔍 Verificando calidad de datos...")
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
    
    # 2. GeoPackage (formato moderno, recomendado)
    ruta_gpkg = f"{ruta_salida}.gpkg"
    unidades_unificadas.to_file(ruta_gpkg, driver='GPKG')
    print(f"   ✅ GeoPackage: {ruta_gpkg}")
    
    # 3. Shapefile (compatible con todo)
    ruta_shapefile = f"{ruta_salida}.shp"
    columnas_shp = unidades_unificadas.copy()
    columnas_shp = columnas_shp.rename(columns={
        'codigo_divipola': 'cod_divipo',
        'codigo_dpto': 'cod_dpto',
        'codigo_municipio': 'cod_munic',
        'municipio': 'municipio',
        'region': 'region',
        'area_oficial_km2': 'area_ofic',
        'area_geometrica_km2': 'area_geom',
        'perimetro_km': 'perimetro'
    })
    columnas_shp.to_file(ruta_shapefile, driver='ESRI Shapefile')
    print(f"   ✅ Shapefile: {ruta_shapefile}")
    
    # 4. GeoParquet (eficiente para Python/SQL)
    try:
        ruta_parquet = f"{ruta_salida}.parquet"
        unidades_unificadas.to_parquet(ruta_parquet)
        print(f"   ✅ GeoParquet: {ruta_parquet}")
    except ImportError:
        print("   ⚠️  GeoParquet no disponible (instalar: pip install pyarrow)")
    except Exception as e:
        print(f"   ⚠️  Error al guardar GeoParquet: {e}")
    
    # Mostrar muestra de datos por tipo
    print("\n📋 Muestra de datos por tipo:")
    for tipo in ['departamento', 'municipio', 'vereda', 'cabecera']:
        muestra = unidades_unificadas[unidades_unificadas['tipo'] == tipo].head(3)
        print(f"\n{tipo.upper()}:")
        if len(muestra) > 0:
            columnas_muestra = ['tipo', 'codigo_divipola', 'nombre', 'municipio', 'region', 
                              'area_oficial_km2']
            print(muestra[columnas_muestra].to_string(index=False))
    
    return unidades_unificadas

def mostrar_resumen_urbano_rural(gdf):
    """Muestra resumen estadístico específico para análisis urbano/rural"""
    print("\n📊 RESUMEN URBANO/RURAL COMPLETO")
    print("=" * 60)
    
    # Estadísticas por tipo
    print("📈 Estadísticas por tipo:")
    for tipo in ['departamento', 'municipio', 'vereda', 'cabecera']:
        subset = gdf[gdf['tipo'] == tipo]
        if len(subset) > 0:
            area_total = subset['area_oficial_km2'].sum()
            print(f"   {tipo.capitalize()}:")
            print(f"      • Cantidad: {len(subset):,}")
            print(f"      • Área total: {area_total:,.2f} km²")
            if tipo not in ['departamento']:
                print(f"      • Área promedio: {subset['area_oficial_km2'].mean():.2f} km²")
    
    # Análisis urbano vs rural
    print("\n🏙️  Análisis urbano vs rural:")
    veredas = gdf[gdf['tipo'] == 'vereda']
    cabeceras = gdf[gdf['tipo'] == 'cabecera']
    
    if len(veredas) > 0 and len(cabeceras) > 0:
        area_rural = veredas['area_oficial_km2'].sum()
        area_urbana = cabeceras['area_oficial_km2'].sum()
        total_area = area_rural + area_urbana
        
        print(f"   📊 Distribución territorial:")
        print(f"      • Rural: {area_rural:,.2f} km² ({area_rural/total_area*100:.1f}%)")
        print(f"      • Urbano: {area_urbana:,.2f} km² ({area_urbana/total_area*100:.1f}%)")
        
        print(f"   📊 Distribución de unidades:")
        print(f"      • Veredas (rural): {len(veredas):,}")
        print(f"      • Cabeceras (urbano): {len(cabeceras):,}")
    
    # Análisis por región con urbano/rural
    print("\n🗺️  Análisis por región (urbano/rural):")
    regiones = ['CENTRO', 'NEVADOS', 'SUR', 'SUR ORIENTE', 'NORTE', 'ORIENTE']
    
    for region in regiones:
        veredas_region = gdf[(gdf['tipo'] == 'vereda') & (gdf['region'] == region)]
        cabeceras_region = gdf[(gdf['tipo'] == 'cabecera') & (gdf['region'] == region)]
        
        if len(veredas_region) > 0 or len(cabeceras_region) > 0:
            area_rural_region = veredas_region['area_oficial_km2'].sum()
            area_urbana_region = cabeceras_region['area_oficial_km2'].sum()
            
            print(f"\n   📍 {region}:")
            print(f"      • Rural: {len(veredas_region)} veredas ({area_rural_region:,.2f} km²)")
            print(f"      • Urbano: {len(cabeceras_region)} cabeceras ({area_urbana_region:,.2f} km²)")

def validar_estructura_sql_urbano_rural(gdf):
    """Valida estructura con separación urbano/rural para PostgreSQL"""
    print("\n🔧 VALIDACIÓN PARA POSTGRESQL (URBANO/RURAL)")
    print("=" * 50)
    
    # Verificar tipos
    tipos_esperados = {'departamento', 'municipio', 'vereda', 'cabecera'}
    tipos_encontrados = set(gdf['tipo'].unique())
    
    if tipos_esperados == tipos_encontrados:
        print("   ✅ Todos los tipos esperados están presentes")
    else:
        print(f"   ⚠️  Diferencias en tipos:")
        print(f"      Esperados: {tipos_esperados}")
        print(f"      Encontrados: {tipos_encontrados}")
    
if __name__ == "__main__":
    # Configuración - RUTAS AJUSTADAS
    RUTA_MUNICIPIOS = "data\\shapefiles\\Municipios.shp"
    RUTA_VEREDAS = "data\\shapefiles\\Veredas.shp"
    RUTA_CABECERAS = "data\\shapefiles\\Cabeceras_Municipales.shp"
    RUTA_SALIDA = "data\\processed\\tolima_cabeceras_veredas"
    
    try:
        # Verificar archivos
        for archivo in [RUTA_MUNICIPIOS, RUTA_VEREDAS, RUTA_CABECERAS]:
            if not Path(archivo).exists():
                raise FileNotFoundError(f"No se encontró: {archivo}")
        
        # Crear archivo unificado urbano/rural
        print("🚀 Iniciando proceso de unificación urbano/rural...")
        print(f"📍 Regiones configuradas: {len(set(MUNICIPIO_REGION.values()))} regiones")
        print(f"🏘️  Municipios configurados: {len(MUNICIPIO_REGION)} municipios")
        
        unidades = crear_unidades_tolima_urbano_rural(RUTA_MUNICIPIOS, RUTA_VEREDAS, RUTA_CABECERAS, RUTA_SALIDA)
        
        # Mostrar resúmenes
        mostrar_resumen_urbano_rural(unidades)
        validar_estructura_sql_urbano_rural(unidades)
        
        print("\n🎉 ¡Proceso completado exitosamente!")
        print(f"📁 Archivos generados con prefijo: {RUTA_SALIDA}")
        print("\n📋 Archivos listos para:")
        print("   🌐 Mapas web con filtros urbano/rural: .geojson")
        print("   📦 Uso moderno y eficiente: .gpkg (GeoPackage)")
        print("   🗺️  Compatibilidad GIS tradicional: .shp") 
        print("   🐘 PostgreSQL con urbano/rural: .parquet o .geojson")
        
        print("\n🗂️  Funcionalidades incluidas:")
        print("   📍 4 niveles territoriales (departamento, municipio, vereda, cabecera)")
        print("   🏙️  Distinción urbano/rural perfecta (sin solapamientos)")
        print("   🏷️  6 regiones del Tolima (CENTRO, NEVADOS, SUR, etc.)")
        print("   🔗 Códigos DIVIPOLA estándar")
        print("   📝 Nombres estandarizados a Title Case")
        print("   📐 Datos geométricos básicos conservados")
        print("   🎯 Estructura optimizada para análisis epidemiológico urbano/rural")
    
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("💡 Verifica las rutas de los shapefiles:")
        print(f"   • Municipios: {RUTA_MUNICIPIOS}")
        print(f"   • Veredas: {RUTA_VEREDAS}")
        print(f"   • Cabeceras: {RUTA_CABECERAS}")
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print("💡 Verifica que todos los paquetes estén instalados:")
        print("   pip install geopandas pandas pyarrow")