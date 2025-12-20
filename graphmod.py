import numpy as np
import matplotlib.pyplot as plt


def plot_stomach_contour_with_lines(contour_pts, manual_line, type):
    """Canonical plotting function (single source of truth).
    Kept only once to avoid duplicates; other copies were removed.
    """
    fig, ax = plt.subplots(figsize=(6, 8))

    # 胃壁轮廓
    x = np.append(contour_pts[:, 0], contour_pts[0, 0])
    y = np.append(contour_pts[:, 1], contour_pts[0, 1])
    ax.plot(x, y, 'k-', linewidth=2, label='Stomach Wall')

    # 自动设置坐标范围
    xlim, ylim = get_axis_limits_from_contour(contour_pts, margin_ratio=0.05)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    # 画幽门贲门线
    plot_manual_line(ax, manual_line, label=type)

    ax.set_aspect('equal')
    ax.set_xlabel("X (cm)")
    ax.set_ylabel("Y (cm)")
    ax.set_title("Stomach Wall with Manual Pylorus Line")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)

    plt.show()
    
def plot_stomach_contour(
    contour_pts,
    pylorus_x=None,
    show_points=False,
    figsize=(6, 8)
):
    """
    绘制胃壁轮廓

    :param contour_pts: (N,2) 的胃壁轮廓点（物理坐标）
    :param pylorus_x: 幽门 x 位置（可选）
    :param show_points: 是否显示离散轮廓点
    """

    fig, ax = plt.subplots(figsize=figsize)

    # 闭合轮廓
    x = np.append(contour_pts[:, 0], contour_pts[0, 0])
    y = np.append(contour_pts[:, 1], contour_pts[0, 1])

    # 画轮廓线
    ax.plot(x, y, 'k-', linewidth=2, label='Stomach Wall')

    # 是否显示轮廓点
    if show_points:
        ax.scatter(contour_pts[:, 0], contour_pts[:, 1],
                   s=5, c='red', alpha=0.5, label='Contour Points')

    # 幽门位置
    if pylorus_x is not None:
        ax.axvline(pylorus_x, color='purple', linestyle='--',
                   label=f'Pylorus (x={pylorus_x})')

    ax.set_aspect('equal')
    ax.set_xlabel("X (cm)")
    ax.set_ylabel("Y (cm)")
    ax.set_title("Extracted Stomach Wall Contour")
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend()

    plt.show()

def find_pylorus_x_from_contour(contour_pts, percentile=95):
    """
    使用轮廓点的高分位 x 值作为幽门位置
    """
    x_vals = contour_pts[:, 0]
    return np.percentile(x_vals, percentile)

def plot_manual_line(ax, line, label, color="purple"):
    """
    在已有坐标轴上画幽门和贲门虚线
    """
    # 构造直线方向向量（与法向量垂直）
    n = line["normal"]
    direction = np.array([-n[1], n[0]])

    t = np.linspace(-20, 20, 100)
    line_pts = line["point"] + np.outer(t, direction)

    ax.plot(
        line_pts[:, 0],
        line_pts[:, 1],
        linestyle='--',
        color=color,
        linewidth=2,
        label=label
    )

def get_axis_limits_from_contour(contour_pts, margin_ratio=0.05):
    """
    根据胃壁轮廓自动计算绘图范围
    :param contour_pts: (N,2)
    :param margin_ratio: 边界留白比例
    """
    x_min, x_max = contour_pts[:, 0].min(), contour_pts[:, 0].max()
    y_min, y_max = contour_pts[:, 1].min(), contour_pts[:, 1].max()

    dx = x_max - x_min
    dy = y_max - y_min

    xlim = (x_min - margin_ratio * dx, x_max + margin_ratio * dx)
    ylim = (y_min - margin_ratio * dy, y_max + margin_ratio * dy)

    return xlim, ylim

def plot_stomach_with_cardia_and_pylorus(
    contour_pts,
    cardia_line,
    pylorus_line
):
    fig, ax = plt.subplots(figsize=(6, 8))

    # -------------------------
    # 胃壁轮廓
    # -------------------------
    x = np.append(contour_pts[:, 0], contour_pts[0, 0])
    y = np.append(contour_pts[:, 1], contour_pts[0, 1])
    ax.plot(x, y, 'k-', linewidth=2, label='Stomach Wall')

    # -------------------------
    # 自动裁剪坐标轴
    # -------------------------
    xlim, ylim = get_axis_limits_from_contour(contour_pts, margin_ratio=0.05)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    # -------------------------
    # 贲门线（入口）
    # -------------------------
    plot_manual_line(
        ax,
        cardia_line,
        label='Cardia (Inlet)',
        color='green'
    )

    # -------------------------
    # 幽门线（出口）
    # -------------------------
    plot_manual_line(
        ax,
        pylorus_line,
        label='Pylorus (Outlet)',
        color='purple'
    )

    # -------------------------
    # 统一图形风格
    # -------------------------
    ax.set_aspect('equal')
    ax.set_xlabel("X (cm)")
    ax.set_ylabel("Y (cm)")
    ax.set_title("Stomach Model with Manual Cardia & Pylorus Boundaries")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)

    plt.show()
