"""
Manage fleet - dispatch and estimate arrival times
"""
from dataclasses import dataclass

import utils.common
import utils.pool_utils


@dataclass
class Pricing:
    """ Store information regarding prices in the system """
    private_price: float
    pool_prices: dict


@dataclass
class CityProperties:
    """ Properties considering city specifics """
    speed: float


@dataclass
class Fleet:
    """ Contains list of all available types of vehicles """
    pool_cars: list
    private_cars: list


@dataclass
class OngoingRides:
    """ Store information on all ongoing rides """
    pooled_rides: list


class Dispatcher:
    """ Class designed to operate the fleet """

    def __init__(self, fleet, config):
        self.pricing = Pricing(
            private_price=config["private_price"],
            pool_prices=config["pool_prices"]
        )
        self.city_properties = CityProperties(
            speed=config["speed"]
        )
        self.fleet = fleet
        self.ongoing_rides = OngoingRides(
            pooled_rides=[]
        )

    def pick_up_delay(self, available_fleet, node, skim):
        """ Given the fleet, find minimal time to pick-up """
        if len(available_fleet) == 0:
            return None

        if len(available_fleet) == 1:
            return utils.common.compute_distance([available_fleet[0][1].current_position, node], skim) \
                / self.city_properties.speed

        minimal = (0, utils.common.compute_distance([available_fleet[0][1].current_position, node], skim))
        for num, veh in available_fleet[1:]:
            dist = utils.common.compute_distance([veh.current_position, node], skim)
            if dist < minimal[1]:
                minimal = (num, dist)
        return minimal

    def private_pick_up_delay(self, node, skim):
        """ Calculate the pick-up time for a private ride """
        strictly_private = [(num, t) for num, t in enumerate(self.fleet.private_cars) if t.available]
        min_strictly_private = self.pick_up_delay(strictly_private, node, skim)
        pooled = [(num, t) for num, t in enumerate(self.fleet.pool_cars) if t.available]
        min_pooled = self.pick_up_delay(pooled, node, skim)
        if min_strictly_private[1] < min_pooled[1]:
            return min_strictly_private[1], ('private', min_strictly_private[0])
        return min_pooled[1], ('pooled', min_pooled[0])

    def pooled_pick_up_delay(self, node, skim):
        """ Calculate the pick-up time for a private ride """
        available_fleet = [t for t in self.fleet.pool_cars if t.available]
        out = self.pick_up_delay(available_fleet, node, skim)
        return out[1], ('pooled', out[0])

    def dispatch_pooled(self, traveller, skim):
        """ Find the most feasible shared ride """
        minimals = []
        for pooled_ride in self.ongoing_rides.pooled_rides:
            origins_destinations = [t[0] for t in pooled_ride.events.future_events if t[1] == 'o' or t[1] == 'd'] + \
                                   [traveller.request_details.origin] + \
                                   [traveller.request_details.destination]
            combinations = utils.pool_utils.admissible_future_combinations(origins_destinations)
            for comb in combinations:
                out = pooled_ride.new_future_profit(comb, self, skim)
                if out[0]:
                    travellers = pooled_ride.travellers.scheduled_travellers + [traveller]
                    utilities = pooled_ride.shared_ride_utilities(
                        event_sequence=comb,
                        travellers=travellers,
                        dispatcher=self,
                        skim=skim
                    )
                    if all([utilities[trav.traveller_id] >= trav.utilities['private'] for trav in travellers]):
                        minimals.append((out[1], pooled_ride))
        if len(minimals) > 0:
            matched_ride = min(minimals, key=lambda x: x[0])[1]




