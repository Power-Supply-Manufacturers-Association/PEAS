#pragma once

// PEAS::Topology — the converter-topology taxonomy enum. PEAS OWNS this vocabulary (every family's
// designRequirements references it); it is defined once in the PEAS schema at
// schemas/utils.json#/$defs/topology. This C++ header is generated from that $def via quicktype
// (--namespace PEAS, -t Topology) and committed here so MAS/CAS/RAS/SAS and downstream consumers
// (Kirchhoff, MKF) share the SINGLE PEAS::Topology type. There is no MAS::Topology — MAS.hpp's generated
// struct is post-processed to use ::PEAS::Topology directly.
//
// Regenerate (when the $def changes):
//   node -e '...extract utils.json#/$defs/topology to a root-enum schema...' && \
//   quicktype -l c++ -s schema --namespace PEAS -t Topology --no-boost ... -o PeasTopology.hpp
// (see PEAS BUILD docs). Keep the enum mirroring the schema's value list exactly.

#include <nlohmann/json.hpp>

#include <optional>
#include <stdexcept>
#include <regex>
#include <unordered_map>
namespace PEAS {
    using nlohmann::json;

    #ifndef NLOHMANN_UNTYPED_PEAS_HELPER
    #define NLOHMANN_UNTYPED_PEAS_HELPER
    inline json get_untyped(const json & j, const char * property) {
        if (j.find(property) != j.end()) {
            return j.at(property).get<json>();
        }
        return json();
    }

    inline json get_untyped(const json & j, std::string property) {
        return get_untyped(j, property.data());
    }
    #endif

    /**
     * Power-electronics converter topology, used by every family's designRequirements to tag
     * which converter a component is designed for (e.g. a capacitor's stress/lifetime model
     * depends on it). PEAS HOSTS this shared vocabulary because all families reference it and
     * PEAS is the only layer beneath them all; MAS OWNS its content (MAS implements the
     * converter topologies under inputs/topologies/ and is the IEC standard candidate). This
     * enum must mirror MAS's implemented topology set exactly — add a value here only when MAS
     * adds the corresponding topology.
     */
    enum class Topology : int { ACTIVE_CLAMP_FORWARD_CONVERTER, ASYMMETRIC_HALF_BRIDGE_CONVERTER, BOOST_CONVERTER, BUCK_CONVERTER, CLLC_RESONANT_CONVERTER, CLLLC_RESONANT_CONVERTER, COMMON_MODE_CHOKE, CUK_CONVERTER, CURRENT_TRANSFORMER, DIFFERENTIAL_MODE_CHOKE, DUAL_ACTIVE_BRIDGE_CONVERTER, FLYBACK_CONVERTER, FOUR_SWITCH_BUCK_BOOST_CONVERTER, ISOLATED_BUCK_BOOST_CONVERTER, ISOLATED_BUCK_CONVERTER, LLC_RESONANT_CONVERTER, PHASE_SHIFTED_FULL_BRIDGE_CONVERTER, PHASE_SHIFTED_HALF_BRIDGE_CONVERTER, POWER_FACTOR_CORRECTION, PUSH_PULL_CONVERTER, SEPIC_CONVERTER, SERIES_RESONANT_CONVERTER, SINGLE_SWITCH_FORWARD_CONVERTER, TWO_SWITCH_FORWARD_CONVERTER, VIENNA_RECTIFIER_CONVERTER, WEINBERG_CONVERTER, ZETA_CONVERTER };
}

namespace PEAS {
    void from_json(const json & j, Topology & x);
    void to_json(json & j, const Topology & x);

