#include "gul/scenarios.hpp"
#include "gul/spec_profile.hpp"
#include "gul/predicate.hpp"
#include <sstream>

namespace gul {

std::vector<std::string> ScenarioRegistry::family_names() {
    return {
        "permit_path",
        "deny_path",
        "defer_escalation",
        "abstain_scope",
        "conflict_resolution",
        "threshold_fail",
        "jurisdiction_override",
    };
}

ScenarioFamily ScenarioRegistry::from_name(const std::string& name) {
    if (name == "permit_path") return ScenarioFamily::PermitPath;
    if (name == "deny_path") return ScenarioFamily::DenyPath;
    if (name == "defer_escalation") return ScenarioFamily::DeferEscalation;
    if (name == "abstain_scope") return ScenarioFamily::AbstainScope;
    if (name == "conflict_resolution") return ScenarioFamily::ConflictResolution;
    if (name == "threshold_fail") return ScenarioFamily::ThresholdFail;
    if (name == "jurisdiction_override") return ScenarioFamily::JurisdictionOverride;
    return ScenarioFamily::PermitPath;
}

ScenarioFamily ScenarioRegistry::pick_balanced(std::size_t index) {
    const auto names = family_names();
    return from_name(names[index % names.size()]);
}

ScenarioFamily ScenarioRegistry::pick_adversarial(std::mt19937& rng) {
    static const ScenarioFamily weighted[] = {
        ScenarioFamily::DenyPath,
        ScenarioFamily::DeferEscalation,
        ScenarioFamily::ConflictResolution,
        ScenarioFamily::ThresholdFail,
        ScenarioFamily::JurisdictionOverride,
        ScenarioFamily::AbstainScope,
        ScenarioFamily::PermitPath,
    };
    std::uniform_int_distribution<std::size_t> dist(0, sizeof(weighted) / sizeof(weighted[0]) - 1);
    return weighted[dist(rng)];
}

ScenarioSample ScenarioRegistry::generate(
    ScenarioFamily family,
    std::mt19937& rng,
    std::uint64_t seed,
    std::size_t index,
    const SpecProfile* spec) {
    Entity agent("agent", "alice");
    Entity resource("resource", "doc-policy");
    Entity context("context", "workspace:prod");
    const std::string family_name = family_names()[static_cast<std::size_t>(family) % family_names().size()];
    const std::string spec_id = spec ? ("spec:" + spec->spec_id) : ("scenario:" + family_name);
    ScenarioSample out{
        DatasetSample{agent, has_role(agent, "reviewer"), 0.0, Decision::PERMIT, Confidence(0.0), {}},
        family_name,
        spec_id,
    };

    switch (family) {
        case ScenarioFamily::PermitPath:
            out.sample = DatasetSample{
                agent,
                has_role(agent, "reviewer"),
                0.92,
                Decision::PERMIT,
                Confidence(0.91),
                {"role check passed", "scenario:permit_path"},
            };
            break;
        case ScenarioFamily::DenyPath:
            out.sample = DatasetSample{
                agent,
                has_attribute(resource, "classification", "secret"),
                0.88,
                Decision::DENY,
                Confidence(0.93),
                {"classification blocked", "scenario:deny_path"},
            };
            break;
        case ScenarioFamily::DeferEscalation:
            out.sample = DatasetSample{
                agent,
                in_context(agent, context),
                0.55,
                Decision::DEFER,
                Confidence(0.52),
                {"confidence below escalation threshold", "scenario:defer_escalation"},
            };
            break;
        case ScenarioFamily::AbstainScope:
            out.sample = DatasetSample{
                agent,
                belongs_to(agent, resource),
                0.80,
                Decision::ABSTAIN,
                Confidence(1.0),
                {"out of jurisdiction scope", "scenario:abstain_scope"},
            };
            break;
        case ScenarioFamily::ConflictResolution:
            out.sample = DatasetSample{
                agent,
                custom("conflict_pair"),
                0.74,
                Decision::DENY,
                Confidence(0.81),
                {"deny dominates permit in conflict", "scenario:conflict_resolution"},
            };
            break;
        case ScenarioFamily::ThresholdFail:
            out.sample = DatasetSample{
                agent,
                has_role(agent, "contractor"),
                0.61,
                Decision::DEFER,
                Confidence(0.58),
                {"below policy threshold", "scenario:threshold_fail"},
            };
            break;
        case ScenarioFamily::JurisdictionOverride:
            out.sample = DatasetSample{
                agent,
                custom("override_grant"),
                0.86,
                Decision::PERMIT,
                Confidence(0.89),
                {"higher authority override", "scenario:jurisdiction_override"},
            };
            break;
    }

    out.sample.provenance_scenario = out.family_name;
    out.sample.provenance_source_spec_id = out.source_spec_id;
    out.sample.provenance_seed = seed;
    out.sample.provenance_generator_version = DATASET_GENERATOR_VERSION;
    out.sample.provenance_index = index;

    if (spec && spec->has_baseline && family == ScenarioFamily::PermitPath) {
        out.sample.decision = spec->baseline_decision;
        out.sample.confidence = Confidence(spec->baseline_confidence);
        out.sample.evidence.push_back("derived from spec inference: " + spec->spec_id);
    }
    return out;
}

} // namespace gul
