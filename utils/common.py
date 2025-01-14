""" Tools used across scripts """
import json
import os
import sys
import pickle
import logging

from datetime import datetime as dt
from datetime import date

import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx


def initialise_logger(
        logger_level: str or float = 'INFO'
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


def log_if_logger(
        logger: logging.Logger or None,
        level: float,
        message: str
) -> None:
    """
    Pass a message through the logger only if it was initialised
    @param logger: the logging.Logger
    @param level: 0, 10, 20, 30, 40, 50 as the levels
    @param message: message to be logged
    @return:
    """
    if logger is None:
        return None
    else:
        logger.log(level, message)




def load_config(
        path: str,
        logger: logging.Logger or None = None
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
    except FileNotFoundError as exc:
        raise exc

    if logger is not None:
        logger.info(f"Successfully loaded config from {path}")
    return config


def distinguish_fleet(
        vehicles: pd.DataFrame or None,
        logger: logging.Logger or None = None
) -> dict or None:
    """
    Split fleet by vehicle type
    :param vehicles dataframe with vehicles
    :param logger for logging purposes
    :return: fleet with assigned types (dict)
    """
    if vehicles is None:
        return None

    types = np.unique(np.array(vehicles["type"]))
    fleet = {}
    for _type in types:
        fleet[_type] = []
        for num, veh in vehicles.loc[vehicles["type"] == _type].iterrows():
            fleet[_type].append(veh)
    try:
        logger.warning("Fleet assigned by types")
    except AttributeError:
        pass
    return fleet


def folder_creator(
        path: str,
        logger: logging.Logger or None = None
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
        log_if_logger(logger, 30, f'Creating folder at {path}')


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
        # city_graph = nx.read_graphml(city_config['paths']['city_graph'])
        city_graph = pickle.load(open(city_config['paths']['city_graph'], 'rb'))
    except FileNotFoundError:
        logger.warning("City graph missing, using osmnx")
        logger.warning(f"Writing the city graph to {city_config['paths']['city_graph']}")
        city_graph = ox.graph_from_place(city_config['city'], network_type='drive')
        # ox.save_graphml(city_graph, city_config['paths']['city_graph'])
        pickle.dump(city_graph, open(city_config['paths']['city_graph'], 'wb'))
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
    assert isinstance(path, str), "Wrong path format"
    assert len(path) > 3, "Incorrect path"
    if path[-3:] == "csv":
        return pd.read_csv(path)
    elif path[-4:] == "xlsx":
        return pd.read_excel(path)
    else:
        raise ValueError("Incorrect path")


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


def initialise_data_simulation(
        simulation_path: str
) -> dict:
    """ Load dota required for the simulation """
    simulation_config = load_config(simulation_path, None)
    logger = initialise_logger("INFO")
    requests = load_any_excel(simulation_config["requests"])
    vehicles = load_any_excel(simulation_config["vehicles"])
    city_config = load_config(simulation_config["city_config"], logger)
    behavioural_config = load_config(simulation_config["behavioural_config"], logger)
    fare_config = load_config(simulation_config["fares_config"], logger)
    skim = load_skim(city_config, logger)
    return {
        "simulation_config": simulation_config,
        "logger": logger,
        "requests": requests,
        "vehicles": vehicles,
        "city_config": city_config,
        "behavioural_config": behavioural_config,
        "fare_config": fare_config,
        "skim": skim
    }


def sort_events_chronologically(
        requests: pd.DataFrame,
        vehicles: pd.DataFrame
) -> list:
    """
    Sort all events (added and removed vehicles)
    :param requests: requests Excel file loaded initially
    :param vehicles: vehicles Excel file loaded initially
    @type vehicles: pd.Dataframe
    @type requests: pd.Dataframe
    @return list of results
    """
    requests = requests[['id', 'origin', 'destination', 'request_time', 'type', 'operator']]
    vehicles = vehicles[['id', 'origin', 'start_time', 'end_time',
                         'type', 'capacity', 'speed', 'operator']]
    r_t = [(str_to_datetime(req['request_time']), 'request', req) for num, req in requests.iterrows()]
    v_st = [(str_to_datetime(veh['start_time']), 'new_vehicle', veh) for num, veh in vehicles.iterrows()]
    return sorted(r_t + v_st, key=lambda x: (x[0], x[1]))


def homogeneous_behaviours(
        initial_configuration: dict,
        requests: pd.DataFrame
) -> dict:
    """
    Create the same behavioural preferences for all travellers
    @param initial_configuration: the configuration to be applied for all travellers
    @param requests: dataframe with all travel requests
    @return: dictionary with the individual preferences
    """
    output = {}
    ids = list(requests['id'])

    for pax_id in ids:
        output[pax_id] = initial_configuration

    return output


def compute_distance(
        list_of_points: list,
        skim: dict
) -> float:
    """ Compute distance between points in the city """
    assert len(list_of_points) >= 2
    if len(list_of_points) == 2:
        if list_of_points[0] == list_of_points[1]:
            return 0
        return skim["skim_matrix"].loc[list_of_points[1], list_of_points[0]]
    dist = 0
    current_node = list_of_points[0]
    for node in list_of_points[1:]:
        if node == current_node:
            continue
        dist += skim["skim_matrix"].loc[node, current_node]
        current_node = node
    return dist


def difference_times(time1, time2) -> int:
    """ Calculate difference between times """
    def amend_time_type(time):
        if isinstance(time, str):
            return dt.strptime(time, '%Y-%m-%d %H:%M:%S')
        return time

    time1 = amend_time_type(time1)
    time2 = amend_time_type(time2)
    return int((time1 - time2).total_seconds())


def compute_path(
        list_of_points: list,
        skim: dict
) -> list:
    """ Calculate the shortest path between two city points """
    assert len(list_of_points) >= 2
    if skim["type"] == "graph":
        current_node = list_of_points[0]
        path = [current_node]
        for node in list_of_points[1:]:
            path += nx.dijkstra_path(
                G=skim["city_graph"],
                source=current_node,
                target=node,
                weight='length'
            )[1:]
            current_node = node
    else:
        raise NotImplementedError("Currently not implemented")

    return path


def post_hoc_analysis(
        vehicles: list,
        rides: list,
        travellers: dict,
        config: dict,
        skim: dict,
        logger: logging.Logger or None = None
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

    def create_event_list(vehicles_rides, is_vehicle=False):
        """ Create a list of events from the ride or vehicle object """
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

    def format_and_save_event_list(event_list, name, is_vehicle=False):
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

    veh_events = create_event_list(vehicles, True)
    ride_events = create_event_list(rides)

    folder_creator(config["output_path"], logger)
    folder_creator(config["output_path"] + str(date.today()), logger)

    format_and_save_event_list(veh_events, 'vehicle', True)
    format_and_save_event_list(ride_events, 'ride')

    with open(config["output_path"] + str(date.today()) + '/traveller_results.txt',
              'w', encoding='utf-8') as file:
        req_length = 0
        actual_length = 0
        file.write("PAX ID".ljust(10))
        file.write(" || REQUEST LENGTH || TRIP LENGTH \n")
        for pax_id, pax in travellers.items():
            file.write(str(pax_id).ljust(10) + " || ")
            file.write(str(round(pax.request_details.trip_length)).ljust(14) + " || ")
            req_length += round(pax.request_details.trip_length)
            for trip_name, trip_len in pax.distance_travelled.items():
                file.write(f"{trip_name}: {round(trip_len)} |")
                actual_length += trip_len
            file.write("\n")
        file.write("OVERALL".ljust(10) + " || " + str(round(req_length)).ljust(14))
        file.write(" || " + str(round(actual_length)))

    # Utility analysis
    with open(config["output_path"] + str(date.today()) + '/utility_results.txt',
              'w', encoding='utf-8') as file:
        file.write("PAX ID".ljust(10))
        file.write(" || UTILITIES \n")
        for pax_id, pax in travellers.items():
            file.write(str(pax_id).ljust(10) + " || ")
            for ut_name, ut_val in pax.utilities.items():
                file.write(f"{ut_name}: {ut_val} |")
            file.write("\n")

    # Global perspective analysis
    # Mileage
    total_vehicle_mileage = round(sum(_v.mileage for _v in vehicles), 1)
    rides_mileage = 0
    for ride in rides:
        nodes_visited = []
        for event in ride.events:
            if event[2] == 'o' or event[2] == 'd':
                nodes_visited.append(event[1])
        rides_mileage += compute_distance(nodes_visited, skim)

    traveller_request_distance = 0
    for pax in travellers.values():
        traveller_request_distance += pax.request_details.trip_length

    # profits
    revenue = 0
    costs = 0
    for ride in rides:
        revenue += ride.profitability.revenue
        costs += ride.profitability.cost

    rides_mileage = round(rides_mileage, 1)
    traveller_request_distance = round(traveller_request_distance, 1)
    revenue = round(revenue, 3)
    costs = round(costs, 3)

    with open(config["output_path"] + str(date.today()) + '/general_results.txt',
              'w', encoding='utf-8') as file:
        file.write("Total vehicle mileage: ".ljust(25) +
                   str(total_vehicle_mileage) + '\n')
        file.write("Total rides mileage: ".ljust(25) +
                   str(rides_mileage) + '\n')
        file.write("Total requests mileage: ".ljust(25) +
                   str(traveller_request_distance) + '\n')
        file.write("Mileage reduction (m): ".ljust(25) +
                   str(round(traveller_request_distance - rides_mileage, 1)) + '\n')
        file.write("Mileage reduction (%): ".ljust(25) +
                   str(round(100*(traveller_request_distance - rides_mileage)
                             / traveller_request_distance, 2)) + '\n')
        file.write("Total profits: ".ljust(25) + str(revenue) + '\n')
        file.write("Total costs: ".ljust(25) + str(costs))

    logger.error("Post-hoc analysis finished, results saved")
