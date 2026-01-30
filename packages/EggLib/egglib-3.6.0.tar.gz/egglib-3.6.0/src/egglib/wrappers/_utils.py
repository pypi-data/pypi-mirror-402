"""
    Copyright 2016-2023 Stephane De Mita, Mathieu Siol

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

import os, re, tempfile, shutil, pathlib, platformdirs
from .. import _interface

#### write sequences down a file #######################################

def _write_sample(obj, fname):
    if not isinstance(obj, (_interface.SampleView, str)): raise TypeError('invalid type for `obj` argument')
    f = open(fname, 'w')

    if isinstance(obj, _interface.SampleView):
        name = obj[0]
        sequence =list(obj[1].string())
        f.write('>{0}\n'.format(name))
        for j in range(0, len(sequence), 60):
            f.write(''.join(sequence[j:j+60]) + '\n')
    elif isinstance(obj, str):
        sequence =list(obj)
        f.write('>String_to_fasta\n')
        for j in range(0, len(sequence), 60):
            f.write(''.join(sequence[j:j+60]) + '\n')
    f.close()

def _write(obj, fname, mapping):
    f = open(fname, 'w')
    for i, sam in enumerate(obj):
        n = 'seq-{0}'.format(len(mapping) + 1)
        f.write('>{0}\n'.format(n))
        for j in range(0, len(sam.sequence), 100):
            f.write(sam.sequence[j:j+100] + '\n')
        mapping[n] = sam
    f.close()

#### decorator running a function in a temp directory ##################

_protect_path_mapping = {}
def _protect_run(f):
    """
    This function is designed to be a decorator for wrapper functions.
    It runs the argument function into a temporary directory, ensuring
    that the temporary directory is deleted after completion of the
    function.
    """
    def _f(*args, **kwargs):
        tmp = None
        curr = os.getcwd()
        try:
            tmp = tempfile.mkdtemp()
            _protect_path_mapping[tmp] = curr
            os.chdir(tmp)
            return f(*args, **kwargs)
        finally:
            os.chdir(curr)
            if tmp is not None:
                shutil.rmtree(tmp)
            del _protect_path_mapping[tmp]
    _f.__name__ = f.__name__
    _f.__doc__ = f.__doc__
    return _f

#### external application paths manager ################################

class _Paths(object):
    """
    Class (designed to be a singleton) holding external applications.
    Each application is represented by an _App instance. Instances are
    iterable (iteration over application keys instances). Paths can be
    set/accessed through the [] operator.
    """

    def __init__(self):
        self._fname_g = pathlib.Path(__file__).parent / 'apps.conf'
        self._fname_u = platformdirs.user_config_path(appname='EggLib') / 'apps.conf'

        if self._fname_u.is_file():
            self._fname = self._fname_u
        else:
            if not self._fname_g.is_file(): raise RuntimeError('apps.conf file not found')
            self._fname = self._fname_g
        self._apps = {}

    @property
    def fname(self):
        """
        Location of the configuration file.
        """
        return self._fname

    def _add(self, app):
        """
        Add an application wrapper.

        :param app: a :class:`._App` instance.
        :param key: the application's name.
        :param default: the default path.
        """
        self._apps[app._key] = app

    def __iter__(self):
        for i in self._apps:
            yield i

    def __getitem__(self, app):
        if app not in self._apps: raise ValueError('invalid application name: {0}'.format(app))
        return self._apps[app].get_path()

    def get(self, app, default=None):
        """
        Get the _App object corresponding to an application key. If key
        doesn't exist return default value otherwise raise a KeyError.
        """
        try: return self._apps[app]
        except KeyError: return default

    def __setitem__(self, app, path):
        if app not in self._apps: raise ValueError('invalid application name: {0}'.format(app))
        self._apps[app].set_path(path, True)

    def autodetect(self, verbose=False):
        """
        Try to set all paths using default values. Applications who are
        currently configured are skipped.
        """
        failed = {}
        passed = 0
        skipped = 0
        n = len(self._apps)
        sz = len(str(n))
        if verbose:
            print('Detecting external applications: ' + '0'.rjust(sz) + '/' + str(n), flush=True, end='')
        for key, app in self._apps.items():
            if app.get_path() is not None:
                skipped += 1
                if verbose:
                    print('\b'*(2*sz+1) + str(passed+skipped+len(failed)).rjust(sz) + '/' + str(n), flush=True, end='')
                continue
            result = app.set_path(app._default, False)
            if result is None:
                passed += 1
            else:
                failed[key] = app._default, result
            if verbose:
                print('\b'*(2*sz+1) + str(passed+skipped+len(failed)).rjust(sz) + '/' + str(n), flush=True, end='')
        if verbose:
            print('\b'*(2*sz+1) + str(passed).rjust(sz) + '/' + str(n) + f' passed, {skipped} skipped')
            for k, (cmd, msg) in failed.items():
                print(k, ' [', cmd, ']: ', msg, sep='')
        return passed, len(failed), failed

    def save(self, dest=None):
        """
        Save current configuration to configuration file (requires
        administrator rights if the file is located in a protected
        location).

        :param dest: if 'global', force save to global path (within the
            EggLib distribution). If 'user', force save as user config
            file. All other values (default), same as when loading.
        """
        if dest == 'global':
            self._fname = self._fname_g
        elif dest == 'user':
            self._fname_u.parent.mkdir(parents=True, exist_ok=True)
            self._fname = self._fname_u
        try:
            f = open(self.fname, 'w')
        except IOError as e:
            if e.errno == 13: raise ValueError('administrator rights are required')
            else: raise
        for app in self._apps.values(): app.save(f)
        f.close()

    def load(self):
        """
        Load configuration from the persistent file.
        """
        f = open(self.fname)
        for linenum, line in enumerate(f):
            line = line.strip()
            if line == '': continue         # support empty lines
            if line.lstrip()[0] == '#': continue     # support comment lines
            if (mo := re.fullmatch(r'([a-z]+?):[ \t]*(.+)\s*', line)) is None:
                raise RuntimeError('invalid file `apps.conf` (line {0})'.format(linenum+1))
            key, rvalue = mo.groups()
            if key not in self._apps: raise RuntimeError('invalid file `apps.conf` (unknown application: {0})'.format(key))
            self._apps[key].load(rvalue, linenum)
        f.close()

    def __str__(self):
        return str(dict([(i, j.get_path()) for (i,j) in self._apps.items()]))

    def as_dict(self):
        """
        Return configuration as a new dict instance.
        """
        return dict([(i, j.get_path()) for (i,j) in self._apps.items()])

    def clear(self):
        """
        Set all paths to None
        """
        for p in self._apps.values():  p.zero()

    def delete_user(self):
        """
        Delete user configuration. The installation will fall back to
        the default configuration file present in EggLib's installation
        directory.
        """
        self._fname_u.unlink(missing_ok=True)

class _App(object):
    def __init__(self, key, default):
        self._path = None
        self._key = key
        self._default = default
        self.config = {} # option values (only if path is specified)
        self.options = {}

    def add_option(self, **args):
        self.options[args['name']] = args
        self.config[args['name']] = args['default']

    def get_path(self):
        """ Get the application path. """
        return self._path

    def set_path(self, path, critical):
        """
        Set the application path. The path is set if the check function
        (to be implemented as _check_path) succeeds. If it fails, a
        :exc:`~.exceptions.ValueError` is raised (if *critical* is
        ``True``), or the path is set to ``None`` and the error message
        string is returned (otherwise).
        """
        if path is None:
            self._path = None
            self.config = { opt['name']: opt['default'] for opt in self.options.values() }
        else:
            result = self._check_path(path, self.config) # _check_path is responsible of setting options
            if result is None: self._path = path
            elif critical: raise ValueError('cannot set path for {0}: {1}'.format(self._key, result))
            else: return result

    def _set_options(self, options, key):
        if (diff := set(options) - set(self.options)) != set(): raise ValueError('unexpected option(s): {",".join(diff)}')
        for o in set(self.options) - set(options):
            self.config[o] = self.options[o][key]()
        for o, v in options.items():
            try:
                self.config[o] = self.options[o]['f_convert'](v)
            except ValueError:
                raise ValueError(f'invalid option value for option {o}: {v}')

    def set_path_force(self, path, **options):
        """
        Set path without performing the check function.
        """
        self._set_options(options, 'f_set_missing')
        self._path = path

    def save(self, f):
        """
        Write app configuration in file-like object.
        """
        if self._path is None:
            f.write(f'{self._key}: *\n')
        else:
            f.write('{0}: {1}'.format(self._key, self._path))
            if len(self.config) == 0: f.write('\n')
            else:
                for k, v in self.config.items(): f.write(f' ${k}={v}')
                f.write('\n')

    def load(self, string, num):
        """
        Import app configuration from string.
        """
        if (mo := re.fullmatch(r'((?![ \$]).+?)[ \t]*(\$.+)?', string)) is None:
            raise RuntimeError('invalid file `apps.conf` (line {0})'.format(num+1))
        path, options = mo.groups()
        if path == '*':
            self._path = None
        else:
            self._path = path
            if options is not None: options = {k: v for k, v in re.findall(r'\$(\w+)=(\w+)', options)}
            else: options = {}
            self._set_options(options, 'f_load_missing')

    def zero(self):
        """
        Set path to None
        """
        self._path = None
        for k in self.config:
            self.config[k] = self.options[k]['default']

    key = property(lambda self: self._key, doc='key of the object _App')

paths = _Paths()
