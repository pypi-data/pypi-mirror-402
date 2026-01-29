#!/usr/bin/python3

import matplotlib.pyplot as plt
import numpy as np


def clustered_bar_chart1(
        columns_categories = ["Quality", "Productivity", "Efficiency"],
        group_labels = ["Team A", "Team B", "Team C"],
        data = [
            [85, 78, 90],   # Team A
            [70, 82, 88],   # Team B
            [90, 75, 85]    # Team C
        ],
        colors=["#4C72B0", "#DD8452", "#55A868"],
        figsize=(7, 4),
        ylabel="Score (%)",
        xlabel="Metrics",
        output_filepath="clustered_bar_chart1.png"
    ):
    data = np.array(data)

    n_groups = len(group_labels)
    n_categories = len(columns_categories)

    x = np.arange(n_categories)
    bar_width = 0.8 / n_groups

    fig, ax = plt.subplots(figsize=figsize)

    # --- Cores padrão (se não forem fornecidas) ---
    if colors is None:
        colors = plt.cm.tab10.colors

    # --- Plot bars ---
    for i in range(n_groups):
        ax.bar(
            x + i * bar_width,
            data[i],
            width=bar_width,
            label=group_labels[i],
            color=colors[i % len(colors)]
        )

    # --- Axes & labels ---
    ax.set_xticks(x + bar_width * (n_groups - 1) / 2)
    ax.set_xticklabels(columns_categories)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # --- Grid (leve) ---
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    # --- Legend ---
    ax.legend()

    plt.tight_layout(pad=0.5)  
    
    plt.savefig(
        output_filepath,
        bbox_inches='tight',
        pad_inches=0.1,
        dpi=600,
        transparent=True
    )


if __name__ == "__main__":
    clustered_bar_chart1()

