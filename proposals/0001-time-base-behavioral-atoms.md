# PEAS-RFC 0001 — TBAS: Time-Based Agnostic Structure (new family repo)

- **Status:** IMPLEMENTED 2026-07-02 (rev 3). The repo exists at
  `github.com/Power-Supply-Manufacturers-Association/TBAS`; PEAS carries the
  `timeBase` branch + `time` variable; AAS sampleHold has its behavioral
  block; CTAS controlScheme grew as §5.3 (as a complete per-scheme oneOf,
  not a flat enum). Market-survey deltas vs rev 2: `ceramicResonator`
  technology added; `enableFunction`, `dutyCycle`, `spreadSpectrum`,
  `resonantImpedance`, `builtInCapacitance` fields added; `driveLevel` and
  `standbyCurrent` dropped (no buyer filters, no validator use); RTC /
  clock-generator / RF-VCO / SAW confirmed out of scope. The CIAS emitters (§7)
  and the ctas_to_cias lowerings for all six schemes (§6) landed the same
  day — ngspice-verified end-to-end (PWM duty tracks the error command; the
  duty clamp holds). Nothing from this RFC remains open.
- **Created:** 2026-07-02
- **Touches (each schema edit needs separate approval):** new repo
  `OpenConverters/TBAS` (schemas created from scratch), `PEAS/schemas/peas.json`
  (one new discriminator branch + expression-grammar text),
  `AAS/schemas/sampleHold.json` ($defs/behavioral), `CTAS/schemas/*`
  (controlScheme enum), `CIAS` C++ emitter (code, not schema)

## 1. Problem

The behavioral atom set (PEAS `behavioral` natures + the AAS ideal blocks
comparator/multiplier/summer/integrator) has **no time-base primitive**: no
sawtooth/clock oscillator, no VCO, no one-shot timer, no SR latch, and
behavioral expressions have no `time` variable. Consequently voltage-mode
PWM, peak-current-mode, constant-on-time, resonant frequency modulation and
PFC multiplier loops cannot be netlisted at all — CTAS's `controlScheme` is
stuck at `["synchronousRectifier"]`. This was flagged in the 2026-07-01
workspace review as the single biggest "express any converter" gap.

There is a second, catalog-side gap hiding behind the first: **frequency
control products** — crystals, crystal/MEMS oscillators, TCXO/VCXO/OCXO,
programmable oscillators, 555-class timers, clock generators/buffers, RTCs —
are a major orderable-parts category (Abracon, SiTime, Epson, TXC, Microchip)
with **no home in the workspace**: not CAS, not SAS, not RAS, not AAS, not
CTAS. Every converter BOM with a clocked controller or an external sync
source hits this hole.

## 2. Why a repo (and not natures inside PEAS)

Rev 1 of this RFC proposed the atoms as new `peas.json` behavioral natures,
arguing a repo would invert the dependency direction. That argument was
wrong: `peas.json` already `$ref`-pins every discriminator branch into the
sibling family repos — PEAS depending on TBAS is exactly as legitimate as
PEAS depending on AAS. The correct test is *"is this a component family?"*,
and it is (§1, second paragraph). The repo shape buys:

- **Family symmetry.** `TBAS — Time-Based Agnostic Structure` slots into the
  established pattern (MAS/CAS/SAS/RAS/CTAS/CONAS/AAS), with the standard
  PEAS citizenship: `{timeBase: {…}}` discriminator, DR pin, seed branch.
- **One schema for the ideal atom and the orderable part.** AAS proved the
  pattern: the comparator's `behavioral` block "is present on an otherwise
  part-less document to describe an ideal control block", while the same
  family carries full datasheet fields when `manufacturerInfo` is present.
  TBAS oscillators work the same way: the anonymous PWM ramp in a CIAS
  control brick and a SiTime MEMS oscillator in TAS/data are the same type.
