"""
Basic object for managing a ride
"""
from abc import abstractmethod
from dataclasses import dataclass

from traveller import Traveller


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
            travellers: list[Traveller],
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
    def calculate_profitability(self,
                                fare: float,
                                trip_length: float,
                                operating_cost: float,
                                update_self: bool = False
                                ) -> None or tuple[float]:
        """
        :param fare: fare per meter
        :param trip_length: length of the trip (meters)
        :param operating_cost: cost of vehicle travelling per meter
        :param update_self: or return values
        :return: update self
        Calculate ride's profitability
        """
        paxes = self.travellers
        if update_self:
            self.profitability.profit = sum(pax.request_details.cost for pax in paxes)
            self.profitability.cost = trip_length*operating_cost
            self.profitability.profitability = self.profitability.profit - self.profitability.cost

            return None

        else:
            profit = sum(pax.request_details.cost for pax in paxes)
            cost = trip_length*operating_cost
            profitability = self.profitability.profit - self.profitability.cost

            return profit, cost, profitability

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
