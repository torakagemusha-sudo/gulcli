/** Scenario-driven dataset generation for GUL training samples. */
#pragma once

#include "gul/dataset.hpp"
#include <cstddef>
#include <cstdint>
#include <random>
#include <string>
#include <unordered_map>
#include <vector>

namespace gul {

constexpr const char* DATASET_GENERATOR_VERSION = "2.2.0-dev0";

enum class ScenarioFamily {
    PermitPath,
    DenyPath,
    DeferEscalation,
    AbstainScope,
    ConflictResolution,
    ThresholdFail,
    JurisdictionOverride,
};

struct ScenarioSample {
    DatasetSample sample;
    std::string family_name;
    std::string source_spec_id;
};

class ScenarioRegistry {
public:
    static std::vector<std::string> family_names();
    static ScenarioFamily from_name(const std::string& name);
    static ScenarioSample generate(
        ScenarioFamily family,
        std::mt19937& rng,
        std::uint64_t seed,
        std::size_t index);
    static ScenarioFamily pick_balanced(std::size_t index);
    static ScenarioFamily pick_adversarial(std::mt19937& rng);
};

} // namespace gul
