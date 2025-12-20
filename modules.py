import cv2
import numpy as np
from scipy.interpolate import splprep, splev

from matplotlib.path import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches


import yaml
import os
import re

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

np.random.seed(config["seed"])  # 固定随机种子，便于复现结果

class Capsule:
    def __init__(self, x, y, 
                 v_active=config["capsule"]["v_active"], 
                 D_trans=config["capsule"]["D_trans"], 
                 D_rot=config["capsule"]["D_rot"],
                 v_grav=config["capsule"]["v_grav"]):
        """
        初始化微球
        :param x: 初始 X 坐标
        :param y: 初始 Y 坐标
        :param v_active: 活性推进速度 (由 CaCO3 反应产生) 
        :param D_trans: 平动扩散系数 (模拟布朗运动强度)
        :param D_rot: 转动扩散系数 (模拟朝向的随机改变)
        """
        # 位置向量
        self.pos = np.array([x, y], dtype=float)
        
        # 随机初始朝向 (0 到 2pi)
        self.theta = np.random.uniform(0, 2 * np.pi)
        
        # 状态机：free (游离), attached (粘附), exited (排出)
        self.status = 'free'
        
        # 物理参数
        self.v_active = v_active
        self.D_trans = D_trans
        self.D_rot = D_rot
        self.v_grav = v_grav  # 重力导致的沉降速度
        
        # 记录是否已经进入过胃（防止贲门反流）
        self.entered_stomach = False

    def update(self, dt, stomach_sdf_func):
        """
        更新微球状态的核心算法
        :param dt: 时间步长
        :param stomach_sdf_func: 胃部环境的符号距离函数 (Signed Distance Function)
                                 输入 (x,y)，返回距离边界的距离。
                                 负值表示在内部，正值表示在外部/碰撞。
        """
        # 1. 如果已经粘附或排出，不再更新位置
        if self.status != 'free':
            return

        # ---------------------------------------------------------
        # 物理引擎：Langevin 方程
        # ---------------------------------------------------------
        
        # A. 更新朝向
        
        rot_noise = np.random.normal(0, np.sqrt(2 * self.D_rot * dt))
        self.theta += rot_noise

        # B. 计算位移向量
        # 主动推进 
        dx_active = self.v_active * np.cos(self.theta) * dt
        dy_active = self.v_active * np.sin(self.theta) * dt
        
        # 随机热运动 
        # 标准差 sigma = sqrt(2 * D * dt)
        trans_noise_scale = np.sqrt(2 * self.D_trans * dt)
        dx_brownian = np.random.normal(0, trans_noise_scale)
        dy_brownian = np.random.normal(0, trans_noise_scale)

        # 重力沉降分量
        dy_gravity = -self.v_grav * dt
        
        # 综合位移
        displacement = np.array([dx_active + dx_brownian, 
                                 dy_active + dy_brownian + dy_gravity])
        
        # 预测下一步位置
        old_pos = self.pos.copy()
        next_pos = self.pos + displacement
        
        # ---------------------------------------------------------
        # 边界检测与粘附 
        # ---------------------------------------------------------
        
        # 调用SDF函数，检测新位置与胃壁的关系
        # dist < 0: 在胃内; dist > 0: 撞墙
        dist_old, _ = stomach_sdf_func(old_pos[0], old_pos[1])
        dist, location_type = stomach_sdf_func(next_pos[0], next_pos[1])


        if location_type == 'wall_boundary' and dist >= -0.05: 
            # 碰撞胃壁
            self.status = 'attached'
            # 修正位置贴在表面，防止穿模
            self.pos = next_pos 
            return
            
        elif dist_old < 0 and location_type == 'pylorus_exit':
            # 从幽门排出
            self.status = 'exited'
            self.pos = next_pos
            return
        
        elif location_type == 'cardia_exit':
            if not self.entered_stomach:
                # 第一次从贲门进入胃 → 允许
                self.entered_stomach = True
                self.pos = next_pos
            else:
                # 禁止反流
                # 反弹 + 改变方向
                self.theta += np.pi + np.random.normal(0, 0.3)
                return    
        
        elif dist < 0:
            # 正常在胃内运动
            self.pos = next_pos
            
        else:
            # 穿模，回退一步，并随机反弹
            self.theta += np.pi + np.random.normal(0, 0.5) 

    def get_color(self):
        """根据状态返回颜色"""
        if self.status == 'free':
            return 'blue'
        elif self.status == 'attached':
            return 'red'
        else:
            return 'purple'
        
        

