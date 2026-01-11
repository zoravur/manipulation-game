from collections import Counter, defaultdict
from pathlib import Path
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import os
import argparse

from manipulation_game.experiment import ExperimentResult
from manipulation_game.game import Game

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
    args = parser.parse_args()

    # Load data from a file corresponding to the experiment name
    results_path = Path(__file__).parent.parent.parent / "results" / args.experiment
    restaurants = defaultdict(dict)
    games = {}

    with os.scandir(results_path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith(".json"):
                with open(entry.path, 'r') as f:
                    data = ExperimentResult.model_validate_json(f.read())
                    sub_id = data.game.sub_experiment_id
                    seed = data.game.seed
                    restaurants[(sub_id, "rec")][seed] = data.results.recommended_restaurant
                    restaurants[(sub_id, "chosen")][seed] = data.results.chosen_restaurant
                    games[sub_id] = data.game

    summaries = summarize_games(games)

    values = set()
    seeds = set()
    for d in restaurants.values():
        values.update(d.values())
        seeds.update(d.keys())
    values = list(sorted(values))
    seeds = list(sorted(seeds))

    fig, ax = plt.subplots(1, len(summaries), squeeze=False, figsize=(10,6))
    palette = plt.get_cmap('tab10')
    for x, (key, summary) in enumerate(summaries.items()):
        ax[0, x].set_title(summary)
        imdata = np.zeros((len(seeds), 2, 3), dtype=float)
        for x2, rc in enumerate(("rec", "chosen")):
            bottom = 0
            for y, seed in enumerate(seeds):
                restaurant = restaurants[(key, rc)][seed]
                i = values.index(restaurant)
                imdata[y, x2] = palette(i)[:3]
        im = ax[0, x].imshow(imdata, aspect='auto', cmap=palette, vmin=-0.5, vmax=len(values)-0.5)
        ax[0, x].set_xticks(range(2), ["Recommended", "Chosen"])
        ax[0, x].set_yticks(range(len(seeds)), [f"Seed {s}" for s in seeds])
    # Create legend handles and labels
    legend_handles = []
    legend_labels = []
    for i, value in enumerate(values):
        color = palette(i)[:3]
        legend_handles.append(Rectangle((0,0),1,1, facecolor=color))
        legend_labels.append(value)
    
    ax[0,0].legend(legend_handles, legend_labels)
    plt.tight_layout()
    plt.show()
