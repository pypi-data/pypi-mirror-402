#!/usr/bin/python3

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from collections import OrderedDict

def chart_relation_class(
        data = pd.DataFrame({
            "feature1":[1,2,3,4,5,6,7,8,9],
            "feature2":[9,8,7,6,5,4,3,2,1],
            "feature3":[2,3,2,3,2,3,2,3,2]
        }),
        labels = ["A","A","A","B","B","B","C","C","C"],
        palette=None, #palete = ["red","green","blue"]
        diag_plot="kde",
        hist_bins=10,
        hist_alpha=0.7,
        diagonal_color="#4C72B0",
        figsize=(7,7),
        point_size=40,
        point_alpha=0.8,
        axis_linestyle="--", 
        axis_alpha=0.2,
        legend_title="Class",
        output_filepath="chart_relation_class.png"
    ):

    # --- Convert dict to DataFrame ---
    if isinstance(data, dict):
        if not isinstance(data, OrderedDict):
            data = OrderedDict(data)
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise ValueError("data must be dict or DataFrame")

    if len(labels) != len(df):
        raise ValueError("Length of labels must match number of rows in data")
    
    features = df.columns
    n = len(features)

    # --- Color palette ---
    if palette is None:
        unique_labels = pd.Series(labels).unique()
        palette = dict(zip(unique_labels, sns.color_palette("Set2", len(unique_labels))))

    fig, axes = plt.subplots(n, n, figsize=figsize)

    for i in range(n):
        for j in range(n):
            ax = axes[i,j]

            if i == j:
                # Diagonal: hist/KDE
                if diag_plot == "hist":
                    ax.hist(df[features[i]], bins=hist_bins, color=diagonal_color, alpha=hist_alpha)
                elif diag_plot == "kde":
                    sns.kdeplot(df[features[i]], ax=ax, fill=True, color=diagonal_color)
                ax.set_xlabel(features[i])
                ax.set_ylabel('')
            elif i > j:
                # Inferior: scatter colorido por label
                for label_val in pd.Series(labels).unique():
                    mask = (labels == label_val) if isinstance(labels, pd.Series) else [l==label_val for l in labels]
                    ax.scatter(df.loc[mask, features[j]], df.loc[mask, features[i]],
                               s=point_size, alpha=point_alpha, color=palette[label_val])
                ax.set_xlabel(features[j])
                ax.set_ylabel(features[i])
            else:
                # Superior: vazio, exceto a quina superior direita
                ax.axis('off')
                if i == 0 and j == n-1:
                    # Legenda na quina superior direita
                    handles = [plt.Line2D([], [], marker='o', linestyle='', color=palette[val], label=str(val))
                               for val in pd.Series(labels).unique()]
                    ax.legend(handles=handles, title=legend_title, loc='center', frameon=False)

            ax.grid(axis="both", linestyle=axis_linestyle, alpha=axis_alpha)

    plt.tight_layout(pad=0.5)
    plt.savefig(output_filepath,
                bbox_inches='tight',
                pad_inches=0.1,
                dpi=600,
                transparent=True)
    plt.close(fig)


# --- Exemplo ---
if __name__ == "__main__":
    chart_relation_class()

