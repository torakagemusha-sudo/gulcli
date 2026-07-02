#include "gul/spec_profile.hpp"
#include "gul/runtime_io.hpp"
#include <filesystem>

namespace gul {
namespace {

std::string stem_from_path(const std::string& path) {
    const std::filesystem::path p(path);
    std::string stem = p.stem().string();
    if (stem.size() > 4 && stem.substr(stem.size() - 4) == ".gul")
        stem = stem.substr(0, stem.size() - 4);
    return stem.empty() ? "spec" : stem;
}

} // namespace

std::optional<SpecProfile> load_spec_profile(const std::string& path) {
    ValidationResult validation = validate_spec_file(path);
    if (!validation.ok)
        return std::nullopt;

    SpecProfile profile;
    profile.path = path;
    profile.spec_id = stem_from_path(path);
    profile.input_hash = validation.input_hash;

    InferenceResult inference = infer_spec_file(path, false, "");
    profile.has_baseline = true;
    profile.baseline_decision = decision_from_string(inference.decision);
    profile.baseline_confidence = inference.confidence;
    return profile;
}

} // namespace gul
