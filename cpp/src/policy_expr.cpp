#include "gul/policy_expr.hpp"
#include <variant>

namespace gul {

PolicyExpr atom(const Predicate& pred) {
    return PolicyExpr("atom", { PolicyExprChild(pred) });
}

PolicyExpr and_(const PolicyExpr& p1, const PolicyExpr& p2) {
    return PolicyExpr("and_", {
        PolicyExprChild(std::make_shared<PolicyExpr>(p1)),
        PolicyExprChild(std::make_shared<PolicyExpr>(p2))
    });
}

PolicyExpr or_(const PolicyExpr& p1, const PolicyExpr& p2) {
    return PolicyExpr("or_", {
        PolicyExprChild(std::make_shared<PolicyExpr>(p1)),
        PolicyExprChild(std::make_shared<PolicyExpr>(p2))
    });
}

PolicyExpr not_(const PolicyExpr& p) {
    return PolicyExpr("not_", { PolicyExprChild(std::make_shared<PolicyExpr>(p)) });
}

PolicyExpr implies(const PolicyExpr& p1, const PolicyExpr& p2) {
    return PolicyExpr("implies", {
        PolicyExprChild(std::make_shared<PolicyExpr>(p1)),
        PolicyExprChild(std::make_shared<PolicyExpr>(p2))
    });
}

PolicyExpr with_confidence(const PolicyExpr& p, double c) {
    return PolicyExpr("with_confidence", {
        PolicyExprChild(std::make_shared<PolicyExpr>(p)),
        PolicyExprChild(c)
    });
}

PolicyExpr always(const PolicyExpr& p) {
    return PolicyExpr("always", { PolicyExprChild(std::make_shared<PolicyExpr>(p)) });
}

PolicyExpr eventually(const PolicyExpr& p) {
    return PolicyExpr("eventually", { PolicyExprChild(std::make_shared<PolicyExpr>(p)) });
}

PolicyExpr until(const PolicyExpr& p1, const PolicyExpr& p2) {
    return PolicyExpr("until", {
        PolicyExprChild(std::make_shared<PolicyExpr>(p1)),
        PolicyExprChild(std::make_shared<PolicyExpr>(p2))
    });
}

} // namespace gul
