Query
=====

.. raw:: html

   <div class="hero">
     <p class="hero-title">Query</p>
     <p class="hero-subtitle">Fetch PDB entries and validate peptide–protein complexes with high-quality, constraint-driven filters and robust CLI tools.</p>
     <div class="badges">
       <span class="badge">fetch PDB</span>
       <span class="badge">validate & filter</span>
       <span class="badge">batch / parallel</span>
       <span class="badge">CLI friendly</span>
     </div>
   </div>

Quick overview
--------------

.. raw:: html

   <div class="at-a-glance" role="region" aria-label="Query at a glance" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:12px; margin-top:18px;">
     <div class="info-card" role="article" aria-labelledby="q-what">
       <div class="info-icon" aria-hidden="true" style="font-size:20px;">🔎</div>
       <div class="info-body">
         <h4 id="q-what" style="margin:0 0 6px 0;">What</h4>
         <p style="margin:0; font-size:13px;">Retrieve PDB/CIF files and screen peptide–protein complexes using length, canonical, HETATM and experimental constraints.</p>
       </div>
     </div>

     <div class="info-card" role="article" aria-labelledby="q-why">
       <div class="info-icon" aria-hidden="true" style="font-size:20px;">⚙️</div>
       <div class="info-body">
         <h4 id="q-why" style="margin:0 0 6px 0;">Why</h4>
         <p style="margin:0; font-size:13px;">Screen before download to save bandwidth and focus on high-quality, ligand-free complexes for modelling.</p>
       </div>
     </div>

     <div class="info-card" role="article" aria-labelledby="q-how">
       <div class="info-icon" aria-hidden="true" style="font-size:20px;">🚀</div>
       <div class="info-body">
         <h4 id="q-how" style="margin:0 0 6px 0;">How</h4>
         <p style="margin:0; font-size:13px;">Use the Python API for pipelines, or the CLI for batch/streaming workflows (NDJSON → jq → xargs/parallel).</p>
       </div>
     </div>
   </div>

   
Fetch a single PDB
------------------

API:

.. code-block:: python

  from pepkit.query.request import retrieve_pdb

  # writes ./7qwv.pdb or ./7qwv.cif depending on format source
  retrieve_pdb(pdb_id="7qwv", outdir="./", format = 'pdb')

CLI:

.. code-block:: console

   python -m pepkit.query.request 7qwv --output ./ --format pdb

Filter PDB
----------

Online validation of PDB entries using simple constraints (run checks before downloading).

Single validation
^^^^^^^^^^^^^^^^^

Lightweight check for one PDB (no file written):

.. code-block:: python

   from pepkit.query.filter import validate_complex_pdb

   valid, valid_chains, result, valid_sequences = validate_complex_pdb(
       pdb_id="6A90",
       length_cutoff=50,
       canonical_check=False,
       hetatm_check=False,
   )

.. admonition:: Example output
   :class: note

   .. code-block:: text

      (False,
        None,
        None,
        {'B': 'SAKDGDVEGPAGCKKYDVECDSGECCQKQYLWYKWRPLDCRCLKSGFFSSKCVCRDV',
          'A': 'MADNSPLIREERQRLFRPYTRAMLTAPSAQPAKENGKTEENKDNSRDKGRGANKD..'})


Batch validation
^^^^^^^^^^^^^^^^^^

Validate many PDBs in parallel; returns a mapping from pdb_id → result:

.. code-block:: python

   from pepkit.query.filter import validate_complex_pdbs

   pdb_ids = ["6A90", "8S6A", "9H3D", "8CBP"]
   results = validate_complex_pdbs(
       pdb_ids=pdb_ids,
       length_cutoff=50,
       canonical_check=True,
       hetatm_check=True,
       n_jobs=4,
   )
   
Command line interface
^^^^^^^^^^^^^^^^^^^^^^

Validate a set of PDBs (parallel, NDJSON-friendly):

