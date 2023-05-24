"""
Create a ride class - object to store information regarding one separate ride
"""
import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from objects.traveller import Traveller
from basicride import Ride

from dataclasses import dataclass
from datetime import datetime


# @dataclass
# class Traveller:
#     """
#     Store information regarding traveller
#     """
#     trav_id: int
#     private_utility: float or None
#     utility: float or None
#     request_time: datetime
#     origin: int
#     destination: int
#     vot: float
#     pfs: float
#     pfs_const: dict
#     delay_sensitivity: float


# @dataclass
# class Characteristics:
#     start_time: datetime
#     end_time: datetime
#     profitability: int or None


class PoolRide:
    """
    Class representing realisation of a certain ride.
    It starts with some request and progresses over time.
    Possibly becomes a shared ride.
    """

    def __init__(self, travellers: list,
                 start_time: datetime,
                 request: tuple):
        """
        :param travellers: list of Travellers objects
        :param start_time: starting time, datetime object
        :param request: (traveller_id, starting_point, end_point, start_time)
        """
        super().__init__(self, travellers, start_time)
        self.start_time = start_time
        self.od_path = [request[1], request[2]]
        self.travellers = travellers

    def calculate_private_utility(self, skim: dict):
        """
        Calculate utility of a private, non_shared ride
        :param skim: dict with distances
        :return: utility
        """
