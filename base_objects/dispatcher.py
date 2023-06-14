"""
Class of a third party assigning vehicles to requests
"""
import utils.common as utc


class Dispatcher:
    """
    Dispatcher with the modular build
    """
    def __init__(self,
                dispatcher_id: float,
                fares: dict,
                fleet: dict
                ):
        self.dispatcher_id = dispatcher_id
        self.fares = fares
        self.fleet = fleet

    def find_vehicle(self, node, type, skim):
        dist = (1e6, None)
        for veh in self.fleet[type]:
            if veh.available:
                dist_new = utc.compute_distance([node, veh.Positioning.current_position], skim)
                if dist[0] > dist_new:
                    dist = (dist_new, veh.vehicle_id)



