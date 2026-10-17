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
SIBLINGS = ["PEAS", "MAS", "CAS", "SAS", "RAS", "AAS", "CTAS", "CONAS", "TDAS", "EMAS", "TMAS", "TAS", "CIAS", "COAS"]
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
    {"nature": "coupledInductors",
     "inductanceMatrix": [[1e-7, 2e-8], [2e-8, 5e-8]],
     "seriesResistance": [1e-3, 1e-3]},
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


def test_thermistor_validates_as_peas(peas):
    # Thermistors are first-class PEAS citizens via their own branch (mirrors varistor).
    doc = json.loads((WORKSPACE / "RAS/examples/04_thermistor_sl22.json").read_text())
    assert valid(peas, doc)


def test_thermistor_empty_seed_validates(peas):
    doc = {"inputs": {"designRequirements": {"deviceType": "thermistor",
                                              "resistanceAt25C": {"nominal": 10.0},
                                              "minimumSteadyStateCurrent": 5.0}},
           "thermistor": {}}
    assert valid(peas, doc)


PROTECTION_EXAMPLES = sorted((WORKSPACE / "EMAS/examples").glob("*_protection_*.json"))


@pytest.mark.parametrize("path", PROTECTION_EXAMPLES, ids=lambda p: p.name)
def test_protection_validates_as_peas(peas, path):
    # EMAS protection (fuse, PPTC, GDT, fuse holder, thermal cut-off) is a first-class PEAS citizen.
    doc = json.loads(path.read_text())
    assert valid(peas, {"inputs": doc["inputs"], "protection": doc["protection"]})


def test_protection_examples_present():
    # A deleted example must not turn the parametrized test above into "no cases".
    assert len(PROTECTION_EXAMPLES) >= 5


def test_protection_empty_seed_validates(peas):
    doc = {"inputs": {"designRequirements": {"deviceType": "protection", "allowedFamilies": ["fuse"]}},
           "protection": {}}
    assert valid(peas, doc)


def test_protection_design_requirements_pinned_to_emas(peas):
    # The allOf pin: a protection document cannot carry another family's requirements.
    doc = {"inputs": {"designRequirements": {"deviceType": "varistor", "ratedContinuousVoltage": 275.0,
                                              "minimumPeakSurgeCurrent": 100.0}},
           "protection": {}}
    assert not valid(peas, doc)


THERMAL_EXAMPLES = sorted((WORKSPACE / "TMAS/examples").glob("*.json"))


@pytest.mark.parametrize("path", THERMAL_EXAMPLES, ids=lambda p: p.name)
def test_thermal_management_validates_as_peas(peas, path):
    # TMAS parts (heatsink, interface material, fan, mounting hardware) are first-class PEAS citizens.
    doc = json.loads(path.read_text())
    assert valid(peas, {"inputs": doc["inputs"], "thermalManagement": doc["thermalManagement"]})


def test_thermal_management_examples_present():
    # A deleted example must not turn the parametrized test above into "no cases".
    assert len(THERMAL_EXAMPLES) >= 8


def test_thermal_management_empty_seed_validates(peas):
    doc = {"inputs": {"designRequirements": {"name": "TO-220 heatsink", "family": "heatsink"}},
           "thermalManagement": {}}
    assert valid(peas, doc)


def test_thermal_management_design_requirements_pinned_to_tmas(peas):
    # The allOf pin: a thermalManagement document must carry TMAS requirements (family required).
    doc = {"inputs": {"designRequirements": {"name": "no family"}}, "thermalManagement": {}}
    assert not valid(peas, doc)


def _operating_conditions(registry):
    oc = registry.get_or_retrieve("https://psma.com/peas/inputs/operatingConditions.json").value.contents
    return Draft202012Validator(oc, registry=registry)


def test_cooling_names_its_part_by_uri(registry):
    v = _operating_conditions(registry)
    heatsink = {"ambientTemperature": 50, "cooling": {
        "thermalResistance": 24.4, "part": "TAS/data/thermal_management.ndjson?partNumber=577202B00000G",
        "interfaceThermalResistance": 2.9,
        "interfacePart": "TAS/data/thermal_management.ndjson?partNumber=SP900S-0.009-00-43"}}
    fan = {"ambientTemperature": 25, "cooling": {
        "velocity": [1.0, 0.0], "part": "TAS/data/thermal_management.ndjson?partNumber=CFM-4010-13-22"}}
    assert valid(v, heatsink)
    assert valid(v, fan)


