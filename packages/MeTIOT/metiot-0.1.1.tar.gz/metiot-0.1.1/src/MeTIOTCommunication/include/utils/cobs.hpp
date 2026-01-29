#ifndef COBS_HPP
#define COBS_HPP

#include <vector>
#include <cstdint>
#include <iostream>

#include "../core/exceptions.hpp"

/* @brief    Encodes the data using COBS
 *
 * @param    data      Data that is being encoded
 * 
 * @retval   Encoded buffer
 */
std::vector<uint8_t> cobs_encode(const std::vector<uint8_t>& data);

/* @brief    Decodes the data using COBS
 *
 * @param    buffer     The encoded data buffer
 * 
 * @retval   Decoded buffer
 */
std::vector<uint8_t> cobs_decode(const std::vector<uint8_t>& buffer);

#endif