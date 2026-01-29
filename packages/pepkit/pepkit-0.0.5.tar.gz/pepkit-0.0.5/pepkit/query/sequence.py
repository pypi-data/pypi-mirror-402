import argparse
from typing import Dict


# Utils
def three_to_one(res):
    table = {
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
    }
    return table.get(res.upper(), "X")


# 1. Parse ATOM residues per chain: this reserve the correct indexing in the PDB file.
def _extract_atom_sequences(pdb_lines) -> Dict[str, str]:
    """
    Extract protein sequences from ATOM records in PDB file with correct indexing.

    Parameters
    ----------
    pdb_lines
        List of lines from the PDB file.

    Returns
    -------
    Dict[str, str]
        Dictionary with chain IDs as keys and sequences as values.
        Missing residues are represented as "-" to maintain correct indexing.
        Sequence always starts from position 1.
    """
    chain_residues = {}  # chain -> {resseq: one_letter}

    for line in pdb_lines:
        if not line.startswith("ATOM  ") or len(line) < 54:
            continue

        resname = line[17:20].strip().upper()
        chain = line[21]
        resseq_str = line[22:26].strip()

        try:
            resseq = int(resseq_str)
        except ValueError:
            continue

        one_letter = three_to_one(resname)
        if one_letter != "X":
            if chain not in chain_residues:
                chain_residues[chain] = {}
            # Only record each residue once
            if resseq not in chain_residues[chain]:
                chain_residues[chain][resseq] = one_letter

    # Build sequences with correct indexing starting from position 1
    sequences = {}
    for chain, residue_dict in chain_residues.items():
        if not residue_dict:
            sequences[chain] = ""
            continue

        max_res = max(residue_dict.keys())

        sequence = []
        for i in range(1, max_res + 1):
            if i in residue_dict:
                sequence.append(residue_dict[i])
            else:
                sequence.append("-")

        sequences[chain] = "".join(sequence)

    return sequences


# 2. Parse SEQRES sequences per chain: this reserve all residues including unsolved ones.
def _extract_seqres_sequences(pdb_lines) -> Dict[str, str]:
    """
    Extract protein sequences from SEQRES records in PDB file.

    Parameters
    ----------
    pdb_lines
        List of lines from the PDB file.

    Returns
    -------
    Dict[str, str]
        Dictionary with chain IDs as keys and sequences as values.
    """
    chain_sequences = {}
    for line in pdb_lines:
        if line.startswith("SEQRES"):
            chain = line[11]  # Chain identifier at position 11
            residues = line[19:].strip().split()  # Residues start at position 19

            if chain not in chain_sequences:
                chain_sequences[chain] = []

            # Convert 3-letter codes to 1-letter codes using three_to_one
            for res in residues:
                chain_sequences[chain].append(three_to_one(res))

    # Convert lists to strings
    for chain in chain_sequences:
        chain_sequences[chain] = "".join(chain_sequences[chain])

    return chain_sequences


# 3. Alignment SEQRES → ATOM: map all recorded residues into correct PDB indexing.
def _align_sequences(seqres_seq: str, atom_seq: str) -> str:
    """
    Align SEQRES sequence with ATOM sequence to create final sequence starting
    from position 1.

    Parameters
    ----------
    seqres_seq : str
        Complete sequence from SEQRES records (all residues, but may start at wrong index)
    atom_seq : str
        Sequence from ATOM records with gaps ("-") for missing residues
        and correct indexing

    Returns
    -------
    str
        Final aligned sequence starting from position 1 with all residues
        at correct positions
    """
    if not atom_seq:
        return seqres_seq

    if not seqres_seq:
        return atom_seq
    # print(f"Aligning SEQRES: {seqres_seq}")
    # print(f"with ATOM:    {atom_seq}")
    # Remove leading and trailing dashes from ATOM sequence to get actual residues
    atom_trimmed = atom_seq.strip("-")
    if not atom_trimmed:
        return seqres_seq

    # Find where this ATOM sequence aligns in SEQRES
    best_match = 0
    best_seqres_start = 0

    # Try all possible alignments
    for seqres_start in range(len(seqres_seq) - len(atom_trimmed) + 1):
        matches = 0
        for i, atom_char in enumerate(atom_trimmed):
            if (
                seqres_start + i < len(seqres_seq)
                and seqres_seq[seqres_start + i] == atom_char
            ):
                matches += 1

        if matches > best_match:
            best_match = matches
            best_seqres_start = seqres_start

    # Find where the first non-dash residue appears in ATOM sequence
    # (this should be position 1)
    first_residue_pos = 0
    for i, char in enumerate(atom_seq):
        if char != "-":
            first_residue_pos = i
            break

    # Calculate how much to truncate from SEQRES start
    # The first_residue_pos in ATOM corresponds to position 1
    # So we need to truncate SEQRES to align the first ATOM residue with position 1
    truncate_amount = best_seqres_start - first_residue_pos

    if truncate_amount > 0:
        # Truncate SEQRES from the beginning
        return seqres_seq[truncate_amount:]
    else:
        # No truncation needed or ATOM starts after position 1
        return seqres_seq


