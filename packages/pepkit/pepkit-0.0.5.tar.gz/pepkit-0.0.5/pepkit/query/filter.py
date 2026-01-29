import argparse
import pandas as pd
import re
from typing import Dict, Optional, List, Tuple, Set
import urllib.request
import urllib.error
from .sequence import build_complete_sequences
from joblib import Parallel, delayed
from tqdm import tqdm
from .sequence import extract_sequences


# from ..modelling.af.post import Utils ###
# Helpers
def _validate_pdb_id(pdb_id: str) -> str:
    if not re.fullmatch(r"[0-9A-Za-z]{4}", pdb_id or ""):
        raise ValueError(f"Invalid PDB ID: {pdb_id!r}")
    return pdb_id.upper()


def _parse_atom(pdb_line):
    """Extract (chain, resSeq, coords, plddt) from an ATOM/HETATM line."""
    return (
        pdb_line[21].strip(),  # chain ID
        int(pdb_line[22:26]),  # resSeq
        (
            float(pdb_line[30:38]),
            float(pdb_line[38:46]),
            float(pdb_line[46:54]),
        ),  # X  # Y  # Z
        float(pdb_line[60:66]),  # pLDDT in B-factor
    )


def _get_het_names(pdb_lines: str) -> Set[str]:
    het_names = {}
    for line in pdb_lines:
        if line.startswith("HETATM"):
            het_chain = line[12].strip()
            het_name = line[7:10].strip()
            if het_name not in het_names:
                het_names[het_name] = set()
            het_names[het_name].add(het_chain)
    if het_names:
        return False
    return het_names


# Functions
def read_pdb_rcsb(pdb_id):  # -> pdb_lines
    """
    Fetch .pdb file lines from RCSB by PDB ID.
    Returns a list of lines (strings).
    """
    pdb_id = _validate_pdb_id(pdb_id)
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    try:
        with urllib.request.urlopen(url) as resp:
            content = resp.read().decode("utf-8")
            return content.splitlines()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FileNotFoundError("PDB entry not found at RCSB.") from e
        raise


def extract_peptide_chain(
    sequences: Dict[str, str], max_diff: int = 10
) -> Optional[str]:
    """
    Return a peptide chain ID from a PDB file.

    Logic:
      - Count unique residues per chain from ATOM records (resseq + iCode).
      - Consider only chains with > 2 unique residues.
      - Let shortest_len = min(lengths of valid chains).
      - Gather chains with length <= shortest_len + max_diff.
      - If multiple chains in that group: choose the one with largest length
        (tie-break by chain ID). Otherwise return the single shortest chain.
    """
    valid = {}
    chains = sequences.keys()
    valid = {ch: len(sequences[ch]) for ch in chains if len(sequences[ch]) > 2}
    # shortest chain length
    shortest_len = min(valid.values())

    # chains within max_diff of shortest
    candidates = {ch: ln for ch, ln in valid.items() if ln <= (shortest_len + max_diff)}

    if not candidates:
        # defensive fallback; should not happen because shortest chain
        # is always in candidates
        return sorted(valid.items(), key=lambda x: (x[1], x[0]))[0][0]

    if len(candidates) == 1:
        # only the shortest chain qualifies
        return next(iter(candidates.keys()))

    # multiple candidates -> pick the most complete (largest observed residue count)
    # tie-break by chain ID for determinism
    selected = sorted(candidates.items(), key=lambda x: (-x[1], x[0]))[0][0]
    return selected


def extract_protein_chain(
    pdb_lines: str, peptide_chain: str, cutoff: float = 8.0
) -> Optional[str]:
    atoms_by_chain: Dict[str, List[Tuple[float, float, float]]] = {}
    # residues_by_chain: Dict[str, Set[Tuple[str, str]]] = defaultdict(set)

    model_seen = False

    for raw in pdb_lines:
        line = raw.rstrip("\n")
        if line.startswith("MODEL"):
            model_seen = True
            continue
        if model_seen and line.startswith("ENDMDL"):
            break
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        try:
            parsed = _parse_atom(line)
        except Exception:
            # skip malformed atom lines entirely
            continue

        chain_id = None
        coords = None

        if parsed and len(parsed) >= 3:
            chain_id = parsed[0]
            coords = parsed[2]

        # store coords
        atoms_by_chain.setdefault(chain_id, []).append(coords)

    if peptide_chain not in atoms_by_chain:
        raise ValueError(f"Chain '{peptide_chain}' not found in parsed atoms")

    cutoff2 = cutoff * cutoff
    nearby: Set[str] = set()

    # find chains within cutoff (excluding peptide_chain)
    pep_atoms = atoms_by_chain[peptide_chain]
    for c, coords in atoms_by_chain.items():
        if c == peptide_chain:
            continue
        found = False
        for x1, y1, z1 in pep_atoms:
            if found:
                break
            for x2, y2, z2 in coords:
                dx = x1 - x2
                dy = y1 - y2
                dz = z1 - z2
                if dx * dx + dy * dy + dz * dz <= cutoff2:
                    nearby.add(c)
                    found = True
                    break

    return sorted(nearby)


def chain_length(sequences, chain):
    if chain not in sequences:
        raise ValueError(f"Chain {chain} not found in sequences.")
    return len(sequences[chain])


def chain_length_filter(sequences, chain, length_cutoff):
    length = chain_length(sequences, chain)
    return length <= length_cutoff


def canonical_filter(sequences, chain):
    if chain not in sequences:
        raise ValueError(f"Chain {chain} not found in sequences.")
    for res in sequences[chain]:
        if res.upper() == "X":
            return False
    return True


