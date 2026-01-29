#!/usr/bin/python3

import matplotlib.pyplot as plt
import numpy as np


def bubble_chart2(
        labels = ["A", "B", "Equipe C", "D"],
        x_data = [70, 60, 90, 50],
        y_data = [85, 75, 70, 65],
        z_data = [200, 120, 300, 100],
        bubble_size=10,
        bubble_alpha=0.80,
        bubble_text_color="black",
        bubble_text_x_factor=0.00,
        bubble_text_y_factor=0.07,
        bubble_text_fontsize=9,
        axes_x_factor=0.12,
        axes_y_factor=0.08,
        xlabel="X",
        ylabel="Y",
        colorbar_label="Z",
        cmap="viridis",
        figsize=(5, 4),
        output_filepath="bubble_chart2.png"
    ):

    fig, ax = plt.subplots(figsize=figsize)

    # --- Scatter ---
    sizes = np.array(z_data) * bubble_size
    sc = ax.scatter(
        x_data,
        y_data,
        s=sizes,
        c=z_data,                 # 🔹 cores ligadas ao z_data
        cmap=cmap,
        alpha=bubble_alpha
    )

    # --- Ajustar limites dos eixos (evita bolhas cortadas) ---
    space = np.sqrt(np.max(sizes))

    ax.set_xlim(
        min(x_data) - axes_x_factor * space,
        max(x_data) + axes_x_factor * space
    )
    ax.set_ylim(
        min(y_data) - axes_y_factor * space,
        max(y_data) + axes_y_factor * space
    )

    # --- Texto nas bolhas ---
    for i, label in enumerate(labels):
        ax.text(
            x_data[i] + bubble_text_x_factor * np.sqrt(sizes[i]),
            y_data[i] + bubble_text_y_factor * np.sqrt(sizes[i]),
            label,
            ha="center",
            va="center",
            fontsize=bubble_text_fontsize,
            color=bubble_text_color
        )

    # --- Labels ---
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # --- Colorbar ---
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(colorbar_label)

    # --- Grid leve ---
    ax.set_axisbelow(True)
    ax.grid(axis="both", linestyle="--", alpha=0.3)

    plt.tight_layout(pad=0.5)

    plt.savefig(
        output_filepath,
        bbox_inches='tight',
        pad_inches=0.1,
        dpi=600,
        transparent=True
    )


if __name__ == "__main__":
    bubble_chart2()

