"""
Utilidades para carga de datos desde diferentes fuentes.
"""

import streamlit as st
import pandas as pd
import logging
from pathlib import Path
from gdrive_utils import get_file_from_drive

logger = logging.getLogger("FiebreAmarilla-Dashboard")


def load_datasets():
    """
    Carga los datasets necesarios para la aplicación.

    Returns:
        dict: Diccionario con los dataframes cargados.
    """
    try:
        # Inicializar contador de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Resto del código de carga...
        # (Mover aquí todo el código de load_datasets del app.py)

        return {
            "fiebre": fiebre_df,
            "departamentos": deptos_df,
            "metricas": metricas_df,
        }
    except Exception as e:
        logger.error(f"Error al cargar los datos: {str(e)}")
        # Manejar errores...
