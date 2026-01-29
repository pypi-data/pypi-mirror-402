#!/usr/bin/python3

import matplotlib.pyplot as plt
import numpy as np


def stacked_bar_chart1(
        columns_categories = ["Team A", "Team B", "Team C", "Team D"],
        stack_labels = ["Row1", "Row2", "Row3"],
        data = [
            [40, 30, 20, 10],   # Row1
            [25, 35, 30, 20],   # Row2
            [35, 25, 50, 40]    # Row3
        ],
        colors = ["#4C72B0", "#DD8452", "#55A868"],
        figsize=(7, 4),
        ylabel="Score",
        xlabel="Teams",
        axis_alpha=0.4,
        output_filepath="stacked_bar_chart1.png"
    ):
    data = np.array(data)

    n_stacks = len(stack_labels)
    x = np.arange(len(columns_categories))

    fig, ax = plt.subplots(figsize=figsize)

    bottom = np.zeros(len(columns_categories))

    # --- Plot stacked bars ---
    for i in range(n_stacks):
        ax.bar(
            x,
            data[i],
            bottom=bottom,
            label=stack_labels[i],
            color=colors[i % len(colors)]
        )
        bottom += data[i]

    # --- Axes & labels ---
    ax.set_xticks(x)
    ax.set_xticklabels(columns_categories)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # --- Grid (leve) ---
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle="--", alpha=axis_alpha)

    # --- Legend ---
    ax.legend()

    plt.tight_layout(pad=0.5)

    plt.savefig(
        output_filepath,
        bbox_inches="tight",
        pad_inches=0.1,
        dpi=600,
        transparent=True
    )


if __name__ == "__main__":
    stacked_bar_chart1()

