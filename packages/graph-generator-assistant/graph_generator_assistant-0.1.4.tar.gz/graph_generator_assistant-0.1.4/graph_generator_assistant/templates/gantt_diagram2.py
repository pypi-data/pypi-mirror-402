#!/usr/bin/python3


import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt

def gantt_diagram2(
        task_list = ["Planejamento", "Desenvolvimento", "Testes"],
        start_list = [
            dt.date(2026, 1, 1),
            dt.date(2026, 1, 10),
            dt.date(2026, 1, 25)
        ],
        end_list = [
            dt.date(2026, 1, 9),
            dt.date(2026, 1, 24),
            dt.date(2026, 2, 5)
        ],
        color="green",
        figsize=(8, 4),
        rotation=45,
        xlabel="Date",
        ylabel="Task",
        output_filepath="gantt_diagram2.png"
    ):
    
    duracao = [(f - i).days for i, f in zip(start_list, end_list)]

    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(task_list, duracao, left=start_list, color=color)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # 🔹 Formatar eixo X como data
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))

    # 🔹 Melhorar legibilidade
    plt.xticks(rotation=rotation)

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
    gantt_diagram2()
