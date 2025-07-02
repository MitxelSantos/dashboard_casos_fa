"""
Procesamiento y filtrado de datos del dashboard de Fiebre Amarilla.
Actualizado para manejar casos confirmados y epizootias con normalización robusta.
CORREGIDO: Función de fechas para formato DD/MM/YYYY.
"""

import pandas as pd
import numpy as np
import unicodedata
import re
from datetime import datetime
from config.settings import GRUPOS_EDAD, CONDICION_FINAL_MAP, DESCRIPCION_EPIZOOTIAS_MAP


def normalize_text(text):
    """
    Normaliza texto removiendo tildes, convirtiendo a mayúsculas y limpiando espacios.
    Maneja inconsistencias entre bases de datos.

    Args:
        text (str): Texto a normalizar

    Returns:
        str: Texto normalizado
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""

    # Remover tildes y diacríticos
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")

    # Convertir a mayúsculas y limpiar espacios
    text = text.upper().strip()

    # Limpiar espacios múltiples
    text = re.sub(r"\s+", " ", text)

    # Reemplazos específicos para problemas comunes
    replacements = {
        "VILLARICA": "VILLARRICA",  # Corregir inconsistencia común
        "PURIFICACION": "PURIFICACION",  # Mantener sin tilde
    }

    for old, new in replacements.items():
        if text == old:
            text = new
            break

    return text


def capitalize_names(text):
    """
    Convierte texto a formato de nombres propios (Primera letra mayúscula, resto minúscula).
    Maneja casos especiales como nombres con preposiciones.

    Args:
        text (str): Texto a formatear

    Returns:
        str: Texto con formato de nombre propio
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""

    # Limpiar texto primero
    text = text.strip()

    # Palabras que deben mantenerse en minúscula (preposiciones, artículos)
    lowercase_words = {"de", "del", "la", "las", "el", "los", "y", "e", "o", "u"}

    # Dividir en palabras
    words = text.split()
    formatted_words = []

    for i, word in enumerate(words):
        # Limpiar palabra de caracteres especiales al inicio/final para el análisis
        clean_word = re.sub(r"^[^\w]+|[^\w]+$", "", word.lower())

        # Si es la primera palabra o no está en la lista de palabras en minúscula
        if i == 0 or clean_word not in lowercase_words:
            # Capitalizar la primera letra
            if word:
                formatted_word = word[0].upper() + word[1:].lower()
            else:
                formatted_word = word
        else:
            # Mantener en minúscula
            formatted_word = word.lower()

        formatted_words.append(formatted_word)

    return " ".join(formatted_words)


def excel_date_to_datetime(excel_date):
    """
    Convierte fecha de Excel a datetime.
    CORREGIDO: Maneja formato DD/MM/YYYY correctamente.

    Args:
        excel_date: Número de fecha de Excel, datetime, o string

    Returns:
        datetime: Fecha convertida o None si no es válida
    """
    try:
        # Si ya es datetime, retornar tal como está
        if isinstance(excel_date, (pd.Timestamp, datetime)):
            return excel_date

        # Si está vacío o es NaN
        if pd.isna(excel_date) or excel_date == "":
            return None

        # Si es string, intentar parsear con formato DD/MM/YYYY
        if isinstance(excel_date, str):
            # Intentar diferentes formatos comunes
            formatos_fecha = [
                "%d/%m/%Y",      # DD/MM/YYYY
                "%d/%m/%y",      # DD/MM/YY  
                "%d-%m-%Y",      # DD-MM-YYYY
                "%d-%m-%y",      # DD-MM-YY
                "%Y-%m-%d",      # YYYY-MM-DD
                "%d.%m.%Y",      # DD.MM.YYYY
                "%d.%m.%y",      # DD.MM.YY
            ]
            
            for formato in formatos_fecha:
                try:
                    fecha_convertida = datetime.strptime(excel_date.strip(), formato)
                    # Si el año es menor a 50, asumimos que es 20XX, sino 19XX
                    if fecha_convertida.year < 50:
                        fecha_convertida = fecha_convertida.replace(year=fecha_convertida.year + 2000)
                    elif fecha_convertida.year < 100:
                        fecha_convertida = fecha_convertida.replace(year=fecha_convertida.year + 1900)
                    return fecha_convertida
                except ValueError:
                    continue
            
            # Si no funciona ningún formato, intentar pandas
            try:
                return pd.to_datetime(excel_date, dayfirst=True, errors="coerce")
            except:
                return None

        # Si es número, convertir desde formato Excel
        if isinstance(excel_date, (int, float)):
            # Excel cuenta días desde 1900-01-01, pero tiene un bug del año bisiesto
            # Usar 1899-12-30 como origen para corregir
            try:
                return pd.to_datetime(excel_date, origin="1899-12-30", unit="D")
            except:
                return None

        return None
    except Exception as e:
        print(f"Error procesando fecha: {excel_date} - {str(e)}")
        return None


