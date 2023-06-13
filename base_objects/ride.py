"""
Basic object for managing a ride
"""


class Ride:
    """
    Basic object to rides
    """
    def __init__(
            self,
            travellers: list
    ):
        self.travellers = travellers
        self.profitability = None

    def calculate_profitability(self):
        """
        Calculate ride's profitability
        Update self. profitability
        """
        pass


