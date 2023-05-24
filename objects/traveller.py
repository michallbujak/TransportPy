"""
Traveller class: agent in simulation
"""
# import os
# import sys
#
# sys.path.append(
#     os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from datetime import datetime
from dataclasses import dataclass

from objects.dispatcher import Dispatcher

import utils.common


@dataclass
class CharacteristicsBehaviour:
    """
    Store behavioural characteristics of the traveller
    """
    vot: float
    pfs: float
    pfs_const: dict
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
            pfs=behavioural_details['pfs'],
            pfs_const=behavioural_details['pfs_const'],
            pickup_delay_sensitivity=behavioural_details['delay_sensitivity']
        )
        self.utilities = {}

    def calculate_private_utility(self, dispatcher: Dispatcher, skim: dict):
        """
        Calculate utility of a private, non_shared ride.
        :param dispatcher: Dispatcher object
        :param skim: dict with distances
        :return: update self. utilities
        """
        distance = utils.common.compute_distance(
            list_of_points=[self.request_details.origin, self.request_details.destination],
            skim=skim
        )
        delay = dispatcher.private_pick_up_delay(self.request_details.origin, skim)[0]
        if delay is None:
            raise Exception("At the moment not implemented, not sufficient fleet")
        utility = -distance * dispatcher.pricing.private_ride - \
                  self.behavioural_details.vot * distance / dispatcher.city_properties.speed \
                  - delay * self.behavioural_details.pickup_delay_sensitivity
        self.utilities["private"] = utility

