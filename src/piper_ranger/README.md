# 🚗 松灵小车启动指南（Ranger Mini V2）

---

## 🔧 编译与 CAN 驱动加载

```bash
colcon build --symlink-install
sudo modprobe gs_usb
```

---

## 🔌 第一次运行：设置 CAN-USB 接口

```bash
sudo bash src/ranger_ros2/ranger_bringup/scripts/setup_can2usb.bash
```

---

## 🔁 每次重新上电后：激活 CAN 接口

```bash
sudo bash src/ranger_ros2/ranger_bringup/scripts/bringup_can2usb.bash
```

可使用如下命令测试 CAN 接口是否成功连接：

```bash
candump can0
```

---

## 🧰 启动前准备

请确保完成以下环境设置：

```bash
source /opt/ros/humble/setup.sh
source install/setup.sh
sudo bash src/ranger_ros2/ranger_bringup/scripts/bringup_can2usb.bash
```

> 请先 **连接 CAN 线** 并 **给小车上电**，然后再进行启动。

---

## 🚀 启动松灵小车控制节点

```bash
ros2 launch ranger_bringup ranger_mini_v2.launch.xml
```

- 可以发送 `cmd_vel` 类型的 ROS2 消息控制小车运动  
- 订阅 `/odom` 话题即可获取标准 `odom` 格式的里程计数据

---

## 🔁 启用 TF 坐标转换（可选）

如果你需要从 `odom` 坐标系自动转换到 `base_link` 坐标系，可使用以下命令：

```bash
ros2 launch ranger_bringup ranger_mini_v2.launch.xml publish_odom_tf:=true
```

---

## 🎮 启动键盘遥控（teleop）

可通过键盘控制小车：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

---

## ✅ 总结启动顺序建议：

1. 编译项目  
2. 安装并激活 CAN 接口（首次运行 vs 通电后）  
3. 设置 ROS 环境  
4. 启动控制节点或遥控方式  
5. 发送 `cmd_vel`，订阅 `odom`，必要时启用 TF 转换

---

