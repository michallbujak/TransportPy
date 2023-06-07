""" Tools for calculations associated with pooled rides """

import itertools

from objects.dispatcher import Dispatcher
from objects.traveller import Traveller


def admissible_future_combinations(ods):
    """
    Function to create possible combination of sequence of origins and destinations,
     where no destination proceeds corresponding origin
    :param ods: list of labeled origins and destinations
    :return: admissible combinations
    """
    all_combinations = itertools.permutations(ods)
    admissible_combinations = []

    def check_combination(comb):
        # if comb[-2][0] == 'o':
        #     return False
        for num, element in enumerate(comb):
            if element[0] == 'd':
                if element[1] in [t[1] for t in comb[num + 1:]]:
                    return False
        else:
            return True

    for combination in all_combinations:
        if check_combination(combination):
            admissible_combinations.append(combination)

    return admissible_combinations


def pooled_partial_utility_formula(
        distance: float,
        dispatcher: Dispatcher,
        no_travellers: int,
        traveller: Traveller,
) -> float:
    """
    Function designed to calculate utility for a specified traveller in a shared ride
    on the given portion of the road!
    :param distance: distance travelled
    :param dispatcher: Dispatcher class object
    :param no_travellers: number of travellers
    :param traveller: Traveller object
    :return:
    """
    return -distance * dispatcher.city_properties.speed * \
        dispatcher.pricing.pool_prices[no_travellers if no_travellers < 4 else 4] - \
        traveller.behavioural_details.vot * \
        traveller.behavioural_details.pfs[no_travellers if no_travellers < 4 else 4] * \
        distance / dispatcher.city_properties.speed


def pooled_additional_utility(
        traveller: Traveller,
        pickup_delay: float
) -> float:
    return -pickup_delay * traveller.behavioural_details.pickup_delay_sensitivity * \
        traveller.behavioural_details.vot - \
        traveller.behavioural_details.pfs_const
