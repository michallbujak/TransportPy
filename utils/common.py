""" Tools used across scripts """
import json
import os
import sys

import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
import logging
from datetime import datetime as dt

from datetime import timedelta
from dataclasses import asdict

from base_objects.vehicle import Vehicle
from base_objects.ride import Ride


def initialise_logger(
        logger_level: str = 'INFO'
) -> logging.Logger:
    """
    Initialise logger which will be used to provide information on consecutive algorithmic steps
    :param logger_level: level of information
    :return: logger
    """
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
    logger.warning("Fleet assigned by types")
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

    skim_matrix.columns = [int(t) for t in skim_matrix.columns]
    logger.warning("Skim matrix and city graphs loaded")

    return {"type": "graph", "city_graph": city_graph, "skim_matrix": skim_matrix}


def load_any_excel(path:str
                   ) -> pd.DataFrame:
    """
    Flexible function to read either .csv or .xlsx
    @param path: path to the file
    @return: desired dataframe
    """
    try:
        return pd.read_excel(path)
    except UnicodeDecodeError:
        return pd.read_csv(path)


def compute_distance(list_of_points: list,
                     skim: dict
                     ) -> float:
    assert len(list_of_points) >= 2
    if len(list_of_points) == 2:
        if list_of_points[0] == list_of_points[1]:
            return 0
        return skim["skim_matrix"].loc[list_of_points[0], list_of_points[1]]
    dist = 0
    current_node = list_of_points[0]
    for node in list_of_points[1:]:
        if node == current_node:
            continue
        dist += skim["skim_matrix"][current_node][node]
        current_node = node
    return dist


def difference_times(time1, time2):
    def foo(time):
        if isinstance(time, str):
            return dt.strptime(time, '%Y-%m-%d %H:%M:%S')
        return time

    time1 = foo(time1)
    time2 = foo(time2)
    return (time2 - time1).total_seconds()


def compute_path(list_of_points: list,
                 skim: dict
                 ) -> list:
    assert len(list_of_points) >= 2
    if skim["type"] == "graph":
        current_node = list_of_points[0]
        path = [current_node]
        for node in list_of_points[1:]:
            path += nx.shortest_path(
                G=skim["city_graph"],
                source=current_node,
                target=node,
                weight='weight'
            )[1:]
            current_node = node
    else:
        raise NotImplementedError("Currently not implemented")

    return path


def move_vehicle_ride(vehicle: Vehicle,
                      ride: Ride,
                      time: int,
                      skim: dict,
                      logger: logging.Logger
                      ) -> None:
    """
    Function which is designed to move the vehicle along request route
    :param vehicle: Vehicle object
    :param ride: Ride object
    :param time: time by which the vehicle is moved
    :param skim: dictionary with distances
    :param logger: logging purposes
    @type vehicle: Vehicle
    @type ride: Ride
    @type logger: logging.Logger
    """
    avg_speed = vehicle.vehicle_speed
    time_left = time

    while vehicle.path.current_path is not None:
        assert (
                vehicle.path.nearest_crossroad is not None
        ), "The path has not been updated, vehicle does not have a path to follow"

        vehicle.path.stationary_position = False
        distance_to_crossroad = compute_distance(
            [vehicle.path.current_position, vehicle.path.current_path[1]], skim
        )
        time_required_to_crossroad = \
            distance_to_crossroad / avg_speed - vehicle.path.time_between_crossroads

        if time_left < time_required_to_crossroad:
            # not sufficient time to reach the nearest crossroad
            vehicle.path.time_between_crossroads = vehicle.path.time_between_crossroads + time_left
            vehicle.path.current_time = vehicle.path.current_time + timedelta(seconds=time_left)
            break

        # sufficient time to reach the nearest crossroad
        vehicle.mileage += distance_to_crossroad
        time_left -= time_required_to_crossroad
        vehicle.path.current_time = vehicle.path.current_time + timedelta(
            seconds=time_required_to_crossroad
        )
        vehicle.path.current_position = vehicle.path.current_path[1]
        vehicle.path.current_path = vehicle.path.current_path[1:]
        vehicle.path.time_between_crossroads = 0

        if len(vehicle.path.current_path) == 1:
            vehicle.path.current_path = None
            vehicle.path.nearest_crossroad = None
            vehicle.path.stationary_position = True
            vehicle.available = True
            ride.active = False

        else:
            vehicle.path.nearest_crossroad = vehicle.path.current_path[1]

        # Check from the request perspective whether something happens at those nodes
        events = [t for t in ride.locations if t[0] == vehicle.path.current_position]
        for event in events:
            if event[1] == 'o':
                ride.travellers += [event[2]]
                vehicle.travellers += [event[2]]
                vehicle.scheduled_travellers.remove(event[2])
            if event[1] == 'd':
                ride.travellers.remove(event[2])
                vehicle.travellers.remove(event[2])
            if event[1] == 'a':
                vehicle.scheduled_travellers += [event[2]]

    logger.debug(f"Vehicle {vehicle} moved by {time}s")

    return None
