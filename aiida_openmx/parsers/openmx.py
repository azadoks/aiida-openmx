# -*- coding: utf-8 -*-
"""OpenMX `openmx` output parser."""

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict, StructureData
from aiida.parsers.parser import Parser

from pymatgen.core import units

UNITS_SUFFIX = '_units'
CHARGE_UNITS = 'e'
DIPOLE_UNITS = 'Debye'
ENERGY_UNITS = 'eV'
FORCE_UNITS = 'eV/Å'
LENGTH_UNITS = 'Å'
MAGNETIZATION_UNITS = 'μB/cell'
POLARIZATION_UNITS = 'C/m²'
STRESS_UNITS = 'GPa'
COMPUTATIONAL_TIME_UNITS = 's'
SIMULATION_TIME_UNITS = 'fs'

ENERGY_NAME_MAPPING = {
    'Uele.': 'u_band',
    'Ukin.': 'u_kinetic',
    'UH0.': 'u_e_screened_coulomb',
    'UH1.': 'u_ee_coulomb',
    'Una.': 'u_neutral_atom',
    'Unl.': 'u_non_local',
    'Uxc0.': 'u_xc_alpha',
    'Uxc1.': 'u_xc_beta',
    'Ucore.': 'u_core_core_coulomb',
    'Uhub.': 'u_hubbard',
    'Ucs.': 'u_spin_constraint',
    'Uzs.': 'u_zeeman_spin_mag',
    'Uzo.': 'u_zeeman_spin_orb',
    'Uef.': 'u_e_field',
    'UvdW.': 'u_vdw',
    'Uch.': 'u_core_hole',
    'Utot.': 'u_tot',
    'UpV.': 'u_press_vol',
    'Enpy.': 'enthalpy'
}

DIPOLE_NAME_MAPPING = {
    'Total': 'total_dipole',
    'core': 'core_dipole',
    'Electron': 'electron_dipole',
    'Back ground': 'background_dipole'
}

TIMING_NAME_MAPPING = {
    'readfile': 'read_input',
    'truncation': 'truncation',
    'MD_pac': 'md_pac',
    'OutData': 'write_output',
    'DFT': 'dft',
    'Set_OLP_Kin': 'ovlp_kin',
    'Set_Nonlocal': 'nonlocal',
    'Set_ProExpn_VNA': 'pro_expn_vna',
    'Set_Hamiltonian': 'ham',
    'Poisson': 'poisson',
    'Diagonalization': 'diag',
    'Mixing_DM': 'mixing_dm',
    'Force': 'force',
    'Total_Energy': 'total_ene',
    'Set_Aden_Grid': 'aden_grid',
    'Set_Orbitals_Grid': 'orb_grid',
    'Set_Density_Grid': 'den_grid',
    'RestartFileDFT': 'write_restart',
    'Mulliken_Charge': 'mulliken_chg',
    'FFT(2D)_Density': 'fft_2d_den',
    'Others': 'other'
}

MD_TYPES_MD = []
MD_TYPES_OPT = []


