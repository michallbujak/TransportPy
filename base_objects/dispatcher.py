"""
Class of a third party assigning vehicles to requests
"""
from abc import abstractmethod

from base_objects.vehicle import Vehicle


class Dispatcher:
    """
    Dispatcher with the modular build
    """

    def __init__(self,
                 dispatcher_id: float,
                 fares: dict,
                 operating_costs: dict,
                 fleet: dict
                 ):
        self.dispatcher_id = dispatcher_id
        self.fares = fares
        self.operating_costs = operating_costs
        self.fleet = fleet
        self.rides = {}

    def find_closest_vehicle(self,
                             request: tuple,
                             veh_type: str,
                             skim: dict,
                             **kwargs
                             ) -> Vehicle or None:
        """
        Find the most suitable vehicle
        """
        raise NotImplementedError("method find_closest_vehicle must be implemented")
