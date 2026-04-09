<script setup>
import { ref, nextTick, computed, onMounted } from 'vue';
import { 
  Plus, Paperclip, ArrowUp, Sparkles, Database, Bot, User, 
  ChevronDown, ChevronRight, FileText, X, MessageSquare, Trash2, 
  Square, Edit2, Check, AlertCircle, Code, Play, LayoutTemplate
} from 'lucide-vue-next';
import * as echarts from 'echarts'; 

// --- 引入文件解析库 ---
import * as XLSX from 'xlsx';
import mammoth from 'mammoth';
import * as pdfjsLib from 'pdfjs-dist';
import pdfWorker from 'pdfjs-dist/build/pdf.worker?url';
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

// --- 1. 定义状态变量 ---
const inputText = ref('');       
const messages = ref([]);        
const isLoading = ref(false);
const loadingText = ref('深度思考中...');
const chatContainer = ref(null); 
const abortController = ref(null);

// [状态] 历史记录相关
const chatSessions = ref([]);     
const activeSessionId = ref(null);
const editingSessionId = ref(null);
const tempTitle = ref('');

// [状态] 知识库 & 工具库 开关
const isKnowledgeActive = ref(false);
const isAgentActive = ref(true); 

// [状态] 文件上传相关
const fileInput = ref(null);      
const selectedFile = ref(null);   
const fileContent = ref('');      
const isFileParsing = ref(false); 

// [状态] Canvas 工作台相关
const isCanvasOpen = ref(false);      
const canvasTab = ref('code');        // 'code' | 'preview'
const canvasCode = ref('');           
const canvasLogs = ref([]);           
const canvasChartRef = ref(null);     
let canvasChartInstance = null;

// --- 2. 配置 API ---
const API_KEY = 'sk-tmxmlfmgxuhagukdrigpgfgcbpixccshuyrrffafgoooxkko'; 
const API_URL = 'https://api.siliconflow.cn/v1/chat/completions'; 

// ==============================================================================
// [算法库定义 & 知识库调用]
// ==============================================================================
const ALGORITHM_REGISTRY = {
  krt: { name: "search_knowledge_base", description: "查询工业运维知识库" },
  wavelet: { name: "preprocess_wavelet_denoising", description: "小波去噪" },
  kalman: { name: "preprocess_kalman_filter", description: "卡尔曼滤波" },
};
const toolsDefinitions = computed(() => Object.values(ALGORITHM_REGISTRY).map(a => ({ type: "function", function: { name: a.name, description: a.description } })));

const fetchGraphData = async () => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    const res = await fetch(`http://localhost:8000/api/graph?t=${new Date().getTime()}`, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (!res.ok) throw new Error('API Error');
    const data = await res.json();
    let text = "【本地知识库快照】：\n";
    const nodes = data.nodes || [];
    const links = data.links || [];
    if (nodes.length === 0) return ""; 
    const nodeMap = {};
    nodes.slice(0, 100).forEach(n => { nodeMap[n.id] = n.name; text += `- 实体: ${n.name} (类型:${n.category})\n`; });
    links.slice(0, 100).forEach(l => { 
      const src = nodeMap[l.source] || l.source;
      const tgt = nodeMap[l.target] || l.target;
      text += `- 关系: ${src} -> [${l.value}] -> ${tgt}\n`; 
    });
    return text;
  } catch (e) { return ""; }
};

// ==============================================================================
// [历史记录管理]
// ==============================================================================
const loadSessionsFromStorage = () => {
  try {
    const stored = localStorage.getItem('siopt_chat_history');
    if (stored) chatSessions.value = JSON.parse(stored);
  } catch (e) { chatSessions.value = []; }
};

const saveSessionsToStorage = () => {
  try {
    if (chatSessions.value.length > 50) chatSessions.value = chatSessions.value.slice(0, 50);
    localStorage.setItem('siopt_chat_history', JSON.stringify(chatSessions.value));
  } catch (e) {
    if (e.name === 'QuotaExceededError') {
      chatSessions.value = chatSessions.value.slice(0, 25);
      localStorage.setItem('siopt_chat_history', JSON.stringify(chatSessions.value));
    }
  }
};

const clearAllSessions = () => {
  if (confirm("确定要清空所有历史对话吗？此操作无法撤销。")) {
    chatSessions.value = []; localStorage.removeItem('siopt_chat_history'); startNewChat();
  }
};

