"""
Basic object for managing a ride
"""
from abc import abstractmethod


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

    @abstractmethod
    def calculate_profitability(self, **kwargs):
        """
        Calculate ride's profitability
        Update self. profitability
        """
        raise NotImplementedError("method calculate_profitability must be implemented")

    @abstractmethod
    def calculate_utility(self, **kwargs):
        """
        Calculate ride's profitability
        Update self. profitability
        """
        raise NotImplementedError("method calculate_utility must be implemented")

    def __init_subclass__(cls, **kwargs):
        if cls.calculate_utility == Ride.calculate_utility:
            raise TypeError(
               'Subclasses of `Ride` must override the `calculate_utility` method'
            )
        if cls.calculate_profitability == Ride.calculate_profitability:
            raise TypeError(
               'Subclasses of `Ride` must override the `calculate_profitability` method'
            )
        super().__init_subclass__(**kwargs)
