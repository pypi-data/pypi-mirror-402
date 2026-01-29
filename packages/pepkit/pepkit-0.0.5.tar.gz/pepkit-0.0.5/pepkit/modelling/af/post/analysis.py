#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import math
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .base import BaseFeature
from .config import BaseConfig, IndexBasedConfig
from .dockq import (
    ensure_native_pdbs,
    find_native_pdb_file,
    inject_dockq_into_entry,
    native_pdb_dir_for_batch_path,
    read_mapping_csv,
)
from .indices import IndexCalculator
from .pae import PAE
from .plddt import PLDDT
from .ptm import PTM
from .utils import Utils

_DEFAULT_BASE_CONFIG = BaseConfig()
_DEFAULT_ANALYSIS_CONFIG = IndexBasedConfig()

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AnalysisInputs:
    json_path: Optional[Path]
    pdb_path: Optional[Path]


@dataclass(frozen=True)
class EntryMeta:
    length: Optional[int]
    processing_time: Optional[float]


@dataclass
class BatchStats:
    ok: int = 0
    empty: int = 0
    error: int = 0
    dockq_ok: int = 0
    dockq_fail: int = 0


class ProgressLogger:
    """
    Log at K% increments (10%, 20%, ...).
    """

    def __init__(self, total: int, step_pct: int) -> None:
        self.total = max(1, int(total))
        self.step = max(1, int(step_pct))
        self.next_pct = self.step

    def tick(self, i: int) -> None:
        pct = int((100.0 * i) / self.total)
        if pct >= self.next_pct:
            LOGGER.info("Progress: %d/%d (%d%%)", i, self.total, pct)
            self.next_pct += self.step


# ---------------------------------------------------------------------------
# Analysis implementation
# ---------------------------------------------------------------------------


