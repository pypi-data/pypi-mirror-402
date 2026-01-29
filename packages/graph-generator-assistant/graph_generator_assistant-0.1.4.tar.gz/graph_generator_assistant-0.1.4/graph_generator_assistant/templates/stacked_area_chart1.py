#!/usr/bin/python3

import matplotlib.pyplot as plt
import numpy as np


def stacked_area_chart1(
        x_values = [2019, 2020, 2021, 2022, 2023],
        row_labels = ["Product A", "Product B", "Product C"],
        data = [
            [20, 25, 30, 35, 40],  # Product A
            [30, 35, 40, 38, 45],  # Product B
            [10, 15, 20, 25, 30]   # Product C
        ],
        colors = ["#4C72B0", "#DD8452", "#55A868"],
        area_alpha=0.8,
        figsize=(7, 4),
        xlabel="Year",
        ylabel="Total Sales",
        axis_alpha=0.3,
        output_filepath="stacked_area_chart1.png"
    ):
    data = np.array(data)

    fig, ax = plt.subplots(figsize=figsize)

    # --- Stacked area plot ---
    ax.stackplot(
        x_values,
        data,
        labels=row_labels,
        colors=colors,
        alpha=area_alpha
    )

    # --- Axes & labels ---
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # --- Grid (leve) ---
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle="--", alpha=axis_alpha)

    # --- Legend ---
    ax.legend(loc="upper left")

    plt.tight_layout(pad=0.5)

    plt.savefig(
        output_filepath,
        bbox_inches="tight",
        pad_inches=0.1,
        dpi=600,
        transparent=True
    )
    plt.show()


if __name__ == "__main__":
    stacked_area_chart1()

