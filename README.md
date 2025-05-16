# README

## 功能包概览

1. **orbbec_camera / orbbec_camera_msgs / orbbec_description**  
   - 为 Orbbec 深度相机提供驱动、消息定义以及模型描述（URDF 等）所需内容，方便在 ROS 环境中进行相机数据获取与处理。

2. **piper / piper_description**  
   - Piper 机械臂的核心元包及其描述文件，包含机械臂本体的 URDF/Xacro 模型、关节配置和传感器信息等。

3. **piper_msgs**  
   - Piper 机械臂自定义的 ROS 消息定义，用于在各功能模块之间进行数据和状态的交互。

4. **piper_control**  
   - 提供 Piper 机械臂的控制逻辑与控制器配置，包含对关节控制、路径跟踪、移动控制等功能的封装。

5. **piper_launch**  
   - 各个功能节点的 ROS 启动文件集合，简化了机械臂与相机驱动、控制、识别以及其他模块的启动过程。

6. **piper_llm**  
   - 与大型语言模型（LLM）的集成，用于在机械臂应用场景中进行自然语言处理或文本生成，方便实现人机交互。

7. **piper_voice / edge_tts_voice**  
   - 语音功能相关包，用于实现语音识别、语音合成（TTS）等功能，为 Piper 机械臂提供听觉和语言交互能力。

8. **piper_tf**  
   - 用于维护和发布 Piper 机械臂各组件之间的 TF 变换树，确保视觉、控制和传感器数据在相同坐标系下工作。

9. **piper_vision**  
   - 计算机视觉相关包，用于处理来自相机或其他传感器的图像数据，包括目标检测、位姿估计等。

10. **piper_moveit**  
    - 基于 MoveIt 的运动规划功能包，提供关节规划、碰撞检测等高级机械臂运动控制功能。

11. **piper_sim**  
    - Piper 机械臂仿真环境，整合了模型、控制、运动规划等功能，方便在 Gazebo 等模拟器中进行开发和测试。

12. **piper_nav**  
    - 基于 ROS 2 Nav2 框架构建的小车导航功能包，集成了定位（AMCL）、路径规划与避障（Nav2 Planner、Controller）、可视化（RViz）等模块，支持地图载入、生命周期管理、路径跟踪与目标点导航等核心功能。

13. **piper_ranger**  
    - 松灵小车（Ranger Mini V2）控制集成包，负责小车底盘控制、CAN 总线驱动（GS_USB）、Odometry 计算与发布、TF 坐标变换支持，并提供键盘遥控、里程计发布、TF 广播和控制接口桥接等底层接口，确保小车与导航系统的无缝联动。
   
14. **piper_rl**  
    - 基于 ROS2 + Gazebo 仿真环境 + Moveit运动学控制，使用强化学习（PPO算法）训练 Piper 机械臂实现抓取任务。

15. **piper_slam**  
    - 基于unitree_lidar_sdk和IMU的建图（SLAM Toolbox）

15. **piper_spatiallm**  
    - SpatialLM 是一个 3D LLM，旨在处理 3D 点云数据并生成结构化的 3D 场景理解输出。这些输出包括建筑元素，例如墙壁、门、窗以及带有语义类别的定向物体边界框。
   
---

## 🎯 目标

本系统旨在实现以下能力：

1. 用户通过语音下达指令  
2. 大模型（LLM）理解任务  
3. 视觉识别目标 + VLM理解环境 + SpatialLM识别物品特征 
4. 坐标转换  
5. 机械臂执行抓取动作
6. 地图建模与导航、避障
7. 语义地图构建
8. 具身智能管理任务执行

---

## 🔄 完整流程结构图

```
🎤 用户说：抓取红杯子
       │
       ▼
🗣️ whisper_node.py（语音识别）   <-->  tts_output.py(文本转语音)
       │ → /voice_command (String)    <-->  /tts_request (String)
       │ → 这里完成了语音的同步输出与异步输出选择，但是还缺乏流式语音识别和流式语音输出，先凑合用吧
       ▼
🧠 llm_node.py（大模型解析意图） ← LLM（Ollama）
       │ → 输出到 /object_request (String)
       ▼
🎯 SLAM（读取地图，找到目标） ← 语义地图（VLM_mapper）
       │ → 输出到 /object_request (String)
       ▼
🚗 Nav2（导航与避障） ← 地图 + Ranger_SDK
       │ → 输出到 /object_request (String)
       ▼
👁️ yolo_detect_3d.py（到地方了再做新的目标检测，模拟/真实YOLO）
       │ → 输出到 /camera_target_point (geometry_msgs/PointStamped)
       │ → 注意：相机的坐标系与机械臂的坐标系不一定一致，需要手动标定或使用 TF 动态转换
       ▼
📐 tf_transformer.py（相机 → base_link 坐标转换）
       │ → /base_target_point (geometry_msgs/PointStamped)
       │ → 目前使用静态转换（机固定在底座）
       ▼
🦾 grasp_server.py（发送抓取 Action 到 MoveIt）
       │ → 控制机械臂完成抓取任务 ✅
       │ → 防跳点机制：若3s内坐标跳跃 > 0.1m 则忽略，连续五次跳点则认定目标消失
       │ → 后续需增加末端姿态控制
```

