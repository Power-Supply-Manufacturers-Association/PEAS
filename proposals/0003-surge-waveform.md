# PEAS-RFC 0003 — `surgeWaveform`: the shared name of a surge/pulse test impulse

- **Status:** ACCEPTED 2026-10-17 (owner approval, with the amendments below) and implemented the same day.
- **Type:** Additive (non-breaking). One new `$def` in `PEAS/schemas/utils.json`.
- **Consumers:** SAS diode (SAS-RFC 0003: `peakPulseCurrentWaveform`, `peakPulsePowerWaveform`,
  `clampingWaveform`) and RAS varistor (`surgeWaveform`, tightened from a free string to this enum).
  Every edge is module → PEAS; no PEAS → module or module → module edge is created.

## Problem

SAS diode pulse ratings (`peakPulseCurrent`, `peakPulsePower`, `clampingVoltage`) are bare numbers
with no field for the test waveform, and their descriptions contradicted each other ("typically
8/20 us" vs "e.g. 10/1000 us"). An I_PP at 8/20 us is many times the I_PP at 10/1000 us of the same
die, so a rating without its waveform cannot be compared or filtered. RAS varistor already carried
the same idea as a free string (`surgeWaveform: "8/20"`). A concept used by two modules belongs in PEAS.

## Why not the MAS/PEAS excitation model

`operatingPointExcitation` describes one period of a periodic excitation (requires `frequency`;
`processed` requires `label` + `peak` + `offset`; every `waveformLabel` is a converter steady-state
shape). A surge rating condition is a single aperiodic impulse identified by a standardised name.
What is reused is MAS's naming pattern: a named string-enum def that a field `$ref`s.

## Change

`utils.json#/$defs/surgeWaveform`: string enum, exactly

`"8/20"`, `"10/1000"`, `"10/350"`, `"2/10"`, `"5/320"`, `"10/700"`, `"10/560"`, `"9/720"`, `"10/160"`, `"TLP 100 ns"`.

Each label names ONE wave of its standard (not always the current):

| value | wave | standard |
|---|---|---|
| 8/20 | current | IEC 61000-4-5 |
| 10/1000 | current | IEC 61643-321 / GR-1089 |
| 10/350 | current | IEC 62305-1 / IEC 61643-11 Class I |
| 2/10 | current | GR-1089 |
| 5/320 | current (of the 10/700 generator) | ITU-T K.20 / K.21 / K.44 |
| 10/700 | voltage | ITU-T K.20 / K.21 / K.44 |
| 10/560 | current | FCC Part 68 / GR-1089 |
| 9/720 | voltage | FCC Part 68 |
| 10/160 | current | GR-1089 |
| TLP 100 ns | rectangular transmission-line pulse | ANSI/ESD STM5.5.1 |

ISO 7637 / ISO 16750 automotive pulses and IEC 61000-4-2 ESD are not members (ESD lives in the SAS
`esdVoltage*` fields). Absent never means a default.

## Amendments made at approval (2026-10-17)

- Member list widened from the draft's five values to ten (telecom `5/320`, `10/700`, `10/560`,
  `9/720`, `10/160`).
- The description no longer calls `2/10` "automotive" (it is Telcordia GR-1089 telecom) and no
  longer claims every label is the current wave: it states, per value, which wave and standard.

## Amendment 2026-10-18: `10/700` as a current label

Approved by Alf on 2026-10-18 (decision D5 of the EMAS `protection` proposal). Gas discharge tube
and thyristor-protector datasheets print current ratings at the ITU-T 10/700 generator as
"200 A, 10/700 µs" (Bourns 2038 series GDT: "200 A, 10/700 µs, 500 operations"). Under the
2026-10-17 wording `10/700` named only the open-circuit voltage wave, so such a line could not be
stored faithfully. The member list is unchanged. Only the description changes:

- On a voltage condition, `10/700` is the open-circuit voltage wave, as before.
- On a current rating, `10/700` is the current that the 10/700 generator drives, recorded as
  printed.
- `5/320` stays the label for a datasheet that names the current wave by its own shape.
- The two labels are never converted into each other.

Users checked: SAS diode (`peakPulseCurrentWaveform`, `peakPulsePowerWaveform`,
`clampingWaveform`, each tied to its rating by `dependentRequired`), RAS varistor
(`surgeWaveform`) and EMAS protection (`pulseRating.waveform`). None of their descriptions or
`dependentRequired` rules names a wave kind. Blade Runner compares waveforms only for string
equality: `DIO_TVS_PULSE_PRODUCT` needs all three labels equal, `DIO_TVS_WAVEFORM_ORDER` uses only
`8/20` and `10/1000`, and the corpus screens split cohorts by label. So a `10/700` current rating
is only ever judged against other `10/700` ratings.

## Amendment 2026-10-18: four telecom current waves

Approved by Alf on 2026-10-18 (decision 3 of the SAS thyristor / JFET / optocoupler proposal).
Four labels are appended exactly as thyristor surge-protector datasheets print them: `5/310`
(current wave of the ITU-T K.20/K.21 and FTZ R12 10/700 generator as older editions and Bourns /
Littelfuse print it; the generator `5/320` also names, kept as printed rather than rewritten),
`5/200` (VDE 0433 10/700 generator), `0.2/310` (I3124 0.5/700 generator) and `10/360` (Eaton SMCP
and Littelfuse SIDACtor surge tables). Without them a Bourns TISP4350H3BJ keeps only five of its
eight impulse ratings and an Eaton SMCP loses its 10/360 rating. New user: SAS thyristor
(`peakPulseCurrents[].waveform`, required on every entry). Enum appends only; no existing value
changes meaning.

## Data impact

None. All 4,086 live varistor rows and 34,746 live diode rows validate before and after
(0 invalid both times, 2026-10-17). The live varistor strings are `8/20` and `10/350`, both members.

## Tests

`tests/test_schemas.py`: exact member list, every member accepted, free strings (`8x20`,
`8/20us`, `10/1000us`, ISO 7637, IEC 61000-4-2, `TLP`, empty, number) rejected, no "automotive"
in the description. With the def removed these tests fail.
