import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde


def density_raincloud_boxplot( 
        data_dict = {
            "Grupo A": np.random.normal(loc=45, scale=4, size=60),
            "Grupo B": np.random.normal(loc=50, scale=3.5, size=60),
            "Grupo C": np.random.normal(loc=55, scale=5, size=60),
        },
        color_list = ["#FF5A5F", "#FFB400", "#007A87"],
        kde_steps=300, 
        kde_height=0.4, 
        kde_alpha=0.6,
        rain_height=0.25,
        rain_alpha=0.6,
        rain_size=20,
        boxplot_height=0.15,
        boxplot_color="#666666",
        boxplot_linewidth=1.5,
        xlabel="Value",
        ylabel="Groups",
        fontsize=15,
        output_filepath="density_raincloud_boxplot.png"
    ):

    GROUPS = list(data_dict.keys())

    # =========================
    # Figura
    # =========================
    fig, ax = plt.subplots(figsize=(7, 6))

    # =========================
    # Half violin + rain
    # =========================
    for i, group in enumerate(GROUPS):
        values = data_dict[group]

        # KDE
        kde = gaussian_kde(values)
        x = np.linspace(values.min(), values.max(), kde_steps)
        density = kde(x)

        # Normaliza largura do violino
        density = density / density.max() * kde_height

        # Half violin
        ax.fill_between(
            x,
            i,
            i + density,
            color=color_list[i],
            alpha=kde_alpha
        )

        # Rain (pontos)
        y_jitter = i + np.random.uniform(-rain_height, 0.0, size=len(values))
        ax.scatter(
            values,
            y_jitter,
            color=color_list[i],
            alpha=rain_alpha,
            s=rain_size
        )

    # =========================
    # Boxplot
    # =========================
    boxplot_data = [data_dict[g] for g in GROUPS]

    SHIFT = -rain_height/2.0
    POSITIONS = [i + SHIFT for i in range(len(GROUPS))]

    ax.boxplot(
        boxplot_data,
        vert=False,
        positions=POSITIONS,
        widths=boxplot_height,
        showfliers=False,
        showcaps=False,
        boxprops     = dict(color=boxplot_color, linewidth=boxplot_linewidth),
        whiskerprops = dict(color=boxplot_color, linewidth=boxplot_linewidth),
        medianprops  = dict(color=boxplot_color, linewidth=boxplot_linewidth)
    )

    # =========================
    # Eixos e título
    # =========================
    ax.set_yticks(range(len(GROUPS)))
    ax.set_yticklabels(GROUPS, fontsize=fontsize)

    ax.set_xlabel(xlabel, fontsize=fontsize)
    ax.set_ylabel(ylabel, fontsize=fontsize)
    #ax.set_title("Raincloud Plot com Dados Sintéticos", fontsize=18)

    ax.tick_params(labelsize=12)

    plt.tight_layout(pad=0.5)
    plt.savefig(output_filepath, 
                bbox_inches='tight', 
                pad_inches=0.1, 
                dpi=600, 
                transparent=True)

if __name__ == '__main__':
    density_raincloud_boxplot()

