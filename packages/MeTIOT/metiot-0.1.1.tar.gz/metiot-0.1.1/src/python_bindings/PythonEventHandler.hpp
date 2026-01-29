#include "../MeTIOTCommunication/include/interfaces/event_handler.hpp"
#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/functional.h>

namespace py = pybind11;

class PythonEventHandler : public IEventHandler {
public:
    PythonEventHandler(py::function on_data,
                       py::object on_warning = py::none(),
                       py::object on_fatal = py::none())
                    : data_cb_(std::move(on_data)),
                      warn_cb_(std::move(on_warning)),
                      fatal_cb_(std::move(on_fatal)) {}

    void handle_message(DeviceClient* client, int packet_id, const std::vector<uint8_t>& payload) override {
        py::gil_scoped_acquire acquire;
        try {
            data_cb_(client, packet_id, payload);
        } catch (py::error_already_set &e) { handle_py_error(e); }
    }

    void handle_warning(DeviceClient* client, const std::string& message) override {
        py::gil_scoped_acquire acquire;
        if (!warn_cb_.is_none()) {
            try {
                warn_cb_(client, message);
            } catch (py::error_already_set &e) { handle_py_error(e); }
        }
    }

    void handle_fatal_error(DeviceClient* client, const std::string& message) override {
        py::gil_scoped_acquire acquire;
        if (!fatal_cb_.is_none()) {
            try {
                fatal_cb_(client, message);
            } catch (py::error_already_set &e) { handle_py_error(e); }
        }
    }

private:
    void handle_py_error(py::error_already_set &e) {
        std::cerr << "Exception in Python callback: " << e.what() << std::endl;
    }

    py::function data_cb_;
    py::object warn_cb_; // Using object allows for py::none()
    py::object fatal_cb_;
};