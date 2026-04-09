import matplotlib.pyplot as plt
import numpy as np
import platform

# ==========================================
# 1. 数据准备
# ==========================================
models = ['智能体', 'DeepSeek', 'Kimi', '豆包']
accuracies = [100.00, 95.00, 99.94, 99.85]
colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']  # 绿、蓝、橙、红

# ==========================================
# 2. 字体设置 (自动适配 Windows/Mac/Linux)
# ==========================================
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei'] # 优先用微软雅黑
elif system_name == "Darwin": # Mac
    plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial Unicode MS']
else: # Linux
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

# ==========================================
# 3. 绘图逻辑
# ==========================================
plt.figure(figsize=(10, 6)) # 设置画布大小

# 绘制柱状图
bars = plt.bar(models, accuracies, color=colors, width=0.5)

# 设置标题和轴标签
plt.title('各模型故障诊断准确度', fontsize=16, pad=20)
plt.xlabel('模型名称', fontsize=12)
plt.ylabel('准确度 (%)', fontsize=12)

# 设置 Y 轴范围 (80%-105% 以便突显差异，或者 0-110 全貌)
plt.ylim(90, 105) # 这里我设置从 90 开始，因为数据都很高，这样差异更明显
# 如果想从 0 开始，请改为: plt.ylim(0, 110)

# ==========================================
# 4. 添加数值标签 (在柱子上方显示具体百分比)
# ==========================================
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2, height + 0.5, 
             f'{height:.2f}%', 
             ha='center', va='bottom', fontsize=11, fontweight='bold')

# 添加网格线 (仅 Y 轴)
plt.grid(axis='y', linestyle='--', alpha=0.3)

# 显示图表
plt.tight_layout()
plt.show()