"""
utils/name_normalizer.py - EXTREMADAMENTE SIMPLIFICADO
Ya no necesita normalización - los nombres coinciden exactamente
"""

import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# Lista de municipios del Tolima (nombres exactos post-estandarización)
MUNICIPIOS_TOLIMA = [
    "IBAGUE",
    "ALPUJARRA",
    "ALVARADO",
    "AMBALEMA",
    "ANZOATEGUI",
    "ARMERO",
    "ATACO",
    "CAJAMARCA",
    "CARMEN DE APICALA",
    "CASABIANCA",
    "CHAPARRAL",
    "COELLO",
    "COYAIMA",
    "CUNDAY",
    "DOLORES",
    "ESPINAL",
    "FALAN",
    "FLANDES",
    "FRESNO",
    "GUAMO",
    "HERVEO",
    "HONDA",
    "ICONONZO",
    "LERIDA",
    "LIBANO",
    "MARIQUITA",
    "MELGAR",
    "MURILLO",
    "NATAGAIMA",
    "ORTEGA",
    "PALOCABILDO",
    "PIEDRAS",
    "PLANADAS",
    "PRADO",
    "PURIFICACION",
    "RIOBLANCO",
    "RONCESVALLES",
    "ROVIRA",
    "SALDANA",
    "SAN ANTONIO",
    "SAN LUIS",
    "SANTA ISABEL",
    "SUAREZ",
    "VALLE DE SAN JUAN",
    "VENADILLO",
    "VILLAHERMOSA",
    "VILLARRICA",
]


def normalize_name(name: str) -> str:
    """
    Limpiar espacios.
    """
    if not name:
        return ""
    return str(name).strip()


def validate_municipio_name(name: str) -> bool:
    """Valida si un nombre de municipio es válido para el Tolima."""
    if not name:
        return False
    return normalize_name(name) in MUNICIPIOS_TOLIMA


def get_canonical_municipio_name(name: str) -> Optional[str]:
    """
    Obtiene el nombre canónico de un municipio.
    """
    normalized = normalize_name(name)
    return normalized if normalized in MUNICIPIOS_TOLIMA else None


def find_exact_match(target_name: str, candidates: List[str]) -> Optional[str]:
    """
    Búsqueda EXACTA
    """
    if not target_name or not candidates:
        return None

    normalized_target = normalize_name(target_name)

    for candidate in candidates:
        if normalize_name(candidate) == normalized_target:
            return candidate

    return None


def debug_name_matching(name1: str, name2: str) -> dict:
    """Debug."""
    return {
        "input_name1": name1,
        "input_name2": name2,
        "normalized_name1": normalize_name(name1),
        "normalized_name2": normalize_name(name2),
        "match_exact": normalize_name(name1) == normalize_name(name2),
    }

def create_cross_reference_map(
    shapefile_names: List[str], veredas_names: List[str]
) -> dict:
    """
    Mapeo directo - los nombres ya coinciden exactamente.
    """
    cross_map = {}

    for shapefile_name in shapefile_names:
        normalized = normalize_name(shapefile_name)
        if normalized in [normalize_name(v) for v in veredas_names]:
            cross_map[shapefile_name] = normalized

    return cross_map


def validate_data_consistency(
    casos_df, epizootias_df, municipios_authoritativos: List[str]
) -> dict:
    """
    Validación simplificada - comparación directa.
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

    return reporte


def log_normalization_stats(data_dict: dict) -> None:
    """Log simplificado."""
    logger.info("=== ESTADÍSTICAS POST-ESTANDARIZACIÓN ===")
    for data_name, df in data_dict.items():
        if hasattr(df, "empty") and not df.empty:
            if "municipio" in df.columns:
                municipios_unicos = df["municipio"].dropna().unique()
                logger.info(
                    f"{data_name.upper()}: {len(municipios_unicos)} municipios únicos"
                )
    logger.info("=== FIN ESTADÍSTICAS ===")