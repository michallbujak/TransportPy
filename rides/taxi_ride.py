"""
Class representing on demand travel, where traveller
requests a ride from a Dispatcher
"""
from typing import Any
import utils.common

from base_objects.traveller import Traveller
from base_objects.ride import Ride

dist = utils.common.compute_distance


class TaxiRide(Ride):
    """
    Private on-demand transport
    """

    def __init__(self, traveller, locations):
        super().__init__([traveller], locations)
        self.events = []

    def __repr__(self):
        return "taxi"

    def calculate_remaining_profitability(self,
                                          vehicle: Any,
                                          traveller: Traveller,
                                          fare: float,
                                          operating_cost: float,
                                          skim: dict,
                                          **kwargs
                                          ) -> float:
        """
        Calculate a profitability of a ride
        :param vehicle: Vehicle or child class object
        :param traveller: Traveller object
        :param fare: fare in monetary units/meter
        :param operating_cost: operating cost in units/meter
        :param skim: distances dictionary
        :param kwargs: consistence with the Ride class
        :return: profit
        """
        request = traveller.request_details
        if len(self.travellers) >= 1:
            trip_dist = dist([vehicle.path.current_position, request.destination], skim)
            pickup_dist = 0
        else:
            trip_dist = dist([request.origin, request.destination], skim)
            pickup_dist = dist([request.origin, vehicle.path.current_position], skim)
        return trip_dist * fare - (trip_dist + pickup_dist) * operating_cost

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
        return distance * fare * int(flag), distance * operating_cost

    def calculate_utility(self,
                          vehicle: Any,
                          traveller: Traveller,
                          fare: float,
                          skim: dict,
                          **kwargs
                          ) -> float:
        """
        Calculate utility for the traveller
        :param vehicle: Vehicle or child class object
        :param traveller: Traveller object
        :param fare: fare in monetary units/meter
        :param skim: distances dictionary
        :param kwargs: consistence with the Ride class
        :return: utility
        """
        request = traveller.request_details
        trip_length = dist([request.origin, request.destination], skim)
        pickup_delay = dist([request.origin, vehicle.path.current_position], skim) \
                       / vehicle.vehicle_speed
        pref = traveller.behavioural_details
        utility = -trip_length * fare
        utility -= trip_length / vehicle.vehicle_speed * pref['VoT']
        utility -= pickup_delay * pref['VoT'] * pref['pickup_delay_sensitivity']
        return utility
