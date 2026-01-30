import pathlib, re, glob, os
import setuptools, sysconfig
from setuptools.command.build_ext import build_ext

##### GET ENVIRONMENT VARIABLES ########################################
    # get egglib installation options (at some point, we should be able to use the --config-settings option)

DEBUG = os.environ.get('DEBUG', '0')
if DEBUG not in ['0', '1']:
    raise ValueError(f'invalid value for DEBUG: {DEBUG} (accepted values are 0 and 1)')

HTSLIB = os.environ.get('HTSLIB', '2')
if HTSLIB not in ['0', '1', '2']:
    raise ValueError(f'invalid value for HTSLIB: {HTSLIB} (accepted values are 0, 1, 2)')

##### OVERRIDE BUILD_EXT COMMAND #######################################

class build_ext2(build_ext):
    def run(self):
        # get the build path (there should be a better way to get it!)
        build_path = str(pathlib.Path(self.get_ext_fullpath('libegglib')).parent / 'egglib')
        self.library_dirs.append(build_path)

        # build extensions
        super().run()

    def build_extension(self, ext):
        # build an individual extension
        if HTSLIB == '2' and ext.name == 'egglib.io._vcfparser':
            try:
                super().build_extension(ext)
            except setuptools.errors.CompileError as e:
                if HTSLIB == '2' and ext.name == 'egglib.io._vcfparser':
                    print('error ignored:\n', str(e))
                    return
        else:
            super().build_extension(ext)

##### EXTENSION MODULES ################################################

lib = 'egglib' + str(pathlib.Path(sysconfig.get_config_var('EXT_SUFFIX')).stem)
cpath = pathlib.Path('src', 'cfiles')
cpppath = pathlib.Path('src', 'cppfiles')

def filelist(path, names, ext):
    return [path.joinpath(i).with_suffix(ext) for i in libfiles]

libegglib = setuptools.Extension('egglib.libegglib',
                    sources = [str(cpath.joinpath(n).with_suffix('.c')) for n in ['random']],
                    language='c')

random = setuptools.Extension('egglib.random',
                    sources = [str(cpath.joinpath('randomwrapper').with_suffix('.c'))],
                    language='c',
                    libraries = [lib],
                    extra_link_args = ["-Wl,-rpath=$ORIGIN/."])

binding = setuptools.Extension('egglib._eggwrapper',
                    sources=glob.glob(str(pathlib.Path(cpppath, '*.cpp'))),
                    language='c++',
                    swig_opts=['-python', '-c++', '-builtin', '-Wall'],
                    include_dirs = [cpath],
                    libraries = [lib],
                    extra_link_args = ["-Wl,-rpath=$ORIGIN/."])

extensions = [libegglib, binding, random]
if HTSLIB != '0':
    vcf = setuptools.Extension('egglib.io._vcfparser',
                        sources = [str(cpath.joinpath('vcfwrapper').with_suffix('.c'))],
                        language='c',
                        libraries = [lib, 'hts'],
                        extra_link_args = ["-Wl,-rpath=$ORIGIN/.."])
    extensions.append(vcf)

# set DEBUG mode
if DEBUG == '0':
    for ext in extensions: ext.extra_compile_args.extend(['-g', '-O3'])
else:
    for ext in extensions:
        ext.extra_compile_args.extend(['-g', '-O0'])
        ext.define_macros.append(('DEBUG', 1))

##### MAIN PACKAGE #####################################################

pkg_list = ['egglib',
            'egglib.cli',
            'egglib.test',
            'egglib.test.data',
            'egglib.test.base',
            'egglib.test.coalesce',
            'egglib.test.stats',
            'egglib.test.tools',
            'egglib.test.io',
            'egglib.test.wrappers',
            'egglib.coalesce',
            'egglib.io',
            'egglib.stats',
            'egglib.tools',
            'egglib.wrappers']

setuptools.setup(
    cmdclass={'build_ext': build_ext2},
    package_dir={'egglib': os.path.join(r'src', 'egglib')},
    packages=pkg_list,
    package_data={
        'egglib.wrappers': ['apps.conf'],
        'egglib.test.data': ['*.fas', '*.fa', '*.gb', '*.txt',
                             '*.gff3', '*.sta', '*.gnl', '*.fg',
                             '*.aln', '*.vcf', '*.vcfi', '*.bed',
                             '*.hap', '*.inp', '*.gpop', '*.cds',
                             '*.asnb', '*.bcf', '*.clu', '*.tree']},
    ext_modules=extensions
)
