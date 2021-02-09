"""Dictionary utilities."""

from collections import Counter

from aiida.common import exceptions

def _lowercase_dict(dictionary, dict_name):
    """Convert the keys of a dictionary to lowercase and check for case-insensitive duplicates."""
    return _case_transform_dict(dictionary, dict_name, '_lowercase_dict', str.lower)


def _uppercase_dict(dictionary, dict_name):
    """Convert the keys of a dictionary to uppercase and check for case-insensitive duplicates."""
    return _case_transform_dict(dictionary, dict_name, '_uppercase_dict', str.upper)


def _case_transform_dict(dictionary, dict_name, func_name, transform):
    """Transform the keys of a dictionary and check for transformation-insensitive duplicates."""
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