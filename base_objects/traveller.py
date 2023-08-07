"""
Traveller class: agent in simulation
"""

from datetime import datetime
from dataclasses import dataclass

from utils.common import compute_distance


@dataclass
class RequestDetails:
    """
    Details of the request
    """
    request_time: datetime
    origin: int
    destination: int
    request_type: str
    trip_length: float or None


@dataclass
class ServiceDetails:
    """
    Store information regarding service, mainly whether the traveller drops
    """
    resigned: bool
    waiting_time: float or None


class Traveller:
    """
    Basic agent in the simulation
    """

    def __init__(self,
                 request: tuple,
                 behavioural_details: dict
                 ):
        """

        :param request: (id, origin, destination, time, type)
        :param behavioural_details: dictionary, may be nested
        """
        self.traveller_id = request[0]
        self.request_details = RequestDetails(
            request_time=request[3],
            origin=request[1],
            destination=request[2],
            request_type=request[4],
            trip_length=None
        )
        self.behavioural_details = behavioural_details
        self.utilities = {}
        self.distance_travelled = {}
        self.service_details = ServiceDetails(
            resigned=False,
            waiting_time=0
        )

    def __repr__(self):
        """ Way to represent travellers in the system """
        return f"Traveller {self.traveller_id}"

    def calculate_trip_length(self, skim: dict):
        """ Calculate distance from origin to destination """
        self.request_details.trip_length = compute_distance(
            [self.request_details.origin, self.request_details.destination],
            skim
        )

    def update_utility(self, key, val):
        """ Update utility value """
        self.utilities[key] = val