class Analysis(BaseFeature):
    """
    High-level feature aggregation for AF(-Multimer) outputs.

    DockQ integration (via dockq.py):
      - Provide --mapping_csv with pdb_id,mapping to enable DockQ.
      - DockQ is computed for EACH entry *and* EACH rank.
      - Written inside each rank dict:
            rankXXX["total_dockq"]
            rankXXX["avg_dockq"]
    """

    def __init__(
        self,
        json_path: Optional[str] = None,
        pdb_path: Optional[str] = None,
        peptide_chain_position: str = "last",
        distance_cutoff: float = 8.0,
        round_digits: int = 2,
        *,
        pdockq2_d0: float = 10.0,
        pdockq2_sym_pae: bool = True,
    ) -> None:
        super().__init__(
            pdb_lines=None,
            peptide_chain_position=peptide_chain_position,
            distance_cutoff=distance_cutoff,
        )
        self.json_path = Path(json_path) if json_path else None
        self.pdb_path = Path(pdb_path) if pdb_path else None
        self.round_digits = int(round_digits)
        self.pdockq2_d0 = float(pdockq2_d0)
        self.pdockq2_sym_pae = bool(pdockq2_sym_pae)

    # -----------------------
    # Single-rank analysis
    # -----------------------
    def single_analysis(self) -> Dict[str, Any]:
        if self.json_path is None or self.pdb_path is None:
            raise ValueError("single_analysis requires both json_path and pdb_path")

        rec_json: Dict[str, Any] = Utils.process_json(self.json_path)
        pdb_lines: List[str] = Utils.process_pdb(self.pdb_path)

        (
            peptide_indices,
            peptide_chain,
            protein_interface_indices,
            peptide_interface_indices,
            interacting_pairs,
            protein_chains,
        ) = self._compute_interface_indices(pdb_lines)

        plddt_summary = self._compute_plddt(
            rec_json=rec_json,
            peptide_indices=peptide_indices,
            protein_interface_indices=protein_interface_indices,
            peptide_interface_indices=peptide_interface_indices,
        )
        pae_summary = self._compute_pae(
            rec_json=rec_json,
            peptide_indices=peptide_indices,
            protein_interface_indices=protein_interface_indices,
            peptide_interface_indices=peptide_interface_indices,
            interacting_pairs=interacting_pairs,
        )
        ptm_summary = self._compute_ptm(rec_json=rec_json, peptide_chain=peptide_chain)

        dockq_inputs = self._compute_pdockq_contacts_and_ptm(
            pdb_lines=pdb_lines,
            rec_json=rec_json,
            peptide_chain=peptide_chain,
            protein_chains=protein_chains,
            d0_pae=self.pdockq2_d0,
            sym_pae=self.pdockq2_sym_pae,
        )

        d: Dict[str, Any] = {
            **plddt_summary,
            **pae_summary,
            **ptm_summary,
            "protein_interface_residues": protein_interface_indices,
            "peptide_interface_residues": peptide_interface_indices,
            "peptide_chain": peptide_chain,
            "protein_chains": protein_chains,
            "n_chains": 1 + len(protein_chains),
            **dockq_inputs,
        }
        d.update(self._compute_confidence_scores(d))
        return d

    def _compute_interface_indices(
        self, pdb_lines: List[str]
    ) -> Tuple[List[int], str, List[int], List[int], List[Tuple[int, int]], List[str]]:
        peptide_indices, peptide_chain = IndexCalculator.get_peptide_indices(
            pdb_lines,
            peptide_chain_position=self.peptide_chain_position,
        )

        (
            protein_interface_indices,
            peptide_interface_indices,
            protein_chains,
            _,
            interacting_pairs,
        ) = IndexCalculator.get_interface_indices(
            pdb_lines,
            peptide_chain=peptide_chain,
            distance_cutoff=self.distance_cutoff,
        )

        return (
            peptide_indices,
            peptide_chain,
            protein_interface_indices,
            peptide_interface_indices,
            interacting_pairs,
            protein_chains,
        )

    def _compute_plddt(
        self,
        *,
        rec_json: Dict[str, Any],
        peptide_indices: List[int],
        protein_interface_indices: List[int],
        peptide_interface_indices: List[int],
    ) -> Dict[str, Any]:
        plddt_obj = PLDDT(
            rec_json,
            peptide_indices,
            protein_interface_indices,
            peptide_interface_indices,
            round_digits=self.round_digits,
        )
        (
            mean_plddt,
            median_plddt,
            peptide_plddt,
            protein_interface_plddt,
            peptide_interface_plddt,
            interface_plddt,
        ) = plddt_obj.summary()

        return {
            "mean_plddt": mean_plddt,
            "median_plddt": median_plddt,
            "peptide_plddt": peptide_plddt,
            "protein_interface_plddt": protein_interface_plddt,
            "peptide_interface_plddt": peptide_interface_plddt,
            "interface_plddt": interface_plddt,
        }

    def _compute_pae(
        self,
        *,
        rec_json: Dict[str, Any],
        peptide_indices: List[int],
        protein_interface_indices: List[int],
        peptide_interface_indices: List[int],
        interacting_pairs: List[Tuple[int, int]],
    ) -> Dict[str, Any]:
        pae_obj = PAE(
            rec_json,
            peptide_indices=peptide_indices,
            protein_interface_indices=protein_interface_indices,
            peptide_interface_indices=peptide_interface_indices,
            interacting_pairs=interacting_pairs,
            round_digits=self.round_digits,
        )
        (
            mean_pae,
            max_pae,
            peptide_pae,
            protein_interface_pae,
            peptide_interface_pae,
            mean_interface_pae,
        ) = pae_obj.summary()

        return {
            "mean_pae": mean_pae,
            "max_pae": max_pae,
            "peptide_pae": peptide_pae,
            "protein_interface_pae": protein_interface_pae,
            "peptide_interface_pae": peptide_interface_pae,
            "mean_interface_pae": mean_interface_pae,
        }

    def _compute_ptm(
        self, *, rec_json: Dict[str, Any], peptide_chain: str
    ) -> Dict[str, Any]:
        ptm_obj = PTM(
            rec_json,
            peptide_chain=peptide_chain,
            round_digits=self.round_digits,
        )
        ptm, global_iptm, composite_ptm, peptide_ptm, protein_ptm, actif_ptm = (
            ptm_obj.summary()
        )
        return {
            "ptm": ptm,
            "global_iptm": global_iptm,
            "composite_ptm": composite_ptm,
            "peptide_ptm": peptide_ptm,
            "protein_ptm": protein_ptm,
            "actif_ptm": actif_ptm,
        }

    def _compute_pdockq_contacts_and_ptm(
        self,
        *,
        pdb_lines: List[str],
        rec_json: Dict[str, Any],
        peptide_chain: str,
        protein_chains: List[str],
        d0_pae: float = 10.0,
        sym_pae: bool = True,
    ) -> Dict[str, Any]:
        from .contact import ContactCounter  # local import to avoid circular deps

        cc = ContactCounter(
            pdb_lines=pdb_lines,
            peptide_chain_position=self.peptide_chain_position,
            distance_cutoff=self.distance_cutoff,
        )

        all_pairs_global: List[Tuple[int, int]] = []
        n_contacts_total = 0

        for prot_chain in protein_chains:
            if prot_chain == peptide_chain:
                continue
            r = cc.contact_count_pair(peptide_chain, prot_chain, return_global=True)
            n_contacts_total += int(r.n_contacts)
            if r.pairs_global:
                all_pairs_global.extend(r.pairs_global)

        pae = rec_json.get("pae", None)
        mean_ptm = float("nan")

        if pae is not None and all_pairs_global:
            vals: List[float] = []
            for gi, gj in all_pairs_global:
                i = int(gi) - 1
                j = int(gj) - 1
                try:
                    pae_ij = float(pae[i][j])
                    pae_use = pae_ij
                    if sym_pae:
                        pae_ji = float(pae[j][i])
                        pae_use = 0.5 * (pae_ij + pae_ji)
                    vals.append(1.0 / (1.0 + (pae_use / float(d0_pae)) ** 2))
                except Exception:
                    continue
            if vals:
                mean_ptm = float(sum(vals) / len(vals))

        return {
            "n_contacts_pdockq": int(n_contacts_total),
            "mean_ptm_pdockq2": (
                round(mean_ptm, self.round_digits)
                if mean_ptm == mean_ptm
                else float("nan")
            ),
        }

    def _compute_confidence_scores(self, d: Dict[str, Any]) -> Dict[str, Any]:
        from ..score.mpdockq import MPDockQ
        from ..score.pdockq import PDockQ
        from ..score.pdockq2 import PDockQ2

        def clean(x: float) -> Optional[float]:
            if isinstance(x, float) and math.isnan(x):
                return None
            return round(float(x), self.round_digits)

        return {
            "pdockq": clean(PDockQ().compute(d).score),
            "pdockq2": clean(PDockQ2().compute(d).score),
            "mpdockq": clean(MPDockQ(warn_if_lt3=False).compute(d).score),
        }

    # -----------------------
    # Entry directory analysis (per-rank)
    # -----------------------
    def all_analysis(self, dir_path: Union[str, Path]) -> Dict[str, Any]:
        entry_dir = _resolve_entry_dir(Path(dir_path))
        entry_result: Dict[str, Any] = {}

        try:
            meta = self._entry_meta(entry_dir)
            for i in range(1, 6):
                key = f"rank{i:03d}"
                inputs = self._rank_inputs(entry_dir, i)
                if inputs is None:
                    self._warn_missing_rank(entry_dir, i)
                    continue

                try:
                    rank_out = Analysis(
                        json_path=str(inputs.json_path),
                        pdb_path=str(inputs.pdb_path),
                        peptide_chain_position=self.peptide_chain_position,
                        distance_cutoff=self.distance_cutoff,
                        round_digits=self.round_digits,
                        pdockq2_d0=self.pdockq2_d0,
                        pdockq2_sym_pae=self.pdockq2_sym_pae,
                    ).single_analysis()

                    # Keep path for DockQ injection later
                    rank_out["_pred_pdb_path"] = (
                        str(inputs.pdb_path) if inputs.pdb_path else None
                    )
                    entry_result[key] = rank_out
                except Exception as e:
                    self.log_error(f"Error processing {entry_dir.name} rank {i}: {e}")
                    continue

            entry_result["length"] = meta.length
            entry_result["processing_time"] = meta.processing_time
            return entry_result

        except Exception as e:
            self.log_error(f"Error processing entry {entry_dir.name}: {e}")
            return {}

    def _entry_meta(self, entry_dir: Path) -> EntryMeta:
        length = Utils.get_length(entry_dir)
        log_matches = sorted(entry_dir.glob("*log.txt"))
        process_time = Utils.processing_time(log_matches[0]) if log_matches else None
        return EntryMeta(length=length, processing_time=process_time)

    @staticmethod
    def _rank_inputs(entry_dir: Path, rank_i: int) -> Optional[AnalysisInputs]:
        rank_tag = f"rank_{rank_i:03d}"
        json_matches = sorted(entry_dir.glob(f"*_scores_{rank_tag}_*.json"))
        pdb_matches = sorted(entry_dir.glob(f"*relaxed_{rank_tag}_*.pdb"))
        if not json_matches or not pdb_matches:
            return None
        return AnalysisInputs(json_path=json_matches[0], pdb_path=pdb_matches[0])

    @staticmethod
    def _warn_missing_rank(entry_dir: Path, rank_i: int) -> None:
        LOGGER.warning(
            "No matching PDB or JSON file found for %s rank %d",
            entry_dir.name,
            rank_i,
        )

    # -----------------------
    # Batch analysis (+ DockQ injection into EACH rank) + PROGRESS LOGGING
    # -----------------------
    def batch_analysis(
        self,
        batch_dir: Union[str, Path],
        *,
        delete_zips: bool = True,
        mapping_by_pdbid: Optional[Dict[str, Dict[str, str]]] = None,
        native_pdb_dir: Optional[Path] = None,
        progress_step_pct: int = 10,
    ) -> Dict[str, Any]:
        """
        progress_step_pct=10 => log at 10%,20%,...,100%
        """
        batch_result: Dict[str, Any] = {}
        entry_dirs, _ = _prepare_batch_dirs(batch_dir, delete_zips=delete_zips)

        n = len(entry_dirs)
        if n == 0:
            LOGGER.warning("No entry directories found under %s", batch_dir)
            return {}

        LOGGER.info("Processing %d entries...", n)
        progress = ProgressLogger(total=n, step_pct=progress_step_pct)
        stats = BatchStats()

        for i, entry_dir in enumerate(entry_dirs, start=1):
            progress.tick(i)
            name = entry_dir.name
            real_entry_dir = _resolve_entry_dir(entry_dir)

            try:
                entry_out = self._process_one_entry(
                    real_entry_dir=real_entry_dir,
                    entry_dir_name=name,
                    mapping_by_pdbid=mapping_by_pdbid,
                    native_pdb_dir=native_pdb_dir,
                    stats=stats,
                )
                batch_result[name] = entry_out
                stats.ok += 1
                if not entry_out:
                    stats.empty += 1
            except Exception as e:
                self.log_error(f"Batch error in entry {name}: {e}")
                batch_result[name] = {}
                stats.error += 1

        LOGGER.info(
            "DONE. ok=%d empty=%d error=%d | dockq_ok=%d dockq_fail=%d",
            stats.ok,
            stats.empty,
            stats.error,
            stats.dockq_ok,
            stats.dockq_fail,
        )
        return batch_result

    def _process_one_entry(
        self,
        *,
        real_entry_dir: Path,
        entry_dir_name: str,
        mapping_by_pdbid: Optional[Dict[str, Dict[str, str]]],
        native_pdb_dir: Optional[Path],
        stats: BatchStats,
    ) -> Dict[str, Any]:
        entry_out = self.all_analysis(real_entry_dir)

        if mapping_by_pdbid is None or native_pdb_dir is None:
            return entry_out

        pid = entry_dir_name.split("_")[0].lower()
        mapping = mapping_by_pdbid.get(pid)
        exp_pdb = find_native_pdb_file(native_pdb_dir, pid)

        if mapping is None:
            LOGGER.debug("DockQ: no mapping for %s", pid)
            return entry_out
        if exp_pdb is None:
            LOGGER.debug(
                "DockQ: native PDB missing for %s under %s",
                pid,
                native_pdb_dir,
            )
            return entry_out

        dq_stats = inject_dockq_into_entry(
            entry_out=entry_out,
            entry_dir_name=entry_dir_name,
            mapping=mapping,
            exp_pdb=exp_pdb,
            round_digits=self.round_digits,
        )
        stats.dockq_ok += dq_stats.ok
        stats.dockq_fail += dq_stats.fail
        return entry_out

    # -----------------------
    # CLI
    # -----------------------
    @staticmethod
    def args() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Extract summary metrics from JSON and PDB files"
        )
        parser.add_argument("--json", type=str, help="Path to the JSON file")
        parser.add_argument("--pdb", type=str, help="Path to the PDB file")
        parser.add_argument(
            "--chain",
            type=str,
            choices=["last", "first", "none"],
            default=_DEFAULT_BASE_CONFIG.peptide_chain_position,
            help="Which chain to consider as peptide",
        )
        parser.add_argument(
            "--cutoff",
            type=float,
            default=_DEFAULT_BASE_CONFIG.cutoff,
            help="Distance cutoff (Å) for defining interface residues",
        )
        parser.add_argument(
            "--round",
            type=int,
            default=_DEFAULT_ANALYSIS_CONFIG.round_digits,
            help="Number of decimal places to round metrics",
        )
        parser.add_argument(
            "--entry_dir",
            type=str,
            help="Path to a single entry directory",
        )
        parser.add_argument(
            "--batch_dir",
            type=str,
            help="Path to a batch directory OR a .zip containing it",
        )
        parser.add_argument(
            "--mapping_csv",
            type=str,
            default=None,
            help=(
                "Optional CSV with columns pdb_id,mapping. If provided, downloads "
                "native PDBs and computes DockQ per rank."
            ),
        )
        parser.add_argument(
            "--progress_pct",
            type=int,
            default=10,
            help="Progress logging step in percent (default: 10).",
        )
        parser.add_argument("--pdockq2_d0", type=float, default=10.0)
        parser.add_argument("--pdockq2_sym_pae", action="store_true")
        parser.add_argument("--verbose", action="store_true")
        return parser


