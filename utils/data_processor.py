"""
Procesamiento y filtrado de datos del dashboard.
"""

import pandas as pd
import numpy as np
from config.settings import FILTER_MAPPINGS, CASOS_CONFIRMADOS


def apply_filters(data, filters):
    """
    Aplica los filtros seleccionados a los datos.

    Args:
        data (dict): Diccionario con los dataframes originales.
        filters (dict): Diccionario con los filtros a aplicar.

    Returns:
        dict: Diccionario con los dataframes filtrados.
    """
    # Crear copias para no modificar los originales
    filtered_data = {
        "fiebre": data["fiebre"].copy(),
        "departamentos": data["departamentos"].copy(),
        "metricas": data["metricas"].copy(),
    }

    # Filtro por año
    if (
        filters.get("año", "Todos") != "Todos"
        and "año" in filtered_data["fiebre"].columns
    ):
        año_filtro = filters["año"]
        if str(año_filtro).isdigit():
            filtered_data["fiebre"] = filtered_data["fiebre"][
                filtered_data["fiebre"]["año"] == int(año_filtro)
            ]
        else:
            filtered_data["fiebre"] = filtered_data["fiebre"][
                filtered_data["fiebre"]["año"] == año_filtro
            ]

    # Filtro por tipo de caso
    if (
        filters.get("tipo_caso", "Todos") != "Todos"
        and "tip_cas_" in filtered_data["fiebre"].columns
    ):
        tipo_filtro = filters["tipo_caso"]
        # Usar mapeo inverso para obtener el código
        tipo_mapping_inv = {v: k for k, v in FILTER_MAPPINGS["tipo_caso"].items()}

        if tipo_filtro in tipo_mapping_inv:
            filtered_data["fiebre"] = filtered_data["fiebre"][
                filtered_data["fiebre"]["tip_cas_"] == tipo_mapping_inv[tipo_filtro]
            ]

    # Filtro por departamento
    if (
        filters.get("departamento", "Todos") != "Todos"
        and "ndep_resi" in filtered_data["fiebre"].columns
    ):
        filtered_data["fiebre"] = filtered_data["fiebre"][
            filtered_data["fiebre"]["ndep_resi"].str.upper()
            == filters["departamento"].upper()
        ]

    # Filtro por municipio
    if (
        filters.get("municipio", "Todos") != "Todos"
        and "nmun_resi" in filtered_data["fiebre"].columns
    ):
        filtered_data["fiebre"] = filtered_data["fiebre"][
            filtered_data["fiebre"]["nmun_resi"] == filters["municipio"]
        ]

    # Filtro por tipo de seguridad social
    if (
        filters.get("tipo_ss", "Todos") != "Todos"
        and "tip_ss_" in filtered_data["fiebre"].columns
    ):
        tipo_ss_filtro = filters["tipo_ss"]
        if " - " in tipo_ss_filtro:
            codigo = tipo_ss_filtro.split(" - ")[0]
            filtered_data["fiebre"] = filtered_data["fiebre"][
                filtered_data["fiebre"]["tip_ss_"].astype(str) == codigo
            ]
        else:
            filtered_data["fiebre"] = filtered_data["fiebre"][
                filtered_data["fiebre"]["tip_ss_"] == tipo_ss_filtro
            ]

    # Filtro por sexo
    if (
        filters.get("sexo", "Todos") != "Todos"
        and "sexo_" in filtered_data["fiebre"].columns
    ):
        filtered_data["fiebre"] = filtered_data["fiebre"][
            filtered_data["fiebre"]["sexo_"] == filters["sexo"]
        ]

    # Recalcular métricas con datos filtrados
    from .metrics_calculator import calculate_metrics

    filtered_data["metricas"] = calculate_metrics(filtered_data["fiebre"])

    # Recalcular datos departamentales
    if (
        "cod_dpto_r" in filtered_data["fiebre"].columns
        and "ndep_resi" in filtered_data["fiebre"].columns
    ):
        filtered_data["departamentos"] = (
            filtered_data["fiebre"]
            .groupby(["cod_dpto_r", "ndep_resi"])
            .size()
            .reset_index()
        )
        filtered_data["departamentos"].columns = ["cod_dpto", "departamento", "casos"]

    return filtered_data