def format_date_display(date_value):
    """
    Formatea una fecha para mostrar solo YYYY-MM-DD sin hora.

    Args:
        date_value: Valor de fecha a formatear

    Returns:
        str: Fecha formateada o cadena vacía si no es válida
    """
    if pd.isna(date_value):
        return ""

    try:
        if isinstance(date_value, (pd.Timestamp, datetime)):
            return date_value.strftime("%Y-%m-%d")
        else:
            # Intentar convertir primero
            converted_date = excel_date_to_datetime(date_value)
            if converted_date:
                return converted_date.strftime("%Y-%m-%d")
            else:
                return ""
    except:
        return ""


def create_age_groups(ages):
    """
    Crea grupos de edad a partir de una serie de edades usando configuración predefinida.

    Args:
        ages (pd.Series): Serie con las edades

    Returns:
        pd.Series: Serie con los grupos de edad
    """

    def classify_age(age):
        if pd.isna(age):
            return "No especificado"

        age = int(age) if not pd.isna(age) else 0

        for grupo in GRUPOS_EDAD:
            if grupo["min"] <= age <= grupo["max"]:
                return grupo["label"]

        return "No especificado"

    return ages.apply(classify_age)


def normalize_municipio_name(municipio):
    """
    Normaliza nombres de municipios para resolver inconsistencias específicas.

    Args:
        municipio (str): Nombre del municipio

    Returns:
        str: Nombre normalizado
    """
    if pd.isna(municipio):
        return ""

    # Aplicar normalización básica
    normalized = normalize_text(str(municipio))

    # Mapeo específico para municipios conocidos con inconsistencias
    municipio_map = {
        "VILLARICA": "VILLARRICA",
        "PURIFICACION": "PURIFICACION",
        "PLANADAS": "PLANADAS",
        "CHAPARRAL": "CHAPARRAL",
        "ATACO": "ATACO",
        "CUNDAY": "CUNDAY",
        "PRADO": "PRADO",
        "IBAGUE": "IBAGUE",
    }

    return municipio_map.get(normalized, normalized)


def process_casos_dataframe(df):
    """
    Procesa el dataframe de casos confirmados con limpieza específica.

    Args:
        df (pd.DataFrame): DataFrame de casos confirmados

    Returns:
        pd.DataFrame: DataFrame procesado
    """
    df_processed = df.copy()

    # Normalizar municipios y veredas
    if "municipio" in df_processed.columns:
        df_processed["municipio_normalizado"] = df_processed["municipio"].apply(
            normalize_municipio_name
        )
        df_processed["municipio"] = df_processed["municipio"].apply(capitalize_names)

    if "vereda" in df_processed.columns:
        df_processed["vereda_normalizada"] = df_processed["vereda"].apply(
            normalize_text
        )
        df_processed["vereda"] = df_processed["vereda"].apply(capitalize_names)

    # Procesar fechas con formato DD/MM/YYYY
    if "fecha_inicio_sintomas" in df_processed.columns:
        print("Procesando fechas de casos...")
        df_processed["fecha_inicio_sintomas"] = df_processed[
            "fecha_inicio_sintomas"
        ].apply(excel_date_to_datetime)
        
        # Debug: mostrar algunas fechas procesadas
        fechas_validas = df_processed["fecha_inicio_sintomas"].dropna()
        if not fechas_validas.empty:
            print(f"Fechas procesadas - Mínima: {fechas_validas.min()}, Máxima: {fechas_validas.max()}")

    # Crear grupos de edad
    if "edad" in df_processed.columns:
        df_processed["grupo_edad"] = create_age_groups(df_processed["edad"])

    # Normalizar sexo
    if "sexo" in df_processed.columns:
        df_processed["sexo"] = (
            df_processed["sexo"]
            .str.upper()
            .replace({"M": "Masculino", "F": "Femenino"})
        )

    # Agregar año de inicio de síntomas
    if "fecha_inicio_sintomas" in df_processed.columns:
        df_processed["año_inicio"] = df_processed["fecha_inicio_sintomas"].dt.year

    return df_processed


