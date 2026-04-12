#include "gul/decision.hpp"
#include "gul/jurisdiction.hpp"

namespace gul {

bool EvaluatedDecision::is_high_confidence(double threshold) const {
    return confidence.value() >= threshold;
}

bool EvaluatedDecision::should_defer(double min_confidence) const {
    return decision == Decision::DEFER || confidence.value() < min_confidence;
}

Decision DecisionCombiner::combine(Decision d1, Decision d2) {
    if (d1 == Decision::DENY || d2 == Decision::DENY) return Decision::DENY;
    if (d1 == Decision::PERMIT && d2 == Decision::PERMIT) return Decision::PERMIT;
    if (d1 == Decision::DEFER || d2 == Decision::DEFER) return Decision::DEFER;
    if (d1 == Decision::ABSTAIN) return d2;
    if (d2 == Decision::ABSTAIN) return d1;
    return Decision::DEFER;
}

Decision DecisionCombiner::combine_all(const Decision* begin, const Decision* end) {
    if (begin == end) return Decision::ABSTAIN;
    Decision r = *begin;
    for (const Decision* p = begin + 1; p != end; ++p)
        r = combine(r, *p);
    return r;
}

Decision DecisionCombiner::override(Decision base, Decision over) {
    if (over == Decision::ABSTAIN) return base;
    return over;
}

Decision DecisionCombiner::invert(Decision d) {
    if (d == Decision::PERMIT) return Decision::DENY;
    if (d == Decision::DENY) return Decision::PERMIT;
    return d;
}

} // namespace gul
