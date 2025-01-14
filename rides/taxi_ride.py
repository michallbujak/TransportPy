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

    def __init__(self, traveller, destination_points, ride_type):
        super().__init__([traveller], destination_points, ride_type)
        self.events = []

    def __repr__(self):
        return "taxi"

    @staticmethod
    def calculate_profitability(vehicle: Any,
                                traveller: Traveller,
                                fare: float,
                                operating_cost: float,
                                skim: dict,
                                **kwargs
                                ) -> tuple[float, float, float]:
        """
        Calculate a profitability of a ride
        :param vehicle: Vehicle or child class object
        :param traveller: Traveller object
        :param fare: fare in monetary units/meter
        :param operating_cost: operating cost in units/meter
        :param skim: distances dictionary
        :param kwargs: consistence with the Ride class
        :return: profitability
        """
        request = traveller.request_details
        revenue = request.trip_length * fare
        cost = dist([vehicle.current_position, request.origin], skim)
        cost += request.trip_length
        cost *= operating_cost
        return revenue, cost, revenue-cost

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

    @staticmethod
    def calculate_utility(vehicle: Any,
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
        trip_length = traveller.request_details.trip_length

        if kwargs.get('pickup_delay') is None:
            pickup_delay = dist([request.origin, vehicle.path.current_position], skim) \
                           / vehicle.vehicle_speed
        else:
            pickup_delay = kwargs['pickup_delay']

        pref = traveller.behavioural_details
        utility = -trip_length * fare
        utility -= trip_length / vehicle.vehicle_speed * pref['VoT']
        utility -= pickup_delay * pref['VoT'] * pref['pickup_delay_sensitivity']
        return utility
