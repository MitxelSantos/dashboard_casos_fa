"""
Procesamiento y filtrado de datos MEJORADO del dashboard de Fiebre Amarilla.
ACTUALIZADO: Integración con sistema de mapeo automático y manejo robusto de datos
"""

import pandas as pd
import numpy as np
import unicodedata
import re
import logging
from datetime import datetime
from config.settings import GRUPOS_EDAD, CONDICION_FINAL_MAP, DESCRIPCION_EPIZOOTIAS_MAP

# Configurar logging
logger = logging.getLogger(__name__)

# Importación opcional para fuzzy matching
try:
    from fuzzywuzzy import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# Importación del sistema de mapeos automáticos (se actualiza después de generar)
try:
    from utils.automatic_mappings import (
        apply_shapefile_mapping_safe,
        get_municipio_mapping,
        get_vereda_mapping,
        safe_normalize_text
    )
    MAPPING_SYSTEM_AVAILABLE = True
    logger.info("✅ Sistema de mapeos automáticos cargado")
except ImportError:
    MAPPING_SYSTEM_AVAILABLE = False
    logger.warning("⚠️ Sistema de mapeos automáticos no disponible")

def capitalize_names(text):
    """
    MEJORADO: Convierte texto a formato de nombres propios con manejo robusto.
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""

    # Limpiar texto primero
    text = text.strip()
    
    if not text:
        return ""

    # Palabras que deben mantenerse en minúscula (preposiciones, artículos)
    lowercase_words = {"de", "del", "la", "las", "el", "los", "y", "e", "o", "u"}

    try:
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
        
    except Exception as e:
        logger.warning(f"Error capitalizando '{text}': {e}")
        return text


def excel_date_to_datetime(excel_date):
    """
    MEJORADO: Convierte fecha de Excel a datetime con manejo más robusto.
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
            # Limpiar string primero
            excel_date = excel_date.strip()
            if not excel_date or excel_date.lower() in ['nan', 'none', 'null']:
                return None
                
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
                    fecha_convertida = datetime.strptime(excel_date, formato)
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
            # Validar que sea un número razonable
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
    """
    MEJORADO: Formatea una fecha para mostrar con manejo de errores.
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
    except Exception as e:
        logger.warning(f"Error formateando fecha {date_value}: {e}")
        return ""
    
def process_casos_dataframe(df):
    """
    SIMPLIFICADO: Procesa el dataframe de casos sin normalización.
    """
    df_processed = df.copy()

    # ELIMINADO: No más normalización de municipios y veredas
    # Los nombres ya coinciden con los shapefiles

    # Procesar fechas (mantener)
    if "fecha_inicio_sintomas" in df_processed.columns:
        logger.info("📅 Procesando fechas de casos...")
        df_processed["fecha_inicio_sintomas"] = df_processed["fecha_inicio_sintomas"].apply(excel_date_to_datetime)

    # Crear grupos de edad (mantener)
    if "edad" in df_processed.columns:
        df_processed["grupo_edad"] = create_age_groups(df_processed["edad"])

    # Normalizar sexo (mantener - es simple)
    if "sexo" in df_processed.columns:
        df_processed["sexo"] = (
            df_processed["sexo"]
            .str.upper()
            .replace({"M": "Masculino", "F": "Femenino"})
        )

    # Agregar año de inicio de síntomas (mantener)
    if "fecha_inicio_sintomas" in df_processed.columns:
        df_processed["año_inicio"] = df_processed["fecha_inicio_sintomas"].dt.year

    return df_processed

# Las demás funciones permanecen igual...
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


def get_latest_case_info(df, date_column, location_columns=None):
    """Obtiene información del caso más reciente."""
    if df.empty or date_column not in df.columns:
        return {
            "existe": False,
            "fecha": None,
            "ubicacion": "Sin datos",
            "dias_transcurridos": None,
            "tiempo_transcurrido": "Sin datos"
        }
    
    # Filtrar solo registros con fecha válida
    df_with_dates = df.dropna(subset=[date_column])
    
    if df_with_dates.empty:
        return {
            "existe": False,
            "fecha": None,
            "ubicacion": "Sin fechas válidas",
            "dias_transcurridos": None,
            "tiempo_transcurrido": "Sin fechas válidas"
        }
    
    # Obtener el registro más reciente
    latest_idx = df_with_dates[date_column].idxmax()
    latest_record = df_with_dates.loc[latest_idx]
    
    fecha = latest_record[date_column]
    dias = calculate_days_since(fecha)
    tiempo_transcurrido = format_time_elapsed(dias)
    
    # Construir información de ubicación
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

def process_epizootias_dataframe(df):
    """
    SIMPLIFICADO: Procesa el dataframe de epizootias sin normalización.
    """
    df_processed = df.copy()

    # ELIMINADO: No más normalización de municipios y veredas
    # Los nombres ya coinciden con los shapefiles

    # Procesar fechas (mantener)
    if "fecha_recoleccion" in df_processed.columns:
        logger.info("📅 Procesando fechas de epizootias...")
        df_processed["fecha_recoleccion"] = df_processed["fecha_recoleccion"].apply(excel_date_to_datetime)

    # Limpiar descripción (mantener pero simplificar)
    if "descripcion" in df_processed.columns:
        df_processed["descripcion"] = df_processed["descripcion"].str.upper().str.strip()

    # Limpiar proveniente (mantener)
    if "proveniente" in df_processed.columns:
        df_processed["proveniente"] = df_processed["proveniente"].str.strip()

    # Agregar año de recolección (mantener)
    if "fecha_recoleccion" in df_processed.columns:
        df_processed["año_recoleccion"] = df_processed["fecha_recoleccion"].dt.year

    # Categorizar resultados (mantener)
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

def apply_filters_to_data(casos_df, epizootias_df, filters):
    """
    SIMPLIFICADO: Aplica filtros usando nombres directos.
    """
    casos_filtrados = casos_df.copy()
    epizootias_filtradas = epizootias_df.copy()

    # Aplicar filtro de municipio (SIN normalización)
    if filters.get("municipio_display") and filters.get("municipio_display") != "Todos":
        municipio = filters["municipio_display"]
        casos_filtrados = casos_filtrados[casos_filtrados["municipio"] == municipio]
        epizootias_filtradas = epizootias_filtradas[epizootias_filtradas["municipio"] == municipio]

    # Aplicar filtro de vereda (SIN normalización)
    if filters.get("vereda_display") and filters.get("vereda_display") != "Todas":
        vereda = filters["vereda_display"]
        casos_filtrados = casos_filtrados[casos_filtrados["vereda"] == vereda]
        epizootias_filtradas = epizootias_filtradas[epizootias_filtradas["vereda"] == vereda]

    # Aplicar filtro de fechas (mantener sin cambios)
    if filters.get("fecha_rango") and len(filters["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters["fecha_rango"]
        fecha_inicio = pd.Timestamp(fecha_inicio)
        fecha_fin = pd.Timestamp(fecha_fin)

        if "fecha_inicio_sintomas" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                (casos_filtrados["fecha_inicio_sintomas"] >= fecha_inicio)
                & (casos_filtrados["fecha_inicio_sintomas"] <= fecha_fin)
            ]

        if "fecha_recoleccion" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                (epizootias_filtradas["fecha_recoleccion"] >= fecha_inicio)
                & (epizootias_filtradas["fecha_recoleccion"] <= fecha_fin)
            ]

    return casos_filtrados, epizootias_filtradas


def calculate_basic_metrics(casos_df, epizootias_df):
    """
    Calcula métricas básicas de los datos.
    ACTUALIZADO: Incluye métricas para positivas + en estudio

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
        vivos = (casos_df["condicion_final"] == "Vivo").sum()
        metrics["fallecidos"] = fallecidos
        metrics["vivos"] = vivos
        metrics["letalidad"] = (
            (fallecidos / len(casos_df) * 100) if len(casos_df) > 0 else 0
        )
    else:
        metrics["fallecidos"] = 0
        metrics["vivos"] = 0
        metrics["letalidad"] = 0

    # NUEVO: Información del último caso
    if not casos_df.empty:
        ultimo_caso = get_latest_case_info(
            casos_df, 
            "fecha_inicio_sintomas", 
            ["vereda", "municipio"]
        )
        metrics["ultimo_caso"] = ultimo_caso
    else:
        metrics["ultimo_caso"] = {"existe": False}

    # ACTUALIZADO: Métricas de epizootias (positivas + en estudio)
    metrics["total_epizootias"] = len(epizootias_df)

    if "descripcion" in epizootias_df.columns:
        positivos = (epizootias_df["descripcion"] == "POSITIVO FA").sum()
        en_estudio = (epizootias_df["descripcion"] == "EN ESTUDIO").sum()
        
        metrics["epizootias_positivas"] = positivos
        metrics["epizootias_en_estudio"] = en_estudio
        metrics["positividad"] = (
            (positivos / len(epizootias_df) * 100) if len(epizootias_df) > 0 else 0
        )
    else:
        metrics["epizootias_positivas"] = 0
        metrics["epizootias_en_estudio"] = 0
        metrics["positividad"] = 0

    # NUEVO: Información de la última epizootia positiva
    if not epizootias_df.empty:
        epizootias_positivas = epizootias_df[epizootias_df["descripcion"] == "POSITIVO FA"]
        ultima_epizootia = get_latest_case_info(
            epizootias_positivas,
            "fecha_recoleccion",
            ["vereda", "municipio"]
        )
        metrics["ultima_epizootia_positiva"] = ultima_epizootia
    else:
        metrics["ultima_epizootia_positiva"] = {"existe": False}

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
    SIMPLIFICADO: Obtiene ubicaciones únicas usando nombres directos.
    """
    locations = {"municipios": set(), "veredas_por_municipio": {}}

    # Obtener municipios únicos (SIN normalización)
    if "municipio" in casos_df.columns:
        locations["municipios"].update(casos_df["municipio"].dropna().unique())

    if "municipio" in epizootias_df.columns:
        locations["municipios"].update(epizootias_df["municipio"].dropna().unique())

    locations["municipios"] = sorted(list(locations["municipios"]))

    # Obtener veredas por municipio (SIN normalización)
    for municipio in locations["municipios"]:
        veredas = set()

        # Veredas de casos
        if "vereda" in casos_df.columns:
            veredas_casos = casos_df[casos_df["municipio"] == municipio]["vereda"].dropna().unique()
            veredas.update(veredas_casos)

        # Veredas de epizootias
        if "vereda" in epizootias_df.columns:
            veredas_epi = epizootias_df[epizootias_df["municipio"] == municipio]["vereda"].dropna().unique()
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

        # ACTUALIZADO: Verificar distribución de descripciones
        if "descripcion" in epizootias_df.columns:
            desc_counts = epizootias_df["descripcion"].value_counts()
            validation_report["epizootias"]["distribuciones"] = desc_counts.to_dict()

    return validation_report


def create_summary_by_location(casos_df, epizootias_df):
    """
    Crea resumen de datos por ubicación.
    ACTUALIZADO: Incluye estadísticas de positivas + en estudio

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
        en_estudio = 0
        if (
            not epizootias_municipio.empty
            and "descripcion" in epizootias_municipio.columns
        ):
            positivos = (epizootias_municipio["descripcion"] == "POSITIVO FA").sum()
            en_estudio = (epizootias_municipio["descripcion"] == "EN ESTUDIO").sum()

        summary_data.append(
            {
                "municipio": municipio,
                "total_casos": total_casos,
                "fallecidos": fallecidos,
                "letalidad": (fallecidos / total_casos * 100) if total_casos > 0 else 0,
                "total_epizootias": total_epizootias,
                "epizootias_positivas": positivos,
                "epizootias_en_estudio": en_estudio,
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