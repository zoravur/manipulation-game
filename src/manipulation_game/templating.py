import random
from typing import Literal
from pydantic import BaseModel
from jinja2 import Environment, PackageLoader

from .game import Game
# import game

RestaurantFacts = dict[str, list[str]]

class TemplateResult(BaseModel):
    sys: str
    user: str

def random_facts(facts: RestaurantFacts, restaurant: str, num_facts: int) -> list[str]:
    return random.sample(facts[restaurant], k=num_facts)

def all_facts(facts: RestaurantFacts, restaurant: str) -> list[str]:
    return facts[restaurant]

def a_vars(game: Game, restaurant_facts: RestaurantFacts) -> dict:
    return {
        "scheming": game.a_scheming,
        "restaurants": [
            {
                "name": r,
                "facts": restaurant_facts[r],
                "commission": (game.a_commission_percentage if game.a_commission_restaurant == r else 0),
            } for r in game.restaurants
        ]
    }

def b_vars(game: Game, restaurant_facts: RestaurantFacts) -> dict:
    return {
    }

def template(
    player: Literal["A", "B"],
    game: Game,
    restaurant_facts: RestaurantFacts,
) -> TemplateResult:
    env = Environment(
        loader=PackageLoader("manipulation_game.templating"),
        autoescape=False,
    )
    match player:
        case "A":
            sys_template = env.get_template(f"sys_templateA.jinja")
            vars = a_vars(game, restaurant_facts)
        case "B":
            sys_template = env.get_template(f"sys_templateB.jinja")
            vars = b_vars(game, restaurant_facts)
        case _:
            raise ValueError(f"Unknown player: {player}")
    sys_rendered = sys_template.render(**vars)
    return TemplateResult(
        sys=sys_rendered,
        user="",
    )

if __name__ == "__main__":
    import json
    g = Game.model_validate(json.load(open("example_game.json")))
    facts=json.load(open("restaurant_facts.json"))
    print(template("A", g, facts).sys)

    
