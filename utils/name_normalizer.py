"""
Módulo de normalización robusto para nombres de municipios y veredas.
Maneja tildes, espacios, mayúsculas y equivalencias entre diferentes fuentes.
"""

import unicodedata
import re
import logging
from typing import Dict, Optional, Set
import pandas as pd

logger = logging.getLogger(__name__)

# ===== DICCIONARIOS DE EQUIVALENCIAS =====

# Mapeo de municipios con tildes a su versión sin tildes
MUNICIPIOS_EQUIVALENCIAS = {
    # Municipios con tildes problemáticos
    "IBAGUE": "IBAGUÉ",
    "IBAGUÉ": "IBAGUE",
    "PURIFICACION": "PURIFICACIÓN",
    "PURIFICACIÓN": "PURIFICACION",
    "ARMERO": "ARMERO-GUAYABAL",
    "ARMERO-GUAYABAL": "ARMERO",
    "LIBANO": "LÍBANO",
    "LÍBANO": "LIBANO",
    "LERIDA": "LÉRIDA",
    "LÉRIDA": "LERIDA",
    "SALDAÑA": "SALDANA",
    "SALDANA": "SALDAÑA",
    # Variaciones comunes
    "VALLE DE SAN JUAN": "VALLE DE SAN JUAN",
    "VALLE SAN JUAN": "VALLE DE SAN JUAN",
    "CARMEN DE APICALA": "CARMEN DE APICALÁ",
    "CARMEN DE APICALÁ": "CARMEN DE APICALA",
    "SAN ANTONIO": "SAN ANTONIO",
    "SAN LUIS": "SAN LUIS",
    "SANTA ISABEL": "SANTA ISABEL",
}

# Mapeo bidireccional automático
MUNICIPIOS_BIDIRECCIONAL = {}
for key, value in MUNICIPIOS_EQUIVALENCIAS.items():
    MUNICIPIOS_BIDIRECCIONAL[key] = value
    MUNICIPIOS_BIDIRECCIONAL[value] = key

# Lista de municipios del Tolima (versión autoritativa)
MUNICIPIOS_TOLIMA_AUTORITATIVOS = [
    "IBAGUÉ",
    "ALPUJARRA",
    "ALVARADO",
    "AMBALEMA",
    "ANZOÁTEGUI",
    "ARMERO",
    "ATACO",
    "CAJAMARCA",
    "CARMEN DE APICALÁ",
    "CASABIANCA",
    "CHAPARRAL",
    "COELLO",
    "COYAIMA",
    "CUNDAY",
    "DOLORES",
    "ESPINAL",
    "FALÁN",
    "FLANDES",
    "FRESNO",
    "GUAMO",
    "HERVEO",
    "HONDA",
    "ICONONZO",
    "LÉRIDA",
    "LÍBANO",
    "MARIQUITA",
    "MELGAR",
    "MURILLO",
    "NATAGAIMA",
    "ORTEGA",
    "PALOCABILDO",
    "PIEDRAS",
    "PLANADAS",
    "PRADO",
    "PURIFICACIÓN",
    "RIOBLANCO",
    "RONCESVALLES",
    "ROVIRA",
    "SALDAÑA",
    "SAN ANTONIO",
    "SAN LUIS",
    "SANTA ISABEL",
    "SUÁREZ",
    "VALLE DE SAN JUAN",
    "VENADILLO",
    "VILLAHERMOSA",
    "VILLARRICA",
]

# ===== FUNCIONES DE NORMALIZACIÓN =====


def remove_accents(text: str) -> str:
    """
    Remueve tildes y acentos de un texto.

    Args:
        text: Texto con posibles tildes

    Returns:
        str: Texto sin tildes
    """
    if not text:
        return ""

    # Normalizar a NFD (decomposed form)
    nfd = unicodedata.normalize("NFD", text)

    # Filtrar solo caracteres que no sean diacríticos
    without_accents = "".join(
        char for char in nfd if unicodedata.category(char) != "Mn"
    )

    return without_accents


def clean_text(text: str) -> str:
    """
    Limpia texto: mayúsculas, sin espacios extra, sin caracteres especiales.

    Args:
        text: Texto a limpiar

    Returns:
        str: Texto limpio
    """
    if not text or pd.isna(text):
        return ""

    # Convertir a string y limpiar
    text = str(text).strip()

    # Reemplazar múltiples espacios con uno solo
    text = re.sub(r"\s+", " ", text)

    # Mayúsculas
    text = text.upper()

    return text


def normalize_name_robust(name: str) -> str:
    """
    Normalización robusta para nombres de municipios y veredas.

    Args:
        name: Nombre a normalizar

    Returns:
        str: Nombre normalizado (mayúsculas, sin tildes, espacios limpios)
    """
    if not name or pd.isna(name):
        return ""

    # Limpiar texto básico
    cleaned = clean_text(name)

    # Remover tildes
    normalized = remove_accents(cleaned)

    logger.debug(f"Normalización: '{name}' -> '{normalized}'")

    return normalized


