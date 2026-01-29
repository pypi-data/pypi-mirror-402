#ifndef SOCKET_CORE_HPP
#define SOCKET_CORE_HPP

#include <string>
#include <vector>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include "exceptions.hpp"

#define MAX_RECV_SIZE 1024

class SocketCore {
  private:
    int clientSocket;
    std::string serverIP;
    int serverPORT;
    sockaddr_in serverAddress;

  public:
    SocketCore(const std::string& ip, int port);
    ~SocketCore();

    int connect_device();

    int disconnect();

    int send_data(const std::vector<uint8_t>& data);

    std::vector<uint8_t> recv_data();
};

#endif
