from __future__ import annotations

import ast
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mapping CSV
# ---------------------------------------------------------------------------


def _parse_mapping_cell(raw: str, *, pdb_id: str) -> Dict[str, str]:
    raw = (raw or "").strip()
    if not raw:
        return {}

    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return {str(k): str(v) for k, v in obj.items()}
    except Exception:
        pass

    try:
        obj = ast.literal_eval(raw)
    except Exception as e:
        raise ValueError(
            f"Failed to parse mapping for {pdb_id} from {raw!r}: {e}"
        ) from e

    if not isinstance(obj, dict):
        raise ValueError(
            f"Mapping for {pdb_id} must be a dict-like string, got: {type(obj)!r}"
        )
    return {str(k): str(v) for k, v in obj.items()}


def read_mapping_csv(csv_path: Union[str, Path]) -> Dict[str, Dict[str, str]]:
    """
    Read a CSV containing:
        pdb_id,mapping
        1avf,"{'A': 'J', 'B': 'Q'}"

    Returns:
        {pdb_id_lower: {chain1: chain2}} (direction resolved later per entry).
    """
    import csv

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(path)

    out: Dict[str, Dict[str, str]] = {}
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            pid = (row.get("pdb_id") or "").strip().lower()
            if not pid:
                continue
            mapping = _parse_mapping_cell(row.get("mapping") or "", pdb_id=pid)
            if mapping:
                out[pid] = mapping
    return out


# ---------------------------------------------------------------------------
# Native PDB cache + chain helpers
# ---------------------------------------------------------------------------


def native_pdb_dir_for_batch_path(batch_dir: Union[str, Path]) -> Path:
    p = Path(batch_dir)
    return p.parent / "pdb"


