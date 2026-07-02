# PEAS-RFC 0001 — Time-base behavioral atoms (oscillator, latch, `time` variable)

- **Status:** Draft (stub — from the 2026-07 workspace review; the largest remaining
  "express any converter" gap)
- **Created:** 2026-07-02

## Problem

The behavioral atom set (PEAS `behavioral` natures + AAS comparator/multiplier/summer/
integrator) has **no time-base primitive**: no sawtooth/clock oscillator, no VCO, no SR
latch, and PEAS behavioral expressions have no `time` variable. Consequently voltage-mode
PWM, peak-current-mode, constant-on-time, resonant frequency control and PFC multiplier
loops cannot be netlisted at all — CTAS's `controlScheme` is stuck at
`["synchronousRectifier"]`.

## Direction (to be designed)

1. A `nature: "oscillator"` behavioral (waveform label, frequency or control-pin-driven
   VCO gain, amplitude/offset) emitted as a SPICE PULSE/SIN/behavioral source.
2. An SR-latch atom (AAS block or behavioral nature) for PCM/COT commutation.
3. A `time` variable in the behavioral expression grammar (maps to ngspice/LTspice `time`).
4. CTAS `controlScheme` grows (voltageModePWM, peakCurrentMode, constantOnTime,
   frequencyControl, pfcMultiplier) with ctas_to_cias lowerings built from the new atoms.
