"""
Calculadora de métricas epidemiológicas.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from config.settings import CASOS_CONFIRMADOS

def calculate_metrics(df):
    """
    Calcula métricas generales sobre los datos de fiebre amarilla.
    
    Args:
        df (DataFrame): DataFrame con los datos de fiebre amarilla.
        
    Returns:
        DataFrame: DataFrame con las métricas calculadas.
    """
    # Total de casos
    total_casos = len(df)
    
    # Casos por tipo
    if 'tip_cas_' in df.columns:
        casos_tipo = df['tip_cas_'].value_counts().to_dict()
    else:
        casos_tipo = {"No disponible": total_casos}
    
    # Casos por condición final
    if 'con_fin_' in df.columns:
        condicion_final = df['con_fin_'].value_counts().to_dict()
        # Calcular tasa de letalidad
        fallecidos = condicion_final.get(2, 0)  # 2 = Fallecido
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
    else:
        condicion_final = {"No disponible": total_casos}
        letalidad = 0
    
    # Casos confirmados
    confirmados = 0
    if 'tip_cas_' in df.columns:
        confirmados = df[df['tip_cas_'].isin(CASOS_CONFIRMADOS)].shape[0]
    
    # Crear diccionario con todas las métricas
    metricas_dict = {
        "total_casos": [total_casos],
        "confirmados": [confirmados],
        "letalidad": [letalidad],
        "fecha_actualizacion": [datetime.now().strftime("%Y-%m-%d %H:%M")]
    }
    
    return pd.DataFrame(metricas_dict)


def calculate_confirmed_metrics(df):
    """
    Calcula métricas específicas para casos confirmados.
    
    Args:
        df (DataFrame): DataFrame con los datos de fiebre amarilla.
        
    Returns:
        dict: Diccionario con métricas de casos confirmados.
    """
    metrics = {}
    
    # Verificar columnas necesarias
    has_tipo_caso = "tip_cas_" in df.columns
    has_condicion_final = "con_fin_" in df.columns
    has_recuperados = "est_rec_" in df.columns
    
    if not has_tipo_caso:
        return metrics
    
    # Filtrar casos confirmados
    df_confirmados = df[df["tip_cas_"].isin(CASOS_CONFIRMADOS)]
    total_confirmados = len(df_confirmados)
    
    metrics["total_confirmados"] = total_confirmados
    
    if has_condicion_final:
        # Fallecidos confirmados
        fallecidos_confirmados = df_confirmados[df_confirmados["con_fin_"] == 2].shape[0]
        metrics["fallecidos_confirmados"] = fallecidos_confirmados
        
        # Letalidad en confirmados
        letalidad_confirmados = (fallecidos_confirmados / total_confirmados * 100) if total_confirmados > 0 else 0
        metrics["letalidad_confirmados"] = letalidad_confirmados
        
        # Casos activos
        if has_recuperados:
            recuperados = df_confirmados[df_confirmados["est_rec_"] == 1].shape[0]
            metrics["recuperados"] = recuperados
            activos = total_confirmados - fallecidos_confirmados - recuperados
        else:
            metrics["recuperados"] = 0
            activos = total_confirmados - fallecidos_confirmados
        
        metrics["activos"] = max(0, activos)
    
    return metrics


def calculate_active_cases(df):
    """
    Calcula y filtra casos activos.
    
    Args:
        df (DataFrame): DataFrame con los datos de fiebre amarilla.
        
    Returns:
        DataFrame: DataFrame solo con casos activos.
    """
    if "tip_cas_" not in df.columns or "con_fin_" not in df.columns:
        return pd.DataFrame()
    
    # Filtrar casos confirmados y no fallecidos
    df_activos = df[
        df["tip_cas_"].isin(CASOS_CONFIRMADOS) & 
        (df["con_fin_"] != 2)
    ]
    
    # Si existe columna de recuperados, excluir recuperados
    if "est_rec_" in df.columns:
        df_activos = df_activos[df_activos["est_rec_"] != 1]
    
    return df_activos


def calculate_temporal_metrics(df, date_column="ini_sin_"):
    """
    Calcula métricas temporales.
    
    Args:
        df (DataFrame): DataFrame con los datos
        date_column (str): Columna de fecha a analizar
        
    Returns:
        dict: Diccionario con métricas temporales
    """
    metrics = {}
    
    if date_column not in df.columns:
        return metrics
    
    # Convertir a datetime
    df_temp = df.copy()
    df_temp[date_column] = pd.to_datetime(df_temp[date_column], errors='coerce')
    df_temp = df_temp.dropna(subset=[date_column])
    
    if df_temp.empty:
        return metrics
    
    # Rango de fechas
    fecha_min = df_temp[date_column].min()
    fecha_max = df_temp[date_column].max()
    
    metrics["fecha_primer_caso"] = fecha_min
    metrics["fecha_ultimo_caso"] = fecha_max
    metrics["rango_dias"] = (fecha_max - fecha_min).days
    
    # Casos por año
    df_temp["año"] = df_temp[date_column].dt.year
    casos_por_año = df_temp["año"].value_counts().to_dict()
    metrics["casos_por_año"] = casos_por_año
    
    # Casos por mes
    df_temp["mes"] = df_temp[date_column].dt.month
    casos_por_mes = df_temp["mes"].value_counts().to_dict()
    metrics["casos_por_mes"] = casos_por_mes
    
    return metrics


def calculate_geographic_metrics(df, depto_col="ndep_resi", muni_col="nmun_resi"):
    """
    Calcula métricas geográficas.
    
    Args:
        df (DataFrame): DataFrame con los datos
        depto_col (str): Columna de departamento
        muni_col (str): Columna de municipio
        
    Returns:
        dict: Diccionario con métricas geográficas
    """
    metrics = {}
    
    if depto_col in df.columns:
        # Departamentos afectados
        deptos_unicos = df[depto_col].nunique()
        metrics["departamentos_afectados"] = deptos_unicos
        
        # Departamento con más casos
        depto_top = df[depto_col].value_counts()
        if not depto_top.empty:
            metrics["departamento_mas_casos"] = depto_top.index[0]
            metrics["casos_departamento_top"] = depto_top.iloc[0]
    
    if muni_col in df.columns:
        # Municipios afectados
        munis_unicos = df[muni_col].nunique()
        metrics["municipios_afectados"] = munis_unicos
        
        # Municipio con más casos
        muni_top = df[muni_col].value_counts()
        if not muni_top.empty:
            metrics["municipio_mas_casos"] = muni_top.index[0]
            metrics["casos_municipio_top"] = muni_top.iloc[0]
    
    return metrics


def calculate_demographic_metrics(df):
    """
    Calcula métricas demográficas.
    
    Args:
        df (DataFrame): DataFrame con los datos
        
    Returns:
        dict: Diccionario con métricas demográficas
    """
    metrics = {}
    
    # Distribución por sexo
    if "sexo_" in df.columns:
        sexo_dist = df["sexo_"].value_counts(normalize=True).to_dict()
        metrics["distribucion_sexo"] = sexo_dist
    
    # Estadísticas de edad
    if "edad_" in df.columns:
        edad_stats = {
            "edad_promedio": df["edad_"].mean(),
            "edad_mediana": df["edad_"].median(),
            "edad_min": df["edad_"].min(),
            "edad_max": df["edad_"].max(),
            "edad_std": df["edad_"].std()
        }
        metrics["estadisticas_edad"] = edad_stats
    
    # Distribución por pertenencia étnica
    if "per_etn_" in df.columns:
        etnia_dist = df["per_etn_"].value_counts().to_dict()
        metrics["distribucion_etnica"] = etnia_dist
    
    return metrics