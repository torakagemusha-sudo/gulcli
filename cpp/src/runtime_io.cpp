#include "gul/runtime_io.hpp"
#include "gul/decision.hpp"
#include "gul/fact_environment.hpp"
#include "gul/inference.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <unordered_set>

namespace gul {
namespace {

constexpr const char* RUNTIME_VERSION = "2.2.0-dev0";
const std::unordered_set<std::string> kValidDecisions = {
    "permit", "deny", "defer", "abstain"
};
const std::unordered_set<std::string> kBinaryTags = {
    "and_", "or_", "sequential", "parallel", "implies", "until"
};
const std::unordered_set<std::string> kUnaryTags = {
    "not_", "always", "eventually"
};

struct EvalOutcome {
    Decision decision = Decision::ABSTAIN;
    double confidence = 0.0;
    std::vector<std::string> evidence;
    std::string jurisdiction;
};

void add_message(std::vector<ValidationMessage>& messages,
    const std::string& path, const std::string& code, const std::string& message) {
    messages.push_back({path, code, "error", message});
}

void ensure_confidence(double value, const std::string& path, std::vector<ValidationMessage>& messages) {
    if (value < 0.0 || value > 1.0)
        add_message(messages, path, "E_CONF_RANGE", "confidence must be in [0,1]");
}

JsonValue normalize_value(const JsonValue& value) {
    if (value.is_object()) {
        JsonValue out = JsonValue::null();
        out.type = JsonValue::Type::Object;
        for (const auto& entry : value.object)
            out.object.emplace(entry.first, normalize_value(entry.second));
        return out;
    }
    if (value.is_array()) {
        JsonValue out = JsonValue::null();
        out.type = JsonValue::Type::Array;
        for (const auto& item : value.array)
            out.array.push_back(normalize_value(item));
        return out;
    }
    return value;
}

std::string stable_json(const JsonValue& value);

std::string stable_object(const JsonValue& value) {
    std::ostringstream out;
    out << "{";
    bool first = true;
    for (const auto& entry : value.object) {
        if (!first) out << ",";
        first = false;
        out << "\"" << json_escape(entry.first) << "\":" << stable_json(entry.second);
    }
    out << "}";
    return out.str();
}

std::string stable_json(const JsonValue& value) {
    switch (value.type) {
        case JsonValue::Type::Null: return "null";
        case JsonValue::Type::Bool: return value.b ? "true" : "false";
        case JsonValue::Type::Number: {
            std::ostringstream out;
            out << std::setprecision(15) << value.number;
            return out.str();
        }
        case JsonValue::Type::String:
            return "\"" + json_escape(value.str) + "\"";
        case JsonValue::Type::Array: {
            std::ostringstream out;
            out << "[";
            for (std::size_t i = 0; i < value.array.size(); ++i) {
                if (i) out << ",";
                out << stable_json(value.array[i]);
            }
            out << "]";
            return out.str();
        }
        case JsonValue::Type::Object:
            return stable_object(value);
    }
    return "null";
}

// Minimal SHA-256 for input_hash parity with Python runtime.
std::string sha256_hex(const std::string& input) {
    static const std::uint32_t k[64] = {
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
    };
    auto rotr = [](std::uint32_t x, std::uint32_t n) { return (x >> n) | (x << (32 - n)); };
    std::uint32_t h[8] = {
        0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
    };
    std::vector<std::uint8_t> msg(input.begin(), input.end());
    std::uint64_t bit_len = msg.size() * 8;
    msg.push_back(0x80);
    while ((msg.size() % 64) != 56) msg.push_back(0x00);
    for (int i = 7; i >= 0; --i) msg.push_back(static_cast<std::uint8_t>((bit_len >> (i * 8)) & 0xff));
    for (std::size_t chunk = 0; chunk < msg.size(); chunk += 64) {
        std::uint32_t w[64];
        for (int i = 0; i < 16; ++i) {
            w[i] = (msg[chunk + i * 4] << 24) | (msg[chunk + i * 4 + 1] << 16) |
                   (msg[chunk + i * 4 + 2] << 8) | msg[chunk + i * 4 + 3];
        }
        for (int i = 16; i < 64; ++i) {
            std::uint32_t s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
            std::uint32_t s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16] + s0 + w[i - 7] + s1;
        }
        std::uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
        for (int i = 0; i < 64; ++i) {
            std::uint32_t S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
            std::uint32_t ch = (e & f) ^ ((~e) & g);
            std::uint32_t temp1 = hh + S1 + ch + k[i] + w[i];
            std::uint32_t S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
            std::uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
            std::uint32_t temp2 = S0 + maj;
            hh = g; g = f; f = e; e = d + temp1; d = c; c = b; b = a; a = temp1 + temp2;
        }
        h[0] += a; h[1] += b; h[2] += c; h[3] += d; h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
    }
    std::ostringstream out;
    for (int i = 0; i < 8; ++i)
        out << std::hex << std::setfill('0') << std::setw(8) << h[i];
    return out.str();
}

void validate_predicate(const JsonValue& pred, const std::string& path, std::vector<ValidationMessage>& messages) {
    if (!pred.is_object()) {
        add_message(messages, path, "E_PRED_TYPE", "predicate must be an object");
        return;
    }
    if (!pred.get("tag") || !pred.get("tag")->is_string())
        add_message(messages, path, "E_PRED_TAG", "predicate.tag must be a string");
}

void validate_node(const JsonValue& node, const std::string& path, std::vector<ValidationMessage>& messages) {
    if (!node.is_object()) {
        add_message(messages, path, "E_NODE_TYPE", "expression node must be an object");
        return;
    }
    const JsonValue* tag_value = node.get("tag");
    if (!tag_value || !tag_value->is_string()) {
        add_message(messages, path, "E_TAG", "tag must be a string");
        return;
    }
    const std::string tag = tag_value->str;

    if (kBinaryTags.count(tag)) {
        if (!node.get("p1") || !node.get("p2"))
            add_message(messages, path, "E_BINARY_CHILDREN", tag + " requires p1 and p2");
        else {
            validate_node(*node.get("p1"), path + ".p1", messages);
            validate_node(*node.get("p2"), path + ".p2", messages);
        }
        return;
    }
    if (kUnaryTags.count(tag)) {
        if (!node.get("p"))
            add_message(messages, path, "E_UNARY_CHILD", tag + " requires p");
        else
            validate_node(*node.get("p"), path + ".p", messages);
        return;
    }
    if (tag == "decision") {
        const std::string decision = node.get_string("decision");
        if (!kValidDecisions.count(decision))
            add_message(messages, path, "E_DECISION_VALUE", "decision must be one of permit|deny|defer|abstain");
        ensure_confidence(node.get_number("confidence", 1.0), path + ".confidence", messages);
        return;
    }
    if (tag == "atom") {
        if (!node.get("pred"))
            add_message(messages, path, "E_ATOM_PRED", "atom requires pred");
        else
            validate_predicate(*node.get("pred"), path + ".pred", messages);
        return;
    }
    if (tag == "with_confidence") {
        if (!node.get("p"))
            add_message(messages, path, "E_WITH_CONF_CHILD", "with_confidence requires p");
        else
            validate_node(*node.get("p"), path + ".p", messages);
        ensure_confidence(node.get_number("confidence"), path + ".confidence", messages);
        return;
    }
    if (tag == "threshold") {
        if (!node.get("p"))
            add_message(messages, path, "E_THRESHOLD_CHILD", "threshold requires p");
        else
            validate_node(*node.get("p"), path + ".p", messages);
        ensure_confidence(node.get_number("threshold"), path + ".threshold", messages);
        return;
    }
    if (tag == "jurisdiction") {
        if (!node.get("p"))
            add_message(messages, path, "E_JUR_CHILD", "jurisdiction requires p");
        else
            validate_node(*node.get("p"), path + ".p", messages);
        if (node.get_string("required").empty())
            add_message(messages, path, "E_JUR_REQUIRED", "jurisdiction.required must be a non-empty string");
        return;
    }
    if (tag == "override") {
        if (!node.get("base") || !node.get("override"))
            add_message(messages, path, "E_OVERRIDE_CHILDREN", "override requires base and override");
        else {
            validate_node(*node.get("base"), path + ".base", messages);
            validate_node(*node.get("override"), path + ".override", messages);
        }
        return;
    }
    add_message(messages, path, "E_TAG_UNKNOWN", "unknown tag: " + tag);
}

Decision parse_decision(const std::string& value) {
    if (value == "permit") return Decision::PERMIT;
    if (value == "deny") return Decision::DENY;
    if (value == "defer") return Decision::DEFER;
    return Decision::ABSTAIN;
}

EvaluatedDecision from_decision_node(const JsonValue& node) {
    EvaluatedDecision out{
        parse_decision(node.get_string("decision")),
        Confidence(node.get_number("confidence", 1.0)),
        {},
        nullptr
    };
    if (const JsonValue* evidence = node.get("evidence")) {
        if (evidence->is_array())
            for (const auto& item : evidence->array)
                if (item.is_string()) out.evidence.push_back(item.str);
    }
    return out;
}

EvalOutcome from_evaluated(const EvaluatedDecision& ed, const std::string& jurisdiction = "") {
    EvalOutcome out;
    out.decision = ed.decision;
    out.confidence = ed.confidence.value();
    out.evidence = ed.evidence;
    out.jurisdiction = jurisdiction;
    return out;
}

EvalOutcome eval_atom(const JsonValue& node, const FactEnvironment* facts) {
    if (!facts) {
        throw std::runtime_error(
            "atom nodes require a fact environment; use --facts or python3 -m gulcli infer --facts");
    }
    const JsonValue* pred = node.get("pred");
    if (!pred)
        throw std::runtime_error("atom node missing pred");
    return from_evaluated(facts->evaluate_predicate(*pred));
}

EvalOutcome eval_node(const JsonValue& node, GULInferenceEngine& engine, const FactEnvironment* facts);

EvalOutcome eval_node(const JsonValue& node, GULInferenceEngine& engine, const FactEnvironment* facts) {
    const std::string tag = node.get_string("tag");
    if (tag == "decision") return from_evaluated(from_decision_node(node));
    if (tag == "atom") return eval_atom(node, facts);
    if (tag == "and_") {
        EvalOutcome left = eval_node(*node.get("p1"), engine, facts);
        EvalOutcome right = eval_node(*node.get("p2"), engine, facts);
        EvaluatedDecision d1{left.decision, Confidence(left.confidence), left.evidence, nullptr};
        EvaluatedDecision d2{right.decision, Confidence(right.confidence), right.evidence, nullptr};
        return from_evaluated(engine.evaluate_and(d1, d2), left.jurisdiction.empty() ? right.jurisdiction : left.jurisdiction);
    }
    if (tag == "or_") {
        EvalOutcome left = eval_node(*node.get("p1"), engine, facts);
        EvalOutcome right = eval_node(*node.get("p2"), engine, facts);
        EvaluatedDecision d1{left.decision, Confidence(left.confidence), left.evidence, nullptr};
        EvaluatedDecision d2{right.decision, Confidence(right.confidence), right.evidence, nullptr};
        return from_evaluated(engine.evaluate_or(d1, d2), left.jurisdiction.empty() ? right.jurisdiction : left.jurisdiction);
    }
    if (tag == "sequential") {
        EvalOutcome left = eval_node(*node.get("p1"), engine, facts);
        EvalOutcome right = eval_node(*node.get("p2"), engine, facts);
        EvaluatedDecision d1{left.decision, Confidence(left.confidence), left.evidence, nullptr};
        EvaluatedDecision d2{right.decision, Confidence(right.confidence), right.evidence, nullptr};
        return from_evaluated(engine.evaluate_sequential(d1, d2));
    }
    if (tag == "parallel") {
        EvalOutcome left = eval_node(*node.get("p1"), engine, facts);
        EvalOutcome right = eval_node(*node.get("p2"), engine, facts);
        EvaluatedDecision d1{left.decision, Confidence(left.confidence), left.evidence, nullptr};
        EvaluatedDecision d2{right.decision, Confidence(right.confidence), right.evidence, nullptr};
        return from_evaluated(engine.evaluate_parallel(d1, d2));
    }
    if (tag == "not_") {
        EvalOutcome inner = eval_node(*node.get("p"), engine, facts);
        EvaluatedDecision d{inner.decision, Confidence(inner.confidence), inner.evidence, nullptr};
        return from_evaluated(engine.evaluate_not(d), inner.jurisdiction);
    }
    if (tag == "threshold") {
        EvalOutcome inner = eval_node(*node.get("p"), engine, facts);
        EvaluatedDecision d{inner.decision, Confidence(inner.confidence), inner.evidence, nullptr};
        return from_evaluated(engine.evaluate_threshold(d, node.get_number("threshold")), inner.jurisdiction);
    }
    if (tag == "override") {
        EvalOutcome base = eval_node(*node.get("base"), engine, facts);
        EvalOutcome over = eval_node(*node.get("override"), engine, facts);
        Decision final_decision = DecisionCombiner::override(base.decision, over.decision);
        if (over.decision == Decision::ABSTAIN) {
            EvalOutcome out = base;
            out.evidence.push_back("override abstained");
            return out;
        }
        EvalOutcome out;
        out.decision = final_decision;
        out.confidence = ConfidenceOps::combine_union(Confidence(base.confidence), Confidence(over.confidence)).value();
        out.evidence = base.evidence;
        out.evidence.insert(out.evidence.end(), over.evidence.begin(), over.evidence.end());
        out.evidence.push_back("override applied");
        out.jurisdiction = over.jurisdiction.empty() ? base.jurisdiction : over.jurisdiction;
        return out;
    }
    if (tag == "jurisdiction") {
        EvalOutcome inner = eval_node(*node.get("p"), engine, facts);
        std::string required = node.get_string("required");
        std::string request = node.get_string("request", required);
        if (request == required || request.rfind(required + ".", 0) == 0) {
            inner.jurisdiction = required;
            inner.evidence.push_back("jurisdiction in scope: " + request + " ⊆ " + required);
            return inner;
        }
        EvalOutcome out;
        out.decision = Decision::ABSTAIN;
        out.confidence = 1.0;
        out.jurisdiction = required;
        out.evidence = inner.evidence;
        out.evidence.push_back("out of jurisdiction: " + request + " ⊄ " + required);
        return out;
    }
    if (tag == "implies") {
        EvalOutcome antecedent = eval_node(*node.get("p1"), engine, facts);
        EvalOutcome consequent = eval_node(*node.get("p2"), engine, facts);
        EvaluatedDecision d1{antecedent.decision, Confidence(antecedent.confidence), antecedent.evidence, nullptr};
        EvaluatedDecision d2{consequent.decision, Confidence(consequent.confidence), consequent.evidence, nullptr};
        EvaluatedDecision not_a = engine.evaluate_not(d1);
        return from_evaluated(engine.evaluate_or(not_a, d2));
    }
    if (tag == "with_confidence") {
        EvalOutcome inner = eval_node(*node.get("p"), engine, facts);
        Confidence annotated(node.get_number("confidence"));
        EvalOutcome out = inner;
        out.confidence = ConfidenceOps::combine_intersection(Confidence(inner.confidence), annotated).value();
        out.evidence.push_back("annotated confidence=" + std::to_string(annotated.value()));
        return out;
    }
    if (tag == "always" || tag == "eventually") {
        EvalOutcome inner = eval_node(*node.get("p"), engine, facts);
        inner.evidence.push_back(std::string(tag) + " constraint preserved structurally");
        return inner;
    }
    if (tag == "until") {
        EvalOutcome left = eval_node(*node.get("p1"), engine, facts);
        EvalOutcome right = eval_node(*node.get("p2"), engine, facts);
        EvaluatedDecision d1{left.decision, Confidence(left.confidence), left.evidence, nullptr};
        EvaluatedDecision d2{right.decision, Confidence(right.confidence), right.evidence, nullptr};
        EvalOutcome out = from_evaluated(engine.evaluate_sequential(d1, d2));
        out.evidence.push_back("until composed as sequential approximation");
        return out;
    }
    throw std::runtime_error("unsupported tag: " + tag);
}

const JsonValue& root_expr(const JsonValue& data) {
    if (data.is_object() && data.get("expr"))
        return *data.get("expr");
    return data;
}

std::string render_errors_json(const std::vector<ValidationMessage>& messages) {
    std::ostringstream out;
    out << "[";
    for (std::size_t i = 0; i < messages.size(); ++i) {
        if (i) out << ",";
        const auto& msg = messages[i];
        out << "{\"path\":\"" << json_escape(msg.path) << "\",\"code\":\"" << json_escape(msg.code)
            << "\",\"severity\":\"" << json_escape(msg.severity) << "\",\"message\":\""
            << json_escape(msg.message) << "\"}";
    }
    out << "]";
    return out.str();
}

} // namespace