@pytest.mark.parametrize("uri", ["577202B00000G", "TAS/data/thermal_management.ndjson?partNumber=A&x=B",
                                 "TAS/data/thermal_management.ndjson"])
def test_cooling_part_must_be_a_catalogue_uri(registry, uri):
    v = _operating_conditions(registry)
    assert not valid(v, {"ambientTemperature": 50, "cooling": {"thermalResistance": 24.4, "part": uri}})


def test_cooling_thermal_number_stays_required(registry):
    # The URI is traceability; the number the thermal model uses cannot be dropped for it.
    v = _operating_conditions(registry)
    assert not valid(v, {"ambientTemperature": 50, "cooling": {
        "part": "TAS/data/thermal_management.ndjson?partNumber=577202B00000G"}})


def test_transmission_line_validates(peas):
    doc = {
        "inputs": {"designRequirements": {}},
        "transmissionLine": {
            "kind": "lossy", "length": 0.1,
            "perUnitLength": {"resistance": 0.1, "inductance": 1e-7, "conductance": 1e-9, "capacitance": 1e-10},
        },
    }
    assert valid(peas, doc)


def test_coupled_inductors_missing_matrix_rejected(peas):
    # The branch requires inductanceMatrix; nature alone must not validate.
    doc = {"inputs": {"designRequirements": {"name": "x"}},
           "behavioral": {"nature": "coupledInductors"}}
    assert not valid(peas, doc)


def test_coupled_inductors_negative_series_resistance_rejected(peas):
    doc = {"inputs": {"designRequirements": {"name": "x"}},
           "behavioral": {"nature": "coupledInductors",
                          "inductanceMatrix": [[1e-7]],
                          "seriesResistance": [-1.0]}}
    assert not valid(peas, doc)


def test_coupled_inductors_extra_key_rejected(peas):
    # Closed object: no stray keys on the branch.
    doc = {"inputs": {"designRequirements": {"name": "x"}},
           "behavioral": {"nature": "coupledInductors",
                          "inductanceMatrix": [[1e-7]],
                          "couplingFactor": 0.9}}
    assert not valid(peas, doc)


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


# ---------------------------------------------------------------------------
# Guard: pinout / land-pattern types are defined ONCE, in PEAS (2026-08 hoist).
# History: before the hoist, FIVE divergent module-local representations existed
# (AAS pinout w/ 25-value enum, CTAS pins w/ free-string function, CONAS
# pcbFootprint w/ plating conflated into the shape enum, CONAS signalRole,
# MAS bobbin pinout) and two of them were the same type defined twice with
# ZERO shared vocabulary values. No module may reimplement these again: extend
# via allOf over the PEAS base (AAS outputStage is the worked example) and add
# missing vocabulary values to PEAS pinFunction, never locally.
# ---------------------------------------------------------------------------

# MAS is allowlisted: committee-governed (own RFC process), and its bobbin
# `pinout` is a bobbin MANUFACTURING spec (pitch arrays, row geometry), not a
# per-terminal function map. Migrating the finished-magnetic side is proposed
# through the MAS RFC process, not imposed here.
_PINOUT_GUARD_REPOS = [r for r in SIBLINGS if r not in ("PEAS", "MAS")]

_DESIGNATOR_KEYS = {"pin", "number", "designator"}