class OpenmxParser(Parser):
    """Basic parser for OpenMX outputs."""

    def parse(self, **kwargs):
        """Parse outputs and store them in the AiiDA database."""
        try:
            _ = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_TEMPORARY_FOLDER

        # the md type is used to know how/if to parse the final structure
        md_type = self.node.inputs.parameters.get_dict().get('MD_TYPE', 'nomd')
        exit_code = self._parse_stdout(md_type)

        return exit_code

    # TODO: parse Mulliken populations, dipole moments, forces
    def _parse_stdout(self, md_type):
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements,too-many-nested-blocks
        """Parse OpenMX stdout.

        OpenMX writes the following information to stdout:
            - version and parallelization information
            - automatically generated cutoffs and grids
            - MD / geometry optimization history
            - SCF history
            - total energy and its components
            - chemical potential and eigenvalues
            - history of cell optimization
            - Mulliken populations
            - dipole moment
            - cell vectors and derivatives of total energy of final structure
            - xyz-coordinates and forces of final structure
            - fractional coordinates of final structure
            - computational timings
        """
        filename = self.node.process_class.output_filename

        if filename not in self.retrieved.list_object_names():
            return self.exit_codes.ERROR_OUTPUT_STDOUT_MISSING

        try:
            with self.retrieved.open(filename, 'r') as stream:
                lines = stream.readlines()
        except FileNotFoundError:
            return self.exit_codes.ERROR_OUTPUT_STDOUT_MISSING
        except OSError:
            return self.exit_codes.ERROR_OUTPUT_STDOUT_READ

        parameters = {}
        # printed multiple times (at each MD step)
        energies = {value: [] for value in ENERGY_NAME_MAPPING.values()}  # [Ha] -> eV

        for line_i, line in enumerate(lines):
            if 'OpenMX Ver.' in line:
                parameters['openmx_version'] = line.strip().split()[7]

            if 'MPI processes' in line:
                parameters['mpi_procs'] = int(line.strip().split()[1])

            if 'OpenMP threads' in line:
                parameters['omp_threads'] = int(line.strip().split()[5])

            if 'Used cutoff energy (Ryd) for 3D-grids' in line:
                cutoff_a, cutoff_b, cutoff_c = line.strip().split('=')[1].strip().split(',')  # [Ry]
                parameters['true_scf_ecut'] = [
                    float(cutoff_a) * units.Ha_to_eV / 2,
                    float(cutoff_b) * units.Ha_to_eV / 2,
                    float(cutoff_c) * units.Ha_to_eV / 2
                ]
                parameters['true_scf_ecut' + UNITS_SUFFIX] = ENERGY_UNITS

            if 'Num. of grids of a-, b-, and c-axes' in line:
                grid_a, grid_b, grid_c = line.strip().split('=')[1].strip().split(',')
                parameters['3d_fft_grid'] = [int(grid_a), int(grid_b), int(grid_c)]

            ## contains total energy and its components
            if 'Total energy (Hartree) at MD' in line:
                energies_start = line_i + 3

                energies_stop = energies_start
                while 'Note:' not in lines[energies_stop]:
                    energies_stop += 1

                for energy_line in lines[energies_start:energies_stop]:
                    for energy_openmx_name, energy_aiida_name in ENERGY_NAME_MAPPING.items():
                        if energy_openmx_name in energy_line:
                            energy_tmp = float(energy_line.strip().split()[1]) * units.Ha_to_eV
                            energies[energy_aiida_name].append(energy_tmp)

            if 'Eigenvalues (Hartree) of SCF KS-eq.' in line:
                bands = {
                    'e_fermi': [],  # [Ha] -> [eV]
                    'n_states': [],
                    'k_points': [],  # reciprocal coords [frac]
                    'up': [],  # spin-up eigenvalues [Ha] -> [eV]
                    'down': []  # spin-down eigenvalues [Ha] -> [eV]
                }
                ## eigenvalues block
                # set to start of block
                eigvals_start = line_i + 4
                # find line index for end of block
                eigvals_stop = eigvals_start
                while '*' not in lines[eigvals_stop]:
                    eigvals_stop += 1
                # set to end of block
                eigvals_stop -= 1
                eigvals_lines = lines[eigvals_start:eigvals_stop]

                ## header info
                # chemical potential (AZ: I'm assuming this is the Fermi energy)
                e_F_tmp = float(eigvals_lines[0].split('=')[1].strip())  # "Chemical Potential ..." [Ha]
                bands['e_fermi'].append(e_F_tmp * units.Ha_to_eV)  # [eV]
                n_states_tmp = float(eigvals_lines[1].split('=')[1].strip())  # "Number of States ..."
                bands['n_states'].append(n_states_tmp)

                ## k-points blocks
                # get the line index (in eigvals_lines) for the start of each "kloop" block
                kloop_starts = []
                for line_j, eigvals_line in enumerate(eigvals_lines):
                    if 'kloop' in eigvals_line:  # "kloop=`kloop_i`"
                        kloop_starts.append(line_j)
                kloop_stops = kloop_starts[1:] + [len(eigvals_lines)]

                # spin-up and spin-down eigenvalues for each "kloop" block
                for kloop_start, kloop_stop in zip(kloop_starts, kloop_stops):
                    # a block is [start_indices[i] -> start_indices[i + 1]) long
                    kloop_lines = eigvals_lines[kloop_start:kloop_stop]
                    # the second line of the block gives the k-point
                    k_words = kloop_lines[1].strip().split()  # ["k1=", k1, "k2=", k2, "k3=", k3]
                    bands['k_points'].append([float(k_words[1]), float(k_words[3]), float(k_words[5])])

                    # the fourth to second-to-last lines hold the eigenvalues
                    eigvals_up_tmp = []
                    eigvals_down_tmp = []
                    for kloop_line in kloop_lines[3:-2]:
                        _, e_up, e_down = kloop_line.strip().split()  # [band index], [Ha], [Ha]
                        eigvals_up_tmp.append(float(e_up) * units.Ha_to_eV)
                        eigvals_down_tmp.append(float(e_down) * units.Ha_to_eV)
                    bands['up'].append(eigvals_up_tmp)
                    bands['down'].append(eigvals_down_tmp)

            if 'History of cell optimization' in line:
                cell_opt = {
                    'sd_scaling': [],
                    'abs_max_force': [],  # [Ha/Bohr] -> [eV/Å]
                    'max_step': [],
                    'u_tot': [],  # [Ha] -> [eV]
                    'enthalpy': [],  # [Ha] -> [eV]
                    'vol': []  # [Å^3]
                }
                cell_opt_start = line_i + 7
                cell_opt_stop = cell_opt_start
                while '*' not in lines[cell_opt_stop]:
                    cell_opt_stop += 1

                cell_opt_lines = lines[cell_opt_start:cell_opt_stop - 1]
                for cell_opt_line in cell_opt_lines:
                    _, sd_scaling, abs_max_force, max_step, u_tot, enthalpy, vol = cell_opt_line.strip().split()
                    cell_opt['sd_scaling'].append(float(sd_scaling))
                    cell_opt['abs_max_force'].append(
                        float(abs_max_force) * units.Ha_to_eV / units.bohr_to_ang
                    )  # [eV/Å]
                    cell_opt['max_step'].append(float(max_step))  # [Å]
                    cell_opt['u_tot'].append(float(u_tot) * units.Ha_to_eV)  # [eV]
                    cell_opt['enthalpy'].append(float(enthalpy) * units.Ha_to_eV)  # [eV]
                    cell_opt['vol'].append(float(vol))  # [Å^3]

            if 'Mulliken populations' in line:
                pass

            if 'Dipole moment (Debye)' in line:
                dipole_start = line_i + 4
                dipole_stop = dipole_start
                while '*' not in lines[dipole_stop]:
                    dipole_stop += 1

                for dipole_line in lines[dipole_start:dipole_stop]:
                    if 'Absolute D' in dipole_line:
                        parameters['abs_dipole_mom'] = float(dipole_line.strip().split()[2])  # [Debye]
                        parameters['abs_dipole_mom' + UNITS_SUFFIX] = DIPOLE_UNITS
                    else:
                        for openmx_dipole_name, aiida_dipole_name in DIPOLE_NAME_MAPPING.items():
                            if openmx_dipole_name in dipole_line:
                                dx, dy, dz = dipole_line.replace(openmx_dipole_name, '').strip().split()
                                parameters[aiida_dipole_name] = [float(dx), float(dy), float(dz)]  # [Debye]
                                parameters[aiida_dipole_name + UNITS_SUFFIX] = DIPOLE_UNITS

            if 'Cell vectors (Ang.) and derivatives of total energy' in line:
                final_cell_vectors = []
                final_de_dcell = []

                cell_start = line_i + 4
                cell_stop = cell_start
                while '*' not in lines[cell_stop]:
                    cell_stop += 1

                cell_lines = lines[cell_start:cell_stop]
                for cell_line in cell_lines:
                    if 'a' in cell_line:
                        cell_text, de_dcell_text = cell_line.strip().split('=')[1:]
                        x, y, z = cell_text.strip().split()[:-1]
                        de_dx, de_dy, de_dz = de_dcell_text.strip().split()

                        final_cell_vectors.append([float(x), float(y), float(z)])  # [Å]
                        final_de_dcell.append([
                            float(de_dx) * units.Ha_to_eV / units.bohr_to_ang,
                            float(de_dy) * units.Ha_to_eV / units.bohr_to_ang,
                            float(de_dz) * units.Ha_to_eV / units.bohr_to_ang
                        ])

                parameters['final_de_dcell'] = final_de_dcell
                parameters['final_de_dcell' + UNITS_SUFFIX] = FORCE_UNITS

            if 'xyz-coordinates (Ang.) and forces (Hartree/Bohr)' in line:
                final_cart_coords = {
                    'species': [],
                    'coords': []  # [Å]
                }
                final_forces = []  # [eV/Å]

                final_cart_coords_start = line_i + 6
                final_cart_coords_stop = final_cart_coords_start
                while 'coordinates.forces' not in lines[final_cart_coords_stop]:
                    final_cart_coords_stop += 1

                for final_cart_coords_line in lines[final_cart_coords_start:final_cart_coords_stop]:
                    specie, x, y, z, fx, fy, fz = final_cart_coords_line.strip().split()[1:]
                    final_cart_coords['species'].append(specie)
                    final_cart_coords['coords'].append([float(x), float(y), float(z)])
                    final_forces.append([
                        float(fx) * units.Ha_to_eV / units.bohr_to_ang,
                        float(fy) * units.Ha_to_eV / units.bohr_to_ang,
                        float(fz) * units.Ha_to_eV / units.bohr_to_ang
                    ])

                parameters['final_forces'] = final_forces
                parameters['final_forces' + UNITS_SUFFIX] = FORCE_UNITS

            if 'Fractional coordinates of the final structure' in line:
                final_frac_coords = {
                    'species': [],
                    'coords': []  # [frac]
                }
                # set to start of block
                final_frac_coords_start = line_i + 4

                # find line index for end of block
                final_frac_coords_stop = final_frac_coords_start
                while '*' not in lines[final_frac_coords_stop]:
                    final_frac_coords_stop += 1

                for final_frac_coords_line in lines[final_frac_coords_start:final_frac_coords_stop - 1]:
                    specie, x, y, z = final_frac_coords_line.strip().split()[1:]  # [species], [frac], [frac], [frac]
                    final_frac_coords['species'].append(specie)
                    final_frac_coords['coords'].append([float(x), float(y), float(z)])

            if 'Computational Time (second)' in line:
                timing = {}  # [s]

                # set to start of block
                timing_start_i = line_i + 4
                # written at the end of the file
                timing_stop_i = len(lines)

                timing['elapsed_time'] = float(lines[timing_start_i].strip().split()[1])
                timing['elapsed_time' + UNITS_SUFFIX] = COMPUTATIONAL_TIME_UNITS

                for timing_line in lines[timing_start_i + 1:timing_stop_i]:
                    for key, value in TIMING_NAME_MAPPING.items():
                        if key in line:
                            min_id, min_time, max_id, max_time = timing_line.strip().split('=')[1].strip().split()
                            timing_tmp = {
                                'min_id': int(min_id),
                                'min_time': float(min_time),
                                'max_id': int(max_id),
                                'max_time': float(max_time)
                            }
                            timing[value] = timing_tmp
                            timing[value + UNITS_SUFFIX] = COMPUTATIONAL_TIME_UNITS

                parameters = {**parameters, **timing}

        ## output parameters
        for energy_name, value in energies.items():
            parameters[energy_name] = value[-1]
            parameters[energy_name + UNITS_SUFFIX] = ENERGY_UNITS

        parameters['e_fermi'] = bands['e_fermi'][-1]
        parameters['e_fermi' + UNITS_SUFFIX] = ENERGY_UNITS
        parameters['n_states'] = bands['n_states'][-1]

        self.out('output_parameters', Dict(dict=parameters))

        ## final structure
        if md_type != 'nomd':
            initial_structure = self.node.inputs.structure.clone()

            if md_type in ['optc1', 'optc2', 'optc3', 'optc4', 'optc5', 'optc6', 'optc7', 'rfc5', 'rfc6', 'rfc7']:
                final_structure = StructureData(cell=final_cell_vectors)
            else:
                final_structure = StructureData(cell=initial_structure.cell)

            for specie, coords in zip(final_cart_coords['species'], final_cart_coords['coords']):
                # specie is a kind name
                kind = initial_structure.get_kind(specie)
                final_structure.append_atom(position=coords, symbols=kind.symbol, name=specie)

            self.out('output_structure', final_structure)

        return ExitCode(0)
