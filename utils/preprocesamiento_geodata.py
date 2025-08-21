#!/usr/bin/env python3
"""
Script para generar archivo unificado de unidades territoriales del Tolima
Incluye 3 niveles: departamento, municipios y veredas + información de regiones
Autor: Tu proyecto epidemiológico
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Mapeo municipio -> región (usando nombres exactos del shapefile IGAC)
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

def crear_unidades_tolima_completo(ruta_veredas_nacional, ruta_municipios_nacional, ruta_salida="tolima_completo_con_regiones"):
    """
    Crea archivo unificado de unidades territoriales del Tolima
    con 3 niveles: departamento, municipios y veredas + información de regiones
    
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
    
    # Asignar regiones
    print("🏷️  Asignando regiones...")
    
    # Mapeo de nombres que difieren entre shapefiles
    MAPEO_NOMBRES_VEREDAS = {
        'SAN SEBASTIÁN DE MARIQUITA': 'Mariquita',
        # Agregar otros si se encuentran
    }
    
    # Función para convertir texto a Title Case apropiado
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
    
    # Función para estandarizar nombres de municipios a Title Case
    def estandarizar_nombre_municipio(nombre_vereda):
        """Convierte nombre de municipio de vereda a formato Title Case estándar"""
        if not nombre_vereda:
            return nombre_vereda
            
        # Aplicar mapeo de nombres diferentes
        nombre_normalizado = MAPEO_NOMBRES_VEREDAS.get(nombre_vereda, nombre_vereda)
        
        # Buscar el nombre en Title Case correspondiente en el diccionario
        for nombre_title, region in MUNICIPIO_REGION.items():
            if nombre_title.upper() == nombre_normalizado.upper():
                return nombre_title
        
        # Si no se encuentra, devolver el original
        return nombre_vereda
    
    # Asignar regiones a municipios (usar nombres directos del shapefile)
    tolima_municipios['region'] = tolima_municipios['MpNombre'].map(MUNICIPIO_REGION)
    
    # Para veredas: primero mapear nombres diferentes, luego buscar región
    tolima_veredas['municipio_normalizado'] = tolima_veredas['NOMB_MPIO'].apply(
        lambda x: MAPEO_NOMBRES_VEREDAS.get(x, x)
    )
    
    # Crear diccionario de región basado en nombres normalizados
    municipio_region_normalizado = {}
    for nombre_title, region in MUNICIPIO_REGION.items():
        municipio_region_normalizado[nombre_title.upper()] = region
    
    # Asignar regiones a veredas
    tolima_veredas['region'] = tolima_veredas['municipio_normalizado'].apply(
        lambda x: municipio_region_normalizado.get(x.upper())
    )
    
    # Estandarizar nombres de municipios en veredas a Title Case
    tolima_veredas['municipio_estandarizado'] = tolima_veredas['municipio_normalizado'].apply(
        lambda x: next((nombre for nombre in MUNICIPIO_REGION.keys() if nombre.upper() == x.upper()), x)
    )
    
    # Estandarizar nombres de veredas a Title Case
    tolima_veredas['vereda_estandarizada'] = tolima_veredas['NOMBRE_VER'].apply(to_title_case)
    
    # Verificar asignación de regiones
    municipios_sin_region = tolima_municipios[tolima_municipios['region'].isna()]
    veredas_sin_region = tolima_veredas[tolima_veredas['region'].isna()]
    
    if len(municipios_sin_region) > 0:
        print(f"   ⚠️  {len(municipios_sin_region)} municipios sin región:")
        for _, mun in municipios_sin_region.iterrows():
            print(f"      - {mun['MpNombre']} (código: {mun['MpCodigo']})")
    else:
        print("   ✅ Todos los municipios tienen región asignada")
    
    if len(veredas_sin_region) > 0:
        print(f"   ⚠️  {len(veredas_sin_region)} veredas sin región")
        municipios_faltantes = veredas_sin_region['NOMB_MPIO'].unique()
        print(f"      Municipios faltantes en veredas: {municipios_faltantes}")
    else:
        print("   ✅ Todas las veredas tienen región asignada")
    
    # Verificar estandarización de nombres
    print("\n📝 Verificando estandarización de nombres...")
    nombres_unicos_municipios = set(tolima_municipios['MpNombre'].unique())
    nombres_unicos_veredas = set(tolima_veredas['municipio_estandarizado'].unique())
    
    diferencias = nombres_unicos_veredas - nombres_unicos_municipios
    if diferencias:
        print(f"   ⚠️  Nombres en veredas no encontrados en municipios: {diferencias}")
    else:
        print("   ✅ Todos los nombres de municipios están estandarizados correctamente")
    
    # Verificar estandarización de nombres de veredas
    print("   📝 Nombres de veredas estandarizados a Title Case:")
    muestra_veredas = tolima_veredas[['NOMBRE_VER', 'vereda_estandarizada']].head(5)
    for _, row in muestra_veredas.iterrows():
        print(f"      '{row['NOMBRE_VER']}' → '{row['vereda_estandarizada']}'")
    print("   ✅ Nombres de veredas estandarizados correctamente")
    
    # Crear estructura unificada
    print("🔧 Creando estructuras unificadas...")
    
    # 1. NIVEL DEPARTAMENTAL
    print("   🏛️  Generando nivel departamental...")
    departamento_geom = tolima_municipios.dissolve().geometry.iloc[0]
    area_total_km2 = tolima_veredas['AREA_HA'].sum() / 100  # Convertir ha a km²
    
    # Calcular perímetro departamental en km (aproximado)
    departamento_bounds = tolima_municipios.total_bounds
    perimetro_aprox = 2 * ((departamento_bounds[2] - departamento_bounds[0]) + 
                          (departamento_bounds[3] - departamento_bounds[1])) * 111  # Conversión grados a km
    
    departamento = gpd.GeoDataFrame({
        'tipo': ['departamento'],
        'codigo_divipola': ['73'],
        'codigo_dpto': ['73'],
        'codigo_municipio': [None],
        'nombre': ['Tolima'],
        'municipio': [None],
        'region': ['TODAS'],  # Nivel departamental incluye todas las regiones
        'area_oficial_km2': [area_total_km2],
        'area_geometrica_km2': [area_total_km2],  # Similar para departamento
        'perimetro_km': [perimetro_aprox],
        'geometry': [departamento_geom]
    }, crs='EPSG:4326')
    
    # 2. NIVEL MUNICIPAL
    print("   🏘️  Generando nivel municipal...")
    
    # Convertir SHAPE_Area de m² a km² (si está en metros cuadrados)
    # Si está en grados cuadrados, calcular área real
    if tolima_municipios.crs == 'EPSG:4326':
        # Para coordenadas geográficas, calcular área real
        municipios_temp = tolima_municipios.to_crs('EPSG:3857')  # Proyección para cálculo preciso
        area_geometrica_m2 = municipios_temp.geometry.area
        perimetro_m = municipios_temp.geometry.length
        area_geometrica_km2 = area_geometrica_m2 / 1_000_000
        perimetro_km = perimetro_m / 1_000
    else:
        # Si ya está proyectado, usar directamente
        area_geometrica_km2 = tolima_municipios['SHAPE_Area'] / 1_000_000
        perimetro_km = tolima_municipios['SHAPE_Leng'] / 1_000
    
    municipios = gpd.GeoDataFrame({
        'tipo': 'municipio',
        'codigo_divipola': tolima_municipios['MpCodigo'],
        'codigo_dpto': '73',
        'codigo_municipio': tolima_municipios['MpCodigo'],
        'nombre': tolima_municipios['MpNombre'],
        'municipio': tolima_municipios['MpNombre'],
        'region': tolima_municipios['region'],
        'area_oficial_km2': tolima_municipios['MpArea'],  # Área oficial en km²
        'area_geometrica_km2': area_geometrica_km2,      # Área calculada del polígono
        'perimetro_km': perimetro_km,                    # Perímetro en km
        'geometry': tolima_municipios['geometry']
    }, crs='EPSG:4326')
    
    # 3. NIVEL VEREDAL
    print("   🌾 Generando nivel veredal...")
    
    # Convertir áreas de veredas (similar proceso)
    if tolima_veredas.crs == 'EPSG:4326':
        veredas_temp = tolima_veredas.to_crs('EPSG:3857')
        area_geometrica_veredas_m2 = veredas_temp.geometry.area
        perimetro_veredas_m = veredas_temp.geometry.length
        area_geometrica_veredas_km2 = area_geometrica_veredas_m2 / 1_000_000
        perimetro_veredas_km = perimetro_veredas_m / 1_000
    else:
        area_geometrica_veredas_km2 = tolima_veredas['SHAPE_Area'] / 1_000_000
        perimetro_veredas_km = tolima_veredas['SHAPE_Leng'] / 1_000
    
    veredas = gpd.GeoDataFrame({
        'tipo': 'vereda',
        'codigo_divipola': tolima_veredas['CODIGO_VER'],
        'codigo_dpto': tolima_veredas['COD_DPTO'],
        'codigo_municipio': tolima_veredas['DPTOMPIO'],
        'nombre': tolima_veredas['vereda_estandarizada'],  # Usar nombre estandarizado
        'municipio': tolima_veredas['municipio_estandarizado'],  # Usar nombre estandarizado
        'region': tolima_veredas['region'],
        'area_oficial_km2': tolima_veredas['AREA_HA'] / 100,    # Convertir ha a km²
        'area_geometrica_km2': area_geometrica_veredas_km2,     # Área calculada del polígono
        'perimetro_km': perimetro_veredas_km,                   # Perímetro en km
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
    area_total = unidades_unificadas[unidades_unificadas['tipo'] == 'departamento']['area_oficial_km2'].iloc[0]
    print(f"   • Área total: {area_total:,.2f} km²")
    print(f"   • Sistema coordenadas: {unidades_unificadas.crs}")
    
    # Estadísticas geométricas
    print(f"   • Información geométrica conservada: perímetros, áreas oficiales y calculadas")
    print(f"   • Índices calculables on-demand: compacidad, complejidad, ratios geométricos")
    
    # Estadísticas por región
    print("\n📍 Estadísticas por región:")
    regiones_stats = unidades_unificadas[unidades_unificadas['tipo'] != 'departamento']['region'].value_counts()
    for region, count in regiones_stats.items():
        if region != 'TODAS':
            municipios_region = len(unidades_unificadas[(unidades_unificadas['tipo'] == 'municipio') & (unidades_unificadas['region'] == region)])
            veredas_region = len(unidades_unificadas[(unidades_unificadas['tipo'] == 'vereda') & (unidades_unificadas['region'] == region)])
            area_region = unidades_unificadas[(unidades_unificadas['tipo'] == 'vereda') & (unidades_unificadas['region'] == region)]['area_oficial_km2'].sum()
            print(f"   • {region}: {municipios_region} municipios, {veredas_region} veredas ({area_region:,.2f} km²)")
    
    # Verificar calidad de datos
    print("\n🔍 Verificando calidad de datos...")
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
    # Truncar nombres de columnas para shapefile (límite 10 caracteres)
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
    for tipo in ['departamento', 'municipio', 'vereda']:
        muestra = unidades_unificadas[unidades_unificadas['tipo'] == tipo].head(3)
        print(f"\n{tipo.upper()}:")
        if len(muestra) > 0:
            columnas_muestra = ['tipo', 'codigo_divipola', 'nombre', 'municipio', 'region', 
                              'area_oficial_km2', 'area_geometrica_km2', 'perimetro_km']
            print(muestra[columnas_muestra].to_string(index=False))
    
    return unidades_unificadas

def mostrar_resumen_completo(gdf):
    """Muestra resumen estadístico completo del GeoDataFrame incluyendo regiones y geometría"""
    print("\n📊 RESUMEN FINAL COMPLETO CON REGIONES Y GEOMETRÍA")
    print("=" * 70)
    
    # Estadísticas por tipo
    print("📈 Estadísticas por tipo:")
    for tipo in ['departamento', 'municipio', 'vereda']:
        subset = gdf[gdf['tipo'] == tipo]
        if len(subset) > 0:
            area_total = subset['area_oficial_km2'].sum()
            print(f"   {tipo.capitalize()}:")
            print(f"      • Cantidad: {len(subset):,}")
            print(f"      • Área total: {area_total:,.2f} km²")
            if tipo != 'departamento':
                print(f"      • Área promedio: {subset['area_oficial_km2'].mean():.2f} km²")
    
    # Análisis por región
    print("\n🗺️  Análisis por región:")
    regiones = ['CENTRO', 'NEVADOS', 'SUR', 'SUR ORIENTE', 'NORTE', 'ORIENTE']
    
    for region in regiones:
        municipios_region = gdf[(gdf['tipo'] == 'municipio') & (gdf['region'] == region)]
        veredas_region = gdf[(gdf['tipo'] == 'vereda') & (gdf['region'] == region)]
        
        area_total = veredas_region['area_oficial_km2'].sum()
        print(f"\n   📍 {region}:")
        print(f"      • Municipios: {len(municipios_region)}")
        print(f"      • Veredas: {len(veredas_region)}")
        print(f"      • Área total: {area_total:,.2f} km²")
        
        # Top 3 municipios por número de veredas en esta región
        if len(veredas_region) > 0:
            veredas_por_municipio = veredas_region['municipio'].value_counts().head(3)
            print(f"      • Top municipios:")
            for municipio, count in veredas_por_municipio.items():
                print(f"        - {municipio}: {count} veredas")
    
    # Información sobre datos geométricos disponibles
    print("\n📐 Datos geométricos conservados:")
    veredas_subset = gdf[gdf['tipo'] == 'vereda']
    if len(veredas_subset) > 0:
        print(f"   📏 Rangos de medidas:")
        print(f"      • Área más grande: {veredas_subset['area_oficial_km2'].max():.2f} km² ({veredas_subset.loc[veredas_subset['area_oficial_km2'].idxmax(), 'nombre']})")
        print(f"      • Área más pequeña: {veredas_subset['area_oficial_km2'].min():.2f} km² ({veredas_subset.loc[veredas_subset['area_oficial_km2'].idxmin(), 'nombre']})")
        print(f"      • Perímetro más largo: {veredas_subset['perimetro_km'].max():.2f} km ({veredas_subset.loc[veredas_subset['perimetro_km'].idxmax(), 'nombre']})")
        print(f"      • Área promedio: {veredas_subset['area_oficial_km2'].mean():.2f} km²")
        print(f"      • Perímetro promedio: {veredas_subset['perimetro_km'].mean():.2f} km")
        
        print("\n   🧮 Índices calculables on-demand:")
        print("      • Compacidad: 4π * área / perímetro²")
        print("      • Complejidad: perímetro / √área") 
        print("      • Relación área oficial/geométrica")
        print("      • Densidad casos por área real vs oficial")


def validar_estructura_sql_regiones(gdf):
    """Valida que la estructura con regiones sea compatible con PostgreSQL"""
    print("\n🔧 VALIDACIÓN PARA POSTGRESQL (CON REGIONES)")
    print("=" * 50)
    
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
    
    # Verificar integridad de regiones
    print("\n🗺️  Verificación de regiones:")
    regiones_esperadas = {'CENTRO', 'NEVADOS', 'SUR', 'SUR ORIENTE', 'NORTE', 'ORIENTE', 'TODAS'}
    regiones_encontradas = set(gdf['region'].dropna().unique())
    
    if regiones_esperadas == regiones_encontradas:
        print("   ✅ Todas las regiones esperadas están presentes")
    else:
        print("   ⚠️  Diferencias en regiones:")
        print(f"      Esperadas: {regiones_esperadas}")
        print(f"      Encontradas: {regiones_encontradas}")
    
    # Sugerir DDL para PostgreSQL
    print("\n💾 DDL sugerido para PostgreSQL (con regiones y datos geométricos):")
    print("""
    CREATE TABLE unidades_territoriales_tolima (
        id SERIAL PRIMARY KEY,
        tipo VARCHAR(20) CHECK (tipo IN ('departamento', 'municipio', 'vereda')),
        codigo_divipola VARCHAR(15) NOT NULL,
        codigo_dpto VARCHAR(2) NOT NULL,
        codigo_municipio VARCHAR(5),
        nombre VARCHAR(200) NOT NULL,
        municipio VARCHAR(100),
        region VARCHAR(20) CHECK (region IN ('CENTRO', 'NEVADOS', 'SUR', 'SUR ORIENTE', 'NORTE', 'ORIENTE', 'TODAS')),
        
        -- Información de áreas y geometría (datos base)
        area_oficial_km2 DECIMAL(12,6),           -- Área catastral/legal
        area_geometrica_km2 DECIMAL(12,6),        -- Área calculada del polígono
        perimetro_km DECIMAL(12,6),               -- Perímetro en kilómetros
        
        geometry GEOMETRY(POLYGON, 4326),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT uk_tipo_codigo UNIQUE (tipo, codigo_divipola)
    );
    
    -- Índices recomendados
    CREATE INDEX idx_unidades_tipo ON unidades_territoriales_tolima(tipo);
    CREATE INDEX idx_unidades_region ON unidades_territoriales_tolima(region);
    CREATE INDEX idx_unidades_municipio ON unidades_territoriales_tolima(codigo_municipio);
    CREATE INDEX idx_unidades_spatial ON unidades_territoriales_tolima USING GIST(geometry);
    CREATE INDEX idx_unidades_area ON unidades_territoriales_tolima(area_oficial_km2);
    
    -- Vistas con índices calculados on-demand (cuando sea necesario)
    CREATE VIEW v_unidades_por_region AS
    SELECT region, tipo, COUNT(*) as cantidad, 
           SUM(area_oficial_km2) as area_total_km2,
           AVG(area_oficial_km2) as area_promedio_km2
    FROM unidades_territoriales_tolima 
    WHERE region != 'TODAS'
    GROUP BY region, tipo
    ORDER BY region, tipo;
    
    -- Vista con índices geométricos (solo cuando sea necesario para análisis)
    CREATE VIEW v_veredas_analisis_geometrico AS
    SELECT nombre, municipio, region, 
           area_oficial_km2, area_geometrica_km2, perimetro_km,
           -- Índices calculados on-demand
           (4 * PI() * area_geometrica_km2) / POWER(perimetro_km, 2) as indice_compacidad,
           perimetro_km / SQRT(area_geometrica_km2) as relacion_perimetro_area,
           ABS(area_oficial_km2 - area_geometrica_km2) / area_oficial_km2 * 100 as diferencia_areas_pct,
           CASE 
               WHEN (4 * PI() * area_geometrica_km2) / POWER(perimetro_km, 2) > 0.7 THEN 'COMPACTA'
               WHEN (4 * PI() * area_geometrica_km2) / POWER(perimetro_km, 2) > 0.4 THEN 'MEDIA'
               ELSE 'ALARGADA'
           END as tipo_forma
    FROM unidades_territoriales_tolima 
    WHERE tipo = 'vereda' AND area_geometrica_km2 > 0 AND perimetro_km > 0;
    
    -- Importar datos:
    -- opción 1: ogr2ogr -f PostgreSQL PG:"host=localhost dbname=tu_db" tolima_completo_con_regiones.gpkg
    -- opción 2: shp2pgsql -I -s 4326 tolima_completo_con_regiones.shp unidades_territoriales_tolima | psql -d tu_db
    -- opción 3: Python con geopandas: gdf.to_postgis('unidades_territoriales_tolima', engine)
    """)

if __name__ == "__main__":
    # Configuración - RUTAS AJUSTADAS
    RUTA_VEREDAS = "data\\shapefiles\\CRVeredas_2020.shp"
    RUTA_MUNICIPIOS = "data\\shapefiles\\Municipio, Distrito y Area no municipalizada.shp"
    RUTA_SALIDA = "data\\processed\\tolima_completo_con_regiones"
    
    try:
        # Verificar archivos
        for archivo in [RUTA_VEREDAS, RUTA_MUNICIPIOS]:
            if not Path(archivo).exists():
                raise FileNotFoundError(f"No se encontró: {archivo}")
        
        # Crear archivo unificado completo con regiones
        print("🚀 Iniciando proceso de unificación completa con regiones...")
        print(f"📍 Regiones configuradas: {len(set(MUNICIPIO_REGION.values()))} regiones")
        print(f"🏘️  Municipios configurados: {len(MUNICIPIO_REGION)} municipios")
        
        unidades = crear_unidades_tolima_completo(RUTA_VEREDAS, RUTA_MUNICIPIOS, RUTA_SALIDA)
        
        # Mostrar resúmenes
        mostrar_resumen_completo(unidades)
        validar_estructura_sql_regiones(unidades)
        
        print("\n🎉 ¡Proceso completado exitosamente!")
        print(f"📁 Archivos generados con prefijo: {RUTA_SALIDA}")
        print("\n📋 Archivos listos para:")
        print("   🌐 Mapas web con filtros por región: .geojson")
        print("   📦 Uso moderno y eficiente: .gpkg (GeoPackage)")
        print("   🗺️  Compatibilidad GIS tradicional: .shp") 
        print("   🐘 PostgreSQL con regiones: .parquet o .geojson")
        print("   🔄 Intercambio de datos: .gpkg (estándar OGC)")
        
        print("\n⭐ RECOMENDACIÓN: Usar .gpkg para la mayoría de usos")
        print("   • Un solo archivo (vs múltiples .shp/.dbf/.shx)")
        print("   • Mejor manejo de caracteres Unicode")
        print("   • Más eficiente que shapefile")
        print("   • Compatible con QGIS, ArcGIS, PostGIS")
        
        print("\n🎓 DISEÑO: Datos básicos conservados, índices calculados on-demand")
        print("   • Principio YAGNI: Solo almacenar lo que necesitas ahora")
        print("   • Base de datos más limpia y manejable")
        print("   • Cálculos epidemiológicos cuando sea necesario (SQL views)")
        print("   • Flexibilidad para diferentes fórmulas futuras")
        print("\n🗂️  Funcionalidades incluidas:")
        print("   📍 3 niveles territoriales (departamento, municipio, vereda)")
        print("   🏷️  6 regiones del Tolima (CENTRO, NEVADOS, SUR, etc.)")
        print("   🔗 Códigos DIVIPOLA estándar")
        print("   📝 Nombres estandarizados a Title Case (municipios y veredas)")
        print("   📐 Datos geométricos básicos conservados (áreas, perímetros)")
        print("   🧮 Índices calculables on-demand según necesidades futuras")
        print("   🎯 Estructura optimizada para filtros web y análisis epidemiológico")
        print("\n📊 Ejemplo de consultas SQL facilitadas:")
        print("   SELECT * FROM unidades WHERE municipio = 'Ibagué';  -- Consistente en todos los niveles")
        print("   SELECT * FROM unidades WHERE nombre = 'Alto de Gualanday';  -- Veredas legibles")
        print("   SELECT region, COUNT(*) FROM unidades WHERE tipo = 'vereda' GROUP BY region;")
        print("\n🔬 Análisis epidemiológico habilitado (on-demand):")
        print("   • Densidad de casos por área real vs oficial")
        print("   • Cálculo de compacidad: 4π * área / perímetro²")
        print("   • Análisis de complejidad: perímetro / √área")
        print("   • Planificación basada en forma territorial (usar vistas SQL)")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("💡 Verifica las rutas de los shapefiles:")
        print(f"   • Veredas: {RUTA_VEREDAS}")
        print(f"   • Municipios: {RUTA_MUNICIPIOS}")
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print("💡 Verifica que todos los paquetes estén instalados:")
        print("   pip install geopandas pandas pyarrow")