# Fetch GoogleTest
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)

# Test executable
add_executable(etb_tests
    test_bit_coordinate.cpp
    test_path.cpp
    test_bit_extraction.cpp
    test_path_generator.cpp
    test_path_count.cpp
    test_signature.cpp
    test_heuristics.cpp
    test_early_stopping.cpp
    test_prefix_trie.cpp
    test_memoization.cpp
    test_bit_pruning.cpp
    test_scoring.cpp
    test_config.cpp
    test_reporting.cpp
)

target_link_libraries(etb_tests PRIVATE
    etb_core
    GTest::gtest_main
)

include(GoogleTest)
gtest_discover_tests(etb_tests)
