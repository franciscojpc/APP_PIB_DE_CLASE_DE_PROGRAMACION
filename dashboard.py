"""Tablero del PIB Trimestral de México (INEGI, base 2018).

Ejecutar:
    .venv/bin/streamlit run dashboard.py
"""

from __future__ import annotations

import os
from contextlib import contextmanager

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import pibt_data as pibt

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(BASE, "tabulados_PIBT")

# ---------------------------------------------------------------- constantes

PAGINA = "#0d0d0d"
SUPERFICIE = "#1a1a19"
TINTA = "#f0efec"
TINTA_2 = "#c3c2b7"
APAGADO = "#898781"
ACENTO = "#3987e5"
LINEA = "rgba(255,255,255,0.08)"
VERDE = "#2fbf71"
ROJO = "#e5484d"
AMBAR = "#e0a03a"
TEAL = "#3cc9b0"
VIOLETA = "#9d7cf4"

REAL = ("PIBT_2.xlsx", "Millones de pesos a precios de 2018")
NOMINAL = ("PIBT_3.xlsx", "Millones de pesos a precios corrientes")
DEFLACTOR = ("PIBT_4.xlsx", "Índice de precios implícitos base 2018=100")
VARIACION = ("PIBT_2.xlsx", "Variación porcentual anual")
ESTRUCTURA = ("PIBT_2.xlsx", "Estructura porcentual")
CONTRIBUCION = ("PIBT_2.xlsx", "Contribución a la variación nacional")
HISTORICO = ("PIBT_r_2.xlsx", "Millones de pesos a precios de 2018")

COLOR_SECTOR = {
    "Primario": TEAL,
    "Secundario": AMBAR,
    "Terciario": ACENTO,
    "Impuestos": APAGADO,
}

ETIQUETAS = {
    "aB.1bP": "PIB",
    "D.21-D.31": "Impuestos a los productos",
    "aB.1bV": "Valor agregado bruto",
    "11": "Agricultura y pesca",
    "21": "Minería",
    "22": "Energía y agua",
    "23": "Construcción",
    "31-33": "Manufactura",
    "43": "Comercio mayoreo",
    "46": "Comercio menudeo",
    "48-49": "Transportes",
    "51": "Medios",
    "52": "Finanzas y seguros",
    "53": "Inmobiliarios",
    "54": "Serv. profesionales",
    "55": "Corporativos",
    "56": "Apoyo a negocios",
    "61": "Educación",
    "62": "Salud",
    "71": "Esparcimiento",
    "72": "Alojamiento y comida",
    "81": "Otros servicios",
    "93": "Gobierno",
}

ETIQUETAS_HISTORICO = {
    "Producto interno bruto": "PIB",
    "Valor agregado bruto": "Valor agregado",
    "Impuestos sobre los productos, netos": "Impuestos",
    "Actividades primarias": "Primarias",
    "Actividades secundarias": "Secundarias",
    "Actividades terciarias": "Terciarias",
}

def gran_sector(codigo: str) -> str:
    c = str(codigo or "")
    if not c:
        return "Otros"
    if c == "31-33" or c[:2] in ("31", "32", "33") or c[:2] in ("21", "22", "23"):
        return "Secundario"
    if c[:2] == "11":
        return "Primario"
    if c[:2] in ("43", "46", "48", "49", "51", "52", "53", "54", "55", "56",
                 "61", "62", "71", "72", "81", "93"):
        return "Terciario"
    return "Otros"


def etiqueta(codigo: str, concepto: str) -> str:
    if codigo in ETIQUETAS:
        return ETIQUETAS[codigo]
    texto = str(concepto)
    return texto if len(texto) <= 36 else texto[:35].rstrip() + "…"


# ---------------------------------------------------------------- estilo

st.set_page_config(
    page_title="PIB México · Tablero trimestral",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=Red+Hat+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Sora', system-ui, sans-serif;
}}
.stApp {{ background: {PAGINA}; color: {TINTA}; }}
[data-testid="stHeader"] {{ background: rgba(13,13,13,0.72); backdrop-filter: blur(8px); }}
[data-testid="stToolbar"], #MainMenu, footer {{ visibility: hidden; }}
[data-testid="stSidebar"] {{
    background: #121211;
    border-right: 1px solid {LINEA};
}}
[data-testid="stSidebar"] > div {{ padding-top: 6px; }}
.block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1480px; }}

/* marca lateral */
.brand {{ display: flex; gap: 11px; align-items: center; margin: 4px 0 14px; }}
.brand-mark {{
    width: 38px; height: 38px; border-radius: 10px; background: {ACENTO};
    display: grid; place-items: center; font-weight: 700; font-size: 13px; color: #fff;
}}
.brand-name {{ font-size: 14px; font-weight: 600; line-height: 1.2; }}
.brand-sub {{ font-size: 11px; color: {APAGADO}; }}
.rail-label {{
    font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
    color: {APAGADO}; font-weight: 600;
}}
.rail-value {{ font-size: 30px; font-weight: 600; letter-spacing: -.02em; margin: 2px 0 2px; }}
.rail-value .unit {{ font-size: 12px; font-weight: 400; color: {APAGADO}; margin-left: 4px; }}
.rail-sub {{ font-size: 12px; color: {TINTA_2}; margin-bottom: 18px; }}
.rail-section {{
    font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
    color: {APAGADO}; font-weight: 600; margin: 6px 0 2px;
    border-top: 1px solid {LINEA}; padding-top: 14px;
}}
.rail-foot {{
    font-size: 11px; color: {APAGADO}; line-height: 1.6;
    border-top: 1px solid {LINEA}; padding-top: 12px; margin-top: 14px;
}}
.rail-foot b {{ color: {TINTA_2}; font-weight: 500; }}

/* portada */
.hero {{ padding: 2px 2px 16px; }}
.hero .eyebrow {{
    font-family: 'Red Hat Mono', monospace; font-size: 11px;
    letter-spacing: .12em; text-transform: uppercase; color: {ACENTO};
}}
.hero h1 {{
    font-size: 32px; font-weight: 600; letter-spacing: -.025em;
    margin: 8px 0 4px; color: {TINTA};
}}
.hero p {{ margin: 0; color: {APAGADO}; font-size: 13.5px; }}

