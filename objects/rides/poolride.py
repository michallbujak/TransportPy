"""
Create a ride class - object to store information regarding one separate ride
"""
from dataclasses import dataclass
from datetime import datetime

from objects.dispatcher import Dispatcher

import utils.common
import utils.pool_utils


@dataclass
class Events:
    """ Store information on events en route """
    past_events: list
    future_events: list


@dataclass
class Travellers:
    """ Store information regarding travellers """
    travellers: dict
    scheduled_travellers: dict
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
                 travellers: dict,
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
            travellers={},
            scheduled_travellers=travellers,
            pickup_delays={}
        )
        self.profit = Profit(
            past_profit=None,
            future_profit=None
        )

    @staticmethod
    def update_traveller_number(event, travellers_no):
        flag = False
        if event[1] == 'o':
            travellers_no += 1
        if event[1] == 'd' and travellers_no == 1:
            flag = True
        if event[1] == 'd' and travellers_no != 1:
            travellers_no -= 1
        return travellers_no, flag

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
            price = dispatcher.pricing.pool_prices[travellers_no if travellers_no < 4 else 4]
            profit += dist * price * travellers_no

            travellers_no, break_flag = self.update_traveller_number(event, travellers_no)
            if break_flag:
                break

        return profit > self.profit.future_profit, profit

    def update_utility(self, visited_nodes):
        ...

    def shared_ride_utilities(self,
                              event_sequence: list,
                              travellers: list,
                              dispatcher: Dispatcher,
                              skim: dict
                              ):
        utilities = {t.traveller_id: 0 for t in travellers}
        all_events = self.events.past_events + event_sequence
        current_travellers = [all_events[0][2]]
        travellers_no = 1
        prev_event = all_events[0]
        pickup_delays = self.travellers.pickup_delays.items()
        for event in all_events:
            dist = utils.common.compute_distance([prev_event[0], event[0]], skim)

            # Update traveller number
            travellers_no, break_flag = self.update_traveller_number(event, travellers_no)
            if break_flag:
                break

            # Update utilities
            for traveller in current_travellers:
                utilities[traveller] -= utils.pool_utils.pooled_partial_utility_formula(
                    distance=dist,
                    dispatcher=dispatcher,
                    no_travellers=travellers_no,
                    traveller=self.travellers.scheduled_travellers[traveller]
                )

            # If some trip finishes, add additional discomforts
            if event[1] == 'd':
                utils.pool_utils.pooled_additional_utility(
                    traveller=self.travellers.scheduled_travellers[event[2]],
                    pickup_delay=pickup_delays[event[2]]
                )
                current_travellers.remove(event[2])

            # If some trip starts
            if event[1] == 'o':