ValidationResult validate_spec_data(const JsonValue& data, const std::string& source) {
    ValidationResult result;
    result.source = source;
    validate_node(root_expr(data), "$", result.errors);
    result.normalized = normalize_value(data);
    result.ok = result.errors.empty();
    result.input_hash = sha256_hex(stable_json(result.normalized));
    return result;
}

InferenceResult infer_spec_data(const JsonValue& data, bool include_trace, const FactEnvironment* facts) {
    ValidationResult validation = validate_spec_data(data, "<memory>");
    if (!validation.ok)
        throw std::runtime_error("input did not validate");

    GULInferenceEngine engine;
    EvalOutcome outcome = eval_node(root_expr(data), engine, facts);
    InferenceResult result;
    result.input_hash = validation.input_hash;
    result.decision = to_string(outcome.decision);
    result.confidence = outcome.confidence;
    result.evidence = outcome.evidence;
    result.jurisdiction = outcome.jurisdiction;
    if (include_trace) {
        for (const auto& step : engine.trace()) {
            std::ostringstream item;
            item << "{\"rule\":\"" << json_escape(step.rule) << "\",\"output\":{"
                 << "\"decision\":\"" << to_string(step.output.decision) << "\","
                 << "\"confidence\":" << step.output.confidence.value() << "}}";
            result.trace_json.push_back(item.str());
        }
    }
    return result;
}