def build_stomach_sdf_from_image(
    image_path,
    x_range=(-10, 10),
    y_range=(-8, 8),
    pylorus_line=None,
    cardia_line=None,
    smooth=True,
    smooth_points=400,
    return_contour=False
):
    """
    从黑白胃剪影图像构造 Signed Distance Function (SDF)

    返回:
        stomach_sdf(x, y) -> (signed_distance, location_type)
    """


    # 读取 & 二值化

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("无法读取胃部剪影图像")

    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)


    # 提取最大轮廓

    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE
    )

    if len(contours) == 0:
        raise ValueError("未检测到胃轮廓")

    contour = max(contours, key=cv2.contourArea)
    pts = contour.squeeze()


    # 像素坐标 → 物理坐标

    h, w = img.shape
    pts_physical = np.zeros_like(pts, dtype=float)

    pts_physical[:, 0] = (
        pts[:, 0] / w * (x_range[1] - x_range[0]) + x_range[0]
    )

    pts_physical[:, 1] = (
        (h - pts[:, 1]) / h * (y_range[1] - y_range[0]) + y_range[0]
    )

    if smooth:
        tck, _ = splprep(pts_physical.T, s=0.5, per=True)
        u_new = np.linspace(0, 1, smooth_points)
        x_s, y_s = splev(u_new, tck)
        pts_physical = np.vstack([x_s, y_s]).T


    # 构造 Path 对象

    stomach_path = Path(pts_physical)


    # 距离计算函数

    def point_to_segment_dist(p, a, b):
        ap = p - a
        ab = b - a
        t = np.clip(np.dot(ap, ab) / np.dot(ab, ab), 0, 1)
        closest = a + t * ab
        return np.linalg.norm(p - closest)

    def distance_to_contour(x, y):
        p = np.array([x, y])
        min_dist = np.inf

        for i in range(len(pts_physical)):
            a = pts_physical[i]
            b = pts_physical[(i + 1) % len(pts_physical)]
            d = point_to_segment_dist(p, a, b)
            if d < min_dist:
                min_dist = d

        return min_dist

    # 门判定通用函数
    
    def is_across_manual_line(x, y, line):
        """
        判断点是否位于指定直线的“外侧”
        """
        p = np.array([x, y])
        p0 = np.array(line["point"])
        n = np.array(line["normal"])
        v = p - p0
        
        return np.dot(v, n) > 0


    
    # 最终 SDF 函数
    def stomach_sdf(x, y):
        dist = distance_to_contour(x, y)
        inside = stomach_path.contains_point((x, y))

        if inside:
            signed_dist = -dist
            location_type = 'inside'
        else:
            signed_dist = dist
            location_type = 'wall_boundary'

        # 门判定
        if not inside and is_across_manual_line(x, y, cardia_line):
            location_type = 'cardia_exit'   

        elif not inside and is_across_manual_line(x, y, pylorus_line):
            location_type = 'pylorus_exit'

        return signed_dist, location_type

    return stomach_sdf, pts_physical
    
# 吞服注入器

def inject_capsules_near_cardia(
    num,
    cardia_line,
    spread,
    offset,
    v_active=0
):
    """
    在贲门线外侧注入粒子（模拟吞服）
    """
    capsules = []

    # 进入胃的方向
    normal = cardia_line["normal"]* -1
    normal = normal / np.linalg.norm(normal)
    inward_dir = normal  # 指向胃内

    # 直线方向
    tangent = np.array([-normal[1], normal[0]])

    for _ in range(num):
        # 沿直线方向随机分布
        s = np.random.uniform(-spread, spread)
        pos = (
            cardia_line["point"]
            + s * tangent
            + offset * inward_dir
        )

        cap = Capsule(pos[0], pos[1])
        cap.theta = np.arctan2(inward_dir[1], inward_dir[0])
        cap.entered_stomach = False

        if v_active != 0:
            cap.v_active = v_active

        capsules.append(cap)

    return capsules


