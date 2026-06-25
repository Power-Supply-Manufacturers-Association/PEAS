#pragma once

// resolve_dimensional_values — JSON overload, split out from Dimension.hpp so THAT header stays
// dependency-free for typed consumers (the generated DimensionWithTolerance structs). Code that holds a
// dimensionWithTolerance as raw nlohmann::json (a {nominal,minimum,maximum} object or a bare number)
// includes this header instead, and gets the SAME MKF resolution semantics (see Dimension.hpp).

#include <optional>
#include <stdexcept>
#include <nlohmann/json.hpp>
#include "Dimension.hpp"

namespace PEAS {

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
