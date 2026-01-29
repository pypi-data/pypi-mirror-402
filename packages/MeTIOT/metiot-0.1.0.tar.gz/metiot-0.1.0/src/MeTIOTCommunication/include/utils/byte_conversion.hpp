#ifndef BYTE_CONVERSION_HPP
#define BYTE_CONVERSION_HPP

#include <cstdint>
#include <vector>
#include <cstring>
#include <algorithm>

int8_t bytes_to_int8(const std::vector<uint8_t>& data, int currentPlace);

uint8_t bytes_to_uint8(const std::vector<uint8_t>& data, int currentPlace);

int16_t bytes_to_int16(const std::vector<uint8_t>& data, int currentPlace);

uint16_t bytes_to_uint16(const std::vector<uint8_t>& data, int currentPlace);

int32_t bytes_to_int32(const std::vector<uint8_t>& data, int currentPlace);

uint32_t bytes_to_uint32(const std::vector<uint8_t>& data, int currentPlace);

int64_t bytes_to_int64(const std::vector<uint8_t>& data, int currentPlace);

uint64_t bytes_to_uint64(const std::vector<uint8_t>& data, int currentPlace);

float bytes_to_float(const std::vector<uint8_t>& data, int currentPlace);

double bytes_to_double(const std::vector<uint8_t>& data, int currentPlace);

#endif