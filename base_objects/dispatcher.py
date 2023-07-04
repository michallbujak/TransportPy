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
from rides.pool_ride import PoolRide


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
        self.rides = {
            'taxi': [],
            'pool': []
        }

    def find_closest_vehicle(self,
                             request: tuple,
                             veh_type: list,
                             skim: dict,
                             **kwargs
                             ) -> Vehicle or None or (dict, Vehicle):
        """
        Find the most suitable vehicle
        """
        node = request[1]
        dist = (1e6, None)
        pool_flag = kwargs.get('empty_pool', False)

        # Find fitting fleet
        return_type = kwargs.get('return_type', False)
        if return_type:
            by_type_closest = {}
        for key in veh_type:
            for veh in self.fleet[key]:
                if key == 'pool' and pool_flag:
                    if len(veh.scheduled_travellers) + len(veh.travellers) != 0:
                        continue
                if veh.available:
                    dist_new = utc.compute_distance([node, veh.path.current_position], skim)
                    if dist[0] > dist_new:
                        dist = (dist_new, veh)
            if return_type:
                by_type_closest[key] = tuple(list(dist))
                dist = None
        if return_type:
            return by_type_closest, dist[1]

        return dist[1]

    def assign_taxi(self,
                    request: tuple,
                    traveller: Traveller,
                    skim: dict,
                    logger: logging.Logger,
                    current_time: dt
                    ) -> None:
        """
        Assign a taxi ride to a traveller
        @param request: (traveller_id, origin, destination, request_time)
        @param traveller: Traveller object
        @param skim: skim dictionary
        @param logger: logging purposes
        @param current_time: for logging purposes
        @return: None
        """
        vehicle = self.find_closest_vehicle(request, ["taxi"], skim)
        locations = [(request[1], 'o', request[0]), (request[2], 'd', request[0])]
        new_ride = TaxiRide([traveller], locations)
        new_ride.serving_vehicle = vehicle
        new_ride.events.append((vehicle.path.current_time,
                                vehicle.path.nearest_crossroad if
                                vehicle.path.nearest_crossroad is not None
                                else vehicle.path.current_position,
                                'a',
                                traveller.traveller_id))

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

    def assign_pool(self,
                    request: tuple,
                    traveller: Traveller,
                    skim: dict,
                    logger: logging.Logger,
                    current_time: dt,
                    **kwargs
                    ) -> None:
        """
        Assigned pooled ride
        @param request: (traveller_id, origin, destination, request_time)
        @param traveller: Traveller object
        @param skim: skim dictionary
        @param logger: logging purposes
        @param current_time: for logging purposes
        @param kwargs: additional settings to choose pooling options
        @return:
        """
        locations = [(request[1], 'o', request[0]), (request[2], 'd', request[0])]

        # Baseline utility (taxi)
        baseline_taxi = TaxiRide(
            traveller=traveller,
            locations=locations
        )
        dict_closest, closest_vehicle = self.find_closest_vehicle(
            request=request,
            veh_type=['taxi', 'pool'],
            skim=skim,
            empty_pool=True,
            return_type=True
        )
        baseline_utility = baseline_taxi.calculate_utility(
            vehicle=closest_vehicle,
            traveller=traveller,
            fare=self.fares['pool'],
            skim=skim
        )
        baseline_profitability = baseline_taxi.calculate_remaining_profitability(
            vehicle=closest_vehicle,
            traveller=traveller,
            fare=self.fares['pool'],
            operating_cost=self.operating_costs['pool'],
            skim=skim
        )

        # Search through ongoing pool rides
        max_profit = baseline_profitability
        max_utility = baseline_utility
        best_pooled = None
        for ride in self.rides["pool"]:
            potential_profitability = ride.calculate_remaining_profitability(
                vehicle=ride.serving_vehicle,
                fare=self.fares['pool'],
                share_discount=self.fares['share_discount'],
                operating_cost=self.operating_costs['pool'],
                skim=skim,
            )
            if potential_profitability > max_profit:
                if not kwargs.get('attractive_only', False):
                    best_pooled = ride
                else:
                    raise NotImplementedError("Attractive only pooled ride based on utility")

        if best_pooled is not None:
            pass

