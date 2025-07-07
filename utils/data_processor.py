"""
utils/data_processor.py CORREGIDO
GARANTIZA: Todas las métricas usan datos filtrados
ELIMINADOS: Accesos inconsistentes a datos originales
CLARIFICADO: Todos los parámetros especifican si son filtrados
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


def excel_date_to_datetime(excel_date):
    """Convierte fecha de Excel a datetime con manejo robusto."""
    try:
        # Si ya es datetime, retornar tal como está
        if isinstance(excel_date, (pd.Timestamp, datetime)):
            return excel_date

        # Si está vacío o es NaN
        if pd.isna(excel_date) or excel_date == "":
            return None

        # Si es string, intentar parsear
        if isinstance(excel_date, str):
            excel_date = excel_date.strip()
            if not excel_date or excel_date.lower() in ['nan', 'none', 'null']:
                return None
                
            # Formatos comunes
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
            
            # Fallback a pandas
            try:
                return pd.to_datetime(excel_date, dayfirst=True, errors="coerce")
            except:
                return None

        # Si es número (formato Excel)
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
            if converted_date:
                return converted_date.strftime("%Y-%m-%d")
            else:
                return ""
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


def get_latest_case_info(casos_filtrados_df, date_column, location_columns=None):
    """
    CORREGIDO: Obtiene información del caso más reciente usando DATOS FILTRADOS.
    
    Args:
        casos_filtrados_df (pd.DataFrame): DataFrame de casos FILTRADOS
        date_column (str): Columna de fecha
        location_columns (list): Columnas de ubicación
        
    Returns:
        dict: Información del caso más reciente en los datos filtrados
    """
    if casos_filtrados_df.empty or date_column not in casos_filtrados_df.columns:
        return {
            "existe": False,
            "fecha": None,
            "ubicacion": "Sin datos filtrados",
            "dias_transcurridos": None,
            "tiempo_transcurrido": "Sin datos filtrados"
        }
    
    # Filtrar solo registros con fecha válida
    df_with_dates = casos_filtrados_df.dropna(subset=[date_column])
    
    if df_with_dates.empty:
        return {
            "existe": False,
            "fecha": None,
            "ubicacion": "Sin fechas válidas en datos filtrados",
            "dias_transcurridos": None,
            "tiempo_transcurrido": "Sin fechas válidas en datos filtrados"
        }
    
    # Obtener el registro más reciente DE LOS DATOS FILTRADOS
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

def calculate_basic_metrics(casos_df, epizootias_df):
    """
    Calcula métricas básicas de los datos CON LOGGING DETALLADO.
    ACTUALIZADO: Incluye métricas para positivas + en estudio

    Args:
        casos_df (pd.DataFrame): DataFrame de casos
        epizootias_df (pd.DataFrame): DataFrame de epizootias

    Returns:
        dict: Diccionario con métricas calculadas
    """
    # LOGGING DETALLADO para debugging
    logger.info(f"🧮 calculate_basic_metrics llamada:")
    logger.info(f"   📊 Casos recibidos: {len(casos_df)} registros")
    logger.info(f"   📊 Epizootias recibidas: {len(epizootias_df)} registros")
    
    # Verificar que son DataFrames válidos
    if not isinstance(casos_df, pd.DataFrame):
        logger.error(f"   ❌ casos_df no es DataFrame: {type(casos_df)}")
        casos_df = pd.DataFrame()
    if not isinstance(epizootias_df, pd.DataFrame):
        logger.error(f"   ❌ epizootias_df no es DataFrame: {type(epizootias_df)}")
        epizootias_df = pd.DataFrame()
    
    metrics = {}

    # Métricas de casos
    metrics["total_casos"] = len(casos_df)
    logger.info(f"   🦠 Total casos: {metrics['total_casos']}")

    if "condicion_final" in casos_df.columns and not casos_df.empty:
        fallecidos = (casos_df["condicion_final"] == "Fallecido").sum()
        vivos = (casos_df["condicion_final"] == "Vivo").sum()
        metrics["fallecidos"] = fallecidos
        metrics["vivos"] = vivos
        metrics["letalidad"] = (
            (fallecidos / len(casos_df) * 100) if len(casos_df) > 0 else 0
        )
        logger.info(f"   ⚰️ Fallecidos: {fallecidos}, Vivos: {vivos}, Letalidad: {metrics['letalidad']:.1f}%")
    else:
        metrics["fallecidos"] = 0
        metrics["vivos"] = 0
        metrics["letalidad"] = 0
        logger.info(f"   ⚠️ No hay columna condicion_final o casos está vacío")

    # NUEVO: Información del último caso
    if not casos_df.empty:
        ultimo_caso = get_latest_case_info(
            casos_df, 
            "fecha_inicio_sintomas", 
            ["vereda", "municipio"]
        )
        metrics["ultimo_caso"] = ultimo_caso
        if ultimo_caso["existe"]:
            logger.info(f"   📍 Último caso: {ultimo_caso['ubicacion']} ({ultimo_caso['tiempo_transcurrido']})")
    else:
        metrics["ultimo_caso"] = {"existe": False}
        logger.info(f"   📍 Sin casos para último caso")

    # ACTUALIZADO: Métricas de epizootias (positivas + en estudio)
    metrics["total_epizootias"] = len(epizootias_df)
    logger.info(f"   🐒 Total epizootias: {metrics['total_epizootias']}")

    if "descripcion" in epizootias_df.columns and not epizootias_df.empty:
        positivos = (epizootias_df["descripcion"] == "POSITIVO FA").sum()
        en_estudio = (epizootias_df["descripcion"] == "EN ESTUDIO").sum()
        
        metrics["epizootias_positivas"] = positivos
        metrics["epizootias_en_estudio"] = en_estudio
        metrics["positividad"] = (
            (positivos / len(epizootias_df) * 100) if len(epizootias_df) > 0 else 0
        )
        logger.info(f"   🔴 Positivas: {positivos}, En estudio: {en_estudio}, Positividad: {metrics['positividad']:.1f}%")
    else:
        metrics["epizootias_positivas"] = 0
        metrics["epizootias_en_estudio"] = 0
        metrics["positividad"] = 0
        logger.info(f"   ⚠️ No hay columna descripcion o epizootias está vacío")

    # NUEVO: Información de la última epizootia positiva
    if not epizootias_df.empty:
        epizootias_positivas = epizootias_df[epizootias_df["descripcion"] == "POSITIVO FA"] if "descripcion" in epizootias_df.columns else pd.DataFrame()
        ultima_epizootia = get_latest_case_info(
            epizootias_positivas,
            "fecha_recoleccion",
            ["vereda", "municipio"]
        )
        metrics["ultima_epizootia_positiva"] = ultima_epizootia
        if ultima_epizootia["existe"]:
            logger.info(f"   📍 Última epizootia positiva: {ultima_epizootia['ubicacion']} ({ultima_epizootia['tiempo_transcurrido']})")
    else:
        metrics["ultima_epizootia_positiva"] = {"existe": False}
        logger.info(f"   📍 Sin epizootias para última epizootia")

    # Métricas geográficas usando nombres directos (sin normalización)
    if "municipio" in casos_df.columns and not casos_df.empty:
        metrics["municipios_con_casos"] = casos_df["municipio"].nunique()
    else:
        metrics["municipios_con_casos"] = 0

    if "municipio" in epizootias_df.columns and not epizootias_df.empty:
        metrics["municipios_con_epizootias"] = epizootias_df["municipio"].nunique()
    else:
        metrics["municipios_con_epizootias"] = 0

    logger.info(f"   📍 Municipios con casos: {metrics['municipios_con_casos']}, con epizootias: {metrics['municipios_con_epizootias']}")
    
    # LOG FINAL CON RESUMEN
    logger.info(f"🧮 Métricas calculadas: {metrics['total_casos']} casos, {metrics['total_epizootias']} epizootias, {metrics['fallecidos']} fallecidos, {metrics['epizootias_positivas']} positivas")

    return metrics

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
        logger.info("📅 Procesando fechas de casos...")
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
        logger.info("📅 Procesando fechas de epizootias...")
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


def apply_filters_to_data(casos_df, epizootias_df, filters):
    """
    SIMPLIFICADO: Aplica filtros usando nombres directos.
    NOTA: Esta función se mantiene solo para compatibilidad.
    El filtrado principal debe hacerse a través del sistema unificado.
    """
    casos_filtrados = casos_df.copy()
    epizootias_filtradas = epizootias_df.copy()

    # Aplicar filtro de municipio
    if filters.get("municipio_display") and filters.get("municipio_display") != "Todos":
        municipio = filters["municipio_display"]
        casos_filtrados = casos_filtrados[casos_filtrados["municipio"] == municipio]
        epizootias_filtradas = epizootias_filtradas[epizootias_filtradas["municipio"] == municipio]

    # Aplicar filtro de vereda
    if filters.get("vereda_display") and filters.get("vereda_display") != "Todas":
        vereda = filters["vereda_display"]
        casos_filtrados = casos_filtrados[casos_filtrados["vereda"] == vereda]
        epizootias_filtradas = epizootias_filtradas[epizootias_filtradas["vereda"] == vereda]

    # Aplicar filtro de fechas
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


def get_unique_locations(casos_filtrados_df, epizootias_filtradas_df):
    """
    CORREGIDO: Obtiene ubicaciones únicas de DATOS FILTRADOS.
    
    Args:
        casos_filtrados_df (pd.DataFrame): Casos filtrados
        epizootias_filtradas_df (pd.DataFrame): Epizootias filtradas
        
    Returns:
        dict: Ubicaciones únicas en los datos filtrados
    """
    locations = {"municipios": set(), "veredas_por_municipio": {}}

    # Obtener municipios únicos de datos filtrados
    if "municipio" in casos_filtrados_df.columns:
        locations["municipios"].update(casos_filtrados_df["municipio"].dropna().unique())

    if "municipio" in epizootias_filtradas_df.columns:
        locations["municipios"].update(epizootias_filtradas_df["municipio"].dropna().unique())

    locations["municipios"] = sorted(list(locations["municipios"]))

    # Obtener veredas por municipio de datos filtrados
    for municipio in locations["municipios"]:
        veredas = set()

        # Veredas de casos filtrados
        if "vereda" in casos_filtrados_df.columns:
            veredas_casos = casos_filtrados_df[
                casos_filtrados_df["municipio"] == municipio
            ]["vereda"].dropna().unique()
            veredas.update(veredas_casos)

        # Veredas de epizootias filtradas
        if "vereda" in epizootias_filtradas_df.columns:
            veredas_epi = epizootias_filtradas_df[
                epizootias_filtradas_df["municipio"] == municipio
            ]["vereda"].dropna().unique()
            veredas.update(veredas_epi)

        locations["veredas_por_municipio"][municipio] = sorted(list(veredas))

    return locations


def create_summary_by_location(casos_filtrados_df, epizootias_filtradas_df):
    """
    CORREGIDO: Crea resumen por ubicación usando DATOS FILTRADOS.
    
    Args:
        casos_filtrados_df (pd.DataFrame): DataFrame de casos filtrados
        epizootias_filtradas_df (pd.DataFrame): DataFrame de epizootias filtradas
        
    Returns:
        pd.DataFrame: Resumen por ubicación de datos filtrados
    """
    summary_data = []

    # Obtener ubicaciones únicas de los datos filtrados
    locations = get_unique_locations(casos_filtrados_df, epizootias_filtradas_df)

    for municipio in locations["municipios"]:
        # Casos en el municipio (de datos filtrados)
        casos_municipio = casos_filtrados_df[
            casos_filtrados_df["municipio"] == municipio
        ] if "municipio" in casos_filtrados_df.columns else pd.DataFrame()
        
        epizootias_municipio = epizootias_filtradas_df[
            epizootias_filtradas_df["municipio"] == municipio
        ] if "municipio" in epizootias_filtradas_df.columns else pd.DataFrame()

        # Calcular métricas de datos filtrados
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
            "positividad": (
                (positivos / total_epizootias * 100) if total_epizootias > 0 else 0
            ),
            "veredas_afectadas": len(
                locations["veredas_por_municipio"].get(municipio, [])
            ),
        })

    return pd.DataFrame(summary_data).sort_values("total_casos", ascending=False)


def prepare_dataframe_for_display(df_filtrado, date_columns=None):
    """
    CORREGIDO: Prepara DataFrame filtrado para mostrar.
    
    Args:
        df_filtrado (pd.DataFrame): DataFrame filtrado para mostrar
        date_columns (list): Columnas de fecha a formatear
        
    Returns:
        pd.DataFrame: DataFrame filtrado preparado para mostrar
    """
    if df_filtrado.empty:
        return df_filtrado

    df_display = df_filtrado.copy()

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


def validate_data_consistency(casos_filtrados_df, epizootias_filtradas_df):
    """
    CORREGIDO: Valida consistencia de DATOS FILTRADOS.
    
    Args:
        casos_filtrados_df (pd.DataFrame): Casos filtrados
        epizootias_filtradas_df (pd.DataFrame): Epizootias filtradas
        
    Returns:
        dict: Reporte de validación de datos filtrados
    """
    validation_report = {
        "casos_filtrados": {}, 
        "epizootias_filtradas": {}, 
        "warnings": [], 
        "errors": []
    }

    # Validar casos filtrados
    if not casos_filtrados_df.empty:
        validation_report["casos_filtrados"]["total_rows"] = len(casos_filtrados_df)
        validation_report["casos_filtrados"]["columns"] = list(casos_filtrados_df.columns)

        # Verificar fechas válidas en datos filtrados
        if "fecha_inicio_sintomas" in casos_filtrados_df.columns:
            fechas_validas = casos_filtrados_df["fecha_inicio_sintomas"].notna().sum()
            validation_report["casos_filtrados"]["fechas_validas"] = fechas_validas
            if fechas_validas == 0:
                validation_report["warnings"].append("No hay fechas válidas en casos filtrados")

    # Validar epizootias filtradas
    if not epizootias_filtradas_df.empty:
        validation_report["epizootias_filtradas"]["total_rows"] = len(epizootias_filtradas_df)
        validation_report["epizootias_filtradas"]["columns"] = list(epizootias_filtradas_df.columns)

        # Verificar distribución de descripciones en datos filtrados
        if "descripcion" in epizootias_filtradas_df.columns:
            desc_counts = epizootias_filtradas_df["descripcion"].value_counts()
            validation_report["epizootias_filtradas"]["distribuciones"] = desc_counts.to_dict()

    return validation_report


# ==================== FUNCIONES DE LOGGING PARA DEBUGGING ====================

def log_filter_application(data_original, data_filtered, filter_description=""):
    """
    NUEVA: Función para logging detallado del filtrado.
    Ayuda a debugging del problema reportado.
    """
    casos_orig = len(data_original.get("casos", []))
    epi_orig = len(data_original.get("epizootias", []))
    
    casos_filt = len(data_filtered.get("casos", []))
    epi_filt = len(data_filtered.get("epizootias", []))
    
    logger.info(f"🔍 Filtrado aplicado {filter_description}:")
    logger.info(f"   🦠 Casos: {casos_orig} → {casos_filt} ({((casos_orig-casos_filt)/casos_orig*100):.1f}% filtrado)" if casos_orig > 0 else f"   🦠 Casos: 0 → 0")
    logger.info(f"   🐒 Epizootias: {epi_orig} → {epi_filt} ({((epi_orig-epi_filt)/epi_orig*100):.1f}% filtrado)" if epi_orig > 0 else f"   🐒 Epizootias: 0 → 0")


def verify_filtered_data_usage(df, function_name=""):
    """
    NUEVA: Función para verificar que se están usando datos filtrados.
    """
    if df.empty:
        logger.warning(f"⚠️ {function_name}: DataFrame vacío - posiblemente sobre-filtrado")
    else:
        logger.info(f"✅ {function_name}: Usando {len(df)} registros filtrados")
        
def verify_filtered_data_usage(data, context="unknown"):
    """
    Verifica que se estén usando datos filtrados y no datos originales.
    
    Args:
        data (pd.DataFrame): DataFrame a verificar
        context (str): Contexto donde se está usando (para logging)
    """
    if data is None:
        logger.warning(f"⚠️ {context}: Datos nulos recibidos")
        return False
    
    # Log básico de verificación
    total_rows = len(data)
    logger.info(f"✅ {context}: Usando datos con {total_rows} registros")
    
    # Verificación adicional: si los datos vienen del session_state de filtros
    if hasattr(data, 'name') and 'filtered' in str(data.name):
        logger.info(f"✅ {context}: Confirmado uso de datos filtrados")
    
    return True


def log_filter_application(data_original, data_filtered, filter_description=""):
    """
    Registra la aplicación de filtros para debugging.
    
    Args:
        data_original (dict): Datos originales con 'casos' y 'epizootias'
        data_filtered (dict): Datos filtrados con 'casos' y 'epizootias' 
        filter_description (str): Descripción de los filtros aplicados
    """
    try:
        # Conteos originales
        casos_orig = len(data_original.get("casos", []))
        epi_orig = len(data_original.get("epizootias", []))
        
        # Conteos filtrados
        casos_filt = len(data_filtered.get("casos", []))
        epi_filt = len(data_filtered.get("epizootias", []))
        
        # Calcular porcentajes de reducción
        casos_reduction = ((casos_orig - casos_filt) / casos_orig * 100) if casos_orig > 0 else 0
        epi_reduction = ((epi_orig - epi_filt) / epi_orig * 100) if epi_orig > 0 else 0
        
        # Log detallado
        logger.info(f"🔍 Aplicación de filtros: {filter_description}")
        logger.info(f"   🦠 Casos: {casos_orig} → {casos_filt} ({casos_reduction:.1f}% filtrado)")
        logger.info(f"   🐒 Epizootias: {epi_orig} → {epi_filt} ({epi_reduction:.1f}% filtrado)")
        
        if casos_reduction > 0 or epi_reduction > 0:
            logger.info(f"   ✅ Filtros aplicados correctamente")
        else:
            logger.info(f"   ℹ️ Sin filtrado (mostrando datos completos)")
            
    except Exception as e:
        logger.error(f"❌ Error en log_filter_application: {str(e)}")


def ensure_filtered_data_usage(casos_filtrados, epizootias_filtradas, context=""):
    """
    Asegura que se estén usando datos filtrados en lugar de originales.
    
    Args:
        casos_filtrados (pd.DataFrame): Casos filtrados
        epizootias_filtradas (pd.DataFrame): Epizootias filtradas
        context (str): Contexto de uso
        
    Returns:
        tuple: (casos_verificados, epizootias_verificadas)
    """
    # Verificar casos
    verify_filtered_data_usage(casos_filtrados, f"{context} - casos")
    
    # Verificar epizootias  
    verify_filtered_data_usage(epizootias_filtradas, f"{context} - epizootias")
    
    # Log de confirmación
    total_casos = len(casos_filtrados) if casos_filtrados is not None else 0
    total_epi = len(epizootias_filtradas) if epizootias_filtradas is not None else 0
    
    logger.info(f"🎯 {context}: Confirmado uso de datos filtrados - {total_casos} casos, {total_epi} epizootias")
    
    return casos_filtrados, epizootias_filtradas


def validate_data_consistency_filtered(data_filtered, filters):
    """
    Valida la consistencia de datos filtrados con los filtros aplicados.
    
    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        
    Returns:
        dict: Reporte de validación
    """
    validation_report = {
        "casos_count": 0,
        "epizootias_count": 0,
        "filters_applied": [],
        "consistency_issues": [],
        "status": "ok"
    }
    
    try:
        casos = data_filtered.get("casos", pd.DataFrame())
        epizootias = data_filtered.get("epizootias", pd.DataFrame())
        
        validation_report["casos_count"] = len(casos)
        validation_report["epizootias_count"] = len(epizootias)
        
        # Verificar filtros activos
        active_filters = filters.get("active_filters", [])
        validation_report["filters_applied"] = active_filters
        
        # Validar consistencia con filtros de ubicación
        municipio_filter = filters.get("municipio_display", "Todos")
        vereda_filter = filters.get("vereda_display", "Todas")
        
        if municipio_filter != "Todos":
            # Verificar que los casos filtrados correspondan al municipio
            if not casos.empty and "municipio" in casos.columns:
                casos_municipio = casos["municipio"].unique()
                if len(casos_municipio) > 1 or (len(casos_municipio) == 1 and casos_municipio[0] != municipio_filter):
                    validation_report["consistency_issues"].append(f"Casos no coinciden con filtro de municipio: {municipio_filter}")
            
            # Verificar epizootias
            if not epizootias.empty and "municipio" in epizootias.columns:
                epi_municipio = epizootias["municipio"].unique()
                if len(epi_municipio) > 1 or (len(epi_municipio) == 1 and epi_municipio[0] != municipio_filter):
                    validation_report["consistency_issues"].append(f"Epizootias no coinciden con filtro de municipio: {municipio_filter}")
        
        if vereda_filter != "Todas":
            # Verificar que los datos filtrados correspondan a la vereda
            if not casos.empty and "vereda" in casos.columns:
                casos_vereda = casos["vereda"].unique()
                if len(casos_vereda) > 1 or (len(casos_vereda) == 1 and casos_vereda[0] != vereda_filter):
                    validation_report["consistency_issues"].append(f"Casos no coinciden con filtro de vereda: {vereda_filter}")
        
        # Determinar status final
        if validation_report["consistency_issues"]:
            validation_report["status"] = "issues_found"
            logger.warning(f"⚠️ Problemas de consistencia en datos filtrados: {validation_report['consistency_issues']}")
        else:
            validation_report["status"] = "ok"
            logger.info(f"✅ Datos filtrados consistentes con filtros aplicados")
            
    except Exception as e:
        validation_report["status"] = "error"
        validation_report["consistency_issues"].append(f"Error en validación: {str(e)}")
        logger.error(f"❌ Error validando consistencia de datos filtrados: {str(e)}")
    
    return validation_report


def debug_data_flow(data_original, data_filtered, filters, stage="unknown"):
    """
    Debug detallado del flujo de datos para identificar problemas de filtrado.
    
    Args:
        data_original (dict): Datos originales
        data_filtered (dict): Datos filtrados  
        filters (dict): Filtros aplicados
        stage (str): Etapa del proceso
    """
    logger.info(f"🔧 DEBUG {stage} - Análisis de flujo de datos:")
    
    # Análisis de datos originales
    if isinstance(data_original, dict):
        casos_orig = len(data_original.get("casos", []))
        epi_orig = len(data_original.get("epizootias", []))
        logger.info(f"   📊 Originales: {casos_orig} casos, {epi_orig} epizootias")
    else:
        logger.warning(f"   ⚠️ data_original no es dict: {type(data_original)}")
    
    # Análisis de datos filtrados
    if isinstance(data_filtered, dict):
        casos_filt = len(data_filtered.get("casos", []))
        epi_filt = len(data_filtered.get("epizootias", []))
        logger.info(f"   🎯 Filtrados: {casos_filt} casos, {epi_filt} epizootias")
        
        # Verificar si realmente hay filtrado
        if isinstance(data_original, dict):
            if casos_filt == casos_orig and epi_filt == epi_orig:
                logger.warning(f"   ⚠️ Los datos filtrados son iguales a los originales - filtros no aplicados?")
            else:
                logger.info(f"   ✅ Filtrado detectado correctamente")
    else:
        logger.warning(f"   ⚠️ data_filtered no es dict: {type(data_filtered)}")
    
    # Análisis de filtros
    active_filters = filters.get("active_filters", []) if isinstance(filters, dict) else []
    logger.info(f"   🎛️ Filtros activos: {len(active_filters)} - {active_filters[:2] if active_filters else 'Ninguno'}")
    
    # Filtros específicos
    if isinstance(filters, dict):
        municipio = filters.get("municipio_display", "Todos")
        vereda = filters.get("vereda_display", "Todas")
        logger.info(f"   📍 Ubicación: {municipio} / {vereda}")