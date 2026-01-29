#!/usr/bin/python3

import matplotlib.pyplot as plt
import numpy as np

def scatter_relationship_plot1(
        x_data=[10, 20, 30, 40, 50, 60, 70],
        y_data=[15, 25, 28, 45, 48, 55, 65],
        point_size=70,
        point_color="#4C72B0",
        point_alpha=0.8,
        point_legend="Data points",
        line_legend="Trend line - ",
        line_color="red",
        line_linewidth=2,
        line_linestyle="--",
        figsize=(6, 4),
        xlabel="Variable X",
        ylabel="Variable Y",
        axis_alpha=0.3,
        show_regression=True,
        output_filepath="scatter_relationship_plot1.png"
    ):
    fig, ax = plt.subplots(figsize=figsize)

    # --- Scatter plot com legenda ---
    scatter = ax.scatter(
        x_data,
        y_data,
        s=point_size,
        color=point_color,
        alpha=point_alpha,
        label=point_legend
    )

    # --- Regression line ---
    if show_regression:
        slope, intercept = np.polyfit(x_data, y_data, 1)
        x_fit = np.linspace(min(x_data), max(x_data), 100)
        y_fit = slope * x_fit + intercept

        # Legenda inclui slope e intercept
        label_line = line_legend + f"slope={slope:.2f}, intercept={intercept:.2f}"
        ax.plot(x_fit, 
                y_fit, 
                color=line_color, 
                linestyle=line_linestyle, 
                linewidth=line_linewidth, 
                label=label_line)

    # --- Axes & labels ---
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # --- Grid leve ---
    ax.set_axisbelow(True)
    ax.grid(axis="both", linestyle="--", alpha=axis_alpha)

    # --- Legend completa ---
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
    scatter_relationship_plot1()

