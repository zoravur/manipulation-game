from typing import Optional
from pydantic import BaseModel

class Game(BaseModel):
    # Shared information
    num_iterations: int
    num_public_facts: int
    restaurants: list[str]

    # A information and behaviour
    # a_name: str
    a_scheming: bool
    a_commission_restaurant: Optional[str]
    a_commission_percentage: int

    # B information
    # b_name: str
    b_num_hunches: int
