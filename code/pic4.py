import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform

# ==========================================
# 1. 数据准备 (保持您的原数据不变)
# ==========================================
data = {
    'API': ['DeepSeek-R1', 'DeepSeek-R1', 'Kimi-K2-Thinking', 'Kimi-K2-Thinking', 
            'Hunyuan-A13B-Instruct', 'Hunyuan-A13B-Instruct', 
            'Qwen3-Next-80B-A3B-Thinking', 'Qwen3-Next-80B-A3B-Thinking'],
    'Status': ['有知识库', '无知识库', '有知识库', '无知识库', 
               '有知识库', '无知识库', '有知识库', '无知识库'],
    'Score': [67.2, 63.7, 68.9, 60.8, 67.9, 60.7, 65.1, 60.3] 
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

scores_on = df[df['Status'] == '有知识库']['Score'].values
scores_off = df[df['Status'] == '无知识库']['Score'].values

# --- 绘图 ---

# 【修改点 1】设置双栏适配尺寸 (宽度3.5英寸，高度3.0英寸)
plt.figure(figsize=(3.5, 3.0), dpi=300)

# 颜色保持您指定的深蓝 (#08306B) 和 浅蓝 (#CCE6FF)
rects1 = plt.bar(x - width/2, scores_on, width, label='有知识库', color='#08306B', alpha=0.9, edgecolor='black', linewidth=0.5)
rects2 = plt.bar(x + width/2, scores_off, width, label='无知识库', color="#CCE6FF", alpha=0.9, edgecolor='black', linewidth=0.5)

# --- 细节调整 ---

plt.ylabel('语义相似度 (%)', fontproperties=cn_font, fontsize=9)

# 【修改点 2】清理标签字符串 (去除原有的换行逻辑，交由下方代码自动对齐)
custom_labels = [
    "DeepSeek-R1", 
    "Kimi-K2-\nThinking", 
    "Hunyuan-\nA13B-Instruct", 
    "Qwen3-Next-\n80B-A3B-\nThinking" 
]

# 【修改点 3】设置垂直居中对齐逻辑
ax = plt.gca()
ax.set_xticks(x)
ax.set_xticklabels(custom_labels, fontsize=8, rotation=0)

for label in ax.get_xticklabels():
    # 设为 center：让文字块的几何中心对齐
    label.set_verticalalignment('center') 
    # 向下移动位置 (根据需要微调，-0.12 是个不错的通用值)
    label.set_y(-0.07) 

plt.yticks(fontsize=9)
# 根据您的数据范围 (60-69)，稍微调整ylim以便显示图例
plt.ylim(55, 74) 

# 图例优化 (双列居中)
plt.legend(prop=cn_font, loc='upper center', ncol=2, frameon=False, columnspacing=0.8, handletextpad=0.2) 

plt.grid(axis='y', linestyle='--', alpha=0.3)

# --- 自动标注数值 ---
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        # 字号改为 7 以适应窄条
        plt.text(rect.get_x() + rect.get_width()/2., height + 0.5,
                 f'{height:.1f}',
                 ha='center', va='bottom',
                 fontsize=7,
                 color='black')

autolabel(rects1)
autolabel(rects2)

# 【修改点 4】手动调整边距
plt.subplots_adjust(left=0.15, right=0.95, bottom=0.15, top=0.97)

plt.savefig('similarity_score_chart.png', dpi=300) 
plt.show()