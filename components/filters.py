"""
Componente de filtros del dashboard.
"""

import streamlit as st
from config.settings import FILTER_MAPPINGS, DASHBOARD_CONFIG


def create_filters(data, on_change_callback):
    """
    Crea todos los filtros del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        on_change_callback (function): Función callback para cambios

    Returns:
        dict: Diccionario con valores de filtros seleccionados
    """
    st.subheader("Filtros")

    filters = {}

    # Filtro de año
    filters["año"] = create_year_filter(data, on_change_callback)

    # Filtro de tipo de caso
    filters["tipo_caso"] = create_case_type_filter(data, on_change_callback)

    # Filtro de departamento
    filters["departamento"] = create_department_filter(data, on_change_callback)

    # Filtro de municipio (dependiente del departamento)
    filters["municipio"] = create_municipality_filter(
        data, filters["departamento"], on_change_callback
    )

    # Filtro de tipo de seguridad social
    filters["tipo_ss"] = create_insurance_filter(data, on_change_callback)

    # Filtro de sexo
    filters["sexo"] = create_sex_filter(data, on_change_callback)

    # Botón para resetear filtros
    create_reset_button(on_change_callback)

    return filters


def create_year_filter(data, on_change_callback):
    """
    Crea el filtro de año.

    Args:
        data (dict): Datos del dashboard
        on_change_callback (function): Función callback

    Returns:
        str: Año seleccionado
    """
    años = ["Todos"]
    if "año" in data["fiebre"].columns and not data["fiebre"].empty:
        años_unicos = data["fiebre"]["año"].dropna().unique().tolist()
        años += sorted(
            [
                str(int(año)) if isinstance(año, (int, float)) else str(año)
                for año in años_unicos
                if not pd.isna(año)
            ]
        )

    return st.selectbox(
        "Año",
        options=años,
        key="año_filter",
        on_change=on_change_callback,
    )


def create_case_type_filter(data, on_change_callback):
    """
    Crea el filtro de tipo de caso.

    Args:
        data (dict): Datos del dashboard
        on_change_callback (function): Función callback

    Returns:
        str: Tipo de caso seleccionado
    """
    tipos_caso = ["Todos"]
    if "tip_cas_" in data["fiebre"].columns and not data["fiebre"].empty:
        # Obtener valores únicos
        tipos_unicos = data["fiebre"]["tip_cas_"].dropna().unique().tolist()

        # Convertir códigos a nombres descriptivos
        for tipo in tipos_unicos:
            if tipo in FILTER_MAPPINGS["tipo_caso"]:
                tipos_caso.append(FILTER_MAPPINGS["tipo_caso"][tipo])
            else:
                tipos_caso.append(str(tipo))

    return st.selectbox(
        "Tipo de Caso",
        options=tipos_caso,
        key="tipo_caso_filter",
        on_change=on_change_callback,
    )


def create_department_filter(data, on_change_callback):
    """
    Crea el filtro de departamento.

    Args:
        data (dict): Datos del dashboard
        on_change_callback (function): Función callback

    Returns:
        str: Departamento seleccionado
    """
    departamentos = ["Todos"]
    if "ndep_resi" in data["fiebre"].columns and not data["fiebre"].empty:
        deptos_unicos = data["fiebre"]["ndep_resi"].dropna().unique().tolist()
        departamentos += sorted([str(depto) for depto in deptos_unicos])

    return st.selectbox(
        "Departamento",
        options=departamentos,
        key="departamento_filter",
        on_change=on_change_callback,
    )


def create_municipality_filter(data, selected_department, on_change_callback):
    """
    Crea el filtro de municipio basado en el departamento seleccionado.

    Args:
        data (dict): Datos del dashboard
        selected_department (str): Departamento seleccionado
        on_change_callback (function): Función callback

    Returns:
        str: Municipio seleccionado
    """
    municipios = ["Todos"]

    if (
        selected_department != "Todos"
        and "ndep_resi" in data["fiebre"].columns
        and "nmun_resi" in data["fiebre"].columns
    ):
        # Filtrar municipios del departamento seleccionado
        muni_filtrados = (
            data["fiebre"][data["fiebre"]["ndep_resi"] == selected_department][
                "nmun_resi"
            ]
            .dropna()
            .unique()
            .tolist()
        )
        municipios += sorted(muni_filtrados)
    elif "nmun_resi" in data["fiebre"].columns:
        # Si no hay departamento seleccionado, mostrar municipios principales
        all_munis = sorted(data["fiebre"]["nmun_resi"].dropna().unique().tolist())
        max_munis = DASHBOARD_CONFIG["max_municipios_dropdown"]
        municipios += all_munis[:max_munis]

    return st.selectbox(
        "Municipio",
        options=municipios,
        key="municipio_filter",
        on_change=on_change_callback,
    )


