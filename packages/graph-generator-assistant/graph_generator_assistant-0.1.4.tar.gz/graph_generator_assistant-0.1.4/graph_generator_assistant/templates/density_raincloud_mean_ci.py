import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde


def density_raincloud_mean_ci(
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
        ci_level=0.95,
        mean_color="#222222",
        mean_size=80,
        ci_linewidth=2.5,
        xlabel="Value",
        ylabel="Groups",
        fontsize=15,
        output_filepath="density_raincloud_mean_ci.png"
    ):

    GROUPS = list(data_dict.keys())
    z = 1.96 if ci_level == 0.95 else 1.0  # simples e claro

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
        density = density / density.max() * kde_height

        ax.fill_between(
            x,
            i,
            i + density,
            color=color_list[i],
            alpha=kde_alpha
        )

        # Rain
        y_jitter = i + np.random.uniform(-rain_height, 0.0, size=len(values))
        ax.scatter(
            values,
            y_jitter,
            color=color_list[i],
            alpha=rain_alpha,
            s=rain_size
        )

    # =========================
    # Mean + Confidence Interval
    # =========================
    SHIFT = -rain_height / 2.0

    for i, group in enumerate(GROUPS):
        values = data_dict[group]

        mean = np.mean(values)
        sem  = np.std(values, ddof=1) / np.sqrt(len(values))
        ci   = z * sem

        y = i + SHIFT

        # CI line
        ax.plot(
            [mean - ci, mean + ci],
            [y, y],
            color=mean_color,
            linewidth=ci_linewidth
        )

        # Mean point
        ax.scatter(
            mean,
            y,
            color=mean_color,
            s=mean_size,
            zorder=5
        )

    # =========================
    # Eixos
    # =========================
    ax.set_yticks(range(len(GROUPS)))
    ax.set_yticklabels(GROUPS, fontsize=fontsize)

    ax.set_xlabel(xlabel, fontsize=fontsize)
    ax.set_ylabel(ylabel, fontsize=fontsize)

    ax.tick_params(labelsize=12)
    
    plt.tight_layout(pad=0.5)
    plt.savefig(output_filepath, 
                bbox_inches='tight', 
                pad_inches=0.1, 
                dpi=600, 
                transparent=True)

if __name__ == '__main__':
    density_raincloud_mean_ci()

