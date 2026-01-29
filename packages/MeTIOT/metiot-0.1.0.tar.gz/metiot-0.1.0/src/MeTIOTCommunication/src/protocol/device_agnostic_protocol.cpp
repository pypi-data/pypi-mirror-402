#include "../../include/protocol/device_agnostic_protocol.hpp"

std::vector<uint8_t> DeviceAgnosticProtocol::create_device_id_request() {
    std::vector<uint8_t> data = {
        static_cast<uint8_t>(Protocol::OutgoingHeader::General::DeviceIdentificationRequest)
    };

    return construct_packet(data);
}

std::pair<uint8_t, uint64_t> DeviceAgnosticProtocol::extract_device_details(const std::vector<uint8_t>& data) {
    if (data.size() != 9) {
        throw ProtocolError("Protocol: Data is not correct size to contain device details");
    }

    uint8_t deviceType = data[0];

    uint64_t deviceID;
    std::memcpy(&deviceID, &data[1], sizeof(uint64_t));

    return {deviceType, deviceID};
}