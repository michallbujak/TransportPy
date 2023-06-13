"""
Class representing on demand travel, where traveller
requests a ride from a Dispatcher
"""
from base_objects.traveller import Traveller
from base_objects.ride import Ride


class TaxiRide:
    """
    Private on-demand transport
    """
    def __int__(self
                ):
        self.travellers = None

    def calculate_utility(self, request, vehicle):
        """
        Calculate utility for the traveller
        :param request: (traveller_id, starting_point, end_point, start_time)
        :param vehicle: Vehicle
        :return: utility, update Traveller
        """
        return 0


