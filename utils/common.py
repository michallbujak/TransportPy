""" Tools used across scripts """
import json
import os
import sys

import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
import logging

from datetime import timedelta
from dataclasses import asdict


def initialise_logger(
        logger_level: str = 'INFO'
) -> logging.Logger:
    '''
    Initialise logger which will be used to provide information on consecutive algorithmic steps
    :param logger_level: level of information
    :return: logger
    '''
    logging.basicConfig(stream=sys.stdout, format='%(asctime)s-%(levelname)s-%(message)s',
                        datefmt='%H:%M:%S', level=logger_level)
    logger = logging.getLogger()
    return logger


def load_config(
        path: str,
        logger: logging.Logger
) -> dict:
    """
    Load configuration files from .json format
    :param path: path to the configuration file
    :param logger: logger for information
    :return: configuration dictionary
    """
    with open(path, encoding='utf-8') as json_file:
        config = json.load(json_file)
    logger.info(f"Successfully loaded config from {path}")
    return config


def distinguish_fleet(
        vehicles: pd.DataFrame,
        logger: logging.Logger
) -> dict:
    """
    Split fleet by vehicle type
    :param vehicles dataframe with vehicles
    :param logger for logging purposes
    :return: fleet with assigned types (dict)
    """
    types = np.unique(np.array(vehicles["type"]))
    fleet = dict()
    for t in types:
        fleet[t] = []
        for num, veh in vehicles.loc[vehicles["type"] == t].iterrows():
            fleet[t].append(veh)
    logger.debug("Fleet assigned by types")
    return fleet


def folder_creator(
        path: str,
        logger: logging.Logger
) -> None:
    """
    Designed to create a folder under given path
    :param path: a path to create a folder
    :param logger: logging purposes
    :return:
    """
    try:
        os.mkdir(path)
    except OSError:
        pass
    else:
        logger.info(f'Creating folder at {path}')


def load_skim(
        city_config: dict,
        logger: logging.Logger,
        skim_type: str = 'graph'
) -> dict:
    """
    Load data necessarily for distance and paths calculations
    :param city_config: configuration of the city
    :param logger: for logging purposes
    :param skim_type: type of configuration for calculations
    :return: skim - dictionary with way of calculation and data
    """
    if skim_type != 'graph':
        raise NotImplementedError("Currently only shortest paths implemented")

    try:
        city_graph = nx.read_graphml(city_config['paths']['city_graph'])
    except FileNotFoundError:
        logger.info("City graph missing, using osmnx")
        logger.info(f"Writing the city graph to {city_config['paths']['city_graph']}")
        city_graph = ox.graph_from_place(city_config['city'], network_type='drive')
        ox.save_graphml(city_graph, city_config['paths']['city_graph'])
        city_config['paths']['city_graph'] = city_config['paths']['city_graph']
    else:
        logger.info("Successfully read city graph")

    try:
        skim_matrix = pd.read_parquet(city_config['paths']['skim_matrix'])
    except FileNotFoundError:
        logger.info("Skim matrix missing, calculating...")
        skim_matrix = pd.DataFrame(dict(nx.all_pairs_dijkstra_path_length(city_graph, weight='length')))
        skim_matrix.columns = [str(col) for col in skim_matrix.columns]

        logger.info(f"Writing the skim matrix to {city_config['paths']['skim_matrix']}")
        skim_matrix.to_parquet(city_config['paths']['skim_matrix'], compression='brotli')
        city_config['paths']['skim_matrix'] = city_config['paths']['skim_matrix']
    else:
        logger.info("Successfully read skim matrix")

    return {"type": "graph", "city_graph": city_graph, "skim_matrix": skim_matrix}


def compute_distance(list_of_points, skim):
    return 0


def compute_path(list_of_points, skim):
    return 0


def move_vehicle_ride(veh_ride, time, skim, event_behaviour=None, veh_speed=6):
    try:
        avg_speed = veh_ride.vehicle_speed
    except AttributeError:
        avg_speed = veh_speed

    time_left = time
    while veh_ride.path.current_path is not None:
        assert (
                veh_ride.path.nearest_crossroad is not None
        ), "The path has not been updated, vehicle does not have a path to follow"

        veh_ride.path.stationary_position = False
        distance_to_crossroad = compute_distance(
            [veh_ride.path.current_position, veh_ride.path.current_path[1]], skim
        )
        time_required_to_crossroad = \
            distance_to_crossroad / avg_speed - veh_ride.path.time_between_crossroads

        if time_left < time_required_to_crossroad:
            # not sufficient time to reach the nearest crossroad
            veh_ride.path.time_between_crossroads = veh_ride.path.time_between_crossroads + time_left
            veh_ride.path.current_time = veh_ride.path.current_time + timedelta(seconds=time_left)
            break

        # sufficient time to reach the nearest crossroad
        time_left -= time_required_to_crossroad
        veh_ride.path.current_time = veh_ride.path.current_time + timedelta(
            seconds=time_required_to_crossroad
        )
        veh_ride.path.current_position = veh_ride.path.current_path[1]
        veh_ride.path.current_path = veh_ride.path.current_path[1:]
        veh_ride.path.time_between_crossroads = 0

        if len(veh_ride.path.current_path) == 1:
            veh_ride.path.current_path = None
            veh_ride.path.nearest_crossroad = None
            if 'stationary_position' in asdict(veh_ride.path).keys():
                veh_ride.path.stationary_position = True

        else:
            veh_ride.path.nearest_crossroad = veh_ride.path.current_path[1]

        if event_behaviour is not None:
            event_behaviour['foo'](veh_ride, event_behaviour['events'])

    return None
