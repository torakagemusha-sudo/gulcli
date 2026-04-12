#include "gul/inference.hpp"
#include "gul/decision.hpp"
#include <stdexcept>

namespace gul {

void GULInferenceEngine::record_trace(const char* rule,
    const std::vector<EvaluatedDecision>& inputs,
    const EvaluatedDecision& output) {
    if (trace_enabled_)
        trace_.push_back({ rule, inputs, output });
}

EvaluatedDecision GULInferenceEngine::evaluate_and(const EvaluatedDecision& d1, const EvaluatedDecision& d2) {
    std::vector<std::string> evidence = d1.evidence;
    evidence.insert(evidence.end(), d2.evidence.begin(), d2.evidence.end());

    if (d1.decision == Decision::DENY || d2.decision == Decision::DENY) {
        Confidence conf = ConfidenceOps::combine_union(d1.confidence, d2.confidence);
        EvaluatedDecision r{ Decision::DENY, conf, evidence, nullptr };
        record_trace("AND", { d1, d2 }, r);
        return r;
    }
    if (d1.decision == Decision::PERMIT && d2.decision == Decision::PERMIT) {
        Confidence conf = ConfidenceOps::combine_intersection(d1.confidence, d2.confidence);
        EvaluatedDecision r{ Decision::PERMIT, conf, evidence, nullptr };
        record_trace("AND", { d1, d2 }, r);
        return r;
    }
    Confidence conf = ConfidenceOps::combine_intersection(d1.confidence, d2.confidence);
    EvaluatedDecision r{ Decision::DEFER, conf, evidence, nullptr };
    record_trace("AND", { d1, d2 }, r);
    return r;
}

EvaluatedDecision GULInferenceEngine::evaluate_or(const EvaluatedDecision& d1, const EvaluatedDecision& d2) {
    std::vector<std::string> evidence = d1.evidence;
    evidence.insert(evidence.end(), d2.evidence.begin(), d2.evidence.end());

    if (d1.decision == Decision::PERMIT || d2.decision == Decision::PERMIT) {
        Confidence conf = ConfidenceOps::combine_union(d1.confidence, d2.confidence);
        EvaluatedDecision r{ Decision::PERMIT, conf, evidence, nullptr };
        record_trace("OR", { d1, d2 }, r);
        return r;
    }
    if (d1.decision == Decision::DENY && d2.decision == Decision::DENY) {
        Confidence conf = ConfidenceOps::combine_intersection(d1.confidence, d2.confidence);
        EvaluatedDecision r{ Decision::DENY, conf, evidence, nullptr };
        record_trace("OR", { d1, d2 }, r);
        return r;
    }
    Confidence conf = ConfidenceOps::combine_intersection(d1.confidence, d2.confidence);
    EvaluatedDecision r{ Decision::DEFER, conf, evidence, nullptr };
    record_trace("OR", { d1, d2 }, r);
    return r;
}

EvaluatedDecision GULInferenceEngine::evaluate_sequential(const EvaluatedDecision& d1, const EvaluatedDecision& d2) {
    Decision dec = DecisionCombiner::combine(d1.decision, d2.decision);
    Confidence conf = ConfidenceOps::combine_sequential(d1.confidence, d2.confidence);
    std::vector<std::string> evidence = d1.evidence;
    evidence.insert(evidence.end(), d2.evidence.begin(), d2.evidence.end());
    EvaluatedDecision r{ dec, conf, evidence, nullptr };
    record_trace("SEQ", { d1, d2 }, r);
    return r;
}

EvaluatedDecision GULInferenceEngine::evaluate_parallel(const EvaluatedDecision& d1, const EvaluatedDecision& d2) {
    Decision dec = DecisionCombiner::combine(d1.decision, d2.decision);
    Confidence conf = ConfidenceOps::combine_parallel(d1.confidence, d2.confidence);
    std::vector<std::string> evidence = d1.evidence;
    evidence.insert(evidence.end(), d2.evidence.begin(), d2.evidence.end());
    EvaluatedDecision r{ dec, conf, evidence, nullptr };
    record_trace("PAR", { d1, d2 }, r);
    return r;
}

EvaluatedDecision GULInferenceEngine::evaluate_not(const EvaluatedDecision& d) {
    Decision inv = DecisionCombiner::invert(d.decision);
    std::vector<std::string> evidence = d.evidence;
    evidence.push_back(std::string("NOT(") + to_string(d.decision) + ")");
    EvaluatedDecision r{ inv, d.confidence, evidence, d.jurisdiction };
    record_trace("NOT", { d }, r);
    return r;
}

EvaluatedDecision GULInferenceEngine::evaluate_threshold(const EvaluatedDecision& d, double threshold) {
    if (d.confidence.value() >= threshold) {
        record_trace("THRESHOLD", { d }, d);
        return d;
    }
    std::vector<std::string> evidence = d.evidence;
    evidence.push_back("below threshold " + std::to_string(threshold));
    EvaluatedDecision r{ Decision::DEFER, d.confidence, evidence, d.jurisdiction };
    record_trace("THRESHOLD", { d }, r);
    return r;
}

EvaluatedDecision GULInferenceEngine::evaluate_jurisdiction_check(
    const EvaluatedDecision& d,
    const JurisdictionId* request_j,
    const JurisdictionId* policy_j) {
    if (!policy_j) return d;
    if (!request_j) return d;
    if (request_j->is_sub_jurisdiction(*policy_j)) return d;
    std::vector<std::string> evidence = d.evidence;
    evidence.push_back("out of jurisdiction");
    EvaluatedDecision r{ Decision::ABSTAIN, Confidence::one(), evidence, policy_j };
    record_trace("JURISDICTION", { d }, r);
    return r;
}

EvaluatedDecision GULInferenceEngine::evaluate_all(
    const EvaluatedDecision* begin, const EvaluatedDecision* end,
    const char* combiner) {
    std::string c(combiner);
    if (c != "and" && c != "or" && c != "sequential" && c != "parallel")
        throw std::invalid_argument("Unknown combiner");
    if (begin == end)
        return EvaluatedDecision{ Decision::ABSTAIN, Confidence::one(), {}, nullptr };
    if (begin + 1 == end)
        return *begin;
    EvaluatedDecision r = *begin;
    for (const EvaluatedDecision* p = begin + 1; p != end; ++p) {
        if (c == "and") r = evaluate_and(r, *p);
        else if (c == "or") r = evaluate_or(r, *p);
        else if (c == "sequential") r = evaluate_sequential(r, *p);
        else r = evaluate_parallel(r, *p);
    }
    return r;
}

} // namespace gul
