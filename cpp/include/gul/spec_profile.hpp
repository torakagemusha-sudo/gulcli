/** Load GUL spec files for spec-driven dataset generation. */
#pragma once

#include "gul/decision.hpp"
#include <optional>
#include <string>

namespace gul {

struct SpecProfile {
    std::string path;
    std::string spec_id;
    std::string input_hash;
    bool has_baseline = false;
    Decision baseline_decision = Decision::ABSTAIN;
    double baseline_confidence = 0.0;
};

/** Resolve a spec path to an id + optional inferred baseline decision. */
std::optional<SpecProfile> load_spec_profile(const std::string& path);

} // namespace gul
