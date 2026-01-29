#!/usr/bin/python3

import matplotlib.pyplot as plt
import squarify
import numpy as np


def treemap_chart1(
        labels = [ "Product A", "Product B", "Product C", "Service A", "Service B" ],
        data   = [40, 30, 20, 25, 15],
        colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2"],
        block_alpha = 0.85,
        text_fontsize = 10,
        text_color = "white",
        text_weight = "bold",
        figsize=(7, 4),
        output_filepath="treemap_chart1.png"
    ):
    fig, ax = plt.subplots(figsize=figsize)

    # --- Normalizar tamanhos ---
    sizes = np.array(data)

    # --- Treemap ---
    squarify.plot(
        sizes=sizes,
        label=labels,
        color=colors,
        alpha=block_alpha,
        ax=ax,
        text_kwargs={
            "fontsize": text_fontsize,
            "color": text_color,
            "weight": text_weight
        }
    )

    # --- Ajustes visuais ---
    #ax.set_title(title)
    ax.axis("off")

    plt.tight_layout(pad=0.5)

    plt.savefig(
        output_filepath,
        bbox_inches="tight",
        pad_inches=0.1,
        dpi=600,
        transparent=True
    )


if __name__ == "__main__":
    treemap_chart1()

