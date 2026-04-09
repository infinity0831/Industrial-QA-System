<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { Search, Database, RefreshCw, Clock, Trash2, PlusCircle, ExternalLink } from 'lucide-vue-next';
import * as echarts from 'echarts'; 

const searchText = ref('');
const chartRef = ref(null);
let myChart = null; 

// ==========================================
// 1. 颜色映射配置
// ==========================================
// 确保这里的 Key 与 Neo4j 中的 Label (Category Name) 一致
const categoryStyleMap = {
  // 英文 Key (后端返回的 category.name)
  'Area':      { color: '#64748b', size: 40 }, // 灰色：区域
  'Solution':  { color: '#3b82f6', size: 15 }, // 蓝：解决方案
  'Equipment': { color: '#10b981', size: 30 }, // 绿：主设备
  'Fault':     { color: '#f59e0b', size: 20 }, // 橙：故障
  'Component': { color: '#ef4444', size: 20 }, // 红：部件
  'Symptom':   { color: '#8b5cf6', size: 15 }, // 紫：现象
  
  // 中文 Key (以防后端返回中文)
  '区域':      { color: '#64748b', size: 40 },
  '解决方案':  { color: '#3b82f6', size: 15 },
  '设备':      { color: '#10b981', size: 30 },
  '故障':      { color: '#f59e0b', size: 20 },
  '部件':      { color: '#ef4444', size: 20 },
  '现象':      { color: '#8b5cf6', size: 15 },
  
  // 默认兜底
  'default':   { color: '#94a3b8', size: 15 }
};

const refreshAll = async () => {
  if (!myChart && chartRef.value) myChart = echarts.init(chartRef.value);
  myChart?.showLoading(loadingConfig);

  try {
    // 1. 获取全量数据
    const response = await fetch(`http://localhost:8000/api/graph?t=${new Date().getTime()}`);
    const fullData = await response.json();

    // 2. 格式化数据（不再过滤，保留所有节点）
    // 这一步关键是把颜色配置注入到 nodes 和 categories 中
    const formattedData = processGraphData(fullData);
    
    myChart?.hideLoading();
    renderChart(myChart, formattedData);

  } catch (error) {
    console.error("图谱数据加载失败:", error);
    myChart?.hideLoading();
  }
};

// --- 数据处理函数：上色与格式化 ---
const processGraphData = (sourceData) => {
  if (!sourceData || !sourceData.nodes) return { nodes: [], links: [], categories: [] };

  // 1. 处理分类 (Categories) - 关键：给图例上色
  const formattedCategories = sourceData.categories.map(cat => {
    const style = categoryStyleMap[cat.name] || categoryStyleMap['default'];
    return {
      name: cat.name,
      itemStyle: { color: style.color } //这里显式指定颜色，图例就会自动变色
    };
  });

  // 2. 处理节点 (Nodes)
  const formattedNodes = sourceData.nodes.map(node => {
    // 确定分类名称
    let categoryName = 'default';
    if (typeof node.category === 'number' && sourceData.categories[node.category]) {
      categoryName = sourceData.categories[node.category].name;
    } else if (typeof node.category === 'string') {
      categoryName = node.category;
    }

    // 获取样式
    const style = categoryStyleMap[categoryName] || categoryStyleMap['default'];
    
    return {
      ...node,
      // 强制使用样式表中的大小和颜色
      symbolSize: style.size,
      itemStyle: { 
        color: style.color,
        borderColor: '#fff', // 加个白边让节点更清晰
        borderWidth: 1
      },
      category: node.category // 保持原始索引引用
    };
  });

  return { 
    nodes: formattedNodes, 
    links: sourceData.links, 
    categories: formattedCategories 
  };
};

const renderChart = (chartInstance, data) => {
  if (!chartInstance) return;
  if (data.nodes.length === 0) {
    chartInstance.clear();
    return;
  }

  const legendData = data.categories.map(c => c.name);

  const option = {
    title: { show: false },
    
    // 【修改点：优化 Tooltip 显示逻辑】
    tooltip: { 
      trigger: 'item', 
      formatter: (params) => {
        if (params.dataType === 'node') {
          // 节点提示：显示名称和类型
          // params.marker 是自带的小圆点颜色
          return `${params.marker} <strong>${params.name}</strong><br/>类型: ${params.data.categoryName || '实体'}`;
        } else if (params.dataType === 'edge') {
          // 连线提示：显示关系名称
          // 尝试解析源和目标（如果params.name是"id > id"这种不友好的格式，这里只显示关系名会更整洁）
          return `关系类型: <strong>${params.data.value || 'Rel'}</strong>`;
        }
        return params.name;
      }
    },

    legend: [{
      data: legendData,
      textStyle: { color: '#64748b', fontSize: 11 },
      itemWidth: 14, 
      itemHeight: 14,
      top: 10,
      left: 'center',
      backgroundColor: 'rgba(255,255,255,0.8)',
      borderRadius: 4,
      padding: 5
    }],
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: data.nodes,
        links: data.links,
        categories: data.categories,
        roam: true,
        draggable: true,
        zoom: 0.6,
        label: {
          show: true,
          position: 'right', 
          formatter: '{b}',
          color: '#334155',
          fontSize: 10
        },
        labelLayout: { hideOverlap: true },
        // 连线上的标签（可选：如果您想直接在线上显示文字，可以开启这个）
        edgeLabel: {
          show: false, // 平时不显示，鼠标移上去显示 tooltip 即可，避免太乱
          formatter: '{c}' 
        },
        lineStyle: {
          color: '#94a3b8',
          curveness: 0.1,
          opacity: 0.5,
          width: 1
        },
        force: {
          repulsion: 1500,
          edgeLength: [150, 300],
          gravity: 0.02,
          layoutAnimation: true
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 3, color: '#3b82f6', opacity: 1 }
        }
      }
    ]
  };
  chartInstance.setOption(option);
};

