"""PEAS schema tests: meta-validation, full cross-repo $ref resolution, per-discriminator
fixtures, and regression guards for the 2026-07 review fixes (H1/H2/H13).

PEAS is the base of the whole family (9 consumers) and previously had no tests. Run from
the PEAS repo root with the sibling repos checked out alongside (the PSMA workspace layout):

    pip install pytest jsonschema referencing
    pytest tests/ -q
"""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO = Path(__file__).resolve().parents[1]
WORKSPACE = REPO.parent
SIBLINGS = ["PEAS", "MAS", "CAS", "SAS", "RAS", "AAS", "CTAS", "CONAS", "TAS", "CIAS", "COAS"]
PEAS_SCHEMAS = sorted(REPO.glob("schemas/**/*.json"))


def build_registry():
    resources = []
    for repo in SIBLINGS:
        sdir = WORKSPACE / repo / "schemas"
        if not sdir.is_dir():
            continue
        for path in sdir.rglob("*.json"):
            doc = json.loads(path.read_text())
            if "$id" in doc:
                resources.append((doc["$id"], Resource.from_contents(doc, default_specification=DRAFT202012)))
    return Registry().with_resources(resources)


@pytest.fixture(scope="session")
def registry():
    return build_registry()


@pytest.fixture(scope="session")
def peas(registry):
    return Draft202012Validator(json.loads((REPO / "schemas/peas.json").read_text()), registry=registry)


def valid(v, doc):
    return not list(v.iter_errors(doc))


# --- hygiene ------------------------------------------------------------------


@pytest.mark.parametrize("path", PEAS_SCHEMAS, ids=lambda p: str(p.relative_to(REPO)))
def test_meta_validates(path):
    Draft202012Validator.check_schema(json.loads(path.read_text()))


def test_every_ref_resolves(registry):
    def walk(node, out):
        if isinstance(node, dict):
            if "$ref" in node:
                out.append(node["$ref"])
            for v in node.values():
                walk(v, out)
        elif isinstance(node, list):
            for v in node:
                walk(v, out)
    for path in PEAS_SCHEMAS:
        doc = json.loads(path.read_text())
        refs = []
        walk(doc, refs)
        resolver = registry.resolver(base_uri=doc["$id"])
        for ref in refs:
            resolver.lookup(ref)  # raises Unresolvable if a target is missing


def test_no_orphan_utils_defs(registry):
    """Every utils.json $def is referenced internally or by >=1 sibling. Guards against the
    irdi / coolingMethod / scalarMatrixAtFrequency orphan class."""
    utils_text = (REPO / "schemas/utils.json").read_text()
    defs = set(json.loads(utils_text)["$defs"])
    seen = set()
    for repo in SIBLINGS:
        sdir = WORKSPACE / repo / "schemas"
        if not sdir.is_dir():
            continue
        for path in sdir.rglob("*.json"):
            text = path.read_text()
            is_peas_utils = path == (REPO / "schemas/utils.json")
            for d in defs:
                # cross-file refs use the qualified form; intra-utils refs use the bare pointer.
                if f"utils.json#/$defs/{d}" in text or (is_peas_utils and f'"#/$defs/{d}"' in text):
                    seen.add(d)
    orphans = defs - seen
    assert not orphans, f"orphan utils $defs (referenced nowhere): {sorted(orphans)}"


# --- per-discriminator positive fixtures --------------------------------------

def _mas_sample():
    return json.loads(sorted((WORKSPACE / "MAS/samples/complete").glob("*.json"))[0].read_text())


def test_mas_sample_is_valid_peas(peas):
    # H1 regression: a full MAS document must validate as PEAS.
    assert valid(peas, _mas_sample())


BEHAVIORAL_NATURES = [
    {"nature": "flux", "expression": "0.001*atan(i)"},
    {"nature": "charge", "expression": "1e-9*v"},
]


@pytest.mark.parametrize("beh", BEHAVIORAL_NATURES, ids=lambda b: b["nature"])
def test_behavioral_validates(peas, beh):
    # H2 regression: behavioral docs validate on their own DR branch, not via a CONAS accident.
    doc = {"inputs": {"designRequirements": {"name": "x"}}, "behavioral": beh}
    assert valid(peas, doc)


def test_varistor_validates_as_peas(peas):
    # Q5 regression: varistors are first-class PEAS citizens via their own branch.
    doc = json.loads((WORKSPACE / "RAS/examples/03_varistor_b72214.json").read_text())
    assert valid(peas, doc)


def test_varistor_empty_seed_validates(peas):
    doc = {"inputs": {"designRequirements": {"deviceType": "varistor",
                                              "ratedContinuousVoltage": 275.0,
                                              "minimumPeakSurgeCurrent": 100.0}},
           "varistor": {}}
    assert valid(peas, doc)


def test_transmission_line_validates(peas):
    doc = {
        "inputs": {"designRequirements": {}},
        "transmissionLine": {
            "kind": "lossy", "length": 0.1,
            "perUnitLength": {"resistance": 0.1, "inductance": 1e-7, "conductance": 1e-9, "capacitance": 1e-10},
        },
    }
    assert valid(peas, doc)


# --- negative fixtures --------------------------------------------------------


def test_junk_dr_key_on_behavioral_rejected(peas):
    # H2: the behavioral DR branch is closed — a foreign family field must not sneak in.
    doc = {"inputs": {"designRequirements": {"capacitance": {"nominal": 1e-6}}},
           "behavioral": {"nature": "flux", "expression": "i"}}
    assert not valid(peas, doc)


def test_dimension_with_tolerance_typo_rejected(peas):
    # H13: dimensionWithTolerance is sealed — a typo'd key is no longer silently accepted.
    doc = {"inputs": {"designRequirements": {"capacitance": {"nomnial": 1e-6}}},
           "capacitor": {"capacitor": {}}}
    assert not valid(peas, doc)


def test_missing_design_requirements_rejected(peas):
    assert not valid(peas, {"inputs": {}, "behavioral": {"nature": "flux", "expression": "i"}})


def test_zero_discriminators_rejected(peas):
    assert not valid(peas, {"inputs": {"designRequirements": {}}})


def test_two_discriminators_rejected(peas):
    # Two seed-valid component branches both match the top-level oneOf -> rejected
    # (oneOf = exactly one), independent of whether the root object is closed.
    doc = {"inputs": {"designRequirements": {}},
           "capacitor": {"capacitor": {}},
           "resistor": {"resistor": {}}}
    assert not valid(peas, doc)
