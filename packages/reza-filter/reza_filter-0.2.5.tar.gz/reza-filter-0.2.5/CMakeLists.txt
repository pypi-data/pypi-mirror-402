cmake_minimum_required(VERSION 3.18)
project(reza_filter LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Recommended by pybind11 when using modern FindPython
set(PYBIND11_FINDPYTHON ON)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module NumPy)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_reza_cpp cpp/reza_core.cpp)
target_link_libraries(_reza_cpp PRIVATE Python::Module Python::NumPy)

# Install the compiled extension inside the Python package `reza`
install(TARGETS _reza_cpp DESTINATION reza)
