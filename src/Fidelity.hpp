#pragma once

// Fidelity — the compulsory model-fidelity directive passed to every per-family `to_cias`
// generator and the CIAS converters. Lives in PEAS because PEAS is the common base every
// component repo depends on; it is a pure value type with no schema/data meaning.
//
// Mirrors MKF's enum-throw pattern (ExtraComponentsMode{IDEAL,REAL}, CurveFittingModes):
// no defaults for `origin`, and an invalid origin for a family THROWS rather than falling back.
// See /home/alf/.claude/plans/i-want-everything-in-enchanted-fox.md (decisions 3 & 4).

#include <string>
#include <stdexcept>
#include <map>

namespace PEAS {

struct Fidelity {
    // Where the equivalent circuit is sourced from. REQUIRED — the caller (driven by TAS) must set it.
    //   REQUIREMENTS : ideal model built from inputs.designRequirements (e.g. just R for a resistor).
    //   DATASHEET    : real model derived from datasheetInfo physical values / curves.
    //   MKF_MODEL    : MAS-only — full physical modeling via MKF export_magnetic_as_subcircuit.
    enum class Origin { REQUIREMENTS, DATASHEET, MKF_MODEL };

    // How a real equivalent circuit is fit from datasheet curves (when applicable).
    enum class CurveFit { NONE, AUTO, LADDER, FRACPOLE, ROSANO };

    Origin origin;                          // no default — must be supplied
    bool allowStoredModelParams = false;    // OFF by default: stored modelParams.* used only when true
    CurveFit curveFit = CurveFit::NONE;

    // Per-component origin overrides, keyed by the component's TAS ref (e.g. "T1"). An entry is an
    // explicit USER DIRECTIVE: it wins over both `origin` and any per-component inference the
    // assembler does from the bound data — REQUIREMENTS renders the ideal seed model even for a
    // bound part; DATASHEET/MKF_MODEL demand the corresponding data on the part and the family
    // converter throws when it is absent (no silent downgrade). A ref that matches no component in
    // the assembled TAS is an error (typo protection), enforced by the assembler.
    std::map<std::string, Origin> componentOrigins;

    explicit Fidelity(Origin o,
                      bool allowStored = false,
                      CurveFit cf = CurveFit::NONE)
        : origin(o), allowStoredModelParams(allowStored), curveFit(cf) {}

    bool is_ideal() const { return origin == Origin::REQUIREMENTS; }
    bool is_real()  const { return origin != Origin::REQUIREMENTS; }
};

// Helper for families that do not support the MKF_MODEL origin (everything except MAS):
// throws loudly rather than silently degrading.
inline void reject_mkf_model(const Fidelity& f, const std::string& family) {
    if (f.origin == Fidelity::Origin::MKF_MODEL)
        throw std::runtime_error(family + ": MKF_MODEL origin is only valid for MAS (magnetic)");
}

} // namespace PEAS
