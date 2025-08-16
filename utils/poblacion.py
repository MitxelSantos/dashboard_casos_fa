#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Conteo Poblacional por Municipios del Tolima
Descripción: Script para generar conteo poblacional agregado por municipio,
             distinguiendo grupos etarios y ubicación urbana/rural
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

warnings.filterwarnings("ignore")

# Configurar pandas
pd.options.mode.chained_assignment = None
pd.set_option("display.max_columns", None)

# ============================================
# CONFIGURACIÓN DE COLUMNAS
# ============================================
# Posiciones de columnas en el CSV (sin encabezados)
COLUMNA_CODIGO_MUNICIPIO = 1  # Código único del municipio (73001)
COLUMNA_MUNICIPIO = 2  # Nombre del municipio (IBAGUÉ)
COLUMNA_VEREDA = 8  # Vereda (para determinar urbano/rural)
COLUMNA_FECHA_REGISTRO = 4  # Fecha registro (formato: 2021-08-27 14:54:39.243)
COLUMNA_FECHA_NACIMIENTO = 18  # Fecha nacimiento (formato: 1947-11-16)
COLUMNA_DOCUMENTO = 17  # Documento de identidad

# Orden estándar de grupos etarios
ORDEN_GRUPOS_ETARIOS = [
    "Menor de 9 meses",
    "09-23 meses",
    "02-19 años",
    "20-59 años",
    "60+ años",
    "Sin datos",
]

# ============================================
# FUNCIONES DE PROCESAMIENTO
# ============================================


def cargar_datos(archivo_csv):
    """Carga el CSV sin encabezados y valida estructura"""
    print(f"\n{'='*60}")
    print("CARGANDO DATOS POBLACIONALES")
    print("=" * 60)

    try:
        df = pd.read_csv(archivo_csv, header=None)
        print(f"✅ CSV cargado exitosamente: {len(df):,} registros")
        print(f"📊 Número de columnas: {len(df.columns)}")

        # Verificación de columnas
        if len(df) > 0:
            print("\n--- VERIFICACIÓN DE COLUMNAS ---")
            print(
                f"Columna {COLUMNA_CODIGO_MUNICIPIO} (Código Municipio): {df.iloc[0, COLUMNA_CODIGO_MUNICIPIO]}"
            )
            print(
                f"Columna {COLUMNA_MUNICIPIO} (Municipio): {df.iloc[0, COLUMNA_MUNICIPIO]}"
            )
            print(f"Columna {COLUMNA_VEREDA} (Vereda): {df.iloc[0, COLUMNA_VEREDA]}")
            print(
                f"Columna {COLUMNA_FECHA_REGISTRO} (Fecha Registro): {df.iloc[0, COLUMNA_FECHA_REGISTRO]}"
            )
            print(
                f"Columna {COLUMNA_FECHA_NACIMIENTO} (Fecha Nacimiento): {df.iloc[0, COLUMNA_FECHA_NACIMIENTO]}"
            )
            print(
                f"Columna {COLUMNA_DOCUMENTO} (Documento): {df.iloc[0, COLUMNA_DOCUMENTO]}"
            )

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
    if pd.isna(texto) or texto == "":
        return None
    return str(texto).strip().title()


