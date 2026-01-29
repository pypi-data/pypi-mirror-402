import seawolf as sw

import matplotlib.pyplot as plt
import seaborn as sns

# Datos de ejemplo para la gráfica apilada
categorias = ["A", "B", "C", "D"]
valores1 = [5, 7, 3, 4]
valores2 = [2, 3, 4, 1]

plt.style.use('petroff10')

fig, ax = plt.subplots()
ax.barh(categorias, valores1, label="Grupo 1", zorder=2)
ax.barh(categorias, valores2, left=valores1, label="Grupo 2", zorder=3)
ax.grid(axis="x", linestyle="--", alpha=0.7, zorder=99)
sw.show_values(
    ax=ax,
    kind="bar",
    loc="center",
    dec=1,
    xpad=0,
    kw_args={"color": "black", "fontsize": 10, "fontweight": "bold"},
)
sw.set_title(
    ax=ax,
    title="Gráfica de barras apiladas",
    loc="left",
    kw_args={"rotation": 0, "fontweight": "bold", "fontsize": 14, "color": "black"},
)
sw.set_subtitle(
    ax=ax,
    subtitle="Subtítulo de la gráfica",
    loc="left",
    kw_args={"fontsize": 10, "color": "gray"},
)
sw.set_legend(ax=ax, title="Grupos", label_fontsize=7, title_loc="left", ncols=2,
              kw_args={"reverse": True})

sw.theme(ax=ax, op="despine", top=True, right=True, despine_offset=5)
plt.tight_layout()
plt.show()