---

## 🛠 各模块说明与用法

1. **whisper_node.py**  |  **tts_output.py**  
   - **作用**：分别负责语音录音识别（Whisper）和文本转语音  
   - **输入**：麦克风（whisper_node.py），并输出到扬声器（tts_output.py）  
   - **输出**：
     - whisper_node.py 发布到 `/voice_command` (String)  
     - tts_output.py 订阅 `/tts_request` (String)  
   - **特性**：支持在识别与播报时进行同步提示，避免用户说话被打断

2. **llm_node.py**  
   - **作用**：调用本地 LLM 模型解析用户意图（如提取“红杯子”）  
   - **输入**：用户话语文本  
   - **输出**：发布 `/object_request`（String）  
   - **特性**：可适配 Ollama 等本地部署模型

3. **yolo_detect_3d.py**  
   - **作用**：基于 RGB + 深度图检测图像中的目标  
   - **输入**：订阅 `/camera/color/image_raw`、`/depth/image_raw` 等话题  
   - **输出**：发布目标位置到 `/camera_target_point`（geometry_msgs/PointStamped）

4. **tf_transformer.py**  
   - **作用**：将相机坐标系下的目标位置转换到 `base_link` 坐标系  
   - **输入**：订阅 `/camera_target_point`  
   - **输出**：发布 `/base_target_point`

5. **grasp_server.py**  
   - **作用**：调用 MoveIt 进行机械臂抓取  
   - **输入**：订阅 `/base_target_point`  
   - **动作**：通过 Action Client 发送抓取命令  
   - **特性**：支持防跳点机制、多轮服务调用和异步结果反馈

---



![机械臂与深度相机静态位置](./arm_camera_connector.jpg)

## ✅ 启动流程建议

下面是一个可能的启动顺序（可根据实际需求调整）：

1. 语音节点  
   ```bash
   ros2 run piper_voice whisper_node
   ros2 run piper_voice tts_output
   ```

2. 大模型节点  
   ```bash
   ros2 run piper_llm llm_node
   ```

3. TF 坐标转换前的准备  
   ```bash
   # 假设相机静态固定于机械臂底座, 如上面的图所示
   # 可根据实际情况调整数值，这里是按照图片中来的大致数值
   ros2 run tf2_ros static_transform_publisher 0.02 0. -0.08 0 0 0 camera_link base_link
   ```

4. 启动 tf_transformer  
   ```bash
   ros2 run piper_tf tf_transformer
   ```

5. 启动视觉检测  
   ```bash
   ros2 launch orbbec_camera dabai_dcw2.launch.py
   当前的检测还没有接收大模型给定的指令，所以先以瓶子检测作为目标
   ros2 run piper_vision yolo_detect_3d --ros-args -p device:=cpu -p interest:=bottle   
   # 或模拟信号
     ros2 topic pub /camera_target_point geometry_msgs/PointStamped \
     "{header: {frame_id: 'camera_link'}, point: {x: 0.1, y: 0.05, z: 0.03}}" --once
   ```

6. 启动机械臂及其 MoveIt  
   ```bash
   ros2 launch piper start_single_piper.launch.py
   ros2 launch piper_with_gripper_moveit demo.launch.py
   ```

7. 启动抓取服务  
   ```bash
   ros2 run piper_control grasp_server
   # 测试抓取服务
   ros2 service call /grasp_command std_srvs/srv/Trigger "{}"
   ```

---

![moveit界面](./moveit.jpg)


## 🧪 测试建议

- 对语音进行多轮指令测试，观察识别效果。  
- 模拟或真实相机检测多个物体，检查抓取动作的准确性。  
- 用 RViz 或 Gazebo 仿真来校验目标位置和机械臂末端姿态。

---

![静态布置相机视角](./camera.jpg)

## 🧩 常见问题排查

- **语音识别无法检测到设备**：麦克风设备号被写死在代码里需要自行考虑更换。  
- **语音识别延迟或噪音大**：检查麦克风输入、Whisper 模型精度或网络延迟。  
- **LLM 解析意图出错**：检查 LLM 本地部署是否成功、输入文本格式是否正确。  
- **坐标转换不准确**：确认静态变换的发布参数是否与实际硬件位置匹配。  
- **抓取动作异常**：查看 MoveIt 配置文件中的关节限制、碰撞模型是否正确。

---

## 🏁 总结

本系统整合了：

- **💬 语音交互（Whisper）**  
- **🧠 智能理解（大模型 LLM）**  
- **👁️ 目标识别（YOLO）**  
- **📐 坐标转换（TF）**  
- **🦾 动作规划（MoveIt）**

实现从自然语言指令到实际物理操作的完整链路。各模块之间结构清晰、松耦合，方便按需组合、逐步学习与自主扩展。欢迎贡献更多功能与改进，一起让 Piper 机械臂更强大！
