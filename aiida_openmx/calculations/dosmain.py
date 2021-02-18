# -*- coding: utf-8 -*-
"""`CalcJob` for OpenMX `DosMain`."""

import os

from aiida import orm
from aiida.common import exceptions, datastructures, folders
from aiida.engine import CalcJob

# from aiida_openmx.utils.dosmain import write_input_file
from aiida_openmx.calculations.openmx import OpenmxCalculation


class DosmainCalculation(CalcJob):
    """`CalcJob` for OpenMX `DosMain`."""

    _DATA_PATH = './'
    _INPUT_FILE = 'aiida.in'
    _OUTPUT_FILE = 'aiida.out'

    _DEFAULT_PARSER_NAME = 'openmx.dosmain'

    @classmethod
    def define(cls, spec):
        """Define the inputs and outputs of the Calculation."""
        # yapf: disable
        super(DosmainCalculation, cls).define(spec)

        ## Inputs
        # Metadata
        spec.input('metadata.options.parser_name', valid_type=str, default=cls._DEFAULT_PARSER_NAME)
        spec.input('metadata.options.resources', valid_type=dict,
            default={'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        # Pure inputs
        spec.input('dos_type', valid_type=orm.Str,
            help='The type of DOS to calculate: either `dos` or `pdos`.')
        spec.input('dos_method', valid_type=orm.Str,
            help='The method used for constructing the DOS or PDOS: either `tetrahedron` or `gaussian`.')
        spec.input('gaussian_broadening', valid_type=orm.Float, required=False,
            help='The Gaussian broadening in eV used if `dos_type` is `gaussian`.')
        spec.input('pdos_atom_indices', valid_type=orm.ArrayData, required=False,
            help='The indices of the atoms (as in the OpenMX input file) for which to construct the PDOS if '
                 '`dos_method` is `pdos`.')
        spec.input('openmx_output_folder', valid_type=orm.RemoteData,
            help='The `RemoteData` node from a completed `OpenmxCalculation` where `DOS_FILEOUT=True`.')
        spec.input('openmx_input_structure', valid_type=orm.StructureData, required=False,
            help='The input `StructureData` used for the `OpenmxCalculation`, used if `dos_method` is `pdos`.')
        spec.input('openmx_orbital_configurations', valid_type=orm.StructureData, required=False,
            help='The orbital configurations used for the `OpenmxCalculation`, used if `dos_method` is `pdos`.')


        ## Outputs
        spec.output('output_dos', valid_type=orm.ArrayData, required=False,
            help='The `output_dos` output node of the successful calculation if present. '
                 'Each DOS array in `output_dos` has three columns: energy [eV], DOS [eV^-1], integrated DOS.')

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
        #  yapf: enable

    # pylint: disable=too-many-locals,unsubscriptable-object
    def prepare_for_submission(self, folder: folders.Folder):
        """Create input files from the input nodes passed to this instance of the `CalcJob`.

        :param folder: an `aiida.common.folders.Folder` to temporarily write files on disk
        :return: `aiida.common.datastructures.CalcInfo` instance
        """
        self._validate_inputs()

        dos_filenames = OpenmxCalculation.dos_filenames

        remote_symlink_list = [
            (
                self.inputs.openmx_output_folder.computer.uuid,
                os.path.join(self.inputs.openmx_output_folder.get_remote_path(),
                             dos_filenames['val']), os.path.join(self._DATA_PATH, dos_filenames['val'])
            ),
            (
                self.inputs.openmx_output_folder.computer.uuid,
                os.path.join(self.inputs.openmx_output_folder.get_remote_path(),
                             dos_filenames['vec']), os.path.join(self._DATA_PATH, dos_filenames['vec'])
            ),
        ]

        retrieve_list = self._generate_retrieve_list()

        input_file_content = self._write_input_file()
        with folder.open(self._INPUT_FILE, 'w') as handle:
            handle.write(input_file_content)

        # Fill out the `CodeInfo`
        codeinfo = datastructures.CodeInfo()
        codeinfo.cmdline_params = ([dos_filenames['val'], dos_filenames['vec']])
        codeinfo.stdin_name = self._INPUT_FILE
        codeinfo.stdout_name = self._OUTPUT_FILE
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.with_mpi = True

        # Fill out the `CalcInfo`
        calcinfo = datastructures.CalcInfo()
        calcinfo.uuid = str(self.uuid)
        calcinfo.codes_info = [codeinfo]
        calcinfo.remote_symlink_list = remote_symlink_list
        calcinfo.retrieve_list = retrieve_list
        calcinfo.retrieve_list.append(self._OUTPUT_FILE)

        return calcinfo

    def _validate_inputs(self):
        if self.inputs.dos_method not in ['tetrahedron', 'gaussian']:
            raise exceptions.InputValidationError(
                f'`dos_method` should be `tetrahedron` or `gaussian`, not {self.inputs.dos_method.value}'
            )

        if self.inputs.dos_method == 'gaussian':
            if 'gaussian_broadening' not in self.inputs:
                raise exceptions.InputValidationError(
                    '`gaussian_broadening` must be provided if `dos_method` is `gaussian`'
                )

        if self.inputs.dos_type == 'pdos':
            required_inputs_pdos = ['pdos_atom_indices', 'openmx_input_structure', 'openmx_orbital_configurations']
            for required_input in required_inputs_pdos:
                if required_input not in self.inputs:
                    raise exceptions.InputValidationError(
                        f'`{required_input}` must be provided if `dos_type` is `pdos`'
                    )

    def _generate_retrieve_list(self):
        dos_type = self.inputs.dos_type
        dos_method = self.inputs.dos_method

        if dos_type == 'dos':
            if dos_method == 'tetrahedron':
                dos_output_filename = OpenmxCalculation.system_name + '.DOS.Tetrahedron'
            else:  # gaussian
                dos_output_filename = OpenmxCalculation.system_name + '.DOS.Gaussian'
            return [dos_output_filename]
        # pdos
        # TODO: get number, order, and symbols of species and their orbital configurations
        raise exceptions.FeatureNotAvailable(f'{dos_type} is not yet supported.')

    def _write_input_file(self):
        dos_type = self.inputs.dos_type
        dos_method = self.inputs.dos_method
        input_file_content = ''

        if dos_method == 'tetrahedron':
            input_file_content += '1\n'

        if dos_method == 'gaussian':
            input_file_content += '2\n'
            input_file_content += '{:0.12f}\n'.format(self.inputs.gaussian_broadening.value)

        if dos_type == 'dos':
            input_file_content += '1\n'

        if dos_type == 'pdos':
            input_file_content += '2\n'
            atom_indices = self.inputs.pdos_atom_indices.get_array('atom_indices')
            input_file_content += ' '.join([f'{atom_index:d}' for atom_index in atom_indices]) + '\n'

        return input_file_content
