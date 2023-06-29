"""
Class of a third party assigning vehicles to requests
"""
import datetime
import logging
from typing import Any
from datetime import datetime as dt

import utils.common as utc
from base_objects.vehicle import Vehicle
from base_objects.traveller import Traveller

from rides.taxi_ride import TaxiRide


class Dispatcher:
    """
    Dispatcher with the modular build
    """

    def __init__(self,
                 dispatcher_id: float,
                 fares: dict,
                 fleet: dict
                 ):
        self.dispatcher_id = dispatcher_id
        self.fares = fares
        self.fleet = fleet
        self.rides = {
            'taxi': [],
            'pool': []
        }

    def find_vehicle(self,
                     request: tuple,
                     veh_type: str,
                     skim: dict
                     ) -> Vehicle:
        """
        Find the most suitable vehicle
        """
        node = request[1]
        dist = (1e6, None)
        for veh in self.fleet[veh_type]:
            if veh.available:
                dist_new = utc.compute_distance([node, veh.path.current_position], skim)
                if dist[0] > dist_new:
                    dist = (dist_new, veh)
        return dist[1]

    def assign_taxi(self,
                    request: tuple,
                    traveller: Traveller,
                    skim: dict,
                    logger: logging.Logger,
                    current_time: dt
                    ) -> Any:
        vehicle = self.find_vehicle(request, "taxi", skim)
        locations = [(request[1], 'o', request[0]), (request[2], 'd', request[0])]
        new_ride = TaxiRide([traveller], locations)
        new_ride.serving_vehicle = vehicle
        new_ride.events.append((vehicle.path.current_time, None, 'a', traveller.traveller_id))

        vehicle.available = False
        vehicle.scheduled_travellers = [traveller]
        vehicle.path.current_path = utc.compute_path(
            [vehicle.path.current_position] + [t[0] for t in locations],
            skim
        )
        vehicle.path.nearest_crossroad = vehicle.path.current_path[1]
        vehicle.path.stationary_position = False

        if 'taxi' not in self.rides.keys():
            self.rides['taxi'] = [new_ride]
        else:
            self.rides['taxi'].append(new_ride)

        traveller.utilities['taxi'] = new_ride.calculate_utility(vehicle=new_ride.serving_vehicle, traveller=traveller,
                                                                 fare=self.fares['taxi'], skim=skim)

        logger.warning(f"{current_time}:"
                       f" Traveller {traveller} assigned to vehicle {vehicle}")


