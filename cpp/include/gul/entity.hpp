/** GUL v2.1 — Entity (agent, resource, context, policy). */
#pragma once

#include <string>

namespace gul {

struct Entity {
    std::string kind; // "agent" | "resource" | "context" | "policy"
    std::string id;

    Entity() = default;
    Entity(std::string k, std::string i) : kind(std::move(k)), id(std::move(i)) {}
};

} // namespace gul
