import os
from datetime import datetime as dt
from datetime import timedelta as td

import utils.common as utc
from dispatchers.taxidispatcher import TaxiDispatcher
from base_objects.traveller import Traveller
from base_objects.vehicle import Vehicle

os.chdir(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))

# Initialise data, configs and logger
simulation_config, logger, requests, vehicles, city_config, \
    behavioural_config, fare_config, skim, fleet = utc.initialise_simulation(
    "data/configs/simulation_configs/simulation_config_pool.json"
)

# Initialise Operators
Dispatcher = TaxiDispatcher(
    dispatcher_id=0,
    fares=simulation_config["fares"]['0'],
    operating_costs=simulation_config['operating_costs']['0']
)

