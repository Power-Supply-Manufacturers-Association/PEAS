# OpenConverters Ecosystem Architecture

This document describes the full architecture of the OpenConverters component schema ecosystem, how the schemas relate to each other, and how data flows from individual component definitions to complete converter designs.

---

## Overview

The OpenConverters ecosystem defines a family of JSON schemas for describing electronic components and power converter designs. The architecture follows an object-oriented pattern:

- **PEAS** is the abstract base class
- **MAS, SAS, CAS, RAS** are the concrete implementations (one per component family)
- **TAS** is the composite that assembles components into complete designs

```mermaid
classDiagram
    class PEAS {
        <<abstract>>
        +inputs
        +outputs
        +oneOf discriminator
    }
    class MAS {
        +magnetic
        cores, coils, wire
    }
    class SAS {
        +semiconductor
        MOSFETs, diodes, IGBTs
    }
    class CAS {
        +capacitor
        MLCC, electrolytic, film
    }
    class RAS {
        +resistor
        thick film, shunt, foil
    }
    class TAS {
        +inputs
        +components
        +outputs
        whole converter
    }
    PEAS <|-- MAS
    PEAS <|-- SAS
    PEAS <|-- CAS
    PEAS <|-- RAS
    MAS --o TAS
    SAS --o TAS
    CAS --o TAS
    RAS --o TAS
```

```mermaid
flowchart TB
    subgraph OpenMagnetics
        MAS_REPO["MAS<br/>Magnetic Agnostic Structure"]
        PyOM["PyOpenMagnetics<br/>Python computation library"]
    end

    subgraph OpenConverters
        PEAS_REPO["PEAS<br/>Power Electronics Agnostic Structure<br/>(abstract base)"]
        SAS_REPO["SAS<br/>Semiconductor"]
        CAS_REPO["CAS<br/>Capacitor"]
        RAS_REPO["RAS<br/>Resistor"]
        TAS_REPO["TAS<br/>Topology<br/>(complete converters)"]
        Proteus["Proteus<br/>AI-powered design system"]
    end

    MAS_REPO -->|"referenced by"| PEAS_REPO
    SAS_REPO -->|"local ref"| PEAS_REPO
    CAS_REPO -->|"local ref"| PEAS_REPO
    RAS_REPO -->|"local ref"| PEAS_REPO
    PEAS_REPO -->|"referenced by"| TAS_REPO
    TAS_REPO -->|"used by"| Proteus
    PyOM -->|"used by"| Proteus
    MAS_REPO -->|"backed by"| PyOM
```

```mermaid
sequenceDiagram
    participant CL as component-librarian
    participant DS as Datasheets (Web)
    participant TAS as TAS/data/
    participant CD as converter-designer

    CL->>DS: Search for component datasheets
    DS-->>CL: Datasheet PDF / product page
    CL->>CL: Extract parameters per PEAS/SAS/CAS/RAS schema
    CL->>TAS: Write NDJSON entry (mosfets, diodes, caps, etc.)
    CD->>TAS: Query for components matching requirements
    TAS-->>CD: Matching components with full specs
    CD->>CD: Select best components, build converter design
```

---

## Schema Descriptions

### PEAS -- Power Electronics Agnostic Structure

**Repository**: `Power-Supply-Manufacturers-Association/PEAS/`
**Schema**: `schemas/peas.json`
**Role**: Abstract base type for all electronic components

PEAS defines the universal contract:
- Every component has `inputs` (with `inputs.designRequirements` required; operating points optional)
- `outputs` (computed results) is optional
- The root object is closed (`additionalProperties: false`) — unknown top-level keys are rejected
- Exactly one component-type key must be present: `magnetic` (MAS), `capacitor` (CAS), `semiconductor` (SAS), `resistor` / `varistor` (RAS), `controller` (CTAS), `connector` (CONAS), `analog` (AAS), or the PEAS-native `behavioral` / `transmissionLine` primitives

The `oneOf` discriminator pattern allows polymorphic references: any code or schema that accepts an PEAS document can handle any component type without knowing which one it is in advance.

**Schema ID**: `https://psma.com/peas/peas.json`

---

### MAS -- Magnetic Agnostic Structure

