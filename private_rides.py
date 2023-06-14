"""
Script for a basic run for only private taxi rides
"""
import pandas as pd

import utils.common as utc
from base_objects.dispatcher import Dispatcher
from base_objects.traveller import Traveller
from rides.taxi_ride import TaxiRide

# Initialise all required data
initial_config = utc.load_config("data/configs/simulation_configs/simulation_config_test.json")

requests = pd.read_excel(initial_config["requests"])
vehicles = pd.read_excel(initial_config["vehicles"])

city_config = utc.load_config(initial_config["city_config"])
behavioural_config = utc.load_config(initial_config["behavioural_config"])

fleet = utc.distinguish_fleet(vehicles)

Dispatcher = Dispatcher(
    dispatcher_id=1,
    fares=initial_config["fares"],
    fleet=fleet
)

x = 0