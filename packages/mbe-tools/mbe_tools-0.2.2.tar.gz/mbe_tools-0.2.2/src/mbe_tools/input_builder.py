from __future__ import annotations
import re
from typing import Dict, List, Optional, Tuple

GeomAtom = Tuple[str, float, float, float, bool]
ExternalCharge = Tuple[float, float, float, float]


def _element_from_token(token: str) -> str:
    letters = re.findall(r"[A-Za-z]+", token)
    if not letters:
        return ""
    return letters[-1].capitalize()


def _parse_geom_atoms(geom_block: str) -> List[GeomAtom]:
    atoms: List[GeomAtom] = []
    for line in geom_block.strip().splitlines():
        ln = line.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split()
        token = parts[0] if parts else ""
        elem = _element_from_token(token) if token else ""
        ghost = token.startswith("@")
        coords: List[float] = []
        if len(parts) >= 4:
            try:
                coords = [float(parts[1]), float(parts[2]), float(parts[3])]
            except ValueError:
                coords = []
        if len(coords) < 3:
            # Fallback: grab the first three numeric tokens anywhere in the line
            coords = []
            for m in re.finditer(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", ln):
                try:
                    coords.append(float(m.group(0)))
                except ValueError:
                    continue
                if len(coords) >= 3:
                    break
        if len(coords) >= 3:
            atoms.append((elem, coords[0], coords[1], coords[2], ghost))
    return atoms


def _external_charges_for_giee(geom_block: str, charges: Dict[str, float]) -> List[ExternalCharge]:
    entries: List[ExternalCharge] = []
    if not charges:
        return entries
    charges_upper: Dict[str, float] = {}
    for k, v in charges.items():
        if k is None:
            continue
        key = str(k).strip().upper()
        if not key:
            continue
        try:
            charges_upper[key] = float(v)
        except (TypeError, ValueError):
            continue

    # Only attach embedding charges to ghost atoms (prefixed with '@')
    for elem, x, y, z, ghost in _parse_geom_atoms(geom_block):
        if not ghost or not elem:
            continue
        key = elem.upper()
        if key in charges_upper:
            entries.append((x, y, z, charges_upper[key]))
    return entries


def _external_charges_from_file(path: str) -> List[ExternalCharge]:
    entries: List[ExternalCharge] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            try:
                x, y, z, q = map(float, parts[:4])
            except ValueError:
                continue
            entries.append((x, y, z, q))
    if not entries:
        raise ValueError(f"No external charges parsed from file: {path}")
    return entries


def _read_geom(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def render_qchem_input(
    geom_block: str,
    *,
    method: str,
    basis: str,
    charge: int = 0,
    multiplicity: int = 1,
    thresh: Optional[float] = None,
    tole: Optional[float] = None,
    scf_convergence: Optional[str] = None,
    xc_grid: Optional[str] = None,
    rem_extra: Optional[str] = None,
    sym_ignore: bool = True,
    external_charges: Optional[List[ExternalCharge]] = None,
) -> str:
    """Render a minimal Q-Chem input from a geometry block."""
    lines = [
        "$molecule",
        f"{charge} {multiplicity}",
        geom_block.strip(),
        "$end",
        "",
        "$rem",
        f"  method        {method}",
        f"  basis         {basis}",
    ]
    if thresh is not None:
        lines.append(f"  thresh        {thresh:g}")
    if tole is not None:
        lines.append(f"  tole          {tole:g}")
    if scf_convergence is not None:
        lines.append(f"  scf_convergence {scf_convergence}")
    if xc_grid is not None:
        lines.append(f"  xc_grid       {xc_grid}")
    if sym_ignore:
        lines.append("  SYM_IGNORE    true")
    if rem_extra:
        for ln in rem_extra.strip().splitlines():
            ln = ln.strip()
            if ln:
                lines.append(f"  {ln}")
    lines.append("$end")
    if external_charges:
        lines.append("")
        lines.append("$external_charges")
        for x, y, z, q in external_charges:
            lines.append(f"  {x:.10f}  {y:.10f}  {z:.10f}  {q:.10f}")
        lines.append("$end")
    return "\n".join(lines) + "\n"


def render_orca_input(
    geom_block: str,
    *,
    method: str,
    basis: str,
    charge: int = 0,
    multiplicity: int = 1,
    grid: Optional[str] = None,
    scf_convergence: Optional[str] = None,
    keyword_line_extra: Optional[str] = None,
) -> str:
    """Render a minimal ORCA input from a geometry block."""
    header_parts = [method, basis]
    if grid:
        header_parts.append(grid)
    if scf_convergence:
        header_parts.append(scf_convergence)
    if keyword_line_extra:
        header_parts.append(keyword_line_extra.strip())
    header = "! " + " ".join(header_parts)
    lines = [
        header,
        f"* xyz {charge} {multiplicity}",
        geom_block.strip(),
        "*",
    ]
    return "\n".join(lines) + "\n"


def build_input_from_geom(
    geom_path: str,
    *,
    backend: str,
    method: str,
    basis: str,
    charge: int = 0,
    multiplicity: int = 1,
    thresh: Optional[float] = None,
    tole: Optional[float] = None,
    scf_convergence: Optional[str] = None,
    xc_grid: Optional[str] = None,
    grid: Optional[str] = None,
    rem_extra: Optional[str] = None,
    keyword_line_extra: Optional[str] = None,
    sym_ignore: bool = True,
    giee_charges: Optional[Dict[str, float]] = None,
    gdee_path: Optional[str] = None,
) -> str:
    geom = _read_geom(geom_path)
    name = backend.lower()
    if name in ("qchem", "q-chem"):
        if giee_charges is not None and gdee_path:
            raise ValueError("Use only one of giee_charges or gdee_path for external charges")
        external_charges = None
        if giee_charges is not None:
            external_charges = _external_charges_for_giee(geom, giee_charges)
        elif gdee_path:
            external_charges = _external_charges_from_file(gdee_path)
        return render_qchem_input(
            geom,
            method=method,
            basis=basis,
            charge=charge,
            multiplicity=multiplicity,
            thresh=thresh,
            tole=tole,
            scf_convergence=scf_convergence,
            xc_grid=xc_grid,
            rem_extra=rem_extra,
            sym_ignore=sym_ignore,
            external_charges=external_charges,
        )
    if (giee_charges is not None or gdee_path) and name != "qchem" and name != "q-chem":
        raise ValueError("External charges are only supported for the Q-Chem backend")

    if name == "orca":
        return render_orca_input(
            geom,
            method=method,
            basis=basis,
            charge=charge,
            multiplicity=multiplicity,
            grid=grid,
            scf_convergence=scf_convergence,
            keyword_line_extra=keyword_line_extra,
        )
    raise ValueError(f"Unknown backend for input build: {backend}")
