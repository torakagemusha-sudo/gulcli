cmake_minimum_required(VERSION 3.14)
project(gul VERSION 2.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(GUL_SOURCES
  src/confidence.cpp
  src/decision.cpp
  src/jurisdiction.cpp
  src/predicate.cpp
  src/policy_expr.cpp
  src/inference.cpp
  src/dataset.cpp
  src/config.cpp
  src/json_io.cpp
  src/runtime_io.cpp
  src/fact_environment.cpp
  src/scenarios.cpp
  src/cli.cpp
  src/main.cpp
)

add_executable(gul ${GUL_SOURCES})
target_include_directories(gul PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_features(gul PRIVATE cxx_std_17)

if(WIN32)
  target_link_libraries(gul PRIVATE ws2_32)
endif()

install(TARGETS gul RUNTIME DESTINATION bin)
