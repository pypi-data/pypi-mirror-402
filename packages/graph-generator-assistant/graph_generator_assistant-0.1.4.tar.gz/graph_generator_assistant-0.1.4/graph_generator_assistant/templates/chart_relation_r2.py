#!/usr/bin/python3

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from collections import OrderedDict
from scipy.stats import pearsonr

def chart_relation_r2(
        data = pd.DataFrame({
            "mpg" :[21,21,22.8,21.4,18.7,18.1,14.3,16],
            "disp":[160,160,108,258,360,225,360,300],
            "hp"  :[110,110,93,110,175,105,245,110],
            "drat":[3.9,3.9,3.85,3.08,3.15,2.76,3.21,3]
        }),
        diag_plot="kde",      # "hist" ou "kde"
        hist_bins=10,
        hist_alpha=0.7,
        diagonal_color="#4C72B0",
        figsize=(7,7),
        point_size=30,
        point_alpha=0.7,
        point_color="#B04C72",
        axis_linestyle="--", 
        axis_alpha=0.2,
        r2_fontsize=10, 
        r2_color="black",
        show_r2=True,
        output_filepath="chart_relation_r2.png"
    ):

    if isinstance(data, dict):
        if not isinstance(data, OrderedDict):
            data = OrderedDict(data)
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise ValueError("data must be dict or DataFrame")

    features = df.columns
    n = len(features)

    fig, axes = plt.subplots(n, n, figsize=figsize)

    for i in range(n):
        for j in range(n):
            ax = axes[i,j]

            if i == j:
                # --- Diagonal ---
                if diag_plot == "hist":
                    ax.hist(df[features[i]], bins=hist_bins, color=diagonal_color, alpha=hist_alpha)
                elif diag_plot == "kde":
                    sns.kdeplot(df[features[i]], ax=ax, fill=True, color=diagonal_color)
                ax.set_xlabel(features[i])
                ax.set_ylabel('')
            elif i > j:
                # --- Inferior: scatter plot ---
                ax.scatter(df[features[j]], df[features[i]],
                           s=point_size, alpha=point_alpha, color=point_color)
                ax.set_xlabel(features[j])
                ax.set_ylabel(features[i])
            else:
                # --- Superior: R² ---
                ax.axis('off')
                if show_r2:
                    r, _ = pearsonr(df[features[j]], df[features[i]])
                    r2 = r**2
                    ax.annotate(f"R²={r2:.2f}", xy=(0.5, 0.5), xycoords='axes fraction',
                                fontsize=r2_fontsize, color=r2_color, ha='center', va='center')

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
    chart_relation_r2()

