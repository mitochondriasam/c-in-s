from modules import build_stomach_sdf_from_image
from graphmod import *
import numpy as np

import yaml

with open("config.yaml", 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

if config["draw"]["parse_switch"]:
    stomach_sdf, contour_pts = build_stomach_sdf_from_image(
        image_path=config["draw"]["image_path"],
        x_range=config["draw"]["x_range"],
        y_range=config["draw"]["y_range"],
        return_contour=config["draw"]["return_contour"]
    )
if config["draw"]["return_contour"]:
    plot_stomach_contour(
        contour_pts,
        show_points=False
    )


plot_stomach_contour_with_lines(
    contour_pts,
    manual_line = {
    "point": np.array(config["stomach"]["pylorus_line"]["point"]),   # 左下角移动
    "normal": np.array(config["stomach"]["pylorus_line"]["normal"])     # 控制斜率方向
},
    type="Pylorus Line"
)

plot_stomach_contour_with_lines(
    contour_pts,
    manual_line = {
    "point": np.array(config["stomach"]["cardia_line"]["point"]),   # 左下角移动
    "normal": np.array(config["stomach"]["cardia_line"]["normal"])     # 控制斜率方向
},
    type="Cardia Line"
)