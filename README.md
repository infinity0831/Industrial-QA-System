Industrial-QA-System (工业故障诊断智能问答系统)
本项目是一款针对工业领域（如冷水机组、钢铁生产）设计的智能问答与决策支持系统。它集成了 Vue 3 构建的现代化响应式前端，以及基于 LLM (如 DeepSeek/Kimi) 和 机器学习算法 的后端智能体。

🌟 核心功能
智能对话交互：支持与工业大模型实时对话，解决生产过程中的操作与维护咨询。

多模式视图切换：

ChatView: 沉浸式对话界面，支持 Markdown 语法渲染。

KnowledgeView: 关联工业知识库与故障诊断手册。

ToolsView: 集成算法工具箱（如钢铁故障分类器、特征缩放工具）。

自动化诊断：后端集成 steel_fault_classifier.pkl 模型，可对工业传感器数据进行实时故障分类。

多模型支持：适配 DeepSeek、Kimi、豆包等主流国产大模型 API。

🛠️ 技术栈
前端: Vue 3, Vite, CSS3 (Flexbox/Grid), JavaScript

后端: Python 3.x, Flask/FastAPI (建议), Scikit-learn

模型: 大语言模型 (LLM) + 传统机器学习 (Random Forest/KPCA)

🚀 快速开始
1. 克隆/下载项目
Bash
git clone https://github.com/infinity0831/Industrial-QA-System.git
cd Industrial-QA-System
2. 前端环境配置 (ai_system 目录下)
需要安装 Node.js 环境，然后执行：

Bash
cd ai_system
npm install   # 下载 Vue 相关依赖包
npm run dev   # 启动前端开发服务器
主要依赖项：vue, vite, eslint, prettier。

3. 后端环境配置 (根目录下)
建议使用虚拟环境：

Bash
# 安装必要 Python 依赖
pip install pandas numpy scikit-learn requests flask
运行后端：

Bash
python backend/main.py
📂 目录结构说明
ai_system/: Vue 3 前端源代码。

src/components/: 包含 ChatView.vue (对话), KnowledgeView.vue (知识库), ToolsView.vue (工具箱) 等核心组件。

backend/: 后端服务接口。

code/: 智能体逻辑与算法实验脚本（包含 agent.py, deepseek.py 等）。

*.pkl: 训练好的机器学习模型文件（用于故障预测）。

📝 使用说明
启动后端 API 服务，确保模型和 LLM 接口正常调用。

启动前端 Vue 项目，访问浏览器显示的本地链接（通常为 http://localhost:5173）。

在对话框输入工业相关问题，或者通过工具箱上传数据进行故障诊断。
