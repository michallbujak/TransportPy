from itertools import permutations
import time
from collections import Counter


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
        ods: list,
        max_trip_length: float,
        execution_time: bool = True)\
-> list:
    """
    Function to create possible combination of sequence of origins and destinations,
     where no destination proceeds corresponding origin
    :param ods: list of labeled origins and destinations tuples (node, 'o', traveller)
    :param max_trip_length: maximal admissible trip length
    :param execution_time: monitor execution time
    :return: admissible combinations
    """
    if execution_time:
        start_time = time.time()

    ods_dict = {(od, pax): (node, od, pax) for node, od, pax in ods}
    ods_mini = [(od, pax) for node, od, pax in ods]

    seq_paxes = [t for n, o, t in ods]
    unique = [k for k, v in Counter(seq_paxes).items() if v == 1]

    combinations = set(permutations(seq_paxes))

    for comb in combinations:
        out = []
        for el in comb:
            if