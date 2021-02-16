# -*- coding: utf-8 -*-
"""Input utilities and constants."""

from os.path import splitext
import functools

import jsonschema
import numpy as np

_RESERVED_KEYWORDS = [
    'System_CurrentDirectory', 'System_Name', 'DATA_PATH', 'level_of_stdout', 'level_of_fileout', 'Species_Number',
    'Definition_of_Atomic_Species', 'scf_XcType', 'scf_Kgrid', 'Atoms_Number', 'Atoms_SpeciesAndCoordinates_Unit',
    'Atoms_SpeciesAndCoordinates', 'Atoms_Unitvectors_Unit', 'Atoms_Unitvectors', 'Atoms_NetCharge', 'scf_restart',
    'scf_restart_filename', 'Dos_fileout', 'DosGauss_fileout', 'FermiSurfer_fileout', 'HS_fileout'
]

_FORMAT_TYPE_MAPPING = {'number': '{:0.12f}', 'integer': '{:d}', 'string': '{}'}

_BLOCK_PARAMETER_WRITERS = {
    'Atoms_SpeciesAndCoordinates': _write_atoms_spec_and_coords,
    'Atoms_Unitvectors': functools.partial(_write_array_block, item_type='number', tag='Atoms.Unitvectors'),
    'Definition_of_Atomic_Species': _write_def_atomic_species,
    'Band_kpath': _write_band_kpath,
    'Band_kpath_UnitCell': functools.partial(_write_array_block, item_type='number', tag='Band.kpath.UnitCell')
}


def _get_is_int(validator):
    """Create a integer type checker with numpy support for the given validator."""

    # pylint: disable=unused-argument
    def is_int(checker, instance):
        return (
            validator.TYPE_CHECKER.is_type(instance, 'integer') or
            isinstance(instance, (np.int32, np.int64, np.int128))
        )

    return is_int


def _get_is_number(validator):
    """Create a number type checker with numpy support for the given validator."""

    # pylint: disable=unused-argument,consider-merging-isinstance
    def is_number(checker, instance):
        return (
            validator.TYPE_CHECKER.is_type(instance, 'number') or
            isinstance(instance, (np.int16, np.int32, np.int64, np.int128)) or
            isinstance(instance, (np.float16, np.float32, np.float64, np.float128)) or
            isinstance(instance, (np.complex64, np.complex128, np.complex256))
        )

    return is_number


def _get_is_array(validator):
    """Create an array type checker with numpy support for the given validator."""

    # pylint: disable=unused-argument
    def is_array(checker, instance):
        return (validator.TYPE_CHECKER.is_type(instance, 'array') or isinstance(instance, (tuple, np.ndarray)))

    return is_array


def _get_validator(schema):
    """Create a custom validator with numpy support for the given schema."""
    validator = jsonschema.validators.validator_for(schema)
    type_checker = validator.TYPE_CHECKER
    type_checker = type_checker.redefine('integer', _get_is_int(validator))
    type_checker = type_checker.redefine('number', _get_is_number(validator))
    type_checker = type_checker.redefine('array', _get_is_array(validator))
    OpenmxValidator = jsonschema.validators.extend(validator, type_checker=type_checker)
    return OpenmxValidator(schema)


def validate_parameters(schema, parameters):
    """Validate OpenMX input parameters using jsonschema.

    The jsonschema Validator is retrieved for the appropriate schema version, and its TypeChecker
    is extended to support Numpy int, float, complex, and array types.

    :param schema: contents of the JSON schema file
    :param parameters: OpenMX input parameters
    :returns: None if validation is successful
    """
    validator = _get_validator(schema)
    return validator.validate(parameters)


def _get_xc_type(pseudos):
    """Get the `scf_XcType` parameter from a set of pseudos."""
    xc_set = {pseudo.xc_type for pseudo in pseudos.values()}
    if len(xc_set) != 1:
        msg = 'The provided pseudos have inconsistent exchange-correlation type.'
        raise ValueError(msg)
    return xc_set.pop()


