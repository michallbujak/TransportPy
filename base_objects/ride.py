"""
Basic object for managing a ride
"""


class Ride:
    """
    Basic object to rides
    """
    def __init__(
            self,
            travellers: list,
            locations: list
    ):
        self.travellers = travellers
        self.locations = locations
        self.serving_vehicle = None
        self.profitability = None
        self.active = True

    def calculate_profitability(self):
        """
        Calculate ride's profitability
        Update self. profitability
        """
        raise NotImplementedError("method calculate_profitability must be implemented")

    def calculate_utility(self, traveller, vehicle, fare, skim, *args, **kwargs):
        """
        Calculate ride's profitability
        Update self. profitability
        """
        raise NotImplementedError("method calculate_utility must be implemented")
