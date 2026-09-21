# PEAS-RFC 0002 — Reaching the PEAS `substituteInfo` type from the part families (successors and second sources)

- **Status:** ACCEPTED 2026-09-21 and implemented the same day (uncommitted), with the scope
  **widened by owner decision** from three module files to every part family — see *Scope, as
  decided* and *Amendments after implementation*. No successor data has been imported; that is
  separate work.
- **Type:** Additive (non-breaking) schema change. 28 part-schema files in seven modules gain
  one optional property each; PEAS itself changes only in description text.
- **Author:** drafted 2026-09-21
- **Created:** 2026-09-21
- **Depends on:** nothing new. The type already exists
  (`PEAS/schemas/utils.json#/$defs/substituteInfo`) and is already reached by two modules
  (`CTAS/schemas/controller.json`, `COAS/schemas/converter.json`). This RFC adds the same
  edge from the other part families. Every `$ref` is module → PEAS, which is the only
  cross-package direction the workspace allows; no PEAS → module edge and no module → module
  edge is created.

## Summary

`substituteInfo` models a replacement part: `{partNumber, manufacturer, type, notes, source}`
with `type` ∈ `drop-in | near-equivalent | functional | upgrade | downgrade | successor`.
`CTAS/schemas/controller.json` reaches it through a root `substitutesInfo[]` array and
`COAS/schemas/converter.json` through `commerce.substitutes[]`. **`CAS/schemas/capacitor.json`,
`MAS/schemas/magnetic.json` and `RAS/schemas/varistor.json` do not** — and those three files
govern every part for which a manufacturer-published successor is sitting unharvested today.
All three roots are `additionalProperties: false`, so there is no legal place to put the fact
and the importers drop it.

The proposal is the block CTAS already has (seven lines as formatted in these files), added
to those three files — and, by the owner's decision, to every other part family too (*Scope,
as decided*).

### Correction to the brief

The task described `substituteInfo` as **orphaned — referenced by nothing anywhere**. That is
not what the workspace contains, and the difference matters enough to state before anything
else. A walk of every `schemas/*.json` in all repos finds two live references:

```
CTAS/schemas/controller.json:20   "substitutesInfo": { "type": "array",
                                    "items": { "$ref": ".../utils.json#/$defs/substituteInfo" } }
COAS/schemas/converter.json:33    "substitutes":     { "type": "array", "minItems": 1,
                                    "items": { "$ref": ".../utils.json#/$defs/substituteInfo" } }
```

The earlier audit walked PEAS, CAS, MAS, RAS, SAS and TAS — which is exactly the set of repos
that do **not** reference it — and concluded from six repos that nothing did. CTAS and COAS were
outside the walk.

This makes the proposal smaller and stronger than the brief assumed. There is no orphaned type
to justify, no new definition to design and no placement argument to win: the type is in PEAS,
it is in use, and the question is only whether three more families may reach the same
definition. It also means the naming and the shape are already decided by precedent
(`substitutesInfo[]` at the part root, CTAS spelling) rather than open for invention.

What *is* true, and is the whole motivation, is that **no record anywhere carries the field**:
0 of 253,832 capacitors, 0 of 84,208 magnetics, 0 of 3,404 varistors, and 0 of 2,134
controllers — the one catalogue whose schema already permits it. The property exists in CTAS
and has never been written.

## Evidence

Measured 2026-09-21 against this checkout (`/home/alf/PSMA`) and against TDK's Meister database
`/mnt/c/ProgramData/TDK/TDKMeister/tdkData/TstDB.tmdb` (Jet/Access, read with `mdb-export`;
`db_info.product_db_ref_date` = 2026-03-02).

### (a) TDK publishes a replacement part number for 7,968 parts, and we hold 7,274 of them

Meister's `specification` table carries specification type `100000080`, whose `text_value` is
another TDK part number:

```
part_id    specification_type_id  seq_no  text_value
100000013  100000080              0       C0402C0G1C470J020BC
100000032  100000080              0       C0402C0G1C101J020BC
```

7,968 rows, one per part (7,968 distinct `part_id`, every row `seq_no = 0`, every row
`disable_flag = 0`). 7,931 of the 7,968 named successors are themselves rows in Meister's own
`part` table. No part names itself.

Joining on `manufacturerInfo.reference` against the live catalogues — every match's
`manufacturerInfo.name` is `TDK`, so the join is not picking up collisions from other vendors:

| catalogue | matched rows | `status: obsolete` | `nrnd` | `production` |
|---|---|---|---|---|
| `capacitors.ndjson` | 4,501 | 482 | 0 | 4,019 |
| `magnetics.ndjson` | 2,769 | 947 | 1 | 1,821 |
| `varistors.ndjson` | 4 | 4 | 0 | 0 |
| **live total** | **7,274** | **1,433** | **1** | **5,840** |
| `quarantine.ndjson` | 162 | | | |

The brief's figure — 1,377 parts (425 capacitors, 948 magnetics, 4 varistors) — is the
**obsolete-status subset**, and measures 1,434 (482 + 947 + 1 + 4) today: the magnetics and
varistor figures reproduce almost exactly (947 vs 948, 4 vs 4) and the capacitor figure has
grown (482 vs 425). The full cohort is 5× larger than the brief states, because TDK also names
a replacement for 5,840 parts it still sells. Those 5,840 are discussed in *(d)* — they are not
claimed here as successors.