def _get_def_atomic_species(structure, pseudos, orbitals, orbital_configurations):
    """Construct the `Definition.of.Atomic.Species` parameter dictionary."""
    def_atomic_species = {}
    for kind in structure.kinds:
        def_atomic_species[kind.name] = {
            'pao': {
                'file_stem': splitext(orbitals[kind.name].filename)[0],
                'orbital_configuration': orbital_configurations.get_array(kind.name)
            },
            'pseudo': splitext(pseudos[kind.name].filename)[0]
        }
    return def_atomic_species


def _get_atoms_spec_and_coords(structure, orbitals):
    """Construct the `Atoms.SpeciesAndCoordinates` parameter dictionary."""
    atoms_spec_and_coords = []
    for site in structure.sites:
        kind_name = site.kind_name
        valence = orbitals[kind_name].z_valence
        atoms_spec_and_coords.append({
            'specie': kind_name,
            'coords': site.position,
            'up_charge': valence / 2,
            'down_charge': valence / 2
        })
    return atoms_spec_and_coords


def _tag_block(block, tag):
    """Add the open and close tags to an input block."""
    return f'<{tag}\n' + block + f'\n{tag}>\n'


def _write_def_atomic_species(def_atomic_species):
    """Write the `Definition_of_Atomic_Species` input block."""
    ORB_MAP = {0: 's', 1: 'p', 2: 'd', 3: 'f'}
    TAG = 'Definition.of.Atomic.Species'
    lines = []
    for specie, data in def_atomic_species.items():
        orbital_config = ''.join([
            f'{ORB_MAP[i]}{n_orb}' for i, n_orb in enumerate(data['pao']['orbital_configuration']) if n_orb != 0
        ])
        lines.append(f'{specie} {data["pao"]["file_stem"]}-{orbital_config} {data["pseudo"]}')
    block = _tag_block('\n'.join(lines), TAG)
    return block


def _write_atoms_spec_and_coords(atoms_spec_and_coords):
    """Write the `Atoms.SpeciesAndCoordinates` input block."""
    TAG = 'Atoms.SpeciesAndCoordinates'
    lines = []
    for i, data in enumerate(atoms_spec_and_coords):
        index = i + 1
        kind_name = data['specie']
        x, y, z = data['coords']
        up_charge = data['up_charge']
        down_charge = data['down_charge']
        lines.append(f'{index:d} {kind_name} {x:0.12f} {y:0.12f} {z:0.12f} {up_charge:0.6f} {down_charge:0.6f}')
    block = _tag_block('\n'.join(lines), TAG)
    return block


def _write_band_kpath():
    """Write the `Band.kpath` input block."""
    # TAG = 'Band.kpath'


def _write_array_block(array, item_type, tag):
    """Write an array input block.

    :param array: Array data to write
    :param type: JSON schema type of the items of the array
    :returns: OpenMX-formatted array input block
    """
    type_format = _FORMAT_TYPE_MAPPING[item_type]
    lines = []
    for row in array:
        lines.append(' '.join([type_format.format(item) for item in row]))
    block = _tag_block('\n'.join(lines), tag)
    return block


def write_input_file(parameters, schema):
    """Write an OpenMX input file.

    :param parameters: Input parameters
    :param schema: Input parameters schema
    :returns: Input file content
    """
    input_file_content = ''
    for kw, value in parameters.items():
        value_type = schema['properties'][kw]['type']
        kw_str = kw.replace('_', '.')
        # 2D arrays and complex data
        if kw in _BLOCK_PARAMETER_WRITERS:
            param_content = _BLOCK_PARAMETER_WRITERS[kw](value)
        # 1D arrays
        elif value_type == 'array':
            item_type = schema['properties'][kw]['items']['type']
            item_format = _FORMAT_TYPE_MAPPING[item_type]
            param_content = ' '.join([kw_str] + [item_format.format(item) for item in value]) + '\n'
        # Booleans must be -> ON/OFF for OpenMX
        elif value_type == 'boolean':
            param_content = ' '.join([kw_str, 'on' if value else 'off']) + '\n'
        # Scalar values
        else:
            value_format = _FORMAT_TYPE_MAPPING[value_type]
            param_content = ' '.join([kw_str, value_format.format(value)]) + '\n'
        input_file_content += param_content

    return input_file_content
