"""
Basic object for managing a ride
"""
from abc import abstractmethod
from dataclasses import dataclass

from base_objects.traveller import Traveller


@dataclass
class Profitability:
    """
    Store information regarding ride's profitability
    """
    revenue: float
    cost: float
    profit: float or None


class Ride:
    """
    Basic object to rides
    """

    def __init__(
            self,
            travellers: list[Traveller],
            destination_points: list,
            ride_type: str
    ):
        """
        @param travellers: list of travellers assigned to the ride
        @param destination_points: list of city nodes associated
         with events which will be visited along (node, event, traveller)
        with what happens at those locations
        """
        self.travellers = travellers
        self.destination_points = destination_points
        self.past_destination_points = []
        self.serving_vehicle = None
        self.profitability = Profitability(
            revenue=0,
            cost=0,
            profit=None
        )
        self.ride_type = ride_type
        self.active = True

    # @abstractmethod
    # def calculate_profitability(self,
    #                             **kwargs
    #                             ) -> None or tuple[float]:
    #     """
    #     :return: update self
    #     Calculate ride's profitability
    #     """
    #     raise NotImplementedError("method calculate_profitability not implemented")

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
        # if cls.calculate_profitability == Ride.calculate_profitability:
        #     raise TypeError(
        #         'Subclasses of `Ride` must override the `calculate_profitability` method'
        #     )
        super().__init_subclass__(**kwargs)