### (b) The absence of the field has already put a fabricated value in the catalogue

`TAS/scripts/tdk_meister_import.py` is the importer, and it reads spec `100000080` — it just
has nowhere to put it. Two verbatim comments:

```python
# EOL redirect stub: no real electrical values and no mechanical data — TDK
# keeps it only as a pointer to its replacement part. Not importable.
```

```python
    that test CANNOT work for capacitors: TDK's disc-capacitor stubs carry
    a full 32-spec record - capacitance, tolerance, IR, dimensions - so they sail
    through it and become live parts. 57 such rows did, and one of them acquired a
    440 V rating that belongs to its REPLACEMENT part (10 mm stub vs 8 mm successor).
```

That is `CD10-E2GA152MYGS`, a discontinued 10 mm disc whose record acquired the `X1/440VAC`
rating of `CD45-E2GA152M-GKA`, the 8 mm part TDK names in spec `100000080` as its replacement
(commit `beae721`, "A fabricated 440 V is replaced by TDK's own 400 V"). The vendor stated the
relation, the importer read the relation, the schema had no slot for the relation, and the two
parts' data merged instead. A field that says "this part is replaced by that one" is the direct
antidote to the failure mode that actually occurred.

### (c) Three vendors in the corpus publish this, across three modules

- **TDK** — Meister spec `100000080`, quantified above. Capacitors (CAS), magnetics (MAS),
  varistors (RAS).
- **Panasonic** — `TAS/scripts/panasonic_scrape.py` captures it:
  `elif "recommended replacement" in hl: rec["replacement"] = txt`, described in its own
  docstring as "the part-number, datasheet-PDF and (for EOL) recommended-replacement hrefs".
  `TAS/scripts/panasonic_map.py`, which maps those raw rows onto the schemas, contains no
  occurrence of the string `replacement`: the field is scraped and then dropped at the mapping
  step.
- **Murata** — the PIM API publishes `alternativeProducts`, kept deliberately by
  `TAS/scripts/enumerate_murata_catalog.py`: *"Murata's OWN named replacement is better
  evidence than any similarity match this repo could compute."* It reaches
  `reidentify_murata_parts.py` as `"vendorAlternative": p.get("alternative")` — a key in a
  side report written to a JSON file, never to a catalogue record, because there is no field
  to write it to.

### (d) The corpus-wide need is larger than TDK and spans six modules

Live rows whose `manufacturerInfo.status` already says the part should not be designed in:

| catalogue | `obsolete` | `nrnd` | governing module |
|---|---|---|---|
| `connectors.ndjson` | 842 | 1,452 | CONAS |
| `magnetics.ndjson` | 2,530 | 10 | MAS |
| `capacitors.ndjson` | 610 | 0 | CAS |
| `diodes.ndjson` | 11 | 429 | SAS |
| `igbts.ndjson` | 4 | 33 | SAS |
| `varistors.ndjson` | 21 | 0 | RAS |
| `bjts.ndjson` | 2 | 0 | SAS |
| `timing_devices.ndjson` | 0 | 40 | TDAS |
| **total** | **4,020** | **1,964** | six modules |

4,020 parts are marked dead and not one of them can say what to buy instead. This is the
argument for the type living in PEAS — and it already does, which is the point of the
correction above. It is also why the shape must not be invented per family.

### (e) Successors chain, and the chains are short and acyclic

269 of the 7,968 Meister successors are themselves superseded. Maximum chain depth is 2; there
are no cycles and no self-references. 227 of the 7,274 catalogue matches sit on such a chain.
A complete example, all three records live in `magnetics.ndjson`:

```
CLF10040T-100M     status obsolete    → CLF10040T-100M-D
CLF10040T-100M-D   status production  → SPM7054VC-100M-D
SPM7054VC-100M-D   status production  → (no successor)
```

and one in `capacitors.ndjson`, where all three are `production`:

```
C2012JB1H475M125AB → C2012X5R1H475K125AB → C2012X7R1H475K125AC
```

### (f) A successor is frequently a part we do not stock

Of the 3,544 distinct successor part numbers named for our matched rows, 3,178 are present in
the live catalogues and **366 are not**; per record, 924 of 7,274 matched parts (12.7%) name a
successor that is not in the corpus. The single TDK varistor example is one of them:

```
B72542V6300K062  status obsolete  → B72540X6300K062   (absent from varistors.ndjson
                                                       and from quarantine.ndjson)
```

This measurement decides the reference format — see *Design question 3*.

## Why the quantity belongs where this RFC puts it

The type is in PEAS already, correctly: six modules have obsolete parts and three vendors
publish replacements for parts governed by three different modules. A type used by several
modules belongs in PEAS, defined once and `$ref`-ed — which is exactly what CTAS and COAS do.

What is missing is not a definition but three edges. The proposal adds them at the **part
root**, as a sibling of `manufacturerInfo` and `distributorsInfo`, spelled `substitutesInfo`,
identically to CTAS. The four design questions the brief asks are answered below, with the
reasoning rather than the conclusion.

### Design question 1 — `manufacturerInfo`, or the part root?

**Answer: the part root.** Three reasons, one of them purely mechanical.

