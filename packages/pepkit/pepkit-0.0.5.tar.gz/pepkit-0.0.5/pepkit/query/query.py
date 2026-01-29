import pandas as pd
import argparse
from pathlib import Path
from .rcsbapi import peptide_query
from .filter import main_parallel
from .sequence import extract_sequences
from .mmseqs2 import mmseq2_run, _get_representatives, _get_unique_representatives


def query(
    quality,
    exp_method,
    release_date,
    length_cutoff,
    canonical_check,
    hetatm_check,
    csv_path,
    fasta_path,
    receptor_only,
    n_jobs,
):
    """
    Query, validate, and extract peptide–protein complexes from RCSB.

    This function performs an end-to-end workflow:

    1. Query RCSB for candidate peptide–protein complexes using metadata
       constraints (resolution, experimental method, release date).
    2. Validate each PDB entry using structural and sequence-based criteria
       (peptide detection, length cutoff, canonical residues, HETATM presence).
    3. Write a metadata table (CSV) describing valid complexes.
    4. Extract corresponding sequences into a FASTA file for downstream
       modeling (e.g., AF-Multimer, docking, ML pipelines).

    The function is **side-effect driven**: results are written to disk
    (CSV + FASTA) and not returned explicitly.

    :param quality:
        Maximum allowed experimental resolution (in Å) used to query RCSB.
        Lower values correspond to higher-quality structures.
        Example: ``3.0``.
    :type quality: float

    :param exp_method:
        Experimental method used to solve the structure.
        Must match RCSB metadata exactly.
        Example: ``"X-RAY DIFFRACTION"``.
    :type exp_method: str

    :param release_date:
        Release date constraint for RCSB query.
        Can be either:
        - a dict with ``{"from": YYYY-MM-DD, "to": YYYY-MM-DD}``, or
        - a single date string (interpreted as lower bound).
    :type release_date: dict or str

    :param length_cutoff:
        Maximum allowed sequence length used for peptide/protein filtering.
        Typically peptides are expected to be short (e.g. ≤ 50 residues).
    :type length_cutoff: int

    :param canonical_check:
        If ``True``, discard complexes containing non-canonical amino acids
        (e.g., ``X``) in any retained chain.
    :type canonical_check: bool

    :param hetatm_check:
        If ``True``, discard PDB entries containing HETATM records
        (e.g., ligands, cofactors, modified residues).
    :type hetatm_check: bool

    :param csv_path:
        Output path for the CSV metadata table describing valid
        peptide–protein complexes.
    :type csv_path: str or pathlib.Path

    :param fasta_path:
        Output path for the FASTA file containing extracted sequences.
        The exact content depends on ``receptor_only``.
    :type fasta_path: str or pathlib.Path

    :param receptor_only:
        If ``True``, only receptor (protein) chains are written to FASTA.
        If ``False``, both peptide and protein chains are included.
    :type receptor_only: bool

    :param n_jobs:
        Number of parallel workers used for PDB validation.
        Passed to ``joblib.Parallel``.
    :type n_jobs: int

    :raises RuntimeError:
        If RCSB query fails or no valid complexes are found.
    :raises IOError:
        If output files cannot be written.

    :side effects:
        - Writes ``csv_path`` (CSV metadata)
        - Writes ``fasta_path`` (FASTA sequences)

    :example:

        >>> query(
        ...     quality=3.0,
        ...     exp_method="X-RAY DIFFRACTION",
        ...     release_date={"from": "2018-01-01", "to": "2018-01-08"},
        ...     length_cutoff=50,
        ...     canonical_check=True,
        ...     hetatm_check=True,
        ...     csv_path="demo.csv",
        ...     fasta_path="demo.fasta",
        ...     receptor_only=True,
        ...     n_jobs=4,
        ... )

    """
    peptide_complexes = peptide_query(
        quality=quality, exp_method=exp_method, release_date=release_date
    )
    results = main_parallel(
        pdb_ids=peptide_complexes,
        length_cutoff=length_cutoff,
        canonical_check=canonical_check,
        hetatm_check=hetatm_check,
        n_jobs=n_jobs,
    )
    df = pd.DataFrame(
        [result for valid, valid_chains, result, valid_sequences in results if valid]
    )
    df.to_csv(csv_path, index=False)
    extract_sequences(results, fasta_path=fasta_path, receptor_only=receptor_only)


