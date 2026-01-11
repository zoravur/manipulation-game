from datetime import datetime
import os
from pathlib import Path
import random
from typing import Literal, Optional
from pydantic import BaseModel

from manipulation_game.agent import GameResults, run_game
from manipulation_game.game import Game, hash_game


class Experiment(BaseModel):
    experiment_name: str
    initial_seed: int
    num_trials: int
    num_iterations: int = 1
    city: list[str]   # should set to [] for >1 iteration to allow it to choose randomly
    a_scheming: list[bool]
    a_commission_percentage: list[int]
    model_pairs: list[tuple[str, str]]
    judge_model: str
    measure: list[Literal["scheming","success"]]


class ExperimentResult(BaseModel):
    timestamp: str
    experiment: Experiment
    game: Game
    results: GameResults
    all_results: Optional[list[GameResults]] = None

def experiment_games(exp: Experiment) -> list[Game]:
    games = []
    seed = exp.initial_seed
    random.seed(seed)
    for i in range(exp.num_trials):
        sub_id = 0
        if len(exp.city) == 0:
            # Pick cities randomly
            available_cities = []
            with os.scandir(Path(__file__).parent.parent.parent / "scripts" / "restaurants") as entries:
                for entry in entries:
                    if entry.is_dir() and entry.name != "honolulu":
                        available_cities.append(entry.name)
            city_lists = [available_cities]  # one option, multiple cities
        else:
            assert exp.num_iterations == 1
            city_lists = [[c] for c in exp.city]  # multiple options, one city each
        for city_list in city_lists:
            for a_scheming in exp.a_scheming:
                for a_commission_percentage in exp.a_commission_percentage:
                    for a_model, b_model in exp.model_pairs:
                        games.append(Game(
                            num_iterations=exp.num_iterations,
                            max_turns_per_conversation=10,
                            num_public_facts=0,
                            seed=seed,
                            sub_experiment_id=sub_id,
                            experiment_name=exp.experiment_name,
                            a_model=a_model,
                            a_scheming=a_scheming,
                            a_commission_percentage=a_commission_percentage,
                            b_model=b_model,
                            b_num_hunches=0,
                            judge_model=exp.judge_model,
                            city_list=city_list,
                            realistic_city="",
                            realistic_dir="scripts/restaurants/city_jsons_augmented",
                            templateA_path="dynamic_with_continuations/sys_templateA.jinja",
                            templateB_path="dynamic_with_continuations/sys_templateB.jinja",
                        ))
                        sub_id += 1
                        seed += 1
    return games
    

def run_experiment(exp: Experiment):
    timestamp = datetime.now().isoformat()
    results_path = Path(__file__).parent.parent.parent / "results" / exp.experiment_name
    os.makedirs(results_path, exist_ok=True)
    for game in experiment_games(exp):
        game_hash = hash_game(game)
        sub_experiment_path = results_path / f"seed_{game.seed}_subexperiment_{game.sub_experiment_id}_hash_{game_hash}.json"
        if os.path.exists(sub_experiment_path):
            print(f"Skipping existing result: {sub_experiment_path}")
            continue
        print(f"Running game: {game}")
        results = run_game(game)
        for r in results:
            print(f"Recommended: {r.recommended_restaurant}, Chosen: {r.chosen_restaurant}")
        experiment_result = ExperimentResult(
            timestamp=timestamp,
            experiment=exp,
            game=game,
            results=results[0],
            all_results=results,
        )
        sub_experiment_path.write_text(experiment_result.model_dump_json(indent=2))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", type=str, help="Name of experiment to run")
    args = parser.parse_args()
    path = Path(__file__).parent.parent.parent / f"experiment_{args.experiment}.json"
    exp_data = Experiment.model_validate_json(path.read_text())
    run_experiment(exp_data)