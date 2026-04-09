import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import warnings
import joblib

# Sklearn & XGBoost 工具
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from xgboost import XGBClassifier

# ==========================================
# 0. 基础配置 (字体与警告)
# ==========================================
warnings.filterwarnings('ignore') # 忽略一些版本兼容性警告

# 字体设置 (适配中英文环境)
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
elif system_name == "Darwin":
    plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial Unicode MS']
else:
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. [步骤1] 数据加载与整合
# ==========================================
print(">>> [步骤1] 数据加载与整合...")

# 文件路径
path_health = r"D:\SHU\研究生\问答系统\钢铁故障数据\健康.xlsx"
path_misalign = r"D:\SHU\研究生\问答系统\钢铁故障数据\故障类型-不对中.xlsx"
path_unbalance = r"D:\SHU\研究生\问答系统\钢铁故障数据\故障类型-不平衡.xlsx"

try:
    health_df = pd.read_excel(path_health)
    misalignment_df = pd.read_excel(path_misalign)
    unbalance_df = pd.read_excel(path_unbalance)
except Exception as e:
    print(f"错误：读取文件失败。\n详细信息: {e}")
    exit()

# 合并数据集
data = pd.concat([health_df, misalignment_df, unbalance_df], ignore_index=True)
print(f"数据加载完成，总样本数: {len(data)}")

# ==========================================
# 2. [步骤2] 数据预处理 (标准化)
# ==========================================
print("\n>>> [步骤2] 数据预处理 (Z-Score标准化)...")

# 分离特征和标签
X = data.drop('label', axis=1)
y = data['label']
feature_names = X.columns.tolist()

# 标准化 (fit_transform 整个数据集用于特征分析，后面训练时会重新划分)
# 为了严谨，我们在训练模型时会重新 fit 训练集，这里先展示整体分布
scaler_global = StandardScaler()
X_scaled_global = scaler_global.fit_transform(X)

# ==========================================
# 3. [步骤3] 特征重要性分析 (随机森林)
# ==========================================
print("\n>>> [步骤3] 特征重要性分析...")

# 训练临时随机森林模型
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_scaled_global, y)

# 获取并展示特征重要性
importances = pd.Series(rf.feature_importances_, index=feature_names).sort_values(ascending=False)
print("特征重要性排名:")
print(importances)

plt.figure(figsize=(10, 5))
sns.barplot(x=importances.values, y=importances.index, palette='magma')
plt.title('Feature Importance (Random Forest)')
plt.show()

# ==========================================
# 4. [步骤4] 模型训练与选择 (XGBoost)
# ==========================================
print("\n>>> [步骤4] 模型训练 (XGBoost)...")

# 划分训练集和测试集 (8:2)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 重新标准化 (严格遵守：只 fit 训练集)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 训练 XGBoost 模型
model = XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    random_state=42,
    eval_metric='mlogloss',
    use_label_encoder=False
)
model.fit(X_train_scaled, y_train)
print("XGBoost 模型训练完成。")

# ==========================================
# 5. [步骤5] 模型评估验证 (交叉验证)
# ==========================================
print("\n>>> [步骤5] 模型评估验证...")

# K折交叉验证 (在训练集上做)
cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
print(f"5折交叉验证平均准确率: {cv_scores.mean()*100:.2f}%")

# 在测试集上评估
y_pred = model.predict(X_test_scaled)
print("\n测试集分类报告:")
target_names = ['健康 (0)', '不平衡 (1)', '不对中 (2)']
print(classification_report(y_test, y_pred, target_names=target_names))

# 混淆矩阵
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=target_names, yticklabels=target_names)
plt.title('Confusion Matrix')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.show()

# ==========================================
# 6. [步骤6] 模型持久化
# ==========================================
print("\n>>> [步骤6] 模型持久化 (Saving)...")
joblib.dump(model, 'steel_fault_classifier.pkl')
joblib.dump(scaler, 'feature_scaler.pkl')
print("模型和 Scaler 已保存至当前目录。")

# ==========================================
# 7. [步骤7] 实时数据预测流程
# ==========================================
print("\n>>> [步骤7] 实时数据预测演示...")

def predict_fault(realtime_data_list):
    """
    Kimi 定义的实时预测函数
    """
    # 1. 加载保存的模型和scaler
    try:
        loaded_model = joblib.load('steel_fault_classifier.pkl')
        loaded_scaler = joblib.load('feature_scaler.pkl')
    except:
        return "错误: 模型文件未找到，请先运行训练步骤。"
    
    # 2. 数据预处理
    # 注意：需要 reshape 成二维数组 (1, 7)
    data_array = np.array(realtime_data_list).reshape(1, -1)
    data_scaled = loaded_scaler.transform(data_array)
    
    # 3. 故障预测
    prediction = loaded_model.predict(data_scaled)[0]
    probabilities = loaded_model.predict_proba(data_scaled)[0]
    
    # 4. 结果映射
    fault_types = {0: "健康", 1: "不平衡故障", 2: "不对中故障"}
    
    return {
        '预测结果': fault_types[prediction],
        '置信度': f"{probabilities[prediction]*100:.2f}%",
        '各类型概率': {
            "健康": f"{probabilities[0]*100:.2f}%",
            "不平衡": f"{probabilities[1]*100:.2f}%",
            "不对中": f"{probabilities[2]*100:.2f}%"
        }
    }

# --- 模拟测试 ---
# 场景 1: 从测试集中取一条“不对中”数据 (Label=2)
idx_misalign = np.where(y_test == 2)[0][0]
realtime_sample_1 = X_test.iloc[idx_misalign].tolist()

print(f"\n[模拟场景 1] 输入特征: {realtime_sample_1[:3]}...")
result_1 = predict_fault(realtime_sample_1)
print(result_1)

# 场景 2: 从测试集中取一条“健康”数据 (Label=0)
idx_health = np.where(y_test == 0)[0][0]
realtime_sample_2 = X_test.iloc[idx_health].tolist()

print(f"\n[模拟场景 2] 输入特征: {realtime_sample_2[:3]}...")
result_2 = predict_fault(realtime_sample_2)
print(result_2)