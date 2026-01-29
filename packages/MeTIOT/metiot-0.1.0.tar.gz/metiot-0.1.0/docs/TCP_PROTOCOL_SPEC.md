# TCP Communication Protocol Specification

> [!NOTE]
> This documentation details the technical specifications of the protocol used for all TCP communication. **It is not required** to be read or understood for general use of the associated Python library. For usage instructions, please refer to the [How To Use](HowToUse.md) documentation.

## Protocol Scope and Usage

This protocol governs all TCP communication between MeT IoT devices and external clients (e.g., standalone library, Home Assistant integration).

## Connection Initilization Sequence

This sequence desribes the steps a MeT IoT device and the client library take to establish and identify a connection.

### Initialization Sequence

1. **Discovery:** The device broadcasts a Zeroconf (mDNS) packet for initial discovery.
2. **Connection:** The client library connects to the device's TCP socket.
3. **Request:** The client library sends a **Device Identification Request** command.
4. **Response:** The device responds with a **Device Identifier** response packet.
5. **Operation:** Regular data exchange begins.

### Device Identifier Response Packet

This specific packet is sent by the IoT device to the library during connection initialization.

![Device Identifier Response](images/DeviceIdentifierResponse.jpg)

The Data Payload (within a Data Header `0xFE` packet) contains the following information:

* **8-Bit Device ID:** Specifies the type of device (e.g., Fish Tank).
* **64-Bit Unique Device ID:** A unique identifier for the specific device instance.

## General Packet Format

All data over the TCP connection adheres to a common structure.

![Packet Diagram](images/Packet.jpg)

### Packet Structure Breakdown

| Field | Bytes | Description |
|-|-|-|
| COBS Header | 1 | Marks the start of the packet and contains information for COBS decoding. |
| CRC | 2 | 16-bit Cyclic Redundancy Check for error detection across the entire data payload. |
| Data Header | 1 | Identifies the overall purpose or type of the packet (e.g., data transfer, identification). |
| Data Payload | 0-n | The main data content. Its exact structure depends on the Data Header. |
| COBS Trailer | 1 | Marks the end of the packet, always the value `0x00`. |

### Purpose of Protocol Components

* **Consistent Overhead Byte Stuffing (COBS):** Ensures reliable packet delimitation by guaranteeing the packet trailer byte (`0x00`) never appears in the body of the packet. The header contains essential information for the receiver on how to decode the data.
* **Cyclic Redundancy Check (CRC):** A 16-bit code used for robust error detection. If the received CRC does not match the CRC recalculated from the Data Header and Payload, the packet is discarded as corrupted. The CRC algorithm is based on: G.D. Nguyen, “Fast CRCs,” IEEE Transactions on Computers, vol. 58, no. 10, pp. 1321-1331, Oct. 2009.

## Data Header Commands and Flow

> [!NOTE]
> All relevant **Bytes** columns in tables **do not include protocol overhead** and only include the length of the header + data. The protocol overhead specifically refers to COBS trailer, COBS deliminator, and 16-Bit CRC which make up for a total of **4 bytes not included in those values**.

The Data Header (1 byte) is the first piece of information after the CRC and determines the primary function of the packet.

### Standard Library-to-Device Commands

These are requests or notifications sent from the client library to the MeT IoT device.

| Purpose | Data Header | Data Payload | Bytes |
|-|-|-|-|
| Malformed Packet Notification | `0xFF` | (None) | 1 |
| Device Identification Request | `0xFE` | (None) | 1 |

### Standard Device-to-Library Commands

These are responses or unsolicited notifications sent from the MeT IoT device to the client library.

