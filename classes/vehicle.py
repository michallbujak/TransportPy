"""
Vehicle class
"""
from datetime import datetime, timedelta
from dataclasses import dataclass

from utils.common import compute_distance


@dataclass
class Path:
    """
    Store path details for the vehicle
    """
    current_position: int
    current_time: datetime
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
            maximal_occupancy: int = 8,
            vehicle_speed: int = 6,
    ):
        """
        :param vehicle_id: id of the vehicle
        :param start_node: node at which vehicle is positioned at a given time (osmnx node id)
        :param start_time: starting time: time at which vehicle appears in start_node
        :param maximal_occupancy: maximal occupancy of the vehicle (number of travellers)
        :param vehicle_speed: average speed of the vehicle
        """
        # Vehicle characteristics, constant
        self.ride_id = vehicle_id
        self.start_node = start_node
        self.maximal_occupancy = maximal_occupancy
        self.vehicle_speed = vehicle_speed

        # Occupancy details
        self.travellers = []
        self.scheduled_travellers = []

        # Path characteristics
        self.path = Path(current_position=start_node,
                         current_time=start_time,
                         current_path=None,
                         nearest_crossroad=None,
                         time_between_crossroads=0,
                         stationary_position=True
                         )

        # Data for post-run analysis
        self.mileage = 0

    def move(self, time: int, events: list, skim: dict):
        """
        Move vehicle along the previously determined route
        :param time: how long does it move along the route (seconds)
        :param events: list of tuples (node, event, traveller), where event is in ["a", "o", "d"]
        :param skim: data stating distance between points on the map
        :return:
        """
        time_left = time
        visited_nodes_times = []
        while self.path.current_path is not None:
            assert (
                    self.path.nearest_crossroad is not None
            ), "The path has not been updated, vehicle does not have a path to follow"

            self.path.stationary_position = False
            distance_to_crossroad = compute_distance(
                skim, self.path.current_position, self.path.current_path[1], "option1"
            )
            time_required_to_crossroad = (
                    distance_to_crossroad / self.vehicle_speed
                    - self.path.time_between_crossroads
            )

            if (
                    time_left < time_required_to_crossroad
            ):  # not sufficient time to reach the nearest crossroad
                self.path.time_between_crossroads = self.path.time_between_crossroads + time_left
                self.path.current_time = self.path.current_time + timedelta(seconds=time_left)
                break

            # sufficient time to reach the nearest crossroad
            time_left -= time_required_to_crossroad
            self.path.current_time = self.path.current_time + timedelta(
                seconds=time_required_to_crossroad
            )
            self.path.current_position = self.path.current_path[1]
            self.path.current_path = self.path.current_path[1:]
            self.path.time_between_crossroads = 0

            if len(self.path.current_path) == 1:
                self.path.current_path = None
                self.path.nearest_crossroad = None
                self.path.stationary_position = True

            else:
                self.path.nearest_crossroad = self.path.current_path[1]

            self.mileage += distance_to_crossroad
            visited_nodes_times.append((self.path.current_position, self.path.current_time))
            self.check_if_event(events)

        return visited_nodes_times, events

    def check_if_event(self, events: list):
        """
        Check if certain node is associated with any of the passed events (origins/destinations)
        :param events: list of tuples (node, event, traveller), where event is in ["a", "o", "d"]
        :return: updated event list and updated self. travellers and self. scheduled travellers
        """
        for event in events:
            if event[0] == self.path.current_position:
                if event[1] == "d":
                    self.travellers.remove(event[2])
                elif event[1] == "o":
                    self.travellers.append(event[2])

    def accept_request(self, new_path: list, scheduled_travellers: list):
        """
        Update information upon accepting a new request
        :param new_path: new path for the vehicle
        :param scheduled_travellers: a new set of travellers how are assigned to the vehicle
        :return:
        """
        self.path.current_path = new_path
        self.scheduled_travellers = scheduled_travellers
