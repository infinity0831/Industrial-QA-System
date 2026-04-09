# main.py
from fastapi import FastAPI
from neo4j import GraphDatabase
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 1. 允许 Vue 访问 (CORS 设置)
# 这一步非常重要，否则前端会被浏览器拦截
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 连接 Neo4j 数据库
# 注意：密码已设置为 wuxian0831
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "wuxian0831")

@app.get("/")
def read_root():
    return {"status": "Backend is running!"}

@app.get("/api/graph")
def get_graph_data():
    """
    从 Neo4j 获取所有节点和关系，并整理成 ECharts 需要的格式
    """
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    nodes = []
    links = []
    categories = []
    
    # 类别映射（为了给图谱上色）
    category_set = set()

    with driver.session() as session:
        # 查询所有节点和关系
        result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m")
        
        seen_nodes = set()
        
        for record in result:
            n = record["n"]  # 起始节点
            m = record["m"]  # 结束节点
            r = record["r"]  # 关系
            
            # 处理节点 n
            if n.element_id not in seen_nodes:
                # 获取节点的标签（例如 Equipment, Fault）作为类别
                label = list(n.labels)[0] if n.labels else "Unknown"
                category_set.add(label)
                
                nodes.append({
                    "id": n.element_id,
                    "name": n.get("name") or n.get("desc", "未知节点"),
                    "category": label,
                    "symbolSize": 40 if label == "Equipment" else 20, # 设备节点大一点
                    "draggable": True
                })
                seen_nodes.add(n.element_id)
            
            # 处理节点 m
            if m.element_id not in seen_nodes:
                label = list(m.labels)[0] if m.labels else "Unknown"
                category_set.add(label)
                
                nodes.append({
                    "id": m.element_id,
                    "name": m.get("name") or m.get("desc", "未知节点"),
                    "category": label,
                    "symbolSize": 20,
                    "draggable": True
                })
                seen_nodes.add(m.element_id)
            
            # 处理关系 r
            links.append({
                "source": n.element_id,
                "target": m.element_id,
                "value": type(r).__name__ # 关系名称，如 HAS_COMPONENT
            })
            
    driver.close()
    
    # 整理类别列表
    for cat in category_set:
        categories.append({"name": cat})
        
    return {
        "nodes": nodes,
        "links": links,
        "categories": categories
    }

if __name__ == "__main__":
    import uvicorn
    # 启动服务，端口 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)