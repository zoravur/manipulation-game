from collections import Counter, defaultdict
from pathlib import Path
from matplotlib import pyplot as plt
import os
import argparse

from manipulation_game.experiment import ExperimentResult

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", type=str, help="Name of the experiment to plot")
    args = parser.parse_args()

    # Load data from a file corresponding to the experiment name
    results_path = Path(__file__).parent.parent.parent / "results" / args.experiment
    counts = defaultdict(Counter)

    with os.scandir(results_path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith(".json"):
                with open(entry.path, 'r') as f:
                    data = ExperimentResult.model_validate_json(f.read())
                    sub_id = data.game.sub_experiment_id
                    counts[(sub_id, "_rec")][data.results.recommended_restaurant] += 1
                    counts[(sub_id, "chosen")][data.results.chosen_restaurant] += 1

    values = set()
    for d in counts.values():
        values.update(d.keys())
    values = list(sorted(values))

    palette = plt.get_cmap('tab10')
    for x, (key, d) in enumerate(sorted(counts.items())):
        bottom = 0
        for i, value in enumerate(values):
            plt.bar(x, width=1, height=d[value], bottom=bottom, label=str(value) if x==0 else None, alpha=0.7, color=palette(i))
            bottom += d[value]
    plt.xticks(range(len(counts)), [f"{k[0]} {'(rec)' if k[1]=='_rec' else '(chosen)'}" for k in sorted(counts.keys())], rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.show()
