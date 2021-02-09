""" Tests for calculations

"""
import os
from . import TEST_DIR


def test_process(openmx_code):
    """Test running a calculation
    note this does not test that the expected outputs are created of output parsing"""
    from aiida.plugins import DataFactory, CalculationFactory
    from aiida.engine import run

    # Prepare input parameters
    DiffParameters = DataFactory('openmx')
    parameters = DiffParameters({'ignore-case': True})

    from aiida.orm import SinglefileData
    file1 = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files", 'file1.txt'))
    file2 = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files", 'file2.txt'))

    # set up calculation
    inputs = {
        'code': openmx_code,
        'parameters': parameters,
        'file1': file1,
        'file2': file2,
        'metadata': {
            'options': {
                'max_wallclock_seconds': 30
            },
        },
    }

    result = run(CalculationFactory('openmx'), **inputs)
    computed_diff = result['openmx'].get_content()

    assert 'content1' in computed_diff
    assert 'content2' in computed_diff
