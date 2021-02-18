[![Build Status](https://github.com/zooks97/aiida-openmx/workflows/ci/badge.svg?branch=master)](https://github.com/zooks97/aiida-openmx/actions)
[![Coverage Status](https://coveralls.io/repos/github/zooks97/aiida-openmx/badge.svg?branch=master)](https://coveralls.io/github/zooks97/aiida-openmx?branch=master)
[![Docs status](https://readthedocs.org/projects/aiida-openmx/badge)](http://aiida-openmx.readthedocs.io/)
[![PyPI version](https://badge.fury.io/py/aiida-openmx.svg)](https://badge.fury.io/py/aiida-openmx)

# aiida-openmx

AiiDA plugin for the OpenMX DFT code.

This plugin is the default output of the
[AiiDA plugin cutter](https://github.com/aiidateam/aiida-plugin-cutter),
intended to help developers get started with their AiiDA plugins.

## Installation

### `aiida-openmx`
```shell
pip install aiida-openmx
```


### Creating pseudopotential families
As `aiida-pseudo` does not have any bespoke support for OpenMX pseudopotential families at the moment, setting up pseudopotentials in AiiDA is a little more complex than running `aiida-pseudo install openmx`.

Nevertheless, it is not too difficult. The general steps are:
1. Make a directory with the pseudos you would like to have in a family
2. Create a `PseudoPotentialFamily` in the `verdi shell` from that directory

For example, to install the PBE19 pseudopotentials with the 'S' variants for elements like Co and Fe, one could do the following, replacing `${OPENMX_SOURCE}` with the path to your extracted OpenMX source directory or setting the environment variable `OPENMX_SOURCE` before running these commands:
```shell
mkdir PBE19S
cp ${OPENMX_SOURCE}/DFT_DATA19/VPS/*PBE19.vps PBE19S
cp ${OPENMX_SOURCE}/DFT_DATA19/VPS/*PBE19S.vps PBE19S
```

Once you have placed the desired VPS pseudopotentials in a directory, run the following (or similar) from `verdi shell`

```python
from aiida_pseudo.groups.family import PseudoPotentialFamily
from aiida_pseudo.data.pseudo.vps import VpsData
pbe19s_family = PseudoPotentialFamily.create_from_folder(
    dirpath='PBE19S/',
    label='OpenMX/19/PBE/S',
    description='OpenMX PBE19(S)',
    pseudo_type=VpsData)
```

## Development

```shell
git clone https://github.com/zooks97/aiida-openmx .
cd aiida-openmx
pip install -e .[pre-commit,testing,docs]  # install extra dependencies
pre-commit install  # install pre-commit hooks
pytest -v  # discover and run all tests
```

See the [developer guide](http://aiida-openmx.readthedocs.io/en/latest/developer_guide/index.html) for more information.

## License

MIT


## Contact

austin.zadoks@epfl.ch
