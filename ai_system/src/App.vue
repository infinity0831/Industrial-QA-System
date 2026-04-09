<script setup>
import { ref } from 'vue';
import ChatView from './components/ChatView.vue';
import KnowledgeView from './components/KnowledgeView.vue';
import ToolsView from './components/ToolsView.vue';
import { 
  Bot, Settings, MessageSquare, Database, Wrench, User, Monitor
} from 'lucide-vue-next';

// 当前激活的视图，默认为 'chat'
const currentView = ref('chat');

const setView = (viewName) => {
  currentView.value = viewName;
};
</script>

<template>
  <div class="app-container">
    <aside class="sidebar">
      <div class="logo-area">
        <Bot class="logo-icon" size="32" />
        <span class="logo-text">SIOPT</span>
      </div>

      <nav class="nav-menu">
        <div class="nav-item" :class="{ active: currentView === 'chat' }" @click="setView('chat')">
          <MessageSquare size="20" />
          <span>我的对话</span>
        </div>
        <div class="nav-item" :class="{ active: currentView === 'knowledge' }" @click="setView('knowledge')">
          <Database size="20" />
          <span>我的知识</span>
        </div>
        <div class="nav-item" :class="{ active: currentView === 'tools' }" @click="setView('tools')">
          <Wrench size="20" />
          <span>我的算法</span>
        </div>
      </nav>

      <div class="user-area">
        <div class="nav-item">
          <User size="20" />
          <span>用户</span>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <ChatView v-if="currentView === 'chat'" />
      <KnowledgeView v-if="currentView === 'knowledge'" />
      <ToolsView v-if="currentView === 'tools'" />
    </main>
  </div>
</template>

<style>
/* 全局样式重置 */
body, html {
  margin: 0;
  padding: 0;
  background-color: #1a1f35;
  color: #fff;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  height: 100%;
  overflow: hidden;
}
</style>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: #131728;
}

/* 侧边栏样式 */
.sidebar {
  width: 90px;
  background-color: #1e2538; /* 深蓝背景 */
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  border-right: 1px solid #2b3550;
  flex-shrink: 0;
}

.logo-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40px;
  color: #fff;
}

.logo-text {
  font-weight: bold;
  margin-top: 5px;
  font-size: 14px;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 25px;
  width: 100%;
  align-items: center;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #ffffff;  /* <--- 改为纯白色 */
  cursor: pointer;
  transition: all 0.3s;
  font-size: 12px;
  gap: 5px;
  width: 100%;
  padding: 10px 0;
}

.nav-item:hover {
  color: #fff;
}

.nav-item.active {
  color: #60a5fa; /* 激活态蓝色 */
  background: linear-gradient(90deg, rgba(30,37,56,0) 0%, rgba(45,55,80,1) 50%, rgba(30,37,56,0) 100%);
  border-left: 3px solid #60a5fa;
}

.user-area {
  margin-top: auto;
  width: 100%;
}

.main-content {
  flex: 1;
  background-color: #131728;
  overflow: hidden;
  position: relative;
}
</style>