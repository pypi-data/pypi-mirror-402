#include "etb/signature.hpp"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cctype>
#include <stdexcept>

// Simple JSON parsing - we'll use a minimal approach without external dependencies
// For production, consider using nlohmann/json or similar

namespace etb {

// Helper to convert hex string to bytes
std::vector<uint8_t> SignatureDictionary::hex_to_bytes(const std::string& hex) {
    std::vector<uint8_t> bytes;
    for (size_t i = 0; i < hex.length(); i += 2) {
        if (i + 1 >= hex.length()) break;
        std::string byte_str = hex.substr(i, 2);
        uint8_t byte = static_cast<uint8_t>(std::stoul(byte_str, nullptr, 16));
        bytes.push_back(byte);
    }
    return bytes;
}

std::string SignatureDictionary::normalize_name(const std::string& name) {
    std::string normalized = name;
    std::transform(normalized.begin(), normalized.end(), normalized.begin(),
                   [](unsigned char c) { return std::toupper(c); });
    return normalized;
}

// Simple JSON token types
enum class JsonTokenType {
    OBJECT_START, OBJECT_END,
    ARRAY_START, ARRAY_END,
    STRING, NUMBER, BOOL_TRUE, BOOL_FALSE, NULL_VALUE,
    COLON, COMMA, END_OF_INPUT, ERROR
};

struct JsonToken {
    JsonTokenType type;
    std::string value;
};

class JsonLexer {
public:
    explicit JsonLexer(const std::string& input) : input_(input), pos_(0) {}

    JsonToken next_token() {
        skip_whitespace();
        if (pos_ >= input_.size()) {
            return {JsonTokenType::END_OF_INPUT, ""};
        }

        char c = input_[pos_];
        switch (c) {
            case '{': pos_++; return {JsonTokenType::OBJECT_START, "{"};
            case '}': pos_++; return {JsonTokenType::OBJECT_END, "}"};
            case '[': pos_++; return {JsonTokenType::ARRAY_START, "["};
            case ']': pos_++; return {JsonTokenType::ARRAY_END, "]"};
            case ':': pos_++; return {JsonTokenType::COLON, ":"};
            case ',': pos_++; return {JsonTokenType::COMMA, ","};
            case '"': return read_string();
            case 't': return read_literal("true", JsonTokenType::BOOL_TRUE);
            case 'f': return read_literal("false", JsonTokenType::BOOL_FALSE);
            case 'n': return read_literal("null", JsonTokenType::NULL_VALUE);
            default:
                if (c == '-' || std::isdigit(c)) {
                    return read_number();
                }
                return {JsonTokenType::ERROR, std::string(1, c)};
        }
    }

private:
    void skip_whitespace() {
        while (pos_ < input_.size() && std::isspace(input_[pos_])) {
            pos_++;
        }
    }

    JsonToken read_string() {
        pos_++; // skip opening quote
        std::string value;
        while (pos_ < input_.size() && input_[pos_] != '"') {
            if (input_[pos_] == '\\' && pos_ + 1 < input_.size()) {
                pos_++;
                switch (input_[pos_]) {
                    case 'n': value += '\n'; break;
                    case 't': value += '\t'; break;
                    case 'r': value += '\r'; break;
                    case '"': value += '"'; break;
                    case '\\': value += '\\'; break;
                    default: value += input_[pos_]; break;
                }
            } else {
                value += input_[pos_];
            }
            pos_++;
        }
        if (pos_ < input_.size()) pos_++; // skip closing quote
        return {JsonTokenType::STRING, value};
    }

    JsonToken read_number() {
        std::string value;
        if (input_[pos_] == '-') {
            value += input_[pos_++];
        }
        while (pos_ < input_.size() && (std::isdigit(input_[pos_]) || input_[pos_] == '.')) {
            value += input_[pos_++];
        }
        return {JsonTokenType::NUMBER, value};
    }

    JsonToken read_literal(const std::string& literal, JsonTokenType type) {
        if (input_.substr(pos_, literal.size()) == literal) {
            pos_ += literal.size();
            return {type, literal};
        }
        return {JsonTokenType::ERROR, ""};
    }

    const std::string& input_;
    size_t pos_;
};

// Simple JSON value representation
struct JsonValue {
    enum Type { OBJECT, ARRAY, STRING, NUMBER, BOOL, NULL_TYPE } type;
    std::string string_value;
    double number_value = 0;
    bool bool_value = false;
    std::vector<std::pair<std::string, JsonValue>> object_members;
    std::vector<JsonValue> array_elements;

    const JsonValue* get(const std::string& key) const {
        if (type != OBJECT) return nullptr;
        for (const auto& [k, v] : object_members) {
            if (k == key) return &v;
        }
        return nullptr;
    }

    std::string get_string(const std::string& key, const std::string& default_val = "") const {
        auto* v = get(key);
        return (v && v->type == STRING) ? v->string_value : default_val;
    }

    double get_number(const std::string& key, double default_val = 0) const {
        auto* v = get(key);
        return (v && v->type == NUMBER) ? v->number_value : default_val;
    }