The mechanical one first, because it disposes of the idea that PEAS could fix this by itself.
`utils.json#/$defs/manufacturerInfo` is **not inherited uniformly**. Its own description says
so: *"Each component family builds its OWN closed manufacturerInfo by `$ref`-ing these field
definitions (by JSON pointer) and adding its datasheetInfo; families do NOT allOf-extend this
(incompatible with `additionalProperties: false`)."* `RAS/schemas/varistor.json` and
`CAS/schemas/capacitor.json` do exactly that — a closed object listing
`utils.json#/$defs/manufacturerInfo/properties/name`, `…/status`, `…/family` one pointer at a
time. `MAS/schemas/magnetic.json` does the opposite: `allOf` over the whole PEAS
`manufacturerInfo` sealed with `unevaluatedProperties: false`. So adding a property to the PEAS
`manufacturerInfo` def would appear automatically in MAS and be invisible in CAS and RAS. There
is no placement that avoids touching the three family files; the choice is only about meaning.

The second reason is meaning. `manufacturerInfo` is the block that identifies the part as the
manufacturer sells it — name, reference, order code, datasheet URL, and the part's own
`datasheetInfo`. A substitute is not an attribute of this part; it is a **relation to a
different part**, most of whose entries (`type: functional`, `source: cross-reference`) are not
manufacturer statements at all. `distributorsInfo` — the other root sibling — is the existing
precedent for "facts about this part that point outside it".

The third is precedent, and it is decisive given that precedent exists: CTAS put
`substitutesInfo[]` at the part root, and a second spelling for the same fact in the same
workspace is how a field becomes unqueryable.

The honest counter-argument, recorded rather than buried: `manufacturerInfo.status` is where
`obsolete` is written, and a successor is that field's natural partner — the two are read
together. That argues for adjacency, and it is the one real point in favour of
`manufacturerInfo`. It loses to the three above, and consumers pay a one-key lookup for it.

### Design question 2 — the whole `substituteInfo`, or only the successor part of it?

**Answer: the whole type, unchanged, with one clarification of what `type: successor` asserts.**

A successor and a second source are genuinely different facts. A successor is *directional*
(A is replaced by B, never the reverse), *time-ordered*, and asserted by the part's own
manufacturer. A second source is *symmetric* (either part can be bought instead of the other)
and usually asserted by a third party or by us. Splitting them into two properties is defensible
on that basis.

It is rejected, for two reasons. First, the existing type already discriminates them, in two
independent fields: `type` (with `successor` as one of six values) and `source` (`manufacturer`
/ `distributor` / `cross-reference` / `engineering`). A second property would duplicate a
distinction the type already carries, and nothing would stop a successor being written into the
substitutes array anyway. Second — and this is the constraint, not a preference — CTAS and COAS
already expose the undivided type. Splitting it here would mean either changing their shape (a
breaking change to two modules, for no evidence in their catalogues) or accepting that a TDK
capacitor and a TDK controller record the same fact under different keys.

What the undivided array does need is a stated reading rule, so that the directionality is not
lost in a general-purpose array. Proposed as description text on the PEAS type, changing no
structure:

- `type: "successor"` means **this part is superseded by the named one**. It is written only
  where the manufacturer says so; it is never inferred from similarity, from a part number
  pattern, or from a status of `obsolete`.
- It is one hop. A record names its own immediate successor, never the end of the chain.
- `manufacturer` omitted on a `successor` entry means the same manufacturer as this part, since
  a manufacturer supersedes its own part. It should be written anyway; it must be written when
  it differs.

The enums need nothing: `source: "manufacturer"` already covers a vendor database such as
Meister, and `type: "successor"` already exists. Checked, not assumed.

### Design question 3 — how is the other part referenced?

**Answer: keep `{partNumber, manufacturer}` — a soft reference — and do not adopt the CIAS URI
grammar.** CIAS references a part with a resolvable locator:

> "The URI grammar is `<catalogue>.ndjson?<key>=<value>` … e.g.
> `TAS/data/mosfets.ndjson?partNumber=C3M0032120K`. A resolvable URI must match exactly one
> record in the named file."

That is the right convention *for CIAS*, which describes a circuit built from parts we hold, and
it is the obvious thing to reach for here. It is wrong for this field, on three grounds:

1. **It would not be writable for 12.7% of the data.** 924 of the 7,274 matched parts name a
   successor that is not in any catalogue file (*Evidence (f)*). A locator that must resolve
   forces those 924 vendor statements to be discarded — re-creating, in a new place, the exact
   loss this RFC exists to stop. The TDK varistor cohort would lose all four of its successors.
2. **It would make PEAS depend on TAS's file layout.** The grammar names catalogue files
   (`mosfets.ndjson`) and therefore a directory that belongs to a consumer repo. PEAS is the
   root; embedding a catalogue's storage layout in it is a dependency in the wrong direction in
   substance even where it is not one in `$ref` mechanics. CIAS may do this because CIAS owns
   that grammar; PEAS may not.
3. **The corpus's own experience says resolution is a gate's job, not a schema's.** CIAS states
   it outright: *"Note what the schema cannot check: that the file exists, that the record
   exists, or that it is unique. Those are the job of the referential-integrity pass
   (`TAS/scripts/check_component_uris.py`), so a dangling reference is invisible here by
   construction."* A soft reference plus a gate is the same guarantee with none of the loss.

