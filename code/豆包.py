import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import warnings

# Sklearn 工具库
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC  # <--- 改用 SVM
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# ==========================================
# 0. 基础配置 (字体与警告)
# ==========================================
warnings.filterwarnings('ignore') # 忽略一些版本兼容性警告

# 字体设置 (适配中英文环境，防止绘图乱码)
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
elif system_name == "Darwin":
    plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial Unicode MS']
else:
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. [步骤一] 数据预处理
# ==========================================
print(">>> [步骤一] 数据预处理启动...")

# 1.1 子步骤1：数据加载与合并
# 文件路径 (保持不变)
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

# 统一列名顺序 (防止错位)
columns_order = ['mean_features', 'rms_features', 'peak_features', 'imf_features', 
                 'kf_features', 'wf_features', 'entropy_features', 'label']
df_health = df_health[columns_order]
df_misalign = df_misalign[columns_order]
df_unbalance = df_unbalance[columns_order]

# 合并数据
df_all = pd.concat([df_health, df_misalign, df_unbalance], ignore_index=True)
print(f"数据合并完成，总样本数: {len(df_all)}")

# 1.2 子步骤2：数据清洗 (缺失值与异常值)
if df_all.isnull().sum().sum() > 0:
    print("发现缺失值，正在使用中位数填充...")
    df_all.fillna(df_all.median(), inplace=True)

feature_cols = columns_order[:-1] # 前7列是特征
df_all[feature_cols] = df_all[feature_cols].astype(float)

# 1.3 子步骤3：特征与标签分离
X = df_all[feature_cols]
y = df_all['label']

# ==========================================
# 2. [步骤二] 数据集划分
# ==========================================
print("\n>>> [步骤二] 数据集划分 (分层抽样)...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"训练集样本: {len(X_train)}, 测试集样本: {len(X_test)}")

# 1.4 子步骤4：特征标准化 (关键：仅fit训练集)
# 注意：SVM 对数据标准化极其敏感，这一步是必须的
print("\n>>> [步骤一补] 特征标准化 (Z-Score)...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train) 
X_test_scaled = scaler.transform(X_test)       

# ==========================================
# 3. [步骤三] 分类模型选择与训练 (SVM)
# ==========================================
print("\n>>> [步骤三] 模型训练 (Support Vector Machine)...")

# 使用网格搜索 (GridSearchCV) 寻找最优参数 (豆包建议的 SVM 参数)
param_grid = {
    'C': [0.1, 1, 10, 100],            # 惩罚系数
    'gamma': [1, 0.1, 0.01, 0.001],    # 核函数带宽
    'kernel': ['rbf', 'linear']        # 核函数类型
}

# 实例化 SVM (必须设置 probability=True 才能输出概率)
svm = SVC(probability=True, random_state=42)
grid_search = GridSearchCV(svm, param_grid, cv=5, scoring='accuracy')
grid_search.fit(X_train_scaled, y_train)

best_svm_model = grid_search.best_estimator_
print(f"最优参数组合: {grid_search.best_params_}")
print("SVM 模型训练完成。")

# ==========================================
# 4. [步骤四] 模型评估
# ==========================================
print("\n>>> [步骤四] 模型评估报告...")

y_pred = best_svm_model.predict(X_test_scaled)

# 准确率
acc = accuracy_score(y_test, y_pred)
print(f"测试集准确率 (Accuracy): {acc*100:.2f}%")

# 详细报告
label_map = {0: '健康', 1: '不平衡', 2: '不对中'}
print("\n分类详细报告:")
print(classification_report(y_test, y_pred, target_names=[label_map[0], label_map[1], label_map[2]]))

# 混淆矩阵可视化
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=[label_map[0], label_map[1], label_map[2]],
            yticklabels=[label_map[0], label_map[1], label_map[2]])
plt.title('故障诊断混淆矩阵 (SVM)')
plt.xlabel('预测类别')
plt.ylabel('真实类别')
plt.show()

# 注意：SVM 不支持 feature_importances_ (线性核除外)，所以删除了特征重要性图

# ==========================================
# 5. [步骤五] 实时数据故障预测
# ==========================================
print("\n>>> [步骤五] 实时数据故障预测演示...")

def predict_real_time_data(real_data_raw, model, scaler):
    """
    实时数据处理与预测函数
    """
    # 1. 预处理
    data_array = np.array(real_data_raw).reshape(1, -1)
    # 标准化 (非常重要)
    data_scaled = scaler.transform(data_array)
    
    # 2. 模型预测
    pred_label = model.predict(data_scaled)[0]
    pred_proba = model.predict_proba(data_scaled)[0] # SVM 需要 probability=True
    
    # 结果映射
    result_text = label_map[pred_label]
    confidence = pred_proba[pred_label]
    
    return result_text, confidence

# --- 模拟场景 1: 输入一条“不平衡”数据 ---
idx_unbalance = np.where(y_test == 1)[0][0]
mock_data_1 = X_test.iloc[idx_unbalance].values

print(f"\n[模拟场景 1] 接收到实时数据: {mock_data_1[:3]}...")
diagnosis, conf = predict_real_time_data(mock_data_1, best_svm_model, scaler)
print(f"诊断结果: 【{diagnosis}】 (置信度: {conf*100:.2f}%)")

# --- 模拟场景 2: 输入一条“健康”数据 ---
idx_health = np.where(y_test == 0)[0][0]
mock_data_0 = X_test.iloc[idx_health].values

print(f"\n[模拟场景 2] 接收到实时数据: {mock_data_0[:3]}...")
diagnosis, conf = predict_real_time_data(mock_data_0, best_svm_model, scaler)
print(f"诊断结果: 【{diagnosis}】 (置信度: {conf*100:.2f}%)")