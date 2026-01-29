Dock
====

PepKit provides wrappers/utilities for running peptide docking and refinement with **Rosetta**, plus helpers for extracting and analyzing scorefiles.

.. contents:: On this page
   :local:
   :depth: 2

At a glance
-----------

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - **Run/refine**
     - Batch Rosetta refinement docking (prepack + refine)
   * - **Postprocess**
     - Parse scorefiles, aggregate across folders, select the best complex

Prerequisites
-------------

.. warning::

   Rosetta is distributed separately and may require licensing depending on your use case.
   PepKit assumes you already have Rosetta installed and accessible on your system.

You typically need:

- A Rosetta `main` folder (binaries)
- A Rosetta `database` folder
- Input PDBs (one complex per file)

Rosetta refinement (batch)
--------------------------

Use ``refinement_multiple_dock`` to launch Rosetta's refinement protocol on multiple PDB files.

**Function signature**

.. code-block:: text

   refinement_multiple_dock(
       path_to_main,
       path_to_db,
       pdb_dir,
       prepack_out,
       refinement_out,
       nstruct=1,
   )

**Parameters**

- ``path_to_main``: path to Rosetta ``main`` directory
- ``path_to_db``: path to Rosetta ``main/database``
- ``pdb_dir``: directory containing input PDB files
- ``prepack_out``: output directory for prepacked structures
- ``refinement_out``: output directory for refined complexes
- ``nstruct``: number of output structures per input (default: 1)

**Example**

.. code-block:: python

    from pepkit.dock.rosetta.refinement_dock import refinement_multiple_dock
    from pepkit.examples import rosetta_data

    pdb_dir = rosetta_data.get_rosetta_ex_path()

    refinement_multiple_dock(
        path_to_main="/path/to/rosetta/main",
        path_to_db="/path/to/rosetta/main/database",
        pdb_dir=pdb_dir,
        prepack_out="data/rosetta_test/prepack",
        refinement_out="data/rosetta_test/refinement",
        nstruct=1,
    )

.. tip::

   A simple project layout that scales well:

   .. code-block:: text

      project/
      ├── input_pdbs/
      ├── rosetta/
      │   ├── prepack/
      │   └── refinement/
      └── analysis/

Score extraction utilities
--------------------------

Utilities for reading, converting, and analyzing Rosetta docking scorefiles:

- ``read_and_convert(scorefile)``: read a single Rosetta scorefile into a DataFrame
- ``extract_score(score_dir)``: aggregate all scorefiles in a directory into a DataFrame
- ``get_optimal_clx(df)``: get the optimal complex (e.g., lowest energy score) from a DataFrame

**Example**

.. code-block:: python

    import os
    from pepkit.dock.rosetta.score import read_and_convert, extract_score, get_optimal_clx
    from pepkit.examples import rosetta_data

    test_dir = rosetta_data.get_refinement_path()
    test_score = os.path.join(test_dir, "complex_1", "docking_scores.sc")

    df = read_and_convert(test_score)
    print(df.head())

    df_all = extract_score(test_dir)
    print(df_all.head())

    opt = get_optimal_clx(df)
    print("Optimal structure:", opt)

Typical workflow
----------------

1. Run refinement docking using ``refinement_multiple_dock``.
2. Aggregate scorefiles with ``extract_score``.
3. Select the best structure with ``get_optimal_clx``.
4. (Optional) join docking results with your dataset metadata.

See also
--------

- :doc:`metrics` — evaluate docking models/predictions
- :doc:`api` — full reference for :mod:`pepkit.dock`