So the reference stays `partNumber` (required) + `manufacturer` (optional, meaning "same as this
part" when a successor omits it), and resolution — "does this successor exist in the catalogue,
and exactly once" — belongs to a referential pass alongside `check_component_uris.py`. Stated,
not assumed: JSON Schema cannot check it and must not be asked to.

The bare-string alternative already in the workspace is worth naming as what *not* to copy.
`MAS/schemas/magnetic/core/material.json` has `alternatives`: *"A list of alternative materials
that could replace this one"*, typed `array of string`. No manufacturer, no kind of
substitution, no source. It is a materials-level field, not a part-level one, and its shape is
precisely the impoverished version `substituteInfo` was written to replace.

### Design question 4 — several successors, and a successor that is itself obsolete

**Several:** the property is an array, so `n` successors are `n` entries; no change is needed.
TDK publishes exactly one for every one of its 7,968 parts (all `seq_no = 0`), but Murata's
field is `alternativeProducts`, plural, so the array is not speculative. Order carries no
meaning. Two entries for the same `partNumber` are a defect for the ingest gate, not something
`uniqueItems` can catch (it compares whole objects, so two entries differing only in `notes`
would pass).

**Chained:** each record names its immediate successor and nothing else, and the chain resolves
by traversal — `CLF10040T-100M → CLF10040T-100M-D → SPM7054VC-100M-D`, with the terminal record
naming none. No chain array, no `supersededBy` back-link, no "final replacement" field. The
reasons are that (i) denormalising a chain into every record means every record must be
rewritten when the chain grows a link, (ii) the vendor only ever states one hop, so anything
longer would be our inference presented as TDK's statement, and (iii) the measured chains are
depth 2 and acyclic, so traversal is trivial. Consumers must still be told to traverse and to
bound the walk: a future cycle is a data defect, and the gate should reject one rather than let
a resolver spin.

### What this RFC deliberately does not do

The 5,840 matched parts that TDK still sells (*Evidence (a)*) are **not** proposed for import as
successors. Meister carries no label for spec `100000080` — it appears in none of the
`*_lang` tables — so its meaning is read from its contents and from how the importer already
treats it, and that is sufficient warrant for a discontinued part and not for a live one. The
importer's own comment makes the same point from the other side: *"THE REPLACEMENT SPEC
(100000080) IS NOT THE SIGNAL … 5,845 parts on REAL classes also name a replacement."* So the
first landing is the 1,434 obsolete/NRND matches; the 5,840 production rows wait until TDK's
published label for the field is confirmed. A schema change cannot settle what a vendor field
means.

## Proposed change

*As drafted, three module files gained one optional property each; as decided, every part
family does — see *Scope, as decided* below. The diff is the same seven-line block in every file.*
One PEAS file gains description text.

### 1. `CAS/schemas/capacitor.json` — root properties

```diff
     "distributorsInfo": {
       "description": "Where to buy this component",
       "type": "array",
       "items": { "$ref": "https://psma.com/peas/utils.json#/$defs/distributorInfo" }
-    }
+    },
+    "substitutesInfo": {
+      "description": "Replacement parts for this one: manufacturer-named successors and second sources. An entry with type 'successor' means THIS part is superseded by the named one, one hop, as the manufacturer states it - never inferred from a status of obsolete or from part-number similarity. The schema cannot check that the named part exists in the catalogue, or exists exactly once; that is the referential pass's job, as for CIAS component URIs. Evidence for the claim goes in the record's provenance[] with fields: [\"substitutesInfo\"], carrying the same sourceUrl, retrievedDate and verification stamp as any datasheet field.",
+      "type": "array",
+      "items": { "$ref": "https://psma.com/peas/utils.json#/$defs/substituteInfo" }
+    }
   },
```

(The landed description adds its last sentence — the evidence route — which the owner decision
settled after the draft; see *Compatibility*.)

### 2. `MAS/schemas/magnetic.json` — root properties

The identical block, after `distributorsInfo`. (MAS is committee-stewarded: this file's
change follows the MAS release process and its own `CHANGELOG.md` — 2,769 matched magnetics,
947 of them obsolete.)

### 3. Every other part-family file — root properties

The identical block, byte for byte, immediately after `distributorsInfo` in each of the 26
remaining files listed under *Scope, as decided*. Where `distributorsInfo` was the last root
property the preceding brace gains a comma; where another property followed (`spiceModel`,
`behavioral`, `geometry`, `rotation`) the block is inserted before it. No other line of any
file changes.

### 4. `PEAS/schemas/utils.json` — description text only, no structural change

```diff
     "type": {
       "type": "string",
-      "description": "Type of substitution.",
+      "description": "Kind of substitution. 'successor' is directional and asserts that THIS part is superseded by the named one — one hop, as the manufacturer states it, never inferred from an obsolete status or from a part-number pattern; a superseded successor names its own successor on its own record. The other values are symmetric: either part may be bought in place of the other.",
       "enum": ["drop-in", "near-equivalent", "functional", "upgrade", "downgrade", "successor"]
     },
     "manufacturer": {
       "type": ["string", "null"],
-      "description": "Manufacturer of the substitute."
+      "description": "Manufacturer of the substitute. Omitted on a 'successor' entry it means the same manufacturer as this part, since a manufacturer supersedes its own part; write it anyway, and it MUST be written when it differs."
     },
```

Nothing else changes. No new `$defs`. No enum gains or loses a value. No field becomes required.

### Scope, as drafted and as decided

**As drafted**, this section read: *"`SAS/schemas/*.json`, `RAS/schemas/resistor.json`,
`CONAS/schemas/connector.json` and `AAS/schemas/AAS.json` are deliberately not touched: their
catalogues have obsolete parts (Evidence (d)) but no harvested successor data yet, and they can
adopt the identical five lines when it exists."* The draft wired only the three files where TDK
data is waiting.

**The owner decided the other way (2026-09-21), and the decision is recorded here rather than
silently absorbed.** The reasoning: 4,020 live obsolete and 1,964 NRND rows across six modules
can currently point nowhere, and adding the property only as each vendor's data happens to
arrive means a schema edit per vendor, per family, forever — the same seven-line block, approved and
landed again and again. The shape is fixed by precedent and the edge is module → PEAS, so there
is nothing further to learn by waiting.

So the property lands on **every PEAS part-family file that carries `manufacturerInfo` +
`distributorsInfo` at its root** (enumerated by walking every `schemas/*.json`, not listed from
memory) — 28 files:

| module | files |
|---|---|
| CAS | `capacitor.json` |
| MAS | `magnetic.json` |
| RAS | `resistor.json`, `varistor.json`, `thermistor.json`, `potentiometer.json` |
| SAS | `mosfet.json`, `diode.json`, `igbt.json`, `bjt.json`, `module.json` |
| CONAS | `connector.json`, `connectorAccessory.json` |
| AAS | `adc`, `analogSwitch`, `buffer`, `comparator`, `dac`, `differenceAmplifier`, `instrumentationAmplifier`, `multiplexer`, `multiplier`, `operationalAmplifier`, `programmableGainAmplifier`, `sampleHold` (`.json`) |
| TDAS | `oscillator.json`, `timer.json`, `latch.json` |

`CTAS/schemas/controller.json` already had it and is unchanged.

Two readings of "every module that holds obsolete parts" had to be made, and both are stated so
they can be overruled:

- **TDAS is in.** The decision named SAS, CONAS, AAS and `resistor.json`; it did not name TDAS.
  But the six-module table the decision cites (*Evidence (d)*) includes TDAS
  (`timing_devices.ndjson`, 40 NRND rows), so leaving it out would contradict the stated
  principle. All three TDAS part files get it, not just the two with catalogue rows, so the
  module has one outer shape.
- **Every file within a touched module is in**, not only the ones with obsolete rows today
  (e.g. `thermistor.json`, 535 production rows; `potentiometer.json`; the AAS families, whose
  3,607 rows include no obsolete part). A per-file choice would reproduce, inside a module, the
  per-vendor drift the decision exists to prevent.
- **EMAS is out.** `EMAS/schemas/relay.json` and `switch.json` have the same root shape, but
  `relays.ndjson` (4,693 rows) and `switches.ndjson` (2,914) hold no obsolete or NRND part, and
  EMAS is not among the six modules the decision cites. It is the one remaining part family
  without the property; it adopts the identical block by a one-line decision.
- **MAS building blocks are out.** `MAS/schemas/magnetic/core.json` and `bobbin.json` also carry
  `manufacturerInfo` + `distributorsInfo`, but they are manufacturing building blocks, not
  finished orderable parts, and no evidence in this RFC concerns them.

## Compatibility

Additive and non-breaking, with one explicit non-claim at the end.

- Every currently valid document stays valid. `substitutesInfo` is optional, and every
  touched root is `additionalProperties: false`, so each one only becomes **less** restrictive.
- The seed convention is unaffected **where a seed `anyOf` exists** — 25 of the 28 files. There,
  a document carrying only `substitutesInfo` satisfies no branch and is still rejected, verified
  as a negative test. *As drafted this bullet claimed it for every root; that was wrong for
  three files — see *Amendments after implementation*, item 1.*
- No record is affected: 0 rows in the corpus carry the key today, in any catalogue.
- No migration, no rewrite, no data written before the decision.
- `CTAS/schemas/controller.json` and `COAS/schemas/converter.json` are not edited and their
  documents are unaffected; the description change in `utils.json` alters no validation
  outcome for them.
- **What does change:** documents that were invalid before become valid — namely any document
  carrying `substitutesInfo`. That is the purpose of the change, and it is the only widening.
- **Evidence route — SETTLED (owner decision 2026-09-21).** The evidence for a substitute
  claim is an ordinary entry in the part's `manufacturerInfo.datasheetInfo.provenance[]` with
  `fields: ["substitutesInfo"]`. `substituteInfo` itself gains **no** `sourceUrl` or date
  fields: that would be a second PEAS edit touching CTAS and COAS, which already use the type,
  and it needs its own decision. The consequence is stated plainly because it is the point:
  **a successor claim carries the same `sourceUrl`, `retrievedDate`, `verification` and
  `verificationDate` stamp as any datasheet field, and is held to the same standard.** The
  entry's own `source` enum is a coarse label; the provenance entry is the evidence. This
  matters here specifically — the fabricated 440 V in *Evidence (b)* came from exactly this
  kind of cross-part relation being handled loosely, and a successor pointer with no
  retrievable source would be the same looseness with a field name on it. Validated on three
  real records (see *Implementation*). *As drafted this was an open question, and it claimed
  `provenance[].fields` "is not restricted to `datasheetInfo`"; that overstates the wording —
  see *Amendments after implementation*, item 2.*

## Alternatives considered

1. **Add `successor` / `replacedBy` as a string property on `manufacturerInfo`.** Rejected.
   It is a bare part number with no manufacturer, no kind of substitution and no source — the
   `coreMaterialAlternatives` shape, which is the thing PEAS already improved on. It also
   cannot hold a second source, so the next vendor field would need a second property, and it
   would land automatically in MAS (which `allOf`s PEAS `manufacturerInfo`) while being
   invisible in CAS and RAS (which copy pointers), producing a field present in one family and
   absent in two for no stated reason.

2. **A separate `successorInfo` property, distinct from `substitutesInfo`.** Rejected — see
   *Design question 2*. The facts do differ, but `type` and `source` already distinguish them,
   and a second key would put the same fact under two spellings across five modules.

3. **Reference the successor by CIAS-style URI (`TAS/data/capacitors.ndjson?partNumber=…`).**
   Rejected — see *Design question 3*. It would discard 924 measured vendor statements (12.7%
   of the cohort) for parts we do not stock, and it would write a consumer repo's file layout
   into the workspace root schema.

4. **Store the successor in `manufacturerInfo.description` or in `provenance`.** Rejected
   twice over by house rules: a name/description field holds names, not derivation or
   lifecycle data, and `verificationMethod` is explicitly not a place for anything but
   measurement conditions. Prose is also unqueryable, which defeats the purpose — a
   recommender must be able to *filter* on "has a live successor".

5. **Give each family its own local `substituteInfo` definition.** Rejected by the placement
   rule. The type is used by CTAS and COAS today and by three more families under this
   proposal: a type shared across multiple modules belongs in PEAS, defined once, and a local
   copy is a schema that will drift.

6. **Quarantine obsolete parts instead.** Rejected, and it is not the same fact. Quarantine is
   for records with *verified data errors*; an obsolete part's data is correct — the part is
   simply not to be designed in, which `status` already says. Moving it would also delete the
   successor pointer's subject, and the 5,840 *production* TDK parts that name a replacement
   show the two properties are independent.

7. **Leave it unharvested.** The status quo. It has already cost one fabricated rating
   (*Evidence (b)*), it discards a Panasonic field at the mapping step and a Murata field into
   a side report, and 4,020 dead parts in six catalogues continue to point nowhere.

8. **The narrower scope this RFC originally proposed: only the three files with TDK data
   (`capacitor.json`, `magnetic.json`, `varistor.json`).** Considered — it was the draft — and
   **widened by owner decision**. The draft's argument was that an edge nobody can populate is
   how the orphan-shaped confusion arose. The decision's counter-argument prevailed: the type,
   the name and the shape are all fixed by precedent, so a family's later adoption would be the
   same block with nothing new to decide, and gating it on each vendor's data arriving
   turns one decision into an unbounded series of identical schema edits while 4,020 obsolete
   parts in the unwired families keep pointing nowhere. What the draft's worry *does* still
   warrant is recorded in *Implementation*: the property is empty everywhere, and a field that
   exists but is never written is exactly how CTAS's `substitutesInfo` sat for its whole life.

9. **Add `sourceUrl` / `retrievedDate` to `substituteInfo` itself.** Rejected by owner decision
   in favour of the existing provenance mechanism (see *Compatibility*). It would give a
   substitute claim its own evidence fields, but it is a second PEAS edit to a type CTAS and
   COAS already use, and it would create two places a successor's evidence could live.

## Implementation

Planned text first (as drafted, for three files), then what was actually done.

1. Three schema edits (`CAS/schemas/capacitor.json`, `MAS/schemas/magnetic.json`,
   `RAS/schemas/varistor.json`) plus the two description lines in `PEAS/schemas/utils.json`.
   Each repo's schema change is a separate approval; MAS additionally follows its committee
   release process and gains a `CHANGELOG.md` entry under the next MINOR release.
2. Docs move with the schemas, per the workspace rule: `CAS/docs/schema.md`,
   `RAS/docs/schema.md` and the MAS docs gain the field beside `distributorsInfo`, and
   `CTAS/docs/schema.md` — which already lists `substitutesInfo[] (PEAS shared)` — gains the
   successor reading rule so the two do not drift. *(Corrected in Amendments, item 3: MAS docs
   do not document these properties, and the CTAS rule now lives in the PEAS type itself.)*
3. **The counter-check, stated as the thing that must fail if the change is reverted:**
   - Build a **real** record — the live `magnetics.ndjson` row for `CLF10040T-100M`
     (`status: obsolete`) with
     `"substitutesInfo": [{"partNumber": "CLF10040T-100M-D", "manufacturer": "TDK",
     "type": "successor", "source": "manufacturer"}]` — and validate it against
     `MAS/schemas/magnetic.json` with the full sibling registry
     (`TAS/tests/test_data.py`'s `$id` registry over
     `{PEAS,CIAS,SAS,CAS,RAS,MAS,CTAS,AAS,CONAS}/schemas`).
     Assert **valid after** the change and **invalid before** it
     (`Additional properties are not allowed ('substitutesInfo' was unexpected)`).
     Repeat for a real capacitor (`CD10-E2GA152MYGS` → `CD45-E2GA152M-GKA`) and a real
     varistor (`B72542V6300K062` → `B72540X6300K062`, whose successor is deliberately one we
     do not stock, so the soft reference is exercised).
   - **Then revert the three edits and re-run, and confirm the negative assertions fail.** A
     test that passes in both states proves nothing and is indistinguishable from one that
     works. This is the step, not the intention to do it.
   - Negative cases that must be rejected **both** before and after, so the widening is proved
     to be scoped: an entry without `partNumber`; `type: "replacement"` (not in the enum);
     `source: "vendorDatabase"` (not in the enum); an extra key inside a `substituteInfo`
     entry (the def is `additionalProperties: false`); and a part document carrying
     `substitutesInfo` with no `manufacturerInfo` (the seed branch).
   - `pytest TAS/tests/test_schemas.py -q` (70 cases) and the CAS / RAS / PEAS suites green,
     with the **matched case count checked to be non-zero** — a deleted or mis-tagged test
     reports "no tests ran", which reads like success.
4. Data lands only after acceptance, and separately: the 1,434 obsolete/NRND TDK matches first,
   each entry `{partNumber, manufacturer: "TDK", type: "successor", source: "manufacturer"}`
   with a `provenance[]` entry naming Meister and `fields: ["substitutesInfo"]`. The 5,840
   production matches, the Panasonic EOL rows and the Murata `alternativeProducts` rows follow
   once each vendor's own label for the field is confirmed — see *What this RFC deliberately
   does not do*. Nothing is written to `data/` in advance of the decision.

### What was done (2026-09-21, uncommitted)

**Schemas.** The same seven-line block on all 28 files under *Scope, as decided* — one
distinct block across all of them, `git diff --numstat` `+7 -0` in every file — each confirmed
against `HEAD` to leave every other key of the file identical once `substitutesInfo` is
removed; the two description lines in
`PEAS/schemas/utils.json` (`substituteInfo.type`, `substituteInfo.manufacturer`). No other
schema line changed.

**The counter-check, run, with its results.** The BEFORE schema is the committed `HEAD` blob of
each touched file (`git show HEAD:<path>`, confirmed free of `substitutesInfo` for all 28),
substituted into an otherwise-live `$id` registry of 151 schemas. That is the reverted file's
real content, obtained without mutating a working tree other sessions share.

- **Real records, valid AFTER, invalid BEFORE — 26 of 28 files.** For each file, a real record
  read (never written) from its `TAS/data` catalogue, obsolete or NRND where one exists, else
  the repo's own example: `C0603X5R1A103K030BA` (capacitor, nrnd), `VLS4012ET-2R2M` (magnetic,
  nrnd), `AVR-M14A2C240MT600N` (varistor, obsolete), `MBRS340` (diode, obsolete), `BU931P`
  (bjt, obsolete), `IXGF32N170` (igbt, nrnd), `EPC2019` (mosfet), `BM55B0.5-14DP/2-0.3V(53)`
  (connector, nrnd), `2047230010` (connectorAccessory), `ABM3BN-32.000MHZ-K4Z-T` (oscillator,
  nrnd), `TLC3555` (timer), eleven TI/ADI analog parts (`ADS9316`, `TMUX9832`, `THS6232`,
  `TLV9023L-Q1`, `DAC39RF20`, `INA151`, `INA1H182-SEP`, `TMUX182-SEP`, `AD633`, `TLV4825`,
  `VCA710`), a real resistor, thermistor and potentiometer row, and
  `SAS/examples/03_module_ff2mr12w3m1h.json` for `module.json` (no catalogue holds modules).
  Every one: the record is valid unchanged; with `substitutesInfo` added it is **valid after**
  and **rejected before** with `Additional properties are not allowed ('substitutesInfo' was
  unexpected)`. The successor entry on these 26 is the fixture string
  `TEST-FIXTURE-SUCCESSOR`, deliberately not a plausible part number, because no vendor-named
  successor is on hand for them and a realistic-looking invented one is the very thing this
  RFC exists to prevent.
