#pragma once

// resolve_dimensional_values — resolve a `dimensionWithTolerance` to a single scalar, replicating
// MKF's OpenMagnetics::resolve_dimensional_values (Definitions.h:701-747) semantics:
//   MAXIMUM : maximum -> nominal -> minimum
//   NOMINAL : nominal -> (minimum+maximum)/2 (only when both present) -> maximum -> minimum
//   MINIMUM : minimum -> nominal -> maximum
//
// Template over the generated DimensionWithTolerance type (any type exposing get_nominal() /
// get_minimum() / get_maximum() returning std::optional<double>), so each repo uses its own
// quicktype-generated struct. `exclude*`/`unit` are ignored, exactly as in MKF.
//
// Deviation from MKF: MKF silently returns 0.0 when none of minimum/nominal/maximum is set; the
// PSMA no-fallbacks rule forbids in-band sentinels, and the schema's `anyOf` guarantees at least
// one bound is present, so we THROW instead.

#include <optional>
#include <stdexcept>
#include <nlohmann/json.hpp>

namespace PEAS {

enum class DimensionalValues { MAXIMUM, NOMINAL, MINIMUM };

template <class Dim>
double resolve_dimensional_values(const Dim& d, DimensionalValues preferred = DimensionalValues::NOMINAL) {
    const std::optional<double> nom = d.get_nominal();
    const std::optional<double> lo  = d.get_minimum();
    const std::optional<double> hi  = d.get_maximum();

    switch (preferred) {
        case DimensionalValues::MAXIMUM:
            if (hi)  return *hi;
            if (nom) return *nom;
            if (lo)  return *lo;
            break;
        case DimensionalValues::NOMINAL:
            if (nom)     return *nom;
            if (hi && lo) return 0.5 * (*hi + *lo);
            if (hi)      return *hi;
            if (lo)      return *lo;
            break;
        case DimensionalValues::MINIMUM:
            if (lo)  return *lo;
            if (nom) return *nom;
            if (hi)  return *hi;
            break;
    }
    throw std::runtime_error("resolve_dimensional_values: dimension has no minimum/nominal/maximum");
}

// Pass-through for fields that are already a bare scalar.
inline double resolve_dimensional_values(double value, DimensionalValues = DimensionalValues::NOMINAL) {
    return value;
}

// JSON overload — same MKF semantics for code that holds the dimensionWithTolerance as raw nlohmann::json
// (a {nominal,minimum,maximum} object) or a bare number, rather than the generated struct. Lets json-based
// consumers stop hand-reading nominal/minimum/maximum and share the one canonical resolution rule.
inline double resolve_dimensional_values(const nlohmann::json& j,
                                         DimensionalValues preferred = DimensionalValues::NOMINAL) {
    if (j.is_number()) return j.get<double>();
    auto opt = [&](const char* k) -> std::optional<double> {
        if (j.is_object() && j.contains(k) && j.at(k).is_number()) return j.at(k).get<double>();
        return std::nullopt;
    };
    const std::optional<double> nom = opt("nominal"), lo = opt("minimum"), hi = opt("maximum");
    switch (preferred) {
        case DimensionalValues::MAXIMUM:
            if (hi) return *hi; if (nom) return *nom; if (lo) return *lo; break;
        case DimensionalValues::NOMINAL:
            if (nom) return *nom; if (hi && lo) return 0.5 * (*hi + *lo); if (hi) return *hi; if (lo) return *lo; break;
        case DimensionalValues::MINIMUM:
            if (lo) return *lo; if (nom) return *nom; if (hi) return *hi; break;
    }
    throw std::runtime_error("resolve_dimensional_values(json): dimension has no minimum/nominal/maximum");
}

} // namespace PEAS