- **A home for the datasheet physics.** Frequency stability (ppm), aging,
  phase jitter, startup time, supply pushing — none of that has anywhere to
  live in a PEAS nature.
- **Catalog growth.** `TAS/data/time_based.ndjson` becomes sourceable from
  the usual vendor parametric APIs (frequency-control catalogs are
  well-structured), and Blade Runner can grow physics checks
  (f × stability sanity, jitter floors) once records exist.

What stays OUT of TBAS: the `time` expression variable (it is grammar of the
existing PEAS `behavioral` expressions, §5.3); the AAS `sampleHold`
behavioral block (sampling is analog signal path, and the family already
lives in AAS, §5.4).

## 3. Repo shape

Standard family layout, modeled on AAS (the healthiest repo in the 2026-07
review):

```
TBAS/
  schemas/tbas.json          — family oneOf: oscillator | timer | latch  (type-discriminated)
  schemas/oscillator.json    — parts + behavioral
  schemas/timer.json         — parts + behavioral
  schemas/latch.json         — parts + behavioral
  schemas/inputs/…           — designRequirements (requirement-side enums $ref the part-side anchors)
  schemas/outputs.json       — outputBase mixin, sealed with unevaluatedProperties:false
  docs/schema.md, examples/, tests/ (pytest + registry), scripts/validate.py
  LICENSE (MIT), README.md
```

`$id` namespace `https://psma.com/tbas/…`. Conventions as everywhere: draft
2020-12, closed objects, `const`-pinned discriminators, seed-friendly
(`{timeBase: {}}` and part-less behavioral-only documents both valid),
datasheet requireds only once `manufacturerInfo` is present, SI everywhere
(ppm noted as dimensionless 1e-6 in descriptions).

### 3.1 `oscillator` — free-running waveform source / VCO / orderable oscillator

Behavioral core (the TBAS atom CIAS consumes):

```jsonc
"behavioral": {
  "title": "oscillatorBehavioral",
  "description": "Simulator-agnostic IDEAL periodic source (PWM ramp, clock, resonant drive). Instantaneous frequency f = frequency when frequencyControl is absent, else f = frequency + gain*v(control+,control-) (a VCO; f clamps at 0 — negative instantaneous frequency is meaningless). Backend emission: fixed-frequency sawtooth/triangle/square -> native PULSE source, fixed sine -> SINE/SIN; any oscillator WITH frequencyControl -> canonical phase-accumulator subcircuit (G-source + 1F capacitor integrating f(t) into a phase node, shaping B-source with floor()-wrap or sin(2*pi*phase)).",
  "type": "object",
  "additionalProperties": false,
  "required": ["shape", "frequency", "amplitude", "offset"],
  "properties": {
    "shape":     { "enum": ["sawtooth", "triangle", "square", "sine"] },
    "frequency": { "type": "number", "exclusiveMinimum": 0, "description": "Free-running frequency f0 [Hz]." },
    "amplitude": { "type": "number", "exclusiveMinimum": 0,
                   "description": "Peak amplitude [V]: span offset..offset+amplitude (saw/tri/square) or offset±amplitude (sine)." },
    "offset":    { "type": "number", "description": "DC offset [V]. Required — no implicit 0." },
    "phase":     { "type": "number", "description": "Starting phase [rad]. Absent = waveform origin (a defined convention, not a numeric default)." },
    "dutyCycle": { "type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1,
                   "description": "High fraction of the period (square only)." },
    "frequencyControl": {
      "type": "object", "additionalProperties": false, "required": ["gain"],
      "properties": { "gain": { "type": "number", "description": "VCO gain k [Hz/V] on the control pin pair." } },
      "description": "Present = VCO (LLC/resonant FM control). The control pin pair is part of the component's pin set in CIAS."
    }
  },
  "if":   { "properties": { "shape": { "const": "square" } } },
  "then": { "required": ["dutyCycle"] },
  "else": { "not": { "required": ["dutyCycle"] } }
}
```

