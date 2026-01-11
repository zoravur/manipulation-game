from collections import Counter, defaultdict
from pathlib import Path
from matplotlib import pyplot as plt
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
    counts = defaultdict(Counter)
    games = {}

    with os.scandir(results_path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith(".json"):
                with open(entry.path, 'r') as f:
                    data = ExperimentResult.model_validate_json(f.read())
                    sub_id = data.game.sub_experiment_id
                    counts[(sub_id, "_rec")][data.results.recommended_restaurant] += 1
                    counts[(sub_id, "chosen")][data.results.chosen_restaurant] += 1
                    games[sub_id] = data.game

    summaries = summarize_games(games)

    values = set()
    for d in counts.values():
        values.update(d.keys())
    values = list(sorted(values))

    palette = plt.get_cmap('tab10')
    for x, (key, d) in enumerate(sorted(counts.items())):
        bottom = 0
        for i, value in enumerate(values):
            vstring = "unknown" if value == "" or value is None else str(value) 
            plt.bar(x, width=1, height=d[value], bottom=bottom, label=vstring if x==0 else None, alpha=0.7, color=palette(i))
            bottom += d[value]
    plt.xticks(range(len(counts)), [f"{summaries[k[0]]} {'(rec)' if k[1]=='_rec' else '(chosen)'}" for k in sorted(counts.keys())], rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.show()