def normalize_name_with_accents(name: str) -> str:
    """
    Normalización que MANTIENE las tildes (para display).

    Args:
        name: Nombre a normalizar

    Returns:
        str: Nombre normalizado (mayúsculas, CON tildes, espacios limpios)
    """
    if not name or pd.isna(name):
        return ""

    # Solo limpiar, mantener tildes
    cleaned = clean_text(name)

    logger.debug(f"Normalización con tildes: '{name}' -> '{cleaned}'")

    return cleaned


def find_equivalent_names(name: str) -> Set[str]:
    """
    Encuentra todas las equivalencias posibles de un nombre.

    Args:
        name: Nombre a buscar equivalencias

    Returns:
        Set[str]: Set con todas las equivalencias encontradas
    """
    if not name or pd.isna(name):
        return set()

    # Normalizar el nombre de entrada
    normalized = normalize_name_robust(name)
    normalized_with_accents = normalize_name_with_accents(name)

    equivalents = set()

    # Agregar versiones básicas
    equivalents.add(normalized)
    equivalents.add(normalized_with_accents)

    # Buscar en diccionario de equivalencias
    for variant in [normalized, normalized_with_accents]:
        if variant in MUNICIPIOS_BIDIRECCIONAL:
            equivalents.add(MUNICIPIOS_BIDIRECCIONAL[variant])

    # Agregar versiones con diferentes casings para display
    for equiv in list(equivalents):
        equivalents.add(equiv.title())  # Primera mayúscula
        equivalents.add(equiv.lower())  # Minúsculas

    logger.debug(f"Equivalencias para '{name}': {equivalents}")

    return equivalents


def match_name_fuzzy(target_name: str, candidates: list) -> Optional[str]:
    """
    Busca coincidencia fuzzy entre un nombre y una lista de candidatos.

    Args:
        target_name: Nombre a buscar
        candidates: Lista de nombres candidatos

    Returns:
        Optional[str]: Mejor coincidencia encontrada o None
    """
    if not target_name or not candidates:
        return None

    # Obtener todas las equivalencias del nombre target
    target_equivalents = find_equivalent_names(target_name)

    # Buscar coincidencia exacta primero
    for candidate in candidates:
        candidate_equivalents = find_equivalent_names(candidate)

        # Si hay intersección, hay coincidencia
        if target_equivalents & candidate_equivalents:
            logger.info(f"Coincidencia encontrada: '{target_name}' -> '{candidate}'")
            return candidate

    # Si no hay coincidencia exacta, buscar similitud
    target_no_accents = normalize_name_robust(target_name)

    for candidate in candidates:
        candidate_no_accents = normalize_name_robust(candidate)

        if target_no_accents == candidate_no_accents:
            logger.info(f"Coincidencia sin tildes: '{target_name}' -> '{candidate}'")
            return candidate

    logger.warning(
        f"No se encontró coincidencia para '{target_name}' en {len(candidates)} candidatos"
    )
    return None


def validate_municipio_name(name: str) -> bool:
    """
    Valida si un nombre de municipio es válido para el Tolima.

    Args:
        name: Nombre del municipio a validar

    Returns:
        bool: True si es válido, False si no
    """
    if not name:
        return False

    # Buscar coincidencia con municipios authoritativos
    match = match_name_fuzzy(name, MUNICIPIOS_TOLIMA_AUTORITATIVOS)

    return match is not None


def get_canonical_municipio_name(name: str) -> Optional[str]:
    """
    Obtiene el nombre canónico (autoritativo) de un municipio.

    Args:
        name: Nombre del municipio (cualquier variación)

    Returns:
        Optional[str]: Nombre canónico o None si no se encuentra
    """
    if not name:
        return None

    # Buscar coincidencia con municipios authoritativos
    canonical = match_name_fuzzy(name, MUNICIPIOS_TOLIMA_AUTORITATIVOS)

    if canonical:
        logger.info(f"Nombre canónico: '{name}' -> '{canonical}'")
    else:
        logger.warning(f"No se encontró nombre canónico para '{name}'")

    return canonical


# ===== FUNCIONES DE MAPEO ENTRE FUENTES =====


def create_cross_reference_map(
    shapefile_names: list, veredas_names: list
) -> Dict[str, str]:
    """
    Crea mapeo entre nombres de shapefiles y nombres de hoja VEREDAS.

    Args:
        shapefile_names: Lista de nombres de shapefiles
        veredas_names: Lista de nombres de hoja VEREDAS

    Returns:
        Dict[str, str]: Mapeo shapefile -> veredas
    """
    cross_map = {}

    for shapefile_name in shapefile_names:
        match = match_name_fuzzy(shapefile_name, veredas_names)

        if match:
            cross_map[shapefile_name] = match
        else:
            logger.warning(
                f"No se pudo mapear shapefile '{shapefile_name}' a hoja VEREDAS"
            )

    logger.info(
        f"Mapeo cruzado creado: {len(cross_map)} de {len(shapefile_names)} nombres mapeados"
    )

    return cross_map


