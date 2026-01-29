#!/usr/bin/python3

import matplotlib.pyplot as plt
import numpy as np


def radar_chart1(
        data = {
            "Row A": {
                "Column 1": 40,
                "Column 2": 85,
                "Column 3": 30
            },
            "Row B": {
                "Column 1": 50,
                "Column 2": 35,
                "Column 3": 90
            },
            "Row C": {
                "Column 1": 100,
                "Column 2": 50,
                "Column 3": 60
            }
        },
        figsize=(6, 6),
        r_ticks = [25, 50, 75, 100],
        axis_alpha=0.9,
        plot_linewidth=2,
        plot_alpha=0.15,
        output_filepath="radar_chart1.png"
    ):
    categories = list(next(iter(data.values())).keys())
    n_vars = len(categories)

    angles = np.linspace(0, 2 * np.pi, n_vars, endpoint=False)
    angles_closed = np.append(angles, angles[0])

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    # --- Limites radiais (percentual) ---
    ax.set_ylim(0, 100)

    # --- Ticks radiais percentuais ---
    
    ax.set_yticks(r_ticks)
    ax.set_yticklabels([f"{v}%" for v in r_ticks])
    ax.set_rlabel_position(90)  # posição dos rótulos (% no topo)

    # --- Grid radial leve ---
    ax.yaxis.grid(True, linestyle="--", alpha=axis_alpha)
    ax.xaxis.grid(True, linestyle="--", alpha=axis_alpha)

    # --- Plot ---
    for label, values in data.items():
        stats = list(values.values())
        stats += stats[:1]

        ax.plot(angles_closed, stats, linewidth=plot_linewidth, label=label)
        ax.fill(angles_closed, stats, alpha=plot_alpha)

    # --- Manter eixos angulares ---
    ax.set_xticks(angles)
    ax.set_xticklabels([])

    # --- Rótulos tangenciais das categorias ---
    r_label = 108  # levemente fora do máximo

    for angle, label in zip(angles, categories):
        angle_deg = np.degrees(angle)

        rotation = angle_deg + 90

        ax.text(
            angle,
            r_label,
            label,
            rotation=rotation,
            rotation_mode="anchor",
            ha="center",
            va="center"
        )

    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    
    plt.tight_layout(pad=0.5)  
    
    plt.savefig(output_filepath, 
                bbox_inches='tight', 
                pad_inches=0.1, 
                dpi=600, 
                transparent=True)


if __name__ == "__main__":
    radar_chart1()

