/*

Purpose: The purpose of this file is to make the cpp completely independent of the python layer.

How its used: In the python binding c++ code we create a child class of this class. This allows us to manage the GIL and call the Python function required during
              during the message receive functionality of this library.

How to use it: There should be no reason to directly touch this file at all. If this is being adapted to be independent of C++ just create a c++ child class of 
               this in a similar fashion (but without python related functionality).
               
*/

#ifndef EVENT_HANDLER_HPP
#define EVENT_HANDLER_HPP

#include <vector>
#include <cstdint>

class DeviceClient; // Fix circular dependency

class IEventHandler {
public:
    virtual ~IEventHandler() = default;

    virtual void handle_message(DeviceClient* client, int packet_id, const std::vector<uint8_t>& payload) = 0;

    virtual void handle_warning(DeviceClient* client, const std::string& message) = 0;

    virtual void handle_fatal_error(DeviceClient* client, const std::string& message) = 0;
};

#endif