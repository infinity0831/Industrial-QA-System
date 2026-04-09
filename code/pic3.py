import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform

# ==========================================
# 1. 数据准备
# ==========================================
data = {
    'API': ['DeepSeek-R1', 'DeepSeek-R1', 'Kimi-K2-Thinking', 'Kimi-K2-Thinking', 
            'Hunyuan-A13B-Instruct', 'Hunyuan-A13B-Instruct', 
            'Qwen3-Next-80B-A3B-Thinking', 'Qwen3-Next-80B-A3B-Thinking'],
    'Status': ['有工具库', '无工具库', '有工具库', '无工具库', 
               '有工具库', '无工具库', '有工具库', '无工具库'],
    'Score': [100.00, 95.00, 99.96, 94.12, 98.56, 92.58, 99.41, 94.29] 
}
df = pd.DataFrame(data)

# ==========================================
# 2. 可视化绘制
# ==========================================

# --- A. 全局字体设置 ---
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 9 

# --- B. 中文字体设置 ---
system = platform.system()
if system == "Windows":
    font_path = "C:/Windows/Fonts/simsun.ttc"
elif system == "Darwin":
    font_path = "/System/Library/Fonts/STSong.ttc"
else:
    font_path = "/usr/share/fonts/truetype/arphic/uming.ttc"

try:
    cn_font = fm.FontProperties(fname=font_path, size=9)
except:
    cn_font = None 

# --- 数据准备 ---
apis = df['API'].unique()
x = np.arange(len(apis)) 
width = 0.35 

scores_on = df[df['Status'] == '有工具库']['Score'].values
scores_off = df[df['Status'] == '无工具库']['Score'].values

# --- 绘图 ---

# 保持双栏适配尺寸
plt.figure(figsize=(3.5, 3.0), dpi=300)

rects1 = plt.bar(x - width/2, scores_on, width, label='有工具库', color='#08306B', alpha=0.9, edgecolor='black', linewidth=0.5)
rects2 = plt.bar(x + width/2, scores_off, width, label='无工具库', color="#CCE6FF", alpha=0.9, edgecolor='black', linewidth=0.5)

# --- 细节调整 ---

plt.ylabel('准确率 (%)', fontproperties=cn_font, fontsize=9)

# 【核心修改 1】清理标签字符串
# 去掉所有用于"凑位置"的前后换行符，只保留必要的断行
# 这样每个标签的"几何中心"才是真实的中心
custom_labels = [
    "DeepSeek-R1",                    # 1行 (无需前后加 \n)
    "Kimi-K2-\nThinking",             # 2行
    "Hunyuan-\nA13B-Instruct",        # 2行
    "Qwen3-Next-\n80B-A3B-\nThinking" # 3行
]

# 【核心修改 2】设置垂直居中对齐逻辑
# 先获取当前的 Axes 对象
ax = plt.gca()

# 设置刻度位置和初始标签
ax.set_xticks(x)
ax.set_xticklabels(custom_labels, fontsize=8, rotation=0)

# 遍历每个标签对象进行精细调整
for label in ax.get_xticklabels():
    # 设为 center：让文字块的几何中心对齐参考点
    label.set_verticalalignment('center') 
    
    # 向下移动参考点位置
    # -0.12 是相对于Y轴高度的比例。
    # 您可以微调这个值：如果文字离轴太近就改成 -0.15，太远就改成 -0.10
    label.set_y(-0.07) 

plt.yticks(fontsize=9)
plt.ylim(80, 110) 

# 图例优化
plt.legend(prop=cn_font, loc='upper center', ncol=2, frameon=False, columnspacing=0.8, handletextpad=0.2) 

plt.grid(axis='y', linestyle='--', alpha=0.3)

# --- 自动标注数值 ---
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2., height + 0.5,
                 f'{height:.1f}',
                 ha='center', va='bottom',
                 fontsize=7,
                 color='black')

autolabel(rects1)
autolabel(rects2)

# 手动调整边距
# 这里的 bottom 可能需要根据您最终文字下移的程度微调，0.25 通常是安全的
plt.subplots_adjust(left=0.15, right=0.95, bottom=0.25, top=0.92)

# 保存
plt.savefig('two_column_center_aligned.png', dpi=300) 
plt.show()