/** Minimal JSON value tree for GUL runtime I/O. */
#pragma once

#include <map>
#include <string>
#include <vector>

namespace gul {

struct JsonValue {
    enum class Type { Null, Bool, Number, String, Array, Object };

    Type type = Type::Null;
    bool b = false;
    double number = 0.0;
    std::string str;
    std::vector<JsonValue> array;
    std::map<std::string, JsonValue> object;

    static JsonValue null();
    static JsonValue from_bool(bool value);
    static JsonValue from_number(double value);
    static JsonValue from_string(std::string value);

    bool is_null() const { return type == Type::Null; }
    bool is_object() const { return type == Type::Object; }
    bool is_array() const { return type == Type::Array; }
    bool is_string() const { return type == Type::String; }
    bool is_number() const { return type == Type::Number; }
    bool is_bool() const { return type == Type::Bool; }

    const JsonValue* get(const std::string& key) const;
    std::string get_string(const std::string& key, const std::string& fallback = "") const;
    double get_number(const std::string& key, double fallback = 0.0) const;
};

/** Parse JSON text into a JsonValue tree. Throws std::runtime_error on failure. */
JsonValue parse_json(const std::string& text);

/** Read and parse a JSON file. */
JsonValue load_json_file(const std::string& path);

/** Escape and quote a string for JSON output. */
std::string json_escape(const std::string& value);

} // namespace gul
