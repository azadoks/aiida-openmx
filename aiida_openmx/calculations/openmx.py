"""`CalcJob` for OpenMX."""

import copy
import json
import os

import numpy as np
from aiida import orm
from aiida.common import datastructures, exceptions, folders
from aiida.engine import CalcJob
from aiida_pseudo.data.pseudo import VpsData

from ..utils._dict import _uppercase_dict
from ..utils._input import (_BLOCK_PARAMETERS, _FORMAT_TYPE_MAPPING,
                            _RESERVED_KEYWORDS, _get_atoms_spec_and_coords,
                            _get_def_atomic_species, _get_xc_type,
                            validate_parameters)
from ..utils._parameters import PARAMETERS, RESERVED_KEYWORDS


class OpenmxCalculation(CalcJob):
    """`CalcJob` for OpenMX."""

    _DATA_PATH = './'
    _PSEUDO_SUBFOLDER = _DATA_PATH + 'VPS/'
    _ORBITAL_SUBFOLDER = _DATA_PATH + 'PAO/'
    _SYSTEM_NAME = 'aiida'
    _INPUT_SCHEMA = 'openmx-input-schema.json'

    _RETRIEVE_LIST = []

    _DEFAULT_INPUT_FILE = 'aiida.in'
    _DEFAULT_OUTPUT_FILE = 'aiida.out'
    _DEFAULT_PARSER_NAME = 'openmx.openmx'

    @classmethod
    def define(cls, spec):
        """Define the inputs and outputs of the Calculation."""
        # yapf: disable
        super(OpenmxCalculation, cls).define(spec)

        ## Inputs
        # Metadata
        spec.input('metadata.options.input_filename', valid_type=str, default=cls._DEFAULT_INPUT_FILE)
        spec.input('metadata.options.output_filename', valid_type=str, default=cls._DEFAULT_OUTPUT_FILE)
        spec.input('metadata.options.parser_name', valid_type=str, default=cls._DEFAULT_PARSER_NAME)
        spec.input('metadata.options.withmpi', valid_type=bool, default=True)
        spec.input('metadata.options.resources', valid_type=dict,
            default={'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        # Pure inputs
        spec.input('structure', valid_type=orm.StructureData,
            help='The input structure.')
        spec.input('kpoints', valid_type=orm.KpointsData,
            help='The input k-point mesh or path.')
        spec.input('parameters', valid_type=orm.Dict,
            help='The input parameters that are to be used to construct the input file.')
        spec.input('settings', valid_type=orm.Dict, required=False,
            help='Optional parameters to affect the way the calculation job and the parsing are performed.')
        # Input namespaces
        spec.input_namespace('pseudos', valid_type=VpsData, dynamic=True,
            help='A mapping of `VpsData` nodes onto the kind name to which they should apply.')
        spec.input_namespace('basis_set', valid_type=orm.Str, dynamic=True,
            help='A mapping of PAO file names onto the kind name to which they should apply.')

        ## Outputs
        spec.output('output_parameters', valid_type=orm.Dict,
            help='The `output_parameters` output node of the successful calculation.')
        spec.outputs('output_structure', valid_type=orm.StructureData,
            help='The `output_structure` output node of the successful calculation if present.')
        spec.output('output_trajectory', valid_type=orm.Dict, required=False,
            help='The `output_trajectory` output node of the successful calculation if present.')
        spec.output('output_band', valid_type=orm.BandsData, required=False,
            help='The `output_band` output node of the successful calculation if present.')

        ## Errors
        # Unrecoverable errors: required retrieve files could not be read, parsed, or are otherwise incomplete
        # Significant errors: calculation can be used to restart
        #  yapf: enable

    def prepare_for_submission(self, folder: folders.Folder):
        """
        Create input files from the input nodes passed to this instance of the `CalcJob`.

        :param folder: an `aiida.common.folders.Folder` to temporarily write files on disk
        :return: `aiida.common.datastructures.CalcInfo` instance
        """
        # To be filled out below
        local_copy_list = []
        remote_copy_list = []
        remote_symlink_list = []

        # Create the subfolder that will contain the pseudopotentials
        folder.get_subfolder(self._PSEUDO_SUBFOLDER, create=True)

        # Get an uppercase-key-only version of the settings dictionary (also check for case-insensitive duplicates)
        if 'settings' in self.inputs:
            settings = _uppercase_dict(self.inputs.settings.get_dict(),
                                       dict_name='settings')
        else:
            settings = {}

        # Package arguments for `_generate_inputdata`
        arguments = [
            self.inputs.structure,
            self.inputs.parameters,
            self.inputs.metadata.get_dict(),
            self.inputs.pseudos,
            self.inputs.orbitals,
        ]

        # Validate inputs
        self._validate_inputs(*arguments)

        # Get input file contents and lists of the pseudopotential and orbital files which need to be copied
        input_file_content, local_copy_pseudo_list = self._generate_input_data(*arguments)
        local_copy_list += local_copy_pseudo_list

        # Write input file
        with folder.open(self.metadata.options.input_filename, 'w') as handle:
            handle.write(input_file_content)

        # Fill out the `CodeInfo`
        codeinfo = datastructures.CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        cmdline_params = settings.pop('CMDLINE', [])
        codeinfo.cmdline_params = ([self.metadata.options.input_filename] +
                                   list(cmdline_params))
        codeinfo.stdout_name = self.metadata.options.output_filename

        # Fill out the `CalcInfo`
        calcinfo = datastructures.CalcInfo()
        calcinfo.uuid = str(self.uuid)
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.remote_symlink_list = remote_symlink_list
        calcinfo.retrieve_list = []
        calcinfo.retrieve_list.append(self.metadata.options.output_filename)
        calcinfo.retrieve_list += self._RETRIEVE_LIST
        calcinfo.retrieve_list += settings.pop('ADDITIONAL_RETRIEVE_LIST', [])

        # TODO: pop parser settings and report remaining unknown settings

        return calcinfo

    def _validate_inputs(structure, kpoints, parameters, metadata, pseudos, orbitals):
        # Check that a pseudopotential is specified for each kind present in the `StructureData`
        kinds = [kind.name for kind in structure.kinds]
        if set(kinds) != set(pseudos.keys()):
            raise exceptions.InputValidationError(
                'Mismatch between the defined pseudos and the list of kinds of the structure.\n'
                'Pseudos: {};\nKinds: {}'.format(', '.join(
                    list(pseudos.keys()))), ', '.join(list(kinds)))
        
        # Check that all pseudopotentials have the same exchange-correlation type
        xc_set = {pseudo.xc_type for pseudo in pseudos.values()}
        if len(xc_set) != 1:
            raise exceptions.InputValidationError(
                f'The provided pseudos have inconsistent exchange-correlation types: {xc_set}.'
            )

        # Check that an orbital basis is specified for each kind present in the `StructureData`
        if set(kinds) != set(orbitals.keys()):
            raise exceptions.InputValidationError(
                'Mismatch between the defined orbitals and the list of kinds of the structure.\n'
                'Orbitals: {};\nKinds: {}'.format(', '.join(
                    list(orbitals.keys()))),
                ', '.join(list(kinds)))

        # Check that corresponding orbital bases and pseudopotentials have the same valence
        inconsistent_valence = {}
        for kind in set(kinds):
            if pseudos[kind].valence != orbitals[kind].valence:
                inconsistent_valence[kind] = (pseudos[kind].valence, orbitals[kind].valence)
        if inconsistent_valence:
            raise exceptions.InputValidationError(
                f'Mismatch between the pseudopotential and orbital valences: {inconsistent_valence}.'
            )

        # Check that no reserved parameter keywords are provided
        provided_reserved_kws = []
        for kw in parameters:
            if kw in _RESERVED_KEYWORDS:
                provided_reserved_kws.append(kw)
        if provided_reserved_kws:
            msg = f'The reserved keywords {", ".join(provided_reserved_kws)} should not be provided.'
            raise exceptions.InputValidationError(msg)

        # Check that the KpointsData has a kpoints_mesh; explicit k-points are not yet supported
        try:
            kpoints.get_kpoints_mesh()
        except AttributeError:
            raise exceptions.InputValidationError(
                'Explicit k-points are not yet supported. Instead, set a k-points mesh using '
                'KpointsData.set_kpoints_mesh().'
            )

    def _generate_input_data(cls, structure, kpoints, parameters, metadata, pseudos, orbitals):
        parameters = copy.deepcopy(parameters)

        # Fill out parameters
        parameters['System.Name'] = cls._SYSTEM_NAME
        parameters['DATA.PATH'] = cls._DATA_PATH
        parameters['level.of.stdout'] = 3
        parameters['level.of.fileout'] = 3
        parameters['Species.Number'] = len(structure.kinds)
        parameters['Definition.of.Atomic.Species'] = _get_def_atomic_species(structure, pseudos, orbitals)
        parameters['Atoms.Number'] = len(structure.sites)
        parameters['Atoms.SpeciesAndCoordinates'] = _get_atoms_spec_and_coords(structure, pseudos, orbitals)
        parameters['Atoms.UnitVectors'] = structure.cell
        parameters['scf.XcType'] = _get_xc_type(pseudos)
        parameters['scf.Kgrid'] = kpoints.get_kpoints_mesh()

        # Validate parameters using jsonschema
        with open(f'../schema/{cls._INPUT_SCHEMA}', 'r') as stream:
            schema = json.load(stream)
        validate_parameters(schema, parameters)

        # Write parameters to file contents string
        input_file_content = ''
        for kw, value in parameters:
            if kw in _BLOCK_PARAMETERS:
                param_content = _BLOCK_PARAMETERS[kw](value)
            else:
                value_format = _FORMAT_TYPE_MAPPING(schema[kw]['type'])
                param_content = ' '.join([kw, value_format.format(value)]) + '\n'
            input_file_content += param_content

        # List files
        pseudo_file_list = [
            (pseudo.uuid, pseudo.filename, os.path.join(cls._PSEUDO_SUBFOLDER, pseudo.filename))
                for pseudo in pseudos.values()
        ]
        orbital_file_list = [
            (orbital.uuid, orbital.filename, os.path.join(cls._ORBITAL_SUBFOLDER, orbital.filename))
                for orbital in orbitals.values()
        ]

        return input_file_content, pseudo_file_list, orbital_file_list
