"""`CalcJob` for OpenMX."""

from os.path import splitext

from aiida import orm
from aiida.common import datastructures, exceptions, folders
from aiida.engine import CalcJob

from ..utils._dict import _uppercase_dict


class OpenmxCalculation(CalcJob):
    """`CalcJob` for OpenMX."""

    # Subfolders
    _PSEUDO_SUBFOLDER = './VPS/'
    _ORBITAL_SUBFOLDER = './PAO/'
    _OUTPUT_SUBFOLDER = './out/'

    # Retrieve list
    _RETRIEVE_LIST = []

    # Defaults
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
        # Check that a pseudo potential was specified for each kind present in the `StructureData`
        kinds = [kind.name for kind in self.inputs.structure.kinds]
        if set(kinds) != set(self.inputs.pseudos.keys()):
            raise exceptions.InputValidationError(
                'Mismatch between the defined pseudos and the list of kinds of the structure.\n'
                'Pseudos: {};\nKinds: {}'.format(', '.join(
                    list(self.inputs.pseudos.keys()))), ', '.join(list(kinds)))
        # Check that an orbital basis was specified for each kind present in the `StructureData`
        if set(kinds) != set(self.inputs.orbitals.keys()):
            raise exceptions.InputValidationError(
                'Mismatch between the defined orbitals and the list of kinds of the structure.\n'
                'Orbitals: {};\nKinds: {}'.format(', '.join(
                    list(self.inputs.orbitals.keys()))),
                ', '.join(list(kinds)))

        # Get an uppercase-key-only version of the settings dictionary (also check for case-insensitive duplicates)
        if 'settings' in self.inputs:
            settings = _uppercase_dict(self.inputs.settings.get_dict(),
                                       dict_name='settings')
        else:
            settings = {}

        # To be filled out below
        local_copy_list = []
        remote_copy_list = []
        remote_symlink_list = []

        # Create the subfolder that will contain the pseudopotentials
        folder.get_subfolder(self._PSEUDO_SUBFOLDER, create=True)
        # Create the subfolder that will contain the orbitals
        folder.get_subfolder(self._ORBITAL_SUBFOLDER, create=True)

        # Package arguments for `_generate_inputdata`
        arguments = [
            self.inputs.structure,
            self.inputs.parameters,
            settings,  # The uppercase-key-only dict
            self.inputs.pseudos,
            self.inputs.orbitals,
        ]

        # Get input file contents and lists of the pseudopotential and orbital files which need to be copied
        input_filecontent, local_copy_pseudo_list, local_copy_orbital_list = self._generate_inputdata(
            *arguments)
        local_copy_list += local_copy_pseudo_list
        local_copy_list += local_copy_orbital_list

        # Write input file
        with folder.open(self.metadata.options.input_filename, 'w') as handle:
            handle.write(input_filecontent)

        # Fill out the `CodeInfo` to put in the `CalcInfo`
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

    def _generate_inputdata(structure, kpoints, parameters, settings, pseudos,
                            orbitals):

        return


def _def_atomic_sepcies(structure, pseudos, orbitals):
    TAG = 'Definition.of.Atomic.Species'

    lines = []
    for kind in structure.kinds:
        pseudo_file_stem = splitext(pseudos[kind.name].filename)
        orbital_file_stem = splitext(orbitals[kind.name].filename)
        orbital_configuration = orbitals[kind.name].configuration
        lines.append(
            f'{kind.name} {pseudo_file_stem} {orbital_file_stem}-{orbital_configuration}'
        )
    block = '\n'.join(lines)

    return f'<{TAG}\n{block}\n{TAG}>'


def _atoms_spec_and_coords(structure, orbitals):
    TAG = 'Atoms.SpeciesAndCoordinates'

    lines = []
    for i, site in enumerate(structure.sites):
        index = i + 1
        specie = site.kind_name
        coords = site.position
        valence = orbitals[specie].valence_
        charge_up, charge_down = valence / 2, valence / 2
        lines.append(
            f'{index} {specie} {coords[0]} {coords[1]} {coords[2]} {charge_up} {charge_down}'
        )
    block = '\n'.join(lines)

    return f'<{TAG}\n{block}\n{TAG}>'


def _atoms_unit_vectors(structure):
    TAG = 'Atoms.UnitVectors'

    lines = []
    for cell_vector in structure.cell:
        lines.append(' '.join(
            [f'{component:0.12f}' for component in cell_vector]))
    block = '\n'.join(lines)

    return f'<{TAG}\n{block}\n{TAG}>'