| Purpose | Data Header | Data Payload | Bytes |
|-|-|-|-|
| Malformed Packet Notification | `0xFF` | (None) | 1 |
| Device Identifier | `0xFE` | [1 byte Device ID + 8 byte Unique Device ID](#device-identifier-response-packet). | 10 |
| Data Transfer | `0xFD` | [Variable-length structure.](#data-field-format) | n |

### Device Identification Codes

This 1-byte code is carried in the **Device Identifier** packet (`0xFE`).

| Code (1 Byte) | Device Type |
|-|-|
| `0xFF` | Fish Tank |
| ... | *(Future devices)* |

## Data Payload Structure (Header 0xFD)

When the **Data Header** is `0xFD` (Data Transfer), the **Data Payload** is structured as a series of repeating **Sub-Header** and **Data** fields.

### Data Field Format

![Device Data Field Diagram](images/DeviceData.jpg)

The Data Payload consists of one or more data points, each preceded by its own Sub-Header. This pattern repeats until the payload ends: `Sub-Header`, `Data`, `Sub-Header`, `Data`, ...

| Field | Purpose |
|-|-|
| Data Sub-Header | Identifies the specific data point (e.g., "Current Temp"). |
| Data | The actual data value, interpreted based on the Sub-Header. |

### Supported Data Types

> [!IMPORTANT]
> The following standard C/C++ data types are supported for transmission within the **Data** field:
>
> * `int8_t`
> * `int16_t`
> * `int32_t`
> * `int64_t`
> 
> *All unsigned variants of the above data types are allowed*
>
> The following data types *can* be used but research must first be conducted to ensure each devices architecture support the same byte length.
>
> * `float`
> * `double`

## Device-Specific Protocol: Fish Tank

This section details the custom commands and data formats specific to the Fish Tank device (`Device ID: 0xFF`). The Fish Tank protocol still inherits all commands defined in [Data Header Commands and Flow](#data-header-commands-and-flow).

### Fish Tank: Library-to-Device Commands

| Purpose | Data Header | Data Payload | Bytes |
|-|-|-|-|
| Sensor Attribute Request | `0xFC` | None | 1 |
| Calibration Values | `0xFB` | *To be decided* | |

### Fish Tank: Device-to-Library Commands

| Purpose | Data Header | Data Payload | Bytes |
|-|-|-|-|
| Sensor Attribute Response | `0xFC` | *To be decided* | |
| Calibration Finished | `0xFB` | 1-Byte Sensor Address | 2 | 

### Fish Tank: Data Sub-Header

> [!NOTE]
> Values marked with *(decimal value)* are multiplied by 100 before transmission then divided by 100 when being interpreted. This only gives an accuracy of up to 2 decimal places.

| Sub-Header | Data Field | Data Type |
|-|-|-|
| `0xFF` | Temperature *(decimal value)* | `int16_t` |
| `0xFE` | Humidity *(decimal value)* | `uint16_t` |
| `0xFD` | pH *(decimal value)* | `uint16_t` |
| `0xFC` | Oxidation-Reduction Potential | `int16_t` | 
| `0xFB` | Dissolved Oxygen | `int16_t` |
| `0xFA` | Conductivity | `int16_t` |
| `0x00` | Data End | (None/Blank) |

### Fish Tank: Sensor Attribute Aquisition

During the devices startup it allocates a unique I2C address and stores the device type for all devices on the I2C bus. For later use (like calibration) we will need to store this information so we know what types of devices are currently associated with the device.

#### Sensor Attribute Response Command

I2C Address:Device Type pair can repeat as many times as required.

![Fish Tank Sensor Attribute Response](images/FishTankSensorAttributeResponse.jpg)

#### Sensor Device Types

> [!NOTE]
> A Fish Tank device can have multiple of the same type of device so its important to sort by their I2C address not.

| Code | Device Type |
|-|-|
| `0xFF` | Temeprature Sensor |
| `0xFE` | Humidity Sensor |
| `0xFD` | pH Sensor |
| `0xFC` | Oxidation-Reduction Potential Sensor |
| `0xFB` | Dissolved Oxygen Sensor |
| `0xFA` | Conductivity Sensor |

### Fish Tank: Calibration

#### Calibration Values Command

#### Calibration Finished Command