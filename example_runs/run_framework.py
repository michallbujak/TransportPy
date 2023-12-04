import os
from datetime import datetime as dt
from datetime import timedelta as td

import utils.common as utc
from dispatchers.taxidispatcher import TaxiDispatcher
from base_objects.traveller import Traveller
from base_objects.vehicle import Vehicle
from utils.move_vehicles import move_vehicle_ride

os.chdir(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))

# Initialise data, configs and logger
data_bank = utc.initialise_data_simulation(
    "data/configs/simulation_configs/sim_config_NYC.json"
)

# Initialise Operators
dispatchers = {}
for dispatcher_name in data_bank["simulation_config"]["taxi_operators"]:
    dispatchers[dispatcher_name] = TaxiDispatcher(
        dispatcher_id=dispatcher_name,
        fares=data_bank["fare_config"]["fares"][dispatcher_name],
        operating_costs=data_bank["fare_config"]['operating_costs'][dispatcher_name],
        fleet=data_bank["vehicles"].loc[data_bank["vehicles"]['operator'] == dispatcher_name]
    )
# Add here if there are different kinds of operators
# ...

# Prepare individual behavioural preferences
# should be consistent with id from requests
data_bank['behavioural_details'] = utc.homogeneous_behaviours(
    initial_configuration=data_bank["behavioural_config"],
    requests=data_bank["requests"]
)

# Initialise dictionary with travellers
Travellers = {}

# Calculation is performed at each event point
events_sorted = utc.sort_events_chronologically(
    requests=data_bank["requests"],
    vehicles=data_bank["vehicles"]
)

last_event_time: dt = events_sorted[0][0]
# Do while there are events pending
while events_sorted:
    event = events_sorted[0]
    current_time = event[0]
    time_between_events = utc.difference_times(current_time, last_event_time)

    # If the time has passed from the last event
    if time_between_events > 0:
        for _Dispatcher in dispatchers.values():
            for ride_type in _Dispatcher.rides.values():
                for ride in ride_type:
                    if ride.active:
                        _fares = data_bank["fare_config"]["fares"]
                        _op_costs = data_bank["fare_config"]["operating_costs"]
                        move_vehicle_ride(
                            vehicle=ride.serving_vehicle,
                            ride=ride,
                            move_time=time_between_events,
                            skim=data_bank["skim"],
                            logger=data_bank["logger"]
                        )

    # If the event is a new vehicle
    if event[1] == 'new_vehicle':
        v = event[2]
        _Dispatcher = dispatchers[event[2]['operator']]
        _Dispatcher.fleet[v['type']] += [Vehicle(
            vehicle_id=v['id'],
            start_node=v['origin'],
            start_time=utc.str_to_datetime(v['start_time']),
            end_time=utc.str_to_datetime(v['end_time']),
            capacity=v['capacity'],
            vehicle_speed=v['speed']
        )]

    if event[1] == 'request':
        traveller = Traveller(
            request=tuple(event[2]),
            behavioural_details=data_bank["behavioural_details"][event[2]['id']]
        )
        traveller.calculate_trip_length(data_bank["skim"])
        Travellers[event[2]['id']] = traveller
        serving_Dispatcher = dispatchers[event[2]['operator']]

        # Kind of service one shall be offered
        if event[2]['type'] == 'pool':
            pool_potential, taxi_potential = serving_Dispatcher.pool_utility(
                request=event[2],
                traveller=traveller,
                skim=data_bank["skim"],
                logger=data_bank["logger"]
            )

            if pool_potential:
                serving_Dispatcher.assign_pool(
                    possible_assignments=pool_potential,
                    traveller=traveller,
                    skim=data_bank["skim"]
                )

            elif not pool_potential and taxi_potential is not None:
                serving_Dispatcher.assign_taxi(
                    taxi_ride=taxi_potential["taxi_ride"],
                    vehicle=taxi_potential["vehicle"],
                    pickup_delay=taxi_potential['pickup_delay'],
                    utility=taxi_potential["utility"],
                    traveller=taxi_potential["traveller"],
                    profitability=taxi_potential["profitability"],
                    skim=data_bank["skim"],
                    logger=data_bank["logger"]
                )

            elif not pool_potential and taxi_potential is None:
                traveller.service_details.waiting_time += data_bank["simulation_config"]['refresh_density']

                if data_bank['behavioural_details'][traveller.traveller_id]["maximal_waiting"] \
                        < traveller.service_details.waiting_time:
                    traveller.service_details.resigned = True

                delayed_event = (event[0] + td(seconds=data_bank["simulation_config"]['refresh_density']),
                                 event[1], event[2])
                events_sorted.append(delayed_event)
                events_sorted = sorted(events_sorted, key=lambda x: (x[0], x[1]))

        else:
            raise NotImplementedError("Only 'pool' viable here as for now")

    events_sorted.pop(0)

    for _Dispatcher in dispatchers.values():
        for veh_type in _Dispatcher.fleet.values():
            for veh in veh_type:
                if veh.path.end_time <= current_time:
                    veh.available = False

    if len(events_sorted) == 0:
        all_rides = []
        all_vehicles = []
        for _Dispatcher in dispatchers.values():
            for _ride_type in _Dispatcher.rides.keys():
                all_rides += _Dispatcher.rides[_ride_type]
            for _veh_type in _Dispatcher.fleet.keys():
                all_vehicles += _Dispatcher.fleet[_veh_type]

        if not all(not r.active for r in all_rides):
            events_sorted.append((
                current_time + td(seconds=data_bank["simulation_config"]['refresh_density']),
                None,
                None
            ))


utc.post_hoc_analysis(vehicles=all_vehicles,
                      rides=all_rides,
                      travellers=Travellers,
                      config=data_bank["simulation_config"],
                      skim=data_bank["skim"],
                      logger=data_bank["logger"])
