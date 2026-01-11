from collections import Counter, defaultdict
from pathlib import Path
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import os
import argparse
from enum import Enum

from manipulation_game.experiment import ExperimentResult
from manipulation_game.game import Game

class PlotKind(str, Enum):
    outcome_matrix = "outcome_matrix"
    categorical_heatmap = "categorical_heatmap"

def render_categorical_heatmaps(
    summaries,
    results,
    n_iterations,
    palette,
    figsize=(16, 8),
):
    rcs = []
    for i in range(n_iterations):
        rcs.append(f"rec{i}")
        rcs.append(f"chosen{i}")

    fig, ax = plt.subplots(
        1,
        len(summaries),
        squeeze=False,
        figsize=figsize,
    )

    for col, (key, summary) in enumerate(summaries.items()):
        seeds = sorted({
            seed
            for (sub_id, _), d in results.items()
            if sub_id == key
            for seed in d.keys()
        })

        ax[0, col].set_title(
            summary,
            fontsize=9,
            rotation=90,
            ha="left",
            va="bottom",
        )

        imdata = np.zeros((len(seeds), len(rcs), 3), dtype=float)

        for x, rc in enumerate(rcs):
            for y, seed in enumerate(seeds):
                q = results[(key, rc)][seed]
                imdata[y, x] = palette[q]

        ax[0, col].imshow(imdata, aspect="auto")

        ax[0, col].set_xticks(range(len(rcs)))
        ax[0, col].set_xticklabels(rcs, rotation=90, fontsize=8)

        ax[0, col].set_yticks(range(len(seeds)))
        ax[0, col].set_yticklabels(
            [f"Seed {s}" for s in seeds],
            fontsize=8,
        )

    legend_handles = [
        Rectangle((0, 0), 1, 1, facecolor=color)
        for color in palette.values()
    ]
    ax[0, 0].legend(
        legend_handles,
        list(palette.keys()),
        loc="upper left",
    )

    plt.tight_layout(pad=2.0)
    plt.subplots_adjust(bottom=0.15, top=0.65)
    plt.show()


def render_outcome_matrix(
    summaries,
    results,
    n_iterations,
    palette,
):
    import pprint
    # pprint.pprint(f"{summaries=}")
    print(pprint.pprint(results))
    # print(f"{n_iterations=}")
    # print(f"{palette=}")

def summarize_games(games: dict[int,Game]) -> dict[int,str]:
    include_scheming = len({g.a_scheming for g in games.values()}) > 1
    include_commission = len({g.a_commission_percentage for g in games.values()}) > 1
    include_model_pair = len({(g.a_model, g.b_model) for g in games.values()}) > 1
    summaries = {}
    for key, g in games.items():
        # parts = [f"City: {g.realistic_city}"]
        parts = []
        if include_scheming:
            parts.append(f"Scheming: {g.a_scheming}")
        if include_commission:
            parts.append(f"Commission: {g.a_commission_percentage}%")
        if include_model_pair:
            parts.append(f"A: {g.a_model} / B: {g.b_model}")
        summaries[key] = ", ".join(parts)
    return summaries

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", type=str, help="Name of the experiment to plot")
    parser.add_argument("--plot_kind", type=PlotKind, choices=list(PlotKind), default=PlotKind.categorical_heatmap, help="Plot type to render")
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

    summaries = summarize_games(games)

    palette = { "bad": [0.8,0,0], "good": [0,0.6,0], "unknown": [0.5,0.5,0.5], }

    if args.plot_kind == PlotKind.categorical_heatmap:
        render_categorical_heatmaps(
            summaries=summaries,
            results=results,
            n_iterations=n_iterations,
            palette=palette,
        )
    elif args.plot_kind == PlotKind.outcome_matrix:
        render_outcome_matrix(
            summaries=summaries,
            results=results,
            n_iterations=n_iterations,
            palette=palette,
        )
