/** File-backed GUL validate/infer for canonical JSON specs. */
#pragma once

#include "gul/json_io.hpp"
#include <string>
#include <vector>

namespace gul {

struct ValidationMessage {
    std::string path;
    std::string code;
    std::string severity;
    std::string message;
};

struct ValidationResult {
    bool ok = false;
    std::string source;
    std::vector<ValidationMessage> errors;
    JsonValue normalized;
    std::string input_hash;
    std::string to_json() const;
};

struct InferenceResult {
    std::string input_hash;
    std::string decision;
    double confidence = 0.0;
    std::vector<std::string> evidence;
    std::string jurisdiction;
    std::vector<std::string> trace_json;
    std::string to_json() const;
};

ValidationResult validate_spec_data(const JsonValue& data, const std::string& source);
InferenceResult infer_spec_data(const JsonValue& data, bool include_trace = false);

ValidationResult validate_spec_file(const std::string& path);
InferenceResult infer_spec_file(const std::string& path, bool include_trace = false, const std::string& facts_path = "");

} // namespace gul
