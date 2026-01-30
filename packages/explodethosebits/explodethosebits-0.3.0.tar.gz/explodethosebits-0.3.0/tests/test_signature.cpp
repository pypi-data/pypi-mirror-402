#include <gtest/gtest.h>
#include "etb/signature.hpp"
#include <vector>
#include <cstdint>

using namespace etb;

class SignatureDictionaryTest : public ::testing::Test {
protected:
    SignatureDictionary dict;

    const std::string sample_json = R"({
        "version": "1.0",
        "signatures": [
            {
                "format": "PNG",
                "category": "image",
                "signatures": [
                    {"magic": "89504E470D0A1A0A", "offset": 0, "confidence": 0.95}
                ],
                "footer": {
                    "magic": "49454E44AE426082",
                    "required": false
                }
            },
            {
                "format": "JPEG",
                "category": "image",
                "signatures": [
                    {"magic": "FFD8FFE0", "offset": 0, "confidence": 0.90}
                ],
                "footer": {
                    "magic": "FFD9",
                    "required": true
                }
            }
        ]
    })";
};

TEST_F(SignatureDictionaryTest, LoadFromJsonString) {
    EXPECT_TRUE(dict.load_from_json_string(sample_json));
    EXPECT_EQ(dict.format_count(), 2);
}

TEST_F(SignatureDictionaryTest, GetFormatByName) {
    dict.load_from_json_string(sample_json);
    
    const FormatDefinition* png = dict.get_format_by_name("PNG");
    ASSERT_NE(png, nullptr);
    EXPECT_EQ(png->format_name, "PNG");
    EXPECT_EQ(png->category, "image");
    
    // Case insensitive lookup
    const FormatDefinition* png_lower = dict.get_format_by_name("png");
    ASSERT_NE(png_lower, nullptr);
    EXPECT_EQ(png_lower->format_name, "PNG");
}

TEST_F(SignatureDictionaryTest, GetFormatById) {
    dict.load_from_json_string(sample_json);
    
    const FormatDefinition* format = dict.get_format_by_id(1);
    ASSERT_NE(format, nullptr);
    EXPECT_EQ(format->format_name, "PNG");
}

TEST_F(SignatureDictionaryTest, AddFormatProgrammatically) {
    FormatDefinition format;
    format.format_name = "TEST";
    format.category = "test";
    
    FileSignature sig;
    sig.magic_bytes = {0x54, 0x45, 0x53, 0x54}; // "TEST"
    sig.mask = {0xFF, 0xFF, 0xFF, 0xFF};
    sig.offset = 0;
    sig.base_confidence = 0.9f;
    format.signatures.push_back(sig);
    
    dict.add_format(format);
    
    EXPECT_EQ(dict.format_count(), 1);
    const FormatDefinition* retrieved = dict.get_format_by_name("TEST");
    ASSERT_NE(retrieved, nullptr);
    EXPECT_EQ(retrieved->signatures.size(), 1);
}

TEST_F(SignatureDictionaryTest, ClearDictionary) {
    dict.load_from_json_string(sample_json);
    EXPECT_FALSE(dict.empty());
    
    dict.clear();
    EXPECT_TRUE(dict.empty());
    EXPECT_EQ(dict.format_count(), 0);
}

TEST_F(SignatureDictionaryTest, InvalidJsonReturnsFailure) {
    EXPECT_FALSE(dict.load_from_json_string("not valid json"));
    EXPECT_FALSE(dict.load_from_json_string("{}"));  // Missing signatures array
}

class SignatureMatcherTest : public ::testing::Test {
protected:
    SignatureDictionary dict;

    void SetUp() override {
        const std::string json = R"({
            "version": "1.0",
            "signatures": [
                {
                    "format": "PNG",
                    "category": "image",
                    "signatures": [
                        {"magic": "89504E470D0A1A0A", "offset": 0, "confidence": 0.95}
                    ],
                    "footer": {
                        "magic": "49454E44AE426082",
                        "required": false
                    }
                },
                {
                    "format": "JPEG",
                    "category": "image",
                    "signatures": [
                        {"magic": "FFD8FFE0", "offset": 0, "confidence": 0.90}
                    ],
                    "footer": {
                        "magic": "FFD9",
                        "required": true
                    }
                },
                {
                    "format": "MP4",
                    "category": "video",
                    "signatures": [
                        {"magic": "66747970", "offset": 4, "confidence": 0.85}
                    ]
                }
            ]
        })";
        dict.load_from_json_string(json);
    }
};

TEST_F(SignatureMatcherTest, MatchPngHeader) {
    SignatureMatcher matcher(dict);
    
    // PNG header bytes
    std::vector<uint8_t> png_data = {0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 
                                      0x00, 0x00, 0x00, 0x00};
    
    SignatureMatch result = matcher.match(png_data);
    
    EXPECT_TRUE(result.matched);
    EXPECT_EQ(result.format_name, "PNG");
    EXPECT_EQ(result.category, "image");
    EXPECT_TRUE(result.header_matched);
    EXPECT_GT(result.confidence, 0.9f);
}

