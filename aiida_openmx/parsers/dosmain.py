# -*- coding: utf-8 -*-
"""OpenMX `DosMain` output parser."""

import numpy as np

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import ArrayData
from aiida.parsers.parser import Parser

UNITS_SUFFIX = '_units'
ENERGY_UNITS = 'eV'


class DosmainParser(Parser):
    """Basis parser for DosMain outputs."""

    def parse(self, **kwargs):
        """Parse outputs and store them in the AiiDA database."""
        try:
            _ = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_TEMPORARY_FOLDER

        if self.node.inputs.dos_type == 'dos':
            exit_code = self._parse_dos()
        else:
            exit_code = self._parse_pdos()

        return exit_code

    def _parse_dos(self):
        """Parse DosMain DOS output."""
        if self.node.inputs.dos_method == 'tetrahedron':
            filename = 'aiida.DOS.Tetrahedron'
        else:
            filename = 'aiida.DOS.Gaussian'

        if filename not in self.retrieved.list_object_names():
            return self.exit_codes.ERROR_DOS_OUTPUT_MISSING

        try:
            with self.retrieved.open(filename, 'r') as stream:
                dos = np.loadtxt(stream)
        except FileNotFoundError:
            return self.exit_codes.ERROR_DOS_OUTPUT_MISSING
        except OSError:
            return self.exit_codes.ERROR_DOS_OUTPUT_READ

        dos_ad = ArrayData()
        dos_ad.set_array('dos', dos)
        self.out('output_dos', dos_ad)

        return ExitCode(0)

    def _parse_pdos(self):
        return ExitCode(0)