    bool get_bool(const std::string& key, bool default_val = false) const {
        auto* v = get(key);
        return (v && v->type == BOOL) ? v->bool_value : default_val;
    }
};

class JsonParser {
public:
    explicit JsonParser(const std::string& input) : lexer_(input), current_token_(lexer_.next_token()) {}

    JsonValue parse() {
        return parse_value();
    }

private:
    JsonValue parse_value() {
        JsonValue value;
        switch (current_token_.type) {
            case JsonTokenType::OBJECT_START:
                return parse_object();
            case JsonTokenType::ARRAY_START:
                return parse_array();
            case JsonTokenType::STRING:
                value.type = JsonValue::STRING;
                value.string_value = current_token_.value;
                advance();
                return value;
            case JsonTokenType::NUMBER:
                value.type = JsonValue::NUMBER;
                value.number_value = std::stod(current_token_.value);
                advance();
                return value;
            case JsonTokenType::BOOL_TRUE:
                value.type = JsonValue::BOOL;
                value.bool_value = true;
                advance();
                return value;
            case JsonTokenType::BOOL_FALSE:
                value.type = JsonValue::BOOL;
                value.bool_value = false;
                advance();
                return value;
            case JsonTokenType::NULL_VALUE:
                value.type = JsonValue::NULL_TYPE;
                advance();
                return value;
            default:
                throw std::runtime_error("Unexpected token in JSON");
        }
    }

    JsonValue parse_object() {
        JsonValue obj;
        obj.type = JsonValue::OBJECT;
        advance(); // skip '{'

        while (current_token_.type != JsonTokenType::OBJECT_END) {
            if (current_token_.type != JsonTokenType::STRING) {
                throw std::runtime_error("Expected string key in object");
            }
            std::string key = current_token_.value;
            advance();

            if (current_token_.type != JsonTokenType::COLON) {
                throw std::runtime_error("Expected ':' after key");
            }
            advance();

            JsonValue value = parse_value();
            obj.object_members.emplace_back(key, value);

            if (current_token_.type == JsonTokenType::COMMA) {
                advance();
            }
        }
        advance(); // skip '}'
        return obj;
    }

    JsonValue parse_array() {
        JsonValue arr;
        arr.type = JsonValue::ARRAY;
        advance(); // skip '['

        while (current_token_.type != JsonTokenType::ARRAY_END) {
            arr.array_elements.push_back(parse_value());
            if (current_token_.type == JsonTokenType::COMMA) {
                advance();
            }
        }
        advance(); // skip ']'
        return arr;
    }

    void advance() {
        current_token_ = lexer_.next_token();
    }

