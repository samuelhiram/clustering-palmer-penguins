# Proyecto Minería de Datos — Clustering de Palmer Penguins

Proyecto corto de minería de datos siguiendo prácticas de **Ciencia 2.0**: datos públicos, código abierto y experimentos reproducibles.

## Problema

¿Se pueden descubrir automáticamente grupos naturales de pingüinos a partir de sus características físicas usando algoritmos de **clustering no supervisado**? Comparamos K-Means, DBSCAN y Agglomerative Clustering sobre el dataset Palmer Penguins.

## Estructura del repositorio

```
proyecto-mineria-datos/
│
├── notebook.ipynb          # Notebook principal (Jupyter / Google Colab)
├── README.md
├── requirements.txt
├── data/
│   └── penguins.csv        # Dataset Palmer Penguins
└── images/                 # Figuras generadas por el notebook
```

## Dataset

**Palmer Penguins** — 344 observaciones de 3 especies (Adelie, Chinstrap, Gentoo) recolectadas en el archipiélago Palmer (Antártida) por la Dra. Kristen Gorman.

- Licencia: CC-0
- Fuente original: https://github.com/allisonhorst/palmerpenguins
- Variables: `bill_length_mm`, `bill_depth_mm`, `flipper_length_mm`, `body_mass_g`, `species`, `island`, `sex`

## Cómo ejecutar

### Opción A — Google Colab
1. Subir `notebook.ipynb` a Google Drive.
2. Abrirlo con Google Colab.
3. Ejecutar todas las celdas (`Runtime > Run all`).

### Opción B — Local
```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
jupyter notebook notebook.ipynb
```

## Reproducibilidad

Todas las semillas aleatorias están fijadas con `RANDOM_STATE = 42`. El notebook se ejecuta de principio a fin sin intervención manual.

## Métodos comparados

| Algoritmo | Hiperparámetros | Notas |
|---|---|---|
| K-Means | k=3 | Requiere número de clusters |
| DBSCAN | eps=0.5, min_samples=5 | Detecta ruido automáticamente |
| Agglomerative | n_clusters=3, linkage=ward | Jerárquico |

Métricas: **Silhouette Score**, **Adjusted Rand Index (ARI)** vs. la etiqueta verdadera de especie, y matriz de confusión.

## Autoría

Proyecto del curso de Minería de Datos — entrega 26 de mayo de 2026.