def create_insurance_filter(data, on_change_callback):
    """
    Crea el filtro de tipo de seguridad social.

    Args:
        data (dict): Datos del dashboard
        on_change_callback (function): Función callback

    Returns:
        str: Tipo de seguridad social seleccionado
    """
    tipos_ss = ["Todos"]
    if "tip_ss_" in data["fiebre"].columns and not data["fiebre"].empty:
        # Obtener valores únicos
        ss_unicos = data["fiebre"]["tip_ss_"].dropna().unique().tolist()

        # Añadir valores con descripciones
        for ss in ss_unicos:
            ss_str = str(ss)
            if ss_str in FILTER_MAPPINGS["seguridad_social"]:
                tipos_ss.append(
                    f"{ss_str} - {FILTER_MAPPINGS['seguridad_social'][ss_str]}"
                )
            else:
                tipos_ss.append(ss_str)

    return st.selectbox(
        "Tipo de Seguridad Social",
        options=tipos_ss,
        key="tipo_ss_filter",
        on_change=on_change_callback,
    )


def create_sex_filter(data, on_change_callback):
    """
    Crea el filtro de sexo.

    Args:
        data (dict): Datos del dashboard
        on_change_callback (function): Función callback

    Returns:
        str: Sexo seleccionado
    """
    sexos = ["Todos"]
    if "sexo_" in data["fiebre"].columns and not data["fiebre"].empty:
        sexos_unicos = data["fiebre"]["sexo_"].dropna().unique().tolist()
        sexos += sorted([str(sexo) for sexo in sexos_unicos])

    return st.selectbox(
        "Sexo",
        options=sexos,
        key="sexo_filter",
        on_change=on_change_callback,
    )


def create_reset_button(on_change_callback):
    """
    Crea el botón para resetear todos los filtros.

    Args:
        on_change_callback (function): Función callback

    Returns:
        None
    """

    def reset_filters():
        # Resetear todos los filtros
        filter_keys = [
            "año_filter",
            "tipo_caso_filter",
            "departamento_filter",
            "municipio_filter",
            "tipo_ss_filter",
            "sexo_filter",
        ]

        for key in filter_keys:
            st.session_state.update({key: "Todos"})

        # Llamar callback para actualizar filtros
        on_change_callback()

    if st.button("Restablecer Filtros", on_click=reset_filters):
        pass


def get_filter_options(data, filter_type):
    """
    Obtiene las opciones disponibles para un tipo de filtro específico.

    Args:
        data (dict): Datos del dashboard
        filter_type (str): Tipo de filtro

    Returns:
        list: Lista de opciones disponibles
    """
    options = ["Todos"]

    if filter_type == "year" and "año" in data["fiebre"].columns:
        años_unicos = data["fiebre"]["año"].dropna().unique().tolist()
        options += sorted([str(int(año)) for año in años_unicos])

    elif filter_type == "case_type" and "tip_cas_" in data["fiebre"].columns:
        tipos_unicos = data["fiebre"]["tip_cas_"].dropna().unique().tolist()
        for tipo in tipos_unicos:
            if tipo in FILTER_MAPPINGS["tipo_caso"]:
                options.append(FILTER_MAPPINGS["tipo_caso"][tipo])

    # Agregar más tipos de filtros según sea necesario

    return options


def apply_filter_logic(data, filter_name, filter_value):
    """
    Aplica la lógica de filtrado para un filtro específico.

    Args:
        data (pd.DataFrame): DataFrame a filtrar
        filter_name (str): Nombre del filtro
        filter_value: Valor del filtro

    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    if filter_value == "Todos":
        return data

    # Aplicar lógica específica según el tipo de filtro
    if filter_name == "año" and "año" in data.columns:
        return data[data["año"] == int(filter_value)]

    elif filter_name == "departamento" and "ndep_resi" in data.columns:
        return data[data["ndep_resi"].str.upper() == filter_value.upper()]

    # Agregar más lógica según sea necesario

    return data
