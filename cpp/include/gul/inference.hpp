/** GUL v2.1 — Inference engine (AND, OR, sequential, parallel, NOT, threshold). */
#pragma once

#include "gul/confidence.hpp"
#include "gul/decision.hpp"
#include "gul/jurisdiction.hpp"
#include <vector>
#include <functional>

namespace gul {

class GULInferenceEngine {
public:
    GULInferenceEngine() = default;
    void enable_trace(bool enabled = true) { trace_enabled_ = enabled; }
    void clear_trace() { trace_.clear(); }

    EvaluatedDecision evaluate_and(const EvaluatedDecision& d1, const EvaluatedDecision& d2);
    EvaluatedDecision evaluate_or(const EvaluatedDecision& d1, const EvaluatedDecision& d2);
    EvaluatedDecision evaluate_sequential(const EvaluatedDecision& d1, const EvaluatedDecision& d2);
    EvaluatedDecision evaluate_parallel(const EvaluatedDecision& d1, const EvaluatedDecision& d2);
    EvaluatedDecision evaluate_not(const EvaluatedDecision& d);
    EvaluatedDecision evaluate_threshold(const EvaluatedDecision& d, double threshold);
    EvaluatedDecision evaluate_jurisdiction_check(
        const EvaluatedDecision& d,
        const JurisdictionId* request_j,
        const JurisdictionId* policy_j);

    EvaluatedDecision evaluate_all(
        const EvaluatedDecision* begin, const EvaluatedDecision* end,
        const char* combiner = "and");

    struct TraceStep {
        std::string rule;
        std::vector<EvaluatedDecision> inputs;
        EvaluatedDecision output;
    };
    const std::vector<TraceStep>& trace() const { return trace_; }

private:
    std::vector<TraceStep> trace_;
    bool trace_enabled_ = true;
    void record_trace(const char* rule,
        const std::vector<EvaluatedDecision>& inputs,
        const EvaluatedDecision& output);
};

} // namespace gul
