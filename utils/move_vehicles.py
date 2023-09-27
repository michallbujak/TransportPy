import logging
from datetime import timedelta

import utils.common as utc

from base_objects.vehicle import Vehicle
from base_objects.ride import Ride


def move_vehicle_ride(vehicle: Vehicle,
                      ride: Ride,
                      move_time: int,
                      skim: dict,
                      **kwargs
                      ) -> None:
    """
    Function which is designed to move the vehicle along request route
    :param vehicle: Vehicle object
    :param ride: Ride object
    :param move_time: time by which the vehicle is moved
    :param skim: dictionary with distances
    :param simulation_config: simulation configuration
    :param logger: logging purposes
    @type vehicle: Vehicle
    @type ride: Ride
    @type move_time: int
    @type skim: dict
    """

    def check_if_event(_r, _v):
        curr_time = _v.path.current_time
        evs = [t for t in _r.destination_points if t[0] == _v.path.current_position]
        for ev in evs:
            traveller = [t for t in _r.travellers if t.traveller_id == ev[2]][0]
            if ev[1] == 'o':
                _v.events.append((_v.path.current_time, _v.path.current_position, 'o', ev[2]))
                try:
                    _r.events += [(_v.path.current_time, _v.path.current_position, 'o', ev[2])]
                except AttributeError:
                    pass
                _v.travellers += [traveller]
                try:
                    utc.log_if_logger(kwargs.get("logger"), 20,
                                         f"{curr_time}: Traveller {ev[2]} joined vehicle {_v}")
                    _v.scheduled_travellers.remove(
                        [t for t in _v.scheduled_travellers if t.traveller_id == ev[2]][0]
                    )
                except AttributeError:
                    pass
            if ev[1] == 'd':
                _r.travellers.remove(traveller)
                _r.events.append((_v.path.current_time, _v.path.current_position, 'd', ev[2]))
                _v.travellers.remove(traveller)
                _v.events.append((_v.path.current_time, _v.path.current_position, 'd', ev[2]))
                utc.log_if_logger(kwargs.get("logger"), 20,
                                     f"{curr_time}: Traveller {traveller} finished trip")

                if kwargs.get('pool_capacity_freed', False):
                    _v.available = True

            if ev[1] == 'a':
                _v.scheduled_travellers += [traveller]
                _v.events.append((_v.path.current_time, _v.path.current_position, 'a', ev[2]))
                _r.events.append((_v.path.current_time, _v.path.current_position, 'a', ev[2]))

            try:
                if ev[1] in ['d', 'o']:
                    for comb in _r.adm_combinations:
                        comb.remove(ev)
            except AttributeError:
                pass

            _r.destination_points.remove(ev)
            _r.past_destination_points.append(ev)

        if len(_r.travellers) == 0:
            _r.active = False

        return _r, _v

    avg_speed = vehicle.vehicle_speed
    time_left = move_time

    while vehicle.path.current_path is not None:
        assert (
                vehicle.path.closest_crossroad is not None
        ), "The path has not been updated, vehicle does not have a path to follow"

        vehicle.path.stationary_position = False

        distance_to_crossroad = utc.compute_distance(
            [vehicle.path.current_position, vehicle.path.current_path[1]], skim
        )
        time_required_to_crossroad = \
            distance_to_crossroad / avg_speed - vehicle.path.time_between_crossroads
        time_required_to_crossroad = int(time_required_to_crossroad)

        if time_left < time_required_to_crossroad:
            # not sufficient time to reach the nearest crossroad
            utc.log_if_logger(kwargs.get("logger"), 10,
                                 f"Vehicle {vehicle}: Insufficient time to reach"
                                 f" crossroad {vehicle.path.current_path[1]}")

            vehicle.path.time_between_crossroads = vehicle.path.time_between_crossroads + time_left
            vehicle.path.to_closest_crossroads = time_required_to_crossroad - vehicle.path.time_between_crossroads
            vehicle.path.current_time = vehicle.path.current_time + timedelta(seconds=time_left)
            ride, vehicle = check_if_event(ride, vehicle)
            break

        # First check if something happens at the initial node
        ride, vehicle = check_if_event(ride, vehicle)

        # sufficient time to reach the nearest crossroad
        utc.log_if_logger(kwargs.get("logger"), 10,
                             f"{vehicle.path.current_time}: Vehicle {vehicle}: Reached"
                             f" crossroad {vehicle.path.current_path[1]}")
        vehicle.mileage += distance_to_crossroad
        time_left -= time_required_to_crossroad
        vehicle.path.current_time = vehicle.path.current_time + timedelta(
            seconds=time_required_to_crossroad
        )
        vehicle.path.current_position = vehicle.path.current_path[1]
        vehicle.path.current_path = vehicle.path.current_path[1:]
        vehicle.path.time_between_crossroads = 0
        vehicle.path.to_closest_crossroads = None

        # Update traveller detailed movement
        for trav in vehicle.travellers:
            if ride.ride_type in trav.distance_travelled.keys():
                trav.distance_travelled[ride.ride_type] += distance_to_crossroad
            else:
                trav.distance_travelled[ride.ride_type] = distance_to_crossroad

        ride, vehicle = check_if_event(ride, vehicle)

        if len(vehicle.path.current_path) == 1:
            vehicle.path.current_path = None
            vehicle.path.closest_crossroad = None
            vehicle.path.stationary_position = True
            vehicle.available = True
            ride.active = False
            utc.log_if_logger(kwargs.get("logger"), 30,
                                 f"{vehicle.path.current_time}: "
                                 f"Ride {ride} finished with vehicle {vehicle}")

        else:
            vehicle.path.closest_crossroad = vehicle.path.current_path[1]

        # Check from the request perspective whether something happens at those nodes
        ride, vehicle = check_if_event(ride, vehicle)

    if vehicle.path.current_time >= vehicle.path.end_time:
        vehicle.available = False

    utc.log_if_logger(kwargs.get("logger"), 10,
                         f"{vehicle.path.current_time}:"
                         f" Vehicle {vehicle} moved by {move_time}s")

    return None
