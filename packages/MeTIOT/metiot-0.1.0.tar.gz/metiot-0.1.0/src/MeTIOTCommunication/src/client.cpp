#include "../include/client.hpp"

void DeviceClient::listen_loop() {
    uint8_t warningCount = 0;

    while (true) {
        try {
            std::vector<uint8_t> packet = socketCore.recv_data(); // * This throws the fatal errors

            std::pair<uint8_t, std::vector<uint8_t>> data = protocolHandler->deconstruct_packet(packet); // * This throws the warning errors

            callbackHandler->handle_message(this, data.first, data.second);
            warningCount = 0; // Reset warning count after a single successful recv
        } catch (const SocketError& e) { // Catch specific fatal first
            // Fatal error & kill thread
            callbackHandler->handle_fatal_error(this, e.what());
            return;
        } catch (const LibraryError& e) { // Catch rest of error types (non fatal) including Protocol & Encoding
            warningCount += 1;

            if (warningCount >= FATAL_WARNING_THRESHOLD) {
                callbackHandler->handle_fatal_error(this, e.what());
                return;
            }

            // Notify python dev via callback
            callbackHandler->handle_warning(this, e.what());

            // Send a packet reject to client
            std::vector<uint8_t> packet = protocolHandler->create_rejection_packet();

            try {
                send_packet(packet);
            } catch (const SocketError& e) {
                // Fatal Error. Stop thread
                callbackHandler->handle_fatal_error(this, e.what());
                return;
            }
        } catch (const std::exception& e) {
            callbackHandler->handle_fatal_error(this, "Unexpected System Error: " + std::string(e.what()));
            return;
        }
    }
}

void DeviceClient::connect() {
    // Connect to device
    int ret = socketCore.connect_device();
    if (ret != 0) {
        throw SocketError("Socket: Failed to connect to device");
    }

    // Complete Device initialization
    perform_device_initialization(); // * Throws errors if fail
}

void DeviceClient::disconnect() {
    socketCore.disconnect();
}

void DeviceClient::assign_receive_handler(std::shared_ptr<IEventHandler> handler) {
    callbackHandler = std::move(handler);
}

void DeviceClient::start_listening() {
    if (!callbackHandler) {
        throw LogicError("Logic: You must first define a callbackHandler");
    }

    std::thread t(&DeviceClient::listen_loop, this);
    t.detach();
}

void DeviceClient::send_packet(const std::vector<uint8_t>& packet) {
    int bytesSent = socketCore.send_data(packet);
    if (bytesSent == -1) {
        throw SocketError("Socket: Error occured when sending packet.");
    } else if (bytesSent != packet.size()) {
        throw SocketError("Socket: Failed to send all bytes when sending packet.");
    }
}

uint64_t DeviceClient::get_unique_id() {
    return uniqueDeviceID;
}

bool DeviceClient::assign_device_protocol(uint8_t deviceID) {
    switch(deviceID) {
        case (static_cast<uint8_t>(Protocol::DeviceIdentifier::FishTank)): {
            deviceType = DeviceType::FISH_TANK;
            protocolHandler = std::make_unique<FishTankProtocol>();

            return true;
        }
        default: {
            DeviceType::UNKNOWN;

            return false;
        }
    }
}

AbstractProtocol* DeviceClient::get_protocol_handler() const { 
    if (initialized) {
        return protocolHandler.get(); 
    }
    throw LogicError("Logic: Device has not been initialized");
}

DeviceType DeviceClient::get_device_type() const { 
    if (initialized) {
        return deviceType;
    }
    throw LogicError("Logic: Device has not been initialized");
}

void DeviceClient::perform_device_initialization() {
    // -- Send device identification request
    // Create DeviceAgnosticProtocol
    DeviceAgnosticProtocol deviceAgnosticProtocol;

    // Create packet
    std::vector<uint8_t> idRequestPacket = deviceAgnosticProtocol.create_device_id_request();
    
    // Send data
    send_packet(idRequestPacket); // * This will throw error if failed to send

    // This loop guards against possible scenarios where the device happens to be scheduled
    // to first send a data packet before it sends the deviceIDResponse.
    uint8_t loopCount = 0;
    while (true) {
        // TODO: Time based fail condition
        loopCount += 1;

        if (loopCount >= WRONG_PACKET_DURING_INIT_THRESHOLD) {
            throw ProtocolError("Protocol: Device failed to send its ID");
        }

        // -- Recieve device data
        std::vector<uint8_t> idResponsePacket = socketCore.recv_data(); // * This will throw error if failed to recv

        // Decode
        std::pair<uint8_t, std::vector<uint8_t>> deconstructedIdResponsePacket = deviceAgnosticProtocol.deconstruct_packet(idResponsePacket);

        // Ensure it is the correct
        if (deconstructedIdResponsePacket.first == static_cast<uint8_t>(Protocol::IncomingHeader::General::DeviceIdentifier)) {
            // Extract device details
            std::pair<uint8_t, uint64_t> deviceDetails = deviceAgnosticProtocol.extract_device_details(deconstructedIdResponsePacket.second);
            
            // Assign specific protocol to protocolHandler
            bool success = assign_device_protocol(deviceDetails.first);
            if (!success) {
                std::cerr << "WARNING: Device type not recognised. Type \"UNKNOWN\" assigned." << std::endl;
            }

            // Save uniqueID
            uniqueDeviceID = deviceDetails.second;
            break;
        }
    }

    initialized = true;
}