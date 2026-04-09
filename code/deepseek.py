import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import warnings

# Sklearn & XGBoost 工具
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, IsolationForest
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
# 1. 数据加载与预处理 (DeepSeek 步骤 1)
# ==========================================
print(">>> [步骤1] 数据加载与预处理...")

# 文件路径
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

# 合并数据
df_all = pd.concat([df_health, df_misalign, df_unbalance], ignore_index=True)
X = df_all.drop('label', axis=1)
y = df_all['label']
feature_names = X.columns.tolist()

# 划分数据集 (80% 训练, 20% 测试)
X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 特征标准化 (Z-Score)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_raw)
X_test_scaled = scaler.transform(X_test_raw) # 注意：测试集使用训练集的参数

print(f"训练集形状: {X_train_scaled.shape}, 测试集形状: {X_test_scaled.shape}")

# ==========================================
# 2. 特征重要性分析 (DeepSeek 步骤 2)
# ==========================================
print("\n>>> [步骤2] 特征重要性分析 (基于随机森林)...")

rf_analyzer = RandomForestClassifier(n_estimators=100, random_state=42)
rf_analyzer.fit(X_train_scaled, y_train)

importances = pd.Series(rf_analyzer.feature_importances_, index=feature_names).sort_values(ascending=False)
print("关键特征贡献度排名:")
print(importances.head(3))

# 可视化特征重要性
plt.figure(figsize=(10, 5))
sns.barplot(x=importances.values, y=importances.index, palette='viridis')
plt.title('Feature Importance (Random Forest Analysis)')
plt.show()

# ==========================================
# 3. 特征降维 PCA (DeepSeek 步骤 3)
# ==========================================
print("\n>>> [步骤3] PCA 特征降维...")

# 保留 95% 的方差信息 (DeepSeek 建议保留 85% 以上)
pca = PCA(n_components=0.95) 
X_train_pca = pca.fit_transform(X_train_scaled)
X_test_pca = pca.transform(X_test_scaled)

print(f"降维后特征维度: {X_train_pca.shape[1]} (原维度: 7)")
print(f"各主成分方差解释率: {pca.explained_variance_ratio_}")

# 可视化 PCA 空间 (取前两个主成分)
plt.figure(figsize=(8, 6))
scatter = plt.scatter(X_train_pca[:, 0], X_train_pca[:, 1], c=y_train, cmap='viridis', alpha=0.6)
plt.legend(handles=scatter.legend_elements()[0], labels=['健康', '不平衡', '不对中'])
plt.title('PCA Feature Space Distribution')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.grid(True, alpha=0.3)
plt.show()

# ==========================================
# 4. 分类模型训练 - 集成学习 (DeepSeek 步骤 4)
# ==========================================
print("\n>>> [步骤4] 训练集成模型 (RF + XGBoost)...")

# 基分类器 1: 随机森林
rf_clf = RandomForestClassifier(n_estimators=100, random_state=42)

# 基分类器 2: XGBoost
xgb_clf = XGBClassifier(n_estimators=100, learning_rate=0.1, eval_metric='mlogloss', use_label_encoder=False)

# 集成学习 (软投票)
ensemble_model = VotingClassifier(
    estimators=[('rf', rf_clf), ('xgb', xgb_clf)],
    voting='soft'
)

# 注意：使用 PCA 降维后的数据进行训练
ensemble_model.fit(X_train_pca, y_train)
print("集成模型训练完成。")

# 评估模型
y_pred = ensemble_model.predict(X_test_pca)
print(f"测试集准确率: {accuracy_score(y_test, y_pred)*100:.2f}%")

# ==========================================
# 5. 异常检测模型训练 (DeepSeek 步骤 5-阶段一)
# ==========================================
print("\n>>> [步骤5准备] 训练异常检测模型 (Isolation Forest)...")
# 仅使用训练集中的“健康数据(Label=0)”来训练异常检测器，定义“正常”的边界
X_train_healthy = X_train_scaled[y_train == 0]
iso_forest = IsolationForest(contamination=0.01, random_state=42) # 假设1%的污染率
iso_forest.fit(X_train_healthy)
print("异常检测器训练完成 (仅基于健康数据)。")

# ==========================================
# 6. 实时诊断流程模拟 (DeepSeek 步骤 5 & 6)
# ==========================================
print("\n>>> [步骤6] 模拟实时滑动窗口诊断流程...")

label_map = {0: '健康 (Health)', 1: '不平衡 (Unbalance)', 2: '不对中 (Misalignment)'}

def real_time_pipeline(window_data_raw, scaler, pca, iso_model, clf_model):
    """
    模拟 DeepSeek 提出的完整实时诊断流水线
    """
    results = []
    
    # 1. 预处理 (标准化)
    window_scaled = scaler.transform(window_data_raw)
    
    # 2. 异常检测 (阶段一)
    # IsolationForest 输出: 1为正常, -1为异常
    iso_preds = iso_model.predict(window_scaled)
    # 计算窗口内被判定为"正常"的比例
    normal_ratio = np.sum(iso_preds == 1) / len(iso_preds)
    
    print(f"  - 异常检测阶段: 窗口内 {normal_ratio*100:.1f}% 被判定为符合健康分布")
    
    # 阈值判断：如果绝大多数样本都符合健康分布，直接判定健康，不再走分类器
    # (DeepSeek 建议阈值 0.8)
    if normal_ratio > 0.8:
        return "健康 (Health) [由异常检测器直接判定]", 1.0
    
    # 3. 故障分类 (阶段二)
    # 如果异常检测认为有问题，进入分类器
    window_pca = pca.transform(window_scaled)
    probs = clf_model.predict_proba(window_pca)
    
    # 4. 滑动窗口投票 (Step 6)
    # 对窗口内的每个样本进行预测，然后取平均概率或多数投票
    avg_probs = np.mean(probs, axis=0) # 计算各类别的平均概率
    final_pred_idx = np.argmax(avg_probs)
    final_confidence = avg_probs[final_pred_idx]
    
    diagnosis = label_map[final_pred_idx]
    
    # 5. 置信度评估 (Step 5-阶段三)
    confidence_level = "低"
    if final_confidence > 0.7:
        confidence_level = "高"
    elif final_confidence > 0.5:
        confidence_level = "中"
        
    return f"{diagnosis} [置信度: {confidence_level}]", final_confidence

# --- 模拟运行 ---
# 场景 A: 从测试集中抽取 20 个“不平衡”样本作为一个时间窗口
print("\n--- 场景 A: 模拟不平衡故障发生 ---")
target_label = 1 # 不平衡
indices = np.where(y_test == target_label)[0][:20] # 取前20个
window_samples = X_test_raw.iloc[indices]

diagnosis_result, conf = real_time_pipeline(window_samples, scaler, pca, iso_forest, ensemble_model)
print(f"最终诊断结论: {diagnosis_result}")
print(f"平均概率分布: {conf:.4f}")

# 场景 B: 从测试集中抽取 20 个“健康”样本
print("\n--- 场景 B: 模拟设备正常运行 ---")
target_label = 0 # 健康
indices = np.where(y_test == target_label)[0][:20]
window_samples = X_test_raw.iloc[indices]

diagnosis_result, conf = real_time_pipeline(window_samples, scaler, pca, iso_forest, ensemble_model)
print(f"最终诊断结论: {diagnosis_result}")