def process_epizootias_dataframe(df):
    """
    Procesa el dataframe de epizootias con limpieza específica.

    Args:
        df (pd.DataFrame): DataFrame de epizootias

    Returns:
        pd.DataFrame: DataFrame procesado
    """
    df_processed = df.copy()

    # Normalizar municipios y veredas
    if "municipio" in df_processed.columns:
        df_processed["municipio_normalizado"] = df_processed["municipio"].apply(
            normalize_municipio_name
        )
        df_processed["municipio"] = df_processed["municipio"].apply(capitalize_names)

    if "vereda" in df_processed.columns:
        df_processed["vereda_normalizada"] = df_processed["vereda"].apply(
            normalize_text
        )
        df_processed["vereda"] = df_processed["vereda"].apply(capitalize_names)

    # Procesar fechas con formato DD/MM/YYYY
    if "fecha_recoleccion" in df_processed.columns:
        print("Procesando fechas de epizootias...")
        df_processed["fecha_recoleccion"] = df_processed["fecha_recoleccion"].apply(
            excel_date_to_datetime
        )
        
        # Debug: mostrar algunas fechas procesadas
        fechas_validas = df_processed["fecha_recoleccion"].dropna()
        if not fechas_validas.empty:
            print(f"Fechas de epizootias - Mínima: {fechas_validas.min()}, Máxima: {fechas_validas.max()}")

    # Normalizar descripción
    if "descripcion" in df_processed.columns:
        df_processed["descripcion"] = (
            df_processed["descripcion"].str.upper().str.strip()
        )

    # Normalizar proveniente
    if "proveniente" in df_processed.columns:
        df_processed["proveniente"] = df_processed["proveniente"].str.strip()

    # Agregar año de recolección
    if "fecha_recoleccion" in df_processed.columns:
        df_processed["año_recoleccion"] = df_processed["fecha_recoleccion"].dt.year

    # Categorizar resultados
    if "descripcion" in df_processed.columns:
        df_processed["categoria_resultado"] = (
            df_processed["descripcion"]
            .map(
                {
                    "POSITIVO FA": "Positivo",
                    "NEGATIVO FA": "Negativo",
                    "NO APTA": "No apta",
                    "EN ESTUDIO": "En estudio",
                }
            )
            .fillna("Otro")
        )

    return df_processed


def apply_filters_to_data(casos_df, epizootias_df, filters):
    """
    Aplica filtros a ambos dataframes de manera coordinada.

    Args:
        casos_df (pd.DataFrame): DataFrame de casos
        epizootias_df (pd.DataFrame): DataFrame de epizootias
        filters (dict): Diccionario con filtros a aplicar

    Returns:
        tuple: (casos_filtrados, epizootias_filtradas)
    """
    casos_filtrados = casos_df.copy()
    epizootias_filtradas = epizootias_df.copy()

    # Aplicar filtro de municipio
    if filters.get("municipio_normalizado"):
        municipio_norm = filters["municipio_normalizado"]
        casos_filtrados = casos_filtrados[
            casos_filtrados["municipio_normalizado"] == municipio_norm
        ]
        epizootias_filtradas = epizootias_filtradas[
            epizootias_filtradas["municipio_normalizado"] == municipio_norm
        ]

    # Aplicar filtro de vereda
    if filters.get("vereda_normalizada"):
        vereda_norm = filters["vereda_normalizada"]
        casos_filtrados = casos_filtrados[
            casos_filtrados["vereda_normalizada"] == vereda_norm
        ]
        epizootias_filtradas = epizootias_filtradas[
            epizootias_filtradas["vereda_normalizada"] == vereda_norm
        ]

    # Aplicar filtro de fechas
    if filters.get("fecha_rango") and len(filters["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters["fecha_rango"]
        fecha_inicio = pd.Timestamp(fecha_inicio)
        fecha_fin = pd.Timestamp(fecha_fin)

        # Filtrar casos por fecha de inicio de síntomas
        if "fecha_inicio_sintomas" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                (casos_filtrados["fecha_inicio_sintomas"] >= fecha_inicio)
                & (casos_filtrados["fecha_inicio_sintomas"] <= fecha_fin)
            ]

        # Filtrar epizootias por fecha de recolección
        if "fecha_recoleccion" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                (epizootias_filtradas["fecha_recoleccion"] >= fecha_inicio)
                & (epizootias_filtradas["fecha_recoleccion"] <= fecha_fin)
            ]

    return casos_filtrados, epizootias_filtradas


