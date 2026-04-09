import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, ConfusionMatrixDisplay

# ==========================================
# 0. 绘图字体与画布配置
# ==========================================

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 9
plt.rcParams['axes.unicode_minus'] = False

system_name = platform.system()
if system_name == "Windows":
    font_path = "C:/Windows/Fonts/simsun.ttc"
elif system_name == "Darwin":
    font_path = "/System/Library/Fonts/STSong.ttc"
else:
    font_path = "/usr/share/fonts/truetype/arphic/uming.ttc"

try:
    cn_font = fm.FontProperties(fname=font_path, size=6)
except:
    cn_font = None

# ==========================================
# 1. 数据准备 (保持不变)
# ==========================================

path_health = r"D:\SHU\研究生\问答系统\钢铁故障数据\健康.xlsx"
path_misalign = r"D:\SHU\研究生\问答系统\钢铁故障数据\故障类型-不对中.xlsx"
path_unbalance = r"D:\SHU\研究生\问答系统\钢铁故障数据\故障类型-不平衡.xlsx"

try:
    df_health = pd.read_excel(path_health)
    df_misalign = pd.read_excel(path_misalign)
    df_unbalance = pd.read_excel(path_unbalance)
except Exception as e:
    print(f"错误：读取文件失败。\n详细信息: {e}")
    exit()

df_all = pd.concat([df_health, df_misalign, df_unbalance], ignore_index=True)
X = df_all.drop('label', axis=1)
y = df_all['label']
label_map = {0: '健康', 1: '不平衡', 2: '不对中'}

# ==========================================
# 2. 模型训练
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

rf_clf = RandomForestClassifier(n_estimators=100, random_state=42)
rf_clf.fit(X_train_scaled, y_train)

y_pred = rf_clf.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
print(f"测试集准确率: {accuracy*100:.2f}%")

# ==========================================
# 3. 绘图修改
# ==========================================

# --- 图表 1: 混淆矩阵 (保持原比例不变) ---

fig, ax = plt.subplots(figsize=(2.3, 2.0), dpi=300)

conf_matrix = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=conf_matrix, display_labels=[label_map[0], label_map[1], label_map[2]])

disp.plot(cmap='Blues', ax=ax, values_format='d', colorbar=False)

cbar = fig.colorbar(disp.im_, ax=ax, shrink=0.65, aspect=15, pad=0.05)
cbar.ax.tick_params(labelsize=8)

ax.set_xlabel('预测标签', fontproperties=cn_font, fontsize=9, labelpad=3)
ax.set_ylabel('真实标签', fontproperties=cn_font, fontsize=9, labelpad=3)

plt.setp(ax.get_xticklabels(), fontproperties=cn_font, fontsize=9)
plt.setp(ax.get_yticklabels(), fontproperties=cn_font, fontsize=9)

plt.subplots_adjust(left=0.10, right=0.92, bottom=0.10, top=1.00)

plt.savefig('confusion_matrix_3col.png', dpi=300)
plt.show()


# --- 图表 2: 特征重要性分析 (调整比例适配虚线框) ---

importances = pd.Series(rf_clf.feature_importances_, index=X.columns).sort_values(ascending=False)

rename_map = {
    'rms_features': '均方根',
    'peak_features': '峰值',
    'entropy_features': '均值',
    'wf_features': '小波特征', 
    'kf_features': '峭度因子'  
}

importances = importances.rename(index=rename_map)
top_n = 5
importances_top = importances.head(top_n)

# ==========================================
# 3. 绘图修改 (字体整体缩小版)
# ==========================================

# 1. 画布设置 (保持 2.3 : 1.0 的长条形比例)
plt.figure(figsize=(2.1, 1.0), dpi=300)

# 2. 绘图 (调整柱子宽度和线宽，使其更精致)
importances_top.plot(kind='bar', color="#08306B", width=0.4, edgecolor='black', linewidth=0.3)

# 【核心修改 1】Y轴标题字号改为 6
plt.ylabel('重要性得分', fontproperties=cn_font, labelpad=2, fontsize=6)

ax = plt.gca()
ax.tick_params(width=0.3, length=2)
for spine in ax.spines.values():
    spine.set_linewidth(0.3)

# 【核心修改 2】X轴标签字号保持 4 (或 4.5)，配合宋体
ax.set_xticklabels(importances_top.index, fontsize=6, fontproperties=cn_font, rotation=0)

for label in ax.get_xticklabels():
    label.set_verticalalignment('center') 
    # 调整垂直偏移量 (因为字体变小了，偏移量可以稍微收一点，或者保持 -0.35)
    label.set_y(0) 

# 【核心修改 3】Y轴刻度字号改为 6
plt.yticks(fontsize=6)

# 网格线变细
plt.grid(axis='y', linestyle='--', alpha=0.3, linewidth=0.3)

# 3. 边距调整
# 因为字变小了，bottom 可以稍微收一点点 (0.40 -> 0.35)，让柱子显得高一点
plt.subplots_adjust(left=0.18, right=0.95, bottom=0.25, top=0.90)

plt.savefig('feature_importance_small_font.png', dpi=300)
plt.show()