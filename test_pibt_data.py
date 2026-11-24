"""Pruebas de humo del parser. Ejecutar: .venv/bin/python test_pibt_data.py"""

import os

import pandas as pd

import pibt_data as pibt

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tabulados_PIBT")


def main():
    df = pibt.cargar_todos(CARPETA)

    # 1. Los cinco archivos se leen y traen los bloques esperados
    esperado = {
        "PIBT_2.xlsx": 4,
        "PIBT_3.xlsx": 4,
        "PIBT_4.xlsx": 2,
        "PIBT_r_2.xlsx": 1,
        "PIBT_r_3.xlsx": 1,
    }
    for archivo, n_secciones in esperado.items():
        secciones = df[df.archivo == archivo].seccion.nunique()
        assert secciones == n_secciones, (archivo, secciones)

    # 2. Jerarquía completa hasta clase (nivel 4) en el detalle
    assert df[df.archivo == "PIBT_2.xlsx"].nivel.max() == 4

    # 3. No hay duplicados en la llave completa
    llave = ["archivo", "seccion", "concepto", "codigo", "anio", "periodo"]
    assert not df.duplicated(llave).any()

    # 4. PIB real anual 2018 (año base) y coherencia nominal/deflactor
    real = df[(df.archivo == "PIBT_2.xlsx") & (df.codigo == "aB.1bP") &
              (df.periodo == "Anual") & (df.anio == 2018)].valor.iloc[0]
    assert abs(real - 24_176_670.374) < 1

    def valor(archivo, seccion, anio):
        return df[(df.archivo == archivo) & (df.seccion == seccion) &
                  (df.codigo == "aB.1bP") & (df.periodo == "Anual") &
                  (df.anio == anio)].valor.iloc[0]

    nominal = valor("PIBT_3.xlsx", "Millones de pesos a precios corrientes", 2025)
    deflactor = valor("PIBT_4.xlsx", "Índice de precios implícitos base 2018=100", 2025)
    pib_2025 = valor("PIBT_2.xlsx", "Millones de pesos a precios de 2018", 2025)
    assert abs(nominal / pib_2025 * 100 - deflactor) < 0.01

    # 5. La estructura porcentual de los grandes sectores suma 100
    est = df[(df.archivo == "PIBT_2.xlsx") &
             (df.seccion == "Estructura porcentual") &
             (df.nivel == 1) & (df.periodo == "Anual") & (df.anio == 2025)]
    assert abs(est.valor.sum() - 100) < 0.01

    # 6. Serie histórica y detalle coinciden donde se traslapan
    hist = df[(df.archivo == "PIBT_r_2.xlsx") & (df.periodo == "Anual") &
              (df.anio == 2025) & (df.concepto == "Producto interno bruto")].valor.iloc[0]
    assert abs(hist - pib_2025) < 1

    print("OK — todas las pruebas pasaron:", len(df), "registros")


if __name__ == "__main__":
    main()