const loadingConfig = {
  text: '同步 Neo4j 数据...',
  color: '#3b82f6',
  textColor: '#1e293b',
  maskColor: 'rgba(255, 255, 255, 0.9)'
};

const openNeo4jConsole = () => {
  window.open('http://localhost:7474/browser/', '_blank');
};

onMounted(() => {
  refreshAll();
  window.addEventListener('resize', handleResize);
});

const handleResize = () => {
  myChart && myChart.resize();
};

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  myChart?.dispose();
});
</script>

<template>
  <div class="knowledge-layout">
    <div class="sidebar">
      <button class="update-btn" @click="refreshAll">
         <RefreshCw size="16" style="margin-right:8px"/> 立即刷新图谱
      </button>
      <div class="update-list">
        <div class="list-title">今天</div>
        <div class="update-item">
          <div class="item-title">事件：知识库同步</div>
          <div class="item-time">状态：API 实时连接</div>
          <div class="item-desc">
            数据源：Neo4j<br>
            当前视图：钢铁设备全景
          </div>
        </div>
      </div>
    </div>

    <div class="main-content">
      <div class="search-bar">
        <div class="search-input-wrapper">
          <Search class="search-icon" size="18" />
          <input type="text" v-model="searchText" placeholder="输入节点名称搜索..." class="search-input" />
        </div>
        <div class="search-result-title"><Database size="16"/> 知识库概览</div>
      </div>

      <div class="cards-grid">
        <div class="knowledge-card active-card">
          <div class="card-header-row">
            <span class="header-title">厚板主轧线电机运维知识图谱</span>
            <button class="edit-icon-btn" @click="openNeo4jConsole">
              <ExternalLink size="16" /> 编辑
            </button>
          </div>
          <div ref="chartRef" class="chart-container"></div>
        </div>
      </div>

      <div class="bottom-actions">
        <button class="action-btn" @click="refreshAll"><RefreshCw size="16"/> 知识更新</button>
        <button class="action-btn"><PlusCircle size="16"/> 创建新知识</button>
        <button class="action-btn"><Clock size="16"/> 查看历史版本</button>
        <button class="action-btn delete-btn"><Trash2 size="16"/> 删除知识库</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 浅色主题 */
.knowledge-layout { display: flex; height: 100%; background-color: #f8fafc; color: #1e293b; }

.sidebar { width: 260px; background-color: #ffffff; padding: 20px; display: flex; flex-direction: column; border-right: 1px solid #e0f2fe; }

.update-btn { background-color: #3b82f6; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-weight: bold; margin-bottom: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
.update-btn:hover { background-color: #2563eb; }

.list-title { color: #334155; font-weight: bold; margin: 15px 0 10px 0; font-size: 14px; }

.update-item { background-color: #f1f5f9; border-radius: 6px; padding: 10px; margin-bottom: 10px; border-left: 3px solid #10b981; }
.item-title { font-size: 13px; font-weight: bold; margin-bottom: 5px; color: #1e293b; }
.item-time { font-size: 12px; color: #64748b; margin-bottom: 5px; }
.item-desc { font-size: 12px; color: #475569; line-height: 1.4; }

.main-content { flex: 1; padding: 20px 40px; display: flex; flex-direction: column; }
.search-bar { margin-bottom: 20px; }
.search-input-wrapper { display: flex; align-items: center; background-color: #ffffff; padding: 10px 15px; border-radius: 8px; width: 300px; margin-bottom: 20px; border: 1px solid #bfdbfe; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.search-icon { color: #94a3b8; margin-right: 10px; }
.search-input { background: transparent; border: none; color: #1e293b; width: 100%; outline: none; }
.search-result-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: bold; color: #1e293b; }

/* 全屏卡片布局 */
.cards-grid { 
  display: grid; 
  grid-template-columns: 1fr; 
  grid-template-rows: 1fr; 
  gap: 20px; 
  flex: 1; 
  min-height: 0; 
}

.knowledge-card { background-color: #ffffff; border-radius: 12px; border: 1px solid #bfdbfe; display: flex; flex-direction: column; padding: 15px; overflow: hidden; position: relative; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }

.active-card { 
  border: 1px solid #3b82f6; 
  background: radial-gradient(circle at center, #ffffff 0%, #eff6ff 100%); 
}
.chart-container { width: 100%; height: 100%; }

.card-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
.header-title { font-weight: bold; font-size: 14px; color: #1e293b; }

.edit-icon-btn { background: transparent; border: none; color: #64748b; cursor: pointer; display: flex; align-items: center; gap: 4px; font-size: 12px; padding: 4px 8px; border-radius: 4px; transition: all 0.2s; }
.edit-icon-btn:hover { background-color: #f1f5f9; color: #3b82f6; }

.bottom-actions { display: flex; justify-content: flex-end; gap: 15px; margin-top: 20px; }
.action-btn { background-color: #ffffff; border: 1px solid #e2e8f0; color: #334155; padding: 10px 20px; border-radius: 6px; display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.action-btn:hover { background-color: #f8fafc; border-color: #3b82f6; color: #3b82f6; }
.delete-btn { color: #94a3b8; }
.delete-btn:hover { color: #ef4444; border-color: #ef4444; }
</style>