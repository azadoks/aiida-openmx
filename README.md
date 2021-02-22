[![Build Status](https://github.com/zooks97/aiida-openmx/workflows/ci/badge.svg?branch=master)](https://github.com/zooks97/aiida-openmx/actions)
[![Coverage Status](https://coveralls.io/repos/github/zooks97/aiida-openmx/badge.svg?branch=master)](https://coveralls.io/github/zooks97/aiida-openmx?branch=master)
[![Docs status](https://readthedocs.org/projects/aiida-openmx/badge)](http://aiida-openmx.readthedocs.io/)
[![PyPI version](https://badge.fury.io/py/aiida-openmx.svg)](https://badge.fury.io/py/aiida-openmx)

# aiida-openmx

AiiDA plugin for the OpenMX DFT code.


## Installation

### `aiida-openmx`

```shell
pip install aiida-openmx
```

### Setting up some `code`s



### Pseudopotential families and basis sets

To simplify the use of pseudopotentials and orbital bases in `aiida-openmx`, `aiida-pseudo` and `aiida-basis` have support for OpenMX's VPS pseudopotential and PAO pseudoatomic orbital formats respectively.
For high-throughput studies, it is additionally useful to create `PseudoPotentialFamily` and `BasisSet` AiiDA `Group`s, which hold many pseudopotentials and orbital bases as well as various metadata.

As an example, lets create a `PseudoPotentialFamily` for OpenMX's soft PBE19 pseudopotentials and a `BasisSet` for OpenMX's soft 'standard' recommendation.

First, we collect the appropriate `.vps` pseudopotentials in a directory:
```shell
export OPENMX_SOURCE=$HOME/openmx3.9/  # Path to the extracted OpenMX source code on your computer
mkdir PBE_19_soft                                              # Directory to hold the .vps files
cp ${OPENMX_SOURCE}/DFT_DATA19/VPS/*PBE19.vps ./PBE_19_soft/   # Copy non-hard/soft .vps files
cp ${OPENMX_SOURCE}/DFT_DATA19/VPS/*PBE19S.vps ./PBE_19_soft/  # Copy soft version of hard/soft .vps files
```

Next, we'll create a `PseudoPotentialFamily` which contains all of the pseudopotentials in our directory.
First, run `python`, `ipython`, or `verdi shell`.
Then, run something like the following code:

```python
from aiida_pseudo.groups.family import PseudoPotentialFamily
from aiida_pseudo.data.pseudo import VpsData

PBE_19_soft_family = PseudoPotentialFamily(
    dirpath='./PBE_19_soft/',          # Directory where we copied our .vps files
    label='OpenMX/19/PBE/S',           # Name of the PseudoPotentialFamily in the AiiDA database
    description='OpenMX PBE19 (soft)'  # Longer description of what the PseudoPotentialFamily contains
    pseudo_type=VpsData                # AiiDA data type for VPS pseudopotentials
)
```

We can then check that the `PseudoPotentialFamily` is listed in our AiiDA `Groups`:

```shell
verdi group list -a
```

```
  PK  Label              Type string    User
----  -----------------  -------------  ---------------------
   1  OpenMX/19/PBE/S    pseudo.family  austin.zadoks@epfl.ch
```

Great! Now we can set up our pseudoatomic orbitals in a similar manner.
Because it's a bit trickier to collect all the appropriate files in this case, `aiida-openmx` provides some PAO tables based on OpenMX's recommendations.

```shell
export OPENMX_SOURCE=$HOME/openmx3.9/
export AIIDA_OPENMX=$(python -c "import pathlib; import aiida_openmx; print(pathlib.Path(aiida_openmx.__file__).parent)")
mkdir standard_19_soft
for paofile in $(cat $AIIDA_OPENMX/data/pao/standard_s.txt); do cp $OPENMX_SOURCE/DFT_DATA19/PAO/$paofile ./standard_19_soft/; done
```

Finally, we'll create a `BasisSet` which contains all of the pseudoatomic orbitals in our directory.
First, run `python`, `ipython`, or `verdi shell`.
Then, run something like the following code:

```python
from aiida_basis.groups.set import BasisSet
from aiida_basis.data.basis import PaoData

standard_19_soft_set = BasisSet(
    dirpath='./standard_19_soft/',  # Directory where we copied our .pao files
    label='OpenMX/19/standard/S',  # Name of the BasisSet in the AiiDA database
    description='OpenMX standard 19 (soft)'  # Longer description of what the BasisSet contains
    basis_type=PaoData  # AiiDA data type for PAO bases
)
```

We can then check that the `BasisSet` is listed in our AiiDA `Groups`:

```shell
verdi group list -a
```

```
  PK  Label                 Type string    User
----  --------------------  -------------  ---------------------
   1  OpenMX/19/PBE/S       pseudo.family  austin.zadoks@epfl.ch
   2  OpenMX/19/standard/S  basis.set      austin.zadoks@epfl.ch
```

## Development

If you would like to contribute to the development of `aiida-openmx`, please clone this Github repository and install `aiida-openmx` as follows:

```shell
git clone https://github.com/zooks97/aiida-openmx .
cd aiida-openmx
pip install -e .[pre-commit,testing,docs]  # Install extra dependencies
pre-commit install  # Install pre-commit hooks
pytest -v  # Discover and run all tests
```

See the [developer guide](http://aiida-openmx.readthedocs.io/en/latest/developer_guide/index.html) for more information.


## License

MIT


## Contact

austin.zadoks@epfl.ch
