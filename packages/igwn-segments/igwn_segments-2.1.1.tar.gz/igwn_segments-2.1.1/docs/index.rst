#############
igwn-segments
#############

|pypi-version| |license| |python-versions|

.. |pypi-version| image:: https://badge.fury.io/py/igwn-segments.svg
   :target: http://badge.fury.io/py/igwn-segments

.. |license| image:: https://img.shields.io/pypi/l/igwn-segments.svg
   :target: https://choosealicense.com/licenses/gpl-3.0/

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/igwn-segments.svg
   :target: http://badge.fury.io/py/igwn-segments

.. automodule:: igwn_segments

.. admonition:: This is a fork of ligo-segments
    :class: seealso

    This project is a fork of
    `ligo-segments <https://git.ligo.org/lscsoft/ligo-segments>`__,
    authored by Kipp Cannon and distributed under the GPLv3 license.

============
Installation
============

.. tab-set::
    .. tab-item:: Conda

        .. code-block:: bash

            conda install -c conda-forge igwn-segments

    .. tab-item:: Debian Linux

        .. code-block:: bash

            apt-get install python3-igwn-segments

        See the IGWN Computing Guide software repositories entry for
        `Debian <https://computing.docs.ligo.org/guide/software/debian/>`__
        for instructions on how to configure the required
        IGWN repositories.

    .. tab-item:: Pip

        .. code-block:: bash

            python -m pip install igwn-segments

    .. tab-item:: Scientific Linux

       .. code-block:: bash

           dnf install python3-igwn-segments

       See the IGWN Computing Guide software repositories entries for
       `Rocky Linux 8 <https://computing.docs.ligo.org/guide/software/rl8/>`__
       and other distributions for instructions on how to configure the
       required IGWN repositories.

=============
Documentation
=============

Classes
-------

.. automodsumm:: igwn_segments
    :caption: Classes
    :toctree: api

Modules
-------

.. toctree::
    :caption: Modules
    :hidden:

    igwn_segments.utils

.. currentmodule:: None
.. autosummary::

    igwn_segments.utils
