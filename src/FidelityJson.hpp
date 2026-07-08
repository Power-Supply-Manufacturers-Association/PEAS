#pragma once

// JSON <-> Fidelity for the pybind / emscripten bindings. Kept separate from Fidelity.hpp so the
// pure value type stays dependency-free.

#include "Fidelity.hpp"
#include <nlohmann/json.hpp>
#include <string>
#include <algorithm>
#include <stdexcept>

namespace PEAS {

inline std::string upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return std::toupper(c); });
    return s;
}

inline Fidelity::Origin origin_from_string(const std::string& raw) {
    const std::string o = upper(raw);
    if (o == "REQUIREMENTS" || o == "IDEAL")  return Fidelity::Origin::REQUIREMENTS;
    if (o == "DATASHEET" || o == "REAL")      return Fidelity::Origin::DATASHEET;
    if (o == "MKF_MODEL" || o == "MKF")       return Fidelity::Origin::MKF_MODEL;
    throw std::runtime_error("Fidelity: unknown origin '" + o +
                             "' (REQUIREMENTS|DATASHEET|MKF_MODEL)");
}

// {"origin": "REQUIREMENTS"|"DATASHEET"|"MKF_MODEL" (also accepts IDEAL/REAL/MKF),
//  "allowStoredModelParams": bool, "curveFit": "NONE"|"AUTO"|"LADDER"|"FRACPOLE"|"ROSANO",
//  "components": {"<ref>": "<origin>", ...}}   — per-component origin overrides (see Fidelity.hpp)
inline Fidelity fidelity_from_json(const nlohmann::json& j) {
    if (!j.is_object() || !j.contains("origin"))
        throw std::runtime_error("Fidelity: object with required 'origin' expected");

    const Fidelity::Origin origin = origin_from_string(j.at("origin").get<std::string>());

    const bool allow = j.value("allowStoredModelParams", false);

    Fidelity::CurveFit cf = Fidelity::CurveFit::NONE;
    if (j.contains("curveFit")) {
        const std::string c = upper(j.at("curveFit").get<std::string>());
        if      (c == "NONE")     cf = Fidelity::CurveFit::NONE;
        else if (c == "AUTO")     cf = Fidelity::CurveFit::AUTO;
        else if (c == "LADDER")   cf = Fidelity::CurveFit::LADDER;
        else if (c == "FRACPOLE") cf = Fidelity::CurveFit::FRACPOLE;
        else if (c == "ROSANO")   cf = Fidelity::CurveFit::ROSANO;
        else throw std::runtime_error("Fidelity: unknown curveFit '" + c + "'");
    }
    Fidelity f(origin, allow, cf);
    if (j.contains("components")) {
        if (!j.at("components").is_object())
            throw std::runtime_error("Fidelity: 'components' must be an object of ref -> origin");
        for (auto it = j.at("components").begin(); it != j.at("components").end(); ++it) {
            if (!it.value().is_string())
                throw std::runtime_error("Fidelity: components['" + it.key() + "'] must be an origin string");
            f.componentOrigins[it.key()] = origin_from_string(it.value().get<std::string>());
        }
    }
    return f;
}

} // namespace PEAS