# ---------------------------------------------------------------------------
# File + zip utilities
# ---------------------------------------------------------------------------


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4)


def _has_any_af_files(d: Path) -> bool:
    return bool(list(d.glob("*_scores_*.json"))) and bool(
        list(d.glob("*relaxed_*.pdb"))
    )


def _resolve_entry_dir(entry_dir: Path, max_depth: int = 3) -> Path:
    cur = Path(entry_dir)
    for _ in range(max_depth):
        if _has_any_af_files(cur):
            return cur

        same = cur / cur.name
        if same.is_dir() and _has_any_af_files(same):
            return same

        subs = [p for p in cur.iterdir() if p.is_dir()]
        if len(subs) == 1:
            cur = subs[0]
            continue

        return cur
    return cur


def _unzip_zip_to_dir(zip_path: Path, out_dir: Path) -> Path:
    zip_path = Path(zip_path)
    out_dir = Path(out_dir)

    if out_dir.exists():
        return out_dir
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip not found: {zip_path}")

    tmp = out_dir.with_name(out_dir.name + "__tmp_extract")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp)

        candidate: Optional[Path] = None

        inner = tmp / "outputdir" / "outputdir"
        if inner.is_dir():
            items = [p for p in inner.iterdir()]
            if len(items) == 1 and items[0].is_dir():
                candidate = items[0]

        if candidate is None:
            top_dirs = [p for p in tmp.iterdir() if p.is_dir()]
            top_files = [p for p in tmp.iterdir() if p.is_file()]
            if len(top_dirs) == 1 and not top_files:
                candidate = top_dirs[0]

        if candidate is not None:
            shutil.move(str(candidate), str(out_dir))
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            for p in tmp.iterdir():
                shutil.move(str(p), str(out_dir / p.name))
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)

    return out_dir


