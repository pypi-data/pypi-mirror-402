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

from .. import __version__, config, wrappers
import click, pathlib

@click.group()
def main():
    pass

#### command for editing app paths from the console #####################

@main.command(no_args_is_help=True)

@click.option('-z', '--zero', nargs=1, multiple=True,
    help='Format: --zero APP. Reset application configuration, '
         'dismissing previous configuration.')

@click.option('-Z', '--zero-all', is_flag=True, default=False,
    help='Reset all applications configuration, dismissing all '
         'previous configuration. Doesn\'t clear the persistent '
         'configuration file unless --save is used.')

@click.option('-a', '--auto', is_flag=True, default=False,
    help='Try default command names, which are usually the application \
name. This will work if the external applications are installed in the \
executable path. Only applications that are not currently configured \
are considered. If the test doesn\'t succeed, the error message is \
printed and the application is not configured. The default for \
individual applications can be overriden by --force-cmd, --cmd and \
--path options.')

@click.option('-c', '--cmd', 'commands', nargs=2, multiple=True,
    help='Format: --cmd APP COMMAND. Set the command used to start the \
application. To specify a full or relative path to the executable, use \
--path. Overrides the defaults specified by --auto. The is no priority \
between --force-cmd, --cmd and --path (the latest specified prevails). \
For --cmd and --path, if the test doesn\'t succeed, an error is \
caused.')

@click.option('-f', '--force-cmd', 'fcommands', nargs=2, multiple=True,
    help='Format: --force-cmd APP COMMAND. Set an application command. \
Like --cmd, but disable testing. The user needs to ensure that the \
software will be available through this command at runtime.')

@click.option('-p', '--path', 'paths', nargs=2, multiple=True,
    help='Format: --path APP PATH. Set the relative or absolute path to \
start the application. Relative paths are reformatted to be absolute. \
Overrides the defaults specified by --auto. The is no priority between \
--force-cmd, --cmd and --path (the latest specified prevails). For \
--cmd and--path, ff the test doesn\'t succeed, an error is caused.',
   type=(str, click.Path(exists=True, dir_okay=False,
         resolve_path=True, path_type=pathlib.Path)))

@click.option('-L', '--list', 'list_', is_flag=True, default=False,
    help='Display application configuration. If any of --auto, --cmd, \
and --path is used, the final result is displayed.')

@click.option('-s', '--save', default=False, is_flag=True,
    help='Save configuration, after any change mandated by --clear \
--auto, --cmd and/or --path, in persistent file. The location of the \
file is controlled by --global and --user options.')

@click.option('-g', '--global', 'dest', flag_value='global',
    help='Save configuration in EggLib installation. This will affect \
all users using this installation of EggLib and might require \
administrative rights (like the EggLib installation).  The default is \
to use the current configuration file.')

@click.option('-u', '--user', 'dest', flag_value='user',
    help='Save configuration in user settings. This guarantees that \
only the current user will see the results when importing EggLib. \
Create the user-specific configuration file if it does not exist. The \
default is to use the current configuration file.')

@click.option('--delete-user', default=False, is_flag=True,
    help='Delete user configuration file, if any. This operation is \
not affected by any configuration operation specified by --clear, \
--auto, --cmd, and --path options. It is technically possible to \
save the configuration in the user\'s settings and then delete it \
using this function. Note that this operation is always performed \
last. To ignore user configuration and regenerate it, use --zero.')

def apps(zero_all, zero, auto, commands, fcommands, paths, list_, save, dest, delete_user):
    """
    Manage external application command names or paths. These are the
    commands who are used whenever EggLib uses an external application.
    Actions triggers by options are performed in the order in which they
    are listed.
    """

    if zero_all:
        wrappers.paths.clear()

    for key in zero:
        if not (app := wrappers.paths.get(key)):
            raise click.ClickException(f'Unknown application: "{key}"')
        app.zero()

    if auto:
        wrappers.paths.autodetect(True)

    for key, cmd in commands:
        if not (app := wrappers.paths.get(key)):
            raise click.ClickException(f'Unknown application: "{key}"')
        if (error := app.set_path(cmd, False)) != None:
            raise click.ClickException(f'Invalid command for {key}: "{cmd}"; error was:\n{error}')

    for key, cmd in fcommands:
        if not (app := wrappers.paths.get(key)):
            raise click.ClickException(f'Unknown application: "{key}"')
        app.set_path_force(cmd)

    for key, path in paths:
        if not (app := wrappers.paths.get(key)):
            raise click.ClickException(f'Unknown application: "{key}"')
        if (error := app.set_path(path, False)) != None:
            raise click.ClickException(f'Invalid command for {key}: "{path}"; error was:\n{error}')

    if list_:
        click.echo('Current values of application paths:')
        for p in wrappers.paths:
            if wrappers.paths[p] is None: click.echo(f'    - {p} (none)')
            else: click.echo(f'    + {p}: `{wrappers.paths[p]}\'')

    if save:
        wrappers.paths.save(dest)
        click.echo(f'Application paths saved to {wrappers.paths.fname}')

    if delete_user:
        wrappers.paths.delete_user()

#### just display version ##############################################

@main.command()
def version():
    click.echo(__version__)

#### display more information ##########################################

@main.command()
def infos():
    """
    Display information on EggLib installation.
    """

    click.echo(f'EggLib version {__version__}')
    click.echo(f'Installation path: {wrappers.__path__[0]}')
    click.echo(f'External application configuration file: {wrappers.paths.fname}')
    click.echo(f'debug flag: {config.debug:d}')
    click.echo(f'htslib flag: {config.htslib:d}')
    click.echo(f'version of muscle: {wrappers.paths.get("muscle").config["version"]}')
