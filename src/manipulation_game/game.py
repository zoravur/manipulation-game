from typing import Optional
from pydantic import BaseModel

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


