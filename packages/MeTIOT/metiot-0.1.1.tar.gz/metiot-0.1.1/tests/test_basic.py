import MeTIOT

def test_client_init():
    client = MeTIOT.DeviceClient("0.0.0.0", 12345)
    assert client is not None