"""
Script for a basic run for only private taxi rides
"""
from datetime import datetime as dt

import utils.common as utc
from base_objects.dispatcher import Dispatcher
from base_objects.traveller import Traveller
from base_objects.vehicle import Vehicle

# Initialise logger
logger = utc.initialise_logger("INFO")

# Initialise all required data
initial_config = utc.load_config("data/configs/simulation_configs/simulation_config_test.json", logger)

requests = utc.load_any_excel(initial_config["requests"])
vehicles = utc.load_any_excel(initial_config["vehicles"])

city_config = utc.load_config(initial_config["city_config"], logger)
behavioural_config = utc.load_config(initial_config["behavioural_config"], logger)

fleet = utc.distinguish_fleet(vehicles, logger)

Dispatcher = Dispatcher(
    dispatcher_id=1,
    fares=initial_config["fares"],
    fleet={'taxi': []}
)
Dispatcher.rides['taxi'] = []

Travellers = {}

skim = utc.load_skim(city_config, logger)

req_times = [(req['request_time'], 1, req) for num, req in requests.iterrows()]
veh_times = [(veh['start_time'], 0, veh) for veh in fleet['taxi']]
veh_req_times = sorted(req_times + veh_times, key=lambda x: (x[0], x[1]))

FLAG_FIRST = True

for veh_req in veh_req_times:
    current_time = utc.str_to_datetime(veh_req[0])
    if veh_req[1] == 0:
        v = veh_req[2]
        Dispatcher.fleet['taxi'] += [Vehicle(
            vehicle_id=v['id'],
            start_node=v['origin'],
            start_time=utc.str_to_datetime(v['start_time']),
            capacity=v['capacity'],
            vehicle_speed=v['speed']
        )]
        continue

    if FLAG_FIRST:
        last_event_time = current_time
        FLAG_FIRST = False
        continue

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

    traveller = Traveller(
        request=tuple(veh_req[2]),
        behavioural_details=behavioural_config
    )
    Travellers[veh_req[2]['id']] = traveller
    Dispatcher.assign_taxi(tuple(veh_req[2]), traveller, skim, logger, current_time)

