<h1 align="center">PEAS - Power Electronics Agnostic Structure</h1>

<p align="center">
  <em>The abstract base for all electronic component schemas in the OpenConverters ecosystem</em>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://json-schema.org/"><img src="https://img.shields.io/badge/JSON%20Schema-2020--12-blue.svg" alt="JSON Schema"></a>
</p>

---

## What is PEAS?

**PEAS is the abstract base type (virtual class) for all electronic components** in the OpenConverters ecosystem. It defines the universal contract that every component -- whether a magnetic, semiconductor, capacitor, or resistor -- must satisfy: an `inputs` section, an `outputs` section, and exactly one component-type-specific payload.

PEAS itself is never instantiated directly. Instead, it acts as a polymorphic container: any valid MAS, SAS, CAS, or RAS document is automatically a valid PEAS document. This allows higher-level schemas like TAS (Topology Agnostic Structure) to reference "any component" without knowing its specific type.

### The Role of PEAS

```mermaid
classDiagram
    class PEAS {
        <<abstract>>
        +inputs
        +outputs
        +oneOf component
    }
    class MAS {
        +magnetic
        inductor, transformer, choke
    }
    class SAS {
        +semiconductor
        MOSFET, diode, IGBT, BJT
    }
    class CAS {
        +capacitor
        ceramic, electrolytic, film
    }
    class RAS {
        +resistor
        thickFilm, shunt, foil
    }
    class TAS {
        +components
        complete converter design
    }
    PEAS <|-- MAS : magnetic components
    PEAS <|-- SAS : semiconductors
    PEAS <|-- CAS : capacitors
    PEAS <|-- RAS : resistors
    MAS --o TAS : assembled into
    SAS --o TAS : assembled into
    CAS --o TAS : assembled into
    RAS --o TAS : assembled into
```

### Why PEAS Exists

Without PEAS, the TAS schema would need separate fields for each component type (`magnetic`, `semiconductor`, `capacitor`, `resistor`) and would break every time a new component type is added. Instead, TAS references PEAS documents, and the `oneOf` discriminator in PEAS determines the actual type at validation time.

This is the same pattern as a virtual base class in object-oriented programming: PEAS defines the interface, and MAS/SAS/CAS/RAS provide the concrete implementations.

---

## The oneOf Discriminator

PEAS uses JSON Schema's `oneOf` keyword to enforce that exactly one component type is present. The discriminator is the presence of a type-specific property key:

| Property Key | Schema | Component Type |
|-------------|--------|----------------|
| `magnetic` | MAS (`https://psma.com/mas/magnetic.json`) | Inductors, transformers, chokes |
| `capacitor` | CAS (`https://psma.com/cas/capacitor.json`) | Ceramic, electrolytic, film capacitors |
| `semiconductor` | SAS (`https://psma.com/sas/SAS.json`) | MOSFETs, diodes, IGBTs, BJTs |
| `resistor` | RAS (`https://psma.com/ras/resistor.json`) | Thin/thick film, shunt, wirewound resistors |
| `varistor` | RAS (`https://psma.com/ras/varistor.json`) | MOV / multilayer voltage-dependent protection elements |
| `controller` | CTAS (`https://psma.com/ctas/controller.json`) | PWM / LLC / PFC / sync-rectifier / gate-driver / reference control ICs |
| `connector` | CONAS (`https://psma.com/conas/connector.json`) | Terminals, headers, edge-card, wire-to-board, power |
| `analog` | AAS (`https://psma.com/aas/AAS.json`) | Op amps, comparators, ADC/DAC, analog switches |
| `behavioral` | PEAS-native (`#/$defs/behavioral`) | Analytic Ψ(i)/Q(v) or Chan saturable-core models |
| `transmissionLine` | PEAS-native (`#/$defs/transmissionLine`) | Distributed RLGC lines |

Cross-repo `$ref`s use the **absolute** `https://psma.com/<repo>/...` `$id` URIs (resolved via a `referencing.Registry`), never relative paths.

A valid PEAS document must contain `inputs` (with `inputs.designRequirements`) and **exactly one** of the component keys above. `outputs` is optional. The root object is closed (`additionalProperties: false`): unknown top-level keys are rejected.