/* tarjetas KPI */
.kpi {{
    background: {SUPERFICIE}; border: 1px solid {LINEA}; border-radius: 14px;
    padding: 15px 18px 14px; height: 100%;
}}
.kpi .label {{
    font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
    color: {APAGADO}; font-weight: 600;
}}
.kpi .value {{
    font-size: 30px; font-weight: 600; letter-spacing: -.02em;
    margin: 7px 0 4px; line-height: 1.1; color: {TINTA};
}}
.kpi .value .unit {{ font-size: 12px; font-weight: 400; color: {APAGADO}; margin-left: 5px; }}
.kpi .foot {{ font-size: 12px; color: {APAGADO}; line-height: 1.45; }}
.chip {{
    display: inline-flex; align-items: center; padding: 1px 8px; border-radius: 999px;
    font-family: 'Red Hat Mono', monospace; font-size: 11px; margin-right: 6px;
}}
.chip.pos {{ background: rgba(47,191,113,.15); color: #58d68d; }}
.chip.neg {{ background: rgba(229,72,77,.16); color: #ff7b7f; }}
.chip.neu {{ background: rgba(255,255,255,.07); color: {TINTA_2}; }}

/* paneles */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {SUPERFICIE};
    border: 1px solid {LINEA} !important;
    border-radius: 14px;
}}
div[data-testid="stVerticalBlockBorderWrapper"] > div {{
    padding: 12px 16px 10px;
}}
.panel-title {{ font-size: 15px; font-weight: 600; color: {TINTA}; }}
.panel-sub {{ font-size: 12px; color: {APAGADO}; margin: 2px 0 4px; }}

/* pestañas */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {LINEA}; }}
.stTabs [data-baseweb="tab"] {{
    height: 40px; padding: 0 16px; border-radius: 9px 9px 0 0;
    color: {APAGADO}; font-size: 14px; font-weight: 500; background: transparent;
}}
.stTabs [aria-selected="true"] {{ color: {TINTA}; background: rgba(57,135,229,.10); }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {ACENTO}; }}
.stTabs [data-baseweb="tab-border"] {{ background: transparent; }}

/* resumen */
.insights {{ display: flex; flex-direction: column; gap: 9px; }}
.insight {{
    display: flex; gap: 10px; font-size: 13px; color: {TINTA_2}; line-height: 1.5;
}}
.insight .dot {{
    width: 7px; height: 7px; border-radius: 50%; background: {ACENTO};
    margin-top: 7px; flex: none;
}}
.insight b {{ color: {TINTA}; font-weight: 600; }}

/* widgets */
div[data-baseweb="select"] > div {{
    background: {SUPERFICIE} !important;
    border-color: {LINEA} !important;
}}
.stSlider [data-baseweb="slider"] div[role="slider"] {{ background: {ACENTO}; }}
label, .stRadio label, .stMultiSelect label, .stSelectbox label {{
    color: {TINTA_2} !important; font-size: 12px !important;
}}

/* barra de herramientas de las gráficas */
.js-plotly-plot .plotly .modebar {{ background: transparent !important; top: 2px; right: 4px; }}
.js-plotly-plot .plotly .modebar-group {{ background: transparent !important; }}
.js-plotly-plot .plotly .modebar-btn path {{ fill: rgba(195,194,183,.65) !important; }}
.js-plotly-plot .plotly .modebar-btn:hover path,
.js-plotly-plot .plotly .modebar-btn.active path {{ fill: {TINTA} !important; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- datos

@st.cache_data(show_spinner="Cargando tabulados del INEGI…")
def cargar_datos():
    return pibt.cargar_todos_cache(CARPETA)


@st.cache_data(show_spinner=False)
def cargar_meta():
    return pibt.cargar_meta(os.path.join(CARPETA, "PIBT_2.xlsx"))


df = cargar_datos()
meta = cargar_meta()


def serie(archivo, seccion, campo=None, valor=None, frecuencia="Anual"):
    """Serie de una sola variable, opcionalmente filtrada por código o concepto."""
    s = df[(df.archivo == archivo) & (df.seccion == seccion)].copy()
    if campo is not None:
        s = s[s[campo] == valor]
    if frecuencia == "Trimestral":
        s = s[s.periodo.isin(pibt.PERIODOS_TRIMESTRALES)].copy()
        s["trimestre"] = s.periodo.str[1].astype(int)
        s["fecha"] = pd.to_datetime(
            dict(year=s.anio, month=(s.trimestre - 1) * 3 + 1, day=1))
        s = s.sort_values("fecha")
        s["etiqueta"] = s.anio.astype(str) + " " + s.periodo
    else:
        s = s[s.periodo == "Anual"].sort_values("anio")
        s["etiqueta"] = s.anio.astype(str)
    return s.dropna(subset=["valor"])


def serie_pib(archivo, seccion, frecuencia="Anual"):
    if archivo == "PIBT_r_2.xlsx":
        return serie(archivo, seccion, "concepto", "Producto interno bruto", frecuencia)
    return serie(archivo, seccion, "codigo", "aB.1bP", frecuencia)


@contextmanager
def panel(titulo, subtitulo=""):
    with st.container(border=True):
        st.markdown(
            f'<div class="panel-title">{titulo}</div>'
            f'<div class="panel-sub">{subtitulo}</div>',
            unsafe_allow_html=True)
        yield


def tema(fig, altura=340, leyenda=True):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Sora, system-ui, sans-serif", color=TINTA_2, size=12),
        colorway=[ACENTO, TEAL, AMBAR, VIOLETA, ROJO, "#f472b6", APAGADO],
        margin=dict(l=8, r=12, t=12, b=8),
        height=altura,
        showlegend=leyenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#222220", bordercolor="rgba(255,255,255,.14)",
                        font=dict(family="Red Hat Mono, monospace",
                                  color=TINTA, size=11)),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, zeroline=False,
                     linecolor="rgba(255,255,255,.12)",
                     tickfont=dict(color=APAGADO, size=11))
    fig.update_yaxes(gridcolor="rgba(255,255,255,.06)", zeroline=False,
                     tickfont=dict(color=APAGADO, size=11))
    return fig


