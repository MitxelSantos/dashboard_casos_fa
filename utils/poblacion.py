#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Conteo Poblacional por Municipios del Tolima
Descripción: Script para generar conteo poblacional agregado por municipio,
             distinguiendo grupos etarios y ubicación urbana/rural

CRITERIOS DE EXCLUSIÓN DE REGISTROS:
1. Fecha nacimiento nula o inválida
2. Fecha nacimiento posterior a fecha actual
3. Edad calculada menor a 0 años (nacimientos problemáticos)
4. Edad calculada mayor a 90 años
5. Registros duplicados por documento (conservar más reciente por fecha nacimiento)

CRITERIOS DE INCLUSIÓN EN CSV FINAL:
- Solo población que pertenece a los grupos etarios definidos en clasificar_grupo_etario()
- Población fuera de grupos etarios (ej: < 9 meses) se muestra en consola pero NO va al CSV
- Población sin datos de edad se muestra en consola pero NO va al CSV

CRITERIOS DE CLASIFICACIÓN URBANO/RURAL:
- RURAL:
  1. Si vereda ≠ "SIN VEREDA" → Rural (la vereda manda)
  2. Si vereda = "SIN VEREDA" pero corregimiento ≠ "SIN CORREGIMIENTO" y ≠ "CABECERA MUNICIPAL" → Rural
- URBANO:
  1. Si vereda = "SIN VEREDA" y corregimiento = "CABECERA MUNICIPAL" → Urbano
  2. Si vereda = "SIN VEREDA" y corregimiento = "SIN CORREGIMIENTO" y barrio ≠ "SIN BARRIO" → Urbano
  3. Si vereda = "SIN VEREDA" y corregimiento = "SIN CORREGIMIENTO" y barrio = "SIN BARRIO" → Urbano

FLEXIBILIDAD:
- Modificar grupos etarios en función clasificar_grupo_etario() adapta automáticamente toda la lógica
- Sistema auto-detecta qué población está dentro/fuera de los grupos definidos

