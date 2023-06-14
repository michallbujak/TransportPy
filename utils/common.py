""" Tools used across scripts """
import json
import os

import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx

from datetime import timedelta
from dataclasses import asdict


def load_config(path):
    """
    Load configuration files from .json format
    :param path: path to the configuration file
    :return: configuration dictionary
    """
    print(os.getcwd())
    with open(path, encoding='utf-8') as json_file:
        config = json.load(json_file)
    return config


def distinguish_fleet(vehicles):
    types = np.unique(np.array(vehicles["type"]))
    fleet = dict()
    for t in types:
        fleet[t] = []
        for num, veh in vehicles.loc[vehicles["type"] == t].iterrows():
            fleet[t].append(veh)
    return fleet


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
