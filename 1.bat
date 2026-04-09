@echo off
:: 强制将控制台代码页设置为 UTF-8 (65001)，解决乱码问题
chcp 65001 >nul

echo ==========================================
echo       正在启动 SIOPT 问答系统...
echo ==========================================

:: 1. 启动 Python 后端
echo 正在启动后端服务...
start "Python Backend" cmd /k "cd backend && python main.py"

:: 2. 启动 Vue 前端
echo 正在启动前端界面...
start "Vue Frontend" cmd /k "cd ai_system && npm run dev"

echo.
echo 系统启动中，请确保 Neo4j 数据库已手动开启！
echo.
pause