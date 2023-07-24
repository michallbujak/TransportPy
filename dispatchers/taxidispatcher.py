"""
Class of a third party assigning vehicles to requests
"""
import datetime
import logging
from typing import Any
from datetime import datetime as dt

import utils.common as utc
import utils.pool_tools

from base_objects.vehicle import Vehicle
from base_objects.traveller import Traveller
from base_objects.dispatcher import Dispatcher

from rides.taxi_ride import TaxiRide
from rides.pool_ride import PoolRide


class TaxiDispatcher(Dispatcher):
    """
    Dispatcher with the modular build
    """

    def __init__(self,
                 dispatcher_id: float,
                 fares: dict,
                 operating_costs: dict,
                 fleet: dict or None = None
                 ):
        super().__init__(dispatcher_id, fares, operating_costs, fleet)
        self.rides = {
            'taxi': [],
            'pool': []
        }

    def find_closest_vehicle(self,
                             request: tuple,
                             veh_type: str,
                             skim: dict,
                             **kwargs
                             ) -> Vehicle or None:
        """
        Find the most suitable vehicle
        """
        node = request[1]
        dist = (1e6, None)
        pool_flag = kwargs.get('empty_pool', False)

        # Find fitting fleet
        for veh in self.fleet[veh_type]:
            if veh_type == 'pool' and pool_flag:
                if len(veh.scheduled_travellers) + len(veh.travellers) != 0:
                    continue
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
        vehicle = self.find_closest_vehicle(request, "taxi", skim)
        locations = [(request[1], 'o', request[0]), (request[2], 'd', request[0])]
        new_ride = TaxiRide([traveller], locations, 'taxi')
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

        traveller.utilities['taxi'] = new_ride.calculate_utility(
            vehicle=new_ride.serving_vehicle,
            traveller=traveller,
            fare=self.fares['taxi'],
            skim=skim
        )

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

        # Baseline utility (solo ride)
        baseline_taxi = TaxiRide(
            traveller=traveller,
            destination_points=locations,
            ride_type='taxi'
        )
        closest_vehicle = self.find_closest_vehicle(
            request=request,
            veh_type='pool',
            skim=skim,
            empty_pool=True
        )
        baseline_utility = baseline_taxi.calculate_utility(
            vehicle=closest_vehicle,
            traveller=traveller,
            fare=self.fares['taxi'],
            skim=skim
        )
        baseline_profitability = baseline_taxi.calculate_remaining_profitability(
            vehicle=closest_vehicle,
            traveller=traveller,
            fare=self.fares['taxi'],
            operating_cost=self.operating_costs['pool'],
            skim=skim
        )

        # Search through ongoing pool rides
        profitability_relative_increase_max = 0
        max_utility = baseline_utility
        ods_seq = []
        best_pooled = None

        for ride in self.rides["pool"]:
            if len(ride.travellers) == 0:
                continue
            destination_points = list(ride.destination_points)
            destination_points += [(request[1], 'o', traveller.traveller_id)]
            destination_points += [(request[2], 'd', traveller.traveller_id)]

            combinations_ods = utils.pool_tools.admissible_future_combinations(destination_points)

            for combination in combinations_ods:
                potential_profitability = ride.calculate_remaining_profitability(
                    vehicle=ride.serving_vehicle,
                    fare=self.fares['taxi'],
                    pool_discount=self.fares['pool_discount'],
                    operating_cost=self.operating_costs['pool'],
                    skim=skim,
                    destination_points=combination,
                    additional_traveller=traveller
                )

                if potential_profitability - ride.profitability.profitability < baseline_profitability:
                    continue

                profitability_relative_increase_new = \
                    (potential_profitability - ride.profitability.profitability) \
                    / ride.profitability.profitability

                if profitability_relative_increase_new > profitability_relative_increase_max:
                    if not kwargs.get('attractive_only', False):
                        best_pooled = ride
                        ods_seq = combination
                        profitability_relative_increase_max = profitability_relative_increase_new
                    else:
                        raise NotImplementedError("Attractive only pooled ride based on utility")

        # if there is a fitting ride, add a traveller
        if best_pooled is not None:
            logger.warning(f"{current_time}: {best_pooled}"
                           f" found suitable for traveller {traveller}")
            best_pooled.add_traveller(
                traveller=traveller,
                new_profitability=profitability_relative_increase_max,
                ods_sequence=ods_seq,
                skim=skim
            )

        else:
            logger.info(f"{current_time}: No ongoing pool rides are attractive for {traveller}")
            logger.warning(f"{current_time}: Traveller {traveller} assigned to a new "
                           f"ride with the vehicle {closest_vehicle}")
            destination_points = [(traveller.request_details.origin, 'o', traveller.traveller_id),
                                  (traveller.request_details.destination, 'd', traveller.traveller_id)]
            new_ride = PoolRide(
                traveller=traveller,
                destination_points=destination_points,
                ride_type='pool'
            )
            new_ride.active = True
            new_ride.serving_vehicle = closest_vehicle
            new_ride.profitability.profitability = baseline_profitability
            self.rides['pool'].append(new_ride)

            veh = new_ride.serving_vehicle
            veh.path.current_path = utc.compute_path(
                list_of_points=[veh.path.current_position] +
                               [t[0] for t in destination_points],
                skim=skim
            )
            veh.path.nearest_crossroad = veh.path.current_path[1]
            veh.path.current_time = current_time
            veh.path.stationary_position = False
            veh.scheduled_travellers.append(traveller)
