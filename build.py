from pybuilder.core import use_plugin, init, Author

use_plugin('python.core')
use_plugin('python.install_dependencies')
use_plugin('python.distutils')
use_plugin('python.flake8')
use_plugin('python.unittest')
use_plugin('python.coverage')
use_plugin('copy_resources')
use_plugin('python.pytddmon')

default_task = ['analyze', 'publish']

name = 'aws-monocyte2'
version = '0.0.3'
summary = 'Monocyte - Search and Destroy unwanted AWS Resources relentlessly.'
description = """
    Monocyte is a bot for destroying AWS resources in non-EU regions written in Python using Boto.
    It is especially useful for companies that are bound to European privacy laws
    and for that reason don't want to process user data in non-EU regions.
    """
authors = [Author('Jan Brennenstuhl', 'jan@brennenstuhl.me'),
           Author('Arne Hilmann', 'arne.hilmann@gmail.com')]
url = 'https://github.com/ImmobilienScout24/aws-monocyte'
license = 'Apache License 2.0'


@init
def set_properties(project):
    project.set_property("verbose", True)

    project.depends_on("docopt")
    project.depends_on("boto")
    project.depends_on("python-cloudwatchlogs-logging")

    project.build_depends_on("mock")

    project.set_property("flake8_include_test_sources", True)
    project.set_property('coverage_break_build', False)

    project.set_property("install_dependencies_upgrade", True)

    project.set_property('copy_resources_target', '$dir_dist')
    project.get_property('copy_resources_glob').append('setup.cfg')
    project.set_property('dir_dist_scripts', 'scripts')

    project.set_property('distutils_classifiers', [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
        'Topic :: System :: Networking',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration'
    ])


@init(environments='teamcity')
def set_properties_for_teamcity_builds(project):
    import os
    project.version = '%s-%s' % (
        project.version, os.environ.get('BUILD_NUMBER', 0))
    project.default_task = ['install_build_dependencies', 'publish']
    project.set_property(
        'install_dependencies_index_url', os.environ.get('PYPIPROXY_URL'))
    project.set_property('install_dependencies_use_mirrors', False)
    project.set_property('teamcity_output', True)
