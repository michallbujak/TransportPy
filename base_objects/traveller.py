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
    pfs_pool: dict
    pfs_pool_const: dict
    pickup_delay_sensitivity: float


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
        self.traveller_id = request[0]
        self.request_details = RequestDetails(
            request_time=request[3],
            origin=request[1],
            destination=request[2],
        )
        self.behavioural_details = CharacteristicsBehaviour(
            vot=behavioural_details['vot'],
            pfs_pool=behavioural_details['pfs_pool'],
            pfs_pool_const=behavioural_details['pfs_pool_const'],
            pickup_delay_sensitivity=behavioural_details['delay_sensitivity']
        )
        self.utilities = {}
