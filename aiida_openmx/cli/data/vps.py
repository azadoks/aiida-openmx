# -*- coding: utf-8 -*-
"""Command line utilities to create and inspect `VpsData` nodes."""
import click

from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators, echo

from . import cmd_data


@cmd_data.group('vps')
def cmd_vps():
    """Commands to create and inspect `VpsData` nodes."""


@cmd_vps.command('import')
@click.argument('filename', type=click.File('r'))
@options.DRY_RUN()
@decorators.with_dbenv()
def cmd_import(filename, dry_run):
    """Import a `VpsData` from a `.vps` pseudopotential file."""
    from aiida_pseudo.data.pseudo.vps import VpsData

    vps = VpsData.get_or_create(filename=filename)

    if dry_run:
        echo.echo_success(f'parsed VPS with element {vps.element}')
    else:
        vps.store()
        echo.echo_success(f'parsed and stored VpsData<{vps.pk}> with element {vps.element}')
