.. toctree::
   :hidden:

   igwn-ligolw <self>

###########
igwn-ligolw
###########

|pypi-version| |license| |python-versions|

.. |pypi-version| image:: https://badge.fury.io/py/igwn-ligolw.svg
   :target: http://badge.fury.io/py/igwn-ligolw

.. |license| image:: https://img.shields.io/pypi/l/igwn-ligolw.svg
   :target: https://choosealicense.com/licenses/gpl-3.0/

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/igwn-ligolw.svg
   :target: http://badge.fury.io/py/igwn-ligolw

.. automodule:: igwn_ligolw

.. admonition:: This is a fork of ligo-ligolw
    :class: seealso

    This project is a fork of
    `python-ligo-lw <https://git.ligo.org/kipp.cannon/python-ligo-lw>`__,
    authored by Kipp Cannon and distributed under the GPLv3 license.

============
Installation
============

.. tab-set::
    .. tab-item:: Conda

        .. code-block:: bash

            conda install -c conda-forge igwn-ligolw

    .. tab-item:: Debian Linux

        .. code-block:: bash

            apt-get install python3-igwn-ligolw

        See the IGWN Computing Guide software repositories entry for
        `Debian <https://computing.docs.ligo.org/guide/software/debian/>`__
        for instructions on how to configure the required
        IGWN repositories.

    .. tab-item:: Pip

        .. code-block:: bash

            python -m pip install igwn-ligolw

    .. tab-item:: Scientific Linux

       .. code-block:: bash

           dnf install python3-igwn-ligolw

       See the IGWN Computing Guide software repositories entries for
       `Rocky Linux 8 <https://computing.docs.ligo.org/guide/software/rl8/>`__
       and other distributions for instructions on how to configure the
       required IGWN repositories.

=============
Documentation
=============

.. toctree::
    :caption: Modules
    :maxdepth: 1

    array
    dbtables
    ligolw
    lsctables
    param
    table
    tokenizer
    types
    utils/index
