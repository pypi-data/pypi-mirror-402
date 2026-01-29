.. _getting-started-pepkit:

Getting Started
===============

Welcome! This guide helps you install **PepKit** and run a quick sanity check.

.. contents:: On this page
   :local:
   :depth: 2

What is PepKit?
---------------

**PepKit** is a small toolbox for **peptide-centric computational workflows**, covering
representation conversion, dataset preparation, structure post-processing,
and complex-quality evaluation.

It supports:

- Conversion between peptide representations (**FASTA / sequence ⇄ SMILES**)
- Standardization and filtering of peptide datasets
- Computation of peptide properties and descriptors for machine learning
- Querying protein–peptide complexes from the Protein Data Bank using
  user-defined constraints (e.g. release date)
- Post-processing of **AlphaFold-Multimer** outputs
- External rescoring of predicted complexes (``pDockQ``, ``pDockQ2``, ``MPDockQ``)
- Computation of **``DockQ``** when a native (experimental) complex is available

.. figure:: ../data/Figure/pepkit.png
   :align: center
   :width: 90%
   :alt: PepKit workflow overview


TL;DR install
-------------

.. code-block:: bash

   pip install pepkit

Verify installation
-------------------

.. code-block:: bash

   python -c "import pepkit; print(pepkit.__version__)"

If that prints a version string, you're good.

Recommended: use a virtual environment
--------------------------------------

Creating an isolated environment prevents dependency conflicts.

**Option A — venv (cross-platform)**

.. code-block:: bash

   python3 -m venv pepkit-env
   source pepkit-env/bin/activate    # Linux/macOS
   pepkit-env\Scripts\activate       # Windows PowerShell

**Option B — conda**

.. code-block:: bash

   conda create -n pepkit-env python=3.11
   conda activate pepkit-env

Support
-------

If you hit an issue:

- Report bugs and feature requests on GitHub: `PepKit Issues <https://github.com/Vivi-tran/PepKit/issues>`_
- Check the :doc:`api` section for complete function/class references.
