# Tablero del PIB de México

Dashboard interactivo del **Producto Interno Bruto Trimestral** del INEGI
(año base 2018), construido con Streamlit y Plotly a partir de los tabulados
en `tabulados_PIBT/`.

## Ejecutar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run dashboard.py
```

Abre <http://localhost:8501>.

Pruebas del parser:

```bash
.venv/bin/python test_pibt_data.py
```

## Qué incluye

- **Panorama** — serie trimestral real o nominal (1993–2026), crecimiento por
  gran sector y composición del PIB (área apilada), más una lectura rápida
  automática del año seleccionado.
- **Sectores** — dispersión crecimiento vs. participación de las 20 ramas,
  ranking de participación, contribución al crecimiento y mapa de calor anual.
- **Explorar** — comparación de hasta 8 series (detalle por ramas 1993–2026 o
  serie histórica de agregados 1980–2026), normalización a índice 100 y
  estadísticas descriptivas (CAGR, crecimiento medio, volatilidad, mejor y
  peor año).
- **Datos** — tabla pivote por año a nivel de agregados, gran sector, ramas,
  subramas y clases, con búsqueda y descarga en CSV.

Filtros globales en la barra lateral: rango de años, año de análisis, serie
(real/nominal) y frecuencia (trimestral/anual).

## Fuente

INEGI, Sistema de Cuentas Nacionales de México, Producto Interno Bruto
Trimestral, año base 2018. Actualización: 23 de noviembre de 2026.
Cifras trimestrales anualizadas (×4); R = revisadas, P = preliminares.

## Archivos

| Archivo | Descripción |
| --- | --- |
| `dashboard.py` | Aplicación Streamlit (interfaz, gráficas y estilo). |
| `pibt_data.py` | Parser de los Excel de INEGI y caché en parquet. |
| `tabulados_PIBT/` | Tabulados originales (`PIBT_2`, `PIBT_3`, `PIBT_4`, `PIBT_r_2`, `PIBT_r_3`). |
| `.streamlit/config.toml` | Tema oscuro del tablero. |

La primera ejecución tarda unos segundos porque lee los cinco Excel; después
se reutiliza `.cache/pibt_long.parquet` (se regenera si cambia algún archivo).
