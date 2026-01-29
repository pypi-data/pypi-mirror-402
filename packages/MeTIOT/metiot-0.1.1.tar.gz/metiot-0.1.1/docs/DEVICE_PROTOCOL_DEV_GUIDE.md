# Device Protocol

## Current Device Protocol Implementation

**Challenge:** Our `DeviceClient` class's `protocolHandler` is of the type `std::unique_ptr<AbstractProtocol>` which stops us from calling device protocol specific functions (e.g., function to create a calibration packet with specific parameters.)

**Solution:** Ideally the python programmer using this library simply calls the same function to get all of their device specific commands regardless of the device type. The solution to this issue is during the python function call `get_specific_protocol_handler` we automatically resolve exactly what protocol data type we are using (stored in `deviceType` for simplicity) then we dynamically cast the `std::unique_ptr<AbstractProtocol>` type into what ever the device protocol actually is.

## Creating New Device Protocols

> [!NOTE]
> The above information in `Current Device Protocol Implementation` is important to read to understand *why* you are doing the following

When creating a new device protocol (to support device specific protocol commands) following these steps should lead to success:

1. Add protocol .hpp file to `include/protocol/` and .cpp file to `src/protocol/`.
2. Create a class inheriting `AbstractProtocol` (This gives access to required functions like `constructPacket`).
3. Copy a similar workflow to other reference protocols. Function called -> Create data field -> Call constructPacket() -> return packet.
4. Add your new device type to `enum class DeviceType` in `include/client.hpp`.
5. Modify the device identification function in `src/client.cpp` to support your new protocol.
6. Modify `/src/python_bindings/bindings.cpp` to support your new protocol. You need to add support for protocol specific functions as well as support for dynamically casting the `AbstractProtocol` pointer to your Protocol pointer.

> If you want to add more OUTGOING fields or any protocol related header/subheader names add them to `include/protocol/protocol_constants.hpp`.