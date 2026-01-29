#include "../../include/protocol/abstract_protocol.hpp"

// Fix for python implementation
AbstractProtocol::~AbstractProtocol() = default;

std::vector<uint8_t> AbstractProtocol::construct_packet(const std::vector<uint8_t>& data) {
    std::vector<uint8_t> crcDataBuffer;
    
    // -- Calc CRC (little endian)
    uint16_t crc = calculate_crc(data);
    uint8_t highByte = (crc >> 8) & 0xFF;
    uint8_t lowByte = crc & 0xFF;

    crcDataBuffer.emplace_back(lowByte);
    crcDataBuffer.emplace_back(highByte);
    
    // Copy in data
    crcDataBuffer.insert(crcDataBuffer.end(), data.begin(), data.end());

    // -- Encode in COBS
    std::vector<uint8_t> packet = cobs_encode(crcDataBuffer);

    // Resize to actual encoded size
    return packet;
}

std::pair<uint8_t, std::vector<uint8_t>> AbstractProtocol::deconstruct_packet(const std::vector<uint8_t>& packet) {
    if (packet.empty()) {
        throw ProtocolError("Protocol: Packet size before COBS decoding is not big enough.");
    }

    // -- Decode COBS
    std::vector<uint8_t> headerAndData = cobs_decode(packet);

    // -- Check CRC (little endian)
    if (headerAndData.size() < CRC_SIZE) {
        throw ProtocolError("Protocol: Packet size after COBS decoding is not big enough to contain data.");
    }

    uint16_t crc = static_cast<uint16_t>(headerAndData[1] << 8) | headerAndData[0];

    // Remove CRC from data
    std::shift_left(headerAndData.begin(), headerAndData.end(), CRC_SIZE);
    headerAndData.resize(headerAndData.size() - CRC_SIZE);

    bool crcCheckResult = check_crc(crc, headerAndData);
    if (!crcCheckResult) {
        throw EncodingError("CRC: CRC failed check failed.");
    }

    // Seperate header and data
    uint8_t header = headerAndData[0];
    std::vector<uint8_t> data(headerAndData.begin() + 1, headerAndData.end());

    return {header, data};
}

std::vector<uint8_t> AbstractProtocol::create_rejection_packet() {
    std::vector<uint8_t> data = {
        static_cast<uint8_t>(Protocol::OutgoingHeader::General::MalformedPacketNotification)
    };

    return construct_packet(data);
}