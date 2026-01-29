#!/usr/bin/python3


import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

def gantt_diagram1(
        task_list = [
            "Planejamento",
            "Desenvolvimento",
            "Testes",
            "Deploy"
        ], # Dados do Gantt
        start_list  = [0, 5, 8, 14],  # início de cada tarefa
        duration_list = [6, 7, 7, 5],  # duração de cada tarefa
        color="green",
        figsize=(8, 4),
        xlabel="Days",
        ylabel="Task",
        output_filepath="gantt_diagram1.png"
    ):
    # Criar figura
    fig, ax = plt.subplots(figsize=figsize)

    # Plotar barras horizontais
    ax.barh(task_list, duration_list, left=start_list, color=color)

    # Labels
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    ax.set_axisbelow(True)  # grid fica atrás das barras
    ax.grid(
        axis='x',
        linestyle='--',
        linewidth=0.6,
        alpha=0.3
    )

    plt.tight_layout(pad=0.5)
    plt.savefig(output_filepath, 
                bbox_inches='tight', 
                pad_inches=0.1, 
                dpi=600, 
                transparent=True)
                
if __name__ == '__main__':
    gantt_diagram1()