def _walk_schema_nodes(node, path=""):
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            yield from _walk_schema_nodes(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_schema_nodes(v, f"{path}/{i}")


def test_no_module_local_pinout_or_landpattern():
    """A module schema must not re-declare the pin-map shape (a properties set
    carrying a designator key AND 'function') or the pad-array shape (a 'pads'
    array whose items declare x/y). Both live in PEAS utils; modules $ref them."""
    offenders = []
    for repo in _PINOUT_GUARD_REPOS:
        sdir = WORKSPACE / repo / "schemas"
        if not sdir.is_dir():
            continue
        for path in sorted(sdir.rglob("*.json")):
            doc = json.loads(path.read_text())
            for where, node in _walk_schema_nodes(doc):
                props = node.get("properties")
                if not isinstance(props, dict):
                    continue
                # pin-map shape: designator + function declared side by side
                if "function" in props and _DESIGNATOR_KEYS & set(props):
                    offenders.append(f"{repo}:{path.name}{where} re-declares a pin map "
                                     f"(has {sorted(_DESIGNATOR_KEYS & set(props))} + function); "
                                     "use https://psma.com/peas/utils.json#/$defs/pin[out]")
                # pad-array shape: pads[] items declaring coordinates
                pads = props.get("pads")
                if isinstance(pads, dict):
                    items = pads.get("items")
                    if isinstance(items, dict):
                        ip = items.get("properties")
                        if isinstance(ip, dict) and {"x", "y"} <= set(ip):
                            offenders.append(f"{repo}:{path.name}{where} re-declares a pad array; "
                                             "use https://psma.com/peas/utils.json#/$defs/landPattern")
    assert not offenders, "module-local pinout/landPattern definitions found:\n  " + "\n  ".join(offenders)


def test_no_module_local_pin_function_vocabulary():
    """A module schema must not carry its own pin-function vocabulary (an enum
    containing the telltale role values). The single vocabulary is PEAS
    pinFunction; missing values are ADDED there (enums are complete unions),
    never forked locally. Catches the CTAS controllerPinFunction class."""
    telltale = {"ground", "gnd", "noConnect", "supplyPositive", "vcc", "gateHighSide"}
    offenders = []
    for repo in _PINOUT_GUARD_REPOS:
        sdir = WORKSPACE / repo / "schemas"
        if not sdir.is_dir():
            continue
        for path in sorted(sdir.rglob("*.json")):
            doc = json.loads(path.read_text())
            for where, node in _walk_schema_nodes(doc):
                enum = node.get("enum")
                if isinstance(enum, list) and len(telltale & set(map(str, enum))) >= 2:
                    offenders.append(f"{repo}:{path.name}{where} carries a local pin-function "
                                     "vocabulary; extend PEAS utils.json#/$defs/pinFunction instead")
    assert not offenders, "module-local pin-function vocabularies found:\n  " + "\n  ".join(offenders)


# --- surgeWaveform (PEAS-RFC 0003) ----------------------------------------------

SURGE_WAVEFORMS = ["8/20", "10/1000", "10/350", "2/10", "5/320", "10/700",
                   "10/560", "9/720", "10/160", "TLP 100 ns",
                   # 2026-10 telecom current waves, as thyristor-protector datasheets print them
                   "5/310", "5/200", "0.2/310", "10/360"]


@pytest.fixture(scope="session")
def surge(registry):
    return Draft202012Validator({"$ref": "https://psma.com/peas/utils.json#/$defs/surgeWaveform"},
                                registry=registry)


def test_surge_waveform_members_exact():
    d = json.loads((REPO / "schemas/utils.json").read_text())["$defs"]["surgeWaveform"]
    assert d["enum"] == SURGE_WAVEFORMS


@pytest.mark.parametrize("w", SURGE_WAVEFORMS)
def test_surge_waveform_member_accepted(surge, w):
    assert valid(surge, w)


@pytest.mark.parametrize("w", ["8x20", "8/20us", "8/20 µs", "10/1000us", "ISO 7637-2 pulse 1",
                               "IEC 61000-4-2", "TLP", "", 8.20])
def test_surge_waveform_unknown_rejected(surge, w):
    assert not valid(surge, w)


def test_surge_waveform_description_has_no_automotive_claim():
    d = json.loads((REPO / "schemas/utils.json").read_text())["$defs"]["surgeWaveform"]
    assert "automotive" not in d["description"].lower()


def test_surge_waveform_10_700_is_also_a_current_label():
    """Amendment 2026-10-18 (D5): GDT/TSPD datasheets print '200 A, 10/700 us'. The description
    must say that '10/700' on a CURRENT rating is the current of the 10/700 generator, and must not
    restrict the label to the open-circuit voltage wave alone."""
    d = json.loads((REPO / "schemas/utils.json").read_text())["$defs"]["surgeWaveform"]["description"]
    assert "'10/700' VOLTAGE wave (open circuit)" not in d
    assert "on a CURRENT rating it is the current that generator drives" in d
    assert "never converted into each other" in d


# --- resistive-element pin roles (2026-10, AAS digitalPotentiometer) -------------


@pytest.fixture(scope="session")
def pinout(registry):
    return Draft202012Validator({"$ref": "https://psma.com/peas/utils.json#/$defs/pinout"},
                                registry=registry)


def test_resistive_element_pin_roles_accepted(pinout):
    """A potentiometer pinout can say which pin is the wiper and which are the ends."""
    doc = [{"pin": "8", "name": "A", "function": "terminalA"},
           {"pin": "7", "name": "B", "function": "terminalB"},
           {"pin": "1", "name": "W", "function": "wiper"}]
    assert valid(pinout, doc)


@pytest.mark.parametrize("bad", ["terminalC", "end", "Wiper", "W"])
def test_resistive_element_pin_role_unknown_rejected(pinout, bad):
    assert not valid(pinout, [{"pin": "1", "function": bad}])


def test_triac_main_terminal_pin_roles_accepted(pinout):
    """A triac pinout names its main terminals MT1/MT2 (WeEn BTA16: T1, T2, G)."""
    doc = [{"pin": "1", "name": "T1", "function": "mainTerminal1"},
           {"pin": "2", "name": "T2", "function": "mainTerminal2"},
           {"pin": "3", "name": "G", "function": "gate"}]
    assert valid(pinout, doc)


@pytest.mark.parametrize("bad", ["MT1", "mainTerminal", "mainTerminal3", "T2"])
def test_triac_main_terminal_unknown_rejected(pinout, bad):
    assert not valid(pinout, [{"pin": "1", "function": bad}])


# --- isolationRating (hoisted from CTAS 2026-10) ------------------------------


@pytest.fixture(scope="session")
def isolation(registry):
    return Draft202012Validator({"$ref": "https://psma.com/peas/utils.json#/$defs/isolationRating"},
                                registry=registry)


CTAS_ISOLATION_KEYS = {"isolationType", "withstandVoltageRms", "workingVoltage", "surgeVoltage",
                       "cmti", "barrierCapacitance", "creepage", "clearance"}


def test_isolation_rating_keeps_ctas_key_names():
    """The hoist kept every CTAS key name, so the controller rows and Blade Runner need no change."""
    props = set(json.loads((REPO / "schemas/utils.json").read_text())["$defs"]["isolationRating"]["properties"])
    assert CTAS_ISOLATION_KEYS <= props


def test_isolation_rating_full_block_accepted(isolation):
    doc = {"isolationType": "reinforced", "withstandVoltageRms": 5000, "withstandVoltageDuration": 60,
           "workingVoltage": 2121, "workingVoltageRms": 1500, "transientVoltage": 8000, "impulseVoltage": 7692,
           "surgeVoltage": 10000, "cmti": 100e9, "barrierCapacitance": 1e-12, "barrierResistance": 1e12,
           "creepage": 0.008, "clearance": 0.008, "distanceThroughInsulation": 21e-6,
           "comparativeTrackingIndex": 600, "materialGroup": "I", "pollutionDegree": "PD2",
           "ratedInsulationVoltage": [{"voltage": 150, "insulationClass": "reinforced", "overvoltageCategory": "III",
                                       "pollutionDegree": "PD2", "standard": "EN 50178"}]}
    assert valid(isolation, doc)


def test_isolation_rating_supplementary_accepted(isolation):
    assert valid(isolation, {"isolationType": "supplementary"})


def test_isolation_rating_none_rejected(isolation):
    """A non-isolated part omits the block; the old CTAS value 'none' is gone."""
    assert not valid(isolation, {"isolationType": "none"})


def test_isolation_rating_unknown_key_rejected(isolation):
    assert not valid(isolation, {"isolationType": "basic", "workingVoltageDc": 600})


def test_isolation_rating_rated_voltage_needs_voltage(isolation):
    assert not valid(isolation, {"ratedInsulationVoltage": [{"overvoltageCategory": "III"}]})


def test_isolation_rating_material_group_closed(isolation):
    assert not valid(isolation, {"materialGroup": "III"})
