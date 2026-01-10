import os
from pathlib import Path
from typing import Literal
from pydantic import BaseModel

from manipulation_game.game import Game


class Experiment(BaseModel):
    experiment_name: str
    initial_seed: int
    num_trials: int
    city: list[str]
    a_scheming: list[bool]
    model_pairs: list[tuple[str, str]]
    judge_model: str
    measure: list[Literal["scheming","success"]]


class ExperimentResult(BaseModel):
    experiment_name: str
    seed: int
    game: Game


def experiment_games(exp: Experiment) -> list[Game]:
    games = []
    for i in range(exp.num_trials):
        seed = exp.initial_seed + i
        for a_scheming in exp.a_scheming:
            for a_model, b_model in exp.model_pairs:
                game = Game(
                    num_iterations=1,
                    max_turns_per_conversation=10,
                    num_public_facts=0,
                    restaurants=[f"Restaurant {j}" for j in range(1, 6)],
                    a_model=a_model,
                    a_scheming=a_scheming,
                    a_commission_restaurant=None,
                    a_commission_percentage=10,
                    b_model=b_model,
                    b_num_hunches=0,
                    judge_model=exp.judge_model,
                    realistic_city=exp.city[i % len(exp.city)],
                    realistic_dir="data/realistic_info",
                    templateA_path="templates/agent_a_template.jinja",
                    templateB_path="templates/agent_b_template.jinja",
                )
                games.append(game)
    return games

def run_experiment(exp: Experiment):
    results_path = Path(__file__).parent / "results" / f"{exp.experiment_name}_results.json"
    os.makedirs(results_path.parent, exist_ok=True)
    all_results = []


if __name__ == "__main__":
    path = Path(__file__).parent / "experiment_figure3.json"
    exp_data = Experiment.model_validate_json(path.read_text())
    run_experiment(exp_data)