#include "etb/path_generator.hpp"

namespace etb {

PathGenerator::PathGenerator(uint32_t input_length)
    : PathGenerator(PathGeneratorConfig(input_length))
{}

PathGenerator::PathGenerator(const PathGeneratorConfig& config)
    : config_(config)
    , paths_generated_(0)
    , exhausted_(false)
    , first_call_(true)
{
    if (config_.max_path_length == 0) {
        config_.max_path_length = config_.input_length;
    }
}

bool PathGenerator::is_bit_allowed(uint8_t bit_pos) const {
    return (config_.bit_mask & (1 << bit_pos)) != 0;
}

int PathGenerator::next_allowed_bit(uint8_t start_pos) const {
    for (uint8_t pos = start_pos; pos <= 7; ++pos) {
        if (is_bit_allowed(pos)) {
            return pos;
        }
    }
    return -1;  // No allowed bit found
}

void PathGenerator::initialize_stack() {
    // Clear any existing state
    while (!stack_.empty()) stack_.pop();
    current_path_.clear();
    
    // Find first allowed bit position
    int first_bit = next_allowed_bit(0);
    if (first_bit < 0 || config_.starting_byte_index >= config_.input_length) {
        exhausted_ = true;
        return;
    }
    
    // Push the first coordinate onto the stack
    stack_.push({config_.starting_byte_index, static_cast<uint8_t>(first_bit), false});
}

bool PathGenerator::has_next() const {
    if (first_call_) {
        return config_.input_length > 0 && config_.starting_byte_index < config_.input_length;
    }
    return !exhausted_;
}

std::optional<Path> PathGenerator::next() {
    if (first_call_) {
        first_call_ = false;
        initialize_stack();
        if (exhausted_) {
            return std::nullopt;
        }
    }
    
    while (!stack_.empty()) {
        StackFrame& top = stack_.top();
        
        // If we haven't explored this node yet, yield a path ending here
        if (!top.explored) {
            top.explored = true;
            
            // Build the current path from stack
            current_path_.clear();
            std::vector<StackFrame> frames;
            
            // Copy stack to vector for iteration
            std::stack<StackFrame> temp_stack = stack_;
            while (!temp_stack.empty()) {
                frames.push_back(temp_stack.top());
                temp_stack.pop();
            }
            
            // Build path in correct order (bottom to top of stack)
            for (auto it = frames.rbegin(); it != frames.rend(); ++it) {
                current_path_.add(BitCoordinate(it->byte_index, it->bit_position));
            }
            
            paths_generated_++;
            
            // Try to go deeper if we haven't reached max depth
            if (current_path_.length() < config_.max_path_length) {
                uint32_t next_byte = top.byte_index + 1;
                if (next_byte < config_.input_length) {
                    int first_bit = next_allowed_bit(0);
                    if (first_bit >= 0) {
                        stack_.push({next_byte, static_cast<uint8_t>(first_bit), false});
                    }
                }
            }
            
            return current_path_;
        }
        
        // Try next bit position at current byte
        int next_bit = next_allowed_bit(top.bit_position + 1);
        if (next_bit >= 0) {
            top.bit_position = static_cast<uint8_t>(next_bit);
            top.explored = false;
            continue;
        }
        
        // No more bits at this byte, try next byte at same depth
        uint32_t next_byte = top.byte_index + 1;
        
        // Calculate the minimum byte index we need (must be > previous in path)
        uint32_t min_byte = config_.starting_byte_index;
        if (stack_.size() > 1) {
            // Get the byte index of the parent
            StackFrame current = stack_.top();
            stack_.pop();
            if (!stack_.empty()) {
                min_byte = stack_.top().byte_index + 1;
            }
            stack_.push(current);
        }
        
        if (next_byte < config_.input_length && next_byte >= min_byte) {
            int first_bit = next_allowed_bit(0);
            if (first_bit >= 0) {
                top.byte_index = next_byte;
                top.bit_position = static_cast<uint8_t>(first_bit);
                top.explored = false;
                continue;
            }
        }
        
        // Backtrack
        stack_.pop();
    }
    
    exhausted_ = true;
    return std::nullopt;
}

void PathGenerator::reset() {
    while (!stack_.empty()) stack_.pop();
    current_path_.clear();
    paths_generated_ = 0;
    exhausted_ = false;
    first_call_ = true;
}

// PathIterator implementation
PathIterator::PathIterator(PathGenerator* gen) : generator_(gen) {
    if (generator_ && generator_->has_next()) {
        current_path_ = generator_->next();
    }
}

PathIterator& PathIterator::operator++() {
    if (generator_ && generator_->has_next()) {
        current_path_ = generator_->next();
    } else {
        current_path_ = std::nullopt;
    }
    return *this;
}

PathIterator PathIterator::operator++(int) {
    PathIterator tmp = *this;
    ++(*this);
    return tmp;
}

bool PathIterator::operator==(const PathIterator& other) const {
    // Both are end iterators
    if (!current_path_.has_value() && !other.current_path_.has_value()) {
        return true;
    }
    // One is end, one is not
    if (current_path_.has_value() != other.current_path_.has_value()) {
        return false;
    }
    // Both have values - compare generators
    return generator_ == other.generator_;
}

} // namespace etb
