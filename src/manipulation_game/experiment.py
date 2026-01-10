from datetime import datetime
import os
from pathlib import Path
from typing import Literal
from pydantic import BaseModel

from manipulation_game.agent import GameResults, run_game
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
    timestamp: str
    experiment: Experiment
    game: Game
    results: GameResults

def experiment_games(exp: Experiment) -> list[Game]:
    games = []
    for i in range(exp.num_trials):
        sub_id = 0
        for city in exp.city:
            for a_scheming in exp.a_scheming:
                for a_model, b_model in exp.model_pairs:
                    games.append(Game(
                        num_iterations=1,
                        max_turns_per_conversation=10,
                        num_public_facts=0,
                        seed=exp.initial_seed + i,
                        sub_experiment_id=sub_id,
                        experiment_name=exp.experiment_name,
                        a_model=a_model,
                        a_scheming=a_scheming,
                        a_commission_percentage=10,
                        b_model=b_model,
                        b_num_hunches=0,
                        judge_model=exp.judge_model,
                        realistic_city=city,
                        realistic_dir="scripts/restaurants",
                        templateA_path="realistic/sys_templateA.jinja",
                        templateB_path="realistic/sys_templateB.jinja",
                    ))
                    sub_id += 1
    return games

def run_experiment(exp: Experiment):
    timestamp = datetime.now().isoformat()
    results_path = Path(__file__).parent.parent.parent / "results" / exp.experiment_name
    os.makedirs(results_path, exist_ok=True)
    for game in experiment_games(exp):
        sub_experiment_path = results_path / f"seed_{game.seed}_subexperiment_{game.sub_experiment_id}.json"
        if os.path.exists(sub_experiment_path):
            print(f"Skipping existing result: {sub_experiment_path}")
            continue
        print(f"Running game: {game}")
        result = run_game(game)
        print(result)
        experiment_result = ExperimentResult(
            timestamp=timestamp,
            experiment=exp,
            game=game,
            results=result,
        )
        sub_experiment_path.write_text(experiment_result.model_dump_json(indent=2))

if __name__ == "__main__":
    path = Path(__file__).parent.parent.parent / "experiment_example.json"
    exp_data = Experiment.model_validate_json(path.read_text())
    run_experiment(exp_data)