def _unzip_all_zips_in_folder(folder: Path, *, delete_zips: bool) -> List[Path]:
    folder = Path(folder)
    extracted: List[Path] = []
    zips = sorted(folder.glob("*.zip"))
    if not zips:
        return extracted

    LOGGER.info("Unzipping %d zip(s) in %s", len(zips), folder)

    for z in zips:
        target = folder / z.stem
        _unzip_zip_to_dir(z, target)
        extracted.append(z)
        if delete_zips:
            try:
                z.unlink()
            except Exception as e:
                LOGGER.warning("Failed to delete zip %s: %s", z, e)

    return extracted


def _normalize_batch_root(batch_dir: Union[str, Path]) -> Path:
    batch_path = Path(batch_dir)
    if not batch_path.exists():
        raise FileNotFoundError(f"Batch path not found: {batch_path}")

    if batch_path.is_file() and batch_path.suffix == ".zip":
        out_dir = batch_path.parent / batch_path.stem
        LOGGER.info("Unzipping batch archive %s -> %s", batch_path, out_dir)
        _unzip_zip_to_dir(batch_path, out_dir)
        return out_dir

    if batch_path.is_dir():
        return batch_path

    raise ValueError(f"Unsupported batch_dir type: {batch_path}")


def _prepare_batch_dirs(
    batch_dir: Union[str, Path],
    *,
    delete_zips: bool,
) -> Tuple[List[Path], List[Path]]:
    root = _normalize_batch_root(batch_dir)
    extracted_zip_paths: List[Path] = []
    extracted_zip_paths.extend(_unzip_all_zips_in_folder(root, delete_zips=delete_zips))

    entry_dirs: List[Path] = []
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        extracted_zip_paths.extend(
            _unzip_all_zips_in_folder(p, delete_zips=delete_zips)
        )
        entry_dirs.append(p)

    return entry_dirs, extracted_zip_paths


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)s | %(message)s")