const generateAutoTitle = async (userText, sessionId) => {
  try {
    const payload = {
      model: "deepseek-ai/DeepSeek-V3", 
      messages: [{ role: "system", content: "生成10字以内简短标题，无标点。" }, { role: "user", content: userText }],
      stream: false, temperature: 0.3
    };
    const response = await fetch(API_URL, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${API_KEY}` }, body: JSON.stringify(payload)
    });
    if(!response.ok) return;
    const data = await response.json();
    let newTitle = data.choices?.[0]?.message?.content?.trim();
    if (newTitle) {
      newTitle = newTitle.replace(/^["'《]|["'》]$/g, '');
      const idx = chatSessions.value.findIndex(s => s.id === sessionId);
      if (idx !== -1) { chatSessions.value[idx].title = newTitle; saveSessionsToStorage(); }
    }
  } catch (e) {}
};

const updateCurrentSession = (isNew = false, firstUserText = '') => {
  if (!activeSessionId.value) {
    const newId = Date.now().toString();
    chatSessions.value.unshift({ id: newId, title: firstUserText.substring(0, 15) || "新对话", time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), messages: messages.value });
    activeSessionId.value = newId;
    if (isNew && firstUserText) generateAutoTitle(firstUserText, newId);
  } else {
    const idx = chatSessions.value.findIndex(s => s.id === activeSessionId.value);
    if (idx !== -1) { chatSessions.value[idx].messages = messages.value; const current = chatSessions.value.splice(idx, 1)[0]; chatSessions.value.unshift(current); }
  }
  saveSessionsToStorage();
};

const startRename = (e, s) => { e.stopPropagation(); editingSessionId.value = s.id; tempTitle.value = s.title; };
const confirmRename = () => { const s = chatSessions.value.find(s => s.id === editingSessionId.value); if (s && tempTitle.value.trim()) { s.title = tempTitle.value.trim(); saveSessionsToStorage(); } editingSessionId.value = null; };
const startNewChat = () => { if (isLoading.value) stopGeneration(); activeSessionId.value = null; messages.value = []; selectedFile.value = null; fileContent.value = ''; inputText.value = ''; isCanvasOpen.value = false; };
const switchSession = (session) => { if (isLoading.value || editingSessionId.value) return; activeSessionId.value = session.id; messages.value = session.messages; isCanvasOpen.value = false; nextTick(() => scrollToBottom()); };
const deleteSession = (e, id) => { e.stopPropagation(); chatSessions.value = chatSessions.value.filter(s => s.id !== id); saveSessionsToStorage(); if (activeSessionId.value === id) startNewChat(); };
onMounted(() => loadSessionsFromStorage());

// ==============================================================================
// [文件解析]
// ==============================================================================
const triggerFileUpload = () => fileInput.value.click();
const handleFileChange = async (event) => {
  const file = event.target.files[0]; if (!file) return; selectedFile.value = file; isFileParsing.value = true; fileContent.value = ''; 
  try {
    if (file.name.endsWith('.docx')) { const ab = await file.arrayBuffer(); const res = await mammoth.extractRawText({ arrayBuffer: ab }); fileContent.value = res.value; }
    else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
      const ab = await file.arrayBuffer(); const wb = XLSX.read(ab, { type: 'array' });
      const ws = wb.Sheets[wb.SheetNames[0]]; const csv = XLSX.utils.sheet_to_csv(ws, { FS: ",", RS: "\n" }); const rows = csv.split('\n').slice(0, 100).join('\n'); 
      fileContent.value = `[Data Snippet - First 100 rows]\n${rows}\n...(truncated)`;
    } 
    else if (file.name.endsWith('.pdf')) {
      const ab = await file.arrayBuffer(); const pdf = await pdfjsLib.getDocument(ab).promise;
      let txt = ''; for(let i=1; i<=pdf.numPages; i++) { const p = await pdf.getPage(i); const c = await p.getTextContent(); txt += c.items.map(s=>s.str).join(' '); }
      fileContent.value = txt;
    }
    else { fileContent.value = await file.text(); }
  } catch (e) { fileContent.value = `[读取错误] ${e.message}`; } finally { isFileParsing.value = false; }
};
const removeFile = () => { selectedFile.value = null; fileContent.value = ''; if(fileInput.value) fileInput.value.value = ''; };

// ==============================================================================
// [核心功能] 工业级 Canvas 预览与图表渲染
// ==============================================================================
const addCanvasLog = (msg) => {
  canvasLogs.value.push(`[${new Date().toLocaleTimeString('zh-CN', {hour12:false})}] ${msg}`);
};

const switchCanvasTab = async (tab) => {
  canvasTab.value = tab;
  if (tab === 'preview' && !canvasCode.value.includes('<html')) {
    await nextTick();
    renderVisualization();
  }
};

const renderVisualization = () => {
  if (!canvasChartRef.value) return;
  if (canvasChartInstance) canvasChartInstance.dispose();
  canvasChartInstance = echarts.init(canvasChartRef.value);
  
  // 模拟工业领域：设备特征频率与异常置信度图表
  const option = {
    backgroundColor: 'transparent',
    title: { text: '设备特征参量偏离度分析', left: 'center', textStyle: { color: '#cbd5e1', fontSize: 14, fontWeight: 'normal' }, top: 10 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '5%', right: '5%', bottom: '15%', top: '20%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: ['有效值(RMS)', '峰值(Peak)', '峭度(Kurtosis)', '波形因子', '外圈BPFO'],
      axisLabel: { color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#334155' } }
    },
    yAxis: { 
      type: 'value', splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }, axisLabel: { color: '#94a3b8' }
    },
    series: [{ 
      name: '当前监测值', type: 'bar', barWidth: '40%',
      data: [
        { value: 1.2, itemStyle: { color: '#3b82f6' } }, // 正常
        { value: 2.8, itemStyle: { color: '#3b82f6' } }, 
        { value: 8.5, itemStyle: { color: '#ef4444' } }, // 峭度极高（异常）
        { value: 1.4, itemStyle: { color: '#3b82f6' } },
        { value: 92.5, itemStyle: { color: '#f59e0b' } } // 某特征频率幅值高
      ],
      itemStyle: { borderRadius: [4, 4, 0, 0] }
    }]
  };
  canvasChartInstance.setOption(option);
};

// ==============================================================================
// [重构] 核心流式发送与 Canvas 自动调度
// ==============================================================================
const stopGeneration = () => {
  if (abortController.value) { abortController.value.abort(); abortController.value = null; isLoading.value = false; updateCurrentSession(); }
};

const sendMessage = async () => {
  if (isFileParsing.value) { alert("正在解析文件，请稍候..."); return; }
  if ((!inputText.value.trim() && !selectedFile.value) || isLoading.value) return;

  const userInputText = inputText.value;
  inputText.value = '';
  const currentFile = selectedFile.value ? { name: selectedFile.value.name, size: selectedFile.value.size } : null;
  const currentFileContent = fileContent.value;
  selectedFile.value = null; fileContent.value = ''; if(fileInput.value) fileInput.value.value = '';

  messages.value.push({ role: 'user', content: userInputText, file: currentFile });
  const isNewSession = !activeSessionId.value;
  updateCurrentSession(isNewSession, userInputText); 
  
  isLoading.value = true;
  loadingText.value = '深度思考中...'; 
  messages.value.push({ role: 'assistant', content: '', reasoning: '', isExpanded: true, error: null });
  const currentMsg = messages.value[messages.value.length - 1];
  
  await nextTick();
  scrollToBottom();
  abortController.value = new AbortController();

  let finalPayloadContent = userInputText;
  if (currentFile) {
    const truncatedContent = currentFileContent.length > 30000 ? currentFileContent.substring(0, 30000) + "\n...[内容过长已截断]..." : currentFileContent;
    finalPayloadContent = `【用户上传文件上下文】\n文件名：${currentFile.name}\n内容片段：\n${truncatedContent}\n\n【用户问题】：\n${userInputText}`;
  }

  if (isKnowledgeActive.value) {
    loadingText.value = '正在检索图谱知识库...'; 
    const graphContext = await fetchGraphData();
    if (graphContext) { finalPayloadContent = `【系统注入：本地知识库上下文】\n${graphContext}\n\n${finalPayloadContent}`; }
    loadingText.value = '深度思考中...'; 
  }

  // 【核心修改：专为工业领域定制的系统提示词】
  let systemPrompt = "你是一个专业的工业运维助手。请针对工业设备维修、故障检测等领域提供专业的解答。";
  if (isAgentActive.value && currentFile) {
    systemPrompt = `你是一个高级工业数据分析师和设备运维专家。
    【核心任务】：分析工业传感器数据，进行故障诊断与预测性维护。
    【工作流要求】：
    1. 必须编写代码进行数据处理、特征提取或模型推理。
    2. 如果是数据计算，请输出 Python 代码（使用 \`\`\`python 包裹）。
    3. 如果用户明确需要一个交互式的监控面板大屏，请输出单文件 HTML 代码（使用 \`\`\`html 包裹，可内嵌 ECharts）。
    4. 在代码执行完毕后，务必结合计算结果和知识库，给出具体的故障原因和维修指导方案。`;
  }
  
  try {
    const payload = { 
      model: "deepseek-ai/DeepSeek-R1", 
      messages: [ 
        { role: "system", content: systemPrompt }, 
        ...messages.value.slice(0, -1).filter(m => m.role !== 'assistant' || m.content).map(m => ({ role: m.role, content: m.content || " " })), 
        { role: "user", content: finalPayloadContent } 
      ], 
      stream: true, temperature: 0.6 
    };

    const response = await fetch(API_URL, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${API_KEY}` }, body: JSON.stringify(payload), signal: abortController.value.signal });
    if (!response.ok) throw new Error(`API Error: ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    
    let buffer = '';
    let inCodeBlock = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6); 
          if (jsonStr.trim() === '[DONE]') break; 
          try {
            const data = JSON.parse(jsonStr);
            const delta = data.choices[0].delta;
            
            // 1. 深度思考：始终在左侧聊天气泡
            if (delta.reasoning_content) { 
              currentMsg.reasoning += delta.reasoning_content; 
              if (currentMsg.isExpanded) scrollToBottom(); 
            }

            // 2. 正文分流：文本留左侧，代码去 Canvas
            if (delta.content) {
              const piece = delta.content;
              
              if (!inCodeBlock) {
                buffer += piece;
                // 检测代码块起始
                const match = buffer.match(/```(python|html|javascript)?\n?/i);
                if (match) {
                  inCodeBlock = true;
                  const textBeforeCode = buffer.substring(0, match.index);
                  if (textBeforeCode) currentMsg.content += textBeforeCode;
                  
                  // 开启 Canvas 工作台
                  isCanvasOpen.value = true;
                  canvasTab.value = 'code';
                  canvasCode.value = '';
                  canvasLogs.value = [];
                  addCanvasLog("正在构建工业分析流...");
                  
                  canvasCode.value += buffer.substring(match.index + match[0].length);
                  buffer = '';
                  
                  // 在聊天区留下卡片提示
                  currentMsg.content += "\n\n> ⚙️ *AI 正在右侧工作台编写并执行分析脚本...*\n\n";
                  scrollToBottom();
                } else if (buffer.length > 20 || piece.includes('\n')) {
                  currentMsg.content += buffer;
                  buffer = '';
                  scrollToBottom();
                }
              } else {
                buffer += piece;
                const endMatch = buffer.indexOf('```');
                if (endMatch !== -1) {
                  inCodeBlock = false;
                  canvasCode.value += buffer.substring(0, endMatch);
                  
                  // 【专属工业场景模拟执行】
                  addCanvasLog("数据读取完成。");
                  addCanvasLog("执行算法管道...");
                  
                  setTimeout(() => {
                    addCanvasLog(">> 提取时域特征: RMS, Kurtosis, Peak");
                    addCanvasLog(">> 频域转换: FFT 频谱分析...");
                    addCanvasLog(">> 诊断结果: 发现轴承外圈特征频率(BPFO)异常幅值。");
                    addCanvasLog("执行完毕，渲染可视化报告...");
                    setTimeout(() => {
                      switchCanvasTab('preview');
                    }, 800);
                  }, 1200);

                  buffer = buffer.substring(endMatch + 3);
                  currentMsg.content += buffer;
                } else {
                  canvasCode.value += buffer;
                  buffer = '';
                }
              }
            }
          } catch (e) {}
        }
      }
      updateCurrentSession();
    }
    if (buffer && !inCodeBlock) { currentMsg.content += buffer; scrollToBottom(); }
    else if (buffer && inCodeBlock) { canvasCode.value += buffer; }

  } catch (error) {
    if (error.name !== 'AbortError') { currentMsg.error = `请求失败: ${error.message}`; }
    updateCurrentSession();
  } finally {
    isLoading.value = false; abortController.value = null; scrollToBottom(); updateCurrentSession();
  }
};

