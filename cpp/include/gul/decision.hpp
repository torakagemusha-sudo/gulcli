/** GUL v2.1 — 4-valued decision (permit, deny, defer, abstain) and combiners. */
#pragma once

#include "gul/confidence.hpp"
#include <string>
#include <vector>

namespace gul {

enum class Decision {
    PERMIT,
    DENY,
    DEFER,
    ABSTAIN
};

inline const char* to_string(Decision d) {
    switch (d) {
        case Decision::PERMIT:  return "permit";
        case Decision::DENY:    return "deny";
        case Decision::DEFER:   return "defer";
        case Decision::ABSTAIN: return "abstain";
    }
    return "abstain";
}

inline Decision decision_from_string(const std::string& value) {
    if (value == "permit") return Decision::PERMIT;
    if (value == "deny") return Decision::DENY;
    if (value == "defer") return Decision::DEFER;
    return Decision::ABSTAIN;
}

struct JurisdictionId; // forward

struct EvaluatedDecision {
    Decision decision;
    Confidence confidence;
    std::vector<std::string> evidence;
    const JurisdictionId* jurisdiction = nullptr;

    bool is_high_confidence(double threshold = 0.8) const;
    bool should_defer(double min_confidence = 0.5) const;
};

class DecisionCombiner {
public:
    static Decision combine(Decision d1, Decision d2);
    static Decision combine_all(const Decision* begin, const Decision* end);
    static Decision override(Decision base, Decision over);
    static Decision invert(Decision d);
};

inline bool Decision_is_terminal(Decision d) {
    return d == Decision::PERMIT || d == Decision::DENY;
}
inline bool Decision_is_positive(Decision d) { return d == Decision::PERMIT; }
inline bool Decision_is_negative(Decision d) { return d == Decision::DENY; }

} // namespace gul
