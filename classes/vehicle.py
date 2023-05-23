from datetime import datetime, timedelta
from utils.common import compute_distance


class Vehicle:
    def __init__(self,
                 vehicle_id: int,
                 start_node: int,
                 start_time: datetime,
                 maximal_occupancy: int = 8,
                 vehicle_speed: int = 6
                 ):
        """
        Class representing vehicles
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
        self.current_position = start_node
        self.current_time = start_time
        self.current_path = None
        self.nearest_crossroad = None
        self.time_between_crossroads = 0
        self.stationary_position = True

        # Data for post-run analysis
        self.mileage = 0

    def move(self,
             time,
             events,
             skim
             ):
        """
        Move vehicle along the previously determined route
        :param time: how long does it move along the route
        :param events: origin or destination points for travellers
        :param skim: data stating distance between points on the map
        :return:
        """
        time_left = time
        visited_nodes_times = []
        while self.current_path is not None:

            assert self.nearest_crossroad is not None, "The path has not been updated, vehicle does not have a path to follow"

            self.stationary_position = False
            distance_to_crossroad = compute_distance(skim, self.current_position, self.current_path[1], "big_dataset")
            time_required_to_crossroad = distance_to_crossroad / self.vehicle_speed - self.time_between_crossroads

            if time_left < time_required_to_crossroad:  # not sufficient time to reach the nearest crossroad
                self.time_between_crossroads = self.time_between_crossroads + time_left
                self.current_time = self.current_time + timedelta(seconds=time_left)
                break

            else:  # sufficient time to reach the nearest crossroad
                time_left -= time_required_to_crossroad
                self.current_time = self.current_time + timedelta(seconds=time_required_to_crossroad)
                self.current_position = self.current_path[1]
                self.current_path = self.current_path[1:]
                self.time_between_crossroads = 0

                if len(self.current_path) == 1:
                    self.current_path = None
                    self.nearest_crossroad = None
                    self.stationary_position = True

                else:
                    self.nearest_crossroad = self.current_path[1]

                if time_left == 0:
                    self.stationary_position = True

                self.mileage += distance_to_crossroad
                visited_nodes_times.append((self.current_position, self.current_time))

        return visited_nodes_times, events

    def check_if_event(self, events):
        """
        Check if certain node is associated with any of the passed events (origins/destinations)
        :param events: a tuple (node, event, traveller), where event is in ["a", "o", "d"]
        :return: updated event list and updated self. travellers and self. scheduled travellers
        """
        for event in events:
            if event[0] == self.current_position:
                if event[1] == "d":
                    self.travellers.remove(event[2])
                elif event[1] == "o":
                    self.travellers.append(event[2])


    def accept_request(self,
                       new_path,
                       new_travellers
                       ):
        """
        Update information upon accepting a new request
        :param new_path: new path for the vehicle
        :param new_travellers: a new set of travellers how are assigned to the vehicle
        :return:
        """
        self.current_path = new_path
        self.scheduled_travellers = new_travellers
