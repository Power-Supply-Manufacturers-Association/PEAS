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

// {"origin": "REQUIREMENTS"|"DATASHEET"|"MKF_MODEL" (also accepts IDEAL/REAL/MKF),
//  "allowStoredModelParams": bool, "curveFit": "NONE"|"AUTO"|"LADDER"|"FRACPOLE"|"ROSANO"}
inline Fidelity fidelity_from_json(const nlohmann::json& j) {
    if (!j.is_object() || !j.contains("origin"))
        throw std::runtime_error("Fidelity: object with required 'origin' expected");

    const std::string o = upper(j.at("origin").get<std::string>());
    Fidelity::Origin origin;
    if (o == "REQUIREMENTS" || o == "IDEAL")    origin = Fidelity::Origin::REQUIREMENTS;
    else if (o == "DATASHEET" || o == "REAL")   origin = Fidelity::Origin::DATASHEET;
    else if (o == "MKF_MODEL" || o == "MKF")    origin = Fidelity::Origin::MKF_MODEL;
    else throw std::runtime_error("Fidelity: unknown origin '" + o +
                                  "' (REQUIREMENTS|DATASHEET|MKF_MODEL)");

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
    return Fidelity(origin, allow, cf);
}

} // namespace PEAS
