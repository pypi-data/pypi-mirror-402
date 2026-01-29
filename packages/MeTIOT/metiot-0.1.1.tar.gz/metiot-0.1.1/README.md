# MeT IOT Communication

## How To Use

### Importing the Library

#### Use pip to install the library

```sh
pip install MeTIOT
```

> [!NOTE]
> This library is not pre-compiled.
> You must have installed on your system (Other version may work but are official unsupported):
> * GCC >= 15.2.1
> * CMake >= 3.10

### Programming with the Library

#### Testing the library imported successfully

You can use this code to test you can successfully import the library into your code.

```py
import MeTIOT

client = MeTIOT.DeviceClient("0.0.0.0", 12345)

print(type(client))
print("MeTIOT import successful!")
```

#### Using the library

For further information on how to use this library refer to the [PYTHON_LIB_GUIDE.md document](https://github.com/Microelectronic-Technologies/MeTIOTCommunication/blob/main/docs/PYTHON_LIB_GUIDE.md).

## How to Compile (Manual. For Testing)

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

