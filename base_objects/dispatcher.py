"""
Class of a third party assigning vehicles to requests
"""


class Dispatcher:
    """
    Dispatcher with the modular build
    """
    def __int__(self,
                dispatcher_id: float,
                pricing: dict,
                fleet: dict
                ):
        self.dispatcher_id = dispatcher_id
        self.pricing = pricing
        self.fleet = fleet

