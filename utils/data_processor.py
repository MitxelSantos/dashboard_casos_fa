"""
utils/data_processor.py
"""

import pandas as pd
import numpy as np
import unicodedata
import re
import logging
from datetime import datetime
from config.settings import GRUPOS_EDAD, CONDICION_FINAL_MAP, DESCRIPCION_EPIZOOTIAS_MAP

logger = logging.getLogger(__name__)

# ===== FUNCIONES CORE DE FECHAS =====

def excel_date_to_datetime(excel_date):
    """Convierte fecha de Excel a datetime con manejo robusto."""
    try:
        if isinstance(excel_date, (pd.Timestamp, datetime)):
            return excel_date
        
        if pd.isna(excel_date) or excel_date == "":
            return None

        if isinstance(excel_date, str):
            excel_date = excel_date.strip()
            if not excel_date or excel_date.lower() in ['nan', 'none', 'null']:
                return None
                
            formatos_fecha = [
                "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y",
                "%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y",
            ]
            
            for formato in formatos_fecha:
                try:
                    fecha_convertida = datetime.strptime(excel_date, formato)
                    if fecha_convertida.year < 50:
                        fecha_convertida = fecha_convertida.replace(year=fecha_convertida.year + 2000)
                    elif fecha_convertida.year < 100:
                        fecha_convertida = fecha_convertida.replace(year=fecha_convertida.year + 1900)
                    return fecha_convertida
                except ValueError:
                    continue
            
            try:
                return pd.to_datetime(excel_date, dayfirst=True, errors="coerce")
            except:
                return None

        if isinstance(excel_date, (int, float)):
            if pd.isna(excel_date) or excel_date < 0 or excel_date > 100000:
                return None
            try:
                return pd.to_datetime(excel_date, origin="1899-12-30", unit="D")
            except:
                return None

        return None
        
    except Exception as e:
        logger.warning(f"Error procesando fecha: {excel_date} - {str(e)}")
        return None

def format_date_display(date_value):
    """Formatea una fecha para mostrar."""
    if pd.isna(date_value):
        return ""
    try:
        if isinstance(date_value, (pd.Timestamp, datetime)):
            return date_value.strftime("%Y-%m-%d")
        else:
            converted_date = excel_date_to_datetime(date_value)
            return converted_date.strftime("%Y-%m-%d") if converted_date else ""
    except Exception as e:
        logger.warning(f"Error formateando fecha {date_value}: {e}")
        return ""

def calculate_days_since(date_value):
    """Calcula los días transcurridos desde una fecha hasta hoy."""
    if pd.isna(date_value):
        return None
    
    try:
        if isinstance(date_value, (pd.Timestamp, datetime)):
            fecha = date_value
        else:
            fecha = excel_date_to_datetime(date_value)
        
        if fecha:
            hoy = datetime.now()
            delta = hoy - fecha
            return delta.days
        return None
    except:
        return None

def format_time_elapsed(days):
    """Formatea tiempo transcurrido en formato legible."""
    if days is None or days < 0:
        return "Fecha inválida"
    
    if days == 0:
        return "Hoy"
    elif days == 1:
        return "Ayer"
    elif days < 7:
        return f"{days} días"
    elif days < 30:
        semanas = days // 7
        return f"{semanas} semana{'s' if semanas > 1 else ''}"
    elif days < 365:
        meses = days // 30
        return f"{meses} mes{'es' if meses > 1 else ''}"
    else:
        años = days // 365
        return f"{años} año{'s' if años > 1 else ''}"

# ===== FUNCIONES CORE DE CÁLCULO =====

def get_latest_case_info(casos_df, date_column, location_columns=None):
    """Obtiene información del caso más reciente."""
    if casos_df.empty or date_column not in casos_df.columns:
        return {
            "existe": False,
            "fecha": None,
            "ubicacion": "Sin datos",
            "dias_transcurridos": None,
            "tiempo_transcurrido": "Sin datos"
        }
    
    df_with_dates = casos_df.dropna(subset=[date_column])
    
    if df_with_dates.empty:
        return {
            "existe": False,
            "fecha": None,
            "ubicacion": "Sin fechas válidas",
            "dias_transcurridos": None,
            "tiempo_transcurrido": "Sin fechas válidas"
        }
    
    latest_idx = df_with_dates[date_column].idxmax()
    latest_record = df_with_dates.loc[latest_idx]
    
    fecha = latest_record[date_column]
    dias = calculate_days_since(fecha)
    tiempo_transcurrido = format_time_elapsed(dias)
    
    ubicacion_parts = []
    if location_columns:
        for col in location_columns:
            if col in latest_record and pd.notna(latest_record[col]):
                ubicacion_parts.append(str(latest_record[col]))
    
    ubicacion = " - ".join(ubicacion_parts) if ubicacion_parts else "Ubicación no especificada"
    
    return {
        "existe": True,
        "fecha": fecha,
        "ubicacion": ubicacion,
        "dias_transcurridos": dias,
        "tiempo_transcurrido": tiempo_transcurrido
    }

