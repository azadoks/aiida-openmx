# -*- coding: utf-8 -*-
"""`CalcJob` for OpenMX `openmx`."""

import copy
import json
import os

from aiida import orm
from aiida.common import datastructures, exceptions, folders
from aiida.common.lang import classproperty
from aiida.engine import CalcJob
from aiida_pseudo.data.pseudo import VpsData
from aiida_pseudo.data.pseudo import PaoData

from aiida_openmx.utils.dict import uppercase_dict_keys, lowercase_dict_values
from aiida_openmx.calculations.helpers.openmx import (
    _RESERVED_KEYWORDS, _get_atoms_spec_and_coords, _get_def_atomic_species, _get_xc_type, write_input_file,
    validate_parameters
)

_DIR = os.path.dirname(os.path.abspath(__file__))


class OpenmxCalculation(CalcJob):
    """`CalcJob` for OpenMX `openmx`."""

    _DATA_PATH = './'
    _PSEUDO_SUBFOLDER = _DATA_PATH + 'VPS/'
    _ORBITAL_SUBFOLDER = _DATA_PATH + 'PAO/'
    _SYSTEM_NAME = 'aiida'
    _INPUT_FILE = _SYSTEM_NAME + '.in'
    _OUTPUT_FILE = _SYSTEM_NAME + '.out'
    _INPUT_SCHEMA = os.path.join(_DIR, 'helpers/openmx-input-schema.json')

    _DATAFILE_DOS_VAL_FILE = _SYSTEM_NAME + '.Dos.val'
    _DATAFILE_DOS_VEC_FILE = _SYSTEM_NAME + '.Dos.vec'
    _DATAFILE_BAND_FILE = _SYSTEM_NAME + '.Band'
    _DATAFILE_XYZ_FILE = _SYSTEM_NAME + '.xyz'
    _DATAFILE_BULK_XYZ_FILE = _SYSTEM_NAME + '.bulk.xyz'
    _DATAFILE_MD_FILE = _SYSTEM_NAME + '.md'
    _DATAFILE_MD2_FILE = _SYSTEM_NAME + '.md2'
    _DATAFILE_CIF_FILE = _SYSTEM_NAME + '.cif'
    _DATAFILE_ENE_FILE = _SYSTEM_NAME + '.ene'

    _DEFAULT_PARSER_NAME = 'openmx.openmx'

    @classproperty
    def system_name(cls):
        """Return the system name."""
        # pylint: disable=no-self-argument
        return cls._SYSTEM_NAME

    @classproperty
    def output_filename(cls):
        """Return the stdout output filename."""
        # pylint: disable=no-self-argument
        return cls._OUTPUT_FILE

    @classproperty
    def dos_filenames(cls):
        """Return a dictionary of DOS output filenames that could be written by a calculation.

        Note that these will not be written unless the OpenMX input parameter `DOS_FILEOUT` is True
        """
        # pylint: disable=no-self-argument
        return {'val': cls._DATAFILE_DOS_VAL_FILE, 'vec': cls._DATAFILE_DOS_VEC_FILE}

    @classproperty
    def md_filenames(cls):
        """Return a dictionary of MD output filenames that could be written by a calculation.

        Note that these will not be written unless the OpenMX input parameter `MD_TYPE` is not `nomd`
        """
        # pylint: disable=no-self-argument
        return {'md': cls._DATAFILE_MD_FILE, 'md2': cls._DATAFILE_MD2_FILE}

    @classproperty
    def band_filename(cls):
        """Return the band output filename that could be written by a calculation.

        Note that this will not be written unless the OpenMX input parameters include:
            - `BAND_NKPATH != 0`
            - `SCF_EIGENVALUESOLVER == band`
        """
        #pylint: disable=no-self-argument
        return cls._DATAFILE_BAND_FILE

    @classmethod
    def define(cls, spec):
        """Define the inputs and outputs of the Calculation."""
        # yapf: disable
        super(OpenmxCalculation, cls).define(spec)

        ## Inputs
        # Metadata
        spec.input('metadata.options.parser_name', valid_type=str, default=cls._DEFAULT_PARSER_NAME)
        spec.input('metadata.options.resources', valid_type=dict,
            default={'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        # Pure inputs
        spec.input('structure', valid_type=orm.StructureData,
            help='The input structure.')
        spec.input('kpoints', valid_type=orm.KpointsData,
            help='The input k-point mesh or path.')
        spec.input('parameters', valid_type=orm.Dict,
            help='The input parameters that are to be used to construct the input file.')
        spec.input('orbital_configurations', valid_type=orm.ArrayData,
            help='Contains arrays named by kind whose entries correspond to the number of s, p, d, and f orbitals '
                 'desired.')
        spec.input('settings', valid_type=orm.Dict, required=False,
            help='Optional parameters to affect the way the calculation job and the parsing are performed.')
        # Input namespaces
        spec.input_namespace('pseudos', valid_type=VpsData, dynamic=True,
            help='A mapping of `VpsData` nodes onto the kind name to which they should apply.')
        spec.input_namespace('orbitals', valid_type=PaoData, dynamic=True,
            help='A mapping of `PaoData` nodes onto the kind name to which they should apply.')

        ## Outputs
        spec.output('output_parameters', valid_type=orm.Dict,
            help='The `output_parameters` output node of the successful calculation.')
        spec.output('output_structure', valid_type=orm.StructureData, required=False,
            help='The `output_structure` output node of the successful calculation if present.')
        spec.output('output_trajectory', valid_type=orm.Dict, required=False,
            help='The `output_trajectory` output node of the successful calculation if present.')

        ## Errors
        # Unrecoverable errors: required retrieve files could not be read, parsed, or are otherwise incomplete
        spec.exit_code(301, 'ERROR_NO_RETRIEVED_TEMPORARY_FOLDER',
            message='The retrieved temporary folder could not be accessed.')
        spec.exit_code(302, 'ERROR_OUTPUT_STDOUT_MISSING',
            message='The retrieved folder did not contain the required stdout output file.')
        spec.exit_code(303, 'ERROR_OUTPUT_DOS_MISSING',
            message='The retrieved folder did not contain the required dos output file.')
        spec.exit_code(310, 'ERROR_OUTPUT_STDOUT_READ',
            message='The stdout output file could not be read.')
        spec.exit_code(311, 'ERROR_OUTPUT_STDOUT_PARSE',
            message='The stdout output file could not be parsed.')
        spec.exit_code(312, 'ERROR_OUTPUT_STDOUT_INCOMPLETE',
            message='The stdout output file was incomplete probably because the calculation was interrupted.')
        spec.exit_code(313, 'ERROR_OUTPUT_DOS_READ',
            message='The dos output file could not be read.')
        spec.exit_code(314, 'ERROR_OUTPUT_DOS_PARSE',
            message='The dos output file could not be parsed.')
        spec.exit_code(315, 'ERRO_OUTPUT_DOS_INCOMPLETE',
            message='The dos output file was incomplete probably because the calculation was interrupted.')
        spec.exit_code(350, 'ERROR_UNEXPECTED_PARSER_EXCEPTION',
            message='The parser raised an unexpected exception.')
        # Significant errors: calculation can be used to restart
        spec.exit_code(400, 'ERROR_OUT_OF_WALLTIME',
            message='The calculation stopped prematurely because it ran out of walltime.')
        spec.exit_code(410, 'ERROR_ELECTRONIC_CONVERGENCE_NOT_REACHED',
            message='The electronic minimization cycle did not reach self-consistency.')
        spec.exit_code(500, 'ERROR_IONIC_CONVERGENCE_NOT_REACHED',
            message='The ionic minimization cycle did not converge for the given thresholds.')
        spec.exit_code(502, 'ERROR_IONIC_CYCLE_EXCEEDED_NSTEP',
            message='The ionic minimization cycle did not converge after the maximum number of steps.')
        spec.exit_code(510, 'ERROR_IONIC_CYCLE_ELECTRONIC_CONVERGENCE_NOT_REACHED',
            message='The electronic minimization cycle failed during an ionic minimization cycle.')

        #  yapf: enable

    # pylint: disable=too-many-locals
    def prepare_for_submission(self, folder: folders.Folder):
        """Create input files from the input nodes passed to this instance of the `CalcJob`.

        :param folder: an `aiida.common.folders.Folder` to temporarily write files on disk
        :return: `aiida.common.datastructures.CalcInfo` instance
        """
        # To be filled out below
        local_copy_list = []
        remote_copy_list = []
        remote_symlink_list = []

        # Create the subfolders for pseudopotentials and orbitals
        folder.get_subfolder(self._PSEUDO_SUBFOLDER, create=True)
        folder.get_subfolder(self._ORBITAL_SUBFOLDER, create=True)

        # Get an uppercase-key-only version of the settings dictionary (also check for case-insensitive duplicates)
        if 'settings' in self.inputs:
            settings = uppercase_dict_keys(self.inputs.settings.get_dict(), dict_name='settings')
        else:
            settings = {}

        # Get an uppercase-key-only verion of the parameters dictionary (also check for case-insensitive duplicates)
        parameters = uppercase_dict_keys(self.inputs.parameters.get_dict(), dict_name='parameters')

        # No reserved parameter keywords should be provided
        self._check_reserved_keywords(parameters)

        # Load parameter schema
        with open(self._INPUT_SCHEMA, 'r') as stream:
            schema = json.load(stream)

        # Automatically generate input parameters for derived fields, e.g. structure -> Atoms.Unitvectors, etc.
        parameters = self._generate_input_parameters(
            self.inputs.structure, self.inputs.kpoints, parameters, self.inputs.pseudos, self.inputs.orbitals,
            self.inputs.orbital_configurations
        )

        # Get a lowercase-value-only version of the parameters dictionary
        parameters = lowercase_dict_values(parameters)

        # Validate input parameters
        self._validate_inputs(
            self.inputs.structure, self.inputs.kpoints, parameters, self.inputs.pseudos, self.inputs.orbitals,
            self.inputs.orbital_configurations, schema
        )

        # Get input file contents and lists of the pseudopotential and orbital files which need to be copied
        input_file_content = write_input_file(parameters, schema)
        local_copy_pseudo_list, local_copy_orbital_list = self._generate_local_copy_lists(
            self.inputs.pseudos, self.inputs.orbitals
        )

        local_copy_list += local_copy_pseudo_list
        local_copy_list += local_copy_orbital_list

        # Add output files to retrieve which have been specified to write in the input parameters
        retrieve_list = []
        if parameters.get('BAND_NKPATH', 0) > 0 and parameters.get('SCF_EIGENVALUESOLVER', 'band') == 'band':
            retrieve_list.append(self._DATAFILE_BAND_FILE)
        if parameters.get('MD_TYPE', 'nomd') != 'nomd':
            retrieve_list.append(self._DATAFILE_MD_FILE)
            retrieve_list.append(self._DATAFILE_MD2_FILE)

        # Write input file
        with folder.open(self._INPUT_FILE, 'w') as handle:
            handle.write(input_file_content)

        # Fill out the `CodeInfo`
        codeinfo = datastructures.CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.with_mpi = True
        codeinfo.cmdline_params = ([self._INPUT_FILE] + list(settings.pop('CMDLINE', [])))
        codeinfo.stdout_name = self._OUTPUT_FILE

        # Fill out the `CalcInfo`
        calcinfo = datastructures.CalcInfo()
        calcinfo.uuid = str(self.uuid)
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.remote_symlink_list = remote_symlink_list
        calcinfo.retrieve_list = retrieve_list
        calcinfo.retrieve_list.append(self._OUTPUT_FILE)
        calcinfo.retrieve_list += settings.pop('ADDITIONAL_RETRIEVE_LIST', [])

        # TODO: pop parser settings and report remaining unknown settings

        return calcinfo

    # pylint: disable=too-many-arguments
    def _generate_input_parameters(self, structure, kpoints, parameters, pseudos, orbitals, orbital_configurations):
        parameters = copy.deepcopy(parameters)

        parameters['SYSTEM_NAME'] = self._SYSTEM_NAME
        parameters['DATA_PATH'] = self._DATA_PATH
        parameters['LEVEL_OF_STDOUT'] = 3
        parameters['LEVEL_OF_FILEOUT'] = 0
        parameters['SPECIES_NUMBER'] = len(structure.kinds)
        parameters['DEFINITION_OF_ATOMIC_SPECIES'] = _get_def_atomic_species(
            structure, pseudos, orbitals, orbital_configurations
        )
        parameters['ATOMS_NUMBER'] = len(structure.sites)
        parameters['ATOMS_SPECIESANDCOORDINATES'] = _get_atoms_spec_and_coords(structure, orbitals)
        parameters['ATOMS_UNITVECTORS'] = structure.cell
        parameters['SCF_XCTYPE'] = _get_xc_type(pseudos)
        parameters['SCF_KGRID'] = kpoints.get_kpoints_mesh()[0]

        return parameters

    def _check_reserved_keywords(self, parameters):
        provided_reserved_kws = []
        for kw in parameters:
            if kw in _RESERVED_KEYWORDS:
                provided_reserved_kws.append(kw)
        if provided_reserved_kws:
            msg = f'The reserved keywords {", ".join(provided_reserved_kws)} were specified but should not be provided.'
            raise exceptions.InputValidationError(msg)

    # pylint: disable=too-many-arguments
    def _validate_inputs(self, structure, kpoints, parameters, pseudos, orbitals, orbital_configurations, schema):
        # A pseudopotential should be specified for each kind present in the `StructureData`
        kinds = [kind.name for kind in structure.kinds]
        if set(kinds) != set(pseudos.keys()):
            raise exceptions.InputValidationError(
                'Mismatch between the defined pseudos and the list of kinds of the structure.\n'
                'Pseudos: {};\nKinds: {}'.format(', '.join(list(pseudos.keys())), ', '.join(list(kinds)))
            )

        # All pseudopotentials should have the same exchange-correlation type
        xc_set = {pseudo.xc_type for pseudo in pseudos.values()}
        if len(xc_set) != 1:
            raise exceptions.InputValidationError(
                f'The provided pseudos have inconsistent exchange-correlation types: {xc_set}.'
            )

        # An orbital basis should be specified for each kind present in the `StructureData`
        if set(kinds) != set(orbitals.keys()):
            raise exceptions.InputValidationError(
                'Mismatch between the defined orbitals and the list of kinds of the structure.\n'
                'Orbitals: {};\nKinds: {}'.format(', '.join(list(orbitals.keys())), ', '.join(list(kinds)))
            )

        # Corresponding orbital bases and pseudopotentials should have the same Z-valence
        inconsistent_z_valence = {}
        for kind in set(kinds):
            if pseudos[kind].z_valence != orbitals[kind].z_valence:
                inconsistent_z_valence[kind] = (pseudos[kind].z_valence, orbitals[kind].z_valence)
        if inconsistent_z_valence:
            raise exceptions.InputValidationError(
                f'Mismatch between the pseudopotential and orbital valences: {inconsistent_z_valence}.'
            )

        # An orbital configuration should be specified for each orbital basis
        if set(orbital_configurations.get_arraynames()) != set(orbitals.keys()):
            raise exceptions.InputValidationError(
                'Mismatch between the defined orbitals and the array names of the orbital configurations.\n'
                'Orbitals: {};\nOrbital configurations: {}'.format(
                    ','.join(list(orbitals.keys())), ', '.join(orbital_configurations.get_arraynames())
                )
            )

        # KpointsData should have a kpoints_mesh; explicit k-points are not supported
        try:
            kpoints.get_kpoints_mesh()
        except AttributeError:
            raise exceptions.InputValidationError(
                'Explicit k-points are not supported. Instead, set a k-points mesh using '
                'KpointsData.set_kpoints_mesh().'
            )

        # KpointsData should have a 0-shift; shifts are not supported
        try:
            shift = kpoints.get_kpoints_mesh()[1]
            if any([shift_i != 0 for shift_i in shift]):
                raise exceptions.InputValidationError('k-points shifts are not supported.')
        except AttributeError:
            pass

        # Validate against the JSON schema
        validate_parameters(schema, parameters)

    def _generate_local_copy_lists(self, pseudos, orbitals):
        pseudo_file_list = [(pseudo.uuid, pseudo.filename, os.path.join(self._PSEUDO_SUBFOLDER, pseudo.filename))
                            for pseudo in pseudos.values()]
        orbital_file_list = [(orbital.uuid, orbital.filename, os.path.join(self._ORBITAL_SUBFOLDER, orbital.filename))
                             for orbital in orbitals.values()]

        return pseudo_file_list, orbital_file_list