def calculate_basic_metrics(casos_df, epizootias_df):
    """
    Calcula métricas básicas de los datos.

    Args:
        casos_df (pd.DataFrame): DataFrame de casos
        epizootias_df (pd.DataFrame): DataFrame de epizootias

    Returns:
        dict: Diccionario con métricas calculadas
    """
    metrics = {}

    # Métricas de casos
    metrics["total_casos"] = len(casos_df)

    if "condicion_final" in casos_df.columns:
        fallecidos = (casos_df["condicion_final"] == "Fallecido").sum()
        metrics["fallecidos"] = fallecidos
        metrics["vivos"] = (casos_df["condicion_final"] == "Vivo").sum()
        metrics["letalidad"] = (
            (fallecidos / len(casos_df) * 100) if len(casos_df) > 0 else 0
        )
    else:
        metrics["fallecidos"] = 0
        metrics["vivos"] = 0
        metrics["letalidad"] = 0

    # Métricas de epizootias
    metrics["total_epizootias"] = len(epizootias_df)

    if "descripcion" in epizootias_df.columns:
        positivos = (epizootias_df["descripcion"] == "POSITIVO FA").sum()
        metrics["epizootias_positivas"] = positivos
        metrics["positividad"] = (
            (positivos / len(epizootias_df) * 100) if len(epizootias_df) > 0 else 0
        )
    else:
        metrics["epizootias_positivas"] = 0
        metrics["positividad"] = 0

    # Métricas geográficas
    if "municipio_normalizado" in casos_df.columns:
        metrics["municipios_con_casos"] = casos_df["municipio_normalizado"].nunique()
    else:
        metrics["municipios_con_casos"] = 0

    if "municipio_normalizado" in epizootias_df.columns:
        metrics["municipios_con_epizootias"] = epizootias_df[
            "municipio_normalizado"
        ].nunique()
    else:
        metrics["municipios_con_epizootias"] = 0

    return metrics


def get_unique_locations(casos_df, epizootias_df):
    """
    Obtiene ubicaciones únicas de ambas fuentes de datos.

    Args:
        casos_df (pd.DataFrame): DataFrame de casos
        epizootias_df (pd.DataFrame): DataFrame de epizootias

    Returns:
        dict: Diccionario con ubicaciones únicas
    """
    locations = {"municipios": set(), "veredas_por_municipio": {}}

    # Obtener municipios únicos
    if "municipio_normalizado" in casos_df.columns:
        locations["municipios"].update(
            casos_df["municipio_normalizado"].dropna().unique()
        )

    if "municipio_normalizado" in epizootias_df.columns:
        locations["municipios"].update(
            epizootias_df["municipio_normalizado"].dropna().unique()
        )

    locations["municipios"] = sorted(list(locations["municipios"]))

    # Obtener veredas por municipio
    for municipio in locations["municipios"]:
        veredas = set()

        # Veredas de casos
        if "vereda_normalizada" in casos_df.columns:
            veredas_casos = (
                casos_df[casos_df["municipio_normalizado"] == municipio][
                    "vereda_normalizada"
                ]
                .dropna()
                .unique()
            )
            veredas.update(veredas_casos)

        # Veredas de epizootias
        if "vereda_normalizada" in epizootias_df.columns:
            veredas_epi = (
                epizootias_df[epizootias_df["municipio_normalizado"] == municipio][
                    "vereda_normalizada"
                ]
                .dropna()
                .unique()
            )
            veredas.update(veredas_epi)

        locations["veredas_por_municipio"][municipio] = sorted(list(veredas))

    return locations