    JsonLexer lexer_;
    JsonToken current_token_;
};

bool SignatureDictionary::load_from_json(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        return false;
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    return load_from_json_string(buffer.str());
}

bool SignatureDictionary::load_from_json_string(const std::string& json_content) {
    try {
        JsonParser parser(json_content);
        JsonValue root = parser.parse();

        if (root.type != JsonValue::OBJECT) {
            return false;
        }

        auto* signatures_array = root.get("signatures");
        if (!signatures_array || signatures_array->type != JsonValue::ARRAY) {
            return false;
        }

        for (const auto& format_json : signatures_array->array_elements) {
            if (format_json.type != JsonValue::OBJECT) continue;

            FormatDefinition format;
            format.format_name = format_json.get_string("format");
            format.category = format_json.get_string("category");
            format.format_id = next_format_id_++;

            // Parse signatures array
            auto* sigs = format_json.get("signatures");
            if (sigs && sigs->type == JsonValue::ARRAY) {
                for (const auto& sig_json : sigs->array_elements) {
                    if (sig_json.type != JsonValue::OBJECT) continue;

                    FileSignature sig;
                    std::string magic = sig_json.get_string("magic");
                    sig.magic_bytes = hex_to_bytes(magic);
                    sig.offset = static_cast<uint16_t>(sig_json.get_number("offset", 0));
                    sig.base_confidence = static_cast<float>(sig_json.get_number("confidence", 0.9));

                    // Parse mask if present
                    std::string mask_str = sig_json.get_string("mask");
                    if (!mask_str.empty()) {
                        sig.mask = hex_to_bytes(mask_str);
                    } else {
                        // Default mask: all bytes must match
                        sig.mask.assign(sig.magic_bytes.size(), 0xFF);
                    }

                    format.signatures.push_back(sig);
                }
            }

            // Parse footer if present
            auto* footer_json = format_json.get("footer");
            if (footer_json && footer_json->type == JsonValue::OBJECT) {
                FooterSignature footer;
                std::string magic = footer_json->get_string("magic");
                footer.magic_bytes = hex_to_bytes(magic);
                footer.required = footer_json->get_bool("required", false);
                format.footer = footer;
            }

            add_format(format);
        }

        return true;
    } catch (const std::exception&) {
        return false;
    }
}

void SignatureDictionary::add_format(const FormatDefinition& format) {
    FormatDefinition fmt = format;
    if (fmt.format_id == 0) {
        fmt.format_id = next_format_id_++;
    }

    size_t index = formats_.size();
    formats_.push_back(fmt);

    std::string normalized = normalize_name(fmt.format_name);
    name_index_[normalized] = index;
    id_index_[fmt.format_id] = index;
}

const FormatDefinition* SignatureDictionary::get_format_by_name(const std::string& name) const {
    std::string normalized = normalize_name(name);
    auto it = name_index_.find(normalized);
    if (it != name_index_.end()) {
        return &formats_[it->second];
    }
    return nullptr;
}

const FormatDefinition* SignatureDictionary::get_format_by_id(uint16_t id) const {
    auto it = id_index_.find(id);
    if (it != id_index_.end()) {
        return &formats_[it->second];
    }
    return nullptr;
}

void SignatureDictionary::clear() {
    formats_.clear();
    name_index_.clear();
    id_index_.clear();
    next_format_id_ = 1;
}

// SignatureMatcher implementation

SignatureMatcher::SignatureMatcher(const SignatureDictionary& dictionary)
    : dictionary_(dictionary) {}

bool SignatureMatcher::check_signature_at(const uint8_t* data, size_t length,
                                          const FileSignature& sig, size_t position) const {
    size_t sig_start = position + sig.offset;
    if (sig_start + sig.magic_bytes.size() > length) {
        return false;
    }

    for (size_t i = 0; i < sig.magic_bytes.size(); i++) {
        uint8_t mask = (i < sig.mask.size()) ? sig.mask[i] : 0xFF;
        if ((data[sig_start + i] & mask) != (sig.magic_bytes[i] & mask)) {
            return false;
        }
    }
    return true;
}

bool SignatureMatcher::check_footer(const uint8_t* data, size_t length,
                                    const FooterSignature& footer) const {
    if (footer.magic_bytes.empty() || length < footer.magic_bytes.size()) {
        return false;
    }

    size_t footer_start = length - footer.magic_bytes.size();
    for (size_t i = 0; i < footer.magic_bytes.size(); i++) {
        if (data[footer_start + i] != footer.magic_bytes[i]) {
            return false;
        }
    }
    return true;
}

float SignatureMatcher::calculate_confidence(const FileSignature& sig, bool header_matched,
                                             bool footer_matched, bool footer_required) const {
    if (!header_matched) {
        return 0.0f;
    }

    float confidence = sig.base_confidence;

    if (footer_required) {
        if (footer_matched) {
            // Both header and footer matched - boost confidence
            confidence = std::min(1.0f, confidence + 0.05f);
        } else {
            // Footer required but not found - reduce confidence
            confidence *= 0.7f;
        }
    } else if (footer_matched) {
        // Footer not required but found - slight boost
        confidence = std::min(1.0f, confidence + 0.03f);
    }

    return confidence;
}

SignatureMatch SignatureMatcher::match(const uint8_t* data, size_t length, size_t max_offset) const {
    SignatureMatch best_match;

    for (const auto& format : dictionary_.get_formats()) {
        for (const auto& sig : format.signatures) {
            // Sliding window search up to max_offset
            size_t search_limit = std::min(max_offset, length);
            for (size_t offset = 0; offset <= search_limit; offset++) {
                if (check_signature_at(data, length, sig, offset)) {
                    bool header_matched = true;
                    bool footer_matched = false;
                    bool footer_required = false;

                    if (format.footer.has_value()) {
                        footer_required = format.footer->required;
                        footer_matched = check_footer(data, length, *format.footer);
                    }

                    float confidence = calculate_confidence(sig, header_matched, 
                                                           footer_matched, footer_required);

                    if (confidence > best_match.confidence) {
                        best_match.matched = true;
                        best_match.format_name = format.format_name;
                        best_match.category = format.category;
                        best_match.format_id = format.format_id;
                        best_match.confidence = confidence;
                        best_match.match_offset = static_cast<uint32_t>(offset + sig.offset);
                        best_match.header_matched = header_matched;
                        best_match.footer_matched = footer_matched;
                    }

                    // Found match at this offset, no need to continue sliding
                    break;
                }
            }
        }
    }

    return best_match;
}

SignatureMatch SignatureMatcher::match(const std::vector<uint8_t>& data, size_t max_offset) const {
    return match(data.data(), data.size(), max_offset);
}

SignatureMatch SignatureMatcher::match_format(const uint8_t* data, size_t length,
                                              const std::string& format_name) const {
    SignatureMatch result;
    const FormatDefinition* format = dictionary_.get_format_by_name(format_name);
    if (!format) {
        return result;
    }

    for (const auto& sig : format->signatures) {
        if (check_signature_at(data, length, sig, 0)) {
            bool footer_matched = false;
            bool footer_required = false;

            if (format->footer.has_value()) {
                footer_required = format->footer->required;
                footer_matched = check_footer(data, length, *format->footer);
            }

            float confidence = calculate_confidence(sig, true, footer_matched, footer_required);

            result.matched = true;
            result.format_name = format->format_name;
            result.category = format->category;
            result.format_id = format->format_id;
            result.confidence = confidence;
            result.match_offset = sig.offset;
            result.header_matched = true;
            result.footer_matched = footer_matched;
            return result;
        }
    }

    return result;
}

} // namespace etb
