# -*- coding: utf-8 -*-
"""Workchain to run an OpenMX calculation and calculate the density of states with DosMain."""
from aiida import orm
from aiida.common import AttributeDict
from aiida.engine import WorkChain
from aiida.plugins import CalculationFactory
from aiida.engine import ToContext

OpenmxCalculation = CalculationFactory('openmx.openmx')
DosmainCalculation = CalculationFactory('openmx.dosmain')


# pylint: disable=unused-argument,no-member,inconsistent-return-statements
def validate_inputs(inputs, ctx=None):
    """Validate the inputs of the entire input namespace."""
    if 'DOS_FILEOUT' not in inputs.openmx.parameters.keys():
        return DosWorkChain.exit_codes.ERROR_DOS_FILEOUT_NOT_SPECIFIED.message


class DosWorkChain(WorkChain):
    """Workchain to run an OpenMX calculation and calculate the density of states with DosMain."""

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        # yapf: disable
        super(DosWorkChain, cls).define(spec)

        spec.expose_inputs(OpenmxCalculation, namespace='openmx')
        spec.expose_inputs(DosmainCalculation, namespace='dosmain',
            exclude=('openmx_output_folder', 'openmx_input_structure', 'openmx_orbital_configurations'))
        spec.inputs_validator = validate_inputs

        spec.outline(
            cls.run_openmx,
            cls.inspect_openmx,
            cls.run_dosmain,
            cls.inspect_dosmain,
            cls.results
        )

        spec.exit_code(201, 'ERROR_DOS_FILEOUT_NOT_SPECIFIED',
            message='`DOS_FILEOUT` must be True in `openmx.parameters`.')
        spec.exit_code(401, 'ERROR_SUBPROCESS_FAILED_OPENMX',
            message='The openmx OpenmxCalculation subprocess failed.')
        spec.exit_code(402, 'ERROR_SUBPROCESS_FAILED_DOSMAIN',
            message='The DosMain DosmainCalculation subprocess failed.')

        spec.output('openmx_parameters', valid_type=orm.Dict,
            help='The output parameters of the openmx `OpenmxCalculation`.')
        spec.output('dosmain_dos', valid_type=orm.ArrayData,
            help='The output DOS of the DosMain `DosmainCalculation`.')
        # yapf: enable

    def run_openmx(self):
        """Run the OpenmxCalculation subprocess."""
        inputs = AttributeDict(self.exposed_inputs(OpenmxCalculation, namespace='openmx'))
        inputs.metadata.call_link_label = 'openmx'

        running = self.submit(OpenmxCalculation, **inputs)
        self.report(f'launching OpenmxCalculation<{running.pk}>')

        return ToContext(openmx_calculation=running)

    # pylint: disable=inconsistent-return-statements
    def inspect_openmx(self):
        """Verify that the OpenmxCalculation finished successfully."""
        calculation = self.ctx.openmx_calculation

        if not calculation.is_finished_ok:
            self.report(f'OpenmxCalculation failed with exit status {calculation.exit_status}')
            return self.exit_codes.ERROR_SUBPROCESS_FAILED_OPENMX

    def run_dosmain(self):
        """Run the DosmainCalculation subprocess."""
        inputs = AttributeDict(self.exposed_inputs(DosmainCalculation, namespace='dosmain'))
        openmx_calculation = self.ctx.openmx_calculation
        inputs.openmx_output_folder = openmx_calculation.outputs.remote_folder
        inputs.openmx_input_structure = openmx_calculation.inputs.structure
        inputs.openmx_orbital_configurations = openmx_calculation.inputs.orbital_configurations
        inputs.metadata.call_link_label = 'dosmain'

        running = self.submit(DosmainCalculation, **inputs)
        self.report(f'launching DosmainCalculation<{running.pk}>')

        return ToContext(dosmain_calculation=running)

    # pylint: disable=inconsistent-return-statements
    def inspect_dosmain(self):
        """Verify that the DosmainCalculation finished successfully."""
        calculation = self.ctx.dosmain_calculation

        if not calculation.is_finished_ok:
            self.report(f'DosmainCalculation failed with exit status {calculation.exit_status}')
            return self.exit_codes.ERROR_SUBPROCESS_FAILED_DOSMAIN

    def results(self):
        """Attach the desired output nodes directly as outputs of the workchain."""
        self.report('workchain completed successfully')
        self.out('openmx_parameters', self.ctx.openmx_calculation.outputs.output_parameters)
        self.out('dosmain_dos', self.ctx.dosmain_calculation.outputs.output_dos)
