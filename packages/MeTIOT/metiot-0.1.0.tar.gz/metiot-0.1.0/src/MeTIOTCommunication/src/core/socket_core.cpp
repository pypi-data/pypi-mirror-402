#include "../include/core/socket_core.hpp"

SocketCore::SocketCore(const std::string& ip, int port) {
    serverIP = ip;
    serverPORT = port;

    clientSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (clientSocket < 0) {
        throw SocketError("Socket: Failed to create socket object.");
    }

    serverAddress.sin_family = AF_INET;
    serverAddress.sin_port = htons(serverPORT);

    if (inet_pton(AF_INET, serverIP.c_str(), &(serverAddress.sin_addr)) <= 0) {
        throw SocketError("Socket: Invalid/Not Supported IP Address.");
    }
}

SocketCore::~SocketCore() {

}

int SocketCore::connect_device() {
    return connect(clientSocket, (struct sockaddr*)&serverAddress, sizeof(serverAddress));
}

int SocketCore::disconnect() {
    return close(clientSocket);
}

int SocketCore::send_data(const std::vector<uint8_t>& data) {
    return send(clientSocket, data.data(), data.size(), 0);
}

std::vector<uint8_t> SocketCore::recv_data() {
    std::vector<uint8_t> buffer;
    buffer.resize(MAX_RECV_SIZE);

    ssize_t bytesReceived = recv(clientSocket, buffer.data(), MAX_RECV_SIZE, 0);

    if (bytesReceived > 0) {
        buffer.resize(bytesReceived);
    } else if (bytesReceived == 0) {
        throw SocketError("Socket: Connection closed by peer.");
    } else {
        throw SocketError("Socket: Error occured during read.");
    }

    return buffer;
}