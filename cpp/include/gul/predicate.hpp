/** GUL v2.1 — Predicate (atomic policy predicates). */
#pragma once

#include "gul/entity.hpp"
#include <string>
#include <vector>
#include <cstdint>

namespace gul {

struct Predicate {
    std::string tag;  // belongs_to, has_role, has_attribute, in_context, time_before, time_after, custom
    std::vector<std::string> args;  // serialized args; for custom: [name, ...entity_ids]

    Predicate() = default;
    Predicate(std::string t, std::vector<std::string> a = {})
        : tag(std::move(t)), args(std::move(a)) {}
};

// Helpers
Predicate belongs_to(const Entity& entity, const Entity& resource);
Predicate has_role(const Entity& agent, const std::string& role);
Predicate has_attribute(const Entity& entity, const std::string& attr, const std::string& value);
Predicate in_context(const Entity& entity, const Entity& ctx);
Predicate time_before(std::int64_t timestamp);
Predicate time_after(std::int64_t timestamp);
Predicate custom(const std::string& name);

} // namespace gul
