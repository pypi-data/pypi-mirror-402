"""
    Copyright 2023 Stéphane De Mita, Mathieu Siol, Thomas Coudoux

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

import click, pkgutil, pathlib, unittest
from .. import test
from ..test.stats import test_cstats

@click.command(no_args_is_help=True)
@click.option('-b', '--base', is_flag=True, help='run top-level tests')
@click.option('-i', '--io', is_flag=True, help='run io module tests')
@click.option('-t', '--tools', is_flag=True, help='run tools module tests')
@click.option('-s', '--stats', is_flag=True, help='run stats module tests')
@click.option('-c', '--coalesce', is_flag=True, help='run coalesce module tests')
@click.option('-w', '--wrappers', is_flag=True, help='run wrappers module tests')
@click.option('-k', '--custom', type=str, multiple=True, default=[], help='add individual test units')
@click.option('-a', '--all', 'all_', is_flag=True, help='equivalent to -bitscw')
@click.option('-m', '--most', is_flag=True, help='equivalent to -bitsc')
@click.option('--muscle3', is_flag=True, help='test muscle3 rather than muscle5 (if both toggled)')
@click.option('--skip-vcf', is_flag=True, help='skip tests of VCF (dependency on HTSlib)')
@click.option('-L', '--list', 'list_', is_flag=True, help='display list of selected test units')
@click.option('-S', '--stop', is_flag=True, help='stop at first failed test')
@click.option('-e', '--error', is_flag=True, help='terminate with an error if tests don\'t pass')
@click.option('-o', '--output', help='file where to save error messages', type=click.File('w'), default=None)
@click.option('-r', '--stats-report', help='validation of statistics against expectations', type=click.File('w'), default=None)
def main(base, io, tools, stats, coalesce, wrappers, custom, all_, most, muscle3, skip_vcf, list_, stop, error, output, stats_report):
    """
    Run test suite

    If the option --list is specified, the list of selected test units
    is diplayed but no tests are actually run. By default (if no
    selection is specified with other options), the full list of test
    units is displayed.
    """

    # launch stats validation
    if stats_report:
        obj = test_cstats.Statistics_test()
        obj.setUp()
        obj._run_test(stats_report)

    # import all test classes from the test subpackage
    unit_mapping = {}
    group_mapping = {}
    for package in pkgutil.walk_packages(test.__path__):
        group_mapping[package.name] = {}
        for module in pkgutil.walk_packages([str(pathlib.Path(test.__path__[0]) / package.name)]):
            if module.ispkg: raise RuntimeError('problem with test package structure: subpackage found')
            spec = module.module_finder.find_spec(module.name)
            m = spec.loader.load_module()
            for n in dir(m):
                if n[-5:] == '_test':
                    cls = getattr(m, n)
                    if not issubclass(cls, unittest.TestCase):
                        raise RuntimeError(f'problem with test package structure: {module.name}.{n} is not a TestCase subclass')
                    name = n[:-5]
                    if name in unit_mapping:
                        raise RuntimeError(f'problem with test package structure: test unit name {name} repeated')
                    unit_mapping[name] = [package.name, cls]
                    group_mapping[package.name][name] = cls
                    
    # activate all module flags is 'all' is switched on
    if most or all_:
        base = True
        io = True
        tools = True
        stats = True
        if all_:
            wrappers = True

    # include whole requested module tests
    tests = {}
    for name, boolean in [('base', base),
                 ('io', io),
                 ('tools', tools),
                 ('stats', stats),
                 ('coalesce', coalesce),
                 ('wrappers', wrappers)]:
        if boolean: tests[name] = group_mapping[name]

    # include individual units
    for unit in custom:
        try:
            package, cls = unit_mapping[unit]
        except KeyError:
            raise RuntimeError(f'invalid test unit: {unit}')
        if package not in tests: tests[package] = {}
        tests[package][unit] = cls

    # exclude VCF if requested (and present)
    if skip_vcf and 'io' in tests and 'VCF' in tests['io']:
        del tests['io']['VCF']

    # choose muscle3 rather than muscle 5 if requested
    if 'wrappers' in tests and 'muscle3' in tests['wrappers'] and 'muscle5' in tests['wrappers']:
        if muscle3: del tests['wrappers']['muscle5']
        else: del tests['wrappers']['muscle3']

    # list
    if list_:
        if len(tests) == 0:
            tests = group_mapping
        for grp, units in tests.items():
            click.echo(click.style(grp, bold=True))
            for name, unit in units.items():
                click.echo(f'    {name}')

    # perform tests
    elif len(tests):
        suite = unittest.TestSuite()
        for package, units in tests.items():
            for name, cls in units.items():
                suite.addTests(
                    unittest.defaultTestLoader.loadTestsFromTestCase(cls))
        runner = unittest.TextTestRunner(stream=None, verbosity=2,
            failfast=stop)
        results = runner.run(suite)

        # report
        click.echo(f'num tests.............{results.testsRun:.>5d}')
        click.echo(f'errors................{len(results.errors):.>5d}')
        click.echo(f'failures..............{len(results.failures):.>5d}')
        click.echo(f'skipped...............{len(results.skipped):.>5d}')
        click.echo(f'expected failures.....{len(results.expectedFailures):.>5d}')
        click.echo(f'unexpected successes..{len(results.unexpectedSuccesses):.>5d}')
        click.echo(f'stop option...........{int(results.failfast):.>5d}')
        click.echo( 'result:................', nl=False)
        if results.wasSuccessful(): msg = 'pass'; c = 'green'
        else: msg = 'fail'; c = 'red'
        click.echo(click.style(msg.rjust(4, '.'), bold=True, fg=c))

        if output:
            for k in ['errors', 'failures', 'skipped', 'expectedFailures', 'unexpectedSuccesses']:
                items = getattr(results, k)
                h = f'{k}: {len(items)}'
                output.write('=' * len(h) + '\n')
                output.write(h + '\n')
                output.write('=' * len(h) + '\n\n')
                for case, message in items:
                    name = str(case)
                    output.write(name + '\n')
                    output.write('-' * len(name) + '\n')
                    output.write(message + '\n')

        if not results.wasSuccessful() and error:
            raise click.ClickException('tests finished with fail status')