**Repository**: `OpenMagnetics/MAS/`
**Schema**: `schemas/MAS.json`
**Role**: Inductors, transformers, and chokes

MAS is the most mature schema in the ecosystem. It describes:
- **Core**: shape (ETD, PQ, RM, E, toroid, planar), material (N87, 3C95, High Flux, MPP), gapping, stacking
- **Coil**: turns, parallels, wire type (round, litz, foil), insulation layers, bobbin
- **Operating conditions**: frequency, voltage/current waveforms, temperature

MAS includes extensive databases of standard components (500+ core shapes, 50+ ferrite materials, 50+ powder materials, 200+ wire types) and is backed by computation libraries:
- **PyOpenMagnetics** (Python) -- core loss (iGSE), winding loss (Dowell), thermal modeling
- **MKF** (C++) -- high-performance simulation engine

The three-section pattern (`inputs` + `magnetic` + `outputs`) that MAS established became the template for all other component schemas.

**Schema ID**: `https://psma.com/mas/MAS.json`
**Component key in PEAS**: `magnetic`

---

### SAS -- Semiconductor Agnostic Structure

**Repository**: `OpenConverters/SAS/`
**Schema**: `schemas/SAS.json`
**Role**: MOSFETs, diodes, IGBTs, BJTs

SAS describes semiconductor devices used in power converters:
- Device identification (part number, technology, package)
- Electrical parameters (voltage ratings, current ratings, on-resistance, threshold voltage)
- Switching characteristics (rise/fall times, gate charge, reverse recovery)
- Thermal parameters (junction-to-case, junction-to-ambient thermal resistance)
- SPICE model parameters

**Schema ID**: `https://psma.com/sas/SAS.json`
**Component key in PEAS**: `semiconductor`

---

### CAS -- Capacitor Agnostic Structure

**Repository**: `OpenConverters/CAS/`
**Schema**: `schemas/CAS.json`
**Role**: Ceramic, electrolytic, and film capacitors

CAS describes capacitor components:
- Capacitor technology (MLCC, aluminum electrolytic, polymer, film)
- Electrical parameters (capacitance, voltage rating, ESR, ESL, dissipation factor)
- Bias derating (DC bias effect on MLCC capacitance)
- Temperature characteristics (X5R, X7R, C0G, etc.)
- Ripple current ratings and lifetime models

**Schema ID**: `https://psma.com/cas/CAS.json`
**Component key in PEAS**: `capacitor`

---

### RAS -- Resistor Agnostic Structure

**Repository**: `OpenConverters/RAS/`
**Schema**: `schemas/RAS.json`
**Role**: Thin film, thick film, wirewound, shunt, foil, and other resistors

RAS describes resistor components:
- Technology type (thinFilm, thickFilm, wirewound, carbonComposition, metalOxide, foil, shunt)
- Electrical parameters (resistance, tolerance, TCR, power rating, max voltage)
- SPICE model parameters (r, tcr1, tcr2)
- Power derating curves (temperature vs. allowable power fraction)
- Mechanical dimensions and assembly type

**Schema ID**: `https://psma.com/ras/RAS.json`
**Component key in PEAS**: `resistor`

---

### CTAS -- Controller Agnostic Structure

**Repository**: `OpenConverters/CTAS/`
**Schema**: `schemas/CTAS.json`
**Role**: Control ICs -- PWM / multiphase / LLC / PFC / phase-shift / sync-rectifier controllers, isolated & non-isolated gate drivers, digital/PMBus controllers, shunt regulators, voltage references, current-sense & isolated amplifiers, hot-swap / eFuse controllers

CTAS describes the control-IC half of a converter, with one agnostic schema discriminated internally on `function.category`:
- Functional class, intended topologies, modulation / conduction mode, channel & phase count
- Common electricals (supply, switching-frequency band, duty, reference, soft-start) plus category-gated capability sub-objects (`gateDrive`, `isolation`, `currentMode`, `shuntReference`, `hotSwap`, `senseAmplifier`, `syncRectifier`, `pfc`, `loadLine`, ...)
- On-die protections, slim pin map, digital interface + telemetry, thermal / mechanical / compliance

