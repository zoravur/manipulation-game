import os
from pathlib import Path
from typing import Literal
from pydantic import BaseModel


class Experiment(BaseModel):
    experiment_name: str
    initial_seed: int
    num_trials: int
    city: list[str]
    a_scheming: list[bool]
    model_pairs: list[tuple[str, str]]
    judge_model: str
    measure: list[Literal["scheming","success"]]


def run_experiment(exp: Experiment):
    results_path = Path(__file__).parent / "results" / f"{exp.experiment_name}_results.json"
    os.path.makedirs()

if __name__ == "__main__":
    path = Path(__file__).parent / "experiment_figure3.json"
    exp_data = Experiment.model_validate_json(path.read_text())
    run_experiment(exp_data)