Autor: Sistema de Análisis Demográfico
"""

# ============================================
# IMPORTACIÓN DE LIBRERÍAS
# ============================================
import pandas as pd
import numpy as np
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import warnings
import os
import sys

warnings.filterwarnings('ignore')

# Configurar pandas
pd.options.mode.chained_assignment = None
pd.set_option('display.max_columns', None)

# ============================================
# CONFIGURACIÓN DE COLUMNAS
# ============================================
# Mapeo de columnas del CSV (sin encabezados)
MAPEO_COLUMNAS = {
    'col_1': 'codigo_municipio',
    'col_2': 'municipio', 
    'col_6': 'corregimiento',
    'col_8': 'vereda',
    'col_10': 'barrio',
    'col_11': 'direccion',
    'col_17': 'documento',
    'col_18': 'fecha_nacimiento'
}

# Orden estándar de grupos etarios
ORDEN_GRUPOS_ETARIOS = ['Menor de 9 meses', '09-23 meses', '02-19 años', '20-59 años', '60+ años', 'Sin datos']

# ============================================
# FUNCIONES DE PROCESAMIENTO
# ============================================

def cargar_datos(archivo_csv):
    """Carga el CSV sin encabezados, mapea columnas y valida estructura"""
    print(f"\n{'='*60}")
    print("CARGANDO DATOS POBLACIONALES")
    print('='*60)
    
    try:
        # Cargar CSV sin encabezados
        df = pd.read_csv(archivo_csv, header=None)
        print(f"✅ CSV cargado exitosamente: {len(df):,} registros")
        print(f"📊 Número de columnas: {len(df.columns)}")
        
        # Asignar nombres genéricos a las columnas
        df.columns = [f"col_{i}" for i in range(df.shape[1])]
        
        # Renombrar columnas relevantes
        df = df.rename(columns=MAPEO_COLUMNAS)
        
        # Verificación de columnas mapeadas
        if len(df) > 0:
            print("\n--- VERIFICACIÓN DE COLUMNAS MAPEADAS ---")
            print(f"codigo_municipio: {df['codigo_municipio'].iloc[0]}")
            print(f"municipio: {df['municipio'].iloc[0]}")
            print(f"corregimiento: {df['corregimiento'].iloc[0]}")
            print(f"vereda: {df['vereda'].iloc[0]}")
            print(f"barrio: {df['barrio'].iloc[0]}")
            print(f"fecha_nacimiento: {df['fecha_nacimiento'].iloc[0]}")
            print(f"documento: {df['documento'].iloc[0]}")
        
        return df
        
    except FileNotFoundError:
        print(f"❌ ERROR: No se encontró el archivo '{archivo_csv}'")
        print("Verifica que el archivo esté en el mismo directorio que este script")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR al cargar el archivo: {e}")
        sys.exit(1)

def normalizar_texto(texto):
    """Normaliza texto a Title Case"""
    if pd.isna(texto) or texto == '':
        return None
    return str(texto).strip().title()

def validar_fecha_nacimiento(df):
    """Convierte y valida únicamente la fecha de nacimiento"""
    print(f"\n{'='*60}")
    print("VALIDANDO FECHAS DE NACIMIENTO")
    print('='*60)
    
    # Convertir fecha de nacimiento
    df['fecha_nacimiento'] = pd.to_datetime(df['fecha_nacimiento'], 
                                           format='%Y-%m-%d', 
                                           errors='coerce')
    
    # Verificar fechas nulas
    fechas_nacimiento_nulas = df['fecha_nacimiento'].isna().sum()
    print(f"📅 Fechas de nacimiento nulas/inválidas: {fechas_nacimiento_nulas:,}")
    
    # Eliminar registros con fechas nulas
    df_limpio = df.dropna(subset=['fecha_nacimiento'])
    print(f"✅ Registros con fecha de nacimiento válida: {len(df_limpio):,}")
    
    # Validación de fechas futuras
    fecha_actual = pd.Timestamp.now()
    fechas_futuras = df_limpio[df_limpio['fecha_nacimiento'] > fecha_actual]
    if len(fechas_futuras) > 0:
        print(f"\n⚠️ EXCLUIDO: {len(fechas_futuras)} registros con fecha de nacimiento futura")
        df_limpio = df_limpio[df_limpio['fecha_nacimiento'] <= fecha_actual]
        print(f"Registros válidos después de filtrar fechas futuras: {len(df_limpio):,}")
    
    return df_limpio

def calcular_edad_detallada(fecha_nacimiento, fecha_referencia):
    """Calcula la edad en años y meses totales"""
    if pd.isna(fecha_nacimiento) or pd.isna(fecha_referencia):
        return None, None
    
    if fecha_nacimiento > fecha_referencia:
        return None, None
    
    diferencia = relativedelta(fecha_referencia, fecha_nacimiento)
    edad_anos = diferencia.years
    edad_meses_total = diferencia.years * 12 + diferencia.months
    
    return edad_anos, edad_meses_total

def calcular_edades_y_validar(df_limpio):
    """Calcula las edades y aplica criterios de exclusión por edad"""
    print(f"\n{'='*60}")
    print("CALCULANDO EDADES Y APLICANDO CRITERIOS DE EXCLUSIÓN")
    print('='*60)
    
    fecha_actual = pd.Timestamp.now()
    print(f"📅 Fecha de referencia para cálculo de edad: {fecha_actual.strftime('%Y-%m-%d')}")
    
    # Calcular edades usando fecha actual
    edades = df_limpio.apply(lambda row: calcular_edad_detallada(
        row['fecha_nacimiento'], 
        fecha_actual
    ), axis=1)
    
    df_limpio['edad_anos'] = edades.apply(lambda x: x[0] if x else None)
    df_limpio['edad_meses'] = edades.apply(lambda x: x[1] if x else None)
    
    # Estadísticas antes de filtros
    registros_antes_filtros = len(df_limpio)
    print(f"\n📊 REGISTROS ANTES DE FILTROS DE EDAD: {registros_antes_filtros:,}")
    
    # CRITERIO DE EXCLUSIÓN 3: Edades negativas (nacimientos problemáticos)
    edades_negativas = df_limpio[df_limpio['edad_anos'] < 0]
    if len(edades_negativas) > 0:
        print(f"\n❌ EXCLUIDO: {len(edades_negativas)} registros con edad negativa (nacimientos problemáticos)")
        df_limpio = df_limpio[df_limpio['edad_anos'] >= 0]
    
    # CRITERIO DE EXCLUSIÓN 4: Mayores de 90 años
    mayores_90 = df_limpio[df_limpio['edad_anos'] > 90]
    if len(mayores_90) > 0:
        print(f"❌ EXCLUIDO: {len(mayores_90)} registros con edad mayor a 90 años")
        df_limpio = df_limpio[df_limpio['edad_anos'] <= 90]
    
    # Estadísticas finales
    registros_despues_filtros = len(df_limpio)
    excluidos_por_edad = registros_antes_filtros - registros_despues_filtros
    
    print(f"\n📊 ESTADÍSTICAS DE EDAD:")
    print(f"  Registros excluidos por criterios de edad: {excluidos_por_edad:,}")
    print(f"  Registros válidos finales: {registros_despues_filtros:,}")
    print(f"  Edad mínima: {df_limpio['edad_anos'].min():.1f} años")
    print(f"  Edad máxima: {df_limpio['edad_anos'].max():.1f} años")
    print(f"  Edad promedio: {df_limpio['edad_anos'].mean():.1f} años")
    
    return df_limpio

# ============================================
# CONFIGURACIÓN DE GRUPOS ETARIOS
# ============================================
def clasificar_grupo_etario(edad_meses):
    """
    Clasifica según los grupos etarios especificados
    
    NOTA: Esta función es la fuente única de verdad para los grupos etarios.
    Modificar aquí automáticamente adapta toda la lógica del código.
    
    Returns:
        str: Nombre del grupo etario o None si está fuera de los grupos definidos
    """
    if pd.isna(edad_meses):
        return 'Sin datos'
    
    # GRUPOS ETARIOS DEFINIDOS (modificar aquí para cambiar toda la lógica)
    if edad_meses >= 9 and edad_meses <= 23:
        return '09-23 meses'
    elif edad_meses >= 24 and edad_meses < 240:  # 2 a 19 años
        return '02-19 años'
    elif edad_meses >= 240 and edad_meses < 720:  # 20 a 59 años
        return '20-59 años'
    elif edad_meses >= 720:  # 60+ años
        return '60+ años'
    else:
        # Población fuera de los grupos etarios definidos (ej: < 9 meses)
        return None

def obtener_grupos_etarios_definidos():
    """
    Obtiene la lista de grupos etarios que están definidos en la función clasificar_grupo_etario
    Esta función se auto-adapta cuando se modifican los grupos etarios
    """
    # Probar con diferentes valores para extraer todos los grupos posibles
    valores_prueba = list(range(0, 1200, 1))  # 0 a 100 años en meses
    grupos_encontrados = set()
    
    for meses in valores_prueba:
        grupo = clasificar_grupo_etario(meses)
        if grupo is not None and grupo != 'Sin datos':
            grupos_encontrados.add(grupo)
    
    # Orden lógico de grupos (modificar si es necesario)
    orden_preferido = ['09-23 meses', '02-19 años', '20-59 años', '60+ años', 'Sin datos']
    grupos_ordenados = [g for g in orden_preferido if g in grupos_encontrados]
    
    return grupos_ordenados

# Generar automáticamente la lista de grupos etarios
ORDEN_GRUPOS_ETARIOS = obtener_grupos_etarios_definidos()

def determinar_ubicacion(vereda, corregimiento, barrio):
    """
    Determina si es urbano o rural basado en las reglas establecidas
    
    Args:
        vereda (str): Valor de la columna vereda
        corregimiento (str): Valor de la columna corregimiento  
        barrio (str): Valor de la columna barrio
    
    Returns:
        str: 'Rural' o 'Urbano'
    """
    # Normalizar valores (convertir a string y limpiar)
    vereda = str(vereda).strip().upper() if pd.notna(vereda) else "SIN VEREDA"
    corregimiento = str(corregimiento).strip().upper() if pd.notna(corregimiento) else "SIN CORREGIMIENTO"
    barrio = str(barrio).strip().upper() if pd.notna(barrio) else "SIN BARRIO"
    
    # REGLAS RURALES
    # 1. Si vereda ≠ "SIN VEREDA" → Rural (la vereda manda)
    if vereda != "SIN VEREDA":
        return 'Rural'
    
    # 2. Si vereda = "SIN VEREDA" pero corregimiento ≠ "SIN CORREGIMIENTO" y ≠ "CABECERA MUNICIPAL" → Rural
    if vereda == "SIN VEREDA" and corregimiento not in ["SIN CORREGIMIENTO", "CABECERA MUNICIPAL"]:
        return 'Rural'
    
    # REGLAS URBANAS
    # 1. Si vereda = "SIN VEREDA" y corregimiento = "CABECERA MUNICIPAL" → Urbano
    if vereda == "SIN VEREDA" and corregimiento == "CABECERA MUNICIPAL":
        return 'Urbano'
    
    # 2. Si vereda = "SIN VEREDA" y corregimiento = "SIN CORREGIMIENTO" y barrio ≠ "SIN BARRIO" → Urbano
    if vereda == "SIN VEREDA" and corregimiento == "SIN CORREGIMIENTO" and barrio != "SIN BARRIO":
        return 'Urbano'
    
    # 3. Si vereda = "SIN VEREDA", corregimiento = "SIN CORREGIMIENTO" y barrio = "SIN BARRIO" → Urbano
    if vereda == "SIN VEREDA" and corregimiento == "SIN CORREGIMIENTO" and barrio == "SIN BARRIO":
        return 'Urbano'
    
    # Por defecto (caso no contemplado) → Urbano
    return 'Urbano'

def procesar_y_clasificar(df_limpio):
    """Procesa los datos y los clasifica"""
    print(f"\n{'='*60}")
    print("PROCESANDO Y CLASIFICANDO REGISTROS")
    print('='*60)
    
    # Normalizar nombres de municipios
    df_limpio['municipio'] = df_limpio['municipio'].apply(normalizar_texto)
    
    # Clasificar grupos etarios usando la función flexible
    df_limpio['grupo_etario'] = df_limpio['edad_meses'].apply(clasificar_grupo_etario)
    
    # Identificar población fuera de grupos etarios definidos
    df_limpio['fuera_grupos_etarios'] = df_limpio['grupo_etario'].isna()
    
    # Para los que están fuera de grupos etarios, crear etiqueta descriptiva para estadísticas
    def crear_etiqueta_fuera_grupos(edad_meses):
        if pd.isna(edad_meses):
            return 'Sin datos de edad'
        if edad_meses < 9:
            return 'Menores de 9 meses'
        # Si en el futuro se agregan otros rangos fuera de grupos, agregar aquí
        return 'Fuera de grupos etarios'
    
    df_limpio['etiqueta_fuera_grupos'] = df_limpio.apply(
        lambda row: crear_etiqueta_fuera_grupos(row['edad_meses']) if row['fuera_grupos_etarios'] else None, 
        axis=1
    )
    
    # Determinar ubicación urbana/rural usando las reglas establecidas
    df_limpio['tipo_ubicacion'] = df_limpio.apply(
        lambda row: determinar_ubicacion(row['vereda'], row['corregimiento'], row['barrio']), 
        axis=1
    )
    
    print(f"✅ Clasificación completada")
    print(f"📍 Municipios únicos: {df_limpio['municipio'].nunique()}")
    print(f"🏢 Códigos de municipio únicos: {df_limpio['codigo_municipio'].nunique()}")
    
    # Mostrar distribución urbano/rural
    distribucion_ubicacion = df_limpio['tipo_ubicacion'].value_counts()
    print(f"\n🏙️ DISTRIBUCIÓN URBANO/RURAL:")
    for ubicacion, cantidad in distribucion_ubicacion.items():
        porcentaje = (cantidad / len(df_limpio)) * 100
        print(f"  {ubicacion}: {cantidad:,} ({porcentaje:.1f}%)")
    
    # Mostrar estadísticas completas de clasificación
    total_registros = len(df_limpio)
    
    # Población en grupos etarios definidos
    en_grupos_definidos = df_limpio[~df_limpio['fuera_grupos_etarios'] & (df_limpio['grupo_etario'] != 'Sin datos')]
    
    # Población fuera de grupos etarios
    fuera_grupos = df_limpio[df_limpio['fuera_grupos_etarios']]
    
    # Sin datos de edad
    sin_datos = df_limpio[df_limpio['grupo_etario'] == 'Sin datos']
    
    print(f"\n👥 DISTRIBUCIÓN POBLACIONAL:")
    print(f"  📊 Total registros procesados: {total_registros:,}")
    print(f"  ✅ En grupos etarios definidos: {len(en_grupos_definidos):,} ({len(en_grupos_definidos)/total_registros*100:.1f}%)")
    print(f"  ⚠️  Fuera de grupos etarios: {len(fuera_grupos):,} ({len(fuera_grupos)/total_registros*100:.1f}%)")
    print(f"  ❌ Sin datos de edad: {len(sin_datos):,} ({len(sin_datos)/total_registros*100:.1f}%)")
    
    # Detallar población fuera de grupos etarios
    if len(fuera_grupos) > 0:
        print(f"\n📋 DETALLE POBLACIÓN FUERA DE GRUPOS ETARIOS:")
        for etiqueta, cantidad in fuera_grupos['etiqueta_fuera_grupos'].value_counts().items():
            porcentaje = (cantidad / len(fuera_grupos)) * 100
            print(f"  • {etiqueta}: {cantidad:,} ({porcentaje:.1f}% del total fuera de grupos)")
    
    # Mostrar distribución de grupos etarios definidos
    if len(en_grupos_definidos) > 0:
        print(f"\n🎯 DISTRIBUCIÓN POR GRUPOS ETARIOS DEFINIDOS:")
        for grupo in ORDEN_GRUPOS_ETARIOS:
            if grupo != 'Sin datos':
                cantidad = (en_grupos_definidos['grupo_etario'] == grupo).sum()
                if cantidad > 0:
                    porcentaje = (cantidad / len(en_grupos_definidos)) * 100
                    print(f"  • {grupo}: {cantidad:,} ({porcentaje:.1f}%)")
    
    return df_limpio

def eliminar_duplicados(df_limpio):
    """CRITERIO DE EXCLUSIÓN 5: Elimina duplicados por documento, conservando el más reciente por fecha de nacimiento"""
    print(f"\n{'='*60}")
    print("APLICANDO CRITERIO DE EXCLUSIÓN: DUPLICADOS POR DOCUMENTO")
    print('='*60)
    
    registros_iniciales = len(df_limpio)
    
    # Verificar si hay duplicados
    duplicados_detectados = df_limpio.duplicated(subset=['documento'], keep=False)
    num_duplicados_detectados = duplicados_detectados.sum()
    
    if num_duplicados_detectados > 0:
        print(f"🔍 Documentos duplicados detectados: {num_duplicados_detectados:,} registros")
        
        # Mostrar algunos ejemplos de duplicados
        documentos_duplicados = df_limpio[duplicados_detectados]['documento'].unique()[:5]
        print(f"📋 Ejemplos de documentos duplicados: {list(documentos_duplicados)}")
        
        # Ordenar por fecha de nacimiento (más reciente primero) para conservar el registro más nuevo
        df_limpio = df_limpio.sort_values('fecha_nacimiento', ascending=False, na_position='last')
        
        # Eliminar duplicados por documento (mantener el primero = más reciente)
        df_sin_duplicados = df_limpio.drop_duplicates(subset=['documento'], keep='first')
        
        duplicados_removidos = registros_iniciales - len(df_sin_duplicados)
        print(f"❌ EXCLUIDO: {duplicados_removidos:,} registros duplicados")
        print(f"✅ Registros únicos conservados: {len(df_sin_duplicados):,}")
        print(f"ℹ️  Criterio: Se conservó el registro con fecha de nacimiento más reciente por documento")
        
    else:
        print(f"✅ No se detectaron registros duplicados por documento")
        df_sin_duplicados = df_limpio
        print(f"📊 Total registros: {len(df_sin_duplicados):,}")
    
    return df_sin_duplicados

def crear_conteo_poblacional(df_final):
    """Crea el conteo poblacional agregado por municipio SOLO con grupos etarios definidos"""
    print(f"\n{'='*60}")
    print("CREANDO CONTEO POBLACIONAL PARA CSV (SOLO GRUPOS ETARIOS DEFINIDOS)")
    print('='*60)
    
    # Filtrar SOLO los registros que están en grupos etarios definidos
    df_para_csv = df_final[
        (~df_final['fuera_grupos_etarios']) & 
        (df_final['grupo_etario'] != 'Sin datos') &
        (df_final['grupo_etario'].notna())
    ].copy()
    
    print(f"📊 Registros totales procesados: {len(df_final):,}")
    print(f"📋 Registros incluidos en CSV: {len(df_para_csv):,}")
    print(f"⚠️  Registros excluidos del CSV: {len(df_final) - len(df_para_csv):,}")
    
    if len(df_para_csv) == 0:
        print("❌ ERROR: No hay registros en grupos etarios definidos para generar CSV")
        return pd.DataFrame()
    
    # Conteo agregado solo con grupos etarios definidos
    conteo = df_para_csv.groupby([
        'codigo_municipio', 
        'municipio', 
        'tipo_ubicacion', 
        'grupo_etario'
    ]).size().reset_index(name='poblacion_total')
    
    # Ordenar resultados
    conteo = conteo.sort_values([
        'codigo_municipio', 
        'tipo_ubicacion', 
        'grupo_etario'
    ]).reset_index(drop=True)
    
    print(f"✅ Conteo poblacional creado: {len(conteo)} registros agregados")
    
    # Estadísticas de resumen para CSV
    total_poblacion_csv = conteo['poblacion_total'].sum()
    municipios_unicos = conteo['codigo_municipio'].nunique()
    
    print(f"\n📊 ESTADÍSTICAS PARA CSV:")
    print(f"  Total población en CSV: {total_poblacion_csv:,} personas")
    print(f"  Municipios únicos: {municipios_unicos}")
    
    print(f"\n🏙️ DISTRIBUCIÓN URBANO/RURAL EN CSV:")
    dist_ubicacion = conteo.groupby('tipo_ubicacion')['poblacion_total'].sum()
    for ubicacion, cantidad in dist_ubicacion.items():
        porcentaje = (cantidad / total_poblacion_csv) * 100
        print(f"  {ubicacion}: {cantidad:,} personas ({porcentaje:.1f}%)")
    
    print(f"\n👥 DISTRIBUCIÓN POR GRUPOS ETARIOS EN CSV:")
    dist_grupos = conteo.groupby('grupo_etario')['poblacion_total'].sum()
    for grupo in ORDEN_GRUPOS_ETARIOS:
        if grupo in dist_grupos.index and grupo != 'Sin datos':
            cantidad = dist_grupos[grupo]
            porcentaje = (cantidad / total_poblacion_csv) * 100
            print(f"  {grupo}: {cantidad:,} personas ({porcentaje:.1f}%)")
    
    # Mostrar estadísticas completas de toda la población (incluyendo excluidos del CSV)
    print(f"\n📈 ESTADÍSTICAS COMPLETAS DE TODA LA POBLACIÓN PROCESADA:")
    
    # Población fuera de grupos etarios (excluida del CSV)
    fuera_grupos = df_final[df_final['fuera_grupos_etarios']]
    if len(fuera_grupos) > 0:
        print(f"  📊 Población fuera de grupos etarios: {len(fuera_grupos):,}")
        for etiqueta, cantidad in fuera_grupos['etiqueta_fuera_grupos'].value_counts().items():
            print(f"    • {etiqueta}: {cantidad:,}")
    
    # Sin datos de edad (excluida del CSV)
    sin_datos = df_final[df_final['grupo_etario'] == 'Sin datos']
    if len(sin_datos) > 0:
        print(f"  ❌ Sin datos de edad: {len(sin_datos):,}")
    
    print(f"\n💾 NOTA: El CSV final solo incluirá los {len(df_para_csv):,} registros de grupos etarios definidos.")
    
    return conteo

def guardar_resultado_csv(conteo_poblacional):
    """Guarda el resultado final en CSV para PostgreSQL"""
    print(f"\n{'='*60}")
    print("GUARDANDO RESULTADO FINAL")
    print('='*60)
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime('%Y%m%d')
    archivo_csv = f'data\\processed\\conteo_poblacional_tolima_{timestamp}.csv'
    
    try:
        conteo_poblacional.to_csv(archivo_csv, index=False, encoding='utf-8-sig')
        print(f"✅ Archivo CSV guardado: {archivo_csv}")
        print(f"📁 Ubicación: {os.path.abspath(archivo_csv)}")
        print(f"📊 Registros: {len(conteo_poblacional):,}")
        print(f"📋 Columnas: {list(conteo_poblacional.columns)}")
        
        return archivo_csv
        
    except Exception as e:
        print(f"❌ Error al guardar CSV: {e}")
        return None

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def procesar_conteo_poblacional(archivo_csv):
    """
    Función principal que ejecuta todo el procesamiento
    
    Args:
        archivo_csv (str): Ruta al archivo CSV con datos poblacionales
    
    Returns:
        tuple: (conteo_poblacional, archivo_csv_generado)
    """
    
    print("\n" + "="*80)
    print(" CONTEO POBLACIONAL POR MUNICIPIOS DEL TOLIMA ".center(80))
    print("="*80)
    fecha_actual = datetime.now()
    print(f"Iniciando procesamiento: {fecha_actual.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*80)
    
    # Mostrar criterios aplicados
    print("\n📋 CRITERIOS DE EXCLUSIÓN QUE SE APLICARÁN:")
    print("1. ❌ Fecha nacimiento nula o inválida")
    print("2. ❌ Fecha nacimiento posterior a fecha actual") 
    print("3. ❌ Edad calculada menor a 0 años (nacimientos problemáticos)")
    print("4. ❌ Edad calculada mayor a 90 años")
    print("5. ❌ Registros duplicados por documento (conservar más reciente)")
    
    print("\n📋 CRITERIOS DE INCLUSIÓN EN CSV FINAL:")
    print("✅ Solo población en grupos etarios definidos")
    print("📊 Población fuera de grupos etarios: mostrar en consola, NO incluir en CSV")
    print("📊 Población sin datos de edad: mostrar en consola, NO incluir en CSV")
    
    print("\n🏘️ CRITERIOS DE CLASIFICACIÓN URBANO/RURAL:")
    print("- 🌾 RURAL: vereda ≠ 'SIN VEREDA' O (vereda = 'SIN VEREDA' pero corregimiento rural)")
    print("- 🏙️ URBANO: vereda = 'SIN VEREDA' y (corregimiento = 'CABECERA MUNICIPAL' O otros casos urbanos)")
    
    print(f"\n🎯 GRUPOS ETARIOS DEFINIDOS ACTUALMENTE:")
    for grupo in ORDEN_GRUPOS_ETARIOS:
        if grupo != 'Sin datos':
            print(f"  • {grupo}")
    print("📝 Nota: Modificar función clasificar_grupo_etario() adapta automáticamente toda la lógica")
    
    try:
        # 1. Cargar datos
        df_original = cargar_datos(archivo_csv)
        
        # 2. Validar fecha de nacimiento únicamente
        df_limpio = validar_fecha_nacimiento(df_original)
        
        # 3. Calcular edades y aplicar filtros de edad
        df_limpio = calcular_edades_y_validar(df_limpio)
        
        # 4. Procesar y clasificar urbano/rural
        df_procesado = procesar_y_clasificar(df_limpio)
        
        # 5. Eliminar duplicados
        df_final = eliminar_duplicados(df_procesado)
        
        # 6. Crear conteo poblacional
        conteo_poblacional = crear_conteo_poblacional(df_final)
        
        # 7. Mostrar estadísticas finales en consola
        print(f"\n{'='*60}")
        print("RESUMEN FINAL DEL PROCESAMIENTO")
        print('='*60)
        print(f"📊 Registros originales: {len(df_original):,}")
        print(f"📊 Registros procesados: {len(df_final):,}")
        print(f"📊 Registros excluidos: {len(df_original) - len(df_final):,}")
        print(f"📊 Porcentaje de validez: {(len(df_final)/len(df_original)*100):.1f}%")
        print(f"📊 Registros agregados finales: {len(conteo_poblacional):,}")
        
        # 8. Guardar resultado final
        archivo_csv_generado = guardar_resultado_csv(conteo_poblacional)
        
        # 9. Resumen final
        print(f"\n{'='*80}")
        print(" PROCESAMIENTO COMPLETADO EXITOSAMENTE ".center(80))
        print('='*80)
        
        if archivo_csv_generado:
            print(f"\n💾 Archivo generado: {archivo_csv_generado}")
            print(f"📋 Estructura: codigo_municipio, municipio, tipo_ubicacion, grupo_etario, poblacion_total")
            print(f"📊 Listo para cargar a PostgreSQL")
        
        print(f"\n⏱️ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n¡Procesamiento completado exitosamente!")
        
        return conteo_poblacional, archivo_csv_generado
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ============================================
# EJECUCIÓN DEL SCRIPT
# ============================================

if __name__ == "__main__":
    # Archivo CSV por defecto
    ARCHIVO_CSV_DEFAULT = 'data\\poblacion_veredas.csv'
    
    # Verificar si el archivo existe
    if not os.path.exists(ARCHIVO_CSV_DEFAULT):
        print(f"❌ ERROR: No se encuentra el archivo '{ARCHIVO_CSV_DEFAULT}'")
        print("Opciones:")
        print("1. Asegúrate de que el archivo esté en el mismo directorio")
        print("2. Modifica la variable ARCHIVO_CSV_DEFAULT con la ruta correcta")
        print("3. Ejecuta: procesar_conteo_poblacional('ruta/a/tu/archivo.csv')")
        sys.exit(1)
    
    # Ejecutar procesamiento
    conteo_final, archivo_generado = procesar_conteo_poblacional(ARCHIVO_CSV_DEFAULT)