- **With the real TDK successor**, on the three records the evidence names: `CLF10040T-100M` →
  `CLF10040T-100M-D` (magnetic), `C2012JB1H475M125AB` → `C2012X5R1H475K125AB` (capacitor) and
  `B72542V6300K062` → `B72540X6300K062` (varistor; a successor we do not stock, exercising the
  soft reference) — valid after, rejected before, and still valid after once each also carries
  a `datasheetInfo.provenance[]` entry with `fields: ["substitutesInfo"]` (the settled
  evidence route).
- **The revert makes the positive assertions fail — 26 files on real records.** Against the
  reverted (HEAD) content, every one of the 26 + 3 "valid after" documents above is rejected,
  so the tests measure the change: they pass with it and fail without it. For `latch.json` and
  `sampleHold.json` (no real record — *Amendments*, item 5) only the structural fact is shown:
  the HEAD root is `additionalProperties: false` and does not declare the key.
- **Scope: nothing else was loosened.** Nine negatives × 28 files, each asserted rejected
  **both before and after**: entry without `partNumber`; `type: "replacement"`;
  `source: "vendorDatabase"`; an extra key (`sourceUrl`) inside an entry; `substitutesInfo`
  not an array; an unknown root key (`successorInfo`); a part missing `manufacturerInfo.name`;
  and the two seed probes. 246 of 252 hold; the 6 that do not are the seed probes on three
  files, explained in *Amendments*, item 1. The empty seed `{}` stays valid in all 28, before
  and after.
