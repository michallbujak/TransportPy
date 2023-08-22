"""
Basic object for managing a ride
"""
from abc import abstractmethod
from dataclasses import dataclass


@dataclass
class Profitability:
    """
    Store information regarding ride's profitability
    """
    profit: float
    cost: float
    profitability: float or None


class Ride:
    """
    Basic object to rides
    """

    def __init__(
            self,
            travellers: list,
            destination_points: list,
            ride_type: str
    ):
        """
        @param travellers: list of travellers assigned to the ride
        @param destination_points: list of city nodes which will be visited along
        with what happens at those locations
        """
        self.travellers = travellers
        self.destination_points = destination_points
        self.serving_vehicle = None
        self.profitability = Profitability(
            profit=0,
            cost=0,
            profitability=None
        )
        self.ride_type = ride_type
        self.active = True

    @abstractmethod
    def calculate_profitability(self, **kwargs):
        """
        Calculate ride's profitability
        return profit, cost
        """
        raise NotImplementedError("method calculate_total_profitability must be implemented")

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
                'Subclasses of `Ride` must override the `calculate_remaining_profitability` method'
            )
        super().__init_subclass__(**kwargs)
