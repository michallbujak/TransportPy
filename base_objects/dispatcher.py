"""
Class of a third party assigning vehicles to requests
"""


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

