# -*- coding: utf-8 -*-
"""OpenMX output parser."""

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict, StructureData, TrajectoryData
from aiida.parsers.parser import Parser

UNITS_SUFFIX = '_units'
CHARGE_UNITS = 'e'
DIPOLE_UNITS = 'Debye'
ENERGY_UNITS = 'eV'
FORCE_UNITS = 'eV/Å'
LENGTH_UNITS = 'Å'
MAGNETIZATION_UNITS = 'μB/cell'
POLARIZATION_UNITS = 'C/m²'
STRESS_UNITS = 'GPa'


class OpenmxParser(Parser):
    """Basic parser for OpenMX outputs."""
    
    def parse(self, **kwargs):
        """Parse outputs and store them in the AiiDA database."""
        try:
            _ = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_OUTPUT

        md_type = self.node.inputs['parameters'].get_dict().get('MD.Type')

        return ExitCode(0)