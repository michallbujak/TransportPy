from itertools import permutations
import time


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

    def _permutations(iterable):
        pool = tuple(iterable)
        n = len(pool)
        indices = list(range(n))
        cycles = list(range(n, 0, -1))
        yield tuple(pool[i] for i in indices)
        while n:
            for i in reversed(range(n)):
                cycles[i] -= 1
                if cycles[i] == 0:
                    indices[i:] = indices[i + 1:] + indices[i:i + 1]
                    cycles[i] = n - i
                else:
                    j = cycles[i]
                    indices[i], indices[-j] = indices[-j], indices[i]
                    yield tuple(pool[i] for i in indices[:n])
                    break
            else:
                return

    starting_points = []
    for od in ods_mini:
        if od[0] == 'o':
            starting_points.append(od)
        else:
            if not ('o', od[1]) in ods_mini:
                starting_points.append(od)

    output = []
    for n1, s1 in enumerate(starting_points):
        out1 = [s1]
        starting_points.pop(n1)
        if s1[1] == 'o':
            starting_points.append(starting_points)