- **Suites, all green, case counts non-zero:** PEAS `test_schemas.py` 32 passed; CAS 25; RAS
  72; SAS 77; TAS `test_schemas.py` 70; MAS `validate-fixtures.py` 25/25 and
  `validate-samples.py` 8/8; AAS, CONAS, CTAS and TDAS `scripts/validate.py` PASS.
- **No data touched.** Nothing under any `data/` directory was written; no successor was
  imported. `git status` in each touched repo shows only the schema, doc and changelog files
  named here (plus, in CAS, an untracked `proposals/0001-safety-class-per-class-ratings.md`
  that belongs to another session and was left alone).

**Docs, per each repo's own convention.** CAS `docs/schema.md` and RAS `docs/schema.md` (root
field tables) gained a row; SAS `docs/schema.md` gained the table row, a TOC entry and a
`substitutesInfo` subsection beside `distributorsInfo`, and SAS `README.md` its tree, class
diagram and quick-reference row; RAS `README.md` its tree line; CONAS `docs/schema.md` its two
trees; AAS `docs/schema.md` its outer-shape block plus a paragraph; TDAS `docs/schema.md` its
outer-shape line; MAS `CHANGELOG.md` an *Added* entry under `[Unreleased]` and MAS
`docs/glossary.md` a `substituteInfo` row in its Standards Metadata table. `examples/` are
unchanged in every repo — see *Amendments*, item 4.