.. code-block:: console

   python -m pepkit.query.filter --pdb_ids 6A90 8S6A 9H3D 8CBP \
     --length_cutoff 50 --canonical_check --n_jobs 4

Flag reference
~~~~~~~~~~~~~~

- ``--pdb_ids`` — space-separated PDB IDs (required)  
- ``--length_cutoff`` — minimal peptide/protein chain length (int)  
- ``--canonical_check`` — require canonical amino acids (flag)  
- ``--hetatm_check`` — reject structures with HETATM near the peptide (flag)  
- ``--n_jobs`` — number of parallel workers 


Constraint-based PDB query
--------------------------

Run filtered harvests using quality / experimental / date / sequence constraints.
Writes results to CSV and FASTA; returns a DataFrame (or writes files depending on call).

Python API example:

.. code-block:: python

   from pepkit.query.query import query
   import pandas as pd

   query(
       quality=3.0,
       exp_method="X-RAY DIFFRACTION",
       release_date={"from": "2018-01-01", "to": "2018-01-08"},
       length_cutoff=50,
       canonical_check=True,
       hetatm_check=True,
       csv_path="demo.csv",
       fasta_path="demo.fasta",
       receptor_only=True,
       n_jobs=4,
   )

   df = pd.read_csv("demo.csv")
   print(df.head())

Example CSV
~~~~~~~~~~~

.. code-block:: csv

   pdb_id,peptide_chain,peptide_sequence,protein_chain,protein_sequences,peptide_length,protein_lengths
   5WHB,B,GPRRPRCPGDDASIEDLHEYWARLWNYLYRVA,"['A','J']","MTEYKLVVVGAVGVGKSALTIQLIQNHFVDEYDPTIEDSYR...",32,"{'A':166,'J':166}"
   5WHA,B,GPRRPRCPGDDASIEDLHEYWARLWNYLYAVA,"['A','D','G']","MTEYKLVVVGAVGVGKSALTIQLIQNHFVDEYDPTIEDSYR...",32,"{'A':166,'D':166,'G':166}"

Command line interface
~~~~~~~~~~~~~~~~~~~~~~

Module entry point:

.. code-block:: console

   python -m pepkit.query.query \
     --quality 3.0 \
     --exp_method "X-RAY DIFFRACTION" \
     --core_release_date 2018-01-01 2018-01-08 \
     --length_cutoff 50 \
     --canonical_check \
     --hetatm_check \
     --core_csv_path demo.csv \
     --core_fasta_path demo.fasta \
     --receptor_only \
     --n_jobs 4

Installed CLI:

.. code-block:: console

   pepkit query \
     --quality 3.0 \
     --exp_method "X-RAY DIFFRACTION" \
     --core_release_date 2018-01-01 2018-01-08 \
     --length_cutoff 50 \
     --canonical_check \
     --hetatm_check \
     --core_csv_path demo.csv \
     --core_fasta_path demo.fasta \
     --receptor_only \
     --n_jobs 4

Flag reference
~~~~~~~~~~~~~~

- ``quality`` — numeric threshold for chosen structure quality metric.  
- ``exp_method`` — match PDB experimental method string (case-insensitive).  
- ``release_date`` — dict ``{"from":"YYYY-MM-DD","to":"YYYY-MM-DD"}`` (inclusive). CLI accepts two dates after ``--core_release_date``.  
- ``length_cutoff`` — minimal peptide length.  
- ``canonical_check`` / ``hetatm_check`` — booleans to ensure canonical residues and ligand-free peptides.  
- ``receptor_only`` — only output receptor chains paired to peptides (useful for receptor-centric pipelines).  
- ``n_jobs`` — parallel workers for network/validation tasks.

See also
--------

- :doc:`getting_started` — example pipeline: query → validate → standardize → featurize.  
- :doc:`chem` — sequence ↔ SMILES conversion and chemical filtering.  
- :doc:`graph` — representing validated chains as graphs (ITS/graph processing).  
- :doc:`api` — full programmatic reference for the query module.
