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

from datetime import timedelta, date
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
    logging.basicConfig(stream=sys.stdout, format=f'%(message)s (%(asctime)s)',
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
    try:
        with open(path, encoding='utf-8') as json_file:
            config = json.load(json_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Check path to the 'config' file"
                                f" incorrect {path}")
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
        logger.warning(f'Creating folder at {path}')


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
        logger.warning("City graph missing, using osmnx")
        logger.warning(f"Writing the city graph to {city_config['paths']['city_graph']}")
        city_graph = ox.graph_from_place(city_config['city'], network_type='drive')
        ox.save_graphml(city_graph, city_config['paths']['city_graph'])
        city_config['paths']['city_graph'] = city_config['paths']['city_graph']
    else:
        logger.warning("Successfully read city graph")

    try:
        skim_matrix = pd.read_parquet(city_config['paths']['skim_matrix'])
    except FileNotFoundError:
        logger.warning("Skim matrix missing, calculating...")
        skim_matrix = pd.DataFrame(dict(nx.all_pairs_dijkstra_path_length(city_graph, weight='length')))
        skim_matrix.columns = [str(col) for col in skim_matrix.columns]

        logger.warning(f"Writing the skim matrix to {city_config['paths']['skim_matrix']}")
        skim_matrix.to_parquet(city_config['paths']['skim_matrix'], compression='brotli')
        city_config['paths']['skim_matrix'] = city_config['paths']['skim_matrix']
    else:
        logger.warning("Successfully read skim matrix")

    skim_matrix.columns = [int(t) for t in skim_matrix.columns]
    city_graph = nx.relabel_nodes(city_graph, {t: int(t) for t in city_graph.nodes})
    logger.error("Skim matrix and city graphs loaded")

    return {"type": "graph", "city_graph": city_graph, "skim_matrix": skim_matrix}


def load_any_excel(path: str
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
    except FileNotFoundError:
        raise FileNotFoundError(f"File xlsx/csv not found in {path}")


def str_to_datetime(input_string: str,
                    str_format: str = '%Y-%m-%d %H:%M:%S'
                    ) -> dt:
    """
    Convert string to datetime
    @param input_string: string with date
    @param str_format: format of the string
    @return: return
    """
    return dt.strptime(input_string, str_format)


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
                      move_time: int,
                      skim: dict,
                      logger: logging.Logger
                      ) -> None:
    """
    Function which is designed to move the vehicle along request route
    :param vehicle: Vehicle object
    :param ride: Ride object
    :param move_time: time by which the vehicle is moved
    :param skim: dictionary with distances
    :param logger: logging purposes
    @type vehicle: Vehicle
    @type ride: Ride
    @type move_time: int
    @type skim: dict
    @type logger: logging.Logger
    """
    avg_speed = vehicle.vehicle_speed
    time_left = move_time

    def foo(_r, _v):
        curr_time = _v.path.current_time
        evs = [t for t in _r.destination_points if t[0] == _v.path.current_position]
        for ev in evs:
            if ev[1] == 'o':
                _r.travellers += [ev[2]]
                _v.events.append((_v.path.current_time, _v.path.current_position, 'p', ev[2]))
                try:
                    _r.events += [(_v.path.current_time, _v.path.current_position, 'o', ev[2])]
                except AttributeError:
                    pass
                _v.travellers += [ev[2]]
                try:
                    logger.info(f"{curr_time}: Traveller {ev[2]} joined vehicle {_v}")
                    _v.scheduled_travellers.remove([t for t in _v.scheduled_travellers if t.traveller_id == ev[2]][0])
                except AttributeError:
                    pass
            if ev[1] == 'd':
                _r.travellers.remove(ev[2])
                _r.events.append((_v.path.current_time, _v.path.current_position, 'd', ev[2]))
                _v.travellers.remove(ev[2])
                _v.events.append((_v.path.current_time, _v.path.current_position, 'd', ev[2]))
                logger.info(f"{curr_time}: Traveller {ev[2]} finished trip")
            if ev[1] == 'a':
                _v.scheduled_travellers += [ev[2]]
                _v.events.append((_v.path.current_time, _v.path.current_position, 'a', ev[2]))
            _r.destination_points.remove(ev)

        return _r, _v

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
        time_required_to_crossroad = int(time_required_to_crossroad)

        if time_left < time_required_to_crossroad:
            # not sufficient time to reach the nearest crossroad
            logger.debug(f"Vehicle {vehicle}: Insufficient time to reach"
                         f" crossroad {vehicle.path.current_path[1]}")
            vehicle.path.time_between_crossroads = vehicle.path.time_between_crossroads + time_left
            vehicle.path.current_time = vehicle.path.current_time + timedelta(seconds=time_left)
            ride, vehicle = foo(ride, vehicle)
            break

        # sufficient time to reach the nearest crossroad
        logger.debug(f"{vehicle.path.current_time}: Vehicle {vehicle}: Reached"
                     f" crossroad {vehicle.path.current_path[1]}")
        vehicle.mileage += distance_to_crossroad
        time_left -= time_required_to_crossroad
        vehicle.path.current_time = vehicle.path.current_time + timedelta(
            seconds=time_required_to_crossroad
        )
        ride, vehicle = foo(ride, vehicle)
        vehicle.path.current_position = vehicle.path.current_path[1]
        vehicle.path.current_path = vehicle.path.current_path[1:]
        vehicle.path.time_between_crossroads = 0

        if len(vehicle.path.current_path) == 1:
            vehicle.path.current_path = None
            vehicle.path.nearest_crossroad = None
            vehicle.path.stationary_position = True
            vehicle.available = True
            ride.active = False
            logger.warning(f"{vehicle.path.current_time}: "
                           f"Ride {ride} finished with vehicle {vehicle}")

        else:
            vehicle.path.nearest_crossroad = vehicle.path.current_path[1]

        # Check from the request perspective whether something happens at those nodes
        ride, vehicle = foo(ride, vehicle)

    logger.debug(f"{vehicle.path.current_time}:"
                 f" Vehicle {vehicle} moved by {move_time}s")

    return None


def post_hoc_analysis(
        vehicles: list,
        rides: list,
        travellers: dict,
        config: dict,
        skim: dict,
        logger: logging.Logger
) -> None:
    """
    Analyse run
    @param vehicles: list of vehicles
    @param rides: list of rides
    @param travellers: list of travellers
    @param config: simulation configuration
    @param skim: to compute distances
    @param logger: logger for logging purposes
    @return: None
    """
    def foo(vehicles_rides, is_vehicle=False):
        events = [_t.events for _t in vehicles_rides]
        if is_vehicle:
            events = [list(item) + [_id] for sublist, _id in
                      zip(events, [t.vehicle_id for t in vehicles_rides])
                      for item in sublist]
        else:
            events = [item for sublist in events for item in sublist]
        events = sorted(events, key=lambda x: (x[0], x[3]))

        def foo2(element):
            t_0 = element[0].strftime('%Y-%m-%d %H:%M:%S')
            return [t_0] + list(element[1:])

        events = [foo2(t) for t in events]
        return events

    def foo3(event_list, name, is_vehicle=False):
        with open(config["output_path"] + str(date.today()) + '/' + name + '_log.txt',
                  'w', encoding='utf-8') as f:
            lengths = {
                0: 20,
                1: 12,
                2: 4,
                3: 12,
                4: 10
            }
            f.write("DATE".ljust(lengths[0]) + " || ")
            f.write("NODE".ljust(lengths[1]) + " || ")
            f.write("TYPE".ljust(lengths[2]) + " || ")
            f.write("TRAVELLER ID".ljust(lengths[3]))
            if is_vehicle:
                f.write(" || VEHICLE ID".ljust(lengths[4] + 4))
            f.write("\n")
            for _event in event_list:
                for num, element in enumerate(_event):
                    if element is None:
                        element = " "
                    f.write(str(element).ljust(lengths[num]))
                    if num != len(_event) - 1:
                        f.write(" || ")
                    else:
                        f.write('\n')

    veh_events = foo(vehicles, True)
    ride_events = foo(rides)

    folder_creator(config["output_path"], logger)
    folder_creator(config["output_path"] + str(date.today()), logger)

    foo3(veh_events, 'vehicle', True)
    foo3(ride_events, 'ride')

    # global perspective analysis
    total_vehicle_mileage = round(sum([_v.mileage for _v in vehicles]), 1)
    rides_mileage = 0
    for ride in rides:
        nodes_visited = []
        for event in ride.events:
            if event[2] == 'o' or event[2] == 'd':
                nodes_visited.append(event[1])
        rides_mileage += compute_distance(nodes_visited, skim)

    # Utility analysis
    with open(config["output_path"] + str(date.today()) + '/utility_log.txt',
              'w', encoding='utf-8') as f:
        f.write("PAX ID".ljust(10))
        f.write(" || UTILITIES \n")
        for pax_id, pax in travellers.items():
            f.write(str(pax_id).ljust(10) + " || ")
            for ut_name, ut_val in pax.utilities.items():
                f.write(f"{ut_name}: {ut_val} |")
            f.write("\n")

    logger.error("Post-hoc analysis finished, results saved")
