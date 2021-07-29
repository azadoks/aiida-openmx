# -*- coding: utf-8 -*-
"""Command line utilities to create and inspect `PaoData` nodes."""
import click

from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators, echo

from . import cmd_data


@cmd_data.group('pao')
def cmd_pao():
    """Commands to create and inspect `PaoData` nodes."""


@cmd_pao.command('import')
@click.argument('filename', type=click.File('r'))
@options.DRY_RUN()
@decorators.with_dbenv()
def cmd_import(filename, dry_run):
    """Import a `PaoData` from a `.pao` pseudopotential file."""
    from aiida_basis.data.basis import PaoData

    pao = PaoData.get_or_create(filename=filename)

    if dry_run:
        echo.echo_success(f'parsed VPS with element {pao.element}')
    else:
        pao.store()
        echo.echo_success(f'parsed and stored VpsData<{pao.pk}> with element {pao.element}')
