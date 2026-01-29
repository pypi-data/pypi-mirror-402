#include "../../include/utils/crc.hpp"

uint16_t calculate_crc(const std::vector<uint8_t>& data) {
    uint16_t A, crc = 0;

    for (size_t i = 0; i < data.size(); i++) {
        A = (crc >> 8) ^ data[i];
        crc = (A << 2) ^ (A << 1) ^ A ^ (crc << 8);
    }

    return crc;
}

bool check_crc(const uint16_t crc, const std::vector<uint8_t>& data) {
    uint16_t calculatedCRC = calculate_crc(data);
    return calculatedCRC == crc;
}