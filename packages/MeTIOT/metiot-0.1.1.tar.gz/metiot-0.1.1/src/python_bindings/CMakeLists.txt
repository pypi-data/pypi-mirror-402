pybind11_add_module(
    MeTIOT 
    bindings.cpp
)

target_link_libraries(
    MeTIOT 
    PRIVATE 
    MeTIOTCommunication
)

target_include_directories(
    MeTIOT 
    PRIVATE 
    $<TARGET_PROPERTY:MeTIOTCommunication,INTERFACE_INCLUDE_DIRECTORIES>
)

install(TARGETS MeTIOT LIBRARY DESTINATION .)