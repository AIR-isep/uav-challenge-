cmake_minimum_required(VERSION 3.16)
project(isep_bringup NONE)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config DESTINATION share/${PROJECT_NAME})
# Paramètres et missions ArduPilot du dépôt (dossier ardupilot/ à la racine)
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../../../ardupilot/
  DESTINATION share/${PROJECT_NAME}/ardupilot)

ament_package()
