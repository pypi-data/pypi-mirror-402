# 🧬 PepKit

**A Python Toolkit for Peptide Modeling, Analysis, and Benchmarking**

![PepKit Logo](https://raw.githubusercontent.com/Vivi-tran/PepKit/main/data/Figure/pepkit.png)

PepKit is a modular, peptide-centric Python toolkit designed to support **end-to-end computational peptide workflows**, from sequence processing and descriptor calculation to structural modeling, confidence assessment, and docking-oriented analysis.

The package is built with **reproducibility, scalability, and interoperability** in mind, making it suitable for:

- Peptide–protein interaction studies  
- Machine-learning–ready dataset construction  
- Structural bioinformatics and docking benchmarks  
- Large-scale peptide screening and analysis pipelines  

---

## ✨ Key Features

### 1️⃣ Sequence I/O & Standardization
- Convert between **FASTA** and **SMILES** formats (`fasta_to_smiles`, `smiles_to_fasta`).
- Validate and standardize peptide sequences (canonical residues, charge models).
- Batch processing for lists and pandas DataFrames.

### 2️⃣ Physicochemical Descriptors & Clustering
- Compute peptide-level descriptors (molecular weight, charge, hydrophobicity, pI).
- Generate descriptor tables for ML pipelines.
- Cluster peptide libraries based on sequence or chemical similarity.

### 3️⃣ Structural Modeling & Confidence Metrics
- Post-process **AlphaFold / AlphaFold-Multimer** outputs.
- Compute confidence metrics:
  - pLDDT (global, peptide, interface)
  - PAE (interface-aware)
  - pTM / ipTM / composite pTM
  - pDockQ, pDockQ2, MPDockQ
- Optional **DockQ** evaluation against experimental structures.

### 4️⃣ Peptide–Protein Dataset Construction
- Automated querying of **RCSB PDB** for peptide–protein complexes.
- Heuristic peptide-chain detection and interface extraction.
- CSV + FASTA export for benchmarking and ML.

### 5️⃣ Docking & Benchmark Pipelines
- Prepare inputs for docking and scoring workflows.
- Integrate predicted and experimental metrics in unified tables.
- Designed to interoperate with Rosetta, AlphaFold, and downstream scoring tools.

---

## 📦 Installation

### Install from PyPI
```bash
pip install pepkit
```

### Development installation
```bash
git clone https://github.com/Vivi-tran/PepKit.git
cd PepKit
pip install -e .
```

## 🚀 Quickstart

This section shows how to get started with **PepKit** in just a few lines of code, covering the most common peptide-centric tasks.

---

### 🔹 Sequence Conversion

Convert between peptide **FASTA** and **SMILES** representations:

```python
from pepkit.conversion import fasta_to_smiles, smiles_to_fasta


# FASTA → SMILES
seq = "ACDEFGHIK"
smiles = fasta_to_smiles(seq)
print("SMILES:", smiles)

# SMILES → FASTA
back_seq = smiles_to_fasta(smiles)
print("FASTA:", back_seq)
```


## 📚 Documentation

Full documentation is available at:

👉 **https://pepkit.readthedocs.io/en/latest/**


## License

This project is licensed under MIT License - see the [License](LICENSE) file for details.