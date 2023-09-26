from itertools import permutations
import time
from collections import Counter
from rides.pool_ride import PoolRide
from utils.common import compute_distance as dist


# def admissible_future_combinations(
#         ods: list,
#         execution_time: bool = True)\
# -> list:
#     """
#     Function to create possible combination of sequence of origins and destinations,
#      where no destination proceeds corresponding origin
#     :param ods: list of labeled origins and destinations tuples (node, 'o', traveller)
#     :param execution_time: monitor execution time
#     :return: admissible combinations
#     """
#     start_time = time.time()
#     ods_dict = {(od, pax): (node, od, pax) for node, od, pax in ods}
#     ods_mini = [(od, pax) for node, od, pax in ods]
#
#     def check_combination(comb):
#         if comb[-2][0] == 'o':
#             return False
#         comb_copy = list(comb).copy()
#         while comb_copy:
#             if comb_copy[0][0] == 'd':
#                 return False
#             else:
#                 comb_copy.remove(('d', comb_copy[0][1]))
#                 comb_copy.remove(('o', comb_copy[0][1]))
#         return True
#
#     out = list(filter(lambda x: check_combination(x), permutations(ods_mini)))
#     print("--- %s seconds ---" % (time.time() - start_time))
#
#     return [[ods_dict[e] for e in c] for c in out]

def admissible_future_combinations(
        new_locations: list,
        ride: PoolRide,
        max_trip_length: float,
        max_distance_pickup: float,
        skim: dict,
        execution_time: bool = True
) -> list:
    """
    Look at the admissible combinations for the ride.
    Check where new origin and destination can be inserted,
    such that the trip length is no greater than sum
    of length the ongoing trip + length of the new trip
    @param new_locations: [(node, 'o', traveller), (node, 'd', traveller)]
    @param ride:
    @param max_trip_length:
    @param max_distance_pickup:
    @param skim:
    @param execution_time:
    @return:
    """
    if execution_time:
        start_time = time.time()

    all_combinations = ride.adm_combinations
    out = []

    for combination in all_combinations:
        for i in range(len(combination) - 1):
            c1 = combination.copy()
            c1.insert(i, new_locations[0])

            if dist([t[0] for t in c1[:i]], skim) > max_distance_pickup:
                continue

            for j in range(i+1, len(combination)+1):
                c2 = c1.copy()
                c2.insert(j, new_locations[1])

                if dist([t[0] for t in c2], skim) < max_trip_length:
                    out.append(c2)

    if execution_time:
        print(f"--- Combinations found in {time.time() - start_time} seconds ---")

    return out
