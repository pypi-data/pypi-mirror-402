************
Installation
************

This page describes the installation procedure of EggLib.

------------
Requirements
------------

EggLib works with Python 3.10 and above. Binary distributions are not
currently available.

To compile EggLib from source, you'll need the development libraries for
your version of Python and possibly the ``htslib`` library (see below).

For using any function of the :ref:`wrappers <wrappers>` module, the
corresponding program must be found in your system and EggLib should be
configured accordingly (see :ref:`paths`).

Other requirements are Python packages ``click`` and ``platformdirs``
for the main package, and additional packages for generating
documentation and running tests. They can all be processed easily by
using the package manager **pip**.

Dependency on ``htslib``
========================

The class :class:`~.io.VCF` requires the ``htslib`` external `library
<https://www.htslib.org/download/>`_ with its headers. On major
distributions, ``htslib`` can be installed from the package manager
(under the name ``htslib-devel`` or ``libhts-dev`` on Ubuntu). EggLib
relies on the presence of this library in the system to compile. It is
possible to use environment variables to control where the compiler will
find the libraries as in the following example::

    $ export CPATH=$HOME/.local/include:$CPATH
    $ export LD_LIBRARY_PATH=$HOME/.local/lib
    $ export LIBRARY_PATH=$HOME/.local/lib

(these commands may be inserted into a bash configuration file such as
``.bashrc``).

Note that ``htslib`` is only needed for the class :class:`!VCF`. By
default, if ``htslib`` is missing, this class will be skipped. This can
be checked through the ``htslib`` flag available in the output of the
command ``egglib-config infos`` or as the variable
``egglib.config.htslib`` once EggLib is installed.

This behaviour can be controlled through the environment variable
``HTSLIB``, which we recommend to set in the local shell only (i.e. not
using ``export``) as in the following example::

    $ HTSLIB=1 pip install egglib

This variable takes three possible values:

+------+--------------------------+
| Code | Meaning                  |
+======+==========================+
| 0    | don't require ``htslib`` |
+------+--------------------------+
| 1    | require ``htslib``       |
+------+--------------------------+
| 2    | flexible mode (default)  |
+------+--------------------------+

With variable ``HTSLIB=0``, the class :class:`!VCF` is never included.
With variable ``HTSLIB=1``, the class :class:`!VCF` is included if
compilation and linking to the ``htslib`` library succeeds. If not, an
error is displayed. With variable ``HTSLIB=2``, any error occurring
while compiling the class :class:`!VCF` is masked and the class is
silently skipped. So ``HTSLIB=1`` is recommended if :class:`!VCF` is
actually required.

Local installation of ``htslib``
================================

In some cases, it is not possible to install ``htslib``, blocking the
installation of EggLib with VCF support. The following recipe is a way
to overcome installation restrictions and should be considered as a
temporary fix. It has been designed for Linux systems.

We will install ``htslib`` locally within the user's home and add local
folder to dynamic libraries search paths (and other paths, as shown in
the commands below).

Install ``htslib`` locally (under ``~/.local``)
-----------------------------------------------

This installs ``htslib`` version 1.19.1 (the latest version as of this
writing)::

    $ module load compilers/gcc
    $ wget https://github.com/samtools/htslib/releases/download/1.19.1/htslib-1.19.1.tar.bz2
    $ tar xvf htslib-1.19.1.tar.bz2
    $ cd htslib-1.19.1
    $ ./configure --prefix=${HOME}/.local
    $ make
    $ make install 

Configure system to include local libraries
-------------------------------------------

The following lines should be added to ``${HOME}/.bashrc`` or
``${HOME}/.bash_profile``::

    export CPATH=${HOME}/.local/include:${CPATH}
    export LD_LIBRARY_PATH=$HOME/.local/lib:${LD_LIBRARY_PATH}
    export LIBRARY_PATH=${HOME}/.local/lib :${LIBRARY_PATH}

Changes need to applied using::

    $ source ~/.bashrc 

Install EggLib, making sure it is freshly compiled
==================================================

::

    $ pip cache purge
    $ HTSLIB=1 pip --force-reinstall egglib