## Amendments after implementation (2026-09-21)

Recorded rather than silently fixed: the proposal text above was wrong or incomplete in these
places, and a proposal that stays wrong misleads whoever reads it next.

### 1. Three roots have no seed `anyOf`, so "substitutesInfo alone is still rejected" is false there

The draft's *Compatibility* said every root's `anyOf` is
`[{required: [manufacturerInfo]}, {maxProperties: 0}]`. That holds for 25 files.
**`MAS/schemas/magnetic.json`, `CONAS/schemas/connector.json` and
`CONAS/schemas/connectorAccessory.json` have no root `anyOf` at all** (`magnetic.json` has
`required: []`). The scope check caught it: on those three, a document carrying only
`distributorsInfo` was **already accepted before** this change, and a document carrying only
`substitutesInfo` — rejected before — is **accepted after**.

This is not a loosening of anything else: it is the new key being admitted on the same terms
its sibling `distributorsInfo` has always had in those files. Every other negative holds on all
three. It was not "fixed" by adding a seed `anyOf` to MAS or CONAS, because that would
*tighten* two schemas — rejecting documents valid today — which is a breaking change nobody
approved and outside this RFC. It is flagged: if the owner wants a free-floating
`substitutesInfo` rejected in MAS and CONAS, that is the same gap `distributorsInfo` already
has there, and it needs its own decision.

