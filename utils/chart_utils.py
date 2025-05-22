"""
Utilidades para creación de gráficos con Plotly.
"""

import plotly.express as px
import plotly.graph_objects as go
from config.colors import COLORS, COLOR_PALETTES


def format_chart(
    fig, title=None, xaxis_title=None, yaxis_title=None, show_legend=True, height=None
):
    """
    Aplica formato estándar a los gráficos de Plotly.

    Args:
        fig: Figura de Plotly
        title (str): Título del gráfico
        xaxis_title (str): Título del eje X
        yaxis_title (str): Título del eje Y
        show_legend (bool): Mostrar leyenda
        height (int): Altura del gráfico

    Returns:
        fig: Figura formateada
    """
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=show_legend,
        height=height,
    )

    if title:
        fig.update_layout(
            title={
                "text": title,
                "y": 0.98,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=16, color="#5A4214"),
            }
        )

    if xaxis_title or yaxis_title:
        fig.update_layout(
            xaxis=dict(title=xaxis_title, gridcolor="#f5f5f5"),
            yaxis=dict(title=yaxis_title, gridcolor="#f5f5f5"),
        )

    return fig


def create_bar_chart(
    data,
    x,
    y,
    title=None,
    color=None,
    orientation="v",
    color_sequence=None,
    text_auto=True,
):
    """
    Crea un gráfico de barras estandarizado.

    Args:
        data: DataFrame con los datos
        x (str): Columna para eje X
        y (str): Columna para eje Y
        title (str): Título del gráfico
        color (str): Columna para colorear
        orientation (str): 'v' para vertical, 'h' para horizontal
        color_sequence (list): Secuencia de colores personalizada
        text_auto (bool): Mostrar texto automático en barras

    Returns:
        fig: Figura de Plotly
    """
    if not color_sequence:
        color_sequence = [COLORS["primary"]]

    fig = px.bar(
        data,
        x=x,
        y=y,
        title=title,
        color=color,
        orientation=orientation,
        color_discrete_sequence=color_sequence,
        text=y if text_auto else None,
    )

    # Configurar texto para evitar rotación
    if text_auto:
        fig.update_traces(textangle=0, textposition="outside", cliponaxis=False)

    # Aplicar formato estándar
    xaxis_title = "Número de Casos Probables" if orientation == "h" else None
    yaxis_title = "Número de Casos Probables" if orientation == "v" else None

    fig = format_chart(
        fig, title=title, xaxis_title=xaxis_title, yaxis_title=yaxis_title
    )

    return fig


def create_pie_chart(data, names, values, title=None, hole=0.4, color_sequence=None):
    """
    Crea un gráfico de pastel estandarizado.

    Args:
        data: DataFrame con los datos
        names (str): Columna con los nombres
        values (str): Columna con los valores
        title (str): Título del gráfico
        hole (float): Tamaño del agujero central (0-1)
        color_sequence (list): Secuencia de colores personalizada

    Returns:
        fig: Figura de Plotly
    """
    if not color_sequence:
        color_sequence = COLOR_PALETTES["categorical"]

    fig = px.pie(
        data,
        names=names,
        values=values,
        title=title,
        color_discrete_sequence=color_sequence,
        hole=hole,
    )

    # Mejorar presentación
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label+value",
        textfont_size=12,
        marker=dict(line=dict(color="#FFFFFF", width=2)),
    )

    # Aplicar formato estándar
    fig = format_chart(fig, title=title)

    # Configurar leyenda horizontal
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )

    return fig


def create_line_chart(
    data,
    x,
    y,
    title=None,
    color=None,
    markers=True,
    line_shape="linear",
    color_sequence=None,
):
    """
    Crea un gráfico de líneas estandarizado.

    Args:
        data: DataFrame con los datos
        x (str): Columna para eje X
        y (str): Columna para eje Y
        title (str): Título del gráfico
        color (str): Columna para colorear líneas
        markers (bool): Mostrar marcadores
        line_shape (str): Forma de la línea ('linear', 'spline')
        color_sequence (list): Secuencia de colores personalizada

    Returns:
        fig: Figura de Plotly
    """
    if not color_sequence:
        color_sequence = [COLORS["primary"]]

    fig = px.line(
        data,
        x=x,
        y=y,
        title=title,
        color=color,
        markers=markers,
        line_shape=line_shape,
        color_discrete_sequence=color_sequence,
    )

    # Aplicar formato estándar
    fig = format_chart(
        fig, title=title, xaxis_title=x, yaxis_title="Número de Casos Probables"
    )

    return fig


def create_area_chart(data, x, y, title=None, color_sequence=None):
    """
    Crea un gráfico de área estandarizado.

    Args:
        data: DataFrame con los datos
        x (str): Columna para eje X
        y (str): Columna para eje Y
        title (str): Título del gráfico
        color_sequence (list): Secuencia de colores personalizada

    Returns:
        fig: Figura de Plotly
    """
    if not color_sequence:
        color_sequence = [COLORS["primary"]]

    fig = px.area(
        data,
        x=x,
        y=y,
        title=title,
        color_discrete_sequence=color_sequence,
        line_shape="spline",
    )

    # Aplicar formato estándar
    fig = format_chart(
        fig, title=title, xaxis_title=x, yaxis_title="Número de Casos Probables"
    )

    return fig


def add_trend_line(fig, data, x, y, color=None):
    """
    Añade una línea de tendencia a un gráfico existente.

    Args:
        fig: Figura de Plotly existente
        data: DataFrame con los datos
        x (str): Columna para eje X
        y (str): Columna para eje Y
        color (str): Color de la línea de tendencia

    Returns:
        fig: Figura con línea de tendencia añadida
    """
    if not color:
        color = COLORS["secondary"]

    # Calcular línea de tendencia usando regresión lineal simple
    import numpy as np

    # Limpiar datos
    clean_data = data[[x, y]].dropna()
    if len(clean_data) < 2:
        return fig

    x_vals = clean_data[x].values
    y_vals = clean_data[y].values

    # Calcular pendiente e intercepto
    slope, intercept = np.polyfit(x_vals, y_vals, 1)
    trend_line = slope * x_vals + intercept

    # Añadir línea de tendencia
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=trend_line,
            mode="lines",
            name="Tendencia",
            line=dict(color=color, dash="dash"),
            opacity=0.8,
        )
    )

    return fig


def create_metric_cards_html(metrics_data, colors):
    """
    Genera HTML para tarjetas de métricas.

    Args:
        metrics_data (list): Lista de diccionarios con datos de métricas
        colors (dict): Diccionario de colores

    Returns:
        str: HTML de las tarjetas de métricas
    """
    cards_html = '<div class="metrics-container">'

    for metric in metrics_data:
        card_html = f"""
        <div class="metric-box" style="border-top: 5px solid {metric.get('color', colors['primary'])}">
            <div class="metric-icon">{metric.get('icon', '📊')}</div>
            <div class="metric-title">{metric['title']}</div>
            <div class="metric-value" style="color: {metric.get('color', colors['primary'])};">{metric['value']}</div>
            {f'<div class="metric-subtext">{metric["subtext"]}</div>' if metric.get('subtext') else ''}
        </div>
        """
        cards_html += card_html

    cards_html += "</div>"
    return cards_html
