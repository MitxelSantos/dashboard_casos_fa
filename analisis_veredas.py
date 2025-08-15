# -*- coding: utf-8 -*-
"""
Análisis de Veredas del Tolima - Categorización Urbano/Rural
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime

def normalizar_texto(texto):
    """Normaliza texto para matching"""
    if pd.isna(texto) or texto == '':
        return ''
    
    texto = str(texto).upper().strip()
    
    # Reemplazos de acentos
    replacements = {
        'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A', 'Ã': 'A',
        'É': 'E', 'È': 'E', 'Ë': 'E', 'Ê': 'E',
        'Í': 'I', 'Ì': 'I', 'Ï': 'I', 'Î': 'I',
        'Ó': 'O', 'Ò': 'O', 'Ö': 'O', 'Ô': 'O', 'Õ': 'O',
        'Ú': 'U', 'Ù': 'U', 'Ü': 'U', 'Û': 'U',
        'Ñ': 'N', 'Ç': 'C'
    }
    
    for old, new in replacements.items():
        texto = texto.replace(old, new)
    
    # Solo letras y números
    texto = re.sub(r'[^A-Z0-9]', '', texto)
    return texto.strip()

def categorizar_vereda(nombre_vereda):
    """Categoriza vereda como urbana o rural"""
    if pd.isna(nombre_vereda) or nombre_vereda == '':
        return 'DESCONOCIDO', 'Nombre vacío'
    
    nombre = str(nombre_vereda).upper().strip()
    
    # Patrones urbanos claros
    if any(patron in nombre for patron in [
        'SIN VEREDA', 'CABECERA', 'CENTRO', 'URBANO', 'ZONA URBANA', 
        'CASCO', 'MUNICIPIO', 'CIUDAD'
    ]):
        return 'CASCO_URBANO', f'Patrón urbano en: {nombre}'
    
    # Patrones probablemente urbanos
    if any(patron in nombre for patron in [
        'BARRIO', 'SECTOR', 'VILLA', 'RESIDENCIAL', 'COMUNA'
    ]):
        return 'PROBABLEMENTE_URBANO', f'Patrón urbano en: {nombre}'
    
    # Casos especiales
    if nombre in ['VEREDA', 'VEREDAS']:
        return 'CASCO_URBANO', 'Nombre genérico'
    
    if len(nombre.replace(' ', '')) < 4:
        return 'PROBABLEMENTE_URBANO', f'Nombre muy corto: {nombre}'
    
    if re.match(r'^[0-9\s]+$', nombre):
        return 'PROBABLEMENTE_URBANO', 'Solo números'
    
    return 'REVISION_MANUAL', 'Requiere revisión manual'

def procesar_archivo_veredas(archivo_excel='process.xlsx'):
    """
    Función principal que procesa el archivo y genera todos los resultados
    """
    
    print("🚀 INICIANDO ANÁLISIS DE VEREDAS DEL TOLIMA")
    print("=" * 60)
    
    # 1. CARGAR DATOS
    print("📂 Cargando datos...")
    try:
        datos_poblacion = pd.read_excel(archivo_excel, sheet_name='Hoja1')
        datos_referencia = pd.read_excel(archivo_excel, sheet_name='Hoja2')
        print(f"✅ Datos poblacionales: {len(datos_poblacion):,} registros")
        print(f"✅ Datos de referencia: {len(datos_referencia):,} registros")
    except Exception as e:
        print(f"❌ Error al cargar archivo: {e}")
        return False
    
    # 2. CREAR ÍNDICE DE VEREDAS RURALES (SHAPEFILES)
    print("📍 Creando índice de veredas rurales...")
    datos_referencia['clave_match'] = (
        datos_referencia['municipi_1'].apply(normalizar_texto) + '_' + 
        datos_referencia['vereda_nor'].apply(normalizar_texto)
    )
    
    indice_rurales = {}
    for _, row in datos_referencia.iterrows():
        indice_rurales[row['clave_match']] = {
            'codigo_vereda': row['CODIGO_VER'],
            'municipio_ref': row['municipi_1'],
            'vereda_ref': row['vereda_nor'],
            'region': row['region']
        }
    
    print(f"✅ Índice creado con {len(indice_rurales):,} veredas rurales")
    
    # 3. PROCESAR CADA REGISTRO POBLACIONAL
    print("🔄 Procesando y categorizando registros...")
    
    resultados = []
    contadores = {'VEREDA_RURAL': 0, 'CASCO_URBANO': 0, 'PROBABLEMENTE_URBANO': 0, 'REVISION_MANUAL': 0}
    
    for idx, row in datos_poblacion.iterrows():
        # Crear clave para matching
        clave = f"{normalizar_texto(row['municipio'])}_{normalizar_texto(row['vereda'])}"
        
        # Buscar en veredas rurales
        ref_rural = indice_rurales.get(clave)
        
        # Categorizar
        if ref_rural:
            categoria = 'VEREDA_RURAL'
            razon = 'Encontrada en shapefile rural'
        else:
            categoria, razon = categorizar_vereda(row['vereda'])
        
        contadores[categoria] += 1
        
        # Crear registro completo
        registro = {
            # Datos originales
            'municipio': row['municipio'],
            'vereda': row['vereda'],
            'menor_9_meses': row.get('Menor de 9 meses', 0),
            'meses_9_23': row.get('09-23 meses', 0),
            'anos_2_19': row.get('02-19 años', 0),
            'anos_20_59': row.get('20-59 años', 0),
            'anos_60_mas': row.get('60+ años', 0),
            'total_poblacion': row.get('Total', 0),
            
            # Referencia rural (si existe)
            'codigo_vereda': ref_rural['codigo_vereda'] if ref_rural else None,
            'municipio_referencia': ref_rural['municipio_ref'] if ref_rural else None,
            'vereda_referencia': ref_rural['vereda_ref'] if ref_rural else None,
            'region': ref_rural['region'] if ref_rural else None,
            
            # Categorización
            'categoria': categoria,
            'razon_categoria': razon,
            'requiere_revision': 'SÍ' if categoria == 'REVISION_MANUAL' else 'NO',
            'clave_matching': clave
        }
        
        resultados.append(registro)
        
        # Progreso cada 500 registros
        if (idx + 1) % 500 == 0:
            print(f"   Procesados: {idx + 1:,} registros...")
    
    # Crear DataFrame final
    df_final = pd.DataFrame(resultados)
    
    print(f"✅ Procesamiento completado: {len(df_final):,} registros")
    
    # 4. GENERAR ESTADÍSTICAS
    print("📊 Generando estadísticas...")
    
    total_poblacion = df_final['total_poblacion'].sum()
    
    print(f"\n📈 RESULTADOS POR CATEGORÍA:")
    for categoria in ['VEREDA_RURAL', 'CASCO_URBANO', 'PROBABLEMENTE_URBANO', 'REVISION_MANUAL']:
        subset = df_final[df_final['categoria'] == categoria]
        num_registros = len(subset)
        poblacion = subset['total_poblacion'].sum()
        
        if num_registros > 0:
            print(f"   {categoria}:")
            print(f"     - {num_registros:,} registros ({num_registros/len(df_final)*100:.1f}%)")
            print(f"     - {poblacion:,} habitantes ({poblacion/total_poblacion*100:.1f}%)")
    
    # 5. EXPORTAR RESULTADOS
    print(f"\n📁 Exportando resultados...")
    
    carpeta = f"analisis_veredas_tolima_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    Path(carpeta).mkdir(exist_ok=True)
    
    # Archivo principal
    with pd.ExcelWriter(f'{carpeta}/DATASET_COMPLETO.xlsx', engine='openpyxl') as writer:
        df_final.to_excel(writer, sheet_name='Dataset_Completo', index=False)
        
        # Estadísticas
        stats = df_final.groupby('categoria').agg({
            'total_poblacion': ['count', 'sum'],
            'municipio': 'nunique'
        })
        stats.to_excel(writer, sheet_name='Estadisticas')
    
    # TODOS los casos de revisión manual
    casos_revision = df_final[df_final['categoria'] == 'REVISION_MANUAL']
    
    if len(casos_revision) > 0:
        with pd.ExcelWriter(f'{carpeta}/TODOS_CASOS_REVISION_MANUAL.xlsx', engine='openpyxl') as writer:
            # Todos los casos
            casos_revision.sort_values('total_poblacion', ascending=False).to_excel(
                writer, sheet_name='Todos_Casos', index=False
            )
            
            # Por municipio
            for municipio in casos_revision['municipio'].unique():
                casos_mun = casos_revision[casos_revision['municipio'] == municipio]
                casos_mun = casos_mun.sort_values('total_poblacion', ascending=False)
                
                nombre_hoja = municipio.replace(' ', '_').replace('/', '_')[:31]
                casos_mun.to_excel(writer, sheet_name=nombre_hoja, index=False)
    
    # Casos urbanos
    casos_urbanos = df_final[df_final['categoria'].isin(['CASCO_URBANO', 'PROBABLEMENTE_URBANO'])]
    
    if len(casos_urbanos) > 0:
        casos_urbanos.to_excel(f'{carpeta}/CASOS_URBANOS.xlsx', index=False)
    
    # Veredas rurales confirmadas
    veredas_rurales = df_final[df_final['categoria'] == 'VEREDA_RURAL']
    veredas_rurales.to_excel(f'{carpeta}/VEREDAS_RURALES_CONFIRMADAS.xlsx', index=False)
    
    # CSVs para análisis externo
    df_final.to_csv(f'{carpeta}/dataset_completo.csv', index=False, encoding='utf-8-sig')
    casos_revision.to_csv(f'{carpeta}/casos_revision_manual.csv', index=False, encoding='utf-8-sig')
    
    print(f"✅ Archivos exportados en carpeta: {carpeta}")
    print(f"\n📋 ARCHIVOS GENERADOS:")
    print(f"   📊 DATASET_COMPLETO.xlsx - Base de datos completa")
    print(f"   🔍 TODOS_CASOS_REVISION_MANUAL.xlsx - TODOS los casos para revisar")
    print(f"   🏙️ CASOS_URBANOS.xlsx - Casos detectados como urbanos")
    print(f"   🌾 VEREDAS_RURALES_CONFIRMADAS.xlsx - Veredas con referencia rural")
    print(f"   📄 Archivos CSV adicionales")
    
    # Resumen final
    revision_count = len(casos_revision)
    revision_poblacion = casos_revision['total_poblacion'].sum()
    
    print(f"\n⚠️ CASOS QUE REQUIEREN REVISIÓN MANUAL:")
    print(f"   Total: {revision_count:,} registros")
    print(f"   Población: {revision_poblacion:,} habitantes")
    
    if revision_count > 0:
        print(f"\n🔍 TOP 10 MUNICIPIOS CON MÁS CASOS DE REVISIÓN:")
        top_revision = casos_revision.groupby('municipio')['total_poblacion'].agg(['count', 'sum']).sort_values('sum', ascending=False).head(10)
        
        for municipio, data in top_revision.iterrows():
            print(f"   {municipio}: {int(data['count'])} casos, {int(data['sum']):,} habitantes")
    
    print(f"\n✅ ANÁLISIS COMPLETADO")
    print(f"📁 Revisa la carpeta '{carpeta}' para todos los resultados")
    
    return True

# EJECUTAR EL ANÁLISIS
if __name__ == "__main__":
    try:
        # Verificar si existe el archivo
        if not Path('process.xlsx').exists():
            print("❌ Error: No se encuentra el archivo 'process.xlsx'")
            print("   Asegúrate de que el archivo esté en el mismo directorio que este script")
        else:
            procesar_archivo_veredas('process.xlsx')
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print("   Verifica que tengas instalados pandas y openpyxl:")
        print("   pip install pandas openpyxl")