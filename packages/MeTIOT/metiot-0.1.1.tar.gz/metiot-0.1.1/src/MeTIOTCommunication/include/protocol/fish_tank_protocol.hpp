#ifndef FISH_TANK_PROTOCOL_HPP
#define FISH_TANK_PROTOCOL_HPP

#include <string>
#include <vector>
#include <cstdint>

#include "abstract_protocol.hpp"
#include "../utils/byte_conversion.hpp"
#include "../core/exceptions.hpp"

class FishTankProtocol : public AbstractProtocol {
    public:
        std::map<std::string, ProtocolValue> interpret_data(const std::vector<uint8_t>& data) override;
        
        ~FishTankProtocol() override {}
};

#endif