Datasheet side (applies when `manufacturerInfo` present; all nullable-leaf
style like AAS): `technology` (`crystal`, `mems`, `tcxo`, `vcxo`, `ocxo`,
`siliconRC`, `programmable`), `outputType` (`cmos`, `lvds`, `lvpecl`,
`clippedSine`, `analog`), `frequencyStability` [1e-6], `agingPerYear` [1e-6],
`rmsPhaseJitter` [s], `startupTime` [s], `supplyVoltage`, `currentConsumption`,
`operatingTemperature` — plus the shared PEAS mixins (`datasheetInfo*`,
mechanical/packaging like AAS).

### 3.2 `timer` — monostable / astable (the 555 family)

The one-shot that rev 1 hacked out of a latch+ramp recipe becomes first-class
(constant-on-time control is its whole reason to exist):

```jsonc
"behavioral": {
  "title": "timerBehavioral",
  "description": "IDEAL timer. mode='monostable': output goes to outputHigh for onTime seconds when v(trigger) crosses threshold in the active direction, then returns to outputLow (retriggerable flag decides mid-pulse behavior). mode='astable': free-running rectangular output with period/dutyCycle (a self-triggered oscillator kept here because real 555 astables are ordered as timers). Backend: monostable -> canonical edge-detect + ramp + comparator subcircuit; astable -> PULSE source.",
  "type": "object",
  "additionalProperties": false,
  "required": ["mode", "outputHigh", "outputLow"],
  "properties": {
    "mode":        { "enum": ["monostable", "astable"] },
    "outputHigh":  { "type": "number", "description": "[V]" },
    "outputLow":   { "type": "number", "description": "[V]" },
    "threshold":   { "type": "number", "description": "Trigger trip level [V] (monostable)." },
    "polarity":    { "enum": ["risingEdge", "fallingEdge"], "description": "Active trigger edge (monostable)." },
    "onTime":      { "type": "number", "exclusiveMinimum": 0, "description": "Pulse width [s] (monostable)." },
    "retriggerable": { "type": "boolean", "description": "true: a trigger during the pulse restarts onTime; false: ignored until the pulse ends. Required for monostable — the two behaviors differ exactly when COT hits minimum-off-time." },
    "period":      { "type": "number", "exclusiveMinimum": 0, "description": "[s] (astable)." },
    "dutyCycle":   { "type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1, "description": "(astable)" }
  },
  "oneOf": [
    { "properties": { "mode": { "const": "monostable" } },
      "required": ["threshold", "polarity", "onTime", "retriggerable"],
      "not": { "anyOf": [ { "required": ["period"] }, { "required": ["dutyCycle"] } ] } },
    { "properties": { "mode": { "const": "astable" } },
      "required": ["period", "dutyCycle"],
      "not": { "anyOf": [ { "required": ["threshold"] }, { "required": ["polarity"] },
                          { "required": ["onTime"] }, { "required": ["retriggerable"] } ] } }
  ]
}
```

Datasheet side: `technology` (`bipolar555`, `cmos555`, `precision`),
timing accuracy, minimum pulse width, supply range, temperature drift.

### 3.3 `latch` — set/reset memory element

The commutation memory for peak-current-mode (clock sets, comparator
resets). Orderable parts exist (74HC279-class discrete latches), thin
datasheet side; the behavioral block is the point:

