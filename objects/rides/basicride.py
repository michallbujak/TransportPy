"""
Basic ride time, so any form of transport.
All for of transport shall inherit from the class
"""

from datetime import datetime


class Ride:
    """
    Basic ride object. Parent to all ride classes.
    """
    def __init__(self,
                 travellers: list,
                 start_time: datetime,
                 utilities: dict or None = None,
                 profitability: float or None = None,
                 vehicle: float or None = None
                 ):
        self.travellers = travellers
        self.start_time = start_time
        self.utilities = utilities
        self.profitability = profitability
        self.vehicle = vehicle