CTAS was extracted from the former inline `PEAS/schemas/controller.json` branch; PEAS now references it by `$id`. CTAS owns the controller-family vocabularies and reuses the PEAS shared primitives.

**Schema ID**: `https://psma.com/ctas/CTAS.json`
**Component key in PEAS**: `controller`

---

### TAS -- Topology Agnostic Structure

**Repository**: `OpenConverters/TAS/`
**Schema**: `schemas/TAS.json`
**Role**: Complete power converter designs

TAS is the top-level schema that assembles individual components into a complete converter design:

- **inputs**: Converter-level requirements (input voltage range, output voltage/current, efficiency targets, topology selection, switching frequency)
- **components**: A list of PEAS-typed components with circuit roles and a netlist defining how they connect
- **outputs**: Converter-level results (efficiency, loss breakdown, waveforms, thermal map)

Each component in the `componentList` has:
- `name`: Reference designator (e.g., "T1", "Q1", "C1", "R1")
- `role`: Circuit function (e.g., `mainTransformer`, `highSideSwitch`, `outputCapacitor`, `currentSenseResistor`)
- `data`: Either a full PEAS document inline, or a string path/URI to an external PEAS file

The `netlist` section defines circuit topology by listing nodes and connecting component pins to those nodes.

**Schema ID**: `https://psma.com/tas/TAS.json`

---

## The Inputs-Component-Outputs Pattern

Every schema in the ecosystem follows the same three-section pattern established by MAS:

```
+-----------+     +-------------+     +-----------+
|  inputs   |  +  |  component  |  =  |  outputs  |
+-----------+     +-------------+     +-----------+
| Operating |     | Physical    |     | Computed  |
| conditions|     | description |     | results   |
+-----------+     +-------------+     +-----------+
```

| Schema | Input Examples | Component Key | Output Examples |
|--------|---------------|---------------|-----------------|
| MAS | Inductance, frequency, waveforms | `magnetic` | Core loss, winding loss, flux density |
| SAS | Voltage, current, switching freq. | `semiconductor` | Conduction loss, switching loss, Tj |
| CAS | Ripple current, DC bias, frequency | `capacitor` | ESR loss, lifetime, effective capacitance |
| RAS | Voltage, current, temperature | `resistor` | Power dissipation, temperature rise |
| TAS | Vin, Vout, Iout, topology | `components` | Efficiency, total losses, waveforms |

This separation enables reuse: the same physical component (e.g., an ETD34 transformer) can be evaluated under different operating conditions by changing only the `inputs` section.

---

## Data Organization

Each component schema repository follows a consistent directory structure:

```
<Schema>/
+-- schemas/          # JSON Schema definitions
+-- data/             # Manufacturing building blocks (series, families, templates)
+-- examples/         # Example documents
+-- docs/             # Documentation
```

### Important: data/ vs. TAS/data/

Component-level `data/` directories contain **manufacturing building blocks** -- parametric families, series definitions, and templates that describe what manufacturers offer. These are the raw materials for component selection.

`TAS/data/` contains **finished converter designs** -- complete assemblies with specific components selected for specific applications. This is where selected, configured components end up as part of a working design.

---

## Reference Pattern (Inline vs. Path)

Throughout the ecosystem, data can be provided in two ways:

### Inline (embedded directly)

```json
{
    "name": "T1",
    "role": "mainTransformer",
    "data": {
        "inputs": { "..." },
        "magnetic": { "..." },
        "outputs": []
    }
}
```

### By Reference (path or URI)

```json
{
    "name": "T1",
    "role": "mainTransformer",
    "data": "components/T1_flyback_transformer.json"
}
```

This pattern originates from MAS, where core shapes and materials can be specified by standard name (e.g., `"ETD 34"`, `"N97"`) or by providing full dimensional/property data inline. TAS extends this pattern to entire component documents.

---

## Cross-Repository Dependencies

```mermaid
flowchart TD
    MAS["OpenMagnetics/MAS"]
    PEAS["Power-Supply-Manufacturers-Association/PEAS"]
    SAS["SAS (local ref)"]
    CAS["CAS (local ref)"]
    RAS["RAS (local ref)"]
    TAS["TAS (references PEAS)"]
    Proteus["Proteus (uses TAS + all schemas)"]

    MAS -->|"external URI"| PEAS
    SAS -->|"./semiconductor.json"| PEAS
    CAS -->|"./capacitor.json"| PEAS
    RAS -->|"./resistor.json"| PEAS
    PEAS -->|"URI ref"| TAS
    TAS --> Proteus
```

