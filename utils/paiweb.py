#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Limpieza - Base de Datos PAIweb Fiebre Amarilla
Descripción: Limpia y procesa datos de vacunación de fiebre amarilla para PostgreSQL
Autor: Sistema de Análisis Demográfico
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
import re
import os
import warnings

warnings.filterwarnings("ignore")


def limpiar_paiweb_fiebre_amarilla(archivo_excel, hoja="Vacunas"):
    """
    Limpia y procesa datos de PAIweb para fiebre amarilla del Tolima

    Args:
        archivo_excel (str): Ruta al archivo Excel
        hoja (str): Nombre de la hoja a procesar

    Returns:
        pandas.DataFrame: DataFrame limpio para PostgreSQL
    """

    print("🔄 Cargando archivo Excel...")
    df = pd.read_excel(archivo_excel, sheet_name=hoja)

    print(f"📊 Registros iniciales: {len(df):,}")

    # ================================
    # 1. ELIMINAR COLUMNAS NO NECESARIAS
    # ================================
    columnas_eliminar = ["Departamento", "nombrebiologico", "dosis", "Actualizacion"]
    df = df.drop(columns=[col for col in columnas_eliminar if col in df.columns])

    # ================================
    # 2. MAPEO Y NORMALIZACIÓN DE MUNICIPIOS
    # ================================
    def normalizar_municipio(municipio):
        if pd.isna(municipio):
            return None

        municipio = str(municipio).strip().upper()

        # Mapeo específico
        mapeo_municipios = {
            "SAN SEBASTIÁN DE MARIQUITA": "MARIQUITA",
            "SAN SEBASTIAN DE MARIQUITA": "MARIQUITA",
        }

        if municipio in mapeo_municipios:
            municipio = mapeo_municipios[municipio]

        # Convertir a Title Case para normalizar
        return municipio.title()

    df["Municipio"] = df["Municipio"].apply(normalizar_municipio)

    # ================================
    # 3. LIMPIEZA Y VALIDACIÓN DE FECHAS
    # ================================
    def limpiar_fecha(fecha_str):
        if pd.isna(fecha_str):
            return None

        # Convertir a string y limpiar
        fecha_str = str(fecha_str).strip()

        # Remover partes de tiempo si existen
        if " " in fecha_str:
            fecha_str = fecha_str.split(" ")[0]

        # Intentar diferentes formatos
        formatos = ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%m/%d/%Y"]

        for formato in formatos:
            try:
                return datetime.strptime(fecha_str, formato).date()
            except:
                continue

        return None

    df["fechaaplicacion"] = df["fechaaplicacion"].apply(limpiar_fecha)
    df["FechaNacimiento"] = df["FechaNacimiento"].apply(limpiar_fecha)

    # ================================
    # 4. CALCULAR EDAD Y VALIDACIONES
    # ================================
    fecha_corte = date.today()

    def calcular_edad(fecha_nacimiento):
        if pd.isna(fecha_nacimiento) or fecha_nacimiento is None:
            return None

        try:
            edad = fecha_corte.year - fecha_nacimiento.year
            if fecha_corte.month < fecha_nacimiento.month or (
                fecha_corte.month == fecha_nacimiento.month
                and fecha_corte.day < fecha_nacimiento.day
            ):
                edad -= 1
            return edad
        except:
            return None

    df["edad_anos"] = df["FechaNacimiento"].apply(calcular_edad)

    # ================================
    # 5. CLASIFICACIÓN GRUPOS ETARIOS
    # ================================
    def clasificar_grupo_etario(edad):
        if pd.isna(edad) or edad is None:
            return "Sin datos"

        if edad < 0.75:  # Menor de 9 meses
            return "Menor de 9 meses"
        elif edad < 2:  # 09-23 meses
            return "09-23 meses"
        elif edad <= 19:  # 02-19 años
            return "02-19 años"
        elif edad <= 59:  # 20-59 años
            return "20-59 años"
        else:  # 60+ años
            return "60+ años"

    df["grupo_etario"] = df["edad_anos"].apply(clasificar_grupo_etario)

    # ================================
    # 6. DÍAS DESDE VACUNACIÓN
    # ================================
    def calcular_dias_vacunacion(fecha_aplicacion):
        if pd.isna(fecha_aplicacion) or fecha_aplicacion is None:
            return None

        try:
            delta = fecha_corte - fecha_aplicacion
            return delta.days
        except:
            return None

    df["dias_desde_vacunacion"] = df["fechaaplicacion"].apply(calcular_dias_vacunacion)

    # ================================
    # 7. NORMALIZAR NOMBRES Y TIPO DE UBICACIÓN
    # ================================
    def normalizar_nombre(nombre):
        if pd.isna(nombre):
            return None
        return str(nombre).strip().title()

    campos_nombres = [
        "PrimerNombre",
        "SegundoNombre",
        "PrimerApellido",
        "SegundoApellido",
    ]
    for campo in campos_nombres:
        if campo in df.columns:
            df[campo] = df[campo].apply(normalizar_nombre)

    # Normalizar TipoUbicación y asumir 'Urbano' donde no hay datos
    def normalizar_tipo_ubicacion(tipo):
        if pd.isna(tipo) or str(tipo).strip() == "":
            return "Urbano"
        return str(tipo).strip().title()

    df["TipoUbicación"] = df["TipoUbicación"].apply(normalizar_tipo_ubicacion)

    # ================================
    # 8. VALIDACIONES Y FILTRADO
    # ================================
    registros_iniciales = len(df)

    # Filtrar registros con datos básicos válidos
    df = df.dropna(subset=["fechaaplicacion", "FechaNacimiento", "Documento"])

    # Filtrar fechas coherentes
    df = df[df["fechaaplicacion"] >= df["FechaNacimiento"]]
    df = df[df["fechaaplicacion"] <= fecha_corte]
    df = df[df["FechaNacimiento"] <= fecha_corte]

    # Filtrar edades razonables
    df = df[(df["edad_anos"] >= 0) & (df["edad_anos"] <= 90)]

    print(f"📊 Registros después de validaciones: {len(df):,}")
    print(f"📊 Registros excluidos: {registros_iniciales - len(df):,}")

    # ================================
    # 9. ELIMINAR DUPLICADOS
    # ================================
    print("🔍 Eliminando duplicados por documento...")

    # Ordenar por fecha de aplicación (más reciente primero)
    df = df.sort_values("fechaaplicacion", ascending=False, na_position="last")

    # Eliminar duplicados por documento (mantener el más reciente)
    registros_antes_duplicados = len(df)
    df = df.drop_duplicates(subset=["Documento"], keep="first")

    duplicados_removidos = registros_antes_duplicados - len(df)
    print(f"📋 Duplicados removidos: {duplicados_removidos:,}")
    print(f"✅ Registros únicos finales: {len(df):,}")

    # ================================
    # 10. GENERAR CÓDIGO DE MUNICIPIO
    # ================================
    def generar_codigo_municipio(municipio):
        if pd.isna(municipio):
            return None

        # Mapeo completo de municipios del Tolima
        codigos_municipios = {
            "Ibagué": "73001",
            "Mariquita": "73408",
            "Armero (Guayabal)": "73055",
            "Armero Guayabal": "73055",
            "Armero": "73055",
            "Ambalema": "73024",
            "Anzoátegui": "73043",
            "Ataco": "73067",
            "Cajamarca": "73124",
            "Carmen De Apicalá": "73148",
            "Carmen De Apicala": "73148",
            "Casabianca": "73152",
            "Chaparral": "73168",
            "Coello": "73200",
            "Coyaima": "73217",
            "Cunday": "73226",
            "Dolores": "73236",
            "Espinal": "73268",
            "Falan": "73270",
            "Flandes": "73275",
            "Fresno": "73283",
            "Guamo": "73319",
            "Herveo": "73347",
            "Honda": "73349",
            "Icononzo": "73352",
            "Lérida": "73408",
            "Lerida": "73408",
            "Líbano": "73411",
            "Libano": "73411",
            "Melgar": "73449",
            "Murillo": "73461",
            "Natagaima": "73483",
            "Ortega": "73504",
            "Palocabildo": "73520",
            "Piedras": "73547",
            "Planadas": "73555",
            "Prado": "73563",
            "Purificación": "73585",
            "Purificacion": "73585",
            "Rioblanco": "73616",
            "Roncesvalles": "73622",
            "Rovira": "73624",
            "Saldaña": "73675",
            "Saldana": "73675",
            "San Antonio": "73678",
            "San Luis": "73686",
            "Santa Isabel": "73770",
            "Suárez": "73854",
            "Suarez": "73854",
            "Valle De San Juan": "73861",
            "Valle De San Juan": "73861",
            "Venadillo": "73873",
            "Villahermosa": "73870",
            "Villarrica": "73873",
        }

        # Normalizar municipio para búsqueda
        municipio_norm = str(municipio).strip().title()

        # Buscar código exacto
        codigo = codigos_municipios.get(municipio_norm)

        # Si no se encuentra exacto, buscar coincidencias parciales
        if codigo is None:
            municipio_clean = (
                municipio_norm.upper()
                .replace("Á", "A")
                .replace("É", "E")
                .replace("Í", "I")
                .replace("Ó", "O")
                .replace("Ú", "U")
                .replace("Ñ", "N")
            )

            for mun_mapa, cod_mapa in codigos_municipios.items():
                mun_clean = (
                    mun_mapa.upper()
                    .replace("Á", "A")
                    .replace("É", "E")
                    .replace("Í", "I")
                    .replace("Ó", "O")
                    .replace("Ú", "U")
                    .replace("Ñ", "N")
                )
                if municipio_clean in mun_clean or mun_clean in municipio_clean:
                    codigo = cod_mapa
                    break

        # Si aún no se encuentra, usar código genérico del Tolima
        if codigo is None:
            print(
                f"⚠️ Municipio no encontrado en mapeo: {municipio_norm} - Usando código genérico 73999"
            )
            codigo = "73999"

        return codigo

    df["codigo_municipio"] = df["Municipio"].apply(generar_codigo_municipio)

    # ================================
    # 11. SELECCIONAR COLUMNAS FINALES EN SNAKE_CASE
    # ================================
    # Renombrar columnas a snake_case para PostgreSQL
    df_final = df.rename(
        columns={
            "Municipio": "municipio",
            "Institucion": "institucion",
            "fechaaplicacion": "fecha_aplicacion",
            "tipoDocumento": "tipo_documento",
            "Documento": "documento",
            "PrimerNombre": "primer_nombre",
            "SegundoNombre": "segundo_nombre",
            "PrimerApellido": "primer_apellido",
            "SegundoApellido": "segundo_apellido",
            "FechaNacimiento": "fecha_nacimiento",
            "lote": "lote",
            "TipoUbicación": "tipo_ubicacion",
        }
    )

    # Seleccionar solo las columnas necesarias para PostgreSQL
    columnas_finales = [
        "codigo_municipio",
        "municipio",
        "institucion",
        "fecha_aplicacion",
        "tipo_documento",
        "documento",
        "primer_nombre",
        "segundo_nombre",
        "primer_apellido",
        "segundo_apellido",
        "fecha_nacimiento",
        "lote",
        "tipo_ubicacion",
        "edad_anos",
        "grupo_etario",
        "dias_desde_vacunacion",
    ]

    df_final = df_final[columnas_finales].copy()

    # ================================
    # 12. ESTADÍSTICAS FINALES EN CONSOLA
    # ================================
    print(f"\n{'='*60}")
    print("ESTADÍSTICAS FINALES DEL PROCESAMIENTO")
    print("=" * 60)

    total_registros = len(df_final)

    print(f"📊 Total registros procesados: {total_registros:,}")
    print(f"📍 Municipios únicos: {df_final['municipio'].nunique()}")
    print(f"🏥 Instituciones únicas: {df_final['institucion'].nunique()}")

    print(f"\n🏙️ DISTRIBUCIÓN URBANO/RURAL:")
    dist_ubicacion = df_final["tipo_ubicacion"].value_counts()
    for ubicacion, cantidad in dist_ubicacion.items():
        porcentaje = (cantidad / total_registros) * 100
        print(f"  {ubicacion}: {cantidad:,} ({porcentaje:.1f}%)")

    print(f"\n👥 DISTRIBUCIÓN POR GRUPOS ETARIOS:")
    dist_grupos = df_final["grupo_etario"].value_counts()
    grupos_orden = [
        "Menor de 9 meses",
        "09-23 meses",
        "02-19 años",
        "20-59 años",
        "60+ años",
        "Sin datos",
    ]
    for grupo in grupos_orden:
        if grupo in dist_grupos.index:
            cantidad = dist_grupos[grupo]
            porcentaje = (cantidad / total_registros) * 100
            print(f"  {grupo}: {cantidad:,} ({porcentaje:.1f}%)")

    print(f"\n📅 ESTADÍSTICAS DE EDAD:")
    print(f"  Edad mínima: {df_final['edad_anos'].min():.0f} años")
    print(f"  Edad máxima: {df_final['edad_anos'].max():.0f} años")
    print(f"  Edad promedio: {df_final['edad_anos'].mean():.1f} años")

    print("✅ Procesamiento completado!")

    return df_final


