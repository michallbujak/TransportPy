"""
Class representing on-demand shared travel, where traveller
requests a ride from a Dispatcher
"""
from typing import Any

from base_objects.traveller import Traveller
from base_objects.ride import Ride
from base_objects.vehicle import Vehicle

from utils.common import compute_distance as dist


class PoolRide(Ride):
    """
    Private on-demand transport
    """

    def __init__(self, traveller, locations):
        super().__init__([traveller], locations)
        self.events = []

    def __repr__(self):
        return "pool"

    def calculate_remaining_profitability(self,
                                          vehicle: Vehicle,
                                          fare: float,
                                          share_discount: float,
                                          operating_cost: float,
                                          skim: dict,
                                          **kwargs
                                          ) -> float:
        """
        Calculate a profitability of a ride
        :param vehicle: Vehicle or child class object
        :param fare: fare in monetary units/meter
        :param share_discount: discount for a shared ride
        :param operating_cost: operating cost in units/meter
        :param skim: distances dictionary
        :param kwargs: consistence with the Ride class
        :return: profit
        """
        no_paxes = len(vehicle.travellers)
        costs = dist([vehicle.path.current_position, self.locations[0]], skim) \
                * operating_cost
        locations = kwargs.get('locations', self.locations)

        # if not pooled
        if no_paxes == 1:
            profits = dist([vehicle.path.current_position, locations], skim) \
                      * fare
        # if pooled
        elif no_paxes > 1:
            profits = dist([vehicle.path.current_position, locations], skim) \
                      * fare * (1 - share_discount) * no_paxes

        # vehicle on the way to the first origin
        else:
            profits = 0

        # if only one destination left
        if len(locations) == 1:
            return profits - costs

        prev_node = locations[0]
        for node_counter in range(len(locations[1]) - 1):
            next_node = locations[node_counter + 1]

            if prev_node[1] == 'o':
                no_paxes += 1
            elif prev_node[1] == 'd':
                no_paxes -= 1
            else:
                pass

            if no_paxes == 1:
                profits += dist([prev_node[0], next_node[0]], skim) * fare
            elif no_paxes >= 1:
                profits += dist([prev_node[0], next_node[0]], skim) \
                           * fare * (1 - share_discount) * no_paxes
            else:
                pass

            costs += dist([prev_node[1], next_node[1]], skim) * operating_cost
            prev_node = next_node

        return profits - costs

    def calculate_unit_profitability(self,
                                     distance: float,
                                     fare: float,
                                     operating_cost: float,
                                     **kwargs):
        """
        Calculate profitability for a distance
        :param distance: travelled distance
        :param fare: fare in monetary units/meter
        :param operating_cost: operating cost in units/meter
        return (profits, costs)
        """
        flag = len(self.travellers) >= 1
        return distance * fare if flag else 0, distance * operating_cost

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
        trip_length = dist(nodes_seq, skim)
        pickup_delay = dist([nodes_seq[0], vehicle.path.current_position], skim) \
                       / vehicle.vehicle_speed
        pref = traveller.behavioural_details
        utility = -trip_length * fare
        utility -= trip_length / vehicle.vehicle_speed * pref['VoT'] * pref['pool_rides'][no_travellers]
        utility -= pickup_delay * pref['VoT'] * pref['pickup_delay_sensitivity']
        utility -= pref['pool_rides']['PfS_const']
        return utility
