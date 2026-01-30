from mbe_tools.input_builder import build_input_from_geom, render_orca_input, render_qchem_input


def test_render_qchem_includes_thresh_tole():
    geom = "H 0 0 0"
    text = render_qchem_input(
        geom,
        method="wb97m-v",
        basis="def2",
        charge=0,
        multiplicity=1,
        thresh=14,
        tole=8,
        scf_convergence="tight",
    )
    assert "thresh        14" in text
    assert "tole          8" in text
    assert "scf_convergence tight" in text


def test_render_orca_includes_grid_and_scf():
    geom = "H 0 0 0"
    text = render_orca_input(
        geom,
        method="wb97m-v",
        basis="def2",
        charge=0,
        multiplicity=1,
        grid="GRID5",
        scf_convergence="TightSCF",
        keyword_line_extra="D3BJ",
    )
    header = text.splitlines()[0]
    assert "GRID5" in header
    assert "TightSCF" in header
    assert "D3BJ" in header


def test_render_qchem_sym_ignore_default_and_toggle():
    geom = "H 0 0 0"
    default_text = render_qchem_input(geom, method="m", basis="b", charge=0, multiplicity=1)
    assert "SYM_IGNORE" in default_text

    disabled_text = render_qchem_input(geom, method="m", basis="b", charge=0, multiplicity=1, sym_ignore=False)
    assert "SYM_IGNORE" not in disabled_text


def test_build_input_with_giee_external_charges(tmp_path):
    geom_path = tmp_path / "g.geom"
    geom_path.write_text("@O 0.0 0.0 0.0\n@H 0.0 0.0 1.0\nC 1.0 0.0 0.0\n", encoding="utf-8")

    text = build_input_from_geom(
        str(geom_path),
        backend="qchem",
        method="m",
        basis="b",
        giee_charges={"O": 0.25, "H": -0.1},
    )

    assert "$external_charges" in text
    assert "0.0000000000  0.0000000000  0.0000000000  0.2500000000" in text
    assert "0.0000000000  0.0000000000  1.0000000000  -0.1000000000" in text
    assert "1.0000000000  0.0000000000  0.0000000000" not in text  # non-mapped element excluded


def test_giee_applies_only_to_ghost_atoms(tmp_path):
    geom_path = tmp_path / "g.geom"
    geom_path.write_text("@O 0.0 0.0 0.0\nO 0.0 0.0 1.0\n@H 1.0 0.0 0.0\nH 0.0 1.0 0.0\n", encoding="utf-8")

    text = build_input_from_geom(
        str(geom_path),
        backend="qchem",
        method="m",
        basis="b",
        giee_charges={"O": 0.25, "H": -0.1},
    )

    assert "$external_charges" in text
    ext_block = text.split("$external_charges", 1)[1]
    ext_lines = [ln.strip() for ln in ext_block.splitlines() if ln.strip() and not ln.strip().startswith("$")]
    coords = [tuple(map(float, ln.split())) for ln in ext_lines]

    assert (0.0, 0.0, 0.0, 0.25) in coords  # ghost @O
    assert (1.0, 0.0, 0.0, -0.1) in coords  # ghost @H
    assert (0.0, 0.0, 1.0, 0.25) not in coords  # non-ghost O skipped
    assert (0.0, 1.0, 0.0, -0.1) not in coords  # non-ghost H skipped


def test_build_input_with_gdee_external_charges(tmp_path):
    geom_path = tmp_path / "g.geom"
    geom_path.write_text("O 0 0 0\nH 0 0 1\n", encoding="utf-8")

    charges_path = tmp_path / "charges.txt"
    charges_path.write_text("1.0 2.0 3.0 0.5\n-1.0 -2.0 -3.0 -0.5\n", encoding="utf-8")

    text = build_input_from_geom(
        str(geom_path),
        backend="qchem",
        method="m",
        basis="b",
        gdee_path=str(charges_path),
    )

    assert "$external_charges" in text
    assert "1.0000000000  2.0000000000  3.0000000000  0.5000000000" in text
    assert "-1.0000000000  -2.0000000000  -3.0000000000  -0.5000000000" in text
