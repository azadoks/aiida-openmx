# aiida-openmx
An AiiDA plugin for the OpenMX DFT code.

## Installation
To install from source:
```shell
git clone https://github.com/azadoks/aiida-openmx
pip install aiida-openmx
```

### Pseudopotentials
Pseudopotentials for OpenMX are managed using the `aiida-pseudo` plugin.
The following example shows how to create a `PseudoPotentialFamily` AiiDA `Group` for the OpenMX soft PBE19 pseudopotentials.

First, collect the appropriate `.vps` files in a directory:
```shell
# Path to the extracted OpenMX source code on your computer
export OPENMX_SOURCE=$HOME/openmx3.9/

# Directory to hold the .vps files
mkdir PBE_19_soft

# Copy non-hard/soft .vps files
cp ${OPENMX_SOURCE}/DFT_DATA19/VPS/*PBE19.vps ./PBE_19_soft/

# Copy soft version of hard/soft .vps files
cp ${OPENMX_SOURCE}/DFT_DATA19/VPS/*PBE19S.vps ./PBE_19_soft/
```

Next, open a `verdi` shell and create a `PseudoPotentialFamily` from the directory:
```shell
verdi shell
```
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


### Basis sets
Basis sets for OpenMX are managed using the `aiida-basis` plugin.
The following example shows how to create a `BasisSet` which contains the pseudo-atomic orbitals from OpenMX's standard soft recommendation.

`aiida-openmx` provides some PAO tables based on OpenMX's recommendations to make this easier.
```shell
# OpenMX source directory
export OPENMX_SOURCE=$HOME/openmx3.9/

# Finds where `aiida-openmx` is installed
export AIIDA_OPENMX=$(python -c "import pathlib; import aiida_openmx; print(pathlib.Path(aiida_openmx.__file__).parent)")

# Make a directory to hold the `.pao` files
mkdir standard_19_soft

# Copy all the `.pao` files from the `aiida-openmx` table into the directory
for paofile in $(cat $AIIDA_OPENMX/data/pao/standard_s.txt);
  do cp $OPENMX_SOURCE/DFT_DATA19/PAO/$paofile ./standard_19_soft/;
done
```

Next, open a `verdi` shell and create a `BasisSet` from the directory:
```shell
verdi shell
```
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

## License
The `aiida-openmx` plugin package is released under the MIT license. See the `LICENSE` file for more details.
