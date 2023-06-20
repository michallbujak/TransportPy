"""
Class representing on demand travel, where traveller
requests a ride from a Dispatcher
"""
from typing import Any

from base_objects.traveller import Traveller
from base_objects.ride import Ride

from utils.common import compute_distance as dist


class TaxiRide(Ride):
    """
    Private on-demand transport
    """
    def __init__(self, traveller, locations):
        super().__init__([traveller], locations)

    def __repr__(self):
        return "taxi"

    def calculate_profitability(self):
        """
        Calculate a profitability of a ride
        :return:
        """
        raise NotImplementedError('HH')

    def calculate_utility(self, traveller: Traveller, fare: float, skim: dict, *args, **kwargs):
        """
        Calculate utility for the traveller
        :param traveller: (traveller_id, starting_point, end_point, start_time)
        :param fare: fare in monetary units/meter
        :param skim: distances dictionary
        :return: utility
        """
        vehicle = self.serving_vehicle
        request = traveller.request_details
        trip_length = dist([request['origin'], request['destination']], skim)
        pickup_delay = dist([request['origin'], vehicle.Positioning.current_position], skim)\
                       /vehicle.vehicle_speed
        pref = traveller.behavioural_details
        utility = -trip_length * fare
        utility -= trip_length/vehicle.vehicle_speed * pref['VoT']
        utility -= pickup_delay * pref['VoT'] * pref['pickup_delay']
        return utility

