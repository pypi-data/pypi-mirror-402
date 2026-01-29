# API Reference

The `MeTIOT` library provides a high-level interface for interacting with MeTIOT IoT devices via TCP. The core of the library is the `DeviceClient`, which manages the connection, event loops, and protocol handling.

## 1. Client Library Components (`MeTIOT`)

The `DeviceClient` class is the primary entry point for all device interactions.

### Lifecycle Management

#### `DeviceClient(ip: str, port: int)`

*Constructor* | **Module:** `MeTIOT`

Initializes the client object with the target device's network information.

* **Arguments**
    * `ip` (str): IPv4 address of the device.
    * `port` (int): Communication port.
* **Errors:** Raises `SocketError` if the IP address is invalid or unsupported.

#### `connect()`

*Method* | **Module:** `MeTIOT.DeviceClient`

Establishes the TCP connection and performs initial handshake/device discovery.

* **Errors:** Raises `SocketError` if the device is unreachable.

#### `disconnect()`

*Method* | **Module:** `MeTIOT.DeviceClient`

Safely closes the active TCP connection.

---

### Protocol & Identity

#### `get_protocol_handler()`

*Method* | **Module:** `MeTIOT.DeviceClient`

Returns the `ProtocolHandler` specific to the current device type. use this to encode/decode bytes.

* **Returns:** `ProtocolHandler`

> [!TIP]
> Use this instead of the deprecated `get_specific_protocol_handler()`

#### `get_unique_id()`

*Method* | **Module:** `MeTIOT.DeviceClient`

Retrieves the globally unique 64-bit ID assigned to the hardware.

* **Returns:** 8-byte Device ID.

#### `get_device_type()`

*Method* | **Module:** `MeTIOT.DeviceClient`

Identifies the model/type of the connected device.

* **Returns:** `MeTIOT.DeviceType`

---

### Asynchronous Operations

#### `assign_handlers(on_data, on_warning=None, on_fatal=None)`

*Method* | **Module:** `MeTIOT.DeviceClient`

Registers callback functions for the background listening thread.

| Argument | Signature | Description |
|-|-|-|
| `on_data` | `(device, header, data)` | Triggered on successful packet reception. |
| `on_warning` | `(device, msg)` | **Optional.** Triggered on non-fatal issues (e.g., CRC mismatch). |
| `on_fatal` | `(device, msg)` | **Optional.** Triggered when the loop crashes or 10 warnings occur |

#### `start_listening()`

*Method* | **Module:** `MeTIOT.DeviceClient`

Spawns a background thread to monitor the TCP socket. **Requires handlers to be assigned first.**

* **Errors:** `LibraryError` if `assign_handlers` has not been called.

#### `send_packet(packet: bytes)`

*Method* | **Module:** `MeTIOT.DeviceClient`

Sends a raw byte buffer to the device.

* **Arguments:** `packet` (bytes): The encoded payload.
* **Errors:** `SocketError` on transmission failure.


> [!IMPORTANT]
> **WIP** Document. Below text may not be correct.

## 2. Protocol Handler Methods (Accessed via `client.get_protocol_handler()`)

The methods available on the protocol handler instance depend entirely on the connected device type. The protocol handler also contains universal utility methods for packet handling.

### 2.1 Universal Protocol Utility Methods

| Method | Returns | Description |
|-|-|-|
| `deconstruct_packet(packet: bytes)` | `tuple[int, bytes]` | Decodes the packet buffer, validating CRC, performing COBS unstuffing, and returning the Data Header and raw Data Payload. |
| `interpret_data(data_payload: bytes)` | `dict` | Interprets the raw Data Payload into a key-value dictionary using known Sub-Headers and Data Types. Keys match the Data Field purpose (e.g., "Temperature_C"). |
| `fetch_last_packet()` | `bytes` | Returns the raw byte buffer of the last packet successfully created by this protocol handler instance. Useful for re-sending after a `MalformedPacketNotification`. |

### 2.2 Fish Tank Protocol Methods (`Device ID: 0xFF`)

These methods are available if the device type is "Fish Tank"

| Method | Returns | Purpose | Arguments |
|-|-|-|-|

## 3. Protocol Constants (`MeTIOT.ProtocolConstants`)

These constants are integers representing the 1-byte Header/Sub-Header codes used in the communication. All constants mentioned here are the exposed constants. In other documentation the codes here are referenced as *Device-to-Library Codes*.

### 3.1 Standard Data Header Codes

| Constant Name | Value | Description |
|:---|:---|:---|
| `MalformedPacketNotification` | `0xFF` | Notification for a corrupted/unparsable packet. |
| `DeviceIdentifier` | `0xFE` | Response from the device containing the Device ID and Unique ID. |
| `DataTransfer` | `0xFD` | Unsolicited data/status update from the device. |

### 3.2 Fish Tank Data Header Codes

| Constant Name | Value | Description |
|-|-|-|