from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import os
import argparse

from manipulation_game.experiment import ExperimentResult
from manipulation_game.game import Game

@dataclass
class GamePosition:
    row: int
    col: int
    row_label: str
    col_label: str

def summarize_games(games: dict[int,Game]) -> tuple[int, int, dict[int,GamePosition]]:
    include_scheming = len({g.a_scheming for g in games.values()}) > 1
    include_commission = len({g.a_commission_percentage for g in games.values()}) > 1
    include_model_pair = len({(g.a_model, g.b_model) for g in games.values()}) > 1
    results = {}

    row_labels = []
    col_labels = []
    for key, g in games.items():
        # parts = [f"City: {g.realistic_city}"]
        parts = []
        if include_scheming:
            parts.append(f"Scheming: {g.a_scheming}")
        if include_commission:
            parts.append(f"Commission: {g.a_commission_percentage}%")
        model_pair = f"{g.a_model.split('/')[-1]} / {g.b_model.split('/')[-1]}"
        summary = ", ".join(parts)
        if model_pair not in col_labels:
            col_labels.append(model_pair)
        if summary not in row_labels:
            row_labels.append(summary)
        results[key] = GamePosition(
            row=row_labels.index(summary),
            col=col_labels.index(model_pair),
            row_label=summary,
            col_label=model_pair,
        )
    return len(row_labels), len(col_labels), results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", type=str, help="Name of the experiment to plot")
    args = parser.parse_args()

    # Load data from a file corresponding to the experiment name
    results_path = Path(__file__).parent.parent.parent / "results" / args.experiment
    results = defaultdict(dict)
    games = {}

    n_iterations = 0

    with os.scandir(results_path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith(".json"):
                with open(entry.path, 'r') as f:
                    data = ExperimentResult.model_validate_json(f.read())
                    sub_id = data.game.sub_experiment_id
                    seed = data.game.seed
                    all_results = data.all_results
                    if all_results is None:
                        all_results = [data.results]

                    for i,result in enumerate(all_results):
                        results[(sub_id, f"rec{i}")][seed] = result.quality.get(result.recommended_restaurant, "unknown")
                        results[(sub_id, f"chosen{i}")][seed] = result.quality.get(result.chosen_restaurant, "unknown")
                    games[sub_id] = data.game
                    n_iterations = max(n_iterations, len(all_results))

    nrows, ncols, summaries = summarize_games(games)

    rcs = []
    for i in range(n_iterations):
        rcs.append(f"rec{i}")
        rcs.append(f"chosen{i}")

    fig, ax = plt.subplots(nrows, ncols, squeeze=False, figsize=(10,6))
    palette = {
        "bad": [0.8,0,0],
        "good": [0,0.6,0],
        "unknown": [0.5,0.5,0.5],
    }
    for key, summary in summaries.items():
        seeds = set()
        for k, d in results.items():
            if k[0] == key:
                seeds.update(d.keys())
        seeds = list(sorted(seeds))

        col = summary.col
        row = summary.row

        ax[row, col].set_title(summary.col_label)
        imdata = np.zeros((len(seeds), 2 * n_iterations, 3), dtype=float)
        for x2, rc in enumerate(rcs):
            bottom = 0
            for y, seed in enumerate(seeds):
                q = results[(key, rc)][seed]
                imdata[y, x2] = palette[q]
        im = ax[row, col].imshow(imdata, aspect='auto', vmin=-0.5, vmax=len(palette)-0.5)
        ax[row, col].set_xticks(range(len(rcs)), rcs)
        ax[row, col].set_yticks(range(len(seeds)), [f"Seed {s}" for s in seeds])
        ax[row, col].set_ylabel(summary.row_label)
    # Create legend handles and labels
    legend_handles = []
    legend_labels = []
    for q, color in palette.items():
        legend_handles.append(Rectangle((0,0),1,1, facecolor=color))
        legend_labels.append(q)
    
    ax[0,0].legend(legend_handles, legend_labels)
    plt.tight_layout()
    plt.show()