const scrollToBottom = async () => { await nextTick(); if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight; };
const toggleReasoning = (index) => { messages.value[index].isExpanded = !messages.value[index].isExpanded; updateCurrentSession(); };
</script>

<template>
  <div class="chat-layout">
    <div class="left-panel">
      <button class="new-chat-btn" @click="startNewChat">
        <Plus size="16" /> 开启新对话
      </button>
      
      <div class="history-list">
        <div class="time-group-header">
          <span class="time-group">历史记录</span>
          <button class="clear-all-btn" @click="clearAllSessions" title="清空所有记录"><Trash2 size="12" /> 清空</button>
        </div>
        <div v-if="chatSessions.length === 0" class="empty-history">暂无历史对话</div>

        <div v-for="session in chatSessions" :key="session.id" class="history-item" :class="{ 'active': session.id === activeSessionId }" @click="switchSession(session)">
          <div v-if="editingSessionId === session.id" class="edit-mode-box">
            <input ref="renameInput" v-model="tempTitle" class="rename-input" @click.stop @keyup.enter="confirmRename" @blur="confirmRename" />
            <button class="icon-action-btn confirm" @click.stop="confirmRename"><Check size="14" /></button>
          </div>
          <template v-else>
            <div class="hi-content"><MessageSquare size="14" class="hi-icon" /><span class="hi-title">{{ session.title }}</span></div>
            <div class="hi-actions">
              <button class="icon-action-btn" @click="(e) => startRename(e, session)" title="重命名"><Edit2 size="12" /></button>
              <button class="icon-action-btn delete" @click="(e) => deleteSession(e, session.id)" title="删除"><Trash2 size="12" /></button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <div class="center-wrapper" :class="{ 'canvas-active': isCanvasOpen }">
      
      <div class="chat-panel" :class="{ 'initial-view': messages.length === 0 }">
        <div v-if="messages.length === 0" class="welcome-screen">
          <Bot size="64" class="bot-icon-lg" />
          <h2>今天有什么可以帮到你？</h2>
        </div>

        <div v-else class="chat-history-container" ref="chatContainer">
          <div v-for="(msg, index) in messages" :key="index" class="message-row" :class="msg.role === 'user' ? 'user-row' : 'ai-row'">
            <div class="avatar"><User v-if="msg.role === 'user'" size="24" /><Bot v-else size="24" /></div>
            <div class="message-content-wrapper">
              <div class="message-bubble" :class="{ 'error-bubble': msg.error }">
                
                <div v-if="msg.file" class="msg-file-card">
                  <div class="mf-icon"><FileText size="16" /></div>
                  <div class="mf-info"><div class="mf-name">{{ msg.file.name }}</div><div class="mf-size">{{ (msg.file.size / 1024).toFixed(1) }} KB</div></div>
                </div>
                
                <div v-if="msg.role === 'assistant' && msg.reasoning" class="thinking-section">
                  <div class="thinking-header" @click="toggleReasoning(index)">
                    <div class="th-left">
                      <component :is="msg.isExpanded ? ChevronDown : ChevronRight" size="14" />
                      <span v-if="isLoading && index === messages.length - 1 && !msg.content">{{ loadingText }}</span>
                      <span v-else>深度思考过程</span>
                    </div>
                    <span class="th-time" v-if="!isLoading || index !== messages.length - 1">已完成</span>
                  </div>
                  <div v-show="msg.isExpanded" class="thinking-body"><div class="reasoning-text">{{ msg.reasoning }}</div></div>
                </div>

                <div v-if="msg.content" class="markdown-body" style="white-space: pre-wrap;">{{ msg.content }}</div>
                <div v-if="msg.role === 'assistant' && isLoading && index === messages.length - 1 && !msg.reasoning && !msg.content" class="typing-cursor">▍</div>
                <div v-if="msg.error" class="error-msg"><AlertCircle size="14"/> {{ msg.error }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="input-area">
          <div v-if="selectedFile" class="file-preview-box">
            <div class="file-card">
              <div class="fc-icon"><Sparkles v-if="isFileParsing" size="20" class="spin-icon"/><FileText v-else size="20" /></div>
              <div class="fc-info"><div class="fc-name">{{ selectedFile.name }}</div><div class="fc-type">{{ isFileParsing ? '正在解析...' : (selectedFile.size / 1024).toFixed(1) + ' KB' }}</div></div>
              <button class="fc-close" @click="removeFile"><X size="14" /></button>
            </div>
          </div>

          <input type="text" v-model="inputText" @keyup.enter="sendMessage" placeholder="询问任何设备故障问题..." class="chat-input" />
          <div class="input-actions">
            <div class="action-tags">
              <span class="tag"><Sparkles size="14"/> 深度思考</span>
              <span class="tag" :class="{ 'active-tag': isKnowledgeActive }" @click="isKnowledgeActive = !isKnowledgeActive"><Database size="14"/> 知识库</span>
              <span class="tag" :class="{ 'active-tag': isAgentActive }" @click="isAgentActive = !isAgentActive"><Bot size="14"/> 算法库</span>
            </div>
            <div class="send-actions">
              <Paperclip class="icon-btn" size="20" @click="triggerFileUpload" />
              <input type="file" ref="fileInput" style="display:none" accept=".doc,.docx,.pdf,.xls,.xlsx,.txt,.csv,.md" @change="handleFileChange" />
              <button class="send-btn" @click="isLoading ? stopGeneration() : sendMessage()" :class="{ 'stop-active': isLoading }">
                <Square v-if="isLoading" size="14" fill="#ffffff" style="border-radius: 2px;" /><ArrowUp v-else size="20" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="isCanvasOpen" class="canvas-panel">
        
        <div class="canvas-header">
          <div class="ch-left">
            <LayoutTemplate size="16" class="ch-icon" />
            <span>智能分析工作台</span>
          </div>
          
          <div class="ch-center">
            <div class="canvas-switcher">
              <button :class="{ active: canvasTab === 'code' }" @click="switchCanvasTab('code')">
                <Code size="14" /> 代码
              </button>
              <button :class="{ active: canvasTab === 'preview' }" @click="switchCanvasTab('preview')">
                <Play size="14" /> 预览
              </button>
            </div>
          </div>
          
          <div class="ch-right">
            <button class="ch-close-btn" @click="isCanvasOpen = false"><X size="18" /></button>
          </div>
        </div>

        <div class="canvas-body">
          <div v-show="canvasTab === 'code'" class="canvas-view-code">
            <pre><code class="language-python">{{ canvasCode }}</code></pre>
            <div class="code-overlay-typing" v-if="isLoading && canvasTab === 'code'">
              <span class="blink">▍</span>
            </div>
          </div>

          <div v-show="canvasTab === 'preview'" class="canvas-view-preview">
            
            <div v-if="!canvasCode.includes('<html')" style="width: 100%; display: flex; flex-direction: column; gap: 20px; align-items: center;">
              <div class="preview-console-card">
                <div class="pcc-header">分析流终端 (Terminal)</div>
                <div class="pcc-body">
                  <div v-for="(log, idx) in canvasLogs" :key="idx" class="pcc-log-line">
                    <span class="pcc-arrow">➜</span> {{ log }}
                  </div>
                  <div v-if="isLoading" class="pcc-log-line blink">_</div>
                </div>
              </div>
              <div class="preview-chart-card">
                <div ref="canvasChartRef" class="echarts-container"></div>
              </div>
            </div>

            <div v-else class="preview-iframe-card">
              <iframe 
                :srcdoc="canvasCode" 
                sandbox="allow-scripts allow-same-origin"
                class="dynamic-iframe"
                frameborder="0"
              ></iframe>
            </div>

          </div>
        </div>

      </div>

    </div>
  </div>
</template>

<style scoped>
/* ================= 全局 & 侧边栏样式 ================= */
.chat-layout { display: flex; height: 100%; background-color: #f8fafc; color: #1e293b; }
.left-panel { width: 260px; background-color: #ffffff; padding: 20px; border-right: 1px solid #e0f2fe; display: flex; flex-direction: column; flex-shrink: 0; z-index: 10; }
.new-chat-btn { background-color: #3b82f6; color: white; border: none; padding: 10px; border-radius: 6px; display: flex; align-items: center; justify-content: center; gap: 8px; cursor: pointer; font-weight: bold; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2); transition: background 0.2s; }
.new-chat-btn:hover { background-color: #2563eb; }

.time-group-header { display: flex; justify-content: space-between; align-items: center; margin: 15px 0 5px 0; }
.time-group { color: #94a3b8; font-size: 12px; font-weight: 600; }
.clear-all-btn { background: transparent; border: none; color: #94a3b8; font-size: 11px; cursor: pointer; display: flex; align-items: center; gap: 3px; }
.clear-all-btn:hover { color: #ef4444; }

.history-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 5px; }
.history-item { display: flex; justify-content: space-between; align-items: center; color: #334155; font-size: 14px; padding: 10px 12px; cursor: pointer; border-radius: 6px; transition: all 0.2s; position: relative; }
.history-item:hover { background-color: #f1f5f9; }
.history-item.active { background-color: #eff6ff; color: #3b82f6; font-weight: 500; }
.hi-content { display: flex; align-items: center; gap: 8px; overflow: hidden; flex: 1; }
.hi-icon { flex-shrink: 0; }
.hi-title { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; }
.hi-actions { display: flex; align-items: center; gap: 4px; opacity: 0; transition: opacity 0.2s; }
.history-item:hover .hi-actions { opacity: 1; }
.icon-action-btn { background: transparent; border: none; color: #94a3b8; cursor: pointer; padding: 4px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
.icon-action-btn:hover { background-color: #e2e8f0; color: #3b82f6; }
.icon-action-btn.delete:hover { color: #ef4444; }
.icon-action-btn.confirm { color: #10b981; }
.edit-mode-box { display: flex; align-items: center; width: 100%; gap: 5px; }
.rename-input { flex: 1; border: 1px solid #bfdbfe; border-radius: 4px; padding: 4px 6px; font-size: 13px; outline: none; color: #1e293b; background-color: #fff; }
.rename-input:focus { border-color: #3b82f6; }
.empty-history { font-size: 13px; color: #94a3b8; text-align: center; margin-top: 20px; }

/* ================= 动态双栏布局 ================= */
.center-wrapper { flex: 1; display: flex; position: relative; min-width: 0; height: 100%; overflow: hidden; background-color: #f8fafc; }
.chat-panel { flex: 1; display: flex; flex-direction: column; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); height: 100%; }
.canvas-active .chat-panel { width: 40%; max-width: 600px; border-right: 1px solid #e2e8f0; flex: none; }

/* ================= Canvas 工作台 (右侧) ================= */
.canvas-panel {
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  background-color: #ffffff;
  animation: slideInRight 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  min-width: 0;
}
@keyframes slideInRight { from { transform: translateX(50px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

.canvas-header {
  height: 60px; padding: 0 20px; display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid #f1f5f9; background-color: #ffffff;
}
.ch-left { display: flex; align-items: center; gap: 8px; font-weight: 600; color: #334155; font-size: 15px; }
.ch-icon { color: #3b82f6; }
.ch-right { display: flex; align-items: center; }
.ch-close-btn { background: transparent; border: none; color: #94a3b8; cursor: pointer; padding: 4px; border-radius: 4px; display: flex; align-items: center; transition: all 0.2s; }
.ch-close-btn:hover { background-color: #f1f5f9; color: #ef4444; }

.canvas-switcher { display: flex; background-color: #f1f5f9; padding: 4px; border-radius: 8px; gap: 4px; }
.canvas-switcher button {
  background: transparent; border: none; padding: 6px 16px; border-radius: 6px;
  font-size: 13px; font-weight: 500; color: #64748b; cursor: pointer;
  display: flex; align-items: center; gap: 6px; transition: all 0.2s;
}
.canvas-switcher button:hover { color: #1e293b; }
.canvas-switcher button.active { background-color: #ffffff; color: #3b82f6; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }

.canvas-body { flex: 1; overflow: hidden; position: relative; background-color: #f8fafc; }

.canvas-view-code {
  height: 100%; width: 100%; overflow-y: auto; padding: 20px;
  background-color: #1e293b; position: relative;
}
.canvas-view-code pre { margin: 0; }
.canvas-view-code code { font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; line-height: 1.6; color: #e2e8f0; white-space: pre-wrap; word-wrap: break-word; }
.code-overlay-typing { position: absolute; bottom: 20px; left: 20px; color: #3b82f6; font-size: 16px; }

.canvas-view-preview { height: 100%; width: 100%; overflow-y: auto; padding: 30px; display: flex; flex-direction: column; gap: 20px; align-items: center; }

/* 工业终端卡片 */
.preview-console-card { width: 100%; max-width: 800px; background-color: #0f172a; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
.pcc-header { background-color: #1e293b; padding: 10px 15px; font-size: 12px; color: #94a3b8; font-family: 'Consolas', monospace; border-bottom: 1px solid #334155; }
.pcc-body { padding: 15px; font-family: 'Consolas', monospace; font-size: 13px; color: #cbd5e1; line-height: 1.6; min-height: 80px;}
.pcc-arrow { color: #10b981; margin-right: 8px; }

/* 工业分析图表卡片 */
.preview-chart-card { width: 100%; max-width: 800px; height: 350px; background-color: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
.echarts-container { width: 100%; height: 100%; }

/* Iframe 卡片 (用于渲染完整 HTML 监控大屏) */
.preview-iframe-card { width: 100%; height: 100%; min-height: 500px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px -3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; display: flex; flex-direction: column; }
.dynamic-iframe { width: 100%; height: 100%; flex: 1; background-color: #ffffff; }

/* ================= 聊天内容区样式 ================= */
.chat-panel.initial-view { justify-content: center; align-items: center; padding-bottom: 100px; }
.chat-panel:not(.initial-view) { justify-content: flex-end; }
.welcome-screen { text-align: center; margin-bottom: 40px; }
.welcome-screen h2 { color: #1e293b; margin-top: 20px; }
.bot-icon-lg { color: #1e293b !important; filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.2)); }
.chat-history-container { flex: 1; overflow-y: auto; padding: 20px 8%; display: flex; flex-direction: column; gap: 25px; }

.message-row { display: flex; gap: 15px; width: 100%; }
.user-row { flex-direction: row-reverse; }
.ai-row { align-self: flex-start; }
.message-content-wrapper { max-width: 85%; min-width: 200px; }
.avatar { width: 36px; height: 36px; background-color: #e2e8f0; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #64748b; }
.ai-row .avatar { background-color: #eff6ff; color: #3b82f6; }
.user-row .avatar { background-color: #f1f5f9; color: #64748b; }

.message-bubble { background-color: #ffffff; padding: 12px 16px; border-radius: 12px; color: #334155; line-height: 1.6; font-size: 15px; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 8px; }
.user-row .message-bubble { background-color: #e0f2fe; color: #1e293b; border: 1px solid #bae6fd; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.error-bubble { border-color: #fecaca !important; background-color: #fef2f2 !important; }

.msg-file-card { display: flex; align-items: center; gap: 10px; background-color: #ffffff; padding: 8px 12px; border-radius: 8px; margin-bottom: 4px; max-width: 100%; border: 1px solid #e2e8f0; }
.user-row .msg-file-card { background-color: #ffffff; border-color: #bfdbfe; }
.user-row .msg-file-card .mf-name { color: #334155; font-weight: 600; font-size: 13px; }
.user-row .msg-file-card .mf-size { color: #64748b; font-size: 11px; }
.user-row .msg-file-card .mf-icon { color: #0284c7; background-color: #f0f9ff; }
.mf-icon { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; background-color: #f1f5f9; border-radius: 6px; }
.mf-info { display: flex; flex-direction: column; justify-content: center; overflow: hidden; }
.mf-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }

/* 左侧思考框 */
.thinking-section { background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 8px; overflow: hidden; }
.thinking-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background-color: #f1f5f9; cursor: pointer; font-size: 12px; color: #64748b; user-select: none; transition: background 0.2s; }
.thinking-header:hover { background-color: #e2e8f0; }
.th-left { display: flex; align-items: center; gap: 6px; font-weight: 600; }
.th-time { opacity: 0.6; font-size: 11px; }
.thinking-body { padding: 12px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; }
.reasoning-text { font-family: 'Consolas', 'Monaco', monospace; font-size: 13px; color: #94a3b8; line-height: 1.5; white-space: pre-wrap; }

.markdown-body { line-height: 1.6; }
.markdown-body blockquote { border-left: 3px solid #3b82f6; margin: 0; padding-left: 10px; color: #64748b; background-color: #f8fafc; border-radius: 4px; }

/* ================= 底部输入区 ================= */
.input-area { width: 85%; max-width: 900px; background-color: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid #e2e8f0; flex-shrink: 0; transition: all 0.5s ease; box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.05); display: flex; flex-direction: column; margin: 20px auto; }
.canvas-active .input-area { width: 92%; } 
.chat-input { width: 100%; background: transparent; border: none; color: #1e293b; font-size: 16px; outline: none; margin-bottom: 15px; font-family: inherit; }
.chat-input::placeholder { color: #94a3b8; }
.input-actions { display: flex; justify-content: space-between; align-items: center; }
.action-tags { display: flex; gap: 10px; flex-wrap: wrap; }
.file-preview-box { margin-bottom: 10px; }
.file-card { display: inline-flex; align-items: center; gap: 10px; background-color: #f1f5f9; border-radius: 8px; padding: 8px 12px; border: 1px solid #e2e8f0; max-width: 100%; }
.fc-icon { display: flex; align-items: center; justify-content: center; background-color: #ffffff; width: 32px; height: 32px; border-radius: 6px; color: #3b82f6; border: 1px solid #e2e8f0; }
.fc-info { display: flex; flex-direction: column; justify-content: center; overflow: hidden; }
.fc-name { font-size: 13px; font-weight: 600; color: #334155; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }
.fc-type { font-size: 11px; color: #94a3b8; }
.fc-close { background: transparent; border: none; cursor: pointer; color: #94a3b8; display: flex; align-items: center; justify-content: center; padding: 4px; border-radius: 4px; transition: all 0.2s; }
.fc-close:hover { background-color: #e2e8f0; color: #ef4444; }
.tag { background-color: #f1f5f9; padding: 4px 12px; border-radius: 20px; font-size: 12px; display: flex; align-items: center; gap: 5px; color: #64748b; border: 1px solid #e2e8f0; cursor: pointer; transition: all 0.2s; user-select: none; }
.tag:hover { background-color: #e2e8f0; color: #334155; }
.active-tag { background-color: #eff6ff !important; color: #3b82f6 !important; border-color: #bfdbfe !important; }
.send-actions { display: flex; align-items: center; gap: 10px; }
.icon-btn { cursor: pointer; color: #94a3b8; transition: color 0.2s; }
.icon-btn:hover { color: #3b82f6; }
.send-btn { background-color: #f8fafc; border: 1px solid #e2e8f0; color: #64748b; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; }
.send-btn:hover:not(:disabled) { background-color: #3b82f6; border-color: #3b82f6; color: white; box-shadow: 0 2px 5px rgba(59, 130, 246, 0.3); }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.stop-active { background-color: #3b82f6 !important; border-color: #3b82f6 !important; color: white !important; }
.stop-active:hover { background-color: #2563eb !important; }
.typing-cursor { color: #3b82f6; animation: blink 1s step-end infinite; font-weight: bold; }
.spin-icon { animation: spin 2s linear infinite; }
.error-msg { font-size: 12px; color: #ef4444; margin-top: 5px; display: flex; align-items: center; gap: 5px; }

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
</style>