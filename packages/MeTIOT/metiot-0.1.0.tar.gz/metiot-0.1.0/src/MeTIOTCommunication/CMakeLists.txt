cmake_minimum_required(VERSION 3.10)
project(MeTIOTCommunication LANGUAGES CXX)

add_compile_options(-Wall -Wextra -Wpedantic)

file(GLOB_RECURSE SOURCE_FILES "src/*.cpp")

add_library(
    MeTIOTCommunication
    STATIC
    ${SOURCE_FILES}
)

target_compile_features(
    MeTIOTCommunication
    PUBLIC
    cxx_std_20
)

target_include_directories(
    MeTIOTCommunication
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)