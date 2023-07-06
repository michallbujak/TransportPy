import itertools


def admissible_future_combinations(ods):
    """
    Function to create possible combination of sequence of origins and destinations,
     where no destination proceeds corresponding origin
    :param ods: list of labeled origins and destinations tuples (node, 'o', traveller)
    :return: admissible combinations
    """
    all_combinations = itertools.permutations(ods)
    admissible_combinations = []

    def check_combination(comb):
        if comb[-2][0] == 'o':
            return False
        for num, element in enumerate(comb):
            if element[1] == 'd':
                if element[2] in [t[2] for t in comb[num + 1:]]:
                    return False
        return True

    for combination in all_combinations:
        if check_combination(combination):
            admissible_combinations.append(list(combination))

    return admissible_combinations
