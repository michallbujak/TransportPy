"""
Traveller class: agent in simulation
"""

from datetime import datetime
from dataclasses import dataclass


@dataclass
class CharacteristicsBehaviour:
    """
    Store behavioural characteristics of the traveller
    """
    vot: float
    pfs: float
    pfs_const: dict
    delay_sensitivity: float

@dataclass
class RequestDetails:
    """
    Details of the request
    """
    request_time: datetime
    origin: int
    destination: int


class Traveller:
    """
    Basic agent in the simulation
    """
    def __init__(self, request, behavioural_details):
        self.behavioural_details = CharacteristicsBehaviour(

        )
