#include "gul/json_io.hpp"
#include <cctype>
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace gul {
namespace {

class Parser {
public:
    explicit Parser(std::string input) : input_(std::move(input)) {}

    JsonValue parse() {
        skip_ws();
        auto value = parse_value();
        skip_ws();
        if (pos_ != input_.size())
            throw std::runtime_error("unexpected trailing JSON input");
        return value;
    }

private:
    std::string input_;
    std::size_t pos_ = 0;

    char peek() const { return pos_ < input_.size() ? input_[pos_] : '\0'; }

    char get() {
        if (pos_ >= input_.size())
            throw std::runtime_error("unexpected end of JSON input");
        return input_[pos_++];
    }

    void skip_ws() {
        while (pos_ < input_.size() && std::isspace(static_cast<unsigned char>(input_[pos_])))
            ++pos_;
    }

    JsonValue parse_value() {
        skip_ws();
        char c = peek();
        if (c == '{') return parse_object();
        if (c == '[') return parse_array();
        if (c == '"') return parse_string_value();
        if (c == 't' || c == 'f') return parse_bool();
        if (c == 'n') return parse_null();
        if (c == '-' || std::isdigit(static_cast<unsigned char>(c))) return parse_number();
        throw std::runtime_error("invalid JSON value");
    }

    JsonValue parse_object() {
        JsonValue out = JsonValue::null();
        out.type = JsonValue::Type::Object;
        get();
        skip_ws();
        if (peek() == '}') {
            get();
            return out;
        }
        while (true) {
            skip_ws();
            if (peek() != '"')
                throw std::runtime_error("object key must be string");
            std::string key = parse_string();
            skip_ws();
            if (get() != ':')
                throw std::runtime_error("expected ':' in object");
            out.object.emplace(key, parse_value());
            skip_ws();
            char delim = get();
            if (delim == '}') break;
            if (delim != ',')
                throw std::runtime_error("expected ',' or '}' in object");
        }
        return out;
    }

    JsonValue parse_array() {
        JsonValue out = JsonValue::null();
        out.type = JsonValue::Type::Array;
        get();
        skip_ws();
        if (peek() == ']') {
            get();
            return out;
        }
        while (true) {
            out.array.push_back(parse_value());
            skip_ws();
            char delim = get();
            if (delim == ']') break;
            if (delim != ',')
                throw std::runtime_error("expected ',' or ']' in array");
        }
        return out;
    }

    JsonValue parse_string_value() {
        return JsonValue::from_string(parse_string());
    }

    std::string parse_string() {
        if (get() != '"')
            throw std::runtime_error("expected string");
        std::string out;
        while (pos_ < input_.size()) {
            char c = get();
            if (c == '"') return out;
            if (c == '\\') {
                char esc = get();
                switch (esc) {
                    case '"': out.push_back('"'); break;
                    case '\\': out.push_back('\\'); break;
                    case '/': out.push_back('/'); break;
                    case 'b': out.push_back('\b'); break;
                    case 'f': out.push_back('\f'); break;
                    case 'n': out.push_back('\n'); break;
                    case 'r': out.push_back('\r'); break;
                    case 't': out.push_back('\t'); break;
                    case 'u': pos_ += 4; break;
                    default: out.push_back(esc); break;
                }
            } else {
                out.push_back(c);
            }
        }
        throw std::runtime_error("unterminated string");
    }

    JsonValue parse_bool() {
        if (input_.compare(pos_, 4, "true") == 0) {
            pos_ += 4;
            return JsonValue::from_bool(true);
        }
        if (input_.compare(pos_, 5, "false") == 0) {
            pos_ += 5;
            return JsonValue::from_bool(false);
        }
        throw std::runtime_error("invalid boolean");
    }

    JsonValue parse_null() {
        if (input_.compare(pos_, 4, "null") == 0) {
            pos_ += 4;
            return JsonValue::null();
        }
        throw std::runtime_error("invalid null");
    }

    JsonValue parse_number() {
        std::size_t start = pos_;
        if (peek() == '-') get();
        while (std::isdigit(static_cast<unsigned char>(peek()))) get();
        if (peek() == '.') {
            get();
            while (std::isdigit(static_cast<unsigned char>(peek()))) get();
        }
        if (peek() == 'e' || peek() == 'E') {
            get();
            if (peek() == '+' || peek() == '-') get();
            while (std::isdigit(static_cast<unsigned char>(peek()))) get();
        }
        double value = std::stod(input_.substr(start, pos_ - start));
        return JsonValue::from_number(value);
    }
};

} // namespace

JsonValue JsonValue::null() { return JsonValue{}; }
JsonValue JsonValue::from_bool(bool value) {
    JsonValue out;
    out.type = Type::Bool;
    out.b = value;
    return out;
}
JsonValue JsonValue::from_number(double value) {
    JsonValue out;
    out.type = Type::Number;
    out.number = value;
    return out;
}
JsonValue JsonValue::from_string(std::string value) {
    JsonValue out;
    out.type = Type::String;
    out.str = std::move(value);
    return out;
}

const JsonValue* JsonValue::get(const std::string& key) const {
    if (type != Type::Object) return nullptr;
    auto it = object.find(key);
    return it == object.end() ? nullptr : &it->second;
}

std::string JsonValue::get_string(const std::string& key, const std::string& fallback) const {
    const JsonValue* child = get(key);
    return child && child->is_string() ? child->str : fallback;
}

double JsonValue::get_number(const std::string& key, double fallback) const {
    const JsonValue* child = get(key);
    return child && child->is_number() ? child->number : fallback;
}

JsonValue parse_json(const std::string& text) {
    return Parser(text).parse();
}

JsonValue load_json_file(const std::string& path) {
    std::ifstream in(path);
    if (!in)
        throw std::runtime_error("failed to open JSON file: " + path);
    std::ostringstream buffer;
    buffer << in.rdbuf();
    return parse_json(buffer.str());
}

std::string json_escape(const std::string& value) {
    std::string out;
    out.reserve(value.size() + 8);
    for (char c : value) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default: out.push_back(c); break;
        }
    }
    return out;
}

} // namespace gul
