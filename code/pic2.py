import matplotlib.pyplot as plt
import numpy as np
import platform

# ==========================================
# 1. 数据准备 (保持数值完全一致)
# ==========================================
models = ['智能体', 'Kimi', '豆包', '文心一言', 'DeepSeek']
scores = [73.3, 62.0, 60.1, 59.6, 59.2]

# 定义5种不同的颜色 (您可以根据喜好修改这些十六进制颜色码)
# 顺序：蓝、绿、橙、红、紫
colors = ['#4aa3f0', '#5aca75', '#f6bd16', '#e86452', '#9f7aea']

# ==========================================
# 2. 字体设置 (自动适配系统，防止中文乱码)
# ==========================================
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
elif system_name == "Darwin": # Mac
    plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial Unicode MS']
else:
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 3. 绘图逻辑
# ==========================================
plt.figure(figsize=(10, 6)) # 设置画布大小，保持原图比例

# 绘制柱状图 (设置宽度和颜色)
bars = plt.bar(models, scores, color=colors, width=0.55, zorder=3)

# 设置标题和标签
plt.title('各模型故障诊断回复与标准答案的语义相似度对比', fontsize=14, pad=15)
plt.xlabel('模型名称', fontsize=12)
plt.ylabel('语义相似度 (Score)', fontsize=12)

# 设置 Y 轴范围 (0 到 100)
plt.ylim(0, 100)

# 添加 Y 轴虚线网格 (zorder=0 确保网格在柱子后面)
plt.grid(axis='y', linestyle='--', alpha=0.4, color='#cccccc', zorder=0)

# ==========================================
# 4. 添加数值标签 (在柱子上方显示具体数值)
# ==========================================
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2, height + 1.5, 
             f'{height}', 
             ha='center', va='bottom', fontsize=11, color='black')

# 调整布局
plt.tight_layout()

# 显示图表
plt.show()