    inline void from_json(const json & j, Topology & x) {
        static std::unordered_map<std::string, Topology> enumValues {
            {"activeClampForwardConverter", Topology::ACTIVE_CLAMP_FORWARD_CONVERTER},
            {"asymmetricHalfBridgeConverter", Topology::ASYMMETRIC_HALF_BRIDGE_CONVERTER},
            {"boostConverter", Topology::BOOST_CONVERTER},
            {"buckConverter", Topology::BUCK_CONVERTER},
            {"cllcResonantConverter", Topology::CLLC_RESONANT_CONVERTER},
            {"clllcResonantConverter", Topology::CLLLC_RESONANT_CONVERTER},
            {"commonModeChoke", Topology::COMMON_MODE_CHOKE},
            {"cukConverter", Topology::CUK_CONVERTER},
            {"currentTransformer", Topology::CURRENT_TRANSFORMER},
            {"differentialModeChoke", Topology::DIFFERENTIAL_MODE_CHOKE},
            {"dualActiveBridgeConverter", Topology::DUAL_ACTIVE_BRIDGE_CONVERTER},
            {"flybackConverter", Topology::FLYBACK_CONVERTER},
            {"fourSwitchBuckBoostConverter", Topology::FOUR_SWITCH_BUCK_BOOST_CONVERTER},
            {"isolatedBuckBoostConverter", Topology::ISOLATED_BUCK_BOOST_CONVERTER},
            {"isolatedBuckConverter", Topology::ISOLATED_BUCK_CONVERTER},
            {"llcResonantConverter", Topology::LLC_RESONANT_CONVERTER},
            {"phaseShiftedFullBridgeConverter", Topology::PHASE_SHIFTED_FULL_BRIDGE_CONVERTER},
            {"phaseShiftedHalfBridgeConverter", Topology::PHASE_SHIFTED_HALF_BRIDGE_CONVERTER},
            {"powerFactorCorrection", Topology::POWER_FACTOR_CORRECTION},
            {"pushPullConverter", Topology::PUSH_PULL_CONVERTER},
            {"sepicConverter", Topology::SEPIC_CONVERTER},
            {"seriesResonantConverter", Topology::SERIES_RESONANT_CONVERTER},
            {"singleSwitchForwardConverter", Topology::SINGLE_SWITCH_FORWARD_CONVERTER},
            {"twoSwitchForwardConverter", Topology::TWO_SWITCH_FORWARD_CONVERTER},
            {"viennaRectifierConverter", Topology::VIENNA_RECTIFIER_CONVERTER},
            {"weinbergConverter", Topology::WEINBERG_CONVERTER},
            {"zetaConverter", Topology::ZETA_CONVERTER},
        };
        auto iter = enumValues.find(j.get<std::string>());
        if (iter != enumValues.end()) {
            x = iter->second;
        }
    }

    inline void to_json(json & j, const Topology & x) {
        switch (x) {
            case Topology::ACTIVE_CLAMP_FORWARD_CONVERTER: j = "activeClampForwardConverter"; break;
            case Topology::ASYMMETRIC_HALF_BRIDGE_CONVERTER: j = "asymmetricHalfBridgeConverter"; break;
            case Topology::BOOST_CONVERTER: j = "boostConverter"; break;
            case Topology::BUCK_CONVERTER: j = "buckConverter"; break;
            case Topology::CLLC_RESONANT_CONVERTER: j = "cllcResonantConverter"; break;
            case Topology::CLLLC_RESONANT_CONVERTER: j = "clllcResonantConverter"; break;
            case Topology::COMMON_MODE_CHOKE: j = "commonModeChoke"; break;
            case Topology::CUK_CONVERTER: j = "cukConverter"; break;
            case Topology::CURRENT_TRANSFORMER: j = "currentTransformer"; break;
            case Topology::DIFFERENTIAL_MODE_CHOKE: j = "differentialModeChoke"; break;
            case Topology::DUAL_ACTIVE_BRIDGE_CONVERTER: j = "dualActiveBridgeConverter"; break;
            case Topology::FLYBACK_CONVERTER: j = "flybackConverter"; break;
            case Topology::FOUR_SWITCH_BUCK_BOOST_CONVERTER: j = "fourSwitchBuckBoostConverter"; break;
            case Topology::ISOLATED_BUCK_BOOST_CONVERTER: j = "isolatedBuckBoostConverter"; break;
            case Topology::ISOLATED_BUCK_CONVERTER: j = "isolatedBuckConverter"; break;
            case Topology::LLC_RESONANT_CONVERTER: j = "llcResonantConverter"; break;
            case Topology::PHASE_SHIFTED_FULL_BRIDGE_CONVERTER: j = "phaseShiftedFullBridgeConverter"; break;
            case Topology::PHASE_SHIFTED_HALF_BRIDGE_CONVERTER: j = "phaseShiftedHalfBridgeConverter"; break;
            case Topology::POWER_FACTOR_CORRECTION: j = "powerFactorCorrection"; break;
            case Topology::PUSH_PULL_CONVERTER: j = "pushPullConverter"; break;
            case Topology::SEPIC_CONVERTER: j = "sepicConverter"; break;
            case Topology::SERIES_RESONANT_CONVERTER: j = "seriesResonantConverter"; break;
            case Topology::SINGLE_SWITCH_FORWARD_CONVERTER: j = "singleSwitchForwardConverter"; break;
            case Topology::TWO_SWITCH_FORWARD_CONVERTER: j = "twoSwitchForwardConverter"; break;
            case Topology::VIENNA_RECTIFIER_CONVERTER: j = "viennaRectifierConverter"; break;
            case Topology::WEINBERG_CONVERTER: j = "weinbergConverter"; break;
            case Topology::ZETA_CONVERTER: j = "zetaConverter"; break;
            default: throw std::runtime_error("Unexpected value in enumeration \"Topology\": " + std::to_string(static_cast<int>(x)));
        }
    }
}
