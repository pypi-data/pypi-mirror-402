API Reference
=============

This page contains the full API reference generated from docstrings.
If you are new to PepKit, start with :doc:`getting_started` and the module guides.

.. contents:: On this page
   :local:
   :depth: 2

Module map
----------

.. list-table::
   :widths: 25 75
   :header-rows: 0

   * - :doc:`chem`
     - Parsing/standardization, conversion, properties, descriptors
   * - :doc:`query`
     - Fetch, constraint-based filtering


Chem Module
-----------

Conversion (:mod:`pepkit.chem.conversion.conversion`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Tools for parsing peptide representations (FASTA/SMILES), standardizing sequences, and filtering non-canonical FASTA records.

.. automodule:: pepkit.chem.conversion.conversion
   :members:
   :undoc-members:
   :show-inheritance:

Descriptor (:mod:`pepkit.chem.desc.descriptor`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Calculation of molecular descriptors and physicochemical properties.

.. automodule:: pepkit.chem.desc.descriptor
   :members:
   :undoc-members:
   :show-inheritance:

Standardize (:mod:`pepkit.chem.standardize`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Utilities for standardizing peptide sequences and molecular representations.

.. automodule:: pepkit.chem.standardize
   :members:
   :undoc-members:
   :show-inheritance:


Query Module
------------

Request (:mod:`pepkit.query.request`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: pepkit.query.request.retrieve_pdb
   :noindex:

Filter (:mod:`pepkit.query.filter`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: pepkit.query.filter.validate_complex_pdb
   :noindex:

.. autofunction:: pepkit.query.filter.validate_complex_pdbs
   :noindex:

Constraint-based query (:mod:`pepkit.query.query`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: pepkit.query.query.query
   :noindex:

Modelling Module
----------------

Analysis (:mod:`pepkit.modelling.af.post.analysis`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: pepkit.modelling.af.post.analysis
   :members:
   :undoc-members:
   :show-inheritance:
