"""
Traveller class: agent in simulation
"""

from datetime import datetime
from dataclasses import dataclass


@dataclass
class RequestDetails:
    """
    Details of the request
    """
    request_time: datetime
    origin: int
    destination: int
    request_type: str


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
            request_type=request[4]
        )
        self.behavioural_details = behavioural_details
        self.utilities = {}

    def __repr__(self):
        return f"Traveller {self.traveller_id}"

    def update_utility(self, key, val):
        self.utilities[key] = val
