# 🚗 小车导航启动指南

---

## 🔧 编译项目

```bash
colcon build --symlink-install
```

---

## 🗺️ SLAM 启动步骤

### ✅ 准备工作

1. 安装 `PCL`（点云库）  
2. 设置固定 IP，关闭 DHCP：

```bash
sudo ip addr add 192.168.1.2/24 dev enx00e04c360241
```

---

### 🚀 启动雷达与点云转换

#### 1. 启动 Lidar 驱动发布 `PointCloud2` 数据：

```bash
source install/setup.bash
ros2 launch unitree_lidar_ros2 launch.py
```

#### 2. 手动发布雷达坐标变换（TF）：

```bash
ros2 run tf2_ros static_transform_publisher \
  --x 0 --y 0 --z 0 \
  --qx 0 --qy 0 --qz 1 --qw 0 \
  --frame-id base_link --child-frame-id unilidar_lidar
```

#### 3. 将点云转换为 `LaserScan`：

```bash
source install/setup.bash
ros2 launch pointcloud_to_laserscan sample_pointcloud_to_laserscan_launch.py
```

#### 4. 路径修复模块启动（可选）：

```bash
source install/setup.bash
ros2 launch goal_path_fixer fixers_launch.py
```

---

### 🧭 扫描建图（可选）

如果你只需导航，不需要建图，则此步可跳过。

```bash
source install/setup.bash
ros2 launch slam_toolbox online_sync_launch.py
```

---

## 🚘 小车控制启动

请参考代码路径：  
```
src/piper_ranger
```

---

## 🧠 Nav2 导航启动流程

### 1. 启动 RViz 可视化工具：

```bash
source install/setup.sh
ros2 run rviz2 rviz2 -d rviz/rviz.config.rviz
```

### 2. 启动建图（如需建图）：

```bash
source install/setup.bash
ros2 launch slam_toolbox online_sync_launch.py
```

### 3. 启动 `map_server` 与 `amcl`：

```bash
source install/setup.sh
ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=map/my_map.yaml
ros2 run nav2_amcl amcl --ros-args --params-file nav2_config/nav2_params.yaml
```

或使用脚本一键启动：

```bash
./activate_map.sh
# ros2 lifecycle set map_server configure
# ros2 lifecycle set map_server activate
# ros2 lifecycle set amcl configure
# ros2 lifecycle set amcl activate
```

### 4. 启动 Nav2 主导航系统：

```bash
ros2 launch nav2_bringup navigation_launch.py \
  use_sim_time:=false \
  map:=map/my_map.yaml \
  params_file:=nav2_config/nav2_params.yaml
```

---
