Modelling
=========

Overview
--------

This module provides utilities to post-process AlphaFold-Multimer predictions,
extract interface features, and rescore complexes with ``pDockQ``/``pDockQ2``.
Typical workflows:

- single model analysis (``single_analysis``)
- per-entry processing across ranked models (``all_analysis``)
- batch processing across many entry folders (``batch_analysis``)

Examples
--------

Single (direct) analysis
^^^^^^^^^^^^^^^^^^^^^^^^

Analyze one predicted model (JSON + PDB):

.. code-block:: python

   from pepkit.modelling.af.post.analysis import Analysis

   a = Analysis(
       json_path="data/examples/7QWV_A_7QWV_B/7QWV_A_7QWV_B_scores_rank_001_alphafold2_multimer_v3_model_3_seed_000.json",
       pdb_path="data/examples/7QWV_A_7QWV_B/7QWV_A_7QWV_B_relaxed_rank_001_alphafold2_multimer_v3_model_3_seed_000.pdb",
       peptide_chain_position="last",
       distance_cutoff=8.0,
   )

   result = a.single_analysis()
   subset = {
       "composite_ptm": result.get("composite_ptm"),
       "pdockq": result.get("pdockq"),
       "pdockq2": result.get("pdockq2"),
   }
   print(subset)

Example output:

.. code-block:: python

   {'composite_ptm': 0.82, 'pdockq': 0.16, 'pdockq2': 0.36}

Per-entry (all ranked models)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Process every ranked model in a folder:

.. code-block:: python

   a = Analysis(peptide_chain_position="last")
   entry_result = a.all_analysis("data/examples/7QWV_A_7QWV_B/")

The returned ``entry_result`` is a dict with per-rank keys (``rank001``, ``rank002`` …)
and meta keys such as ``length`` and ``processing_time``.

Command line usage
------------------

Single entry
^^^^^^^^^^^^

Module invocation:

.. code-block:: console

   python -m pepkit.modelling.af.post.analysis --entry_dir data/examples/7QWV_A_7QWV_B

Installed CLI:

.. code-block:: console

   pepkit postprocess --af-out data/examples/7QWV_A_7QWV_B --single-entry

The command writes ``result.json`` inside the entry directory (``af-out/result.json``).

Example ``af-out/result.json`` (valid JSON; truncated):

.. code-block:: json

   {
     "rank001": {
       "mean_plddt": 83.091,
       "median_plddt": 95.0,
       "peptide_plddt": 78.062,
       "protein_interface_plddt": 87.986,
       "peptide_interface_plddt": 78.062,
       "interface_plddt": 83.024,
       "mean_pae": 8.683,
       "max_pae": 31.312,
       "peptide_pae": 8.837,
       "protein_interface_pae": 6.613,
       "peptide_interface_pae": 8.837,
       "mean_interface_pae": 4.408,
       "pdockq": 0.16,
       "pdockq2": 0.36,
       "composite_ptm": 0.82
     },
     "rank002": {},
     "length": 5,
     "processing_time": 12.3
   }

Batch (multiple entries)
^^^^^^^^^^^^^^^^^^^^^^^^

Module invocation:

.. code-block:: console

   python -m pepkit.modelling.af.post.analysis --batch_dir data/examples

Installed CLI:

.. code-block:: console

   pepkit postprocess --af-out data/examples

The batch run processes all entry folders under the provided directory.

Turning results into a summary table
------------------------------------

Collect ``pDockQ`` / ``pDockQ2`` across ranks and build a DataFrame:

.. code-block:: python

   import json
   import pandas as pd
   from pathlib import Path

   rows = []
   for entry_dir in Path("data/examples").iterdir():
       p = entry_dir / "result.json"
       if not p.exists():
           continue
       data = json.loads(p.read_text())
       for rank_key, record in data.items():
           if not rank_key.startswith("rank"):
               continue
           rows.append({
               "entry": entry_dir.name,
               "rank": rank_key,
               "pdockq": record.get("pdockq"),
               "pdockq2": record.get("pdockq2"),
               "composite_ptm": record.get("composite_ptm"),
           })

   df = pd.DataFrame(rows).sort_values(["entry", "rank"])
   print(df.head())

Quick notes & tips
------------------

- ``peptide_chain_position``: use ``"last"`` if the peptide is the last chain in the PDB.
- ``distance_cutoff``: interface radius in Å (example uses 8.0 Å).
- Output is plain JSON dicts; save ``result.json`` per entry for reproducibility.

API quick reference
-------------------

.. list-table::
   :widths: 25 75
   :header-rows: 0

   * - ``Analysis(...)``
     - Constructor. Common args: ``json_path``, ``pdb_path``, ``peptide_chain_position``, ``distance_cutoff``.
   * - ``single_analysis()``
     - Analyze a single JSON+PDB pair → metrics dict.
   * - ``all_analysis(folder_path)``
     - Process ranked models in `folder_path` → dict keyed by rank.
   * - ``batch_analysis(parent_path, progress_step_pct=20)``
     - Process multiple entries under `parent_path` → mapping entry→results.

See also
--------

- :doc:`getting_started`
- :doc:`api`
