"""
Create a ride class - object to store information regarding one separate ride
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Traveller:
    """
    Store information regarding traveller
    """
    trav_id: int
    private_utility: float or None
    utility: float or None
    request_time: datetime
    origin: int
    destination: int
    vot: float
    pfs: float
    pfs_const: dict
    delay_sensitivity: float


@dataclass
class Characteristics:
    start_time: datetime
    end_time: datetime
    profitability: int or None


class PoolRide:
    """
    Class representing realisation of a certain ride.
    It starts with some request and progresses over time.
    Possibly becomes a shared ride.
    """

    def __init__(self, request: tuple, traveller_characteristics: dict):
        """
        :param request: (traveller_id, starting_point, end_point, start_time)
        :param traveller_characteristics: object
        """
        self.vehicle = None
        self.od_path = [request[1], request[2]]
        self.travellers = Traveller(
            trav_id=request[0],
            private_utility=None,
            utility=None,
            request_time=request[3],
            origin=request[1],
            destination=request[2],
            vot=traveller_characteristics['vot'],
            pfs=traveller_characteristics['pfs'],
            pfs_const=traveller_characteristics['pfs_const'],
            delay_sensitivity=traveller_characteristics['delay_sensitivity']
        )
        self.profitability = None

    def calculate_private_utility(self, skim: dict):
        """
        Calculate utility of a private, non_shared ride
        :param skim: dict with distances
        :return: utility
        """