def convertir_fechas(df):
    """Convierte las columnas de fecha al formato correcto"""
    print(f"\n{'='*60}")
    print("CONVIRTIENDO Y VALIDANDO FECHAS")
    print("=" * 60)

    # Convertir fecha de registro
    try:
        df[COLUMNA_FECHA_REGISTRO] = pd.to_datetime(
            df[COLUMNA_FECHA_REGISTRO], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce"
        )
        # Si hay muchos NaT, intenta formato sin milisegundos
        if df[COLUMNA_FECHA_REGISTRO].isna().sum() > len(df) * 0.5:
            df[COLUMNA_FECHA_REGISTRO] = pd.to_datetime(
                df[COLUMNA_FECHA_REGISTRO], format="%Y-%m-%d %H:%M:%S", errors="coerce"
            )
    except:
        df[COLUMNA_FECHA_REGISTRO] = pd.to_datetime(
            df[COLUMNA_FECHA_REGISTRO], errors="coerce"
        )

    # Convertir fecha de nacimiento
    df[COLUMNA_FECHA_NACIMIENTO] = pd.to_datetime(
        df[COLUMNA_FECHA_NACIMIENTO], format="%Y-%m-%d", errors="coerce"
    )

    # Verificar fechas nulas
    fechas_registro_nulas = df[COLUMNA_FECHA_REGISTRO].isna().sum()
    fechas_nacimiento_nulas = df[COLUMNA_FECHA_NACIMIENTO].isna().sum()

    print(f"📅 Fechas de registro nulas/inválidas: {fechas_registro_nulas:,}")
    print(f"📅 Fechas de nacimiento nulas/inválidas: {fechas_nacimiento_nulas:,}")

    # Eliminar registros con fechas nulas
    df_limpio = df.dropna(subset=[COLUMNA_FECHA_REGISTRO, COLUMNA_FECHA_NACIMIENTO])
    print(f"\n✅ Registros válidos para análisis: {len(df_limpio):,}")

    # Validación de fechas lógicas
    fechas_invalidas = df_limpio[
        df_limpio[COLUMNA_FECHA_NACIMIENTO] > df_limpio[COLUMNA_FECHA_REGISTRO]
    ]
    if len(fechas_invalidas) > 0:
        print(
            f"\n⚠️ Advertencia: {len(fechas_invalidas)} registros con fecha de nacimiento posterior a fecha de registro"
        )
        df_limpio = df_limpio[
            df_limpio[COLUMNA_FECHA_NACIMIENTO] <= df_limpio[COLUMNA_FECHA_REGISTRO]
        ]
        print(
            f"Registros válidos después de filtrar fechas ilógicas: {len(df_limpio):,}"
        )

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
    """Calcula las edades y valida los datos"""
    print(f"\n{'='*60}")
    print("CALCULANDO EDADES Y VALIDANDO DATOS")
    print("=" * 60)

    fecha_actual = pd.Timestamp.now()
    print(
        f"📅 Fecha de referencia para cálculo de edad: {fecha_actual.strftime('%Y-%m-%d')}"
    )

    # Calcular edades usando fecha actual
    edades = df_limpio.apply(
        lambda row: calcular_edad_detallada(
            row[COLUMNA_FECHA_NACIMIENTO], fecha_actual
        ),
        axis=1,
    )

    df_limpio["edad_anos"] = edades.apply(lambda x: x[0] if x else None)
    df_limpio["edad_meses"] = edades.apply(lambda x: x[1] if x else None)

    # Validaciones de calidad
    print("\n📊 VALIDACIÓN DE CALIDAD DE DATOS")
    print("-" * 40)

    # Edades negativas (error grave)
    edades_negativas = df_limpio[df_limpio["edad_anos"] < 0]
    if len(edades_negativas) > 0:
        print(f"\n❌ ERROR GRAVE: {len(edades_negativas)} registros con edad negativa")
        df_limpio = df_limpio[df_limpio["edad_anos"] >= 0]

    # Mayores de 90 años (sospechoso, filtrar)
    mayores_90 = df_limpio[df_limpio["edad_anos"] > 90]
    if len(mayores_90) > 0:
        print(f"\n⚠️ FILTRADO: {len(mayores_90)} registros con edad mayor a 90 años")
        df_limpio = df_limpio[df_limpio["edad_anos"] <= 90]

    # Estadísticas finales
    print(f"\n📊 ESTADÍSTICAS DE EDAD:")
    print(f"  Edad mínima: {df_limpio['edad_anos'].min():.1f} años")
    print(f"  Edad máxima: {df_limpio['edad_anos'].max():.1f} años")
    print(f"  Edad promedio: {df_limpio['edad_anos'].mean():.1f} años")
    print(f"  Registros válidos finales: {len(df_limpio):,}")

    return df_limpio


