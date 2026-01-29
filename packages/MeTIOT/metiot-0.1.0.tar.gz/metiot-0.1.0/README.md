# MeT IOT Communication

## Protocol Information

Communication between MeT IOT devices and this library are conducted over TCP sockets. To see more in-depth details about this protocol including encryption standard see [Protocol Docs](docs/Protocol.md)

## How To Use

For all information on **how** to use go to [HowToUse Docs](docs/HowToUse.md). Also see examples of use in the [Examples folder](examples/)

## How to Compile

Linux based systems:

1. Create and navigate into build directory
```bash
mkdir build
cd build
```
2. Compile library using CMake
```bash
cmake ..
cmake --build . --config Release
```
3. Export path to python
```bash
export PYTHONPATH=./src/python_bindings:$PYTHONPATH
```
4. Now you can use the library. If you first want to test it you can try
```bash
python3
```
```py
import MeTIOT
client = MeTIOT.DeviceClient("0.0.0.0", 12345)
type(client)
client.connect()
```

## How to Add More Features

**WIP** docs



