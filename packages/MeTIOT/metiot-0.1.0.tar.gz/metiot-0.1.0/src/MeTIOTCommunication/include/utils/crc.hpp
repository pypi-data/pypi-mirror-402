#ifndef CRC_HPP
#define CRC_HPP

#include <vector>
#include <cstdint>

#define CRC_SIZE 2 // Bytes

/* @brief    Calculates 16-bit CRC using data
 *
 * @param    data         Data used to calculate the CRC
 * 
 * @retval   `uint16_t` - 16-bit CRC value
 *
 * @note     For specific polynomial used refer to documentation.
 */
uint16_t calculate_crc(const std::vector<uint8_t>& data);

/* @brief    Calculates CRC from data and compares the given the the calculated
 *
 * @param    crc   CRC received in message
 * @param    data  Data received in message
 * 
 * @retval   `true`  - CRC's match. Data is valid
 * @retval   `false` - CRC's DONT match. Data is invalid
 */
bool check_crc(const uint16_t crc, const std::vector<uint8_t>& data);

#endif