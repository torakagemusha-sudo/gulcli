/** Fact environment for native atom predicate evaluation. */
#pragma once

#include "gul/decision.hpp"
#include "gul/json_io.hpp"
#include <cstdint>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <utility>
#include <vector>

namespace gul {

class FactEnvironment {
public:
    static FactEnvironment from_json(const JsonValue& data);

    EvaluatedDecision evaluate_predicate(const JsonValue& pred) const;

private:
    std::map<std::string, std::vector<std::string>> roles_;
    std::map<std::string, std::map<std::string, std::string>> attributes_;
    std::set<std::pair<std::string, std::string>> belongs_to_;
    std::set<std::pair<std::string, std::string>> in_context_;
    std::map<std::string, bool> custom_;
    std::optional<std::int64_t> now_;

    static std::string entity_key(const JsonValue& entity);
    EvaluatedDecision permit(const std::string& evidence, double confidence = 0.95) const;
    EvaluatedDecision deny(const std::string& evidence, double confidence = 1.0) const;
    EvaluatedDecision defer(const std::string& evidence) const;
    std::int64_t current_time() const;
};

} // namespace gul
