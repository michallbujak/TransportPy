"""
Create a ride class - object to store information regarding one separate ride
"""
from dataclasses import dataclass
from datetime import datetime

from objects.dispatcher import Dispatcher

import utils.common


@dataclass
class Events:
    """ Store information on events en route """
    past_events: list
    future_events: list


@dataclass
class Travellers:
    """ Store information regarding travellers """
    travellers: list
    scheduled_travellers: list
    pickup_delays: dict


@dataclass
class Profit:
    """ Store information regarding profit """
    past_profit: float or None
    future_profit: float or None


class PoolRide:
    """
    Class representing realisation of a certain ride.
    It starts with some request and progresses over time.
    Possibly becomes a shared ride.
    """

    def __init__(self,
                 travellers: list,
                 start_time: datetime,
                 request: tuple):
        """
        :param travellers: list of Travellers objects
        :param start_time: starting time, datetime object
        :param request: (traveller_id, starting_point, end_point, start_time)
        """
        super().__init__(self, travellers, start_time)
        self.start_time = start_time
        self.events = Events(
            future_events=[(request[1], 'o', request[0]), (request[2], 'd', request[0])],
            past_events=[]
        )
        self.travellers = Travellers(
            travellers=[],
            scheduled_travellers=travellers,
            pickup_delays={}
        )
        self.profit = Profit(
            past_profit=None,
            future_profit=None
        )

    def new_future_profit(self,
                          event_sequence: list,
                          dispatcher: Dispatcher,
                          skim: dict):
        """ Calculated profit in the situation of a new traveller"""
        profit = 0
        prev_event = event_sequence[0]
        travellers_no = 1
        for event in event_sequence[1:]:
            dist = utils.common.compute_distance([prev_event[0], event[0]], skim)
            profit += dist * dispatcher.pricing.pool_prices[travellers_no] * travellers_no
            if event[1] == 'o' and travellers_no < 4:
                travellers_no += 1
            if event[1] == 'd' and travellers_no == 1:
                break
            if event[1] == 'd' and travellers_no != 1:
                travellers_no -= 1
        return profit > self.profit.future_profit, profit


    def shared_ride_utilities(self,
                              event_sequence: list,
                              travellers: list,
                              skim):
        utilities = {t.traveller_id: 0 for t in travellers}
        all_events = self.events.past_events + event_sequence
        current_travellers = [all_events[0][2]]
        no_travellers = 1
        past_event = all_events[0]
        pickup_delays = {}
        past_time =
        for event in all_events:



