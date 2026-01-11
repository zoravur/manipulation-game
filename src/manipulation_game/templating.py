import random
from typing import Literal, Optional
from pydantic import BaseModel
from jinja2 import Environment, PackageLoader
import json
from pathlib import Path

from .game import Game
# import game

RestaurantJSONs = dict[str, dict]

class TemplateResult(BaseModel):
    sys: str
    user: str

# def random_facts(facts: RestaurantFacts, restaurant: str, num_facts: int) -> list[str]:
#     return random.sample(facts[restaurant], k=num_facts)

# def all_facts(facts: RestaurantFacts, restaurant: str) -> list[str]:
#     return facts[restaurant]

# def restaurant_facts_to_list(facts: RestaurantFacts, restaurants: list[str], commission_amount: int, commission_restaurant: str):
#     return [
#         {
#             "name": r,
#             "facts": facts[r],
#             "commission": (commission_amount if commission_restaurant == r else 0),
#         } for r in restaurants
#     ]

# def restaurant_json_to_list(jsons: RealisticRestaurantJSONs, restaurants: list[str], commission_amount: int, commission_restaurant: str):
#     return [
#         {
#             "name": r,
#             "facts": jsons[r],
#             "commission": (commission_amount if commission_restaurant == r else 0),
#         } for r in restaurants
#     ]

def restaurant_data_to_list(data: RestaurantJSONs, restaurants: list[str], commission_amount: int):
    return [
        {
            "name": r,
            "data": {k:v for k,v in data[r].items() if k != "experience"},
            "commission": commission_amount if data[r]["quality"] == "bad" else 0,
        } for r in restaurants
    ]

def a_vars(game: Game, 
           restaurant_json: RestaurantJSONs,
           iteration: int) -> dict:

    return {
        "city": game.current_city(iteration),
        "scheming": game.a_scheming,
        "restaurants": restaurant_data_to_list(
            data=restaurant_json,
            restaurants=[k for k in restaurant_json], 
            commission_amount=game.a_commission_percentage,
        )
    }

def b_vars(game: Game, 
           restaurant_json: RestaurantJSONs,
           iteration: int) -> dict:
    return {
        "city": game.current_city(iteration),
    }

def template(
    player: Literal["A", "B"],
    game: Game,
    restaurant_json: RestaurantJSONs = {},
    iteration: int = 0,
    override_path: Optional[str] = None
) -> TemplateResult:
    env = Environment(
        loader=PackageLoader("manipulation_game.templating"),
        autoescape=False,
    )
    match player:
        case "A":
            if override_path is not None:
                sys_template = env.get_template(override_path)
            else:
                sys_template = env.get_template(game.templateA_path or f"sys_templateA.jinja")
            vars = a_vars(game, restaurant_json, iteration)
        case "B":
            if override_path is not None:
                sys_template = env.get_template(override_path)
            else:
                sys_template = env.get_template(game.templateB_path or f"sys_templateB.jinja")
            vars = b_vars(game,  restaurant_json, iteration)
        case _:
            raise ValueError(f"Unknown player: {player}")
    sys_rendered = sys_template.render(**vars)
    return TemplateResult(
        sys=sys_rendered,
        user="",
    )

def load_all_restaurant_jsons(g: Game, iteration: int) -> RestaurantJSONs:
    d = {}
    if g.city_list is not None:
        city = g.city_list[iteration]
    else:
        city = g.realistic_city
    for p in Path(g.realistic_dir, city).glob("*"):
        with open(p) as f:
            restaurant_json = json.load(f)
        d[restaurant_json["name"]] = restaurant_json
    return d

if __name__ == "__main__":
    g = Game.model_validate(json.load(open("example_game.json")))
    facts=json.load(open("restaurant_facts.json"))

    d = load_all_restaurant_jsons(g, 0)
    print(f"{d=}")

    print(template("A", g, d, 0).sys)

    
