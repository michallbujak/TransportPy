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
        @param request: (node, event, traveller)
        @param veh_types: pool, taxi etc.
        @param skim: skim matrix
        @return (time to arrival, Vehicle) or None (not found)
        """
        node = request[1]
        time_base = (1e6, None)
        pool_flag = kwargs.get('empty_pool', False)

        # Find fitting fleet
        for veh_type in veh_types:
            for veh in self.fleet[veh_type]:
                if veh_type == 'pool' and pool_flag:
                    if len(veh.scheduled_travellers) + len(veh.travellers) != 0:
                        continue
                if veh.available:
                    time_new = utc.compute_distance([node, veh.path.current_position], skim)
                    time_new /= veh.vehicle_speed
                    if time_base[0] > time_new:
                        time_base = (time_new, veh)

        if time_base[1] is None:
            return None

        else:
            return time_base

    def taxi_utility(self,
                     request: tuple,
                     traveller: Traveller,
                     skim: dict,
                     **kwargs
                     ) -> (TaxiRide, Vehicle, float):
        """
        Calculate utility of the taxi ride
        @param request: (traveller_id, origin, destination, request_time)
        @param traveller: Traveller object
        @param skim: skim dictionary
        @return: Ride, vehicle, utility, profitability
        """
        only_taxi = kwargs.get("only_taxi", False)
        if only_taxi:
            closest_vehicle = self.find_closest_vehicle(request, ["taxi"], skim)
        else:
            closest_vehicle = self.find_closest_vehicle(request, ["taxi", "pool"],
                                                        skim, empty_pool=True)

        if closest_vehicle is None:
            return None

        vehicle, pickup_delay = closest_vehicle

        locations = [(request[1], 'o', request[0]), (request[2], 'd', request[0])]
        new_ride = TaxiRide([traveller], locations, 'taxi')
        utility = new_ride.calculate_utility(
            vehicle=vehicle,
            pickup_delay=pickup_delay,
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
        utc.log_if_logger(kwargs.get('logger'), 20,
                          f"For traveller {traveller} calculated "
                          f"utility of the taxi ride for {utility}")

        return TaxiRide, vehicle, profitability, utility

    def assign_taxi(self,
                    taxi_ride: TaxiRide or PoolRide,
                    vehicle: Vehicle,
                    utility: float,
                    traveller: Traveller,
                    profitability: tuple[float],
                    skim: dict,
                    **kwargs
                    ) -> None:
        """
        Assign a taxi ride to a traveller
        @param taxi_ride: TaxiRide or PoolRide object for which the traveller should be assigned
        @param vehicle: Vehicle to which the traveller should be assigned
        @param utility: calculated utility of the taxi ride
        @param traveller: Traveller object
        @param profitability: a tuple (profit, cost, proftability)
        @param skim: skim dictionary
        @return: None
        """
        taxi_or_pool = "taxi" if type(taxi_ride) == TaxiRide else "pool"

        taxi_ride.serving_vehicle = vehicle
        taxi_ride.events.append((vehicle.path.current_time,
                                 vehicle.path.closest_crossroad if
                                 vehicle.path.closest_crossroad is not None
                                 else vehicle.path.current_position,
                                 'a',
                                 traveller.traveller_id))
        taxi_ride.profitability.revenue = profitability[0]
        taxi_ride.profitability.cost = profitability[1]
        taxi_ride.profitability.profit = profitability[2]
        vehicle.available = False
        vehicle.scheduled_travellers = [traveller]
        vehicle.path.current_path = utc.compute_path(
            [vehicle.path.current_position] + [t[0] for t in taxi_ride.destination_points],
            skim
        )
        vehicle.path.closest_crossroad = vehicle.path.current_path[1]
        vehicle.path.stationary_position = False

        if taxi_or_pool not in self.rides.keys():
            self.rides[taxi_or_pool] = [taxi_ride]
        else:
            self.rides[taxi_or_pool].append(taxi_ride)

        traveller.utilities['taxi'] = utility

        if taxi_or_pool == "pool":
            taxi_ride.vehicle_start_position = vehicle.path.closest_crossroad
            taxi_ride.adm_combinations = [taxi_ride.destination_points.copy()]

        if kwargs.get('pickup_delay') is not None:
            traveller.service_details.pickup_delay = kwargs['pickup_delay']

        utc.log_if_logger(kwargs.get('logger'), 30,
                          f"{vehicle.path.current_time}: Traveller"
                          f" {traveller} assigned to vehicle {vehicle}")

    def pool_utility(self,
                     request: tuple,
                     traveller: Traveller,
                     skim: dict,
                     **kwargs
                     ) -> (list, dict or None):
        """
        Calculate utility of a pool ride
        @param request: (traveller_id, origin, destination, request_time)
        @param traveller: Traveller object
        @param skim: skim dictionary
        @param kwargs: additional settings to choose pooling options
        @return:
        """
        new_locations = [(request[1], 'o', request[0]), (request[2], 'd', request[0])]

        maximal_pick_up = traveller.behavioural_details["maximal_pickup"]

        # Consider baseline taxi
        pax_cond = traveller.utilities.get('taxi') is None or False
        baseline_taxi = PoolRide(
            traveller=traveller,
            destination_points=new_locations,
            ride_type='pool'
        )
        closest_vehicle = self.find_closest_vehicle(
            request=request,
            veh_types=['pool'],
            skim=skim,
            empty_pool=True
        )

        if closest_vehicle is None:
            taxi_feasible = False
        else:
            taxi_feasible = True

        if utils.common.compute_distance(
                [closest_vehicle[1].path.current_position, request[1]],
                skim
        ) / closest_vehicle[1].vehicle_speed > maximal_pick_up:
            taxi_feasible = False

        if taxi_feasible and pax_cond:
            traveller.utilities['taxi'] = TaxiRide.calculate_utility(
                vehicle=closest_vehicle[1],
                pickup_delay=closest_vehicle[0],
                traveller=traveller,
                fare=self.fares["taxi"],
                skim=skim
            )

        else:
            traveller.utilities['taxi'] = False

        if taxi_feasible:
            taxi_out = {'taxi_ride': baseline_taxi,
                        'vehicle': closest_vehicle[1],
                        'pickup_delay': closest_vehicle[0],
                        'utility': traveller.utilities['taxi'],
                        'traveller': traveller,
                        'profitability': baseline_taxi.calculate_profitability(
                            fare=self.fares["pool"],
                            operating_cost=self.operating_costs["pool"],
                            skim=skim
                        )}
        else:
            taxi_out = None

        # Search through ongoing pool rides
        possible_assignments = []

        for ride in self.rides["pool"]:
            # look only for actual pool rides
            if len(ride.travellers) == 0:
                continue

            max_distance_pickup = maximal_pick_up / ride.serving_vehicle.vehicle_speed

            # Filter 1: combinations must save kilometres
            destination_points = [ride.serving_vehicle.path.closest_crossroad]\
                                 + [t[0] for t in ride.destination_points]
            max_trip_length = utc.compute_distance(destination_points, skim)
            max_trip_length += utc.compute_distance(
                [t[0] for t in new_locations],
                skim)
            # destination_points += new_locations

            od_combinations = utils.pool_tools.admissible_future_combinations(
                new_locations=new_locations,
                ride=ride,
                max_trip_length=max_trip_length,
                max_distance_pickup=max_distance_pickup,
                skim=skim,
                execution_time=True
            )

            # If it's not feasible to associate the new request
            if not od_combinations:
                continue

            output_pool = {tuple(comb): {} for comb in od_combinations}
            adm_combs = od_combinations.copy()

            # Filter 2: utility for travellers
            if kwargs.get("attractive_only", True):
                for comb in od_combinations.copy():
                    paxes = ride.travellers + [traveller]
                    shared_utility = {pax: ride.calculate_utility(
                        vehicle=ride.serving_vehicle,
                        traveller=pax,
                        nodes_seq=comb,
                        no_travellers=len(paxes),
                        fare=self.fares['pool'],
                        pool_discount=self.fares['pool_discount'],
                        skim=skim
                    ) for pax in paxes}
                    if not all([shared_utility[key] > key.utilities['taxi'] for key in shared_utility.keys()]):
                        od_combinations.remove(comb)
                        del output_pool[tuple(comb)]
                    else:
                        output_pool[tuple(comb)]['shared_utility'] = shared_utility

            # If it's not feasible to assign the new request
            if not od_combinations:
                continue

            # Filter 3: calculate whether it's profitable for operator
            base_profitability = ride.profitability.profit

            if kwargs.get("profitable_only", True):
                for comb in od_combinations.copy():
                    profitability_comb = ride.calculate_profitability(
                        fare=self.fares["pool"],
                        operating_cost=self.operating_costs["pool"],
                        skim=skim,
                        new_ods=comb,
                        additional_traveller=traveller,
                        sharing_discount=self.fares["pool_discount"],
                        update_self=False
                    )
                    if profitability_comb[2] < base_profitability:
                        od_combinations.remove(comb)
                        del output_pool[tuple(comb)]
                    else:
                        output_pool[tuple(comb)]['profitability'] = profitability_comb

            if not od_combinations:
                continue

            for comb in od_combinations:
                possible_assignments.append((ride,
                                             comb,
                                             output_pool[tuple(comb)]['profitability'],
                                             output_pool[tuple(comb)]['shared_utility'],
                                             adm_combs))

        if possible_assignments:
            utc.log_if_logger(kwargs.get("logger"), 20,
                              f"Traveller {traveller}"
                              f" found {len(possible_assignments)}"
                              f" admissible assignments")
        else:
            utc.log_if_logger(kwargs.get("logger"), 20,
                              f"Traveller {traveller}"
                              f" found NO admissible assignments. "
                              f"Feasible private ride: {taxi_out is not None}")

        return sorted(possible_assignments, key=lambda x: x[2][2]), taxi_out

    @staticmethod
    def assign_pool(possible_assignments: list[
        PoolRide,
        tuple or list,
        tuple or list,
        list
    ],
                    traveller: Traveller,
                    skim: dict,
                    **kwargs
                    ) -> None:

        best_ride, comb, profitability, utility, adm_combs = possible_assignments[0]

        traveller.utilities["pool"] = utility[traveller]
        for _traveller in best_ride.travellers:
            _traveller.utilities["pool"] = utility[_traveller]

        best_ride.add_traveller(
            traveller=traveller,
            new_profitability=profitability,
            ods_sequence=comb,
            adm_combinations=adm_combs,
            skim=skim
        )

        utc.log_if_logger(kwargs.get("logger"), 20,
                          f"{best_ride.serving_vehicle.path.current_time} No ongoing pool rides"
                          f" are attractive for {traveller}")

        return None
