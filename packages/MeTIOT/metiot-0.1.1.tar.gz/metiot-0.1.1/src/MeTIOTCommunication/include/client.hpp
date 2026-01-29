#ifndef CLIENT_HPP
#define CLIENT_HPP

#include <string>
#include <vector>
#include <cstdint>
#include <memory>
#include <thread>

#include "core/socket_core.hpp"
#include "protocol/abstract_protocol.hpp"
#include "protocol/device_agnostic_protocol.hpp"
#include "protocol/fish_tank_protocol.hpp"
#include "interfaces/event_handler.hpp"

#define FATAL_WARNING_THRESHOLD 10
#define WRONG_PACKET_DURING_INIT_THRESHOLD 5

enum class DeviceType {
  UNKNOWN,
  FISH_TANK,
};

class DeviceClient {
  private:
    SocketCore socketCore;
    std::unique_ptr<AbstractProtocol> protocolHandler;
    std::shared_ptr<IEventHandler> callbackHandler;
    DeviceType deviceType;
    uint64_t uniqueDeviceID;
    bool initialized = false;

    /* @brief   TCP Listening thread function
     */
    void listen_loop();

    /* @brief   Performs all initialization steps in the correct order
     *
     * @throws   ProtocolError
     * @throws   SocketError (Through functions it calls)
     */
    void perform_device_initialization();

    /* @brief   Assigns deviceType variable based on input
     *
     * @param   deviceID   1 byte device type received during device initialization
     */
    bool assign_device_protocol(uint8_t deviceID);

  public:
    DeviceClient(const std::string& ip, int port) : socketCore(ip, port) {}

    /* @brief    Connects socket using IP and Port provided during initialization.
     */
    void connect();

    /* @brief   
     */
    void assign_receive_handler(std::shared_ptr<IEventHandler> handler);

    /* @brief   Begin the TCP listening thread
     */
    void start_listening();

    /* @brief   Disconnects TCP socket.
     */
    void disconnect();

    /* @brief    Sends packet over TCP socket.
     *
     * @param    packet   The encoded packet to be sent.
     * 
     * @throws   SocketError
     */
    void send_packet(const std::vector<uint8_t>& packet);

    /* @brief   Retrieves unique ID of the device in this class instance.
     *
     * @note    Will be junk unless device is initialized
     */
    uint64_t get_unique_id();

    /* @brief   Retrieves device type of the device in this class instance.
     */
    DeviceType get_device_type() const;

    /* @brief   Retrieves protocolHandler of the device in this class instance.
     *
     * @note    To get access to protocol specific methods (in the child classes) this pointer must be cast to the appropriate child.
     */
    AbstractProtocol* get_protocol_handler() const;
};

#endif
