# Zoo 集成指南

## 在 zoo 中添加 OpenAI Agent

### 1. 复制 agent 文件到 zoo

```bash
# 创建目录
mkdir -p ~/Projects/self/zoo/agents_openai

# 复制核心文件
cp ~/Projects/self/openai-agent-harness/s03_todo_write.py ~/Projects/self/zoo/agents_openai/
cp ~/Projects/self/openai-agent-harness/zoo_adapter.py ~/Projects/self/zoo/agents_openai/
```

### 2. 修改 zoo 的 agents/__init__.py

添加 OpenAI Agent 到服务列表：

```python
from .openai_agent import OpenAIAgentService

def get_animal_services() -> dict[str, AnimalService]:
    return {
        "xueqiu": XueqiuService(),
        "liuliu": LiuliuService(),
        "xiaohuang": XiaohuangService(),
        "openai": OpenAIAgentService(),  # 新增
    }
```

### 3. 更新 API 端点

`/api/api/animals` 会自动返回新的 agent 信息。

### 4. 测试

```bash
curl http://localhost:8001/api/api/animals
```

返回：
```json
{
  "animals": {
    "xueqiu": {...},
    "liuliu": {...},
    "xiaohuang": {...},
    "openai": {
      "name": "OpenAI Agent",
      "species": "AI Assistant",
      "cli": "openai-agent",
      "color": "#9B59B6"
    }
  }
}
```

## 配置

在 zoo 的 .env 中添加：

```
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
MODEL_ID=glm-4-flash
```