def plot_particles(particles,
                   stomach_outline=None,
                   cardia_line=None,
                   pylorus_line=None,
                   step=None,
                   save_path=None):
    fig, ax = plt.subplots(figsize=(8, 6))

    # 胃壁轮廓

    if stomach_outline is not None:
        ax.plot(
            stomach_outline[:, 0],
            stomach_outline[:, 1],
            color='black',
            linewidth=2,
            label='Stomach Wall'
        )

    # 贲门线

    if cardia_line is not None:
        p = cardia_line["point"]
        d = cardia_line["direction"]
        t = np.linspace(-10, 10, 100)

        ax.plot(
            p[0] + t * d[0],
            p[1] + t * d[1],
            linestyle='--',
            color='green',
            linewidth=1.5,
            label='Cardia (Inlet)'
        )


    # 幽门线

    if pylorus_line is not None:
        p = pylorus_line["point"]
        d = pylorus_line["direction"]
        t = np.linspace(-10, 10, 100)

        ax.plot(
            p[0] + t * d[0],
            p[1] + t * d[1],
            linestyle='--',
            color='red',
            linewidth=1.5,
            label='Pylorus (Exit)'
        )


    # 粒子分类

    x_free, y_free = [], []
    x_att, y_att = [], []
    x_exit, y_exit = [], []

    for p in particles:
        if p.status == 'free':
            x_free.append(p.pos[0])
            y_free.append(p.pos[1])
        elif p.status == 'attached':
            x_att.append(p.pos[0])
            y_att.append(p.pos[1])
        elif p.status == 'exited':
            x_exit.append(p.pos[0])
            y_exit.append(p.pos[1])


    # 绘制散点

    ax.scatter(x_free, y_free,
               c='blue', s=10, alpha=0.5, label='Free')

    ax.scatter(x_att, y_att,
               c='red', s=15, alpha=0.8, label='Attached')

    ax.scatter(x_exit, y_exit,
               c='purple', s=15, alpha=0.8, label='Exited')


    ax.set_aspect('equal')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(f'Distribution of Capsules Step {step}')
    ax.legend()
    ax.grid(alpha=0.3)

    # 自动缩放胃壁范围
    if stomach_outline is not None:
        xmin, ymin = stomach_outline.min(axis=0)
        xmax, ymax = stomach_outline.max(axis=0)
        ax.set_xlim(xmin - 0.5, xmax + 0.5)
        ax.set_ylim(ymin - 0.5, ymax + 0.5)

    if save_path == None:
        plt.show()
    else:
        dirpath = os.path.dirname(save_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        plt.savefig(save_path)
        # 释放内存
        plt.close(fig)
        

def images_to_video(input_dir, output_dir, fps=24, output_name='output_video.mp4'):


    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 获取所有 png 图片并按数字顺序排序
    files = [f for f in os.listdir(input_dir) if f.endswith('.png')]
    files.sort(key=lambda f: int(re.sub(r'\D', '', f)))
    
    if not files:
        print("错误：未在 ./tmp 目录下找到图片。")
        return

    # 读取第一张图片以获取分辨率（宽, 高）
    first_img_path = os.path.join(input_dir, files[0])
    frame = cv2.imread(first_img_path)
    height, width, layers = frame.shape
    size = (width, height)

    # 视频写入器使用 mp4v 编码器，输出为 .mp4 格式
    out_path = os.path.join(output_dir, output_name)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    video = cv2.VideoWriter(out_path, fourcc, fps, size)

    print(f"正在合成视频，共 {len(files)} 帧...")

    # 逐帧写入视频
    for file in files:
        img_path = os.path.join(input_dir, file)
        img = cv2.imread(img_path)
        video.write(img)

    # 释放内存
    video.release()
    print(f"视频合成成功！已保存至: {out_path}")
