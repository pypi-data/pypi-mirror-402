from __future__ import annotations
from pathlib import Path
import urllib.request
import urllib.error
import shutil
from typing import List, Union
import os
from os import PathLike
import re
import importlib
from contextlib import contextmanager

# import pytest

_AA3_TO1 = {
    "ALA": "A",
    "ARG": "R",
    "ASN": "N",
    "ASP": "D",
    "CYS": "C",
    "GLN": "Q",
    "GLU": "E",
    "GLY": "G",
    "HIS": "H",
    "ILE": "I",
    "LEU": "L",
    "LYS": "K",
    "MET": "M",
    "PHE": "F",
    "PRO": "P",
    "SER": "S",
    "THR": "T",
    "TRP": "W",
    "TYR": "Y",
    "VAL": "V",
    "SEC": "U",
    "PYL": "O",
    "HOH": "X",
}


def _parse_atom(line):
    """Extract (chain, resSeq, coords, plddt) from an ATOM/HETATM line."""
    return (
        line[21].strip(),  # chain ID
        int(line[22:26]),  # resSeq
        (float(line[30:38]), float(line[38:46]), float(line[46:54])),  # X  # Y  # Z
        float(line[60:66]),  # pLDDT in B-factor
    )


def _load_pdb(pdb: Union[str, bytes, bytearray, PathLike]) -> List[str]:

    if isinstance(pdb, (bytes, bytearray)):
        return pdb.decode("utf-8", "ignore").splitlines()

    # Path-like or filepath
    if isinstance(pdb, (str, PathLike)) and os.path.exists(pdb):
        with open(str(pdb), "r", encoding="utf-8", errors="ignore") as fh:
            return [ln.rstrip("\n") for ln in fh]

    if isinstance(pdb, str):
        return pdb.splitlines()

    raise TypeError("pdb must be a filepath or pdb text (str/bytes)")


@contextmanager
def temp_attr(module_name: str, attr: str, value):
    """
    Temporarily set `module_name.attr = value` for the duration of the context.

    Rationale:
    - Allows tests to control values looked up by `_fasta_parse` (requests, regex)
      without using third-party fixtures or patch helpers.
    - Restores previous value (or deletes attribute if it didn't exist) to avoid
      leaking changes to other tests.
    """
    mod = importlib.import_module(module_name)
    existed = hasattr(mod, attr)
    old = getattr(mod, attr, None)
    setattr(mod, attr, value)
    try:
        yield
    finally:
        if existed:
            setattr(mod, attr, old)
        else:
            delattr(mod, attr)


def _validate(code: str) -> str:
    """Return an uppercase, validated PDB ID or raise *ValueError*."""
    if not re.fullmatch(r"[0-9A-Za-z]{4}", code or ""):
        raise ValueError(f"Invalid PDB ID: {code!r}")
    return code.upper()


def _download_single(code: str, dest_dir: Path) -> Path:
    """Download a single PDB file and return its Path."""
    target = dest_dir / f"{code}.pdb"
    if target.exists():
        return target  # Already present.

    url = f"https://files.rcsb.org/download/{code}.pdb"
    tmp = target.with_suffix(".pdb.part")

    try:
        with urllib.request.urlopen(url) as resp, open(tmp, "wb") as fh:
            shutil.copyfileobj(resp, fh)
        tmp.replace(target)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FileNotFoundError(f"PDB entry {code} not found at RCSB.") from e
        raise
    return target