def main(
    pdb_id: str,
    length_cutoff: int = 50,
    canonical_check: bool = False,
    hetatm_check: bool = False,
):

    pdb_lines = read_pdb_rcsb(pdb_id)
    sequences = build_complete_sequences(pdb_lines)
    # results: dict = {}
    # Extract peptide chain
    try:
        peptide_chain = extract_peptide_chain(sequences)
    except ValueError as e:
        print(f"Error extracting peptide chain: {e}")
        return False, None, None, sequences
    if peptide_chain is None or not chain_length_filter(
        sequences, peptide_chain, length_cutoff
    ):
        print(
            f"No valid peptide chain found for {pdb_id} "
            + f"with length cutoff {length_cutoff}."
        )
        return False, None, None, sequences
    # print(f"Peptide chain for {pdb_id}: {peptide_chain}")
    # Extract protein chains
    try:
        protein_chains = extract_protein_chain(pdb_lines, peptide_chain)
        protein_chains = [ch for ch in protein_chains if ch in sequences.keys()]

    except ValueError as e:
        print(f"Error extracting protein chains: {e}")
        return
    if not protein_chains:
        print(
            f"No protein chains found for {pdb_id} with length cutoff {length_cutoff}."
        )
        return False, None, None, sequences

    valid_protein_chains = []
    for protein_chain in protein_chains:
        if not chain_length_filter(sequences, protein_chain, length_cutoff):
            valid_protein_chains.append(protein_chain)
    if not valid_protein_chains:
        print(f"No valid protein chain found for {pdb_id}")
        return False, None, None, sequences

    valid_chains = [peptide_chain] + valid_protein_chains  # first chain is peptide
    # print(f"Valid chains for {pdb_id}: {valid_chains}")
    # Check canonical in valid peptide-protein chains:
    if canonical_check:
        if not all(
            canonical_filter(sequences, valid_chain) for valid_chain in valid_chains
        ):
            print(f"Non-canonical residues found in {pdb_id}.")
            return False, None, None, sequences

    # Check hetatms in pdb file
    if hetatm_check:
        if _get_het_names(pdb_lines):
            print(f"HETATM residues found in {pdb_id}.")
            return False, None, None, sequences

    result = {
        "pdb_id": pdb_id,
        "peptide_chain": peptide_chain,
        "peptide_sequence": sequences[peptide_chain],
        "protein_chain": valid_protein_chains,
        "protein_sequences": ":".join([sequences[ch] for ch in valid_protein_chains]),
        "peptide_length": len(sequences[peptide_chain]),
        "protein_lengths": {ch: len(sequences[ch]) for ch in valid_protein_chains},
    }
    valid_sequences = {ch: sequences[ch] for ch in valid_chains}
    return True, valid_chains, result, valid_sequences


def main_parallel(
    pdb_ids: list,
    length_cutoff: int = 50,
    canonical_check: bool = False,
    hetatm_check: bool = False,
    n_jobs: int = 8,
):
    with Parallel(n_jobs=n_jobs) as parallel:
        results = parallel(
            delayed(main)(
                pdb_id=pdb_id,
                length_cutoff=length_cutoff,
                canonical_check=canonical_check,
                hetatm_check=hetatm_check,
            )
            for pdb_id in tqdm(pdb_ids)
        )
    return results


def parser():
    parser = argparse.ArgumentParser(
        description="Filter PDB entries based on peptide-protein criteria."
    )
    parser.add_argument("--pdb_ids", nargs="+", type=str, required=True, help="PDB IDs")
    parser.add_argument(
        "--length_cutoff", type=int, required=True, help="Maximum chain length cutoff"
    )
    parser.add_argument(
        "--canonical_check",
        action="store_true",
        help="Check for canonical residues only",
    )
    parser.add_argument(
        "--hetatm_check",
        action="store_true",
        help="Check for presence of HETATM residues",
    )
    parser.add_argument(
        "--n_jobs", type=int, default=4, help="Parallel workers for batch mode"
    )

    return parser


if __name__ == "__main__":
    parser = parser()
    args = parser.parse_args()
    if len(args.pdb_ids) == 1:
        pdb_id = args.pdb_ids[0]
        valid, valid_chains, result, valid_sequences = main(
            pdb_id=pdb_id,
            length_cutoff=args.length_cutoff,
            canonical_check=args.canonical_check,
            hetatm_check=args.hetatm_check,
        )
        if not valid:
            print(f"Invalid PDB entry: {args.pdb_ids[0].upper()}")
            # print(f"Results: {results}")
        else:
            print(f"Valid PDB entry: {args.pdb_ids[0].upper()}")
            print(f"Valid chains: {valid_chains}")
            print(
                f"Valid peptide chain of {args.pdb_ids[0].upper()}: {valid_chains[0]}"
            )
            # print(f"Results: {result}")
            df = pd.DataFrame([result])
            print(df.head(5))
    else:
        # Batch mode
        results = main_parallel(
            pdb_ids=args.pdb_ids,
            length_cutoff=args.length_cutoff,
            canonical_check=args.canonical_check,
            hetatm_check=args.hetatm_check,
            n_jobs=args.n_jobs,
        )
        df = pd.DataFrame(
            [
                result
                for valid, valid_chains, result, valid_sequences in results
                if valid
            ]
        )
        if not df.empty:
            print(df.head(5))
            valids = df["pdb_id"].tolist()
            print(f"Total valid PDB entries: {len(valids)} out of {len(args.pdb_ids)}")
            print(df.head(5))
            df.to_csv("test_core_out.csv", index=False)
            extract_sequences(
                results, fasta_path="test_core_out.fasta", receptor_only=True
            )
        else:
            print("No valid PDB entries found.")
    # python -m pepkit.query.filter --pdb_ids 6A90 8S6A 9H3D 8CBP --length_cutoff 50

# alias
validate_complex_pdb = main
validate_complex_pdbs = main_parallel
