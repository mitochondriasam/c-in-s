import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.interpolate import splprep, splev
from matplotlib.path import Path

import yaml

from modules import *
from graphmod import *

import matplotlib.animation as animation
from tqdm import tqdm

with open("config.yaml", 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

def normal_to_direction(normal):
    n = np.asarray(normal, dtype=float)
    n = n / np.linalg.norm(n)  
    return np.array([-n[1], n[0]])


def plot_init():
    cardia_line = {
        "point": np.array(config["stomach"]["cardia_line"]["point"]),    # 胃的左上入口附近（手动调）
        "normal": np.array(config["stomach"]["cardia_line"]["normal"])    # 指向“胃外（食管方向）”
    }

    pylorus_line = {
        "point": np.array(config["stomach"]["pylorus_line"]["point"]),
        "normal": np.array(config["stomach"]["pylorus_line"]["normal"])
    }

    if config["draw"]["parse_switch"]:
        stomach_sdf, contour_pts = build_stomach_sdf_from_image(
            image_path=config["draw"]["image_path"],
            x_range=config["draw"]["x_range"],
            y_range=config["draw"]["y_range"],
            pylorus_line = pylorus_line,
            cardia_line = cardia_line,
            return_contour=config["draw"]["return_contour"]
        )
    if config["draw"]["return_contour"]:
        plot_stomach_contour(
            contour_pts,
            show_points=False
        )

    plot_stomach_with_cardia_and_pylorus(
        contour_pts=contour_pts,
        cardia_line=cardia_line,
        pylorus_line=pylorus_line
    )
    
    return stomach_sdf, contour_pts

def main():
    # --- 初始化 ---
    num_particles = config["iter"]["num_particles"] # 微球数量
    dt = config["iter"]["dt"]           # 时间步长
    total_steps = config["iter"]["total_steps"]  # 总模拟步数
    
    particles = []

    # -------- 一次性吞服 --------
    particles = inject_capsules_near_cardia(
    num=num_particles,
    cardia_line=cardia_line,
    spread=spread,
    offset=offset,
    v_active=config["capsule"]["v_active"]
    )

    plot_interval = config["iter"]["plot_interval"]
    
    for p in particles:
        p.entered_stomach = True
    
    with tqdm(total=total_steps, desc="Simulating") as pbar:
        picorder = 0
        
        for step in range(total_steps):
        # -------- 更新所有胶囊 --------
            active = 0
            for p in particles:
                if p.status == 'free':
                    p.update(dt, sdf)
                    active += 1
            pbar.set_postfix(
            free=active,
            total=len(particles)
            )
            pbar.update(1)
            
            if step % plot_interval == 0:
                plot_particles(
                    particles,
                    stomach_outline=pts,
                    cardia_line=cardia_line,
                    pylorus_line=pylorus_line,
                    step=step,
                    save_path=config["draw"]["temp_path"]+f"/{picorder}.png"
                )
                picorder += 1
            if all(p.status != 'free' for p in particles):
                break


if __name__ == "__main__":
    cardia_line = {
        "point": np.array(config["stomach"]["cardia_line"]["point"]),    
        "normal": np.array(config["stomach"]["cardia_line"]["normal"]),   
        "direction": normal_to_direction(config["stomach"]["cardia_line"]["normal"])
    }
    pylorus_line = {
        "point": np.array(config["stomach"]["pylorus_line"]["point"]),
        "normal": np.array(config["stomach"]["pylorus_line"]["normal"]),
        "direction": normal_to_direction(config["stomach"]["pylorus_line"]["normal"])
    }
    spread = config["capsule"]["injection"]["spread"]
    offset = config["capsule"]["injection"]["offset"]

    save_path = input_dir = config["draw"]["temp_path"]
    
    sdf, pts = plot_init()
    main()
    
    
    output_dir = config["draw"]["video_path"]
    fps = config["draw"]["fps"]
    output_name = config["draw"]["video_name"]
    images_to_video(input_dir, output_dir, fps, output_name)