def main() -> None:
    parser = Analysis.args()
    args = parser.parse_args()
    _setup_logging(bool(getattr(args, "verbose", False)))

    has_batch = bool(args.batch_dir)
    has_entry = bool(args.entry_dir)
    has_single = bool(args.json and args.pdb)

    modes = sum([has_batch, has_entry, has_single])
    if modes == 0:
        parser.print_help()
        raise SystemExit(2)
    if modes > 1:
        raise SystemExit(
            "Provide exactly one mode: --batch_dir OR --entry_dir OR (--json AND --pdb)."
        )

    mapping_by_pdbid: Optional[Dict[str, Dict[str, str]]] = None
    native_pdb_dir: Optional[Path] = None

    if args.mapping_csv:
        mapping_by_pdbid = read_mapping_csv(args.mapping_csv)

        if args.batch_dir:
            native_pdb_dir = native_pdb_dir_for_batch_path(args.batch_dir)
        elif args.entry_dir:
            native_pdb_dir = Path(args.entry_dir).parent / "pdb"
        else:
            native_pdb_dir = Path(args.pdb).resolve().parent / "pdb"

        ensure_native_pdbs(mapping_by_pdbid, native_pdb_dir)

    if args.batch_dir:
        batch_root = _normalize_batch_root(args.batch_dir)
        analysis = Analysis(
            json_path=None,
            pdb_path=None,
            peptide_chain_position=args.chain,
            distance_cutoff=args.cutoff,
            round_digits=args.round,
            pdockq2_d0=args.pdockq2_d0,
            pdockq2_sym_pae=bool(args.pdockq2_sym_pae),
        )
        result = analysis.batch_analysis(
            batch_root,
            delete_zips=True,
            mapping_by_pdbid=mapping_by_pdbid,
            native_pdb_dir=native_pdb_dir,
            progress_step_pct=int(args.progress_pct),
        )
        out_path = Path(batch_root) / "result.json"
        LOGGER.info("Writing result to %s", out_path)
        _write_json(out_path, result)
        return

    if args.entry_dir:
        analysis = Analysis(
            json_path=None,
            pdb_path=None,
            peptide_chain_position=args.chain,
            distance_cutoff=args.cutoff,
            round_digits=args.round,
            pdockq2_d0=args.pdockq2_d0,
            pdockq2_sym_pae=bool(args.pdockq2_sym_pae),
        )
        result = analysis.all_analysis(args.entry_dir)
        out_path = Path(args.entry_dir) / "result.json"
        _write_json(out_path, result)
        return

    analysis = Analysis(
        json_path=args.json,
        pdb_path=args.pdb,
        peptide_chain_position=args.chain,
        distance_cutoff=args.cutoff,
        round_digits=args.round,
        pdockq2_d0=args.pdockq2_d0,
        pdockq2_sym_pae=bool(args.pdockq2_sym_pae),
    )
    result = analysis.single_analysis()
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
