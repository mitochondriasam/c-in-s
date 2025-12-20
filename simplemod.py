import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import yaml

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
    
def stomach_simple_ellipse(x, y):
    """
    简化的椭圆胃部模型
    长轴 a, 短轴 b
    返回: (distance_proxy, location_type)
    """
    a, b = config["simple_ellipse"]["a"], config["simple_ellipse"]["b"]
    
    # 椭圆方程: (x/a)^2 + (y/b)^2 = 1
    # value < 1: 内部; value > 1: 外部
    normalized_dist_sq = (x / a) ** 2 + (y / b) ** 2
    
    # normalized_dist_sq - 1 作为距离的代理值
    # 避免计算欧几里得距离，速度快
    # < 0 : Inside
    # > 0 : Hit Boundary
    dist_proxy = normalized_dist_sq - 1.0
    
    location_type = 'inside'
    
    # 判定边界类型
    if dist_proxy >= -0.01: # 接近边界或穿过边界
        # 设定出口逻辑：假设出口在椭圆的最右端 (x > 9.5)
        if x > 9.5:
            location_type = 'pylorus_exit'
        else:
            location_type = 'wall_boundary'
            
    return dist_proxy, location_type

def plot_results(particles):
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 绘制容器边界 (椭圆)
    ellipse = patches.Ellipse((0, 0), 20, 12, angle=0, fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(ellipse)
    
    # 标记出口位置
    plt.axvline(x=config["simple_ellipse"]["exit_x"], color='red', linestyle='--', label=f'Pylorus Exit Line (X={config["simple_ellipse"]["exit_x"]} cm)')
    
    # 提取粒子数据
    x_free, y_free = [], []
    x_attached, y_attached = [], []
    x_exited, y_exited = [], []

    for p in particles:
        if p.status == 'free':
            x_free.append(p.pos[0])
            y_free.append(p.pos[1])
        elif p.status == 'attached':
            x_attached.append(p.pos[0])
            y_attached.append(p.pos[1])
        elif p.status == 'exited':
            x_exited.append(p.pos[0])
            y_exited.append(p.pos[1])

    # 绘制散点 (复刻参考图颜色)
    ax.scatter(x_free, y_free, c='blue', s=10, alpha=0.5, label='Free')
    ax.scatter(x_attached, y_attached, c='red', s=15, alpha=0.8, label='Attached')
    ax.scatter(x_exited, y_exited, c='purple', s=15, alpha=0.8, label='Exited')

    # 图表设置
    ax.set_xlim(-12, 14)
    ax.set_ylim(-8, 8)
    ax.set_title(f"Simulation Result (Simple Ellipse Model)")
    ax.set_xlabel("X (cm)")
    ax.set_ylabel("Y (cm)")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)
    
    plt.show()