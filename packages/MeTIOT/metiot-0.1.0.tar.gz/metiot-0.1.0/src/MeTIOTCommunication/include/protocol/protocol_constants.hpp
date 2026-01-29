#ifndef PROTOCOL_CONSTANTS_HPP
#define PROTOCOL_CONSTANTS_HPP

#include <cstdint>

namespace Protocol {
    namespace OutgoingHeader {
        enum class General : uint8_t {
            MalformedPacketNotification = 0xFF,
            DeviceIdentificationRequest = 0xFE,
        };

        enum class FishTank : uint8_t {

        };
    }

    namespace IncomingHeader {
        enum class General : uint8_t {
            MalformedPacketNotification = 0xFF,
            DeviceIdentifier            = 0xFE,
            Data                        = 0xFD,
        };

        enum class FishTank : uint8_t {
        
        };
    }

    namespace DataSubHeader {
        enum class FishTank : uint8_t {
            Temperature                 = 0xFF,
            DataEnd                     = 0x00,
        };
    }

    enum class DeviceIdentifier : uint8_t {
        FishTank                    = 0xFF,
    };
}

#endif