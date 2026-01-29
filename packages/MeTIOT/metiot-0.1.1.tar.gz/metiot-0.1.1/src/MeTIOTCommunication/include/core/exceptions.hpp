#ifndef EXCEPTIONS_HPP
#define EXCEPTIONS_HPP

#include <stdexcept>
#include <string>

class LibraryError : public std::runtime_error {
    using std::runtime_error::runtime_error;
};

// Socket Errors
class SocketError : public LibraryError {
    using LibraryError::LibraryError;
};

// Protocol Errors
class ProtocolError : public LibraryError {
    using LibraryError::LibraryError;
};

// Encoding/COBS Errors
class EncodingError : public LibraryError {
    using LibraryError::LibraryError;
};

class LogicError : public LibraryError {
    using LibraryError::LibraryError;
};

#endif