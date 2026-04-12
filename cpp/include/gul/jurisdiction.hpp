/** GUL v2.1 — Jurisdiction types and hierarchy. */
#pragma once

#include <string>
#include <vector>
#include <memory>

namespace gul {

enum class JurisdictionLevel {
    GLOBAL,
    REGIONAL,
    ORGANIZATIONAL,
    DEPARTMENTAL,
    PERSONAL
};

inline const char* to_string(JurisdictionLevel l) {
    switch (l) {
        case JurisdictionLevel::GLOBAL:         return "global";
        case JurisdictionLevel::REGIONAL:        return "regional";
        case JurisdictionLevel::ORGANIZATIONAL:  return "organizational";
        case JurisdictionLevel::DEPARTMENTAL:    return "departmental";
        case JurisdictionLevel::PERSONAL:        return "personal";
    }
    return "personal";
}

struct JurisdictionId {
    std::string name;
    std::shared_ptr<JurisdictionId> parent;

    JurisdictionId() = default;
    explicit JurisdictionId(std::string n, std::shared_ptr<JurisdictionId> p = nullptr)
        : name(std::move(n)), parent(std::move(p)) {}

    bool is_sub_jurisdiction(const JurisdictionId& other) const;
    int depth() const;
    std::string fully_qualified_name() const;
};

} // namespace gul