Validate that it worked (the line ``htslib: 1`` should appear)::

    $ egglib-config infos

------------
Installation
------------

.. highlight:: bash

EggLib is on the `Python Package Index <https://pypi.org/project/EggLib/>`_
and can be installed using **pip** as::

    $ pip install egglib --user

The ``--user`` flag is not needed in most cases. If the permissions
don't allow you to install EggLib in a system-wide location, it will be
installed in local user libraries.

If the ``pip`` command is not directly accessible or if you want to
install EggLib for a specific (non-default) version of Python (for
example, 3.13) you can type::

    $ python3.13 -m pip install egglib --user

or, on Windows, using the Python Launcher::

    py -3.13 -m pip install egglib --user

You can also:

* Select a specific version of EggLib (for example, 3.5.0): 
  ``pip install egglib==3.5.0``.
* Upgrade to the latest version: ``pip install --upgrade egglib``.
* Remove EggLib: ``pip uninstall egglib``.

To generate the documentation, a set of packages are needed which are
not required by default. To install those, specify the ``doc`` extra::

    $ pip install egglib[doc] --user

Similarly, ``scipy`` is needed to run tests. You can either install it
yourself or let ``pip`` install it (or check it presence) as a
dependency of EggLib::

    $ pip install egglib[test] --user

Binary packages
===============

Binary packages (binary wheels) are available on **pip** for MacOSX and
Windows under Python 3.13 or above. **pip** should use the package wheel
corresponding to your system. By default, it will attempt to compile
EggLib (which is the normal behaviour on Linux).

.. note::
    Binary packages are not currently supported and won't be available
    for recent versions of EggLib.

Download source and binary packages
===================================

The source package can be downloaded from **pip** using::

    $ pip download egglib --no-binary :all:

This will download the source package. Letting you access the source 
code.

To download the binary package corresponding to your system (assuming it
is available), you can just type::

    $ pip download egglib

Alternatively, all files for the current release are available for
download from `<https://pypi.org/project/EggLib/#files>`_. Older
releases are also archived there.

.. _apps:

.. note::
    Binary packages are not currently supported and won't be available
    for recent versions of EggLib.

---------------------------------
Configuring external applications
---------------------------------

If external applications are needed (one is required for every function
of the :ref:`wrappers <wrappers>` module), they must be configured. By
default, EggLib will assume that the corresponding programs are absent
and will not attempt to run them.

Since version 3.2, a companion script in included in the Egglib
installation to manage external application paths. To test for the
presence of external applications and save the configuration in a user
configuration file, issue the following command::

    $ egglib-config apps -aLsu

* Option ``-a`` launchs autodetection of applications using default
  command names for invoking them (e.g. ``phyml`` for the PhyML
  software). If needed, for any application, custom commands can be
  specified using the ``-c`` option and path to executables can be
  specified using  ``-p``. If a command tries by ``-a`` doesn't work,
  this application will be left unavailable.

* Option ``-L`` displays the result.

* Option ``-s`` saves the configuration to a persistent file such as the
  new configuration will be used by EggLib after subsequent imports.

* Option ``-u`` specifies that the configuration file will be saved in
  a user-specific configuration file. By default, the configuration file
  is located within the EggLib installation and is erased when EggLib is
  updated and might require administrator rights for writing. If the
  user-specific file exists, it is used in priority (so ``-u`` only
  needs to be specified when it doesn't exist yet).

See the manual (``egglib-config apps --help``) for more information.

It is also possible to perform these operations using helpers of the
:mod:`!wrappers` module, either permanently or temporarily. For details,
see :ref:`paths`.

-----
Tests
-----

Since version 3.2, the test suite is included as a subpackage of EggLib
and can be invoked through a companion script named ``egglib-test``.
The following command will run all tests and assumes all components
(external applications and ``htslib`` for the :class:`.io.VCF` class) are
available::

    $ egglib-test -a

It is possible to run more limited tests (in particular, skip the 
:ref:`wrappers <wrappers>` module). See ``egglib-test --help`` for more 
details.