```jsonc
"behavioral": {
  "title": "latchBehavioral",
  "description": "IDEAL SR latch: output to outputHigh when v(set) rises through setThreshold, to outputLow when v(reset) rises through resetThreshold, HOLDS otherwise. dominance resolves simultaneous set+reset (a real PCM design decision — required, never defaulted; gate latches are reset-dominant so over-current wins the race with the clock). Backend: canonical self-holding B-source V(state)=if(v(set)>Vth,1,if(v(reset)>Vth,0,v(state))) with a 1ns state RC, plus an output stage mapping 0/1 to outputLow/outputHigh; ngspice alternative XSPICE d_srlatch + bridges.",
  "type": "object",
  "additionalProperties": false,
  "required": ["setThreshold", "resetThreshold", "outputHigh", "outputLow", "dominance"],
  "properties": {
    "setThreshold":   { "type": "number", "description": "[V]" },
    "resetThreshold": { "type": "number", "description": "[V] (independent of setThreshold — controllers routinely differ)." },
    "outputHigh":     { "type": "number", "description": "[V]" },
    "outputLow":      { "type": "number", "description": "[V]" },
    "dominance":      { "enum": ["set", "reset"] }
  }
}
```

(Rev 1's open question Q1 — shared vs split thresholds — is resolved: split,
two required fields, no shared-value ambiguity.)

## 4. PEAS citizenship

One edit to `peas.json` (approval item 2): add the `timeBase` discriminator —
a new `oneOf` branch `{"required": ["timeBase"], "properties": {"timeBase":
{"$ref": "https://psma.com/tbas/tbas.json"}}}` mirroring `analog`, plus the
matching `inputs.designRequirements` pin in the root `allOf` (every branch
has one). TBAS documents then validate as PEAS documents with the
`{timeBase: …}` wrap, TAS `component.data` URIs can point into
`time_based.ndjson`, and CIAS resolves them exactly like AAS blocks.

## 5. The other three pieces (unchanged from rev 1)

### 5.1 `time` in the PEAS expression grammar
Add `time` (simulation time [s]) to the documented variable set of the
`controlled` nature's `expression` and the behavioral variable-convention
list (`i`, `v`, `temp`, `v(p,q)`, `i(p,q)`, `i(<designator>)`, **`time`**).
LTspice/ngspice B-sources expose `time` natively; Verilog-A `$abstime`.
Description-text-only schema edit; enables soft-start ramps and bespoke
stimuli with no new atoms.

### 5.2 AAS `sampleHold` behavioral block
`AAS/schemas/sampleHold.json` exists as a catalog family but has no
`$defs/behavioral`, so a S/H can't join a control netlist. Add (mirroring
the comparator block): `mode` (`trackWhileActive` | `sampleOnEdge`),
`threshold` [V], `polarity` (`activeHigh` | `activeLow`) — all required.
Stays in AAS: sampling is analog signal path, and moving the family would
churn a healthy repo.

### 5.3 CTAS `controlScheme` growth + lowerings
Grow from `["synchronousRectifier"]` to `synchronousRectifier |
voltageModePWM | peakCurrentMode | constantOnTime | frequencyControl |
pfcAverageCurrentMode`, each with a `ctas_to_cias` lowering that
instantiates the §6 recipe as a parameterised CIAS brick (f_sw, ramp
amplitude, slope-comp gain, dead time from controller fields).

## 6. Proof it closes the gap — the five control schemes

Using only existing natures (`source`, `switch`, `controlled`), existing AAS
blocks (comparator, multiplier, integrator, op-amp), and TBAS parts:

1. **Voltage-mode PWM** — error amp → TBAS `oscillator` (sawtooth, f_sw) →
   AAS comparator(err, ramp) → gate. *Needs: oscillator.*
2. **Peak-current-mode** — `oscillator` (square, dutyCycle≈0.05) →
   `latch.set`; comparator(i_sense·Ri + slope-comp vs error) →
   `latch.reset`; `dominance: "reset"`; slope comp = the same sawtooth
   through a `controlled` summer. *Needs: oscillator + latch.*
3. **Constant-on-time** — feedback comparator → TBAS `timer` (monostable,
   onTime = T_on, `retriggerable: false`) → gate. One component where rev 1
   needed a four-atom recipe. *Needs: timer.*
