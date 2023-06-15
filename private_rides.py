"""
Script for a basic run for only private taxi rides
"""
import pandas as pd

import utils.common as utc
from base_objects.dispatcher import Dispatcher
from base_objects.traveller import Traveller
from base_objects.vehicle import Vehicle
from rides.taxi_ride import TaxiRide

# Initialise logger
logger = utc.initialise_logger("INFO")

# Initialise all required data
initial_config = utc.load_config("data/configs/simulation_configs/simulation_config_test.json", logger)

requests = pd.read_excel(initial_config["requests"])
vehicles = pd.read_excel(initial_config["vehicles"])

city_config = utc.load_config(initial_config["city_config"], logger)
behavioural_config = utc.load_config(initial_config["behavioural_config"], logger)

fleet = utc.distinguish_fleet(vehicles, logger)

Dispatcher = Dispatcher(
    dispatcher_id=1,
    fares=initial_config["fares"],
    fleet={}
)

skim = utc.load_skim(city_config, logger)

req_times = [(req['request_time'], 1, req) for num, req in requests.iterrows()]
veh_times = [(veh['start_time'], 0, veh) for veh in fleet['taxi']]
veh_req_times = sorted(req_times + veh_times, key=lambda x: (x[0], x[1]))

for veh_req in veh_req_times:
    if veh_req[1] == 0:
        v = veh_req[2]
        Dispatcher.fleet['taxi'] += Vehicle(
            vehicle_id=v['id'],
            start_node=v['origin'],
            start_time=v['start_time'],
            capacity=v['capacity'],
            vehicle_speed=v['speed']
        )
        continue
    else:
        # Dispatcher.assign_taxi()
        pass



