import argparse
import subprocess
import pandas as pd
from pathlib import Path


def mmseq2_run(sequences_path: str):
    sequences_path = Path(sequences_path)
    sequences_name = sequences_path.stem
    cmd = [
        "mmseqs",
        "easy-cluster",
        str(sequences_path),
        f"{sequences_path.parent}/{sequences_name}_out",
        f"{sequences_path.parent}/{sequences_name}_tmp",
        "--min-seq-id",
        "0.5",
        "-c",
        "0.8",
        "--cov-mode",
        "0",
    ]
    subprocess.run(cmd)
    return


def _get_representatives(input_path: str):
    """
    Get unique representatives from the cluster output file.
    Return all representatives.
    Usage: keep non-redundant sequences within a set.
    """
    df = pd.read_csv(input_path, sep="\t", header=None)
    representatives = set(df.iloc[:, 0].tolist())
    return representatives


def _get_unique_representatives(input_path: str):
    """
    Get unique representatives from the cluster output file.
    Return only clusters with a single representative.
    Usage: keep non-redundant sequences compared to the train set.
    """

    df = pd.read_csv(input_path, sep="\t", header=None)
    counts = df.iloc[:, 0].value_counts()
    unique_representatives = counts[counts == 1].index.to_list()
    return unique_representatives


def parser():
    parser = argparse.ArgumentParser(description="Run MMseqs2 clustering")
    parser.add_argument(
        "--input", type=str, required=True, help="Path to the input sequences file"
    )
    return parser


def main():
    args = parser().parse_args()
    mmseq2_run(args.input)


if __name__ == "__main__":
    main()
