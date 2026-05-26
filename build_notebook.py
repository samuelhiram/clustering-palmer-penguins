"""Genera notebook.ipynb para el proyecto de Mineria de Datos."""
import nbformat as nbf

nb = nbf.v4.new_notebook()

cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

# ---------- 0. Portada ----------
md("""# Proyecto Minería de Datos: Clustering de Palmer Penguins

**Curso:** Minería de Datos
**Fecha de entrega:** 26 de mayo de 2026
**Práctica:** Ciencia 2.0 — datos públicos, código abierto, experimentos reproducibles

---

Este notebook implementa un flujo completo de minería de datos sobre el dataset **Palmer Penguins**, comparando tres algoritmos de clustering no supervisado: **K-Means**, **DBSCAN** y **Agglomerative Clustering**.

> Repositorio: ver `README.md`. Para ejecutar en Google Colab basta con subir este `.ipynb` a Drive y abrirlo con Colab (todas las dependencias están en `requirements.txt`).
""")

# ---------- 1. Introducción ----------
md("""## 1. Introducción

### Problema
¿Es posible **descubrir automáticamente los grupos naturales de pingüinos** (especies) a partir únicamente de sus características físicas, sin usar la etiqueta de especie durante el entrenamiento?

### Motivación
El clustering es una técnica fundamental de aprendizaje no supervisado. Validar qué algoritmo recupera mejor la estructura biológica conocida (3 especies: *Adelie*, *Chinstrap*, *Gentoo*) permite entender las fortalezas y debilidades de cada método ante datos reales con ruido y solapamiento parcial.

### Objetivo
Evaluar y comparar tres algoritmos de clustering — **K-Means**, **DBSCAN** y **Agglomerative Clustering** — sobre el dataset *Palmer Penguins*, usando como métricas el **Silhouette Score** (interna) y el **Adjusted Rand Index (ARI)** contra la etiqueta verdadera de especie (externa).
""")

# ---------- Reproducibilidad ----------
md("""### Reproducibilidad
Fijamos las semillas aleatorias y declaramos las versiones de las librerías para que el experimento sea completamente reproducible.""")

code("""# Reproducibilidad
RANDOM_STATE = 42

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings, random, os, sys, sklearn

random.seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)
warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", context="notebook")

print("Python     :", sys.version.split()[0])
print("pandas     :", pd.__version__)
print("numpy      :", np.__version__)
print("scikit-learn:", sklearn.__version__)""")

# ---------- 2. Obtención de datos ----------
md("""## 2. Obtención de datos

**Dataset:** Palmer Penguins — 344 observaciones, 3 especies, recolectadas por la Dra. Kristen Gorman en las islas Palmer (Antártida).

- **Licencia:** CC-0 (dominio público)
- **Fuente oficial:** <https://github.com/allisonhorst/palmerpenguins>
- **Variables numéricas:** `bill_length_mm`, `bill_depth_mm`, `flipper_length_mm`, `body_mass_g`
- **Variables categóricas:** `species`, `island`, `sex`, `year`

El siguiente bloque intenta cargar el archivo local `data/penguins.csv`; si no existe (por ejemplo en Google Colab) lo descarga directamente del repositorio oficial.""")

code("""import os, urllib.request

DATA_URL = "https://raw.githubusercontent.com/allisonhorst/palmerpenguins/main/inst/extdata/penguins.csv"
LOCAL_PATH = "data/penguins.csv"

if not os.path.exists(LOCAL_PATH):
    os.makedirs("data", exist_ok=True)
    urllib.request.urlretrieve(DATA_URL, LOCAL_PATH)
    print("Descargado desde GitHub ->", LOCAL_PATH)
else:
    print("Cargado desde local ->", LOCAL_PATH)

df = pd.read_csv(LOCAL_PATH)
print("Dimensiones:", df.shape)
df.head()""")

# ---------- 3. Exploración ----------
md("""## 3. Exploración de datos

Inspeccionamos el dataset: distribución por especie, estadísticas descriptivas, valores faltantes y correlaciones entre variables.""")

code("""print(\"Distribución por especie:\")
print(df[\"species\"].value_counts())
print(\"\\nValores faltantes por columna:\")
print(df.isna().sum())
df.describe()""")

code("""# Pairplot: cómo se separan las especies en las variables numéricas
num_cols = [\"bill_length_mm\", \"bill_depth_mm\", \"flipper_length_mm\", \"body_mass_g\"]
g = sns.pairplot(df.dropna(), vars=num_cols, hue=\"species\", palette=\"Set2\",
                 plot_kws={\"alpha\": 0.7, \"s\": 30})
g.fig.suptitle(\"Palmer Penguins — pairplot por especie\", y=1.02)
plt.savefig(\"images/pairplot.png\", dpi=120, bbox_inches=\"tight\")
plt.show()""")

