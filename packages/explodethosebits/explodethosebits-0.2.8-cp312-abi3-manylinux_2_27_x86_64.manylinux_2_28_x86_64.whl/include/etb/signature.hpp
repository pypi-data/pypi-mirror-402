#ifndef ETB_SIGNATURE_HPP
#define ETB_SIGNATURE_HPP

#include <cstdint>
#include <string>
#include <vector>
#include <optional>
#include <unordered_map>

namespace etb {

/**
 * Represents a single file signature (magic bytes).
 */
struct FileSignature {
    std::vector<uint8_t> magic_bytes;   // Magic byte sequence
    std::vector<uint8_t> mask;          // Mask for partial matches (0xFF = must match)
    uint16_t offset;                    // Offset from start where signature appears
    float base_confidence;              // Base confidence for this signature [0.0, 1.0]

    FileSignature() : offset(0), base_confidence(0.9f) {}
};

/**
 * Represents a footer/trailer signature for a format.
 */
struct FooterSignature {
    std::vector<uint8_t> magic_bytes;   // Footer magic bytes
    bool required;                      // Whether footer is required for full confidence

    FooterSignature() : required(false) {}
};

/**
 * Represents a complete format definition with all its signatures.
 */
struct FormatDefinition {
    std::string format_name;            // e.g., "PNG", "JPEG"
    std::string category;               // e.g., "image", "archive", "executable"
    std::vector<FileSignature> signatures;  // Multiple signatures for same format
    std::optional<FooterSignature> footer;  // Optional footer signature
    uint16_t format_id;                 // Unique format identifier

    FormatDefinition() : format_id(0) {}
};

/**
 * Result of a signature match operation.
 */
struct SignatureMatch {
    bool matched;                       // Whether a match was found
    std::string format_name;            // Matched format name
    std::string category;               // Format category
    uint16_t format_id;                 // Format identifier
    float confidence;                   // Match confidence [0.0, 1.0]
    uint32_t match_offset;              // Offset where match was found
    bool header_matched;                // Whether header was matched
    bool footer_matched;                // Whether footer was matched

    SignatureMatch() 
        : matched(false), format_id(0), confidence(0.0f), 
          match_offset(0), header_matched(false), footer_matched(false) {}
};

/**
 * Signature dictionary that loads and manages file signatures.
 * Supports JSON format for signature definitions.
 */
class SignatureDictionary {
public:
    SignatureDictionary() = default;

    /**
     * Load signatures from a JSON file.
     * @param filepath Path to the JSON signature file
     * @return true if loaded successfully
     */
    bool load_from_json(const std::string& filepath);

    /**
     * Load signatures from a JSON string.
     * @param json_content JSON content as string
     * @return true if parsed successfully
     */
    bool load_from_json_string(const std::string& json_content);

    /**
     * Add a format definition programmatically.
     * @param format The format definition to add
     */
    void add_format(const FormatDefinition& format);

    /**
     * Get all loaded format definitions.
     */
    const std::vector<FormatDefinition>& get_formats() const { return formats_; }

    /**
     * Get format by name.
     * @param name Format name (case-insensitive)
     * @return Pointer to format or nullptr if not found
     */
    const FormatDefinition* get_format_by_name(const std::string& name) const;

    /**
     * Get format by ID.
     * @param id Format ID
     * @return Pointer to format or nullptr if not found
     */
    const FormatDefinition* get_format_by_id(uint16_t id) const;

    /**
     * Get the number of loaded formats.
     */
    size_t format_count() const { return formats_.size(); }

    /**
     * Clear all loaded signatures.
     */
    void clear();

    /**
     * Check if dictionary is empty.
     */
    bool empty() const { return formats_.empty(); }

private:
    std::vector<FormatDefinition> formats_;
    std::unordered_map<std::string, size_t> name_index_;  // name -> index in formats_
    std::unordered_map<uint16_t, size_t> id_index_;       // id -> index in formats_
    uint16_t next_format_id_ = 1;

    // Helper to parse hex string to bytes
    static std::vector<uint8_t> hex_to_bytes(const std::string& hex);
    
    // Helper to normalize format name for lookup
    static std::string normalize_name(const std::string& name);
};

/**
 * Signature matcher that performs header and footer detection.
 */
class SignatureMatcher {
public:
    explicit SignatureMatcher(const SignatureDictionary& dictionary);

    /**
     * Match signatures against a byte sequence.
     * Performs sliding window header matching and footer detection.
     * @param data Byte sequence to analyze
     * @param length Length of the byte sequence
     * @param max_offset Maximum offset to search for headers (default: 512)
     * @return Best signature match found
     */
    SignatureMatch match(const uint8_t* data, size_t length, size_t max_offset = 512) const;

    /**
     * Match signatures against a vector of bytes.
     */
    SignatureMatch match(const std::vector<uint8_t>& data, size_t max_offset = 512) const;

    /**
     * Check if data matches a specific format's header.
     * @param data Byte sequence
     * @param length Data length
     * @param format_name Format to check
     * @return Match result for the specific format
     */
    SignatureMatch match_format(const uint8_t* data, size_t length, 
                                const std::string& format_name) const;

private:
    const SignatureDictionary& dictionary_;

    // Check if signature matches at given position
    bool check_signature_at(const uint8_t* data, size_t length, 
                           const FileSignature& sig, size_t position) const;

    // Check if footer matches at end of data
    bool check_footer(const uint8_t* data, size_t length, 
                     const FooterSignature& footer) const;

    // Calculate confidence based on match quality
    float calculate_confidence(const FileSignature& sig, bool header_matched, 
                              bool footer_matched, bool footer_required) const;
};

} // namespace etb

#endif // ETB_SIGNATURE_HPP
