"""
Class representing on-demand shared travel, where traveller
requests a ride from a Dispatcher
"""
from typing import Any

from base_objects.traveller import Traveller
from base_objects.ride import Ride

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

    def calculate_profitability(self):
        """
        Calculate a profitability of a ride
        :return:
        """
        raise NotImplementedError('HH')

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
        :param traveller: (traveller_id, starting_point, end_point, start_time)
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
