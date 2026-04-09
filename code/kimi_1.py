import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import KernelPCA
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

# 设置随机种子
np.random.seed(42)

# ==========================================
# 1. 数据画像模拟 (基础数据生成)
# ==========================================
print(">>> [Step 1] 正在生成数字孪生模拟数据...")
n_samples = 50 # 增加样本量以支持更丰富的模拟
features_list = ['mean', 'rms', 'peak', 'imf', 'kf', 'wf', 'entropy']

# --- 生成三类数据 ---
# 1. 健康 (Health): RMS低(0.08), 熵高(1.75)
data_0 = np.random.normal(0, 0.1, (n_samples, 7))
data_0[:, 1] = np.random.normal(0.08, 0.02, n_samples) 
data_0[:, 6] = np.random.normal(1.75, 0.1, n_samples)

# 2. 不平衡 (Unbalance): RMS中(0.9), 熵低(0.58)
data_1 = np.random.normal(0, 0.1, (n_samples, 7))
data_1[:, 1] = np.random.normal(0.9, 0.1, n_samples)
data_1[:, 6] = np.random.normal(0.58, 0.1, n_samples)
data_1[:, 3] = np.random.normal(2.0, 0.5, n_samples)

# 3. 不对中 (Misalignment): RMS高(2.19), 峰值高
data_2 = np.random.normal(0, 0.1, (n_samples, 7))
data_2[:, 1] = np.random.normal(2.19, 0.2, n_samples)
data_2[:, 2] = np.random.normal(3.5, 0.5, n_samples)
data_2[:, 6] = np.random.normal(1.2, 0.2, n_samples)

# 合并用于训练的数据 (保留部分用于稍后的实时流模拟)
X = np.vstack([data_0, data_1, data_2])
y = np.hstack([np.zeros(n_samples), np.ones(n_samples), np.full(n_samples, 2)])
df = pd.DataFrame(X, columns=features_list)

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

# ==========================================
# 2. 模型训练阶段
# ==========================================
print(">>> [Step 2] 正在训练智能诊断组件...")

# A. 标准化器 (Scaler)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# B. 异常检测器 (守门员): 仅用训练集中的"健康数据"训练
# 作用: 定义什么是"正常"，不符合的统统拦截下来交给诊断模型
healthy_train_data = X_train_scaled[y_train == 0]
iso_forest = IsolationForest(contamination=0.05, random_state=42)
iso_forest.fit(healthy_train_data)

# C. 特征提取 (KPCA): 提取非线性特征
kpca = KernelPCA(n_components=2, kernel='rbf', gamma=0.1)
X_train_kpca = kpca.fit_transform(X_train_scaled)

# D. 故障诊断模型 (GBDT/XGBoost): 精确分类
clf_model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
clf_model.fit(X_train_kpca, y_train)

print(f"    - 模型准确率: {clf_model.score(kpca.transform(X_test_scaled), y_test)*100:.2f}%")

# ==========================================
# 3. 定义实时诊断流水线 (Core Logic)
# ==========================================
label_map = {0: '✅ 设备健康', 1: '⚠️ 不平衡故障', 2: '🔴 不对中故障'}

def real_time_diagnosis(window_data, scaler, kpca, iso_model, clf_model):
    """
    模拟实时数据流的处理逻辑：
    数据 -> 标准化 -> 异常检测(守门) -> (若异常) KPCA特征提取 -> GBDT分类
    """
    # 1. 预处理
    w_scaled = scaler.transform(window_data)
    
    # 2. 阶段一：异常检测 (Gatekeeper)
    # IsolationForest: 1=正常, -1=异常
    iso_preds = iso_model.predict(w_scaled)
    normal_rate = np.mean(iso_preds == 1)
    
    print(f"   [监测] 窗口信号健康度: {normal_rate*100:.1f}% ", end="")
    
    # 逻辑分支：如果窗口内80%以上的点都正常，直接判定健康，不调用分类器
    if normal_rate > 0.8:
        return "✅ 设备健康 (基线监测)", 1.0, 0 # 0是健康的Label
    
    print("-> 发现异常特征 -> 启动诊断模型...")
    
    # 3. 阶段二：故障确诊 (Diagnosis)
    # 提取非线性特征
    w_kpca = kpca.transform(w_scaled)
    # 预测概率
    probs = clf_model.predict_proba(w_kpca)
    
    # 4. 阶段三：投票决策
    # 取窗口内所有样本预测概率的平均值
    avg_probs = np.mean(probs, axis=0)
    pred_label = np.argmax(avg_probs)
    confidence = avg_probs[pred_label]
    
    return label_map[pred_label], confidence, pred_label

# ==========================================
# 4. 模拟实时场景运行
# ==========================================
print("\n" + "="*40)
print(">>> [Step 3] 启动实时流模拟 (Real-time Simulation)")
print("="*40)

# 场景构建：制造一个混合时间序列
# 前10个点是健康的，中间突然发生"不对中"故障(10个点)
sim_health = np.random.normal(0, 0.1, (10, 7))
sim_health[:, 1] += 0.08 # RMS正常
sim_health[:, 6] += 1.75 # 熵正常

sim_fault = np.random.normal(0, 0.1, (10, 7))
sim_fault[:, 1] += 2.2  # RMS剧增 (不对中)
sim_fault[:, 2] += 3.5  # Peak剧增

# 拼接数据流
stream_data = np.vstack([sim_health, sim_fault])
stream_labels = ["健康"]*10 + ["不对中"]*10

# 滑动窗口设置 (窗口大小=5，步长=5)
window_size = 5

for i in range(0, len(stream_data), window_size):
    # 获取当前窗口数据
    window_X = stream_data[i : i+window_size]
    current_true_state = stream_labels[i]
    
    print(f"\nTime Step {i//window_size + 1}: [真实状态: {current_true_state}]")
    
    # 执行诊断管道
    result_str, conf, pred_idx = real_time_diagnosis(
        window_X, scaler, kpca, iso_forest, clf_model
    )
    
    # 输出结果
    print(f"   >>> 诊断结论: {result_str}")
    print(f"   >>> 置信度:   {conf*100:.2f}%")
    
    # 简单报警逻辑
    if pred_idx != 0:
        print(f"   🔔 触发报警! 通知维护部门检查 RMS/Peak 指标")

# ==========================================
# 5. 结果可视化
# ==========================================
plt.figure(figsize=(10, 5))
# 绘制KPCA空间
X_vis = kpca.transform(scaler.transform(X)) # 全量数据背景
plt.scatter(X_vis[y==0, 0], X_vis[y==0, 1], c='green', alpha=0.3, label='Health Baseline')
plt.scatter(X_vis[y==2, 0], X_vis[y==2, 1], c='red', alpha=0.3, label='Misalignment History')

# 绘制刚刚模拟的故障流在空间中的位置
stream_kpca = kpca.transform(scaler.transform(stream_data))
plt.plot(stream_kpca[:10, 0], stream_kpca[:10, 1], 'go-', label='Real-time: Health Stream')
plt.plot(stream_kpca[10:, 0], stream_kpca[10:, 1], 'rx-', label='Real-time: Fault Stream')

plt.title("Real-time Diagnosis Trajectory in KPCA Space")
plt.xlabel("PC1 (Non-linear Component)")
plt.ylabel("PC2")
plt.legend()
plt.tight_layout()
plt.show()