- PEAS references MAS via its external URI (`https://psma.com/mas/magnetic.json`)
- PEAS references SAS, CAS, and RAS via local relative paths (`./semiconductor.json`, `./capacitor.json`, `./resistor.json`)
- TAS references PEAS via its URI (`https://psma.com/peas/peas.json`)
- Proteus (the AI design system) orchestrates the entire ecosystem, using all schemas and computation libraries to produce complete converter designs

---

## Adding a New Component Type

To add a new component type (e.g., a connector or sensor schema):

1. Create a new repository under OpenConverters (e.g., `XAS/`)
2. Define the component schema following the `inputs` + `<type>` + `outputs` pattern
3. Add a new branch to the `oneOf` discriminator in `PEAS/schemas/peas.json`
4. Add corresponding roles in `TAS/schemas/components.json`

The PEAS abstraction means that TAS and all higher-level tools automatically support the new type once PEAS is updated.
## Provenance (data-source trail)

Every `datasheetInfo` carries an optional `provenance` array recording where its data
came from. Optional and closed, so records without it remain valid. Each entry:

| field | meaning |
|---|---|
| `source` | `manufacturerDatasheet` · `manufacturerParametric` · `manufacturerDatabase` · `distributor` · `librarianEnrichment` · `scrape` · `manual` |
| `sourceName` | human-readable source, e.g. `"TI parametric API"`, `"WE - Passive Components.mdb"`, `"DigiKey"` |
| `sourceUrl` | URL the value came from (optional) |
| `retrievedDate` | `YYYY-MM-DD` (optional) |
| `fields` | which `datasheetInfo` fields this source supplied — for mixed-source records (optional) |

It is a **list**: a record may combine sources (e.g. specs from the datasheet, a rated
voltage from a distributor, a missing field back-filled by librarian enrichment). The
canonical definition lives in `PEAS/schemas/utils.json#/$defs/provenance` (mirrored in
`MAS/schemas/utils.json`, which is self-contained).

## Pinout and land pattern (hoisted 2026-08)

`utils.json` carries the family-wide per-terminal and land-pattern types, consolidated
from five previously divergent module-local representations (AAS `pinout`, CTAS
`pins`/`controllerPinFunction`, CONAS `pcbFootprint`, CONAS `signalRole`; MAS
`bobbin.pinout` stays module-side — it is a bobbin manufacturing spec, and MAS adoption
for finished magnetics is proposed via MAS-RFC 0010):

| def | what |
|---|---|
| `pinFunction` | THE single 100-value role vocabulary (generic + differential + amplifier + supply + control + digital + power-semiconductor + magnetics + the merged CTAS power-controller group). Missing values are ADDED here — never forked locally. |
| `pin` | `(pin, name, function, polarity)` — an OPEN mixin base (like `datasheetInfoPartBase`); consumers seal with `unevaluatedProperties: false`, and may extend via `allOf` (AAS adds `outputStage`). |
| `pinout` | pre-sealed array of `pin`, for direct unextended use. |
| `landPatternPad` | one pad/hole: `id` (joins `pinout[].pin`), `x`/`y` (m), `rotation` (degrees — documented SI exception matching MAS coil), `shape` (pure geometry), `width`/`height`, `drill`/`slotLength`/`plated` (through-board character kept separate from shape). |
| `landPattern` | the datasheet's recommended pattern: `pattern` hint, `originDatum`, `recommendedBoardThickness`, `pads[]`. Distinct from CAS's scalar `footprint` (an area in m²), which deliberately keeps a different name. |

Two guard tests in `tests/test_schemas.py` enforce single-definition:
`test_no_module_local_pinout_or_landpattern` (fails on any module schema re-declaring a
designator+function properties set or a pads[]-with-x/y array) and
`test_no_module_local_pin_function_vocabulary` (fails on any module-local enum carrying
the telltale role values).
