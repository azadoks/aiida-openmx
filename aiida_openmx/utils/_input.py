from os.path import splitext

def _xc_type(pseudos):
    xc_set = {pseudo.xc_type for pseudo in pseudos.values()}
    if len(xc_set) != 1:
        msg = 'The provided pseudos have inconsistent exchange-correlation type.'
        raise ValueError(msg)
    return xc_set.pop()

def _def_atomic_species(structure, pseudos, orbitals):
    # TAG = 'Definition.of.Atomic.Species'

    lines = []
    for kind in structure.kinds:
        pseudo_file_stem = splitext(pseudos[kind.name].filename)
        orbital_file_stem = splitext(orbitals[kind.name].filename)
        orbital_configuration = orbitals[kind.name].configuration_string
        lines.append(f'{kind.name} {pseudo_file_stem} {orbital_file_stem}-{orbital_configuration}')
    block = '\n'.join(lines)

    return block
    # return f'<{TAG}\n{block}\n{TAG}>'


def _atoms_spec_and_coords(structure, orbitals):
    # TAG = 'Atoms.SpeciesAndCoordinates'

    lines = []
    for i, site in enumerate(structure.sites):
        index = i + 1
        kind_name = site.kind_name
        x, y, z = site.position
        valence = orbitals[kind_name].valence
        charge_up, charge_down = valence / 2, valence / 2
        lines.append(f'{index:d} {kind_name} {x:0.12f} {y:0.12f} {z:0.12f} {charge_up:0.6f} {charge_down:0.6f}')
    block = '\n'.join(lines)

    return block
    # return f'<{TAG}\n{block}\n{TAG}>'


def _atoms_unit_vectors(structure):
    # TAG = 'Atoms.UnitVectors'

    lines = []
    for cell_vector in structure.cell:
        lines.append(' '.join([f'{component:0.12f}' for component in cell_vector]))
    block = '\n'.join(lines)

    return block
    # return f'<{TAG}\n{block}\n{TAG}>'