def main_process(
    quality,
    exp_method,
    core_release_date,
    train_release_date,
    length_cutoff,
    canonical_check,
    hetatm_check,
    core_csv_path,
    core_fasta_path,
    train_csv_path,
    train_fasta_path,
    final_csv_path,
    receptor_only,
    n_jobs,
):
    # 1. Query peptide-protein complexes from rcsb
    # core -> metadata + fasta
    query(
        quality=quality,
        exp_method=exp_method,
        release_date=core_release_date,
        length_cutoff=length_cutoff,
        canonical_check=canonical_check,
        hetatm_check=hetatm_check,
        csv_path=core_csv_path,
        fasta_path=core_fasta_path,
        receptor_only=receptor_only,
        n_jobs=n_jobs,
    )
    # train -> metadata + fasta
    query(
        quality=quality,
        exp_method=exp_method,
        release_date=train_release_date,
        length_cutoff=length_cutoff,
        canonical_check=False,
        hetatm_check=False,
        csv_path=train_csv_path,
        fasta_path=train_fasta_path,
        receptor_only=receptor_only,
        n_jobs=n_jobs,
    )

    # 2. Run MMseqs2 to find representative sequences
    # Remove redundancy in core set
    mmseq2_run(
        query_fasta=core_fasta_path,
    )

    # Remove overlapping of core vs. train
    # Combine core representatives and all train representatives
    combined_fasta_path = Path(core_fasta_path).parent / "combined.fasta"
    core_cluster_rep_path = (
        Path(core_fasta_path).parent / f"{Path(core_fasta_path).stem}_out_rep_seq.fasta"
    )
    with (
        open(core_cluster_rep_path, "r") as core_file,
        open(train_fasta_path, "r") as train_file,
        open(combined_fasta_path, "w") as combined_file,
    ):
        combined_file.writelines(core_file.readlines())
        combined_file.writelines(train_file.readlines())

    mmseq2_run(
        query_fasta=combined_fasta_path,
    )
    # Get representatives from the core output
    core_representatives = _get_representatives(
        f"{Path(core_fasta_path).parent}/{Path(core_fasta_path).stem}_out_cluster.tsv"
    )
    combined_unique_representatives = _get_unique_representatives(
        f"{Path(combined_fasta_path).parent}/combined_out_cluster.tsv"
    )
    final_core_lists = list(
        set(core_representatives) & set(combined_unique_representatives)
    )

    final_core_lists = list(set(rep.split(".")[0] for rep in final_core_lists))

    # Filter metadata based on final_core_lists
    df = pd.read_csv(core_csv_path)
    final_df = df[df["pdb_id"].isin(final_core_lists)]
    final_df.to_csv(final_csv_path, index=False)

    return final_df


def parser():
    parser = argparse.ArgumentParser(description="Process PDB files")
    parser.add_argument(
        "--quality", type=float, default=3.0, help="Quality of the PDB files"
    )
    parser.add_argument(
        "--exp_method",
        type=str,
        default="X-RAY DIFFRACTION",
        help="Experimental method used",
    )
    parser.add_argument(
        "--core_release_date",
        type=str,
        nargs="+",
        help="Release date range (YYYY-MM-DD YYYY-MM-DD)",
    )
    parser.add_argument(
        "--length_cutoff", type=int, default=50, help="Length cutoff for sequences"
    )
    parser.add_argument(
        "--canonical_check",
        action="store_true",
        default=True,
        help="Check for canonical residues",
    )
    parser.add_argument(
        "--hetatm_check",
        action="store_true",
        default=True,
        help="Check for HETATM records",
    )
    parser.add_argument(
        "--core_csv_path", type=str, default="core.csv", help="Path to core CSV file"
    )
    parser.add_argument(
        "--core_fasta_path",
        type=str,
        default="core.fasta",
        help="Path to core FASTA file",
    )
    parser.add_argument(
        "--train_csv_path", type=str, default="train.csv", help="Path to train CSV file"
    )
    parser.add_argument(
        "--train_fasta_path",
        type=str,
        default="train.fasta",
        help="Path to train FASTA file",
    )
    parser.add_argument(
        "--final_csv_path", type=str, default="final.csv", help="Path to final CSV file"
    )
    parser.add_argument(
        "--receptor_only",
        action="store_true",
        default=True,
        help="Only include receptor chains",
    )
    parser.add_argument(
        "--n_jobs", type=int, default=8, help="Number of jobs for parallel processing"
    )
    return parser.parse_args()


def main():
    args = parser()
    # release_date = None
    if args.core_release_date:
        train_release_date = args.core_release_date[0]
        core_release_date = {
            "from": args.core_release_date[0],
            "to": args.core_release_date[1],
        }
    final_df = main_process(
        quality=args.quality,
        exp_method=args.exp_method,
        core_release_date=core_release_date,
        train_release_date=train_release_date,
        length_cutoff=args.length_cutoff,
        canonical_check=args.canonical_check,
        hetatm_check=args.hetatm_check,
        core_csv_path=args.core_csv_path,
        core_fasta_path=args.core_fasta_path,
        train_csv_path=args.train_csv_path,
        train_fasta_path=args.train_fasta_path,
        final_csv_path=args.final_csv_path,
        receptor_only=args.receptor_only,
        n_jobs=args.n_jobs,
    )
    print(final_df.head(5))


if __name__ == "__main__":
    main()