def clasificar_grupo_etario(edad_meses):
    """Clasifica según los grupos etarios especificados"""
    if pd.isna(edad_meses):
        return "Sin datos"

    if edad_meses < 9:
        return "Menor de 9 meses"
    elif edad_meses >= 9 and edad_meses <= 23:
        return "09-23 meses"
    elif edad_meses >= 24 and edad_meses < 240:  # 2 a 19 años
        return "02-19 años"
    elif edad_meses >= 240 and edad_meses < 720:  # 20 a 59 años
        return "20-59 años"
    else:
        return "60+ años"


def determinar_ubicacion(vereda):
    """Determina si es urbano o rural basado en la vereda"""
    if pd.isna(vereda) or vereda == "":
        return "Urbano"

    vereda_str = str(vereda).upper().strip()

    # Si es "SIN VEREDA" o similar, es urbano
    if any(
        patron in vereda_str
        for patron in ["SIN VEREDA", "SIN", "URBANO", "CENTRO", "CABECERA"]
    ):
        return "Urbano"

    # Si tiene nombre de vereda específico, es rural
    return "Rural"


def procesar_y_clasificar(df_limpio):
    """Procesa los datos y los clasifica"""
    print(f"\n{'='*60}")
    print("PROCESANDO Y CLASIFICANDO REGISTROS")
    print("=" * 60)

    # Agregar código de municipio (columna 1)
    df_limpio["codigo_municipio"] = df_limpio[COLUMNA_CODIGO_MUNICIPIO]

    # Normalizar nombres de municipios
    df_limpio["municipio_normalizado"] = df_limpio[COLUMNA_MUNICIPIO].apply(
        normalizar_texto
    )

    # Clasificar grupos etarios
    df_limpio["grupo_etario"] = df_limpio["edad_meses"].apply(clasificar_grupo_etario)

    # Determinar ubicación urbana/rural
    df_limpio["tipo_ubicacion"] = df_limpio[COLUMNA_VEREDA].apply(determinar_ubicacion)

    print(f"✅ Clasificación completada")
    print(f"📍 Municipios únicos: {df_limpio['municipio_normalizado'].nunique()}")
    print(
        f"🏙️ Distribución urbano/rural: {df_limpio['tipo_ubicacion'].value_counts().to_dict()}"
    )
    print(f"🏢 Códigos de municipio únicos: {df_limpio['codigo_municipio'].nunique()}")

    return df_limpio


def eliminar_duplicados(df_limpio):
    """Elimina duplicados por documento, conservando el registro más reciente"""
    print(f"\n{'='*60}")
    print("ELIMINANDO DUPLICADOS")
    print("=" * 60)

    registros_iniciales = len(df_limpio)

    # Ordenar por fecha de registro (más reciente primero)
    df_limpio = df_limpio.sort_values(
        COLUMNA_FECHA_REGISTRO, ascending=False, na_position="last"
    )

    # Eliminar duplicados por documento (mantener el primero = más reciente)
    df_sin_duplicados = df_limpio.drop_duplicates(
        subset=[COLUMNA_DOCUMENTO], keep="first"
    )

    duplicados_removidos = registros_iniciales - len(df_sin_duplicados)
    print(f"📋 Duplicados removidos: {duplicados_removidos:,}")
    print(f"✅ Registros únicos finales: {len(df_sin_duplicados):,}")

    return df_sin_duplicados