# Barra de herramientas con zoom de acercar y alejar, paneo y restablecer.
# scrollZoom permite usar la rueda del ratón en ambos sentidos.
CONFIG_PLOT = {
    "displayModeBar": "hover",
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": True,
    "doubleClick": "reset",
    "modeBarButtons": [[
        "zoom2d", "pan2d", "zoomIn2d", "zoomOut2d",
        "autoScale2d", "resetScale2d",
    ]],
}


# ---------------------------------------------------------------- números base

trim = serie_pib(*REAL, frecuencia="Trimestral")
anual = serie_pib(*REAL, frecuencia="Anual")
var_trim = serie_pib(*VARIACION, frecuencia="Trimestral")
var_anual = serie_pib(*VARIACION, frecuencia="Anual")

ultimo = trim.iloc[-1]
ultimo_periodo = ultimo.etiqueta
crec_ultimo = var_trim[(var_trim.anio == ultimo.anio) &
                       (var_trim.periodo == ultimo.periodo)].valor
crec_ultimo = float(crec_ultimo.iloc[0]) if len(crec_ultimo) else float("nan")

anios_completos = sorted(anual.anio.astype(int).tolist())
anio_fin_trim = int(trim.anio.max())           # último año con algún trimestre
anio_min = int(anios_completos[0])


def valor_anual(archivo, seccion, codigo, anio):
    s = df[(df.archivo == archivo) & (df.seccion == seccion) &
           (df.codigo == codigo) & (df.periodo == "Anual") &
           (df.anio == anio)].valor.dropna()
    return float(s.iloc[0]) if len(s) else float("nan")


def cagr(anio_fin, anios):
    if anio_fin - anios < anio_min:
        return float("nan")
    v0 = valor_anual(*REAL, "aB.1bP", anio_fin - anios)
    v1 = valor_anual(*REAL, "aB.1bP", anio_fin)
    if pd.isna(v0) or pd.isna(v1) or v0 <= 0:
        return float("nan")
    return (v1 / v0) ** (1 / anios) - 1


def chip(x, texto=None, sufijo=""):
    if pd.isna(x):
        return '<span class="chip neu">s/d</span>'
    clase = "pos" if x >= 0 else "neg"
    signo = "+" if x > 0 else ""
    txt = f"{signo}{x:.1f}%{sufijo}" if texto is None else texto
    return f'<span class="chip {clase}">{txt}</span>'


def fmt_billones(v):
    return f"{v/1e6:,.2f}" if pd.notna(v) else "—"


def fmt_pct(v, decimales=1):
    return f"{v:.{decimales}f}" if pd.notna(v) else "—"


def rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ---------------------------------------------------------------- sidebar

