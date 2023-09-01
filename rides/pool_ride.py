"""
Class representing on-demand shared travel, where traveller
requests a ride from a Dispatcher
"""
from typing import Any
import itertools

from base_objects.traveller import Traveller
from base_objects.ride import Ride
from base_objects.vehicle import Vehicle

from utils.common import compute_distance as dist
from utils.common import compute_path as find_path


class PoolRide(Ride):
    """
    Private on-demand transport
    """

    def __init__(self, traveller, destination_points, ride_type):
        super().__init__([traveller], destination_points, ride_type)
        self.events = []
        self.vehicle_start_position = None
        self.all_destination_points = destination_points

    def __repr__(self):
        return f"Pool: {self.travellers}"

    def calculate_utility(self,
                          vehicle: Any,
                          traveller: Traveller,
                          nodes_seq: list,
                          no_travellers: int,
                          fare: float,
                          skim: dict,
                          **kwargs
                          ) -> float:
        """
        Calculate utility for the traveller
        :param vehicle: Vehicle or child class object
        :param traveller: Traveller object
        :param nodes_seq: nodes to be visited along the route
        :param no_travellers: number of travellers
        :param fare: fare in monetary units/meter
        :param skim: distances dictionary
        :return: utility
        """
        # Check if already picked_up:
        if traveller.service_details.pick_up_delay is not None:
            pickup_delay = traveller.service_details.pick_up_delay
            start = [node for node in self.all_destination_points
                     if (node[1] == 'o' and node[2] == traveller)][0]
            finish = [node for node in nodes_seq if (node[1] == 'd' and node[2] == traveller)][0]
            trip = [self.all_destination_points[self.all_destination_points.index(start):]]
            trip += [vehicle.path.current_position]
            trip += [vehicle.path.closest_crossroad]
            trip += nodes_seq[:(nodes_seq.index(finish)+1)]
            trip_length = dist(trip, skim)

        else:
            start = [node for node in nodes_seq if (node[1] == 'o' and node[2] == traveller)][0]
            finish = [node for node in nodes_seq if (node[1] == 'd' and node[2] == traveller)][0]
            pickup_delay = dist([vehicle.path.closest_crossroad] + nodes_seq[:(nodes_seq.index(start) + 1)], skim)
            pickup_delay *= vehicle.vehicle_speed
            pickup_delay += vehicle.path.to_closest_crossroads
            trip = [nodes_seq[nodes_seq.index(start):(nodes_seq.index(finish)+1)]]
            trip_length = dist(trip, skim)

        # Utility calculation
        pref = traveller.behavioural_details
        utility = -trip_length * fare
        utility -= trip_length / vehicle.vehicle_speed * pref['VoT'] * pref['pool_rides'][no_travellers]
        utility -= pickup_delay * pref['VoT'] * pref['pickup_delay_sensitivity']
        utility -= pref['pool_rides']['PfS_const']
        return utility

    def add_traveller(self,
                      traveller: Traveller,
                      new_profitability: tuple or list,
                      ods_sequence: list,
                      skim: dict
                      ) -> None:
        """
        If a ride is considered attractive for the new traveller
        assign him/her to the ride
        @param traveller: Traveller who is to be assigned
        @param new_profitability: values calculated prior to assignment (profit, cost, profitability)
        @param ods_sequence: sequence of origins and destinations along the route
        @param skim: skim dictionary
        """
        # Update vehicle
        vehicle = self.serving_vehicle
        vehicle.scheduled_travellers.append(traveller)

        if len(vehicle.scheduled_travellers) + len(vehicle.travellers) >= vehicle.maximal_occupancy:
            vehicle.available = False

        vehicle.path.current_path = find_path(
            list_of_points=[vehicle.path.current_position] +
                           [vehicle.path.closest_crossroad] +
                           [t[0] for t in ods_sequence],
            skim=skim
        )

        # Update self
        self.profitability.profit = new_profitability[0]
        self.profitability.cost = new_profitability[1]
        self.profitability.profitability = new_profitability[2]
        self.travellers.append(traveller)
        self.destination_points = ods_sequence



    # def calculate_profitability(self,
    #                             vehicle: Vehicle,
    #                             fare: float,
    #                             pool_discount: float,
    #                             operating_cost: float,
    #                             skim: dict,
    #                             **kwargs
    #                             ) -> float:
    #     """
    #     Calculate a profitability of a ride
    #     :param vehicle: Vehicle or child class object
    #     :param fare: fare in monetary units/meter
    #     :param pool_discount: discount for a shared ride
    #     :param operating_cost: operating cost in units/meter
    #     :param skim: distances dictionary
    #     :param kwargs: consistence with the Ride class
    #     :return: profit
    #     """
    #     destination_points = kwargs.get('destination_points', self.destination_points)
    #     additional_traveller = kwargs.get('additional_traveller', None)
    #     if additional_traveller is not None:
    #         paxes = vehicle.travellers + vehicle.scheduled_travellers + [additional_traveller]
    #     else:
    #         paxes = vehicle.travellers + vehicle.scheduled_travellers
    #
    #     curr_dest_pt = destination_points[0]
    #     curr_dest_pt_idx = destination_points.index(curr_dest_pt)
    #
    #     costs = dist([self.vehicle_start_position] +
    #                  self.all_destination_points[:curr_dest_pt_idx] +
    #                  self.destination_points,
    #                  skim)
    #
    #     profits = 0
    #     if len(paxes) == 1:
    #         profits = paxes[0].request_details.trip_length * fare
    #     else:
    #         for pax in paxes:
    #             profits += pax.request_details.trip_length * fare * (1 - pool_discount)
    #
    #     return profits - costs*operating_cost
