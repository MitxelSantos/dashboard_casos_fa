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


def normalize_text(text):
    """
    Normaliza texto removiendo tildes, convirtiendo a mayúsculas y limpiando espacios.
    MEJORADO: Manejo robusto de tipos y valores especiales.
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""

    # Validación adicional para valores problemáticos
    if text.strip() == "" or text.lower() in ['nan', 'none', 'null']:
        return ""

    try:
        # Remover tildes y diacríticos
        text = unicodedata.normalize("NFD", text)
        text = "".join(char for char in text if unicodedata.category(char) != "Mn")

        # Convertir a mayúsculas y limpiar espacios
        text = text.upper().strip()
        text = re.sub(r"\s+", " ", text)

        # Reemplazos específicos para problemas comunes
        replacements = {
            "VILLARICA": "VILLARRICA",  # Corregir inconsistencia detectada en diagnóstico
            "PURIFICACION": "PURIFICACION",  # Mantener sin tilde
        }

        for old, new in replacements.items():
            if text == old:
                text = new
                break

        return text
        
    except Exception as e:
        logger.warning(f"Error normalizando texto '{text}': {e}")
        return ""


def normalize_vereda_name(vereda_name):
    """
    MEJORADO: Normalización específica para nombres de veredas con mapeo automático.
    """
    if pd.isna(vereda_name) or not isinstance(vereda_name, str):
        return ""
    
    # Aplicar normalización básica
    normalized = normalize_text(vereda_name)
    
    # Patrones comunes de normalización para veredas
    patterns = [
        # Remover prefijos comunes
        (r'^VEREDA\s+', ''),
        (r'^VDA\s+', ''),
        (r'^VER\s+', ''),
        
        # Normalizar conectores
        (r'\s+DE\s+LA\s+', ' '),
        (r'\s+DE\s+LOS\s+', ' '),
        (r'\s+DE\s+LAS\s+', ' '),
        (r'\s+DEL\s+', ' '),
        (r'\s+LA\s+', ' '),
        (r'\s+EL\s+', ' '),
        (r'\s+LOS\s+', ' '),
        (r'\s+LAS\s+', ' '),
        
        # Normalizar números
        (r'\s+NUMERO\s+', ' '),
        (r'\s+NO\s+', ' '),
        (r'\s+#\s+', ' '),
        
        # Limpiar espacios múltiples
        (r'\s+', ' '),
    ]
    
    for pattern, replacement in patterns:
        normalized = re.sub(pattern, replacement, normalized)
    
    return normalized.strip()


def create_intelligent_vereda_mapping(casos_df, epizootias_df):
    """
    MEJORADO: Integra sistema automático de mapeo si está disponible.
    """
    mapping = {}
    
    # Si está disponible el sistema automático, usarlo como base
    if MAPPING_SYSTEM_AVAILABLE:
        try:
            auto_mapping = get_vereda_mapping(include_medium_confidence=True)
            mapping.update(auto_mapping)
            logger.info(f"✅ Sistema automático aplicado: {len(auto_mapping)} mapeos de veredas")
        except Exception as e:
            logger.warning(f"Error aplicando sistema automático: {e}")
    
    # Si no está disponible o como fallback, usar fuzzy matching
    if not mapping and FUZZY_AVAILABLE:
        mapping = _create_fuzzy_vereda_mapping(casos_df, epizootias_df)
        logger.info(f"✅ Sistema fuzzy aplicado: {len(mapping)} mapeos de veredas")
    
    return mapping


def _create_fuzzy_vereda_mapping(casos_df, epizootias_df):
    """Sistema de mapeo fuzzy como fallback."""
    mapping = {}
    
    # Obtener todas las veredas únicas de ambos datasets
    veredas_casos = set()
    veredas_epizootias = set()
    
    if not casos_df.empty and "vereda" in casos_df.columns:
        veredas_casos = set(casos_df["vereda"].dropna().unique())
    
    if not epizootias_df.empty and "vereda" in epizootias_df.columns:
        veredas_epizootias = set(epizootias_df["vereda"].dropna().unique())
    
    todas_veredas = list(veredas_casos.union(veredas_epizootias))
    
    # Normalizar todas las veredas
    veredas_normalizadas = {}
    for vereda in todas_veredas:
        normalized = normalize_vereda_name(vereda)
        if normalized:
            if normalized not in veredas_normalizadas:
                veredas_normalizadas[normalized] = []
            veredas_normalizadas[normalized].append(vereda)
    
    # Encontrar variaciones similares usando fuzzy matching
    processed_veredas = set()
    
    for vereda_norm, variaciones in veredas_normalizadas.items():
        if vereda_norm in processed_veredas:
            continue
        
        # Buscar veredas similares
        similares = []
        for otra_vereda_norm in veredas_normalizadas:
            if otra_vereda_norm != vereda_norm and otra_vereda_norm not in processed_veredas:
                ratio = fuzz.ratio(vereda_norm, otra_vereda_norm)
                token_ratio = fuzz.token_sort_ratio(vereda_norm, otra_vereda_norm)
                
                if ratio >= 85 or token_ratio >= 90:
                    similares.append(otra_vereda_norm)
        
        # Crear mapeo para esta vereda y sus similares
        todas_variaciones = variaciones.copy()
        for similar in similares:
            todas_variaciones.extend(veredas_normalizadas[similar])
            processed_veredas.add(similar)
        
        # Usar la variación más común como canónica
        vereda_canonica = max(set(todas_variaciones), key=todas_variaciones.count)
        
        # Mapear todas las variaciones a la canónica
        for variacion in todas_variaciones:
            mapping[variacion] = vereda_canonica
        
        processed_veredas.add(vereda_norm)
    
    return mapping


def apply_automatic_mapping_to_dataframes(casos_df, epizootias_df):
    """
    NUEVA: Aplica mapeo automático a ambos DataFrames si está disponible.
    """
    if not MAPPING_SYSTEM_AVAILABLE:
        logger.info("Sistema de mapeo automático no disponible, usando mapeo básico")
        return casos_df, epizootias_df
    
    try:
        casos_mapped = casos_df.copy()
        epizootias_mapped = epizootias_df.copy()
        
        # Aplicar mapeo a municipios en casos
        if not casos_mapped.empty and "municipio_normalizado" in casos_mapped.columns:
            casos_mapped = apply_shapefile_mapping_safe(
                casos_mapped,
                'municipio_normalizado',
                'municipios',
                include_medium_confidence=False  # Solo alta confianza inicialmente
            )
            # Usar la columna mapeada
            if 'municipio_normalizado_mapped' in casos_mapped.columns:
                casos_mapped['municipio_normalizado'] = casos_mapped['municipio_normalizado_mapped']
                casos_mapped.drop('municipio_normalizado_mapped', axis=1, inplace=True)
        
        # Aplicar mapeo a municipios en epizootias
        if not epizootias_mapped.empty and "municipio_normalizado" in epizootias_mapped.columns:
            epizootias_mapped = apply_shapefile_mapping_safe(
                epizootias_mapped,
                'municipio_normalizado', 
                'municipios',
                include_medium_confidence=False
            )
            if 'municipio_normalizado_mapped' in epizootias_mapped.columns:
                epizootias_mapped['municipio_normalizado'] = epizootias_mapped['municipio_normalizado_mapped']
                epizootias_mapped.drop('municipio_normalizado_mapped', axis=1, inplace=True)
        
        # Aplicar mapeo a veredas en casos
        if not casos_mapped.empty and "vereda_normalizada" in casos_mapped.columns:
            casos_mapped = apply_shapefile_mapping_safe(
                casos_mapped,
                'vereda_normalizada',
                'veredas',
                include_medium_confidence=False
            )
            if 'vereda_normalizada_mapped' in casos_mapped.columns:
                casos_mapped['vereda_normalizada'] = casos_mapped['vereda_normalizada_mapped'] 
                casos_mapped.drop('vereda_normalizada_mapped', axis=1, inplace=True)
        
        # Aplicar mapeo a veredas en epizootias
        if not epizootias_mapped.empty and "vereda_normalizada" in epizootias_mapped.columns:
            epizootias_mapped = apply_shapefile_mapping_safe(
                epizootias_mapped,
                'vereda_normalizada',
                'veredas',
                include_medium_confidence=False
            )
            if 'vereda_normalizada_mapped' in epizootias_mapped.columns:
                epizootias_mapped['vereda_normalizada'] = epizootias_mapped['vereda_normalizada_mapped']
                epizootias_mapped.drop('vereda_normalizada_mapped', axis=1, inplace=True)
        
        logger.info("✅ Mapeo automático aplicado a ambos DataFrames")
        return casos_mapped, epizootias_mapped
        
    except Exception as e:
        logger.error(f"Error aplicando mapeo automático: {e}")
        return casos_df, epizootias_df


def apply_vereda_mapping(df, vereda_column, mapping):
    """
    MEJORADO: Aplica el mapeo inteligente de veredas a un DataFrame con logging.
    """
    if df.empty or vereda_column not in df.columns or not mapping:
        return df
    
    df_copy = df.copy()
    original_count = len(df_copy[vereda_column].unique())
    
    # Aplicar mapeo
    df_copy[vereda_column] = df_copy[vereda_column].map(mapping).fillna(df_copy[vereda_column])
    
    mapped_count = len(df_copy[vereda_column].unique())
    mappings_applied = original_count - mapped_count
    
    if mappings_applied > 0:
        logger.info(f"✅ Mapeo de veredas aplicado: {mappings_applied} nombres unificados")
    
    return df_copy


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
    MEJORADO: Procesa el dataframe de casos confirmados con mapeo automático.
    """
    df_processed = df.copy()

    # Normalizar municipios y veredas
    if "municipio" in df_processed.columns:
        df_processed["municipio_normalizado"] = df_processed["municipio"].apply(normalize_text)
        df_processed["municipio"] = df_processed["municipio"].apply(capitalize_names)

    if "vereda" in df_processed.columns:
        df_processed["vereda_normalizada"] = df_processed["vereda"].apply(normalize_text)
        df_processed["vereda"] = df_processed["vereda"].apply(capitalize_names)

    # Procesar fechas con formato DD/MM/YYYY
    if "fecha_inicio_sintomas" in df_processed.columns:
        logger.info("📅 Procesando fechas de casos...")
        df_processed["fecha_inicio_sintomas"] = df_processed["fecha_inicio_sintomas"].apply(excel_date_to_datetime)
        
        # Debug: mostrar algunas fechas procesadas
        fechas_validas = df_processed["fecha_inicio_sintomas"].dropna()
        if not fechas_validas.empty:
            logger.info(f"   Fechas procesadas - Mínima: {fechas_validas.min()}, Máxima: {fechas_validas.max()}")

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
    MEJORADO: Procesa el dataframe de epizootias con mapeo automático.
    """
    df_processed = df.copy()

    # Normalizar municipios y veredas
    if "municipio" in df_processed.columns:
        df_processed["municipio_normalizado"] = df_processed["municipio"].apply(normalize_text)
        df_processed["municipio"] = df_processed["municipio"].apply(capitalize_names)

    if "vereda" in df_processed.columns:
        df_processed["vereda_normalizada"] = df_processed["vereda"].apply(normalize_text)
        df_processed["vereda"] = df_processed["vereda"].apply(capitalize_names)

    # Procesar fechas con formato DD/MM/YYYY
    if "fecha_recoleccion" in df_processed.columns:
        logger.info("📅 Procesando fechas de epizootias...")
        df_processed["fecha_recoleccion"] = df_processed["fecha_recoleccion"].apply(excel_date_to_datetime)
        
        # Debug: mostrar algunas fechas procesadas
        fechas_validas = df_processed["fecha_recoleccion"].dropna()
        if not fechas_validas.empty:
            logger.info(f"   Fechas de epizootias - Mínima: {fechas_validas.min()}, Máxima: {fechas_validas.max()}")

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

    # Categorizar resultados (incluyendo en estudio)
    if "descripcion" in df_processed.columns:
        df_processed["categoria_resultado"] = (
            df_processed["descripcion"]
            .map(
                {
                    "POSITIVO FA": "Positivo",
                    "NEGATIVO FA": "Negativo",
                    "NO APTA": "No apta",
                    "EN ESTUDIO": "En Estudio",
                }
            )
            .fillna("Otro")
        )

    return df_processed


def validate_mapping_results(casos_df, epizootias_df):
    """
    NUEVA: Valida los resultados del mapeo automático.
    """
    validation_results = {
        'casos': {'issues': [], 'stats': {}},
        'epizootias': {'issues': [], 'stats': {}}
    }
    
    # Validar casos
    if not casos_df.empty:
        if 'municipio_normalizado' in casos_df.columns:
            # Buscar casos específicos conocidos
            villarica_count = len(casos_df[casos_df['municipio_normalizado'] == 'VILLARICA'])
            villarrica_count = len(casos_df[casos_df['municipio_normalizado'] == 'VILLARRICA'])
            
            validation_results['casos']['stats'] = {
                'total_municipios': casos_df['municipio_normalizado'].nunique(),
                'villarica_original': villarica_count,
                'villarrica_mapped': villarrica_count
            }
            
            if villarica_count > 0:
                validation_results['casos']['issues'].append(
                    f"❌ Encontrados {villarica_count} casos con 'VILLARICA' sin mapear"
                )
    
    # Validar epizootias
    if not epizootias_df.empty:
        if 'municipio_normalizado' in epizootias_df.columns:
            villarica_count = len(epizootias_df[epizootias_df['municipio_normalizado'] == 'VILLARICA'])
            villarrica_count = len(epizootias_df[epizootias_df['municipio_normalizado'] == 'VILLARRICA'])
            
            validation_results['epizootias']['stats'] = {
                'total_municipios': epizootias_df['municipio_normalizado'].nunique(),
                'villarica_original': villarica_count,
                'villarrica_mapped': villarrica_count
            }
            
            if villarica_count > 0:
                validation_results['epizootias']['issues'].append(
                    f"❌ Encontradas {villarica_count} epizootias con 'VILLARICA' sin mapear"
                )
    
    return validation_results


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


def normalize_municipio_name(municipio):
    """
    MEJORADO: Normaliza nombres de municipios integrando sistema automático.
    """
    if pd.isna(municipio):
        return ""

    # Aplicar normalización básica
    normalized = normalize_text(str(municipio))

    # Si está disponible el sistema automático, intentar mapear
    if MAPPING_SYSTEM_AVAILABLE:
        try:
            municipio_mapping = get_municipio_mapping()
            mapped_value = municipio_mapping.get(str(municipio), municipio_mapping.get(normalized, normalized))
            if mapped_value != normalized:
                logger.debug(f"Municipio mapeado: {normalized} → {mapped_value}")
            return mapped_value
        except Exception as e:
            logger.warning(f"Error aplicando mapeo automático a municipio '{municipio}': {e}")

    # Mapeo manual específico como fallback
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
    ACTUALIZADO: Maneja positivas + en estudio

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

    # ACTUALIZADO: Categorizar resultados (incluyendo en estudio)
    if "descripcion" in df_processed.columns:
        df_processed["categoria_resultado"] = (
            df_processed["descripcion"]
            .map(
                {
                    "POSITIVO FA": "Positivo",
                    "NEGATIVO FA": "Negativo",
                    "NO APTA": "No apta",
                    "EN ESTUDIO": "En Estudio",
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