def calculate_basic_metrics(casos_df, epizootias_df):
    """Calcula métricas básicas de los datos."""
    logger.info(f"Calculando métricas: {len(casos_df)} casos, {len(epizootias_df)} epizootias")
    
    if not isinstance(casos_df, pd.DataFrame):
        casos_df = pd.DataFrame()
    if not isinstance(epizootias_df, pd.DataFrame):
        epizootias_df = pd.DataFrame()
    
    metrics = {}

    # Métricas de casos
    metrics["total_casos"] = len(casos_df)

    if "condicion_final" in casos_df.columns and not casos_df.empty:
        fallecidos = (casos_df["condicion_final"] == "Fallecido").sum()
        vivos = (casos_df["condicion_final"] == "Vivo").sum()
        metrics["fallecidos"] = fallecidos
        metrics["vivos"] = vivos
        metrics["letalidad"] = (fallecidos / len(casos_df) * 100) if len(casos_df) > 0 else 0
    else:
        metrics["fallecidos"] = 0
        metrics["vivos"] = 0
        metrics["letalidad"] = 0

    # Información del último caso
    if not casos_df.empty:
        ultimo_caso = get_latest_case_info(casos_df, "fecha_inicio_sintomas", ["vereda", "municipio"])
        metrics["ultimo_caso"] = ultimo_caso
    else:
        metrics["ultimo_caso"] = {"existe": False}

    # Métricas de epizootias
    metrics["total_epizootias"] = len(epizootias_df)

    if "descripcion" in epizootias_df.columns and not epizootias_df.empty:
        positivos = (epizootias_df["descripcion"] == "POSITIVO FA").sum()
        en_estudio = (epizootias_df["descripcion"] == "EN ESTUDIO").sum()
        
        metrics["epizootias_positivas"] = positivos
        metrics["epizootias_en_estudio"] = en_estudio
        metrics["positividad"] = (positivos / len(epizootias_df) * 100) if len(epizootias_df) > 0 else 0
    else:
        metrics["epizootias_positivas"] = 0
        metrics["epizootias_en_estudio"] = 0
        metrics["positividad"] = 0

    # Información de la última epizootia positiva
    if not epizootias_df.empty:
        epizootias_positivas = epizootias_df[epizootias_df["descripcion"] == "POSITIVO FA"] if "descripcion" in epizootias_df.columns else pd.DataFrame()
        ultima_epizootia = get_latest_case_info(epizootias_positivas, "fecha_recoleccion", ["vereda", "municipio"])
        metrics["ultima_epizootia_positiva"] = ultima_epizootia
    else:
        metrics["ultima_epizootia_positiva"] = {"existe": False}

    # Métricas geográficas
    if "municipio" in casos_df.columns and not casos_df.empty:
        metrics["municipios_con_casos"] = casos_df["municipio"].nunique()
    else:
        metrics["municipios_con_casos"] = 0

    if "municipio" in epizootias_df.columns and not epizootias_df.empty:
        metrics["municipios_con_epizootias"] = epizootias_df["municipio"].nunique()
    else:
        metrics["municipios_con_epizootias"] = 0

    return metrics

# ===== FUNCIONES DE PROCESAMIENTO =====

def create_age_groups(ages):
    """Crea grupos de edad a partir de una serie de edades."""
    def classify_age(age):
        if pd.isna(age):
            return "No especificado"

        age = int(age) if not pd.isna(age) else 0

        for grupo in GRUPOS_EDAD:
            if grupo["min"] <= age <= grupo["max"]:
                return grupo["label"]

        return "No especificado"

    return ages.apply(classify_age)

def process_casos_dataframe(casos_df):
    """Procesa el dataframe de casos."""
    df_processed = casos_df.copy()

    # Procesar fechas
    if "fecha_inicio_sintomas" in df_processed.columns:
        df_processed["fecha_inicio_sintomas"] = df_processed["fecha_inicio_sintomas"].apply(excel_date_to_datetime)

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

def process_epizootias_dataframe(epizootias_df):
    """Procesa el dataframe de epizootias."""
    df_processed = epizootias_df.copy()

    # Procesar fechas
    if "fecha_recoleccion" in df_processed.columns:
        df_processed["fecha_recoleccion"] = df_processed["fecha_recoleccion"].apply(excel_date_to_datetime)

    # Limpiar descripción
    if "descripcion" in df_processed.columns:
        df_processed["descripcion"] = df_processed["descripcion"].str.upper().str.strip()

    # Limpiar proveniente
    if "proveniente" in df_processed.columns:
        df_processed["proveniente"] = df_processed["proveniente"].str.strip()

    # Agregar año de recolección
    if "fecha_recoleccion" in df_processed.columns:
        df_processed["año_recoleccion"] = df_processed["fecha_recoleccion"].dt.year

    # Categorizar resultados
    if "descripcion" in df_processed.columns:
        df_processed["categoria_resultado"] = (
            df_processed["descripcion"]
            .map({
                "POSITIVO FA": "Positivo",
                "NEGATIVO FA": "Negativo", 
                "NO APTA": "No apta",
                "EN ESTUDIO": "En Estudio",
            })
            .fillna("Otro")
        )

    return df_processed

