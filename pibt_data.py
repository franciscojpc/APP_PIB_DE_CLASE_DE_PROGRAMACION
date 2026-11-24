"""Carga y normalización de los tabulados del PIB Trimestral (INEGI, base 2018).

Cada hoja "Tabulado" apila varios bloques (millones de pesos, variación
porcentual anual, estructura porcentual, contribución a la variación), bajo un
encabezado común de años (fila 5) y periodos (fila 6). Cada concepto lleva
sangría jerárquica en la columna A.

El resultado es un DataFrame largo:
  archivo, unidad, seccion, concepto, codigo, nivel, anio, periodo, valor
"""

from __future__ import annotations

import glob
import os
import re

import pandas as pd

PERIODOS = ["T1", "T2", "T3", "T4", "6 Meses", "9 Meses", "Anual"]
PERIODOS_TRIMESTRALES = ["T1", "T2", "T3", "T4"]

NOMBRES_UNIDAD = {
    "PIBT_2.xlsx": "Series originales · Millones de pesos anualizados, precios de 2018",
    "PIBT_3.xlsx": "Series originales · Millones de pesos anualizados (precios corrientes)",
    "PIBT_4.xlsx": "Series originales · Índice de precios implícitos 2018 = 100",
    "PIBT_r_2.xlsx": "Valores constantes · Millones de pesos a precios de 2018",
    "PIBT_r_3.xlsx": "Valores constantes · Variación porcentual anual",
}

# Título del primer bloque de cada archivo (los demás bloques se detectan solos)
SECCION_INICIAL = {
    "PIBT_2.xlsx": "Millones de pesos a precios de 2018",
    "PIBT_3.xlsx": "Millones de pesos a precios corrientes",
    "PIBT_4.xlsx": "Índice de precios implícitos base 2018=100",
    "PIBT_r_2.xlsx": "Millones de pesos a precios de 2018",
    "PIBT_r_3.xlsx": "Variación porcentual anual",
}

TITULOS_SECCION = {
    "millones de pesos a precios de 2018",
    "millones de pesos a precios corrientes",
    "índice de precios implícitos base 2018=100",
    "variación porcentual anual",
    "estructura porcentual",
    "contribución a la variación nacional",
}


def _limpia_concepto(texto: str):
    """Devuelve (nombre, codigo, sangria) a partir de la celda con sangría."""
    bruto = str(texto)
    indent = len(bruto) - len(bruto.lstrip(" _"))
    limpio = bruto.strip(" _").strip()
    codigo, nombre = "", limpio
    if " - " in limpio:
        posible, resto = limpio.split(" - ", 1)
        if " " not in posible:  # el código nunca lleva espacios
            codigo, nombre = posible, resto.strip()
    return nombre, codigo, indent


def _mapa_niveles(indents):
    """Sangría -> nivel 0,1,2... usando los valores únicos presentes."""
    return {v: i for i, v in enumerate(sorted(set(indents)))}


def _columnas_periodo(raw: pd.DataFrame):
    """columna -> (año, periodo) a partir de las filas 5 y 6 del Excel."""
    fila_anios = raw.iloc[4].tolist()
    fila_periodos = raw.iloc[5].tolist()
    columnas = {}
    anio_actual = None
    for idx, val in enumerate(fila_anios):
        if idx == 0:
            continue
        if isinstance(val, str) and val.strip():
            anio_actual = int(re.sub(r"[^0-9]", "", val))
        periodo = fila_periodos[idx] if idx < len(fila_periodos) else None
        if anio_actual is None or not isinstance(periodo, str):
            continue
        periodo = periodo.strip().rstrip("RP")
        if periodo in PERIODOS:
            columnas[idx] = (anio_actual, periodo)
    return columnas