def guardar_resultado_csv(df_limpio, nombre_base="paiweb_tolima_fa"):
    """
    Guarda el resultado final en CSV para PostgreSQL
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    archivo_csv = f"data\\processed\\{nombre_base}_{timestamp}.csv"

    try:
        df_limpio.to_csv(archivo_csv, index=False, encoding="utf-8-sig")
        print(f"\n💾 Archivo CSV guardado: {archivo_csv}")
        print(
            f"📁 Ubicación: {os.path.abspath(archivo_csv) if 'os' in globals() else 'Directorio actual'}"
        )
        print(f"📊 Registros: {len(df_limpio):,}")
        print(f"📋 Columnas: {list(df_limpio.columns)}")
        print(f"🗄️ Listo para cargar a PostgreSQL")

        return archivo_csv

    except Exception as e:
        print(f"❌ Error al guardar CSV: {e}")
        return None


# ================================
# FUNCIÓN PRINCIPAL DE USO
# ================================
def procesar_archivo_paiweb(ruta_archivo, hoja="Vacunas"):
    """
    Función principal para procesar archivos PAIweb

    Args:
        ruta_archivo (str): Ruta al archivo Excel
        hoja (str): Nombre de la hoja

    Returns:
        tuple: (dataframe_limpio, archivo_csv_generado)
    """

    print("\n" + "=" * 80)
    print(" PROCESAMIENTO PAIweb FIEBRE AMARILLA PARA POSTGRESQL ".center(80))
    print("=" * 80)
    fecha_actual = datetime.now()
    print(f"Iniciando procesamiento: {fecha_actual.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    try:
        # Procesar archivo
        df_limpio = limpiar_paiweb_fiebre_amarilla(ruta_archivo, hoja)

        # Guardar resultado
        archivo_csv = guardar_resultado_csv(df_limpio)

        # Resumen final
        print(f"\n{'='*80}")
        print(" PROCESAMIENTO COMPLETADO EXITOSAMENTE ".center(80))
        print("=" * 80)

        if archivo_csv:
            print(f"\n💾 Archivo generado: {archivo_csv}")
            print(f"📋 Estructura PostgreSQL lista")

        print(f"\n⏱️ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n¡Procesamiento completado exitosamente!")

        return df_limpio, archivo_csv

    except Exception as e:
        print(f"❌ Error procesando archivo: {str(e)}")
        import traceback

        traceback.print_exc()
        return None, None


# ================================
# EJECUCIÓN DEL SCRIPT
# ================================
if __name__ == "__main__":
    import os

    # Archivo Excel por defecto
    archivo_default = "data\\paiweb.xlsx"

    # Verificar si el archivo existe
    if not os.path.exists(archivo_default):
        print(f"❌ ERROR: No se encuentra el archivo '{archivo_default}'")
        print("Opciones:")
        print("1. Asegúrate de que el archivo esté en el mismo directorio")
        print("2. Modifica la variable archivo_default con la ruta correcta")
        print("3. Ejecuta: procesar_archivo_paiweb('ruta/a/tu/archivo.xlsx')")
    else:
        # Ejecutar procesamiento
        df_resultado, archivo_generado = procesar_archivo_paiweb(archivo_default)