def validate_data_consistency(casos_df, epizootias_df):
    """
    Valida la consistencia de los datos cargados.

    Args:
        casos_df (pd.DataFrame): DataFrame de casos
        epizootias_df (pd.DataFrame): DataFrame de epizootias

    Returns:
        dict: Reporte de validación
    """
    validation_report = {"casos": {}, "epizootias": {}, "warnings": [], "errors": []}

    # Validar casos
    if not casos_df.empty:
        validation_report["casos"]["total_rows"] = len(casos_df)
        validation_report["casos"]["columns"] = list(casos_df.columns)

        # Verificar fechas válidas
        if "fecha_inicio_sintomas" in casos_df.columns:
            fechas_validas = casos_df["fecha_inicio_sintomas"].notna().sum()
            validation_report["casos"]["fechas_validas"] = fechas_validas
            if fechas_validas == 0:
                validation_report["warnings"].append("No hay fechas válidas en casos")

        # Verificar condición final
        if "condicion_final" in casos_df.columns:
            condiciones_validas = casos_df["condicion_final"].notna().sum()
            validation_report["casos"]["condiciones_validas"] = condiciones_validas

    # Validar epizootias
    if not epizootias_df.empty:
        validation_report["epizootias"]["total_rows"] = len(epizootias_df)
        validation_report["epizootias"]["columns"] = list(epizootias_df.columns)

        # Verificar fechas válidas
        if "fecha_recoleccion" in epizootias_df.columns:
            fechas_validas = epizootias_df["fecha_recoleccion"].notna().sum()
            validation_report["epizootias"]["fechas_validas"] = fechas_validas
            if fechas_validas == 0:
                validation_report["warnings"].append(
                    "No hay fechas válidas en epizootias"
                )

    return validation_report


def create_summary_by_location(casos_df, epizootias_df):
    """
    Crea resumen de datos por ubicación.

    Args:
        casos_df (pd.DataFrame): DataFrame de casos
        epizootias_df (pd.DataFrame): DataFrame de epizootias

    Returns:
        pd.DataFrame: DataFrame con resumen por ubicación
    """
    summary_data = []

    # Obtener todas las ubicaciones únicas
    locations = get_unique_locations(casos_df, epizootias_df)

    for municipio in locations["municipios"]:
        # Casos en el municipio
        casos_municipio = (
            casos_df[casos_df["municipio_normalizado"] == municipio]
            if "municipio_normalizado" in casos_df.columns
            else pd.DataFrame()
        )
        epizootias_municipio = (
            epizootias_df[epizootias_df["municipio_normalizado"] == municipio]
            if "municipio_normalizado" in epizootias_df.columns
            else pd.DataFrame()
        )

        # Calcular métricas
        total_casos = len(casos_municipio)
        total_epizootias = len(epizootias_municipio)

        fallecidos = 0
        if not casos_municipio.empty and "condicion_final" in casos_municipio.columns:
            fallecidos = (casos_municipio["condicion_final"] == "Fallecido").sum()

        positivos = 0
        if (
            not epizootias_municipio.empty
            and "descripcion" in epizootias_municipio.columns
        ):
            positivos = (epizootias_municipio["descripcion"] == "POSITIVO FA").sum()

        summary_data.append(
            {
                "municipio": municipio,
                "total_casos": total_casos,
                "fallecidos": fallecidos,
                "letalidad": (fallecidos / total_casos * 100) if total_casos > 0 else 0,
                "total_epizootias": total_epizootias,
                "epizootias_positivas": positivos,
                "positividad": (
                    (positivos / total_epizootias * 100) if total_epizootias > 0 else 0
                ),
                "veredas_afectadas": len(
                    locations["veredas_por_municipio"].get(municipio, [])
                ),
            }
        )

    return pd.DataFrame(summary_data).sort_values("total_casos", ascending=False)


def prepare_dataframe_for_display(df, date_columns=None):
    """
    Prepara un DataFrame para mostrar en la interfaz, formateando fechas y nombres.

    Args:
        df (pd.DataFrame): DataFrame a preparar
        date_columns (list): Lista de columnas de fecha a formatear

    Returns:
        pd.DataFrame: DataFrame preparado para mostrar
    """
    if df.empty:
        return df

    df_display = df.copy()

    # Formatear columnas de fecha si se especifican
    if date_columns:
        for col in date_columns:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(format_date_display)
    else:
        # Detectar automáticamente columnas de fecha
        for col in df_display.columns:
            if "fecha" in col.lower() and df_display[col].dtype == "datetime64[ns]":
                df_display[col] = df_display[col].apply(format_date_display)

    return df_display