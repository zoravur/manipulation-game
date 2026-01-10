import random
from typing import Literal
from pydantic import BaseModel
from jinja2 import Environment, PackageLoader, select_autoescape

from .game import Game
# import game

RestaurantFacts = dict[str, list[str]]

RestaurantJSONs = dict[str, dict]

class TemplateResult(BaseModel):
    sys: str
    user: str

def random_facts(facts: RestaurantFacts, restaurant: str, num_facts: int) -> list[str]:
    return random.sample(facts[restaurant], k=num_facts)

def all_facts(facts: RestaurantFacts, restaurant: str) -> list[str]:
    return facts[restaurant]

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

def restaurant_data_to_list(data: RestaurantFacts | RestaurantJSONs, restaurants: list[str], commission_amount: int, commission_restaurant: str):
    return [
        {
            "name": r,
            "data": data[r],
            "commission": commission_amount if data[r]["quality"] == "bad" else 0,
        } for r in restaurants
    ]

def a_vars(game: Game, 
           restauraunt_json: RestaurantJSONs) -> dict:

    return {
        "scheming": game.a_scheming,
        "restaurants": restaurant_data_to_list(
            data=restauraunt_json,
            restaurants=[k for k in restauraunt_json], 
            commission_amount=game.a_commission_percentage,
            commission_restaurant=game.a_commission_restaurant,
        )
    }

def b_vars(game: Game, 
           restauraunt_json: RestaurantJSONs) -> dict:
    return {
    }

def template(
    player: Literal["A", "B"],
    game: Game,
    restaurant_json: RestaurantJSONs = {}
) -> TemplateResult:
    env = Environment(
        loader=PackageLoader("manipulation_game.templating"),
        autoescape=False,
    )
    match player:
        case "A":
            sys_template = env.get_template(game.templateA_path or f"sys_templateA.jinja")
            vars = a_vars(game, restaurant_json)
        case "B":
            sys_template = env.get_template(game.templateB_path or f"sys_templateB.jinja")
            vars = b_vars(game,  restaurant_json)
        case _:
            raise ValueError(f"Unknown player: {player}")
    sys_rendered = sys_template.render(**vars)
    return TemplateResult(
        sys=sys_rendered,
        user="",
    )

if __name__ == "__main__":
    import json
    from pathlib import Path
    g = Game.model_validate(json.load(open("example_game.json")))
    facts=json.load(open("restaurant_facts.json"))

    d = {}
    for p in Path(g.realistic_dir, g.realistic_city).glob("*"):
        with open(p) as f:
            restaurant_json = json.load(f)
            d[restaurant_json["name"]] = restaurant_json

    print(f"{d=}")

    print(template("A", g, d).sys)

    
