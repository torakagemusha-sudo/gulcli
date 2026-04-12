#include "gul/predicate.hpp"

namespace gul {

Predicate belongs_to(const Entity& entity, const Entity& resource) {
    return Predicate("belongs_to", { entity.kind + ":" + entity.id, resource.kind + ":" + resource.id });
}

Predicate has_role(const Entity& agent, const std::string& role) {
    return Predicate("has_role", { agent.kind + ":" + agent.id, role });
}

Predicate has_attribute(const Entity& entity, const std::string& attr, const std::string& value) {
    return Predicate("has_attribute", { entity.kind + ":" + entity.id, attr, value });
}

Predicate in_context(const Entity& entity, const Entity& ctx) {
    return Predicate("in_context", { entity.kind + ":" + entity.id, ctx.kind + ":" + ctx.id });
}

Predicate time_before(std::int64_t timestamp) {
    return Predicate("time_before", { std::to_string(timestamp) });
}

Predicate time_after(std::int64_t timestamp) {
    return Predicate("time_after", { std::to_string(timestamp) });
}

Predicate custom(const std::string& name) {
    return Predicate("custom", { name });
}

} // namespace gul
