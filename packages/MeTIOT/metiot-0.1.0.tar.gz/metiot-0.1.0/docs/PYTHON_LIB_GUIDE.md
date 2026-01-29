# Guide - How To Use the Library

This guide provides practical steps for using the MeT IoT Python client library. For details on the underlying packet structure, see [TCP_PROTOCOL_SPEC.md](TCP_PROTOCOL_SPEC.md).

## Installation

The MeT IoT library is *soon to be* available on PyPI.

```bash
pip install x
```

## Device Discovery

MeT IoT devices broadcast their presence using Zeroconf (mDNS). The library includes a function to listen for and find available devices on your local network.

1. **WIP**

## Connecting to a Device

Establish a persistent TCP connection and perform the initial device identification handshake.

1. **Create Client:** Create a client with the device's IP & Port.
    ```py
    import MeTIOT

    client = MeTIOT.DeviceClient("192.168.1.100", 12345)
    ```
2. **Connect:** Use the `connect()` method to connect to the device.
    ```py
    client.connect()
    ```
    **Behind the Scenes:** After connecting to the TCP socket, the client sends a Device Identification Request and waits for the Device Identifier response. This identifies the device type and its unique ID.

3. **Device Protocol:** For sending and interpreting message you will need a protocol handler.
    ```py
    protocol = client.get_protocol_handler()
    ```
    **Behind the Scenes:** After the connection has happened and the device type is identified that devices unique protocol class will be assigned to the client. This protocol class comes with its own unique methods. You can find all unique device protocol methods in the [API Reference](API_REFERENCE.md).

## Receiving Data

This library uses a dedicated thread to listen for unsolicited data transfers from the device. You should register callback functions to handle incoming data updates.

> [!NOTE]
> **Prerequisite:** You must first follow [Connecting to a Device](#connecting-to-a-device) creating a client, connecting, **and** fetching the device protocol.

1. **Define Async Callbacks:** Create function to process incoming data object, warning messages, and fatal errors. You will likely have different data processing function for each device type you expect to handle.
    ```py
    def my_update_handler(device, header, data):
        print(f"Received message from {device.get_unique_id()} with header: {header}")

        match header:
            case MeTIOT.Incoming.General.Data:
                # Use the protocol handler to interpret the raw bytes into a dictionary
                deviceProtocol = device.get_protocol_handler()
                telemetry = deviceProtocol.interpret_data(data)
                print(f"Temperature: {telemetry['Temperature_C']} C")

            case MeTIOT.Incoming.MalformedPacketNotification:
                print("Device reported a communication error.")
                # Since the library is stateless, you must track your last
                # sent packet locally if you wish to re-send it (Recommended).

            # Example of modular expansion for specific devices
            # case MeTIOT.Incoming.FishTank.SpecificAlert:
            #     print("Fish tank alert!")

            case _:
                # Handle other commands defined in the API Reference
                pass

    def warning_handler(device, msg):
        # This function is optional
        #
        # When this function is called the warning handling is already handled by the library. This function is just for debugging.
        print(f"Device {device.get_unique_id()} has non-fatal warning: {msg}")

    def error_handler(device, msg):
        # This function is optional
        #
        # When this function is called a fatal error has occured and the listening loop has stopped. The device will no longer listen for messages.
        print(f"Device {device.get_unique_id()} has fatal error: {msg}")
    ```

2. **Register the Handler/s:** Attach the handler/s to the client instance.
    ```py
    # --- To assign all devices the same handler ---
    client.assign_handlers(on_data=my_update_handler, on_warning=warning_handler, on_fatal=error_handler)
    # If you do not want to specify an on_warning or on_fatal handler they can both be removed
    # client.assign_handlers(on_data=my_update_handler)

    #   OR
    # --- To assign different devices types unique handlers ---
    #
    # devType = client.get_device_type() # Fetch the current device type
    #
    # if (devType == MeTIOT.DeviceType.FISH_TANK):
    #     client.assign_handlers(on_data=fish_tank_update_handler, on_warning=warning_handler, on_fatal=error_handler)
    # elif (devType == MeTIOT.DeviceType.UNKNOWN):
    #     print("Unknown device type. Assigning generic handler")
    #     client.assign_handlers(on_data=generic_update_handler, on_warning=warning_handler, on_fatal=error_handler)
    ```
    **Behind the Scenes:** The client initiates a background listener thread to monitor the socket. When a message is detected, the library automatically handles the decoding and verification (CRC/COBS). It segregated the payload into its `header` and `data` components and dispatches them directly to your handler.

## Sending Commands

To send a command (like changing a setting), use the client objects protocol handler for high-level command methods.

> [!NOTE]
> **Prerequisite:** You must first follow [Connecting to a Device](#connecting-to-a-device) creating a client, connecting, **and** fetching the device protocol.

1. **Create Packet:** Use the device-specific methods on the `protocol` object to generate the complete, ready-to-send packet buffer.
    ```py
    # Example for sending a calibration command to a Fish Tank device
    # The protocol method generates the Data Payload + Header + CRC + COBS.
    packet = protocol.create_fish_tank_calibration()
    ```

2. **Send Packet:** Supply that packet buffer to the client's send function.
    ```py
    client.send_packet(packet)
    print("Calibration request packet sent.")
    ```
    **Behind the Scenes:** The protocol handler wraps your command with mandatory overhead (CRC and COBS encoding), ensuring the device can validate the integrity of the message upon receipt.
