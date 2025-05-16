import gymnasium as gym
import numpy as np
import mujoco
from mujoco import viewer
import os
from ament_index_python.packages import get_package_share_directory
import cv2
import math
import random

JOINT_NUM = 6
JOINTLOWERLIMIT = [-2.618, 0, -2.967, -1.745, -1.22, -2.0944]
JOINTUPPERLIMIT = [2.618, 3.14, 0, 1.745, 1.22, 2.0944]
GRIPPER_OPEN_POS_7 = 0.0
GRIPPER_CLOSE_POS_7 = 0.035
GRIPPER_OPEN_POS_8 = 0.0
GRIPPER_CLOSE_POS_8 = -0.035


class MujocoRobotEnv(gym.Env):
    def __init__(
        self,
        sim_steps=10,
        render_mode="rgb_array",
        log_interval=1024,
        capture_interval=None,
        max_step=50000,
    ):
        self.log_interval = log_interval
        self.capture_interval = capture_interval
        self.max_step = max_step
        model_path = os.path.join(
            "./src/piper_description", "mujoco_model", "piper_description.xml"
        )
        model_path = os.path.abspath(model_path)
        self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)

        self.render_mode = render_mode
        if self.render_mode:
            self.renderer = mujoco.Renderer(self.model)
            self.cam = mujoco.MjvCamera()
            # 视距，拉远看整个机械臂
            self.cam.distance = 2.0

        self.sim_steps = sim_steps
        self.step_counter = 0
        self.total_reward = 0
        self.first_catch_step = -1

        self.ee_site_name = "ee_site"
        self.actuator_ids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"joint{i+1}")
            for i in range(JOINT_NUM)
        ]
        # 两个夹爪的 ID
        self.joint7_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_JOINT, "joint7"
        )
        self.joint8_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_JOINT, "joint8"
        )
        self.target_pos = self.gen_target_pos()

        # 动作空间：6个关节增量
        self.action_space = gym.spaces.Box(
            low=np.array([-0.1] * (JOINT_NUM - 1) + [-0.05], dtype=np.float32),
            high=np.array([0.1] * (JOINT_NUM - 1) + [0.05], dtype=np.float32),
            dtype=np.float32,
        )

        # 观测空间：6个关节角度 + ee位置(xyz) + 目标点(xyz)
        self.observation_space = gym.spaces.Box(
            low=np.array(
                JOINTLOWERLIMIT + [-np.inf] * 6,
                dtype=np.float32,
            ),
            high=np.array(
                JOINTUPPERLIMIT + [np.inf] * 6,
                dtype=np.float32,
            ),
            dtype=np.float32,
        )

    def _get_obs(self):
        joint_angles = self.data.qpos[:JOINT_NUM].copy()
        ee_pos = self.data.site(self.ee_site_name).xpos.copy()
        return np.concatenate(
            [
                joint_angles,
                ee_pos,
                self.target_pos,
            ]
        ).astype(np.float32)
        # return self.target_pos

    def reset(self, seed=None, options=None):
        mujoco.mj_resetData(self.model, self.data)
        self.step_counter = 0
        self.total_reward = 0
        self.first_catch_step = -1
        # 设置目标随机化
        self.target_pos = self.gen_target_pos()
        return self._get_obs(), {}

    def ctrl_gripper(self, close=True):
        if close:
            self.data.ctrl[self.joint7_id] = GRIPPER_CLOSE_POS_7
            self.data.ctrl[self.joint8_id] = GRIPPER_CLOSE_POS_8
        else:
            self.data.ctrl[self.joint7_id] = GRIPPER_OPEN_POS_7
            self.data.ctrl[self.joint8_id] = GRIPPER_OPEN_POS_8
        for _ in range(self.sim_steps):
            mujoco.mj_forward(self.model, self.data)
            mujoco.mj_step(self.model, self.data)

    def step(self, action):
        self.step_counter += 1

        # 限制动作范围（安全起见）
        # action = np.clip(action, self.action_space.low, self.action_space.high)

        reward = 0
        # 防止action过于接近边界，[0~0.5]->[0~9.7*6]惩罚力度
        # reward -= np.sum(
        #     10000
        #     * np.abs(
        #         self.norm(action, self.action_space.low, self.action_space.high) - 0.5
        #     )
        #     ** 10
        # )
        for i in range(JOINT_NUM):
            qpos = self.data.qpos[self.actuator_ids[i]] + action[i]
            self.data.ctrl[self.actuator_ids[i]] = np.clip(
                qpos,
                JOINTLOWERLIMIT[i],
                JOINTUPPERLIMIT[i],
            )
            # 关节限制惩罚，防止关节超过可转动范围
            reward -= 10.0 * abs(self.data.ctrl[self.actuator_ids[i]] - qpos)
        # 直接修改qpos但不修改ctrl，相当于让关节瞬移到目标位置
        # 但仿真器又仿真ctrl它回到原点，所以每步step都几乎没动
        # self.data.qpos[:JOINT_NUM] = qpos

        for _ in range(self.sim_steps):
            mujoco.mj_forward(self.model, self.data)
            mujoco.mj_step(self.model, self.data)

        obs = self._get_obs()
        assert np.all(np.isfinite(obs)), f"Invalid observation: {obs}"

        ee_pos = self.data.site(self.ee_site_name).xpos.copy()
        dist = np.linalg.norm(ee_pos - self.target_pos)
        # dist(0 ~ 2) -> reward(20 ~ 0)
        reward += np.exp(-4.0 * dist + 3.0)
        # if dist < 0.1:
        #     # 越接近目标越鼓励小action
        #     reward -= np.linalg.norm(action[:JOINT_NUM]) / dist
        # 阈值定太大了容易鼓励瞎碰：来回动直到刚好碰到目标范围
        if dist < 0.02:
            self.ctrl_gripper(close=True)
            # reward += action[JOINT_NUM] * 20.0
            if self.float_equal(
                self.data.qpos[self.joint7_id], GRIPPER_CLOSE_POS_7
            ) and self.float_equal(self.data.qpos[self.joint8_id], GRIPPER_CLOSE_POS_8):
                reward += 100.0
                catched = True
                if self.first_catch_step == -1:
                    self.first_catch_step = self.step_counter
            else:
                catched = False
        else:
            # reward -= action[JOINT_NUM] * 20.0
            catched = False
        if self.capture_interval and (
            self.step_counter % self.capture_interval == 0 or catched
        ):
            cv2.imwrite(f"videos/{self.step_counter}.png", self.render())
        # reward -= self.step_counter / self.max_step * 100.0
        # 训练其即使到达目标点也不停止，要在max_step内最大化奖励，鼓励其一直留在目标点附近
        if self.step_counter >= self.max_step:
            done = True
        else:
            done = False
        self.total_reward += reward
        if self.step_counter % self.log_interval == 0 or done:
            print(
                f"\n"
                + f"🤖 当前步数: {self.step_counter}\n"
                + f"📍 末端位置: x={ee_pos[0]:.3f}, y={ee_pos[1]:.3f}, z={ee_pos[2]:.3f}\n"
                + f"🎯 目标点:  x={self.target_pos[0]:.3f}, y={self.target_pos[1]:.3f}, z={self.target_pos[2]:.3f}\n"
                + f"📏 当前距离: {dist:.4f} m\n"
                + f'🤖 当前action: {[f"{i:.3f}" for i in action]}\n'
                + f'🤖 当前关节: {[f"{i:.3f}" for i in self.data.qpos[:JOINT_NUM]]}\n'
                + f"💰 当前/总奖励: {reward:.4f} / {self.total_reward:.4f}, 步均奖励: {self.total_reward/self.step_counter:.4f}\n"
                + (
                    f"✅ 成功抓取! 第{self.first_catch_step}步首次抓取\n"
                    if catched
                    else ""
                )
                + (
                    f"❌ 达到最大步数{self.max_step}, 第{self.first_catch_step}步首次抓取\n"
                    if done
                    else ""
                )
            )
        return obs, reward, done, False, {}

    def render(self):
        if self.render_mode == "rgb_array":
            self.renderer.update_scene(self.data, camera=self.cam)
            return self.renderer.render()
        elif self.render_mode == "human":
            if not hasattr(self, "viewer"):
                self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self.viewer.sync()
        else:
            raise ValueError("Invalid render mode. Use 'rgb_array' or 'human'.")

    @staticmethod
    def float_equal(a, b, epsilon=1e-4):
        return abs(a - b) < epsilon

    @staticmethod
    def gen_target_pos():
        return np.random.uniform(low=[0.0, -0.5, 0.2], high=[0.5, 0.5, 0.5])
        # return np.random.uniform(low=[-0.5, -0.5, 0.15], high=[0.5, 0.5, 0.5])

    @staticmethod
    def norm(a, low, high):
        return (a - low) / (high - low)
