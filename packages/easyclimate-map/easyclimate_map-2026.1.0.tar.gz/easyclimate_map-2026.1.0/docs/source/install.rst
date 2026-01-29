
.. _install:

Installation Guide
====================================

.. rst-class:: lead

   Install the **easyclimate-map** as a Python package.

----

easyclimate-map is a user-friendly Python package designed to simplify the process of acquiring, 
handling, and visualizing geographic map data for environmental and climate analysis.


package install
---------------

Easyclimate-map is conveniently available as a Python package on PyPI and can be easily
installed using pip and uv.

.. tab-set::
    :class: outline

    .. tab-item:: :iconify:`devicon:pypi` pip

        .. code-block:: bash

            pip install easyclimate-map

    .. tab-item:: :iconify:`material-icon-theme:uv` uv

        .. code-block:: bash

            uv add --dev easyclimate-map


requirements.txt
----------------

If you're tracking dependencies in ``requirements.txt``, you can create a separate
requirements file for your documentation, such as ``requirements-docs.txt``, and
add ``easyclimate-map`` to that file to ensure it is included in your documentation build.

.. tab-set::

    .. tab-item:: Base requirements

        .. literalinclude:: ../../release_requirements.txt

    .. tab-item:: Test requirements

        .. literalinclude:: ../../test_requirements.txt

    .. tab-item:: Docs build requirements

        .. literalinclude:: ../requirements-docs.txt