with st.sidebar:
    st.markdown(
        '<div class="brand">'
        '<div class="brand-mark">PIB</div>'
        '<div><div class="brand-name">Producto Interno Bruto</div>'
        '<div class="brand-sub">México · Tablero trimestral</div></div>'
        '</div>', unsafe_allow_html=True)
    st.markdown('<div class="rail-label">Último trimestre</div>',
                unsafe_allow_html=True)
    st.markdown(
        f'<div class="rail-value">{fmt_billones(float(ultimo.valor))}'
        f'<span class="unit">billones</span></div>'
        f'<div class="rail-sub">{ultimo_periodo} · {chip(crec_ultimo)} anual</div>',
        unsafe_allow_html=True)

    st.markdown('<div class="rail-section">Filtros</div>', unsafe_allow_html=True)
    rango = st.slider("Rango de años", 1980, anio_fin_trim,
                      (anio_min, anio_fin_trim), step=1,
                      help="Las series detalladas comienzan en 1993; la serie "
                           "histórica de agregados, en 1980.")
    anios_analisis = sorted(var_anual.dropna(subset=["valor"]).anio.unique(),
                            reverse=True)
    anio_sel = st.selectbox(
        "Año de análisis", [int(a) for a in anios_analisis],
        index=0, help="Año que usan las gráficas de barras, el mapa de calor "
                      "y las comparaciones anuales.")
    medida = st.radio("Serie del panorama", ["Real (2018)", "Nominal"],
                      horizontal=True)
    frecuencia = st.radio("Frecuencia", ["Trimestral", "Anual"], horizontal=True)

    st.markdown(
        f'<div class="rail-foot"><b>Fuente:</b> INEGI · Sistema de Cuentas '
        f'Nacionales de México.<br><b>Producto:</b> PIB Trimestral, año base '
        f'2018.<br><b>Actualizado:</b> '
        f'{pd.to_datetime(str(meta.get("FECHA DE ACTUALIZACIÓN", ""))).strftime("%d %b %Y")}'
        f'<br><b>Cobertura:</b> {meta.get("DESCRIPCIÓN PERIODO", "1993–2026")}'
        f'</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- portada

fecha_meta = pd.to_datetime(str(meta.get("FECHA DE ACTUALIZACIÓN", "")))
st.markdown(
    f'<div class="hero">'
    f'<div class="eyebrow">INEGI · SCNM · Año base 2018 · '
    f'Actualizado {fecha_meta.strftime("%d %b %Y")}</div>'
    f'<h1>Producto Interno Bruto de México</h1>'
    f'<p>Serie trimestral {anio_min}–{anio_fin_trim} · 20 ramas de actividad · '
    f'cifras a precios constantes de 2018</p>'
    f'</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- KPIs

pib_anio_sel = valor_anual(*REAL, "aB.1bP", anio_sel)
crec_anio_sel = valor_anual(*VARIACION, "aB.1bP", anio_sel)
crec_10 = cagr(anio_sel, 10)

contr_sel = df[(df.archivo == CONTRIBUCION[0]) & (df.seccion == CONTRIBUCION[1]) &
               (df.periodo == "Anual") & (df.anio == anio_sel) &
               (df.nivel == 2)].dropna(subset=["valor"])
if len(contr_sel):
    top_contr = contr_sel.loc[contr_sel.valor.idxmax()]
    top_contr_label = etiqueta(top_contr.codigo, top_contr.concepto)
    top_contr_val = float(top_contr.valor)
else:
    top_contr_label, top_contr_val = "—", float("nan")
top_contr_corto = (top_contr_label if len(top_contr_label) <= 24
                   else top_contr_label[:23].rstrip() + "…")

c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    st.markdown(
        f'<div class="kpi"><div class="label">PIB trimestral</div>'
        f'<div class="value">{fmt_billones(float(ultimo.valor))}'
        f'<span class="unit">billones</span></div>'
        f'<div class="foot">{chip(crec_ultimo)} anual · {ultimo_periodo}</div></div>',
        unsafe_allow_html=True)
with c2:
    st.markdown(
        f'<div class="kpi"><div class="label">PIB anual {anio_sel}</div>'
        f'<div class="value">{fmt_billones(pib_anio_sel)}'
        f'<span class="unit">billones</span></div>'
        f'<div class="foot">{chip(crec_anio_sel)} real anual</div></div>',
        unsafe_allow_html=True)
with c3:
    st.markdown(
        f'<div class="kpi"><div class="label">Crecimiento 10 años</div>'
        f'<div class="value">{fmt_pct(crec_10*100, 2)}'
        f'<span class="unit">% anual</span></div>'
        f'<div class="foot">Tasa media {anio_sel-10}–{anio_sel}, precios de 2018</div></div>',
        unsafe_allow_html=True)
with c4:
    st.markdown(
        f'<div class="kpi"><div class="label">Mayor contribución {anio_sel}</div>'
        f'<div class="value" style="font-size:21px;line-height:1.3">'
        f'{top_contr_corto}</div>'
        f'<div class="foot">'
        f'{chip(top_contr_val*100, f"{top_contr_val:+.2f} pp" if pd.notna(top_contr_val) else "s/d")} '
        f'al crecimiento del PIB</div></div>',
        unsafe_allow_html=True)

st.write("")

tabs = st.tabs(["Panorama", "Sectores", "Explorar", "Datos"])

# ---------------------------------------------------------------- Panorama

with tabs[0]:
    fuente = REAL if medida.startswith("Real") else NOMINAL
    pib_line = serie_pib(*fuente, frecuencia=frecuencia)
    pib_line = pib_line[(pib_line.anio >= rango[0]) & (pib_line.anio <= rango[1])]

    with panel("Producto interno bruto",
               f"{'Precios constantes de 2018' if medida.startswith('Real') else 'Precios corrientes'}"
               f" · {frecuencia.lower()} · billones de pesos"):
        if pib_line.empty:
            st.info("No hay datos en el rango seleccionado.")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=pib_line.fecha if frecuencia == "Trimestral" else pib_line.anio,
                y=pib_line.valor / 1e6,
                mode="lines",
                line=dict(color=ACENTO, width=2.2),
                fill="tozeroy", fillcolor="rgba(57,135,229,0.09)",
                customdata=pib_line.etiqueta,
                hovertemplate="%{customdata}<br><b>%{y:.2f}</b> billones<extra></extra>",
            ))
            ult = pib_line.iloc[-1]
            fig.add_annotation(
                x=ult.fecha if frecuencia == "Trimestral" else ult.anio,
                y=ult.valor / 1e6, text=f"{ult.valor/1e6:.2f}",
                showarrow=False, xanchor="left", xshift=8,
                font=dict(family="Red Hat Mono, monospace", size=11, color=TINTA),
                bgcolor="#222220", borderpad=4)
            fig.update_yaxes(title_text="billones de pesos",
                             title_font=dict(size=11))
            tema(fig, altura=360, leyenda=False)
            fig.update_layout(hovermode="x")
            fig.update_xaxes(
                hoverformat="T%q %Y" if frecuencia == "Trimestral" else "%Y")
            st.plotly_chart(fig, width="stretch", config=CONFIG_PLOT)
            st.caption("Rueda del ratón: acercar o alejar · arrastrar sobre una "
                       "zona: hacer zoom · doble clic: restablecer.")

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        with panel(f"Crecimiento por gran sector · {anio_sel}",
                   "Variación porcentual anual de las series originales"):
            var_g = df[(df.archivo == VARIACION[0]) & (df.seccion == VARIACION[1]) &
                       (df.periodo == "Anual") & (df.anio == anio_sel) &
                       (df.nivel <= 1)].dropna(subset=["valor"])
            orden = ["Producto interno bruto", "Actividades primarias",
                     "Actividades secundarias", "Actividades terciarias"]
            var_g = var_g[var_g.concepto.isin(orden)]
            var_g["orden"] = var_g.concepto.map({v: i for i, v in enumerate(orden)})
            var_g = var_g.sort_values("orden")
            nombres = {"Producto interno bruto": "PIB total",
                       "Actividades primarias": "Primarias",
                       "Actividades secundarias": "Secundarias",
                       "Actividades terciarias": "Terciarias"}
            colores = {"PIB total": TINTA_2, "Primarias": TEAL,
                       "Secundarias": AMBAR, "Terciarias": ACENTO}
            labels = [nombres.get(c, c) for c in var_g.concepto]
            fig = go.Figure(go.Bar(
                x=var_g.valor, y=labels, orientation="h",
                marker=dict(color=[colores[l] for l in labels],
                            line=dict(width=0)),
                text=[f"{v:+.1f}%" for v in var_g.valor],
                textposition="outside", cliponaxis=False,
                textfont=dict(family="Red Hat Mono, monospace", size=11, color=TINTA_2),
                hovertemplate="%{y}: <b>%{x:.2f}%</b><extra></extra>",
            ))
            fig.add_vline(x=0, line_color="rgba(255,255,255,.22)", line_width=1)
            lo, hi = var_g.valor.min(), var_g.valor.max()
            pad = max((hi - lo) * 0.20, 0.8)
            fig.update_xaxes(title_text="% anual", title_font=dict(size=11),
                             range=[lo - pad, hi + pad])
            fig.update_yaxes(autorange="reversed")
            tema(fig, altura=300, leyenda=False)
            fig.update_layout(hovermode="closest",
                              margin=dict(l=8, r=64, t=8, b=8))
            st.plotly_chart(fig, width="stretch", config=CONFIG_PLOT)

    with col_b:
        with panel("Composición del PIB",
                   f"Estructura porcentual · {rango[0]}–{rango[1]}"):
            est = df[(df.archivo == ESTRUCTURA[0]) & (df.seccion == ESTRUCTURA[1]) &
                     (df.periodo == "Anual") & (df.nivel == 1) &
                     (df.anio.between(rango[0], rango[1]))].dropna(subset=["valor"])
            mapa = {
                "Actividades primarias": ("Primarias", TEAL),
                "Actividades secundarias": ("Secundarias", AMBAR),
                "Actividades terciarias": ("Terciarias", ACENTO),
                "Impuestos sobre los productos, netos": ("Impuestos", APAGADO),
            }
            est["grupo"] = est.concepto.map(lambda x: mapa.get(x, (x, APAGADO))[0])
            est["color"] = est.concepto.map(lambda x: mapa.get(x, (x, APAGADO))[1])
            fig = go.Figure()
            if est.empty:
                st.info("No hay datos en el rango seleccionado.")
            for grupo in ["Primarias", "Secundarias", "Terciarias", "Impuestos"]:
                sub = est[est.grupo == grupo].sort_values("anio")
                if not len(sub):
                    continue
                color = sub.color.iloc[0]
                fig.add_trace(go.Scatter(
                    x=sub.anio, y=sub.valor, name=grupo,
                    mode="lines", stackgroup="pib",
                    line=dict(width=0.6, color=color),
                    fillcolor=rgba(color, 0.55),
                    hovertemplate=f"{grupo}: <b>%{{y:.1f}}%</b><extra></extra>",
                ))
            if not est.empty:
                fig.update_yaxes(title_text="% del PIB", title_font=dict(size=11),
                                 range=[0, 100])
                tema(fig, altura=320)
                fig.update_layout(
                    hovermode="x unified",
                    margin=dict(l=8, r=8, t=8, b=30),
                    legend=dict(orientation="h", yanchor="top", y=-0.16, x=0,
                                font=dict(size=11), bgcolor="rgba(0,0,0,0)"))
                fig.update_traces(opacity=0.9)
                st.plotly_chart(fig, width="stretch", config=CONFIG_PLOT)

    # lectura rápida
    var_gran = df[(df.archivo == VARIACION[0]) & (df.seccion == VARIACION[1]) &
                  (df.periodo == "Anual") & (df.anio == anio_sel) &
                  (df.nivel == 2)].dropna(subset=["valor"])
    if len(var_gran):
        mejor = var_gran.loc[var_gran.valor.idxmax()]
        peor = var_gran.loc[var_gran.valor.idxmin()]
        mejor_txt = f"{etiqueta(mejor.codigo, mejor.concepto)} ({mejor.valor:+.1f}%)"
        peor_txt = f"{etiqueta(peor.codigo, peor.concepto)} ({peor.valor:+.1f}%)"
    else:
        mejor_txt = peor_txt = "—"
    est_sel = df[(df.archivo == ESTRUCTURA[0]) & (df.seccion == ESTRUCTURA[1]) &
                 (df.periodo == "Anual") & (df.anio == anio_sel) &
                 (df.nivel == 1)].dropna(subset=["valor"])
    shares = dict(zip(est_sel.concepto, est_sel.valor))
    pri = shares.get("Actividades primarias", float("nan"))
    sec = shares.get("Actividades secundarias", float("nan"))
    ter = shares.get("Actividades terciarias", float("nan"))
    imp = shares.get("Impuestos sobre los productos, netos", float("nan"))
    prom_crec = var_anual[(var_anual.anio > anio_sel - 10) &
                          (var_anual.anio <= anio_sel)].valor.mean()

    with panel("Lectura rápida", f"Resumen del año {anio_sel}"):
        st.markdown(
            f'<div class="insights">'
            f'<div class="insight"><span class="dot"></span><span>El PIB '
            f'<b>{"creció" if (crec_anio_sel or 0) >= 0 else "se contrajo"} '
            f'{fmt_pct(abs(crec_anio_sel))}%</b> en {anio_sel}; el promedio de la '
            f'década previa fue {fmt_pct(prom_crec, 2)}% anual.</span></div>'
            f'<div class="insight"><span class="dot"></span><span>La rama más '
            f'dinámica fue <b>{mejor_txt}</b>; la de peor desempeño, '
            f'<b>{peor_txt}</b>.</span></div>'
            f'<div class="insight"><span class="dot"></span><span>Los servicios '
            f'aportan <b>{fmt_pct(ter)}%</b> del PIB, la industria '
            f'<b>{fmt_pct(sec)}%</b>, el campo <b>{fmt_pct(pri)}%</b> y los '
            f'impuestos a los productos <b>{fmt_pct(imp)}%</b>.</span></div>'
            f'<div class="insight"><span class="dot"></span><span>La mayor '
            f'contribución al crecimiento vino de <b>{top_contr_label}</b> '
            f'({top_contr_val:+.2f} puntos porcentuales).</span></div>'
            f'</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- Sectores

with tabs[1]:
    est2 = df[(df.archivo == ESTRUCTURA[0]) & (df.seccion == ESTRUCTURA[1]) &
              (df.periodo == "Anual") & (df.anio == anio_sel) &
              (df.nivel == 2)].dropna(subset=["valor"])
    var2 = df[(df.archivo == VARIACION[0]) & (df.seccion == VARIACION[1]) &
              (df.periodo == "Anual") & (df.anio == anio_sel) &
              (df.nivel == 2)].dropna(subset=["valor"])
    niv2 = df[(df.archivo == REAL[0]) & (df.seccion == REAL[1]) &
              (df.periodo == "Anual") & (df.anio == anio_sel) &
              (df.nivel == 2)].dropna(subset=["valor"])

    tab = (est2[["codigo", "concepto", "valor"]]
           .rename(columns={"valor": "estructura"})
           .merge(var2[["codigo", "concepto", "valor"]]
                  .rename(columns={"valor": "variacion"}),
                  on=["codigo", "concepto"], how="inner")
           .merge(niv2[["codigo", "concepto", "valor"]]
                  .rename(columns={"valor": "millones"}),
                  on=["codigo", "concepto"], how="left"))
    tab["etiqueta"] = [etiqueta(c, n) for c, n in zip(tab.codigo, tab.concepto)]
    tab["sector"] = tab.codigo.map(gran_sector)
    ranking = tab.sort_values("estructura", ascending=False).reset_index(drop=True)
    ranking["lugar"] = ranking.index + 1

    with panel(f"Crecimiento vs. participación · {anio_sel}",
               "Cada burbuja es una rama; su tamaño representa el PIB real "
               "anualizado y el color, el gran sector"):
        fig = go.Figure()
        for sector, sub in tab.groupby("sector"):
            tam = (sub.millones / tab.millones.max()) ** 0.5 * 46 + 8
            mostrar = [e if v >= 1.0 else "" for e, v in
                       zip(sub.etiqueta, sub.estructura)]
            fig.add_trace(go.Scatter(
                x=sub.variacion, y=sub.estructura, mode="markers+text",
                name=sector,
                marker=dict(size=tam, color=COLOR_SECTOR.get(sector, APAGADO),
                            opacity=0.85, line=dict(width=1, color="rgba(13,13,13,.7)")),
                text=mostrar, textposition="top center",
                textfont=dict(size=9.5, color=TINTA_2),
                customdata=sub[["etiqueta", "millones"]],
                hovertemplate="<b>%{customdata[0]}</b><br>"
                              "crecimiento %{x:.1f}%<br>"
                              "participación %{y:.1f}%<br>"
                              "PIB %{customdata[1]:,.0f} mdp<extra></extra>",
            ))
        fig.add_vline(x=0, line_color="rgba(255,255,255,.22)", line_width=1)
        fig.update_xaxes(title_text="crecimiento anual %", title_font=dict(size=11))
        fig.update_yaxes(title_text="participación en el PIB %",
                         title_font=dict(size=11))
        tema(fig, altura=430)
        fig.update_layout(hovermode="closest", margin=dict(l=8, r=16, t=32, b=8))
        st.plotly_chart(fig, width="stretch", config=CONFIG_PLOT)

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        with panel(f"Ramas más grandes · {anio_sel}",
                   "Participación en el PIB total"):
            top = ranking.head(10).sort_values("estructura")
            fig = go.Figure(go.Bar(
                x=top.estructura, y=top.etiqueta, orientation="h",
                marker=dict(color=[COLOR_SECTOR.get(s, APAGADO) for s in top.sector],
                            line=dict(width=0)),
                text=[f"{v:.1f}%" for v in top.estructura],
                textposition="outside", cliponaxis=False,
                textfont=dict(family="Red Hat Mono, monospace", size=11, color=TINTA_2),
                hovertemplate="%{y}: <b>%{x:.2f}%</b><extra></extra>",
            ))
            fig.update_xaxes(title_text="% del PIB", title_font=dict(size=11),
                             range=[0, top.estructura.max() * 1.22])
            fig.update_yaxes(tickfont=dict(size=11))
            tema(fig, altura=330, leyenda=False)
            fig.update_layout(hovermode="closest",
                              margin=dict(l=8, r=16, t=8, b=8))
            st.plotly_chart(fig, width="stretch", config=CONFIG_PLOT)

    with col_b:
        with panel(f"Contribución al crecimiento · {anio_sel}",
                   "Puntos porcentuales; excluye impuestos a los productos"):
            contr = df[(df.archivo == CONTRIBUCION[0]) &
                       (df.seccion == CONTRIBUCION[1]) &
                       (df.periodo == "Anual") & (df.anio == anio_sel) &
                       (df.nivel == 2)].dropna(subset=["valor"]).copy()
            contr["etiqueta"] = [etiqueta(c, n) for c, n in
                                 zip(contr.codigo, contr.concepto)]
            top_abs = contr.reindex(contr.valor.abs().sort_values(
                ascending=False).index).head(10)
            top_abs = top_abs.sort_values("valor")
            fig = go.Figure(go.Bar(
                x=top_abs.valor, y=top_abs.etiqueta, orientation="h",
                marker=dict(color=[VERDE if v >= 0 else ROJO for v in top_abs.valor],
                            line=dict(width=0)),
                text=[f"{v:+.2f}" for v in top_abs.valor],
                textposition="outside", cliponaxis=False,
                textfont=dict(family="Red Hat Mono, monospace", size=11, color=TINTA_2),
                hovertemplate="%{y}: <b>%{x:+.3f} pp</b><extra></extra>",
            ))
            fig.add_vline(x=0, line_color="rgba(255,255,255,.22)", line_width=1)
            lo, hi = top_abs.valor.min(), top_abs.valor.max()
            pad = max((hi - lo) * 0.18, 0.02)
            fig.update_xaxes(title_text="puntos porcentuales",
                             title_font=dict(size=11),
                             range=[min(lo, 0) - pad, max(hi, 0) + pad])
            fig.update_yaxes(tickfont=dict(size=11))
            tema(fig, altura=330, leyenda=False)
            fig.update_layout(hovermode="closest",
                              margin=dict(l=8, r=16, t=8, b=8))
            st.plotly_chart(fig, width="stretch", config=CONFIG_PLOT)

    with panel("Mapa de calor del crecimiento",
               "Variación porcentual anual por rama de actividad"):
        var_h = df[(df.archivo == VARIACION[0]) & (df.seccion == VARIACION[1]) &
                   (df.periodo == "Anual") & (df.nivel == 2) &
                   (df.anio.between(max(rango[0], 1993), rango[1]))].copy()
        var_h["etiqueta"] = [etiqueta(c, n) for c, n in
                             zip(var_h.codigo, var_h.concepto)]
        orden_ramas = (est2.sort_values("valor", ascending=False)
                       .set_index("codigo").concepto)
        etiquetas_orden = [etiqueta(c, n) for c, n in orden_ramas.items()]
        pivote = var_h.pivot_table(index="etiqueta", columns="anio",
                                   values="valor", aggfunc="first")
        pivote = pivote.reindex(etiquetas_orden)
        fig = go.Figure(go.Heatmap(
            z=pivote.values, x=pivote.columns, y=pivote.index,
            zmid=0, zmin=-15, zmax=15,
            colorscale=[[0, "#8f3438"], [0.25, "#5c2f31"], [0.5, "#1a1a19"],
                        [0.75, "#2f6b46"], [1, "#2fbf71"]],
            hovertemplate="%{y}<br>%{x}: <b>%{z:.1f}%</b><extra></extra>",
            colorbar=dict(title=dict(text="%", font=dict(size=10)),
                          tickfont=dict(size=10, color=APAGADO),
                          thickness=10, len=0.85,
                          outlinewidth=0),
        ))
        fig.update_yaxes(tickfont=dict(size=10.5), autorange="reversed")
        fig.update_xaxes(tickfont=dict(size=10.5))
        tema(fig, altura=520, leyenda=False)
        fig.update_layout(hovermode="closest", margin=dict(l=8, r=8, t=8, b=8))
        st.plotly_chart(fig, width="stretch", config=CONFIG_PLOT)

# ---------------------------------------------------------------- Explorar

with tabs[2]:
    fuente_hist = st.radio(
        "Fuente de las series",
        ["Detalle por ramas (1993–2026)", "Serie histórica (1980–2026)"],
        horizontal=True, key="fuente_explorar")

    if fuente_hist.startswith("Detalle"):
        base_exp = df[(df.archivo == REAL[0]) & (df.seccion == REAL[1])]
        etiquetas_map = {}
        for _, fila in (base_exp[["codigo", "concepto"]]
                        .drop_duplicates().iterrows()):
            txt = etiqueta(fila.codigo, fila.concepto)
            clave = txt if not fila.codigo else f"{txt} · {fila.codigo}"
            etiquetas_map[clave] = (fila.codigo, fila.concepto)
        opciones = sorted(etiquetas_map)
        predeterminadas = [k for k in opciones if etiquetas_map[k][0] in
                           ("aB.1bP", "31-33", "46", "23", "53")]
    else:
        base_exp = df[(df.archivo == HISTORICO[0]) &
                      (df.seccion == HISTORICO[1])]
        etiquetas_map = {}
        for _, fila in (base_exp[["codigo", "concepto"]]
                        .drop_duplicates().iterrows()):
            txt = ETIQUETAS_HISTORICO.get(fila.concepto, fila.concepto)
            etiquetas_map[txt] = (fila.codigo, fila.concepto)
        opciones = sorted(etiquetas_map)
        predeterminadas = [k for k in ("PIB", "Primarias", "Secundarias",
                                       "Terciarias") if k in opciones]

    sel = st.multiselect(
        "Series a comparar", opciones, default=predeterminadas,
        max_selections=8,
        key="historico" if fuente_hist.startswith("Serie") else "detalle")
    normalizar = st.toggle("Índice 100 al inicio del periodo", value=False)

    if sel:
        fig = go.Figure()
        filas_stats = []
        for i, clave in enumerate(sel):
            codigo, concepto = etiquetas_map[clave]
            if fuente_hist.startswith("Detalle"):
                sub = serie(REAL[0], REAL[1], "codigo", codigo, frecuencia)
                sub = sub[(sub.anio >= rango[0]) & (sub.anio <= rango[1])]
                anual_s = serie(REAL[0], REAL[1], "codigo", codigo, "Anual").copy()
                nombre_serie = etiqueta(codigo, concepto)
            else:
                sub = serie(HISTORICO[0], HISTORICO[1], "concepto", concepto,
                            frecuencia)
                sub = sub[(sub.anio >= rango[0]) & (sub.anio <= rango[1])]
                anual_s = serie(HISTORICO[0], HISTORICO[1], "concepto",
                                concepto, "Anual").copy()
                nombre_serie = ETIQUETAS_HISTORICO.get(
                    concepto, etiqueta(codigo, concepto))
            if not len(sub):
                continue
            y = sub.valor / 1e6
            if normalizar:
                base = y.iloc[0]
                y = y / base * 100 if base else y
            color = ACENTO if nombre_serie == "PIB" else \
                [TEAL, AMBAR, VIOLETA, "#f472b6", "#5aa9e6", "#b7c72e",
                 "#d97757"][i % 7]
            fig.add_trace(go.Scatter(
                x=sub.fecha if frecuencia == "Trimestral" else sub.anio,
                y=y, name=nombre_serie, mode="lines",
                line=dict(width=2, color=color),
                customdata=sub.etiqueta,
                hovertemplate="%{customdata}: <b>%{y:.2f}</b><extra></extra>",
            ))
            # estadísticas sobre la serie anual, dentro del rango elegido
            anual_s = anual_s[(anual_s.anio >= rango[0]) &
                              (anual_s.anio <= rango[1])]
            anual_s = anual_s.dropna(subset=["valor"]).sort_values("anio")
            anual_s["crec"] = anual_s.valor.pct_change() * 100
            crecs = anual_s.dropna(subset=["crec"])
            ultimo_s = anual_s.iloc[-1]
            crec_ult = crecs.iloc[-1].crec if len(crecs) else float("nan")
            if len(anual_s) >= 11:
                v0 = anual_s.valor.iloc[-11]
                v1 = anual_s.valor.iloc[-1]
                cagr10 = ((v1 / v0) ** (1 / 10) - 1) * 100 if v0 > 0 else float("nan")
            else:
                cagr10 = float("nan")
            mejor = crecs.loc[crecs.crec.idxmax()] if len(crecs) else None
            peor = crecs.loc[crecs.crec.idxmin()] if len(crecs) else None
            filas_stats.append({
                "Serie": nombre_serie,
                f"Valor {int(ultimo_s.anio)} (billones)": ultimo_s.valor / 1e6,
                "Var. último año (%)": crec_ult,
                "CAGR 10a (%)": cagr10,
                "Crec. medio (%)": crecs.crec.mean() if len(crecs) else float("nan"),
                "Volatilidad (pp)": crecs.crec.std() if len(crecs) else float("nan"),
                "Mejor año": f"{int(mejor.anio)} · {mejor.crec:+.1f}%" if mejor is not None else "—",
                "Peor año": f"{int(peor.anio)} · {peor.crec:+.1f}%" if peor is not None else "—",
            })

        if not filas_stats:
            st.info("No hay datos en el rango seleccionado.")
        else:
            with panel("Comparación de series",
                       "Billones de pesos a precios de 2018 · índice 100 si se normaliza"
                       if fuente_hist.startswith("Detalle")
                       else "Billones de pesos a precios de 2018 (1980–2026)"):
                tema(fig, altura=420)
                fig.update_layout(hovermode="x unified",
                                  margin=dict(l=8, r=12, t=32, b=8))
                if normalizar:
                    fig.update_yaxes(title_text="índice (inicio = 100)",
                                     title_font=dict(size=11))
                else:
                    fig.update_yaxes(title_text="billones de pesos",
                                     title_font=dict(size=11))
                fig.update_xaxes(
                    hoverformat="T%q %Y" if frecuencia == "Trimestral" else "%Y")
                st.plotly_chart(fig, width="stretch", config=CONFIG_PLOT)

            with panel("Estadísticas descriptivas",
                       "Calculadas sobre la serie anual del rango elegido; la "
                       "volatilidad es la desviación estándar del crecimiento"):
                stats_df = pd.DataFrame(filas_stats)
                formato = {c: "{:,.2f}" for c in stats_df.columns
                           if c not in ("Serie", "Mejor año", "Peor año")}
                st.dataframe(
                    stats_df.style.format(formato, na_rep="—"),
                    width="stretch", hide_index=True)
    else:
        st.info("Elige al menos una serie para comparar.")

# ---------------------------------------------------------------- Datos

with tabs[3]:
    secciones = {
        "Nivel (millones de pesos 2018)": REAL,
        "Variación porcentual anual": VARIACION,
        "Estructura porcentual": ESTRUCTURA,
        "Contribución a la variación": CONTRIBUCION,
        "Deflactor (índice 2018=100)": DEFLACTOR,
    }
    col_f1, col_f2, col_f3 = st.columns([1.1, 1.35, 1.75])
    with col_f1:
        seccion_txt = st.selectbox("Medida", list(secciones))
    with col_f2:
        busqueda = st.text_input("Buscar concepto", placeholder="p. ej. manufactura")
    with col_f3:
        niveles = st.multiselect("Niveles", [0, 1, 2, 3, 4],
                                 default=[0, 1, 2],
                                 format_func=lambda n: {
                                     0: "Agregados",
                                     1: "Gran sector",
                                     2: "Ramas",
                                     3: "Subramas",
                                     4: "Clases"}[n])

    archivo_t, seccion_t = secciones[seccion_txt]
    tabla = df[(df.archivo == archivo_t) & (df.seccion == seccion_t) &
               (df.periodo == "Anual") & (df.nivel.isin(niveles)) &
               (df.anio.between(rango[0], rango[1]))].dropna(subset=["valor"]).copy()
    if busqueda:
        tabla = tabla[tabla.concepto.str.contains(busqueda, case=False, na=False)]
    tabla["Concepto"] = [etiqueta(c, n) + (f" · {c}" if c else "")
                         for c, n in zip(tabla.codigo, tabla.concepto)]
    tabla = tabla.sort_values(["nivel", "codigo", "Concepto"])

    if len(tabla):
        pivote = tabla.pivot_table(index=["nivel", "Concepto"], columns="anio",
                                   values="valor", aggfunc="first")
        pivote.index = pivote.index.droplevel(0)
        formato = "{:,.2f}"
        st.dataframe(
            pivote.style.format(formato, na_rep="—"),
            width="stretch", height=520)
        n_series = tabla[["concepto", "codigo"]].drop_duplicates().shape[0]
        st.caption(
            f"{n_series} series · {len(pivote.columns)} años · "
            f"fuente: {pibt.NOMBRES_UNIDAD.get(archivo_t, archivo_t)}")
    else:
        st.info("No hay series que coincidan con los filtros.")

    csv = tabla[["archivo", "seccion", "concepto", "codigo", "nivel",
                 "anio", "periodo", "valor"]].to_csv(index=False).encode("utf-8-sig")
    st.download_button("Descargar CSV", data=csv,
                       file_name=f"pib_{seccion_t[:20].replace(' ', '_')}.csv",
                       mime="text/csv")

    with st.expander("Notas metodológicas y fuente"):
        st.markdown(
            f"**Producto:** {meta.get('NOMBRE', 'PIB Trimestral')}  \n"
            f"**Institución:** {meta.get('NOMBRE DE LA INSTITUCIÓN', 'INEGI')}  \n"
            f"**Cobertura:** {meta.get('DESCRIPCIÓN PERIODO', '')}  \n"
            f"**Actualización:** {meta.get('FECHA DE ACTUALIZACIÓN', '')}  \n"
            f"**Año base:** 2018. Las cifras trimestrales están anualizadas "
            f"(multiplicadas por cuatro).  \n"
            f"**Notas:** R = cifras revisadas; P = cifras preliminares; "
            f"NA = no aplica. La suma de parciales puede no coincidir con el "
            f"total por redondeo. Fuente: INEGI, Sistema de Cuentas "
            f"Nacionales de México.")