# ===== FUNCIONES DE ANÁLISIS =====

def get_unique_locations(casos_df, epizootias_df):
    """Obtiene ubicaciones únicas de los datos."""
    locations = {"municipios": set(), "veredas_por_municipio": {}}

    # Obtener municipios únicos
    if "municipio" in casos_df.columns:
        locations["municipios"].update(casos_df["municipio"].dropna().unique())

    if "municipio" in epizootias_df.columns:
        locations["municipios"].update(epizootias_df["municipio"].dropna().unique())

    locations["municipios"] = sorted(list(locations["municipios"]))

    # Obtener veredas por municipio
    for municipio in locations["municipios"]:
        veredas = set()

        if "vereda" in casos_df.columns:
            veredas_casos = casos_df[casos_df["municipio"] == municipio]["vereda"].dropna().unique()
            veredas.update(veredas_casos)

        if "vereda" in epizootias_df.columns:
            veredas_epi = epizootias_df[epizootias_df["municipio"] == municipio]["vereda"].dropna().unique()
            veredas.update(veredas_epi)

        locations["veredas_por_municipio"][municipio] = sorted(list(veredas))

    return locations

def create_summary_by_location(casos_df, epizootias_df):
    """Crea resumen por ubicación."""
    summary_data = []
    locations = get_unique_locations(casos_df, epizootias_df)

    for municipio in locations["municipios"]:
        casos_municipio = casos_df[casos_df["municipio"] == municipio] if "municipio" in casos_df.columns else pd.DataFrame()
        epizootias_municipio = epizootias_df[epizootias_df["municipio"] == municipio] if "municipio" in epizootias_df.columns else pd.DataFrame()

        total_casos = len(casos_municipio)
        total_epizootias = len(epizootias_municipio)

        fallecidos = 0
        if not casos_municipio.empty and "condicion_final" in casos_municipio.columns:
            fallecidos = (casos_municipio["condicion_final"] == "Fallecido").sum()

        positivos = 0
        en_estudio = 0
        if not epizootias_municipio.empty and "descripcion" in epizootias_municipio.columns:
            positivos = (epizootias_municipio["descripcion"] == "POSITIVO FA").sum()
            en_estudio = (epizootias_municipio["descripcion"] == "EN ESTUDIO").sum()

        summary_data.append({
            "municipio": municipio,
            "total_casos": total_casos,
            "fallecidos": fallecidos,
            "letalidad": (fallecidos / total_casos * 100) if total_casos > 0 else 0,
            "total_epizootias": total_epizootias,
            "epizootias_positivas": positivos,
            "epizootias_en_estudio": en_estudio,
            "positividad": (positivos / total_epizootias * 100) if total_epizootias > 0 else 0,
            "veredas_afectadas": len(locations["veredas_por_municipio"].get(municipio, [])),
        })

    return pd.DataFrame(summary_data).sort_values("total_casos", ascending=False)

def prepare_dataframe_for_display(df, date_columns=None):
    """Prepara DataFrame para mostrar."""
    if df.empty:
        return df

    df_display = df.copy()

    # Formatear columnas de fecha
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

# ===== FUNCIONES DE DEBUGGING SIMPLIFICADAS =====

def debug_data_flow(data_original, data_filtered, filters, stage="unknown"):
    """Debug simplificado del flujo de datos."""
    if isinstance(data_original, dict) and isinstance(data_filtered, dict):
        casos_orig = len(data_original.get("casos", []))
        epi_orig = len(data_original.get("epizootias", []))
        casos_filt = len(data_filtered.get("casos", []))
        epi_filt = len(data_filtered.get("epizootias", []))
        
        logger.info(f"Debug {stage}: Casos {casos_orig}→{casos_filt}, Epizootias {epi_orig}→{epi_filt}")
        
        active_filters = filters.get("active_filters", []) if isinstance(filters, dict) else []
        if active_filters:
            logger.info(f"Filtros activos: {len(active_filters)}")

def verify_filtered_data_usage(data, context=""):
    """Verifica que se estén usando datos filtrados."""
    if data is None:
        logger.warning(f"⚠️ {context}: Datos nulos")
        return False
    
    total_rows = len(data)
    logger.debug(f"✅ {context}: {total_rows} registros")
    return True