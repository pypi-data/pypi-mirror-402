.. _chem:

Chemical Modeling
=================

The :mod:`pepkit.chem` package contains utilities for peptide sequences and peptide-like molecules:

- **FASTA/SMILES conversion** (linear peptides)
- **Standardization & filtering** (drop non-canonical residues, batch/DataFrame processing)
- **Peptide properties** (net charge, molecular weight, pI)
- **Descriptor calculation** for ML pipelines

.. contents:: On this page
   :local:
   :depth: 2

At a glance
-----------

.. list-table::
   :widths: 25 75
   :header-rows: 0

   * - **Inputs**
     - FASTA strings, peptide sequences, SMILES, or pandas DataFrames
   * - **Outputs**
     - Canonical SMILES, cleaned/standardized sequences, property dicts, descriptor tables
   * - **Where to look next**
     - :doc:`api` for full function/class docs

Sequence ⇄ SMILES conversion
----------------------------

Convert a peptide sequence → SMILES
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Convert a sequence to a canonical SMILES string:

.. code-block:: python

   from pepkit.chem.conversion import fasta_to_smiles

   fasta = "ACDE"
   smiles = fasta_to_smiles(fasta)
   print(smiles)

.. admonition:: Example output
   :class: note

   .. code-block:: text

      SMILES: C[C@H](N)C(=O)N[C@@H](CS)C(=O)N[C@@H](CC(=O)O)C(=O)N[C@@H](CCC(=O)O)C(=O)O


Convert SMILES → sequence
^^^^^^^^^^^^^^^^^^^^^^^^^

Convert a peptide-like SMILES back to a FASTA/sequence (when the SMILES
corresponds to a peptide-like backbone):

.. code-block:: python

   from pepkit.chem.conversion import smiles_to_fasta

   seq = smiles_to_fasta(smiles, header="peptide1")
   print(seq)
.. admonition:: Example output
   :class: note

   .. code-block:: text

      >peptide1
      ACDE

Round-trip quick check
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from pepkit.chem.conversion import fasta_to_smiles, smiles_to_fasta
   seq = "ACDEFGHIK"
   ok = (smiles_to_fasta(fasta_to_smiles(seq), split=True) == seq)
   print("Round Trip:", ok)

.. note::

   - Intended for **linear peptides** (RDKit-style). Modified/cyclic peptides
     or arbitrary small-molecule SMILES may not round-trip.
   - RDKit is required.


Standardization & filtering
---------------------------

**Typical workflow:** **validate → standardize → featurize**

Standardize a list of sequences (remove non-canonical residues; optional pH charge model):

.. code-block:: python

   from pepkit.chem.standardize import Standardizer

   std = Standardizer(remove_non_canonical=True, charge_by_pH=True, pH=7.0)
   seqs = ["ACDEFGHIK", "XYZ"]
   standardized = std.process_list_fasta(seqs)
   print(standardized)
   # Example output (list): [SMILES, None]  # second entry removed / mapped

For pandas DataFrames (vectorized, returns a new DataFrame):

.. code-block:: python

   import pandas as pd
   from pepkit.chem.standardize import Standardizer

   df = pd.DataFrame({"id": [1, 2], "fasta": ["ACDEFGHIK", "XYZ"]})
   std = Standardizer(remove_non_canonical=True, charge_by_pH=True, pH=7.0)
   df_std = std.data_process(df, fasta_key="fasta")
   print(df_std.head())

.. admonition:: Example DataFrame (after standardization)
   :class: note

   .. code-block:: text

      id    fasta            smiles                  valid
      1     ACDEFGHIK        CC[C@H](C)[C@H]...      True
      2     XYZ              None                    False

.. warning::

   When ``remove_non_canonical=True``, records containing non-canonical residues
   will be filtered out or set to ``None`` depending on the API. Confirm how
   your downstream pipeline handles missing values before using this option.

Descriptors
-----------

Generate ML features using peptide-sequence descriptors or RDKit molecular descriptors.

.. code-block:: python

   from pepkit.chem.desc import Descriptor

   # Peptide sequence descriptors
   data_pep = [{"id": "pep1", "peptide_sequence": "ACDE"}]
   desc_pep = Descriptor(engine="peptides").calculate(data_pep)
   print(desc_pep[0])

   # RDKit molecular descriptors
   data_mol = [{"id": "mol1", "smiles": "CCO"}]
   desc_mol = Descriptor(engine="rdkit").calculate(data_mol)
   print(desc_mol[0])

.. note::

   The ``peptides`` engine requires the third-party package ``peptides``.
   Install with ``pip install peptides`` when using ``engine="peptides"``.

See also
--------

- :doc:`getting_started` — quickstart example that chains standardization → descriptors
- :doc:`chem` — full chemistry module overview  
- :doc: `api` — full API reference
