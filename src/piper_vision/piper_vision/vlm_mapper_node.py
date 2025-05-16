import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PointStamped, Point
from std_msgs.msg import Empty          # 触发器消息类型，可替换为你需要的类型

import tf2_ros
import tf2_geometry_msgs
import subprocess
import json
import cv2
from cv_bridge import CvBridge
import os
from datetime import datetime
import s3img
# 通过 pip install volcengine-python-sdk[ark] 安装方舟SDK
from volcenginesdkarkruntime import Ark
from typing import Dict, List
from piper_msgs.msg import AllObjectPos


# 替换 <Model> 为模型的Model ID
vlmmodel="doubao-1.5-vision-pro-32k-250115"


#  @TODO 设计一个服务，如果收到vlm识别的请求，就读取摄像头数据，和当前的摄像头给的目标点的坐标，然后返回当前的一些内容，并且将他们的坐标锚定到目标点坐标附近（or直接给目标点坐标

class VLMMapperNode(Node):
    def __init__(self):
        super().__init__('vlm_mapper')

        # ---------- 基础组件 ----------
        self.bridge = CvBridge()
        self.latest_img_path: str | None = None     # 存最近一帧图像完整路径
        self.latest_img_stamp: str | None = None    # 存图像时间戳字符串
        self.latest_data: Dict[str, Any] | None = None  # 存 parse_object_points 结果

        # ---------- 订阅 ----------
        self.image_sub = self.create_subscription(
            Image, '/camera/color/image_raw', self.image_callback, 10
        )
        self.subscription = self.create_subscription(
            AllObjectPos, '/piper_vision/all_object_points',
            self.parse_object_points, 10
        )
        self.trigger_sub = self.create_subscription(
            Empty, '/detection_trigger', self.on_trigger, 10
        )

        # ---------- 其他 ----------
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.vlmclient = Ark(api_key=os.getenv('ARK_API_KEY'))
        self.get_logger().info("📸 VLM 图像识别与坐标记录节点启动")

    # ------------------------------------------------------------------
    # ① 图像缓存：每到一帧就立即保存，但只保存最新一张
    # ------------------------------------------------------------------
    def image_callback(self, msg: Image):
        cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        now = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 毫秒级
        img_path = f"images/{now}.jpg"
        os.makedirs("images", exist_ok=True)
        cv2.imwrite(img_path, cv_image)

        # 更新缓存
        self.latest_img_path = img_path
        self.latest_img_stamp = now
        self.get_logger().debug(f"✅ 新图像缓存于 {img_path}")

    # ------------------------------------------------------------------
    # ② 目标检测结果缓存（与之前相同，略有删减）
    # ------------------------------------------------------------------
    def parse_object_points(self, msg: AllObjectPos):
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        objs = [
            {
                "name": name,
                "position": {"x": pt.x, "y": pt.y, "z": pt.z},
                "size": {"width": msg.widths[i], "height": msg.heights[i]},
            }
            for i, (name, pt) in enumerate(zip(msg.names, msg.points))
        ]
        self.latest_data = {
            "time": datetime.fromtimestamp(t).isoformat(timespec="milliseconds"),
            "frame": msg.header.frame_id,
            "objects": objs,
        }

    # ------------------------------------------------------------------
    # ③ 触发：拿最近一帧做 VLM + 解析目标检测 + 存储
    # ------------------------------------------------------------------
    def on_trigger(self, _):
        if not (self.latest_img_path and self.latest_data):
            self.get_logger().warn("⚠️ 触发时缺少最新图像或目标数据，忽略")
            return

        # 1) 调用 VLM 识别
        vlm_result = self.call_doubao(self.latest_img_path)
        if vlm_result is None:
            self.get_logger().error("❌ VLM 识别失败")
            return

        # 2) 合并两路结果
        record = {
            "img_path": self.latest_img_path,
            "img_stamp": self.latest_img_stamp,
            "vlm_result": vlm_result,
            "objects": self.latest_data,
        }

        # 3) 写文件（JSON 追加）
        os.makedirs("records", exist_ok=True)
        out_path = f"records/{self.latest_img_stamp}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        self.get_logger().info(f"📝 记录写入 {out_path}")

    # ------------------------------------------------------------------
    # ④ 封装上传 / 调用大模型
    # ------------------------------------------------------------------
    def call_doubao(self, img_path: str) -> list | None:
        try:
            # 假设 s3img.upload_file(img_path) 返回公网 URL
            img_url = s3img.upload_file(img_path)
            resp = self.vlmclient.chat.completions.create(
                model=vlmmodel,
                messages=[
                    {"role": "user", "content": [
                        {"type": "text",
                         "text": "你是一个智能楼宇测绘员，请提炼这张照片中的物品、门牌号、以及所有有价值值得存到语义地图里的信息，以 JSON list 返回"},
                        {"type": "image_url", "image_url": {"url": img_url}},
                    ]}
                ],
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            self.get_logger().error(f"doubao 调用失败: {e}")
            return None



def main(args=None):
    rclpy.init(args=args)
    node = VLMMapperNode()
    rclpy.spin(node)
    rclpy.shutdown()