### Example: A Resistor as an PEAS Document

```json
{
    "inputs": {
        "designRequirements": {
            "deviceType": "resistor",
            "resistance": {"nominal": 0.01},
            "powerRating": 1.0
        }
    },
    "resistor": {
        "manufacturerInfo": {
            "name": "Vishay",
            "reference": "WSK2512R0100FEA",
            "datasheetInfo": {
                "part": {
                    "partNumber": "WSK2512R0100FEA",
                    "technology": "currentSenseShunt",
                    "case": "2512"
                },
                "electrical": {
                    "resistance": {"nominal": 0.01},
                    "tolerance": 0.01,
                    "powerRating": 1.0
                }
            }
        }
    }
}
```

This document is simultaneously a valid RAS document and a valid PEAS document. `inputs.designRequirements` is required (its shape — including the `deviceType` discriminator — is pinned to the `resistor` branch by RAS); `outputs` is optional and omitted here. The authoritative field shapes live in `RAS/schemas/`; see `RAS/examples/` for complete documents.

---

## How TAS References PEAS Documents

TAS (Topology Agnostic Structure) describes complete power converter designs as a tree of stages, each owning a circuit whose `components[]` entries carry a `data` field that is a PEAS document -- either inline or a URI reference into a catalog:

### Inline (full PEAS document embedded)

```json
{
    "name": "R1",
    "role": "currentSenseResistor",
    "data": {
        "inputs": {},
        "resistor": { "..." },
        "outputs": []
    }
}
```

### By Reference (path or URI to an external file)

```json
{
    "name": "R1",
    "role": "currentSenseResistor",
    "data": "components/R1_shunt.json"
}
```

This follows the same pattern used in MAS for core shapes and materials: data can be specified directly or by reference to a standard definition.

### Component Roles in TAS

TAS defines typed roles for each component category:

| Category | Roles |
|----------|-------|
| Magnetics | `mainInductor`, `resonantInductor`, `pfcInductor`, `filterInductor`, `mainTransformer`, `gateTransformer`, `currentTransformer` |
| Semiconductors | `highSideSwitch`, `lowSideSwitch`, `primarySwitch`, `secondarySwitch`, `clampSwitch`, `synchronousRectifier`, `pfcSwitch`, `outputRectifier`, `freewheelDiode`, `clampDiode`, `boostDiode` |
| Capacitors | `inputCapacitor`, `outputCapacitor`, `bulkCapacitor`, `resonantCapacitor`, `bootstrapCapacitor`, `decouplingCapacitor`, `snubberCapacitor`, `clampCapacitor` |
| Resistors | `currentSenseResistor`, `gateResistor`, `feedbackResistor`, `bleederResistor`, `snubberResistor`, `clampResistor` |

---

## Relationship to OpenMagnetics/MAS

