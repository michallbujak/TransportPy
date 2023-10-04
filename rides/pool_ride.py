"""
Class representing on-demand shared travel, where traveller
requests a ride from a Dispatcher
"""
from typing import Any
import itertools

from base_objects.traveller import Traveller
from base_objects.ride import Ride
from base_objects.vehicle import Vehicle
from rides.taxi_ride import TaxiRide

from utils.common import compute_distance as dist
from utils.common import compute_path as find_path


class PoolRide(Ride):
    """
    Private on-demand transport
    """

    def __init__(self, traveller, destination_points, ride_type):
        super().__init__([traveller], destination_points, ride_type)
        self.events = []
        self.vehicle_start_position = None
        self.adm_combinations = []
        self.shared = False

    def __repr__(self):
        return f"Pool: {self.travellers}"

    def calculate_utility(self,
                          vehicle: Any,
                          traveller: Traveller,
                          nodes_seq: list,
                          fare: float,
                          pool_discount: float,
                          skim: dict,
                          **kwargs
                          ) -> float:
        """
        Calculate utility for the traveller
        :param vehicle: Vehicle or child class object
        :param traveller: Traveller object
        :param nodes_seq: (node, event, traveller)
         to be visited along the route
        :param fare: fare in monetary units/meter
        :param pool_discount: discount for a pooled ride
        :param skim: distances dictionary
        :return: utility
        """
        # Check if already picked_up:
        if traveller.service_details.pickup_delay is not None:
            pickup_delay = traveller.service_details.pickup_delay
            start = [node for node in self.past_destination_points
                     if (node[1] == 'o' and node[2] == traveller.traveller_id)][0]
            finish = [node for node in nodes_seq
                      if (node[1] == 'd' and node[2] == traveller.traveller_id)][0]
            start_id = self.past_destination_points.index(start)
            finish_id = nodes_seq.index(finish)
            trip = [t[0] for t in self.past_destination_points[start_id:]]
            trip += [vehicle.path.current_position]
            trip += [vehicle.path.closest_crossroad]
            trip += [t[0] for t in nodes_seq[:(finish_id + 1)]]
            trip_length = dist(trip, skim)

        else:
            start = [node for node in nodes_seq
                     if (node[1] == 'o' and node[2] == traveller.traveller_id)][0]
            start_id = nodes_seq.index(start)
            finish = [node for node in nodes_seq
                      if (node[1] == 'd' and node[2] == traveller.traveller_id)][0]
            finish_id = nodes_seq.index(finish)
            pickup_delay = dist([vehicle.path.closest_crossroad]
                                + [t[0] for t in nodes_seq[:(start_id + 1)]],
                                skim)
            pickup_delay *= vehicle.vehicle_speed
            pickup_delay += vehicle.path.to_closest_crossroads
            trip = [t[0] for t in
                    nodes_seq[nodes_seq.index(start):
                              (finish_id + 1)]]
            trip_length = dist(trip, skim)

        # Utility calculation
        pref = traveller.behavioural_details

        if kwargs.get("pooled_ride", True):
            fare_updated = fare * (1 - pool_discount)
            no_travellers = len(self.travellers)
            trip_time = trip_length / vehicle.vehicle_speed

            utility = -trip_length * fare_updated
            utility -= trip_time * pref['VoT'] * pref['pool_rides']['PfS'][str(no_travellers)]
            utility -= pickup_delay * pref['VoT'] * pref['pickup_delay_sensitivity']
            utility -= pref['pool_rides']['PfS_const']

        else:
            utility = -trip_length * fare
            utility -= trip_length / vehicle.vehicle_speed * pref['VoT']
            utility -= pickup_delay * pref['VoT'] * pref['pickup_delay_sensitivity']

        return utility

    def calculate_profitability(self,
                                fare: float,
                                operating_cost: float,
                                skim: dict,
                                new_ods: list or None = None,
                                additional_traveller: Traveller or None = None,
                                sharing_discount: float or None = None,
                                update_self: bool = False
                                ) -> None or tuple[float]:
        if additional_traveller is not None:
            travellers = self.travellers + [additional_traveller]
        else:
            travellers = self.travellers
        if len(travellers) == 1:
            shared = False
        else:
            shared = True

        if shared:
            revenue = sum(t.request_details.trip_length for t in travellers)
            revenue *= fare * (1 - sharing_discount)
        else:
            revenue = travellers[0].request_details.trip_length * fare

        veh_movement = [t[1] for t in self.events]
        if new_ods is None:
            veh_movement += [t[0] for t in self.destination_points]
        else:
            veh_movement += [t[0] for t in new_ods]

        cost = dist(veh_movement, skim) * operating_cost

        if update_self:
            self.profitability.revenue = revenue
            self.profitability.cost = cost
            self.profitability.profit = revenue - cost
        else:
            return revenue, cost, revenue - cost

    def add_traveller(self,
                      traveller: Traveller,
                      new_profitability: tuple or list,
                      ods_sequence: list,
                      adm_combinations: list[tuple] or list[list],
                      skim: dict
                      ) -> None:
        """
        If a ride is considered attractive for the new traveller
        assign him/her to the ride
        @param traveller: Traveller who is to be assigned
        @param new_profitability: values calculated prior to assignment (revenue, cost, profit)
        @param ods_sequence: sequence of origins and destinations along the route
        @param adm_combinations: list of sequences of admissible combinations
        @param skim: skim dictionary
        """
        # Update vehicle
        vehicle = self.serving_vehicle
        vehicle.scheduled_travellers.append(traveller)

        if len(vehicle.scheduled_travellers) + len(vehicle.travellers) >= vehicle.maximal_occupancy:
            vehicle.available = False

        vehicle.path.current_path = find_path(
            list_of_points=[vehicle.path.current_position] +
                           [vehicle.path.closest_crossroad] +
                           [t[0] for t in ods_sequence],
            skim=skim
        )

        # Update self
        self.profitability.revenue = new_profitability[0]
        self.profitability.cost = new_profitability[1]
        self.profitability.profit = new_profitability[2]
        self.travellers.append(traveller)
        self.destination_points = ods_sequence
        self.shared = True
        self.adm_combinations = adm_combinations
