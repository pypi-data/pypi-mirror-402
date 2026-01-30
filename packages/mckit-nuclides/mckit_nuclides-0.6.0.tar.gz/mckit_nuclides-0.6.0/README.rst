==============================================================================
*mckit-nuclides*: tables with information on elements and nuclides
==============================================================================



|Maintained| |License| |Versions| |PyPI| |Docs|

.. contents::


Description
-----------

The module presents basic information on chemical elements and nuclides including natural presence.
The data is organized as `Polars <https://pola.rs/>`_ tables.
Polars allows efficient data joining and selecting on huge datsets produced in `computations like [1]`_.

More details in documentation_.


Contributing
------------

.. image:: https://github.com/MC-kit/mckit-nuclides/workflows/Tests/badge.svg
   :target: https://github.com/MC-kit/mckit-nuclides/actions?query=workflow%3ATests
   :alt: Tests
.. image:: https://codecov.io/gh/MC-kit/mckit-nuclides/branch/master/graph/badge.svg?token=wlqoa368k8
  :target: https://codecov.io/gh/MC-kit/mckit-nuclides
.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
   :target: https://github.com/astral-sh/ruff
.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
   :target: https://github.com/astral-sh/uv


Some specific: in development environment we use uv_, just_, ruff_.

To setup development environment, run:

.. code-block:: shell

  just install | reinstall

To build documentation, run:

.. code-block:: shell

   just docs        # - for local online docs rendering, while editing 
   just docs-build  # - to build documentation 

To release, run:

.. code-block:: shell

  just bump [major|minor|patch]  # - in `devel` branch
  
Then merge devel to master (via Pull Request) and if all the checks are passed create Release. Manually.


Notes
-----

Half lives are extracted from [5].

.. ... with /home/dvp/.julia/dev/Tools.jl/scripts/extract-half-lives.jl (nice script by the way).

References
----------

1. Y. Chen and U. Fischer, 
   “Rigorous mcnp based shutdown dose rate calculations: computational scheme, verification calculations and application to ITER”
   Fusion Engineering and Design, vol. 63–64, pp. 107–114, Dec. 2002, doi: 10.1016/S0920-3796(02)00144-8.
2. Kim, Sunghwan, Gindulyte, Asta, Zhang, Jian, Thiessen, Paul A. and Bolton, Evan E..
   "PubChem Periodic Table and Element pages: improving access to information on chemical
   elements from authoritative sources" Chemistry Teacher International, vol. 3, no. 1, 2021, pp. 57-65.
   https://doi.org/10.1515/cti-2020-0006
3. Elements table. https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/CSV
4. Coursey, J.S., Schwab, D.J., Tsai, J.J., and Dragoset, R.A. (2018-06-14),
   Atomic Weights and Isotopic Compositions (version 4.1). [Online]
   Available: http://physics.nist.gov/Comp [year, month, day].
   National Institute of Standards and Technology, Gaithersburg, MD.
5. JEFF-3.3 radioactive decay data file https://www.oecd-nea.org/dbdata/jeff/jeff33/downloads/JEFF33-rdd_all.asc
   



.. Links

.. _documentation: https://mckit-nuclides.readthedocs.io/en/latest
.. _`computations like [1]`: https://linkinghub.elsevier.com/retrieve/pii/S0920379602001448 
.. _uv: https://github.com/astral-sh/uv
.. _just: https://github.com/casey/just
.. _ruff: https://github.com/astral-sh/ruff


.. Substitutions

.. |Maintained| image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg
   :target: https://github.com/MC-kit/mckit-nuclides/graphs/commit-activity
.. |Tests| image:: https://github.com/MC-kit/mckit-nuclides/workflows/Tests/badge.svg
   :target: https://github.com/MC-kit/mckit-nuclides/actions?workflow=Tests
   :alt: Tests
.. |License| image:: https://img.shields.io/github/license/MC-kit/mckit-nuclides
   :target: https://github.com/MC-kit/mckit-nuclides
.. |Versions| image:: https://img.shields.io/pypi/pyversions/mckit-nuclides
   :alt: PyPI - Python Version
.. |PyPI| image:: https://img.shields.io/pypi/v/mckit-nuclides
   :target: https://pypi.org/project/mckit-nuclides/
   :alt: PyPI
.. |Docs| image:: https://readthedocs.org/projects/mckit-nuclides/badge/?version=latest
   :target: https://mckit-nuclides.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