### 2. `provenance[].fields` says "on a part that means datasheetInfo fields"

The draft claimed `fields` "is not restricted to `datasheetInfo`". The schema does not restrict
it — `items` is a free string, and the three real records above validate — but the
description text does: *"On a part that means datasheetInfo fields; on a record with no
datasheetInfo (e.g. a CIAS brick) it means whatever fields the source is claiming."*
`substitutesInfo` is a root sibling of `manufacturerInfo`, not a `datasheetInfo` field, so the
settled route is *valid* but *not yet described* by the text a reader will consult. The
proposed fix is description-only, one clause —
*"On a part that means datasheetInfo fields, or `substitutesInfo`"* — in
`PEAS/schemas/utils.json#/$defs/provenance/items/properties/fields`. It changes no validation
outcome, but it is a PEAS schema edit that was not part of the approval, so it has **not** been
made. Flagged for a yes/no.

### 3. Docs: MAS documents these fields only as glossary terms; CTAS needed no edit

The draft said "the MAS docs gain the field beside `distributorsInfo`". MAS has no section to
put it beside: `docs/magnetic.md` walks `name`, `core`, `coil`, `coreElectricalReference` and
`shunts`, and gives `manufacturerInfo` / `distributorsInfo` no section of their own. What MAS
*does* have is a **Standards Metadata** table in `docs/glossary.md` defining `manufacturerInfo`,
`distributorInfo`, `cost`, `datasheetInfo` and `status` as terms — so `substituteInfo` went
there, as one row beside `distributorInfo`, and the change is recorded in `CHANGELOG.md`, which
is how MAS records schema changes. No `magnetic.md` section was added, because that would
invent a documentation pattern the repo does not use for catalogue-level fields. The draft also
promised the successor reading rule in
`CTAS/docs/schema.md`; that became unnecessary once the rule was written into the PEAS
`substituteInfo` descriptions themselves, which is what CTAS's `$ref` resolves to, so CTAS is
untouched.

### 4. Examples: none changed

Each repo's `examples/` are real, named parts. None has a vendor-published successor on hand,
and adding one to make the example exercise the field would put an invented part relation into
a document that readers copy — the fabrication this RFC is about, in its most visible place.
When the TDK import lands, a real record with a real successor and its provenance entry is the
right example to add.

### 5. Two part files have no real record anywhere in the workspace

`TDAS/schemas/latch.json` and `AAS/schemas/sampleHold.json` have no row in any `TAS/data`
catalogue and no sourced example (the only sample-and-hold example is the ideal behavioural
atom, with no `manufacturerInfo`). A real-record proof is therefore impossible for them, and
none was fabricated. What *was* proved for both: the reverted (HEAD) schema rejects the key,
the new one declares it with the exact PEAS `$ref`, and all nine scope negatives hold — but
only trivially, since the stand-in record they were run on is itself incomplete, so for these two
files the scope check is weaker than for the other 26 and is reported as such. The gap
closes when the first real latch or S/H part is catalogued.