ValidationResult validate_spec_file(const std::string& path) {
    return validate_spec_data(load_json_file(path), path);
}

InferenceResult infer_spec_file(const std::string& path, bool include_trace, const std::string& facts_path) {
    const FactEnvironment* facts_ptr = nullptr;
    FactEnvironment facts;
    if (!facts_path.empty()) {
        facts = FactEnvironment::from_json(load_json_file(facts_path));
        facts_ptr = &facts;
    }
    return infer_spec_data(load_json_file(path), include_trace, facts_ptr);
}

std::string ValidationResult::to_json() const {
    std::ostringstream out;
    out << "{\n"
        << "  \"schema\": \"gul.validation.result/1\",\n"
        << "  \"version\": \"" << RUNTIME_VERSION << "\",\n"
        << "  \"source\": \"" << json_escape(source) << "\",\n"
        << "  \"ok\": " << (ok ? "true" : "false") << ",\n"
        << "  \"errors\": " << render_errors_json(errors) << ",\n"
        << "  \"normalized\": " << stable_json(normalized) << ",\n"
        << "  \"input_hash\": \"" << input_hash << "\"\n"
        << "}";
    return out.str();
}

std::string InferenceResult::to_json() const {
    std::ostringstream out;
    out << "{\n"
        << "  \"schema\": \"gul.inference.result/1\",\n"
        << "  \"version\": \"" << RUNTIME_VERSION << "\",\n"
        << "  \"input_hash\": \"" << input_hash << "\",\n"
        << "  \"decision\": \"" << decision << "\",\n"
        << "  \"confidence\": " << confidence << ",\n"
        << "  \"evidence\": [";
    for (std::size_t i = 0; i < evidence.size(); ++i) {
        if (i) out << ", ";
        out << "\"" << json_escape(evidence[i]) << "\"";
    }
    out << "],\n  \"jurisdiction\": ";
    if (jurisdiction.empty()) out << "null";
    else out << "\"" << json_escape(jurisdiction) << "\"";
    out << ",\n  \"trace\": [";
    for (std::size_t i = 0; i < trace_json.size(); ++i) {
        if (i) out << ", ";
        out << trace_json[i];
    }
    out << "]\n}";
    return out.str();
}

} // namespace gul
