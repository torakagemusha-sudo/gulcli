/** GUL v2.1 — Policy expression AST (atom, and, or, not, implies, with_confidence, etc.). */
#pragma once

#include "gul/predicate.hpp"
#include <memory>
#include <string>
#include <variant>
#include <vector>

namespace gul {

struct PolicyExpr;

using PolicyExprChild = std::variant<Predicate, std::shared_ptr<PolicyExpr>, double>;

struct PolicyExpr {
    std::string tag;  // atom, and_, or_, not_, implies, with_confidence, always, eventually, until
    std::vector<PolicyExprChild> children;

    PolicyExpr() = default;
    PolicyExpr(std::string t, std::vector<PolicyExprChild> c = {})
        : tag(std::move(t)), children(std::move(c)) {}
};

PolicyExpr atom(const Predicate& pred);
PolicyExpr and_(const PolicyExpr& p1, const PolicyExpr& p2);
PolicyExpr or_(const PolicyExpr& p1, const PolicyExpr& p2);
PolicyExpr not_(const PolicyExpr& p);
PolicyExpr implies(const PolicyExpr& p1, const PolicyExpr& p2);
PolicyExpr with_confidence(const PolicyExpr& p, double c);
PolicyExpr always(const PolicyExpr& p);
PolicyExpr eventually(const PolicyExpr& p);
PolicyExpr until(const PolicyExpr& p1, const PolicyExpr& p2);

} // namespace gul