def cargar_archivo(path: str) -> pd.DataFrame:
    """Lee un tabulado apilado y lo devuelve en formato largo."""
    raw = pd.read_excel(path, sheet_name="Tabulado", header=None, engine="openpyxl")
    archivo = os.path.basename(path)
    unidad = NOMBRES_UNIDAD.get(archivo, archivo)
    columnas = _columnas_periodo(raw)

    seccion = SECCION_INICIAL.get(archivo, unidad)
    registros, niveles = [], []
    for fila in range(6, len(raw)):
        celda = raw.iat[fila, 0]
        if not isinstance(celda, str) or not celda.strip():
            continue
        nombre, codigo, indent = _limpia_concepto(celda)

        # ¿Título de un nuevo bloque? (algunos traen cifras en la misma fila)
        if nombre.strip().lower() in TITULOS_SECCION:
            seccion = nombre.strip()
            continue

        valores = [pd.to_numeric(raw.iat[fila, c], errors="coerce") for c in columnas]
        if all(pd.isna(v) for v in valores):
            continue  # notas y filas vacías

        for (anio, periodo), valor in zip(columnas.values(), valores):
            registros.append((seccion, nombre, codigo, indent, anio, periodo, valor))
        niveles.append(indent)

    df = pd.DataFrame(registros, columns=[
        "seccion", "concepto", "codigo", "sangria", "anio", "periodo", "valor"])
    df["nivel"] = df["sangria"].map(_mapa_niveles(niveles))
    df = df.drop(columns="sangria")
    df.insert(0, "archivo", archivo)
    df.insert(1, "unidad", unidad)
    return df


def cargar_todos(carpeta: str) -> pd.DataFrame:
    archivos = sorted(glob.glob(os.path.join(carpeta, "*.xlsx")))
    if not archivos:
        raise FileNotFoundError(f"No hay archivos .xlsx en {carpeta}")
    return pd.concat([cargar_archivo(a) for a in archivos], ignore_index=True)


CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")


def cargar_todos_cache(carpeta: str, cache_dir: str = CACHE_DIR) -> pd.DataFrame:
    """Igual que cargar_todos, pero reutiliza un parquet si los Excel no cambiaron."""
    archivos = sorted(glob.glob(os.path.join(carpeta, "*.xlsx")))
    if not archivos:
        raise FileNotFoundError(f"No hay archivos .xlsx en {carpeta}")
    ruta_cache = os.path.join(cache_dir, "pibt_long.parquet")
    if os.path.exists(ruta_cache):
        fuentes = archivos + [os.path.abspath(__file__)]
        if os.path.getmtime(ruta_cache) >= max(os.path.getmtime(a) for a in fuentes):
            return pd.read_parquet(ruta_cache)
    df = cargar_todos(carpeta)
    os.makedirs(cache_dir, exist_ok=True)
    df.to_parquet(ruta_cache, index=False)
    return df


def cargar_meta(path: str) -> dict:
    """Metadatos del INEGI (hoja MetaInfo) como diccionario."""
    raw = pd.read_excel(path, sheet_name="MetaInfo", header=None, engine="openpyxl")
    meta = {}
    for _, fila in raw.iterrows():
        if len(fila) >= 3 and isinstance(fila.iloc[1], str) and fila.iloc[1].strip():
            meta[fila.iloc[1].strip()] = fila.iloc[2]
    return meta


def agregar_trimestres(df: pd.DataFrame) -> pd.DataFrame:
    """Subconjunto trimestral con columna fecha (inicio de trimestre)."""
    trim = df[df["periodo"].isin(PERIODOS_TRIMESTRALES)].copy()
    trim["trimestre"] = trim["periodo"].str[1].astype(int)
    trim["fecha"] = pd.to_datetime(
        dict(year=trim["anio"], month=(trim["trimestre"] - 1) * 3 + 1, day=1))
    return trim.sort_values(["concepto", "fecha"])


if __name__ == "__main__":
    ruta = os.path.join(os.path.dirname(__file__), "tabulados_PIBT")
    df = cargar_todos(ruta)
    print(df.groupby(["archivo", "seccion"]).size())
    print(df[df["archivo"] == "PIBT_2.xlsx"]["nivel"].value_counts().sort_index())
    d = df.groupby(["archivo", "seccion", "concepto", "codigo"]).size()
    print("duplicados:", int((d > 1).sum()))