def crear_conteo_poblacional(df_final):
    """Crea el conteo poblacional agregado por municipio"""
    print(f"\n{'='*60}")
    print("CREANDO CONTEO POBLACIONAL POR MUNICIPIO")
    print("=" * 60)

    # Conteo agregado
    conteo = (
        df_final.groupby(
            [
                "codigo_municipio",
                "municipio_normalizado",
                "tipo_ubicacion",
                "grupo_etario",
            ]
        )
        .size()
        .reset_index(name="poblacion_total")
    )

    # Renombrar columnas para estructura PostgreSQL final
    conteo = conteo.rename(columns={"municipio_normalizado": "municipio"})

    # Ordenar resultados
    conteo = conteo.sort_values(
        ["codigo_municipio", "tipo_ubicacion", "grupo_etario"]
    ).reset_index(drop=True)

    print(f"✅ Conteo poblacional creado: {len(conteo)} registros agregados")

    # Estadísticas de resumen (solo consola)
    total_poblacion = conteo["poblacion_total"].sum()
    municipios_unicos = conteo["codigo_municipio"].nunique()

    print(f"📊 ESTADÍSTICAS FINALES:")
    print(f"  Total población: {total_poblacion:,} personas")
    print(f"  Municipios únicos: {municipios_unicos}")

    print(f"\n🏙️ DISTRIBUCIÓN URBANO/RURAL:")
    dist_ubicacion = conteo.groupby("tipo_ubicacion")["poblacion_total"].sum()
    for ubicacion, cantidad in dist_ubicacion.items():
        porcentaje = (cantidad / total_poblacion) * 100
        print(f"  {ubicacion}: {cantidad:,} personas ({porcentaje:.1f}%)")

    print(f"\n👥 DISTRIBUCIÓN POR GRUPOS ETARIOS:")
    dist_grupos = conteo.groupby("grupo_etario")["poblacion_total"].sum()
    for grupo in ORDEN_GRUPOS_ETARIOS:
        if grupo in dist_grupos.index:
            cantidad = dist_grupos[grupo]
            porcentaje = (cantidad / total_poblacion) * 100
            print(f"  {grupo}: {cantidad:,} personas ({porcentaje:.1f}%)")

    return conteo


def guardar_resultado_csv(conteo_poblacional):
    """Guarda el resultado final en CSV para PostgreSQL"""
    print(f"\n{'='*60}")
    print("GUARDANDO RESULTADO FINAL")
    print("=" * 60)

    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_csv = f"conteo_poblacional_tolima_{timestamp}.csv"

    try:
        conteo_poblacional.to_csv(archivo_csv, index=False, encoding="utf-8-sig")
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

    print("\n" + "=" * 80)
    print(" CONTEO POBLACIONAL POR MUNICIPIOS DEL TOLIMA ".center(80))
    print("=" * 80)
    fecha_actual = datetime.now()
    print(f"Iniciando procesamiento: {fecha_actual.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    try:
        # 1. Cargar datos
        df_original = cargar_datos(archivo_csv)

        # 2. Convertir y validar fechas
        df_limpio = convertir_fechas(df_original)

        # 3. Calcular edades y validar
        df_limpio = calcular_edades_y_validar(df_limpio)

        # 4. Procesar y clasificar
        df_procesado = procesar_y_clasificar(df_limpio)

        # 5. Eliminar duplicados
        df_final = eliminar_duplicados(df_procesado)

        # 6. Crear conteo poblacional
        conteo_poblacional = crear_conteo_poblacional(df_final)

        # 7. Mostrar estadísticas finales en consola
        print(f"\n{'='*60}")
        print("ESTADÍSTICAS FINALES DEL PROCESAMIENTO")
        print("=" * 60)
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
        print("=" * 80)

        if archivo_csv_generado:
            print(f"\n💾 Archivo generado: {archivo_csv_generado}")
            print(
                f"📋 Estructura: codigo_municipio, municipio, tipo_ubicacion, grupo_etario, poblacion_total"
            )
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
    # Verificar dependencias
    try:
        import openpyxl
    except ImportError:
        print(
            "⚠️ NOTA: openpyxl no está instalado, pero no es necesario para este script."
        )
        print("Solo se generará archivo CSV.")

    # Archivo CSV por defecto
    ARCHIVO_CSV_DEFAULT = (
        "E:\\Proyectos\\dashboard_casos_fa\\data\\poblacion_veredas.csv"
    )

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
