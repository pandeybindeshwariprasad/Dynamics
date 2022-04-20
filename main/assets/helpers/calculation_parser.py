import re
from itertools import chain, zip_longest


def interleave(*iterables):
    """
    Combines two lists of different lengths into a single list and alternates between elements from each list in order.
    So [a,b,c] and [Y,Z] becomes [a,Y,b,Z,c]
    Args:
        *iterables:

    Returns:
        A singular list of two lists interleaved

    """
    sentinel = object()
    z = zip_longest(*iterables, fillvalue=sentinel)
    c = chain.from_iterable(z)
    f = filter(lambda x: x is not sentinel, c)

    return list(f)


def calculate_strings(my_string):
    """
    Takes a mathematical function written as a string and evaluates it
    Args:
        my_string:

    Returns:
        float representing evaluated result of this function
    """

    my_string = re.sub(r'(?<=\d)-', '+-', my_string)
    numbers_list = re.findall(r'-?\(?\d+\.?\d*\)?', my_string)
    operators_list = re.findall(r'[/*+]', my_string)
    while len(numbers_list) <= len(operators_list):
        del(operators_list[-1])

    return eval(''.join(interleave(numbers_list, operators_list)))
