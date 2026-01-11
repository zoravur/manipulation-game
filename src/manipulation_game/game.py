from typing import Optional
from pydantic import BaseModel
import hashlib
import json

class Game(BaseModel):
    # Experimental setup
    seed: Optional[int] = None
    experiment_name: Optional[str] = None
    sub_experiment_id: Optional[int] = None

    # Shared information
    num_iterations: int
    max_turns_per_conversation: int
    num_public_facts: int

    # A information and behaviour
    # a_name: str
    a_model: str
    a_scheming: bool
    a_commission_percentage: int

    # B information
    # b_name: str
    b_model: str
    b_num_hunches: int

    # Judge information
    judge_model: str

    realistic_city: str
    realistic_dir: str
    
    templateA_path: str
    templateB_path: str

def hash_game(game: Game) -> str:
    data = game.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
        exclude_unset=True,
    )
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]

