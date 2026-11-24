cmake_minimum_required(VERSION 3.16)
project(isep_description NONE)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config models worlds scripts
  DESTINATION share/${PROJECT_NAME})

# Ajoute share/isep_description/models et worlds à GZ_SIM_RESOURCE_PATH
# dès qu'on fait « source install/setup.bash ».
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.dsv.in")

ament_package()