def process_dataframe(df, clean_columns=True, normalize_text=True):
    """
    Procesa un dataframe con operaciones comunes de limpieza.

    Args:
        df (pd.DataFrame): DataFrame a procesar
        clean_columns (bool): Si limpiar nombres de columnas
        normalize_text (bool): Si normalizar texto

    Returns:
        pd.DataFrame: DataFrame procesado
    """
    df_processed = df.copy()

    if clean_columns:
        # Normalizar nombres de columnas (quitar espacios)
        df_processed.columns = [col.strip() for col in df_processed.columns]

    if normalize_text:
        # Normalizar columnas de texto
        text_columns = df_processed.select_dtypes(include=["object"]).columns
        for col in text_columns:
            if df_processed[col].dtype == "object":
                df_processed[col] = (
                    df_processed[col].astype(str).str.strip().str.upper()
                )

    return df_processed


def create_age_groups(ages, custom_ranges=None):
    """
    Crea grupos de edad a partir de una serie de edades.

    Args:
        ages (pd.Series): Serie con las edades
        custom_ranges (list): Rangos personalizados de edad

    Returns:
        pd.Series: Serie con los grupos de edad
    """

    def classify_age(age):
        if pd.isna(age):
            return "No especificado"
        elif age < 5:
            return "0-4 años"
        elif age < 15:
            return "5-14 años"
        elif age < 20:
            return "15-19 años"
        elif age < 30:
            return "20-29 años"
        elif age < 40:
            return "30-39 años"
        elif age < 50:
            return "40-49 años"
        elif age < 60:
            return "50-59 años"
        elif age < 70:
            return "60-69 años"
        elif age < 80:
            return "70-79 años"
        else:
            return "80+ años"

    return ages.apply(classify_age)


def calculate_time_differences(df, date_columns):
    """
    Calcula diferencias de tiempo entre fechas.

    Args:
        df (pd.DataFrame): DataFrame con columnas de fechas
        date_columns (list): Lista de columnas de fechas

    Returns:
        pd.DataFrame: DataFrame con columnas de diferencias calculadas
    """
    df_dates = df.copy()

    # Convertir columnas a datetime
    for col in date_columns:
        if col in df_dates.columns:
            df_dates[col] = pd.to_datetime(df_dates[col], errors="coerce")

    # Calcular diferencias específicas
    if "ini_sin_" in df_dates.columns and "fec_con_" in df_dates.columns:
        df_dates["dias_sintomas_a_consulta"] = (
            df_dates["fec_con_"] - df_dates["ini_sin_"]
        ).dt.days

    if "ini_sin_" in df_dates.columns and "fec_hos_" in df_dates.columns:
        df_dates["dias_sintomas_a_hospitalizacion"] = (
            df_dates["fec_hos_"] - df_dates["ini_sin_"]
        ).dt.days

    if "ini_sin_" in df_dates.columns and "fec_def_" in df_dates.columns:
        df_dates["dias_sintomas_a_fallecimiento"] = (
            df_dates["fec_def_"] - df_dates["ini_sin_"]
        ).dt.days

    return df_dates


def filter_valid_time_differences(df, time_columns, min_days=0, max_days=60):
    """
    Filtra diferencias de tiempo válidas.

    Args:
        df (pd.DataFrame): DataFrame con columnas de tiempo
        time_columns (list): Lista de columnas de tiempo a filtrar
        min_days (int): Días mínimos válidos
        max_days (int): Días máximos válidos

    Returns:
        pd.DataFrame: DataFrame con valores filtrados
    """
    df_filtered = df.copy()

    for col in time_columns:
        if col in df_filtered.columns:
            df_filtered[col] = df_filtered[col].apply(
                lambda x: x if (x is not None and min_days <= x <= max_days) else None
            )

    return df_filtered
