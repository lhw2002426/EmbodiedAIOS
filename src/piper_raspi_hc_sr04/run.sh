#!/bin/bash
# TODO: ros2 run will failed now
colcon build --packages-select piper_raspi_hc_sr04
source install/setup.bash
ros2 run piper_raspi_hc_sr04 hc_sr04_node