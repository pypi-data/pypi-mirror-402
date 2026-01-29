import argparse
from typing import Union, Literal, List
from rcsbapi.model import ModelQuery
from rcsbapi.search import search_attributes as attrs

ALLOWED_METHODS = [
    "ELECTRON CRYSTALLOGRAPHY",
    "ELECTRON MICROSCOPY",
    "EPR",
    "FIBER DIFFRACTION",
    "FLUORESCENCE TRANSFER",
    "INFRARED SPECTROSCOPY",
    "NEUTRON DIFFRACTION",
    "POWDER DIFFRACTION",
    "SOLID-STATE NMR",
    "SOLUTION NMR",
    "SOLUTION SCATTERING",
    "THEORETICAL MODEL",
    "X-RAY DIFFRACTION",
]


def retrieve_structure(
    entry_ids: Union[str, list], format: Literal["cif", "bcif"], output_dir: str
):
    model_query = ModelQuery()
    if isinstance(entry_ids, str):
        results = model_query.get_full_structure(
            entry_id=entry_ids,
            encoding=format,
            download=True,
            file_directory=output_dir,
        )
    else:
        results = model_query.get_multiple_structures(
            entry_ids=entry_ids,
            query_type="full",
            encoding=format,
            download=True,
            compress_gzip=False,
            file_directory=output_dir,
        )
    return results


def peptide_query(
    quality,
    exp_method: Union[str, List[str]] = "X-RAY DIFFRACTION",
    release_date: Union[str, dict] = None,
):

    # 1. Complex quality
    q5 = attrs.rcsb_entry_info.resolution_combined.less_or_equal(quality)

    # 2. Peptide-related queries
    q1 = attrs.rcsb_pubmed_abstract_text.contains_words("peptide")
    q2 = attrs.chem_comp.type.in_(
        [
            "L-peptide linking",
            "L-peptide NH3 amino terminus",
            "L-peptide COOH carboxy terminus",
        ]
    )
    q3 = attrs.pdbx_molecule_features.details.contains_words("peptide")
    q4 = attrs.struct_keywords.text.contains_words("peptide")

    # 3. Composition queries
    # Exclude DNA | RNA
    q9 = ~attrs.rcsb_entry_info.na_polymer_entity_types.in_(
        ["RNA (only)", "DNA (only)", "DNA/RNA (only)", "NA-hybrid (only)"]
    )
    # Polymer composition (at least has protein)
    q10 = attrs.rcsb_entry_info.polymer_composition.in_(
        [
            "heteromeric protein",
            "protein/NA",
            "protein/NA/oligosaccharide",
            "protein/oligosaccharide",
        ]
    )

    # Exclude monomer complexes
    q6 = ~attrs.rcsb_struct_symmetry.oligomeric_state.exact_match("Monomer")
    # The number of distinct protein polymer entities >= 2
    q11 = attrs.rcsb_entry_info.polymer_entity_count_protein.greater_or_equal(2)

    # 4. Availability of PDB structure
    q7 = attrs.pdbx_database_status.pdb_format_compatible.exact_match("Y")

    # 5. Experimental method
    if isinstance(exp_method, str):
        if exp_method not in ALLOWED_METHODS:
            raise ValueError(f"exp_method must be one of: {ALLOWED_METHODS}")
        q8 = attrs.exptl.method.exact_match(exp_method)
    elif isinstance(exp_method, list):
        invalid = [m for m in exp_method if m not in ALLOWED_METHODS]
        if invalid:
            raise ValueError(
                f"Invalid exp_method(s): {invalid}. Allowed: {ALLOWED_METHODS}"
            )
        q8 = attrs.exptl.method.in_(exp_method)
    else:
        raise ValueError("exp_method must be a string or a list of strings.")

    # 6. Release date range
    if isinstance(release_date, str):
        q = attrs.rcsb_accession_info.initial_release_date.less(release_date)
    elif isinstance(release_date, dict):
        if "from" in release_date and "to" in release_date:
            q = attrs.rcsb_accession_info.initial_release_date.range(release_date)
        else:
            raise ValueError("release_date dict must have 'from' and 'to' keys.")
    else:
        raise ValueError(
            "release_date must be a string (YYYY-MM-DD) or a dict with 'from' and 'to'."
        )

    query = q & (q1 | q2 | q3 | q4) & q5 & q6 & q7 & q8 & (q9 | q10) & q11
    pep_results = list(query())

    return pep_results


def parser():
    parser = argparse.ArgumentParser(description="Retrieve structure from RCSB PDB")
    parser.add_argument("--pdbids", type=str, nargs="+", help="PDB entry IDs")
    parser.add_argument(
        "--format",
        type=str,
        choices=["cif", "bcif"],
        default="cif",
        help="Output format",
    )
    parser.add_argument("--output", type=str, default=".", help="Output directory")
    parser.add_argument(
        "--quality", type=float, default=3.0, help="Maximum resolution quality"
    )
    parser.add_argument(
        "--exp_method",
        type=str,
        nargs="+",
        default=["X-RAY DIFFRACTION"],
        help="Experimental method(s)",
    )
    parser.add_argument(
        "--release_date",
        type=str,
        nargs="+",
        help="Release date (YYYY-MM-DD) or range (YYYY-MM-DD YYYY-MM-DD)",
    )
    return parser


def main():
    args = parser().parse_args()
    if args.pdbids:
        retrieve_structure(args.pdbids, args.format, args.output)
    else:
        release_date = None
        if args.release_date:
            if len(args.release_date) == 2:
                release_date = {
                    "from": args.release_date[0],
                    "to": args.release_date[1],
                }
            elif len(args.release_date) == 1:
                release_date = args.release_date[0]
            else:
                raise ValueError(
                    "release_date must be date (YYYY-MM-DD) or range "
                    + "(YYYY-MM-DD YYYY-MM-DD)."
                )

        results = peptide_query(
            quality=args.quality, exp_method=args.exp_method, release_date=release_date
        )
        # print(results[:5])
        print(f"Total results found: {len(results)}")
        # with open(f"{args.output}/peptide_query_results.txt", "w") as f:
        #     for pid in results:
        #         f.write(f"{pid}\n")


if __name__ == "__main__":
    main()
