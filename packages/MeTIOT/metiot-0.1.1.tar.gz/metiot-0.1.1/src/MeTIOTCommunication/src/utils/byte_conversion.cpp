#include "../../include/utils/byte_conversion.hpp"

int8_t bytes_to_int8(const std::vector<uint8_t>& data, int currentPlace) {
    return static_cast<int8_t>(data[currentPlace]);
}

uint8_t bytes_to_uint8(const std::vector<uint8_t>& data, int currentPlace) {
    return data[currentPlace];
}

int16_t bytes_to_int16(const std::vector<uint8_t>& data, int currentPlace) {
    uint16_t result = (static_cast<uint16_t>(data[currentPlace + 1]) << 8) | 
                       static_cast<uint16_t>(data[currentPlace]);
    return static_cast<int16_t>(result);
}

uint16_t bytes_to_uint16(const std::vector<uint8_t>& data, int currentPlace) {
    return (static_cast<uint16_t>(data[currentPlace + 1]) << 8) | 
           static_cast<uint16_t>(data[currentPlace]);
}

int32_t bytes_to_int32(const std::vector<uint8_t>& data, int currentPlace) {
    uint32_t result = (static_cast<uint32_t>(data[currentPlace + 3]) << 24) |
                      (static_cast<uint32_t>(data[currentPlace + 2]) << 16) |
                      (static_cast<uint32_t>(data[currentPlace + 1]) << 8)  |
                       static_cast<uint32_t>(data[currentPlace]);
    return static_cast<int32_t>(result);
}

uint32_t bytes_to_uint32(const std::vector<uint8_t>& data, int currentPlace) {
    return (static_cast<uint32_t>(data[currentPlace + 3]) << 24) |
           (static_cast<uint32_t>(data[currentPlace + 2]) << 16) |
           (static_cast<uint32_t>(data[currentPlace + 1]) << 8)  |
            static_cast<uint32_t>(data[currentPlace]);
}

int64_t bytes_to_int64(const std::vector<uint8_t>& data, int currentPlace) {
    uint64_t result = (static_cast<uint64_t>(data[currentPlace + 7]) << 56) |
                      (static_cast<uint64_t>(data[currentPlace + 6]) << 48) |
                      (static_cast<uint64_t>(data[currentPlace + 5]) << 40) |
                      (static_cast<uint64_t>(data[currentPlace + 4]) << 32) |
                      (static_cast<uint64_t>(data[currentPlace + 3]) << 24) |
                      (static_cast<uint64_t>(data[currentPlace + 2]) << 16) |
                      (static_cast<uint64_t>(data[currentPlace + 1]) << 8)  |
                       static_cast<uint64_t>(data[currentPlace]);
    return static_cast<int64_t>(result);
}

uint64_t bytes_to_uint64(const std::vector<uint8_t>& data, int currentPlace) {
    return (static_cast<uint64_t>(data[currentPlace + 7]) << 56) |
           (static_cast<uint64_t>(data[currentPlace + 6]) << 48) |
           (static_cast<uint64_t>(data[currentPlace + 5]) << 40) |
           (static_cast<uint64_t>(data[currentPlace + 4]) << 32) |
           (static_cast<uint64_t>(data[currentPlace + 3]) << 24) |
           (static_cast<uint64_t>(data[currentPlace + 2]) << 16) |
           (static_cast<uint64_t>(data[currentPlace + 1]) << 8)  |
            static_cast<uint64_t>(data[currentPlace]);
}

float bytes_to_float(const std::vector<uint8_t>& data, int currentPlace) {
    float result;
    
    // Create a temporary 4-byte array from the data in LE order
    uint8_t bytes[sizeof(float)];
    for (size_t i = 0; i < sizeof(float); ++i) {
        // LE means the vector is already in the correct order for memcpy
        bytes[i] = data[currentPlace + i];
    }
    
    // Copy the raw byte pattern into the float variable
    std::memcpy(&result, bytes, sizeof(float));
    return result;
}

double bytes_to_double(const std::vector<uint8_t>& data, int currentPlace) {
    double result;
    
    // Create a temporary 8-byte array from the data in LE order
    uint8_t bytes[sizeof(double)];
    for (size_t i = 0; i < sizeof(double); ++i) {
        // LE means the vector is already in the correct order for memcpy
        bytes[i] = data[currentPlace + i];
    }
    
    // Copy the raw byte pattern into the double variable
    std::memcpy(&result, bytes, sizeof(double));
    return result;
}