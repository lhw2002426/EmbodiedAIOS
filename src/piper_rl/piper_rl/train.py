import os
import numpy as np
from gymnasium.wrappers import RecordVideo
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from piper_rl_gazebo_node import GazeboRobotEnv
from piper_rl_mujoco import MujocoRobotEnv
import time


def decay_schedule(initial_value):
    def func(progress_remaining):
        return initial_value * (progress_remaining)

    return func


def train():
    if args.gazebo:
        env = GazeboRobotEnv()
    else:
        env = MujocoRobotEnv()
        # env = MujocoRobotEnv(capture_interval=1024 * 100)
        if args.train_record:
            video_dir = "./videos/"
            env = RecordVideo(
                env,
                video_folder=video_dir,
                episode_trigger=lambda e: e % 10 == 0,
                video_length=5000,
            )
    model = PPO(
        policy="MlpPolicy",
        env=env,
        policy_kwargs=dict(
            net_arch=[256, 128],
            log_std_init=-3.0,
            ortho_init=True,
        ),
        learning_rate=decay_schedule(1e-4),
        batch_size=256,
        n_steps=1024,
        gamma=0.99,
        verbose=1,
        ent_coef=1e-2,  # 不能太高，否则std会变大，策略会变得不稳定
        tensorboard_log="./ppo_logs/",
    )
    # model.set_parameters("ppo_models/piper_rl_checkpoint_3900000_steps.zip")

    checkpoint_callback = CheckpointCallback(
        save_freq=100000, save_path="./ppo_models/", name_prefix="piper_rl_checkpoint"
    )

    model.learn(total_timesteps=1000 * 1000 * 10, callback=checkpoint_callback)

    model.save("ppo_piper_final")
    print("✅ 模型训练完成，已保存为 ppo_piper_final.zip")


def test():
    if args.gazebo:
        env = GazeboRobotEnv()
    else:
        env = MujocoRobotEnv()
    model = PPO.load("ppo_piper_final_maximize_z")
    obs = env.reset()
    for epoch in range(100000):
        # time.sleep(1)
        action, _ = model.predict(obs)
        obs, reward, done, _ = env.step(action)

        # print(f"epoch {epoch}, Reward:", reward)
        if done:
            print("🎉 成功抓取，重新开始")
            obs = env.reset()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="测试训练好的策略")
    parser.add_argument("--gazebo", action="store_true", help="使用mujoco仿真")
    parser.add_argument(
        "--train_record",
        default=True,
        action="store_true",
        help="训练时定时录制训练过程",
    )
    args = parser.parse_args()

    if args.test:
        test()
    else:
        train()