def find_native_pdb_file(native_pdb_dir: Path, pdb_id: str) -> Optional[Path]:
    pid = pdb_id.lower()
    candidates = [
        native_pdb_dir / f"{pid}.pdb",
        native_pdb_dir / f"{pid.upper()}.pdb",
        native_pdb_dir / f"{pid.lower()}.pdb",
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    hits = sorted(native_pdb_dir.glob(f"{pid}*.pdb"))
    return hits[0] if hits else None


def ensure_native_pdbs(
    mapping_by_pdbid: Dict[str, Dict[str, str]],
    native_pdb_dir: Path,
) -> None:
    """
    Download missing native PDBs using pepkit.query.request.retrieve_pdb
    """
    native_pdb_dir.mkdir(parents=True, exist_ok=True)

    try:
        from pepkit.query.request import retrieve_pdb  # type: ignore
    except Exception as e:
        raise ImportError(
            "pepkit.query.request.retrieve_pdb is required for --mapping_csv mode, "
            "but could not be imported."
        ) from e

    missing = [
        pid
        for pid in sorted(mapping_by_pdbid.keys())
        if find_native_pdb_file(native_pdb_dir, pid) is None
    ]
    if not missing:
        LOGGER.info(
            "Native PDB cache OK (%d PDBs present in %s).",
            len(mapping_by_pdbid),
            native_pdb_dir,
        )
        return

    LOGGER.info(
        "Retrieving %d missing native PDB(s) into %s ...",
        len(missing),
        native_pdb_dir,
    )
    ok = 0
    for pid in missing:
        try:
            retrieve_pdb(pdb_id=pid, outdir=str(native_pdb_dir))
            ok += 1
        except Exception as e:
            LOGGER.warning("Failed to retrieve PDB %s: %s", pid, e)
    LOGGER.info("Native PDB retrieval: %d/%d succeeded.", ok, len(missing))


def get_chain_ids_from_pdb(pdb_path: Path) -> List[str]:
    ids: List[str] = []
    try:
        with open(pdb_path, "r", encoding="utf-8", errors="ignore") as fh:
            for ln in fh:
                if not (ln.startswith("ATOM") or ln.startswith("HETATM")):
                    continue
                ch = ln[21].strip() or "_"
                if ch not in ids:
                    ids.append(ch)
    except Exception:
        return ids
    return ids


def _invert_map_1to1(d: Dict[str, str]) -> Dict[str, str]:
    inv: Dict[str, str] = {}
    for k, v in d.items():
        prev = inv.get(v)
        if prev is not None and prev != k:
            raise ValueError(
                f"Cannot invert mapping (collision): {v!r} -> {prev!r} vs {k!r}"
            )
        inv[v] = k
    return inv


def ensure_exp_to_pred_mapping(
    mapping: Dict[str, str],
    *,
    exp_pdb: Path,
    pred_pdb: Path,
) -> Tuple[Dict[str, str], str]:
    """
    Ensure mapping is experimental_chain -> predicted_chain for DockQ.
    """
    exp_ch = set(get_chain_ids_from_pdb(exp_pdb))
    pred_ch = set(get_chain_ids_from_pdb(pred_pdb))

    keys = set(mapping.keys())
    vals = set(mapping.values())

    if keys.issubset(exp_ch) and vals.issubset(pred_ch):
        return mapping, "exp->pred"
    if keys.issubset(pred_ch) and vals.issubset(exp_ch):
        return _invert_map_1to1(mapping), "auto-inverted (was pred->exp)"

    keys_in_exp = sum(1 for k in keys if k in exp_ch)
    keys_in_pred = sum(1 for k in keys if k in pred_ch)

    if keys_in_pred > keys_in_exp:
        try:
            return _invert_map_1to1(mapping), "heuristic-inverted"
        except Exception:
            return mapping, "ambiguous (kept as-is; inversion failed)"

    return mapping, "ambiguous (kept as-is)"


# ---------------------------------------------------------------------------
# DockQ compute + injection
# ---------------------------------------------------------------------------


def compute_dockq_for_rank(
    *,
    exp_pdb: Path,
    pred_pdb: Path,
    chain_map: Dict[str, str],
) -> Dict[str, float]:
    """
    Returns:
      {"total_dockq": float, "avg_dockq": float}
    """
    try:
        from DockQ.DockQ import load_PDB, run_on_all_native_interfaces  # type: ignore
    except Exception as e:
        raise ImportError(
            "DockQ is required to compute dockq but could not be imported."
        ) from e

    native_obj = load_PDB(str(exp_pdb))
    model_obj = load_PDB(str(pred_pdb))

    interfaces, total = run_on_all_native_interfaces(
        model_structure=model_obj,
        native_structure=native_obj,
        chain_map=chain_map,
    )
    n_interfaces = len(interfaces) if isinstance(interfaces, dict) else 0
    denom = max(1, int(n_interfaces))

    total_f = float(total)
    return {"total_dockq": total_f, "avg_dockq": total_f / denom}


def iter_rank_dicts(entry_out: Dict[str, Any]) -> Iterable[Tuple[str, Dict[str, Any]]]:
    for k, v in entry_out.items():
        if isinstance(k, str) and k.startswith("rank") and isinstance(v, dict):
            yield k, v


@dataclass
class DockQInjectionStats:
    ok: int = 0
    fail: int = 0


def inject_dockq_into_entry(
    *,
    entry_out: Dict[str, Any],
    entry_dir_name: str,
    mapping: Dict[str, str],
    exp_pdb: Path,
    round_digits: int,
    stats: Optional[DockQInjectionStats] = None,
) -> DockQInjectionStats:
    """
    Mutates entry_out in-place:
      - ensures total_dockq, avg_dockq exist
      - replaces per-rank _pred_pdb_path with computed scores
    """
    if stats is None:
        stats = DockQInjectionStats()

    for rk, rk_dict in iter_rank_dicts(entry_out):
        rk_dict.setdefault("total_dockq", float("nan"))
        rk_dict.setdefault("avg_dockq", float("nan"))

        pred_pdb_path = rk_dict.get("_pred_pdb_path")
        if not pred_pdb_path:
            continue

        pred_pdb = Path(str(pred_pdb_path))
        if not pred_pdb.exists():
            continue

        try:
            fixed_map, note = ensure_exp_to_pred_mapping(
                dict(mapping), exp_pdb=exp_pdb, pred_pdb=pred_pdb
            )
            dq = compute_dockq_for_rank(
                exp_pdb=exp_pdb,
                pred_pdb=pred_pdb,
                chain_map=fixed_map,
            )
            rk_dict["total_dockq"] = round(float(dq["total_dockq"]), round_digits)
            rk_dict["avg_dockq"] = round(float(dq["avg_dockq"]), round_digits)
            rk_dict.pop("_pred_pdb_path", None)

            stats.ok += 1
            LOGGER.debug("DockQ OK %s %s (%s)", entry_dir_name, rk, note)
        except Exception as e:
            stats.fail += 1
            LOGGER.warning("DockQ failed for %s %s: %s", entry_dir_name, rk, e)

    return stats
