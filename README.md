# Capsule-in-Stomach Simulation

本项目使用 Python 构建了一个二维物理模拟模型，用于模拟微型胶囊在胃内的运动、碰壁粘附以及经幽门排出的全过程，并支持将粒子运动过程自动生成视频。

---

## 一、建模背景

假设一种口服药物载体为微型球形胶囊，其表面部分涂有碳酸钙，可与胃酸反应产生气体推进效果，从而使胶囊在胃内运动更加剧烈。胶囊在与胃壁接触后会发生粘附，若未粘附则可能经幽门排出。

## 二、主要功能

- 胶囊粒子类（`Capsule`），包含完整状态机：
  - `free`（游离）
  - `attached`（胃壁粘附）
  - `exited`（经幽门排出）
- 基于SDF的边界判定 (Signed Distance Function，符号距离场函数)
- 从黑白胃剪影图像中提取胃壁轮廓
- 手动配置贲门线与幽门线
- 支持一次性吞入粒子群
- 自动停止条件：当不存在 `free` 状态粒子时终止模拟
- 过程可视化：自动合成为 MP4 视频



## 三、项目结构

```bash
├── main.py               # 主程序入口 
├── module.py             # 核心模块，包含 Capsule 类，剪影转胃壁 SDF 函数，视频合成函数等
├── graphmod.py           # 画图专用函数
├── simple.py             # 测试核心模块
├── graph.py              # 测试画图模块
├── simplemod.py          # 简单测试专用函数
├── config.yaml           # 参数配置文件
├── stomach.png           
├── ./video
│ └── capsule_motion.mp4  # 输出视频
├── ./tmp                 # 帧暂存目录 
│ └── 0.png
│ └── 1.png
│ └── ...
└── README.md
```

---

## 四、核心建模思想

### 1. 粒子动力学

胶囊运动由简化的朗之万 (Langevin) 方程描述：

- 主动推进项
- 平动扩散项（布朗运动）
- 转动扩散项（随机改变朝向）

每个时间步更新胶囊位置与朝向。

---

### 2. 胃壁模型

- 从黑白胃剪影图中提取轮廓点
- 使用最近距离 / 符号距离判断粒子是否接触胃壁

---

### 3. 贲门与幽门建模

- 使用 **点 + 法向量（normal）** 表示边界
- `normal` 用于内外判定
- 贲门：
  - 只允许粒子从外进入
  - 防止反流
- 幽门：
  - 粒子越过后状态变为 `exited`

---

### 4. 自动终止条件

当系统中不存在 `free` 状态粒子时，说明所有胶囊已完成物理过程 (粘附或排出), 模拟自动终止

---

## 五、运行

### 1. 环境依赖

```bash
pip install -r requirements.txt

# 建议创建虚拟环境，防止依赖冲突
# 测试使用uv管理虚拟环境，python版本3.14

pip install uv # 已安装uv可忽略

uv venv --python=3.14

# 激活环境（macOS/Linux）
source .venv/bin/activate

# 激活环境（Windows）
.venv\Scripts\activate

uv pip install -r requirements.txt

# 重要：本项目依赖 opencv，安装时编译 numpy==2.2.6 ，需确保相关编译器正常！(Windows 安装 Visual Studio)
```

---

### 2. 运行模拟并生成视频

```bash
python main.py
```

---

## 六、主要配置

`config.yaml`

| 参数           | 含义     |
| ---------------| -------- |
| `dt`           | 单步时间长度    |
| `total_steps`  | 最大模拟步数    |
| `step_interval`| 每多少步保存一帧 |
| `v_active`     | 胶囊主动推进速度 |
| `D_trans`      | 平动扩散系数     |
| `D_rot`        | 转动扩散系数     |
| `v_grav`       | 重力导致的沉降速度     |



## 七、结果示例

视频中不同颜色表示不同状态：

* 🔵 蓝色：游离（free）
* 🔴 红色：粘附（attached）
* 🟣 紫色：排出（exited）

---

## 八、可扩展方向

* 引入胃蠕动（时间变化的胃壁）
* 粘附概率模型（非确定性）
* 多粒子相互作用
* 三维模型扩展

## 九、可能的Bugs

* 注入速度慢可能会反流
* 排出标记失效