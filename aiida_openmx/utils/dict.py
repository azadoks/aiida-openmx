# -*- coding: utf-8 -*-
"""Dictionary utilities."""

from collections import Counter

from aiida.common import exceptions


def lowercase_dict_keys(dictionary, dict_name):
    """Convert the keys of a dictionary to lowercase and check for case-insensitive duplicates.

    :param dictionary: dict to transform
    :param dict_name: name of `dictionary` for error messages
    :returns: `dictionary` with all keys lowercase
    """
    return case_transform_dict_keys(dictionary, dict_name, 'lowercase_dict_keys', str.lower)


def uppercase_dict_keys(dictionary, dict_name):
    """Convert the keys of a dictionary to uppercase and check for case-insensitive duplicates.

    :param dictionary: dict to transform
    :param dict_name: name of `dictionary` for error messages
    :returns: `dictionary` with all keys uppercase
    """
    return case_transform_dict_keys(dictionary, dict_name, 'uppercase_dict_keys', str.upper)


def case_transform_dict_keys(dictionary, dict_name, func_name, transform):
    """Transform the keys of a dictionary and check for transformation-insensitive duplicates.

    :param dictionary: dict to transform
    :param func_name: name of the transformation function used for error messages
    :param transform: transformation function
    :returns: dictionary where keys have been converted to strings and transformed
    :raises: InputValidationError if case-insensitve comparison leads to duplicate keys
    """
    if not isinstance(dictionary, dict):
        raise TypeError(f'{func_name} accepts only dictionaries as argument, got {type(dictionary)}')
    new_dict = dict((transform(str(k)), v) for k, v in dictionary.items())
    if len(new_dict) != len(dictionary):
        num_items = Counter(transform(str(k)) for k in dictionary.keys())
        double_keys = ','.join([k for k, v in num_items if v > 1])
        raise exceptions.InputValidationError(
            "Inside the dictionary '{}' there are the following keys that "
            'are repeated more than once when compared case-insensitively: {}.'
            'This is not allowed.'.format(dict_name, double_keys)
        )
    return new_dict


def uppercase_dict_values(dictionary):
    """Convert the values of a dictionary to uppercase.

    :param dictionary: dict to transform
    :returns: `dictionary` with all string values uppercase
    """
    return case_transform_dict_values(dictionary, 'uppercase_dict_values', str.upper)


def lowercase_dict_values(dictionary):
    """Convert the values of a dictionary to lowercase.

    :param dictionary: dict to transform
    :returns: `dictionary` with all string values lowercase
    """
    return case_transform_dict_values(dictionary, 'lowercase_dict_values', str.lower)


def case_transform_dict_values(dictionary, func_name, transform):
    """Transform the string-type values of a dictionary.

    :param dictionary: dict to transform
    :param func_name: name of the transformation function used for error messages
    :param transform: transformation function
    :returns: dictionary where string values have been transformed
    """
    if not isinstance(dictionary, dict):
        raise TypeError(f'{func_name} accepts only dictionaries as argument, got {type(dictionary)}')
    new_dict = {}
    for k, v in dictionary.items():
        if isinstance(v, str):
            new_dict[k] = transform(v)
        else:
            new_dict[k] = v
    return new_dict
