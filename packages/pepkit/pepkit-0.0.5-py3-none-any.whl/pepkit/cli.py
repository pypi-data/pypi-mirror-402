from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

from pepkit.modelling.af.post.analysis import main as af_post_main
from pepkit.query.query import main_process


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
def _configure_logging() -> None:
    """
    Configure CLI logging at INFO level.

    Safe to call multiple times. Suppresses DEBUG logs while
    preserving INFO/WARNING/ERROR.
    """
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s | %(message)s",
        )
    else:
        root.setLevel(logging.INFO)


# ---------------------------------------------------------------------
# AF postprocess forwarding
# ---------------------------------------------------------------------
def _forward_to_af_post(
    *,
    af_out: str,
    single_entry: bool,
    mapping_csv: Optional[str],
    extra_args: List[str],
) -> None:
    """
    Forward arguments to pepkit.modelling.af.post.analysis CLI.

    Behaves like:
        python -m pepkit.modelling.af.post.analysis ...
    """
    if single_entry:
        argv = [
            "pepkit-af-post",
            "--entry_dir",
            af_out,
        ]
    else:
        argv = [
            "pepkit-af-post",
            "--batch_dir",
            af_out,
        ]

    if mapping_csv is not None:
        argv.extend(["--mapping_csv", mapping_csv])

    argv.extend(extra_args)

    sys.argv = argv
    af_post_main()


# ---------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------
def main() -> None:
    _configure_logging()

    parser = argparse.ArgumentParser(
        prog="pepkit",
        description="PepKit command line interface",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="<command>",
    )

    # ================================================================
    # pepkit query
    # ================================================================
    query_parser = subparsers.add_parser(
        "query",
        help="Query and curate peptide–protein complexes from RCSB",
        description=(
            "Query peptide–protein complexes from RCSB, "
            "filter by quality and sequence constraints, "
            "and generate core/train datasets."
        ),
    )

    query_parser.add_argument(
        "--quality",
        type=float,
        default=3.0,
        help="Minimum structure quality (default: 3.0)",
    )
    query_parser.add_argument(
        "--exp_method",
        type=str,
        default="X-RAY DIFFRACTION",
        help="Experimental method (default: X-RAY DIFFRACTION)",
    )
    query_parser.add_argument(
        "--core_release_date",
        nargs=2,
        metavar=("FROM", "TO"),
        required=True,
        help="Core release date range (YYYY-MM-DD YYYY-MM-DD)",
    )
    query_parser.add_argument(
        "--length_cutoff",
        type=int,
        default=50,
        help="Maximum peptide length (default: 50)",
    )
    query_parser.add_argument(
        "--canonical_check",
        action="store_true",
        help="Require canonical residues only",
    )
    query_parser.add_argument(
        "--hetatm_check",
        action="store_true",
        help="Exclude structures with HETATM records",
    )
    query_parser.add_argument(
        "--core_csv_path",
        type=str,
        default="core.csv",
        help="Path to core CSV file",
    )
    query_parser.add_argument(
        "--core_fasta_path",
        type=str,
        default="core.fasta",
        help="Path to core FASTA file",
    )
    query_parser.add_argument(
        "--train_csv_path",
        type=str,
        default="train.csv",
        help="Path to train CSV file",
    )
    query_parser.add_argument(
        "--train_fasta_path",
        type=str,
        default="train.fasta",
        help="Path to train FASTA file",
    )
    query_parser.add_argument(
        "--final_csv_path",
        type=str,
        default="final.csv",
        help="Path to final CSV file",
    )
    query_parser.add_argument(
        "--receptor_only",
        action="store_true",
        help="Only include receptor chains in FASTA output",
    )
    query_parser.add_argument(
        "--n_jobs",
        type=int,
        default=8,
        help="Number of parallel jobs (default: 8)",
    )

    # ================================================================
    # pepkit postprocess
    # ================================================================
    post_parser = subparsers.add_parser(
        "postprocess",
        help="Postprocess AlphaFold / ColabFold outputs",
        description=(
            "Run post-processing and confidence scoring "
            "on AlphaFold / ColabFold outputs."
        ),
    )
    post_parser.add_argument(
        "--af-out",
        required=True,
        type=str,
        help="AlphaFold / ColabFold output directory or .zip archive",
    )
    post_parser.add_argument(
        "--single-entry",
        dest="single_entry",
        action="store_true",
        help="Run on a single entry (when set). Otherwise operate in batch mode.",
    )

    post_parser.add_argument(
        "--mapping_csv",
        type=str,
        default=None,
        help="Optional CSV mapping file passed to AF post-analysis",
    )

    # -----------------------------------------------------------------
    # Parse
    # -----------------------------------------------------------------
    args, unknown = parser.parse_known_args()

    # ================================================================
    # Dispatch: query
    # ================================================================
    if args.command == "query":
        core_release_date = {
            "from": args.core_release_date[0],
            "to": args.core_release_date[1],
        }
        train_release_date = args.core_release_date[0]

        logging.info("Running PepKit query pipeline")
        logging.info(
            "Core release date: %s → %s",
            args.core_release_date[0],
            args.core_release_date[1],
        )

        df = main_process(
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

        logging.info("Final core set size: %d", len(df))
        return

    # ================================================================
    # Dispatch: postprocess
    # ================================================================
    if args.command == "postprocess":
        logging.info("Running PepKit AF postprocessing")
        logging.info("AF output: %s", args.af_out)
        if args.mapping_csv:
            logging.info("Mapping CSV: %s", args.mapping_csv)

        _forward_to_af_post(
            af_out=args.af_out,
            single_entry=args.single_entry,
            mapping_csv=args.mapping_csv,
            extra_args=unknown,
        )
        return

    # Defensive fallback
    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
