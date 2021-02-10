"""`CalcJob` for OpenMX."""

import os
import copy

import numpy as np

from aiida import orm
from aiida.common import datastructures, exceptions, folders
from aiida.engine import CalcJob

from ..utils._dict import _uppercase_dict
from ..utils._parameters import PARAMETERS, RESERVED_KEYWORDS
from ..utils._input import _atoms_spec_and_coords, _atoms_unit_vectors, _def_atomic_species, _xc_type


class OpenmxCalculation(CalcJob):
    """`CalcJob` for OpenMX."""

    # Subfolders
    _PSEUDO_SUBFOLDER = './VPS/'
    _ORBITAL_SUBFOLDER = './PAO/'
    _OUTPUT_SUBFOLDER = './out/'
    _SYSTEM_NAME = 'aiida'

    # Retrieve list
    _RETRIEVE_LIST = []

    # Defaults
    _DEFAULT_INPUT_FILE = 'aiida.in'
    _DEFAULT_OUTPUT_FILE = 'aiida.out'
    _DEFAULT_DOS_OUTPUT_FILE = 'aiida.dos'
    _DEFAULT_FERMI_OUTPUT_FILE = 'aiida.fermi'
    _DEFAULT_HS_OUTPUT_FILE = 'aiida.hs'
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
        spec.input('metadata.options.dos_output_filenmae', valid_type=str, default=cls._DEFAULT_DOS_OUTPUT_FILE)
        spec.input('metadata.options.fermi_output_filename', valid_type=str, default=cls._DEFAULT_FERMI_OUTPUT_FILE)
        spec.input('metadata.options.hs_output_filename', valid_type=str, default=cls._DEFAULT_HS_OUTPUT_FILE)
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
        spec.input_namespace('orbitals', valid_type=PaoData, dynamic=True,
            help='A mapping of `PaoData` nodes onto the kind of name to which they should apply.')

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
        # Create the subfolder that will contain the orbitals
        folder.get_subfolder(self._ORBITAL_SUBFOLDER, create=True)

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
            settings,  # The uppercase-key-only dict
            self.inputs.pseudos,
            self.inputs.orbitals,
        ]

        # Validate inputs
        self._validate_inputs(*arguments)

        # Get input file contents and lists of the pseudopotential and orbital files which need to be copied
        input_file_content, local_copy_pseudo_list, local_copy_orbital_list = self._generate_inputdata(*arguments)
        local_copy_list += local_copy_pseudo_list
        local_copy_list += local_copy_orbital_list

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

    def _validate_inputs(structure, kpoints, parameters, settings, pseudos, orbitals):
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
            if kw in RESERVED_KEYWORDS:
                provided_reserved_kws.append(kw)
        if provided_reserved_kws:
            msg = f'The reserved keywords {", ".join(provided_reserved_kws)} should not be provided.'
            raise exceptions.InputValidationError(msg)

        # Check parameters against our specification
        for kw, param in parameters:
            param_def = PARAMETERS[kw]
            # Check type
            if (param_type := param_def.get('type')) is not None:
                if not isinstance(param, param_type):
                    msg = f'Parameter {kw} should be {param_type} but is {type(param)}.'
                    raise exceptions.InputValidationError(msg)
                
            # Check shape
            if (shape := param_def.get('shape')) is not None:
                if not np.shape(param) == shape:
                    msg = f'Parameter {kw} should have shape {shape} but has shape {np.shape(param)}'
                    raise exceptions.InputValidationError(msg)

            # Check limits (numerical parameters)
            if (lims := param_def.get('lims')) is not None:
                if param <= lims[0]:
                    msg = f'Parameter {kw} ({param}) <= lower limit ({lims[0]}).'
                    raise exceptions.InputValidationError(msg)
                if param > lims[1]:
                    msg = f'Parameter {kw} ({param}) > upper limit ({lims[1]}).'
                    raise exceptions.InputValidationError(msg)

            # Check string arguments against valid options
            if (options := param_def.get('options')) is not None:
                if kw not in options:
                    msg = f'Parameter {kw} ({param}) is not in the valid options ({options}).'
                    raise exceptions.InputValidationError(msg)

    def _generate_inputdata(cls, structure, kpoints, parameters, settings, pseudos, orbitals):
        parameters = copy.deepcopy(parameters)
        
        parameters['System.CurrentDirectory'] = cls._OUTPUT_SUBFOLDER
        parameters['System.Name'] = cls._SYSTEM_NAME
        parameters['DATA.PATH'] = './'
        parameters['level.of.stdout'] = 3
        parameters['level.of.fileout'] = 3
        parameters['Species.Number'] = len(structure.kinds)
        parameters['Definition.of.Atomic.Species'] = _def_atomic_species(structure, pseudos, orbitals)
        parameters['scf.XcType'] = _xc_type(pseudos)
        parameters['scf.Kgrid'] = kpoints.get_kpoints_mesh()
        parameters['Atoms.Number'] = len(structure.sites)
        parameters['Atoms.SpeciesAndCoordinates'] = _atoms_spec_and_coords(structure, pseudos, orbitals)
        parameters['Atoms.Unitvectors.Unit'] = 'Ang'
        parameters['Atoms.UnitVectors'] = _atoms_unit_vectors(structure)

        # TODO: order parameters by section
        # PARAMETERS is ordered, so we will follow that order
        input_file_content = ''
        for kw, param_def in PARAMETERS.items():
            if parameters.get(kw) or param_def.get('required'):
                param = parameters.get(kw, param_def.get('default'))
                # Block parameters are provided as pre-formatted strings, and they must be bracketed
                # by "<{keyword}" and "{keyword}>"
                if param_def.get('block'):
                    param_content = f'<{kw}\n{param}\n{kw}>\n'
                # All other parameters go on the same line as their keyword
                else:
                    if param_def['type'] is float:
                        param_content = f'{kw}    {param:0.12f}\n'
                    # Booleans must be converted to OpenMX's "on" / "off" syntax
                    elif param_def['type'] is bool:
                        param_content = f'{kw}    {"on" if param else "off"}\n'
                    else:
                        param_content = f'{kw}    {param}\n'
                input_file_content += param_content

        pseudo_file_list = [
            (pseudo.uuid, pseudo.filename, os.path.join(cls._PSEUDO_SUBFOLDER, pseudo.filename))
                for pseudo in pseudos.values()
        ]
        orbital_file_list = [
            (orbital.uuid, orbital.filename, os.path.join(cls._ORBITAL_SUBFOLDER, orbital.filename))
                for orbital in orbitals.values()
        ]

        return input_file_content, pseudo_file_list, orbital_file_list
