Changelog
=========

This page summarizes user-visible changes between releases.

Version 0.0.5
-------------

Highlights
^^^^^^^^^^

- **Chem**
  - FASTA/sequence ⇄ SMILES conversion
  - parsing, validation, standardization
  - descriptor generation for ML workflows

- **Query**
  - fetch PDB entries from RCSB
  - online constraint-based filtering (e.g. quality, release date, residue/ligand checks)

- **Modelling**
  - AlphaFold(-Multimer) post-processing pipeline
  - rescoring with ``pDockQ`` and ``pDockQ2``

Documentation
^^^^^^^^^^^^^

- Added full documentation on Read the Docs: https://pepkit.readthedocs.io/en/latest/

Packaging & dependencies
^^^^^^^^^^^^^^^^^^^^^^^^

- Split optional dependencies to keep the core package lightweight.
  - Install the core package:

    .. code-block:: console

       pip install pepkit

  - Install modelling + PDB-heavy extras:

    .. code-block:: console

       pip install pepkit[modelling]

  - Install everything:

    .. code-block:: console

       pip install pepkit[all]

CLI
^^^

- Exposed a top-level CLI for common workflows.
  - Query and post-processing can now be run directly from the command line.
  - See the documentation for examples and usage details.