# 4. Main multi-chain function
def build_complete_sequences(pdb_lines):
    """
    Extract final sequences by aligning SEQRES and ATOM sequences.

    Parameters
    ----------
    pdb_path
        Path to the PDB file.

    Returns
    -------
    Dict[str, str]
        Dictionary with chain IDs as keys and aligned sequences starting from position 1.
    """
    seqres_sequences = _extract_seqres_sequences(pdb_lines)
    atom_sequences = _extract_atom_sequences(pdb_lines)

    final_sequences = {}

    for chain in set(seqres_sequences.keys()) | set(atom_sequences.keys()):
        seqres_seq = seqres_sequences.get(chain, "")
        atom_seq = atom_sequences.get(chain, "")

        if seqres_seq and atom_seq:
            # Align both sequences
            final_sequences[chain] = _align_sequences(seqres_seq, atom_seq)
        elif seqres_seq:
            # Only SEQRES available
            final_sequences[chain] = seqres_seq
        elif atom_seq:
            # Only ATOM available, pad to start from position 1
            final_sequences[chain] = atom_seq
        else:
            final_sequences[chain] = ""

    return final_sequences


def extract_sequences(
    results,
    fasta_path,
    receptor_only=False,
):
    """
    Write valid sequences to a FASTA file.
    If only_receptor_chains is True, write only receptor chains
    (ignore first chain of each entry).
    Otherwise, write all valid chains.
    """
    fasta_lines = []
    for valid, valid_chains, result, valid_sequences in results:
        if not valid:
            continue
        pdb_id = result["pdb_id"]
        chains_to_write = valid_chains
        if receptor_only:
            # Skip the first chain (peptide), write only receptor chains
            chains_to_write = valid_chains[1:]
        for chain_id in chains_to_write:
            seq = valid_sequences[chain_id]
            fasta_lines.append(f">{pdb_id}.{chain_id}")
            fasta_lines.append(seq)
    with open(fasta_path, "w") as fasta_out:
        fasta_out.write("\n".join(fasta_lines))
    print(f"Wrote sequences to {fasta_path} (receptor_only={receptor_only})")


def build_argparser():
    parser = argparse.ArgumentParser(
        description="Build complete sequences from PDB files."
    )
    parser.add_argument(
        "--input", "-i", type=str, required=True, help="Path to the PDB file."
    )
    return parser


def main():
    parser = build_argparser()
    args = parser.parse_args()

    pdb_file = args.input
    with open(pdb_file, "r") as f:
        pdb_lines = f.readlines()
    sequences = build_complete_sequences(pdb_lines)

    chain_order = list(sequences.keys())
    print("Chain order:", chain_order)
    if sequences:
        print("Successfully built mapping.")

    for chain in chain_order:
        print("Chain", chain)
        print(sequences[chain])
    return


if __name__ == "__main__":
    main()
    # Example usage:
    # python -m pepkit.query.sequence --input /Users/vitran/Downloads/8CBP.pdb