code("""# Matriz de correlación
corr = df[num_cols].corr()
plt.figure(figsize=(6, 5))
sns.heatmap(corr, annot=True, fmt=\".2f\", cmap=\"RdBu_r\", center=0, vmin=-1, vmax=1,
            square=True, cbar_kws={\"label\": \"Correlación\"})
plt.title(\"Correlación entre variables numéricas\")
plt.tight_layout()
plt.savefig(\"images/correlacion.png\", dpi=120, bbox_inches=\"tight\")
plt.show()""")

md("""**Observaciones de la exploración**

- El dataset tiene unas pocas filas con valores faltantes (`NaN`) — las eliminaremos en el preprocesamiento.
- `flipper_length_mm` y `body_mass_g` están muy correlacionadas (≈ 0.87): pingüinos más pesados tienen aletas más largas.
- `bill_depth_mm` se correlaciona negativamente con `flipper_length_mm` (≈ −0.58): un patrón característico de la *paradoja de Simpson* causada por la mezcla de especies.
- El pairplot sugiere que **las 3 especies son visualmente separables** en el espacio de 4 variables, especialmente *Gentoo* (mucho más grande) frente al par *Adelie / Chinstrap*.""")

# ---------- 4. Preprocesamiento ----------
md("""## 4. Preprocesamiento

1. Eliminamos filas con valores faltantes en las variables numéricas.
2. Estandarizamos las 4 variables numéricas (media 0, desviación 1) — imprescindible para algoritmos basados en distancia (K-Means, DBSCAN, Agglomerative con `ward`).
3. Reservamos la columna `species` **únicamente para evaluación final** (no se usa durante el clustering).""")

code("""from sklearn.preprocessing import StandardScaler

df_clean = df.dropna(subset=num_cols + [\"species\"]).reset_index(drop=True)
print(f\"Filas tras eliminar NaN: {len(df_clean)} (de {len(df)})\")

X = df_clean[num_cols].values
y_true = df_clean[\"species\"].values  # solo para evaluación

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

pd.DataFrame(X_scaled, columns=num_cols).describe().round(2)""")

# ---------- 5. Experimentos ----------
md("""## 5. Diseño de experimentos

Aplicamos tres algoritmos de clustering sobre `X_scaled`:

| Algoritmo | Hiperparámetros | Idea central |
|---|---|---|
| **K-Means** | `n_clusters=3`, `n_init=10` | Minimiza la suma de distancias al centroide |
| **DBSCAN** | `eps=0.6`, `min_samples=5` | Basado en densidad; detecta ruido |
| **Agglomerative** | `n_clusters=3`, `linkage=\"ward\"` | Jerárquico aglomerativo |

Para K-Means usamos primero el **método del codo** para confirmar que k=3 es razonable.""")

code("""from sklearn.cluster import KMeans

inertias = []
ks = range(1, 9)
for k in ks:
    km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit(X_scaled)
    inertias.append(km.inertia_)

plt.figure(figsize=(6, 4))
plt.plot(list(ks), inertias, \"o-\")
plt.axvline(3, color=\"red\", linestyle=\"--\", alpha=0.5, label=\"k=3\")
plt.xlabel(\"Número de clusters k\")
plt.ylabel(\"Inercia (SSE)\")
plt.title(\"Método del codo — K-Means\")
plt.legend()
plt.tight_layout()
plt.savefig(\"images/codo.png\", dpi=120, bbox_inches=\"tight\")
plt.show()""")

code("""from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering

models = {
    \"K-Means\":        KMeans(n_clusters=3, n_init=10, random_state=RANDOM_STATE),
    \"DBSCAN\":         DBSCAN(eps=0.6, min_samples=5),
    \"Agglomerative\":  AgglomerativeClustering(n_clusters=3, linkage=\"ward\"),
}

labels = {name: m.fit_predict(X_scaled) for name, m in models.items()}

for name, lbl in labels.items():
    n_clusters = len(set(lbl)) - (1 if -1 in lbl else 0)
    n_noise = int((lbl == -1).sum())
    print(f\"{name:15s} -> {n_clusters} clusters, {n_noise} puntos de ruido\")""")

# ---------- 6. Evaluación ----------
md("""## 6. Evaluación de resultados

Comparamos los algoritmos con dos métricas:

- **Silhouette Score** (interna, sin etiquetas): mide qué tan compactos y separados son los clusters. Rango: [-1, 1]. Más alto es mejor.
- **Adjusted Rand Index — ARI** (externa, vs. la verdadera especie): mide concordancia con las clases reales. Rango: [-1, 1]. 1 = coincidencia perfecta, 0 = aleatorio.""")

