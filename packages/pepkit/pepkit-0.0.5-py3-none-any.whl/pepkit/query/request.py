import argparse
import re
import shutil
import urllib.request
import urllib.error
from pathlib import Path


def _validate_pdb_id(pdb_id: str) -> str:
    if not re.fullmatch(r"[0-9A-Za-z]{4}", pdb_id or ""):
        raise ValueError(f"Invalid PDB ID: {pdb_id!r}")
    return pdb_id.upper()


def _download_pdb_file(url: str, tmp_path: Path):
    try:
        with urllib.request.urlopen(url) as resp, open(tmp_path, "wb") as fh:
            shutil.copyfileobj(resp, fh)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FileNotFoundError("PDB entry not found at RCSB.") from e
        raise


def retrieve_pdb(pdb_id: str, outdir: str | Path = ".", format: str = "pdb") -> Path:
    """
    Download a .pdb file from RCSB by PDB ID.
    """
    pdb_id = _validate_pdb_id(pdb_id)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    target = outdir / f"{pdb_id}.{format}"
    if target.exists():
        return target

    url = f"https://files.rcsb.org/download/{pdb_id}.{format}"
    tmp = target.with_suffix(".pdb.part")

    try:
        _download_pdb_file(url, tmp)
        tmp.replace(target)
        return target
    except Exception:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def argparse_setup():
    parser = argparse.ArgumentParser(description="Download PDB files from RCSB")
    parser.add_argument("pdb_id", type=str, help="PDB ID to download")
    parser.add_argument(
        "--format",
        type=str,
        choices=["pdb", "cif"],
        default="pdb",
        help="Output format",
    )
    parser.add_argument("--output", type=str, default=".", help="Output directory")
    return parser


def main():
    parser = argparse_setup()
    args = parser.parse_args()
    pdb_id = args.pdb_id
    output = args.output
    format = args.format
    retrieve_pdb(pdb_id, output, format)


if __name__ == "__main__":
    main()
