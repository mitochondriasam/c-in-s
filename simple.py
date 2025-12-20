import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches

import yaml

from modules import *
from simplemod import *

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# ==========================================
# 主循环 (Main Loop)
# ==========================================
def main():
    # --- 初始化 ---
    num_particles = config["iter"]["num_particles"] # 微球数量
    dt = config["iter"]["dt"]           # 时间步长
    total_steps = config["iter"]["total_steps"]  # 总模拟步数
    
    # 微球初始位置中心
    loc_x = config["capsule"]["simple"]["x"]
    loc_y = config["capsule"]["simple"]["y"]

    exit_x = config["simple_ellipse"]["exit_x"]

    np.random.seed(config["seed"])  # 固定随机种子，便于复现结果
    
    # 在中心生成粒子群
    particles = [Capsule(x=loc_x + np.random.normal(0, 1), 
                         y=loc_y + np.random.normal(0, 1)) for _ in range(num_particles)]

    print(f"开始模拟: {num_particles} 个微球, {total_steps} 步...")
    print(f"出口位于X > {exit_x} cm 的区域")

    # 时间循环
    for t in range(total_steps):
        for p in particles:
            p.update(dt, stomach_simple_ellipse)

    # 结果可视化
    plot_results(particles)

if __name__ == "__main__":
    main()