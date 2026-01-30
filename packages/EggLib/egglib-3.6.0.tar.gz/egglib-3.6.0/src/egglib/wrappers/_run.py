"""
    Copyright 2023 Stéphane De Mita, Mathieu Siol

    This file is part of EggLib.

    EggLib is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    EggLib is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with EggLib.  If not, see <http://www.gnu.org/licenses/>.
"""

from .. import __version__
from ._utils import paths
import click

#### command for editing paths from the console ########################

@click.command(no_args_is_help=True)
@click.version_option(__version__, message='EggLib %(version)s')
@click.option('-a', '--autodetect', is_flag=True, show_default=False, default=False,
    help='Auto-configure application paths based on default command names.')
@click.option('-p', '--path', nargs=2, multiple=True, help='set')
@click.option('-d', '--display', is_flag=True, show_default=False, default=False,
    help='Show values of applications paths (after any setting or detection if requested)')
@click.option('--save/--no-save', '-s/-n', default=False, show_default=True,
    help='Save application paths for future imports of EggLib')
def paths_edit(autodetect, path, display, save):
    """
    Edit external application paths for the current EggLib installation.
    """

    if autodetect:
        paths.autodetect(True)

    for k, v in path:
        paths[k] = v

    if display:
        print('Current values of application paths:')
        for p in paths:
            if paths[p] is None: click.echo(f'    {p}:')
            else: click.echo(f'    {p}: `{paths[p]}\'')

    if save:
        paths.save()
        print(f'Application paths saved to {paths.fname}')