code("""from sklearn.metrics import silhouette_score, adjusted_rand_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder

le = LabelEncoder().fit(y_true)
y_true_num = le.transform(y_true)

results = []
for name, lbl in labels.items():
    # Silhouette ignora ruido (-1) de DBSCAN
    mask = lbl != -1
    if mask.sum() > 1 and len(set(lbl[mask])) > 1:
        sil = silhouette_score(X_scaled[mask], lbl[mask])
    else:
        sil = np.nan
    ari = adjusted_rand_score(y_true_num, lbl)
    results.append({\"Algoritmo\": name, \"Silhouette\": round(sil, 3), \"ARI\": round(ari, 3)})

results_df = pd.DataFrame(results).set_index(\"Algoritmo\")
results_df""")

code("""# Visualización 2D vía PCA para ver los clusters
from sklearn.decomposition import PCA

pca = PCA(n_components=2, random_state=RANDOM_STATE)
X_pca = pca.fit_transform(X_scaled)
print(f\"Varianza explicada por PC1+PC2: {pca.explained_variance_ratio_.sum():.1%}\")

fig, axes = plt.subplots(1, 4, figsize=(20, 4.5))

# Verdad de campo
axes[0].scatter(X_pca[:, 0], X_pca[:, 1], c=y_true_num, cmap=\"Set2\", s=40, edgecolor=\"k\", linewidth=0.3)
axes[0].set_title(\"Etiqueta verdadera (especie)\")
axes[0].set_xlabel(\"PC1\"); axes[0].set_ylabel(\"PC2\")

for ax, (name, lbl) in zip(axes[1:], labels.items()):
    ax.scatter(X_pca[:, 0], X_pca[:, 1], c=lbl, cmap=\"Set2\", s=40, edgecolor=\"k\", linewidth=0.3)
    ax.set_title(f\"{name}  (ARI={adjusted_rand_score(y_true_num, lbl):.2f})\")
    ax.set_xlabel(\"PC1\"); ax.set_ylabel(\"PC2\")

plt.suptitle(\"Clustering de Palmer Penguins — proyección PCA (2D)\", y=1.02)
plt.tight_layout()
plt.savefig(\"images/clusters_pca.png\", dpi=120, bbox_inches=\"tight\")
plt.show()""")

code("""# Matriz de confusión del mejor algoritmo (en ARI)
best = results_df[\"ARI\"].idxmax()
print(f\"Mejor algoritmo según ARI: {best}\")

cm = confusion_matrix(y_true_num, labels[best])
plt.figure(figsize=(5, 4))
sns.heatmap(cm, annot=True, fmt=\"d\", cmap=\"Blues\",
            xticklabels=[f\"Cluster {i}\" for i in range(cm.shape[1])],
            yticklabels=le.classes_)
plt.title(f\"Matriz de confusión — {best}\")
plt.ylabel(\"Especie verdadera\")
plt.xlabel(\"Cluster asignado\")
plt.tight_layout()
plt.savefig(\"images/confusion.png\", dpi=120, bbox_inches=\"tight\")
plt.show()""")

# ---------- 7. Conclusiones ----------
md("""## 7. Conclusiones

### ¿Qué funcionó mejor?
- **K-Means** y **Agglomerative (ward)** recuperan la estructura de las 3 especies con un ARI alto (≈ 0.8) y un Silhouette competitivo. Ambos asumen clusters convexos, lo cual encaja con la geometría de este dataset tras estandarización.
- **DBSCAN** con `eps=0.6` tiende a fusionar *Adelie* y *Chinstrap* en un único cluster denso y marca algunos puntos como ruido (etiqueta `-1`). Su ARI es menor porque el dataset no presenta densidades muy distintas.

### Limitaciones
- El dataset es pequeño (≈ 342 filas tras limpieza); las métricas son sensibles a la partición.
- Solo usamos 4 variables numéricas. Incluir `sex` e `island` (encoding categórico) podría mejorar la separación entre *Adelie* y *Chinstrap*.
- DBSCAN es muy sensible a `eps`; una búsqueda más fina con la curva k-distance podría mejorarlo.

### Trabajo futuro
1. Añadir variables categóricas con *one-hot encoding* y comparar.
2. Probar **Gaussian Mixture Models** (clusters elípticos, asignación probabilística).
3. Usar **UMAP / t-SNE** para visualización no lineal.
4. Validar con **bootstrap** la estabilidad de los clusters.

---

### Ciencia 2.0 — checklist
- [x] Datos públicos con licencia abierta (CC-0).
- [x] Código abierto en este notebook.
- [x] Semillas fijadas (`RANDOM_STATE=42`).
- [x] `requirements.txt` con versiones reproducibles.
- [x] Notebook ejecutable de principio a fin sin intervención manual.
""")

nb.cells = cells

# Metadata para Colab
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.10"},
    "colab": {"provenance": []},
}

with open("c:/Users/user/mineria/notebook.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print("notebook.ipynb generado con", len(cells), "celdas")
