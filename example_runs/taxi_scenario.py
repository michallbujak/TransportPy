"""
Script for a basic run for only private taxi rides
"""
import os
from datetime import datetime as dt
from datetime import timedelta as td

import utils.common as utc

from base_objects.dispatcher import Dispatcher
from base_objects.traveller import Traveller
from base_objects.vehicle import Vehicle

os.chdir(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
# Initialise logger
logger = utc.initialise_logger("INFO")

# Initialise configuration
simulation_config = utc.load_config("data/configs/simulation_configs/simulation_config_test.json", logger)

# Read requests and fleet
requests = utc.load_any_excel(simulation_config["requests"])
vehicles = utc.load_any_excel(simulation_config["vehicles"])

# Read behavioural configuration and city parameters
city_config = utc.load_config(simulation_config["city_config"], logger)
behavioural_config = utc.load_config(simulation_config["behavioural_config"], logger)
skim = utc.load_skim(city_config, logger)

# Distinguish different types of fleet
fleet = utc.distinguish_fleet(vehicles, logger)

# Initialise Dispatcher
Dispatcher = Dispatcher(
    dispatcher_id=0,
    fares=simulation_config["fares"]['0'],
    operating_costs=simulation_config['operating_costs']['0'],
    fleet={'taxi': []}
)

# Store travellers
Travellers = {}

# Sort with respect to time
req_times = [(req['request_time'], 1, req) for num, req in requests.iterrows()]
veh_times = [(veh['start_time'], 0, veh) for veh in fleet['taxi']]
veh_req_times = sorted(req_times + veh_times, key=lambda x: (x[0], x[1]))

FLAG_FIRST = True

# Browse chronologically through new vehicles and rides
for veh_req in veh_req_times:
    current_time = utc.str_to_datetime(veh_req[0])

    if FLAG_FIRST:
        last_event_time = current_time
        FLAG_FIRST = False
        if veh_req[1] == 0:
            v = veh_req[2]
            Dispatcher.fleet['taxi'] += [Vehicle(
                vehicle_id=v['id'],
                start_node=v['origin'],
                start_time=utc.str_to_datetime(v['start_time']),
                end_time=utc.str_to_datetime(v['end_time']),
                capacity=v['capacity'],
                vehicle_speed=v['speed']
            )]
            continue
        else:
            raise NotImplementedError("First must come vehicle not travel request")

    time_between_events = utc.difference_times(last_event_time, current_time)
    last_event_time = current_time

    for ride in Dispatcher.rides['taxi']:
        if ride.active:
            utc.move_vehicle_ride(
                vehicle=ride.serving_vehicle,
                ride=ride,
                move_time=time_between_events,
                skim=skim,
                logger=logger
            )

    for veh in Dispatcher.fleet['taxi']:
        veh.path.current_time = current_time

    if veh_req[1] == 0:
        v = veh_req[2]
        Dispatcher.fleet['taxi'] += [Vehicle(
            vehicle_id=v['id'],
            start_node=v['origin'],
            start_time=utc.str_to_datetime(v['start_time']),
            end_time=utc.str_to_datetime(v['end_time']),
            capacity=v['capacity'],
            vehicle_speed=v['speed']
        )]
        continue

    traveller = Traveller(
        request=tuple(veh_req[2]),
        behavioural_details=behavioural_config
    )
    Travellers[veh_req[2]['id']] = traveller
    Dispatcher.assign_taxi(tuple(veh_req[2]), traveller, skim, logger, current_time)

    for veh in Dispatcher.fleet['taxi']:
        if veh.path.end_time <= current_time:
            veh.available = False


# Finish all started rides
while not all(not r.active for r in Dispatcher.rides['taxi']):
    current_time += td(minutes=5)
    time_between_events = utc.difference_times(last_event_time, current_time)
    last_event_time = current_time

    for ride in Dispatcher.rides['taxi']:
        if ride.active:
            utc.move_vehicle_ride(
                vehicle=ride.serving_vehicle,
                ride=ride,
                move_time=time_between_events,
                skim=skim,
                logger=logger
            )

    for veh in Dispatcher.fleet['taxi']:
        veh.path.current_time = current_time

utc.post_hoc_analysis(vehicles=Dispatcher.fleet['taxi'],
                      rides=Dispatcher.rides['taxi'],
                      travellers=Travellers,
                      config=simulation_config,
                      skim=skim,
                      logger=logger)

