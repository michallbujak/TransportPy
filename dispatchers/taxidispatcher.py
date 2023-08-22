"""
Class of a third party assigning vehicles to requests
"""
import datetime
import logging
from typing import Any
from datetime import datetime as dt

import numpy as np

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
                 dispatcher_id: float or str,
                 fares: dict,
                 operating_costs: dict,
                 fleet: dict or None = None
                 ):
        super().__init__(dispatcher_id, fares, operating_costs, fleet)
        self.fleet = {k: [] for k in np.unique(fleet['type'])} if fleet is not None else None
        self.rides = {k: [] for k in np.unique(fleet['type'])} if fleet is not None else None

    def find_closest_vehicle(self,
                             request: tuple,
                             veh_types: list,
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
        for veh_type in veh_types:
            for veh in self.fleet[veh_type]:
                if veh_type == 'pool' and pool_flag:
                    if len(veh.scheduled_travellers) + len(veh.travellers) != 0:
                        continue
                if veh.available:
                    dist_new = utc.compute_distance([node, veh.path.current_position], skim)
                    if dist[0] > dist_new:
                        dist = (dist_new, veh)
        return dist[1]

    def taxi_utility(self,
                     request: tuple,
                     traveller: Traveller,
                     skim: dict,
                     logger: logging.Logger,
                     **kwargs
                     ) -> (TaxiRide, Vehicle, float):
        """
        Calculate utility of the taxi ride
        @param request: (traveller_id, origin, destination, request_time)
        @param traveller: Traveller object
        @param skim: skim dictionary
        @param logger: logging purposes
        @return: Ride, vehicle, utility, profitability
        """
        only_taxi = kwargs.get("only_taxi", False)
        if only_taxi:
            vehicle = self.find_closest_vehicle(request, ["taxi"], skim)
        else:
            vehicle = self.find_closest_vehicle(request, ["taxi", "pool"], skim, empty_pool=True)

        locations = [(request[1], 'o', request[0]), (request[2], 'd', request[0])]
        new_ride = TaxiRide([traveller], locations, 'taxi')
        utility = new_ride.calculate_utility(
            vehicle=vehicle,
            traveller=traveller,
            fare=self.fares['taxi'],
            skim=skim
        )
        profitability = new_ride.calculate_profitability(
            vehicle=vehicle,
            traveller=traveller,
            fare=self.fares['taxi'],
            operating_cost=self.fares['operating_costs'],
            skim=skim
        )
        logger.info(f"For traveller {traveller} calculated utility"
                    f"of the taxi ride for {utility}")
        return TaxiRide, vehicle, utility, profitability

    def assign_taxi(self,
                    taxi_ride: TaxiRide,
                    vehicle: Vehicle,
                    utility: float,
                    traveller: Traveller,
                    skim: dict,
                    logger: logging.Logger,
                    current_time: dt,
                    taxi_or_pool: str = "pool"
                    ) -> None:
        """
        Assign a taxi ride to a traveller
        @param taxi_ride: TaxiRide object for which the traveller should be assigned
        @param vehicle: Vehicle to which the traveller should be assigned
        @param utility: calculated utility of the taxi ride
        @param traveller: Traveller object
        @param skim: skim dictionary
        @param logger: logging purposes
        @param current_time: for logging purposes
        @param taxi_or_pool: choose whether a ride can be further pooled or not
        @return: None
        """
        taxi_ride.serving_vehicle = vehicle
        taxi_ride.events.append((vehicle.path.current_time,
                                 vehicle.path.nearest_crossroad if
                                 vehicle.path.nearest_crossroad is not None
                                 else vehicle.path.current_position,
                                 'a',
                                 traveller.traveller_id))
        vehicle.available = False
        vehicle.scheduled_travellers = [traveller]
        vehicle.path.current_path = utc.compute_path(
            [vehicle.path.current_position] + [t[0] for t in taxi_ride.destination_points],
            skim
        )
        vehicle.path.nearest_crossroad = vehicle.path.current_path[1]
        vehicle.path.stationary_position = False

        if taxi_or_pool not in self.rides.keys():
            self.rides[taxi_or_pool] = [taxi_ride]
        else:
            self.rides[taxi_or_pool].append(taxi_ride)

        traveller.utilities['taxi'] = utility

        logger.warning(f"{current_time}:"
                       f" Traveller {traveller} assigned to vehicle {vehicle}")

    def pool_utility(self,
                     request: tuple,
                     traveller: Traveller,
                     fares: dict,
                     skim: dict,
                     logger: logging.Logger,
                     current_time: dt,
                     **kwargs
                     ) -> tuple or None:
        """
        Calculate utility of a pool ride
        @param request: (traveller_id, origin, destination, request_time)
        @param traveller: Traveller object
        @param fares: fares and costs
        @param skim: skim dictionary
        @param logger: logging purposes
        @param current_time: for logging purposes
        @param kwargs: additional settings to choose pooling options
        @return:
        """
        new_locations = [(request[1], 'o', request[0]), (request[2], 'd', request[0])]

        maximal_pick_up = kwargs.get("maximal_pickup", 1e6)

        # Consider baseline taxi
        if kwargs.get("attractive_only", True):
            baseline_taxi = TaxiRide(
                traveller=traveller,
                destination_points=new_locations,
                ride_type='taxi'
            )
            closest_vehicle = self.find_closest_vehicle(
                request=request,
                veh_types=['pool', 'taxi'],
                skim=skim,
                empty_pool=True
            )

            taxi_feasible = True

            if closest_vehicle is None:
                taxi_feasible = False

            if utils.common.compute_distance(
                    [closest_vehicle.path.current_position, request[1]],
                    skim
            ) / closest_vehicle.vehicle_speed > maximal_pick_up:
                taxi_feasible = False

            if taxi_feasible:
                baseline_utility = baseline_taxi.calculate_utility(
                    vehicle=closest_vehicle,
                    traveller=traveller,
                    fare=self.fares["taxi"],
                    skim=skim
                )
            else:
                baseline_utility=False


        # Search through ongoing pool rides
        possible_assignments = []


        for ride in self.rides["pool"]:
            # look only for actual pool rides
            if len(ride.travellers) == 0:
                continue

            max_distance_pickup = maximal_pick_up/ride.serving_vehicle.vehicle_speed

            # Filter 1: combinations must save kilometres
            destination_points = list(ride.destination_points)
            max_trip_length = utc.compute_distance(destination_points)
            max_trip_length += utc.compute_distance(new_locations)
            destination_points += new_locations

            od_combinations = utils.pool_tools.admissible_future_combinations(
                new_locations=new_locations,
                ride=ride,
                max_trip_length=max_trip_length,
                max_distance_pickup=max_distance_pickup,
                skim=skim,
                execution_time=True
            )

            # If it's not feasible to associate the new requests
            if not od_combinations:
                continue

            # Filter 2: calculate whether it's profitable for operator
            base_profitability = ride.profitability.profitability

            output_pool = {}

            for comb in od_combinations.copy():
                profitability_comb = ride.calculate_profitability(
                    vehicle=ride.serving_vehicle,
                    fare=self.fares["pool"],
                    pool_discount=self.fares["fake_uber"],
                    operating_cost=self.operating_costs["pool"],
                    skim=skim,
                    destination_points=comb,
                    additional_traveller=traveller
                )
                if profitability_comb < base_profitability:
                    od_combinations.remove(comb)
                else:
                    output_pool[comb] = {'profitability': profitability_comb}

            # Filter 3: utility for travellers
            if baseline_utility:
                ride.calculate_utility(

                )




    def assign_pool(self,
                    request: tuple,
                    traveller: Traveller,
                    skim: dict,
                    logger: logging.Logger,
                    current_time: dt,
                    **kwargs
                    ) -> bool:
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

        return True