def validate_data_consistency(
    casos_df: pd.DataFrame, epizootias_df: pd.DataFrame, municipios_authoritativos: list
) -> Dict[str, any]:
    """
    Valida consistencia de nombres entre diferentes fuentes de datos.

    Args:
        casos_df: DataFrame de casos
        epizootias_df: DataFrame de epizootias
        municipios_authoritativos: Lista de municipios authoritativos

    Returns:
        Dict: Reporte de validación
    """
    reporte = {
        "municipios_casos_invalidos": [],
        "municipios_epizootias_invalidos": [],
        "municipios_casos_validos": [],
        "municipios_epizootias_validos": [],
        "total_casos_validados": 0,
        "total_epizootias_validadas": 0,
    }

    # Validar municipios en casos
    if not casos_df.empty and "municipio" in casos_df.columns:
        municipios_casos = casos_df["municipio"].dropna().unique()

        for municipio in municipios_casos:
            if validate_municipio_name(municipio):
                reporte["municipios_casos_validos"].append(municipio)
            else:
                reporte["municipios_casos_invalidos"].append(municipio)

        reporte["total_casos_validados"] = len(reporte["municipios_casos_validos"])

    # Validar municipios en epizootias
    if not epizootias_df.empty and "municipio" in epizootias_df.columns:
        municipios_epizootias = epizootias_df["municipio"].dropna().unique()

        for municipio in municipios_epizootias:
            if validate_municipio_name(municipio):
                reporte["municipios_epizootias_validos"].append(municipio)
            else:
                reporte["municipios_epizootias_invalidos"].append(municipio)

        reporte["total_epizootias_validadas"] = len(
            reporte["municipios_epizootias_validos"]
        )

    # Log del reporte
    logger.info(f"Validación completada:")
    logger.info(f"  Casos: {reporte['total_casos_validados']} municipios válidos")
    logger.info(
        f"  Epizootias: {reporte['total_epizootias_validadas']} municipios válidos"
    )

    if reporte["municipios_casos_invalidos"]:
        logger.warning(
            f"  Municipios inválidos en casos: {reporte['municipios_casos_invalidos']}"
        )

    if reporte["municipios_epizootias_invalidos"]:
        logger.warning(
            f"  Municipios inválidos en epizootias: {reporte['municipios_epizootias_invalidos']}"
        )

    return reporte


# ===== FUNCIONES DE COMPATIBILIDAD =====


def normalize_name(name: str) -> str:
    """
    Función de compatibilidad con el código existente.
    Usa normalización robusta.
    """
    return normalize_name_robust(name)


def normalize_name_for_display(name: str) -> str:
    """
    Normalización para display (primera mayúscula, con tildes).

    Args:
        name: Nombre a normalizar

    Returns:
        str: Nombre para display
    """
    if not name or pd.isna(name):
        return ""

    # Limpiar pero mantener tildes
    cleaned = clean_text(name)

    # Convertir a title case (primera mayúscula)
    display_name = cleaned.title()

    return display_name


# ===== FUNCIONES DE DEBUGGING =====


def debug_name_matching(name1: str, name2: str) -> Dict[str, any]:
    """
    Función de debugging para entender por qué dos nombres no coinciden.

    Args:
        name1: Primer nombre
        name2: Segundo nombre

    Returns:
        Dict: Información detallada de la comparación
    """
    debug_info = {
        "input_name1": name1,
        "input_name2": name2,
        "normalized_name1": normalize_name_robust(name1),
        "normalized_name2": normalize_name_robust(name2),
        "with_accents_name1": normalize_name_with_accents(name1),
        "with_accents_name2": normalize_name_with_accents(name2),
        "equivalents_name1": find_equivalent_names(name1),
        "equivalents_name2": find_equivalent_names(name2),
        "match_exact": normalize_name_robust(name1) == normalize_name_robust(name2),
        "match_with_accents": normalize_name_with_accents(name1)
        == normalize_name_with_accents(name2),
        "match_fuzzy": bool(
            find_equivalent_names(name1) & find_equivalent_names(name2)
        ),
    }

    logger.debug(f"Debug matching: {debug_info}")

    return debug_info


def log_normalization_stats(data_dict: Dict[str, pd.DataFrame]) -> None:
    """
    Registra estadísticas de normalización para debugging.

    Args:
        data_dict: Diccionario con DataFrames (casos, epizootias, etc.)
    """
    logger.info("=== ESTADÍSTICAS DE NORMALIZACIÓN ===")

    for data_name, df in data_dict.items():
        if df.empty:
            continue

        if "municipio" in df.columns:
            municipios_unicos = df["municipio"].dropna().unique()
            logger.info(
                f"{data_name.upper()}: {len(municipios_unicos)} municipios únicos"
            )

            for municipio in municipios_unicos:
                canonical = get_canonical_municipio_name(municipio)
                if canonical != municipio:
                    logger.info(f"  '{municipio}' -> '{canonical}'")

        if "vereda" in df.columns:
            veredas_unicas = df["vereda"].dropna().unique()
            logger.info(f"{data_name.upper()}: {len(veredas_unicas)} veredas únicas")

    logger.info("=== FIN ESTADÍSTICAS ===")
