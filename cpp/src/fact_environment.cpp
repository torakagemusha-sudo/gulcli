#include "gul/fact_environment.hpp"
#include "gul/confidence.hpp"
#include <chrono>
#include <stdexcept>

namespace gul {

std::string FactEnvironment::entity_key(const JsonValue& entity) {
    if (!entity.is_object())
        return "agent:";
    std::string kind = entity.get_string("kind", "agent");
    std::string id = entity.get_string("id");
    return kind + ":" + id;
}

FactEnvironment FactEnvironment::from_json(const JsonValue& data) {
    FactEnvironment env;
    if (const JsonValue* roles = data.get("roles")) {
        if (roles->is_object()) {
            for (const auto& entry : roles->object) {
                std::vector<std::string> values;
                if (entry.second.is_array()) {
                    for (const auto& item : entry.second.array)
                        if (item.is_string()) values.push_back(item.str);
                }
                env.roles_[entry.first] = std::move(values);
            }
        }
    }
    if (const JsonValue* attributes = data.get("attributes")) {
        if (attributes->is_object()) {
            for (const auto& entry : attributes->object) {
                std::map<std::string, std::string> attrs;
                if (entry.second.is_object()) {
                    for (const auto& attr : entry.second.object)
                        if (attr.second.is_string())
                            attrs[attr.first] = attr.second.str;
                }
                env.attributes_[entry.first] = std::move(attrs);
            }
        }
    }
    if (const JsonValue* belongs = data.get("belongs_to")) {
        if (belongs->is_array()) {
            for (const auto& item : belongs->array) {
                if (!item.is_object()) continue;
                const JsonValue* entity = item.get("entity");
                const JsonValue* resource = item.get("resource");
                if (entity && resource)
                    env.belongs_to_.emplace(entity_key(*entity), entity_key(*resource));
            }
        }
    }
    if (const JsonValue* contexts = data.get("in_context")) {
        if (contexts->is_array()) {
            for (const auto& item : contexts->array) {
                if (!item.is_object()) continue;
                const JsonValue* entity = item.get("entity");
                const JsonValue* ctx = item.get("ctx");
                if (!ctx) ctx = item.get("context");
                if (entity && ctx)
                    env.in_context_.emplace(entity_key(*entity), entity_key(*ctx));
            }
        }
    }
    if (const JsonValue* custom = data.get("custom")) {
        if (custom->is_object()) {
            for (const auto& entry : custom->object)
                env.custom_[entry.first] = entry.second.is_bool() && entry.second.b;
        }
    }
    if (const JsonValue* now = data.get("now")) {
        if (now->is_number())
            env.now_ = static_cast<std::int64_t>(now->number);
    }
    return env;
}

std::int64_t FactEnvironment::current_time() const {
    if (now_) return *now_;
    return std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
}

EvaluatedDecision FactEnvironment::permit(const std::string& evidence, double confidence) const {
    return EvaluatedDecision{Decision::PERMIT, Confidence(confidence), {evidence}, nullptr};
}

EvaluatedDecision FactEnvironment::deny(const std::string& evidence, double confidence) const {
    return EvaluatedDecision{Decision::DENY, Confidence(confidence), {evidence}, nullptr};
}

EvaluatedDecision FactEnvironment::defer(const std::string& evidence) const {
    return EvaluatedDecision{Decision::DEFER, Confidence(0.0), {evidence}, nullptr};
}

EvaluatedDecision FactEnvironment::evaluate_predicate(const JsonValue& pred) const {
    if (!pred.is_object())
        throw std::runtime_error("predicate must be an object");
    const std::string tag = pred.get_string("tag");
    if (tag == "has_role") {
        const JsonValue* agent = pred.get("agent");
        std::string agent_key = agent ? entity_key(*agent) : "";
        std::string role = pred.get_string("role");
        auto it = roles_.find(agent_key);
        if (it == roles_.end())
            return defer("fact not found: roles for " + agent_key);
        for (const auto& item : it->second)
            if (item == role)
                return permit("has_role(" + agent_key + ", " + role + ")");
        return deny("missing role '" + role + "' for " + agent_key);
    }
    if (tag == "has_attribute") {
        const JsonValue* entity = pred.get("entity");
        std::string entity_key_value = entity ? entity_key(*entity) : "";
        std::string attr = pred.get_string("attr");
        std::string expected = pred.get_string("value");
        auto it = attributes_.find(entity_key_value);
        if (it == attributes_.end())
            return defer("fact not found: attributes for " + entity_key_value);
        auto attr_it = it->second.find(attr);
        std::string actual = attr_it == it->second.end() ? "" : attr_it->second;
        if (actual == expected)
            return permit("has_attribute(" + entity_key_value + ", " + attr + "=" + expected + ")");
        return deny("attribute '" + attr + "' for " + entity_key_value + " is '" + actual + "', expected '" + expected + "'");
    }
    if (tag == "belongs_to") {
        const JsonValue* entity = pred.get("entity");
        const JsonValue* resource = pred.get("resource");
        std::string left = entity ? entity_key(*entity) : "";
        std::string right = resource ? entity_key(*resource) : "";
        if (belongs_to_.count({left, right}))
            return permit("belongs_to(" + left + ", " + right + ")");
        return deny("no belongs_to fact for " + left + " -> " + right);
    }
    if (tag == "in_context") {
        const JsonValue* entity = pred.get("entity");
        const JsonValue* ctx = pred.get("ctx");
        if (!ctx) ctx = pred.get("context");
        std::string left = entity ? entity_key(*entity) : "";
        std::string right = ctx ? entity_key(*ctx) : "";
        if (in_context_.count({left, right}))
            return permit("in_context(" + left + ", " + right + ")");
        return deny("no in_context fact for " + left + " -> " + right);
    }
    if (tag == "time_before") {
        std::int64_t timestamp = static_cast<std::int64_t>(pred.get_number("timestamp"));
        std::int64_t now = current_time();
        if (now < timestamp)
            return permit("time_before(" + std::to_string(timestamp) + "); now=" + std::to_string(now));
        return deny("time_before(" + std::to_string(timestamp) + ") failed; now=" + std::to_string(now));
    }
    if (tag == "time_after") {
        std::int64_t timestamp = static_cast<std::int64_t>(pred.get_number("timestamp"));
        std::int64_t now = current_time();
        if (now > timestamp)
            return permit("time_after(" + std::to_string(timestamp) + "); now=" + std::to_string(now));
        return deny("time_after(" + std::to_string(timestamp) + ") failed; now=" + std::to_string(now));
    }
    if (tag == "custom") {
        std::string name = pred.get_string("name");
        auto it = custom_.find(name);
        if (it == custom_.end())
            return defer("fact not found: custom." + name);
        if (it->second)
            return permit("custom(" + name + ")");
        return deny("custom(" + name + ") is false");
    }
    return defer("unsupported predicate tag for fact evaluation: " + tag);
}

} // namespace gul