4. **Resonant FM (LLC)** — error amp → `oscillator.frequencyControl`
   (triangle VCO around f_res); two AAS comparators at thresholds ±Δ give
   complementary gates with dead time 2Δ/slope. *Needs: VCO oscillator.*
5. **PFC average-current** — AAS multiplier(|v_line| × error) = current
   reference; inner loop as in (2). *Needs: nothing new beyond (2).*

## 7. Emission summary (CIAS C++ work, no schema impact)

| Atom | LTspice | ngspice | Verilog-A |
|---|---|---|---|
| oscillator fixed saw/tri/square | `PULSE(...)` | `PULSE(...)` | event-driven ramp |
| oscillator fixed sine | `SINE(...)` | `SIN(...)` | `sin(2*pi*f*$abstime)` |
| oscillator VCO (any shape) | G+C phase accumulator + shaping B-source | same | `idt()` + shape fn |
| timer monostable | edge-detect + ramp + comparator canonical subckt | same | `@(cross)` + delay state |
| timer astable | `PULSE(...)` | `PULSE(...)` | ramp |
| latch | self-holding B-source + 1 ns state RC | same (or XSPICE `d_srlatch`) | analog memory block |
| `time` | `time` | `time` | `$abstime` |
| sampleHold | SW + C_hold + E-buffer | XSPICE `sample` idiom | `@(cross)` capture |

Each canonical subcircuit is a single tested template in
`CiasCircuitConverter` — one implementation, no per-consumer copies.

## 8. Compatibility & test plan

- Additive everywhere: a new repo, one new PEAS discriminator branch (the
  root `oneOf` grows exactly as it did for `analog`), one new AAS `$defs`
  block, description-text extensions, CTAS enum growth. No existing document
  changes validity.
- TBAS tests: pytest schema suite (meta-validation, registry over siblings,
  per-family valid/negative fixtures — square-without-dutyCycle,
  monostable-with-period, missing dominance — empty-seed, part-less
  behavioral-only, PEAS citizenship both directions).
- CIAS: Catch2 cases asserting emitted netlists per dialect + one ngspice
  smoke sim per §6 recipe (duty tracks error; latch resets on i_sense
  crossing; VCO frequency tracks control voltage; one-shot width = onTime).
- TAS: `time_based.ndjson` starts empty-or-seeded; `test_data.py` picks it
  up by the existing per-type mapping once records land.
- Blade Runner: no checks initially; candidate follow-up once catalog
  records exist (f × stability sanity, jitter floor vs technology).

## 9. Approval checklist (per the ask-per-schema-change rule)

1. Create the `TBAS` repo scaffold with `schemas/tbas.json` +
   `oscillator.json` + `timer.json` + `latch.json` + inputs/outputs as in §3.
2. `PEAS/schemas/peas.json` — add the `timeBase` discriminator branch + DR
   pin (§4).
3. `PEAS/schemas/peas.json` — add `time` to the expression-grammar
   descriptions (§5.1).
4. `AAS/schemas/sampleHold.json` — add `$defs/behavioral` (§5.2).
5. `CTAS` — grow `controlScheme` (+ lowering parameter fields, specified
   exactly once 1–4 are settled) (§5.3).

CIAS emitter code (§7) and tests (§8) follow the normal non-schema flow once
the schemas exist.

## 10. Open questions

- **Q1:** family list — start with `oscillator | timer | latch`, or include
  `rtc` / `clockGenerator` seeds from day one? (Recommend: start with three;
  the family `oneOf` grows the way AAS grew to 14.)
- **Q2:** should TBAS crystal units (bare crystals, no oscillator circuit)
  be a fourth family or a `technology: "crystal"` oscillator? (Recommend:
  `technology` value first; split later if resonator-specific fields — CL,
  ESR, drive level — accumulate.)
- **Q3:** should the §6 recipes ship as named canonical CIAS bricks in
  `CIAS/examples/` (recommended), or only as documentation?
