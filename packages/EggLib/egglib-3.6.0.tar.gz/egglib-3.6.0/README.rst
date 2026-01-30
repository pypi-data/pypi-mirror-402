.. image:: https://egglib.org/_static/banner.png
   :target: https://egglib.org
   :alt: EggLib Logo

|PythonVersions| |PypiPackage|

.. contents:: Table of Contents
   :depth: 3


About
=====

EggLib is a Python library, largely implemented in C++, for evolutionary
genetics and genomics. Main features are sequence data management,
sequence polymorphism analysis, and coalescent simulations. EggLib is a
flexible Python module with a performant underlying C++ library and
allows fast and intuitive development of Python programs and scripts.

**EggLib home page:** `<https://www.egglib.org>`_


Installation
============

EggLib is available on pip. For more information on installing EggLib or
downloading source code please refer to the installation section of the
documentation: `<https://egglib.org/install.html>`_.

Cloning
=======

You can clone the whole package using::

    git clone https://gitlab.com/demita/egglib.git

For example, this lets you access to the current version on development::

    cd egglib
    git checkout dev

Building local documentation
============================

To generate the documentation locally, you should clone the repository,
install EggLib and the python-sphinx package, and run this::

    python -m sphinx doc/ ../doc

The first argument is the location of the ``doc`` directory within the
EggLib package. The second argument is the destination of the generated
documentation. ``../doc`` is just an example.

Citation
========

Siol M., T. Coudoux, S. Ravel and S. De Mita. 2022. EggLib 3: A python package for population genetics and genomics.
*Mol Ecol. Res.* **22**:3176-3187. `<https://doi.org/10.1111/1755-0998.13672>`_

License
=======

EggLib is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version.

EggLib is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

`<https://www.egglib.org/licence.html>`_

.. |PythonVersions| image:: https://img.shields.io/badge/python-3.10+-blue.svg
   :target: https://www.python.org/downloads
   :alt: Python 3.10+

.. |PypiPackage| image:: https://badge.fury.io/py/EggLib.svg
   :target: https://pypi.org/project/EggLib
   :alt: PyPi package
