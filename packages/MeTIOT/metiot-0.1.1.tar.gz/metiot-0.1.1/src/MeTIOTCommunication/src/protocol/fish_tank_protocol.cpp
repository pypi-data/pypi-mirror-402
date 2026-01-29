#include "../../include/protocol/fish_tank_protocol.hpp"

std::map<std::string, ProtocolValue> FishTankProtocol::interpret_data(const std::vector<uint8_t>& data) {
    unsigned int currentPlace = 0;
    std::map<std::string, ProtocolValue> organisedData;
    
    if (data.empty()) {
        throw ProtocolError("Protocol: Data is empty.");
    }

    while (currentPlace < data.size()) {

        uint8_t subheader = data[currentPlace];
        currentPlace += 1; // Move past the subheader

        switch(static_cast<Protocol::DataSubHeader::FishTank>(subheader)) {
            case (Protocol::DataSubHeader::FishTank::Temperature): {
                // Verify theres enough space in data vector to contain this
                const size_t DATA_SIZE = 2; // Byte count of int16_t
                if (currentPlace + DATA_SIZE > data.size()) {
                    throw ProtocolError("Protocol: Not enough space left in data vector to read data defined in data sub header.");
                }

                // Call util to convert 2 byte array to int16_t
                int16_t rawTemp = bytes_to_int16(data, currentPlace);

                float tempC = rawTemp / 100.0;

                organisedData["Temperature_C"] = tempC;

                // Move pointer
                currentPlace += DATA_SIZE;
                break;
            }
            case (Protocol::DataSubHeader::FishTank::DataEnd): {
                // Data terminator found
                return organisedData;
            }
            default: {
                throw ProtocolError("Protocol: Unknown data sub header occured.");
            }
        }
    }
    
    // throw ProtocolError("Protocol: No end of data sub header was present in data."); // * No strictly required
    return organisedData;
}