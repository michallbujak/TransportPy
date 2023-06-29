"""
Vehicle class
"""
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Positioning:
    """
    Store path details for the vehicle
    """
    current_position: int
    current_time: datetime
    end_time: datetime or None
    current_path: list or None
    nearest_crossroad: int or None
    time_between_crossroads: int
    stationary_position: bool


class Vehicle:
    """
    Class representing vehicles
    """

    def __init__(
            self,
            vehicle_id: int,
            start_node: int,
            start_time: datetime,
            end_time: datetime,
            capacity: int = 8,
            vehicle_speed: int = 6
    ):
        """
        :param vehicle_id: id of the vehicle
        :param start_node: node at which vehicle is positioned at a given time (osmnx node id)
        :param start_time: starting time: time at which vehicle appears in start_node
        :param end_time: time after which no new requests are accepted
        :param capacity: maximal occupancy of the vehicle (number of travellers)
        :param vehicle_speed: average speed of the vehicle
        """
        # Vehicle characteristics, constant
        self.vehicle_id = vehicle_id
        self.start_node = start_node
        self.maximal_occupancy = capacity
        self.vehicle_speed = vehicle_speed
        self.available = True

        # Occupancy details
        self.travellers = []
        self.scheduled_travellers = []

        # Path characteristics
        self.path = Positioning(
            current_position=start_node,
            current_time=start_time,
            end_time=end_time,
            current_path=None,
            nearest_crossroad=None,
            time_between_crossroads=0,
            stationary_position=True
        )

        # Possibly useful in future applications
        self.mileage = 0
        self.events = [(start_time, start_node, 's', self.vehicle_id)]

    def __repr__(self):
        return f"Vehicle {self.vehicle_id}"