MAS (Magnetic Agnostic Structure) was the first component schema, developed under the [OpenMagnetics](https://github.com/OpenMagnetics) organization. It defines the data format for inductors, transformers, and chokes, and is backed by computation libraries (PyOpenMagnetics, MKF).

PEAS was created to generalize the MAS pattern to all electronic component types. Key design decisions inherited from MAS:

- **Three-section structure**: `inputs` + component + `outputs`
- **Reference support**: component data can be inline or referenced by path/URI
- **SI units throughout**: Ohms, Watts, Volts, meters, Celsius
- **JSON Schema 2020-12**: machine-validatable, self-documenting

MAS lives in its own repository (`OpenMagnetics/MAS`) and is referenced by PEAS via the URI `https://psma.com/mas/magnetic.json`. The other component schemas (SAS, CAS, RAS) live under `OpenConverters/`.

---

## The OpenConverters Ecosystem

```
OpenMagnetics/
  +-- MAS/                    # Magnetic Agnostic Structure
  +-- PyOpenMagnetics/        # Python computation library for magnetics

OpenConverters/
  +-- PEAS/                    # Power Electronics Agnostic Structure (this repo -- abstract base)
  +-- SAS/                    # Semiconductor Agnostic Structure
  +-- CAS/                    # Capacitor Agnostic Structure
  +-- RAS/                    # Resistor Agnostic Structure
  +-- TAS/                    # Topology Agnostic Structure (complete converters)
  +-- Proteus/                # AI-powered converter design system (uses all of the above)
```

| Schema | Purpose | Example Components |
|--------|---------|-------------------|
| **MAS** | Magnetic components | ETD34 flyback transformer, PQ26 boost inductor, common-mode choke |
| **SAS** | Semiconductors | GaN FET, SiC MOSFET, Schottky diode, IGBT |
| **CAS** | Capacitors | MLCC, aluminum electrolytic, film capacitor |
| **RAS** | Resistors | Thick film chip, current sense shunt, precision foil |
| **PEAS** | Abstract base | Any of the above, used by TAS for polymorphic references |
| **TAS** | Complete converters | 65W USB-C charger, 300W LLC converter, 1kW PFC + LLC |

### Data Flow

```mermaid
flowchart LR
    subgraph "Manufacturing Building Blocks"
        MAS_D["MAS/data/<br/>cores, wire, bobbins"]
        SAS_D["SAS/data/<br/>dies, packages"]
        CAS_D["CAS/data/<br/>foils, dielectrics"]
        RAS_D["RAS/data/<br/>films, substrates"]
    end

    subgraph "Finished Components"
        TAS_D["TAS/data/<br/>mosfets.ndjson<br/>diodes.ndjson<br/>capacitors.ndjson<br/>resistors.ndjson<br/>magnetics.ndjson"]
    end

    subgraph "Converter Designs"
        CONV["TAS/data/<br/>converters.ndjson"]
    end

    MAS_D --> TAS_D
    SAS_D --> TAS_D
    CAS_D --> TAS_D
    RAS_D --> TAS_D
    TAS_D --> CONV
```

1. Component data (MAS, SAS, CAS, RAS documents) is created from datasheets
2. A converter design tool (e.g., Proteus) selects components for a given specification
3. The selected components are assembled into a TAS document, referencing PEAS-typed data
4. Computation libraries (PyOpenMagnetics, etc.) process the TAS to calculate losses, thermal performance, and efficiency

---

## Schema Definition

`schemas/peas.json` is the authoritative source (this README does not inline it — a hand-copy drifts). Its structure:

- **`type: object`, `additionalProperties: false`** — the root is closed; unknown top-level keys are rejected.
- **`required: ["inputs"]`** — only `inputs` is mandatory; `outputs` is optional.
- **`properties`** — `inputs`, `outputs`, and the ten discriminator keys (declared permissively; the `oneOf` is their real validator).
- **`oneOf`** — the ten mutually-exclusive component branches (see the table above), each `$ref`-ing its family schema by absolute URI.
- **`allOf`** — one `if`/`then` clause per branch, pinning `inputs.designRequirements` to the matching family's designRequirements schema (the PEAS-native `behavioral`/`transmissionLine` branches pin to `#/$defs/behavioralDesignRequirements`).

---

## File Organization

```
PEAS/
├── schemas/
│   ├── peas.json          # The PEAS root (closed object + oneOf discriminator + DR pins)
│   ├── utils.json         # Shared primitives (dimensionWithTolerance, curve, cooling,
│   │                      #   manufacturerInfo, distributorInfo, datasheetInfo* mixins, ...)
│   ├── inputs/            # operatingPoint / operatingConditions / excitation templates
│   └── outputs/           # outputBase + shared result blocks
├── src/                   # header-only C++ helpers (resolve_dimensional_values, Fidelity)
└── tests/test_schemas.py  # meta-validation, $ref resolution, per-discriminator fixtures
```

The concrete component schemas live in their sibling repositories (MAS, CAS, SAS, RAS, CTAS, CONAS, AAS); `utils.json` holds the primitives they share. TAS references PEAS documents for the components inside a converter design.

---

## License

This project is licensed under the MIT License.

---

<p align="center">
  Part of the <a href="https://github.com/OpenConverters">OpenConverters</a> ecosystem
</p>