TEST_F(SignatureMatcherTest, MatchPngWithFooter) {
    SignatureMatcher matcher(dict);
    
    // PNG header + some data + PNG footer (IEND chunk)
    std::vector<uint8_t> png_data = {
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  // PNG header
        0x00, 0x00, 0x00, 0x00,                          // Some data
        0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82   // IEND footer
    };
    
    SignatureMatch result = matcher.match(png_data);
    
    EXPECT_TRUE(result.matched);
    EXPECT_EQ(result.format_name, "PNG");
    EXPECT_TRUE(result.header_matched);
    EXPECT_TRUE(result.footer_matched);
    // Footer match should boost confidence
    EXPECT_GT(result.confidence, 0.95f);
}

TEST_F(SignatureMatcherTest, MatchJpegHeaderOnly) {
    SignatureMatcher matcher(dict);
    
    // JPEG header without footer
    std::vector<uint8_t> jpeg_data = {0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10};
    
    SignatureMatch result = matcher.match(jpeg_data);
    
    EXPECT_TRUE(result.matched);
    EXPECT_EQ(result.format_name, "JPEG");
    EXPECT_TRUE(result.header_matched);
    EXPECT_FALSE(result.footer_matched);
    // JPEG requires footer, so confidence should be reduced
    EXPECT_LT(result.confidence, 0.90f);
}

TEST_F(SignatureMatcherTest, MatchJpegWithFooter) {
    SignatureMatcher matcher(dict);
    
    // JPEG header + data + footer
    std::vector<uint8_t> jpeg_data = {
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10,  // JPEG header
        0x00, 0x00, 0x00, 0x00,              // Some data
        0xFF, 0xD9                           // JPEG footer
    };
    
    SignatureMatch result = matcher.match(jpeg_data);
    
    EXPECT_TRUE(result.matched);
    EXPECT_EQ(result.format_name, "JPEG");
    EXPECT_TRUE(result.header_matched);
    EXPECT_TRUE(result.footer_matched);
    EXPECT_GE(result.confidence, 0.90f);
}

TEST_F(SignatureMatcherTest, MatchWithOffset) {
    SignatureMatcher matcher(dict);
    
    // MP4 has signature at offset 4 ("ftyp")
    std::vector<uint8_t> mp4_data = {
        0x00, 0x00, 0x00, 0x18,              // Size field (4 bytes)
        0x66, 0x74, 0x79, 0x70,              // "ftyp" at offset 4
        0x6D, 0x70, 0x34, 0x32               // "mp42"
    };
    
    SignatureMatch result = matcher.match(mp4_data);
    
    EXPECT_TRUE(result.matched);
    EXPECT_EQ(result.format_name, "MP4");
    EXPECT_EQ(result.match_offset, 4u);
}

TEST_F(SignatureMatcherTest, NoMatchForUnknownFormat) {
    SignatureMatcher matcher(dict);
    
    std::vector<uint8_t> unknown_data = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05};
    
    SignatureMatch result = matcher.match(unknown_data);
    
    EXPECT_FALSE(result.matched);
    EXPECT_EQ(result.confidence, 0.0f);
}

TEST_F(SignatureMatcherTest, SlidingWindowMatch) {
    SignatureMatcher matcher(dict);
    
    // PNG header with some garbage bytes before it
    std::vector<uint8_t> data = {
        0x00, 0x00, 0x00,                                // Garbage
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  // PNG header at offset 3
        0x00, 0x00
    };
    
    SignatureMatch result = matcher.match(data, 10);  // Search up to offset 10
    
    EXPECT_TRUE(result.matched);
    EXPECT_EQ(result.format_name, "PNG");
    EXPECT_EQ(result.match_offset, 3u);
}

TEST_F(SignatureMatcherTest, MatchSpecificFormat) {
    SignatureMatcher matcher(dict);
    
    std::vector<uint8_t> png_data = {0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A};
    
    SignatureMatch result = matcher.match_format(png_data.data(), png_data.size(), "PNG");
    
    EXPECT_TRUE(result.matched);
    EXPECT_EQ(result.format_name, "PNG");
}

TEST_F(SignatureMatcherTest, MatchSpecificFormatNotFound) {
    SignatureMatcher matcher(dict);
    
    std::vector<uint8_t> png_data = {0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A};
    
    // Try to match as JPEG - should fail
    SignatureMatch result = matcher.match_format(png_data.data(), png_data.size(), "JPEG");
    
    EXPECT_FALSE(result.matched);
}

TEST_F(SignatureMatcherTest, EmptyDataNoMatch) {
    SignatureMatcher matcher(dict);
    
    std::vector<uint8_t> empty_data;
    
    SignatureMatch result = matcher.match(empty_data);
    
    EXPECT_FALSE(result.matched);
}

TEST_F(SignatureMatcherTest, DataTooShortNoMatch) {
    SignatureMatcher matcher(dict);
    
    // PNG header is 8 bytes, provide only 4
    std::vector<uint8_t> short_data = {0x89, 0x50, 0x4E, 0x47};
    
    SignatureMatch result = matcher.match(short_data);
    
    EXPECT_FALSE(result.matched);
}

TEST_F(SignatureMatcherTest, ConfidenceInRange) {
    SignatureMatcher matcher(dict);
    
    std::vector<uint8_t> png_data = {0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A};
    
    SignatureMatch result = matcher.match(png_data);
    
    EXPECT_GE(result.confidence, 0.0f);
    EXPECT_LE(result.confidence, 1.0f);
}
