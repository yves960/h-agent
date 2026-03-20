# claw0 整合计划

## claw0 vs learn-claude-code

| 项目 | 来源 | 侧重点 |
|------|------|--------|
| learn-claude-code | s01-s12 | Agent 内部设计、规划、子代理、团队协作 |
| claw0 | c03-c10 | 网关路由、通道、心跳、消息投递、弹性 |

## 整合计划

用 `c` 前缀标识 claw0 的模块：

| 模块 | 功能 | 状态 |
|------|------|:----:|
| s01-s12 | learn-claude-code 功能 | ✅ 已完成 |
| **c03** | Sessions（会话持久化） | ⏳ 待实现 |
| **c04** | Channels（Telegram, Feishu 通道） | ⏳ 待实现 |
| **c05** | Gateway Routing（5层路由） | ⏳ 待实现 |
| **c06** | Intelligence（灵魂、记忆、技能） | ⏳ 待实现 |
| **c07** | Heartbeat & Cron（心跳和定时任务） | ⏳ 待实现 |
| **c08** | Delivery（消息队列、可靠投递） | ⏳ 待实现 |
| **c09** | Resilience（3层重试、认证轮换） | ⏳ 待实现 |
| **c10** | Concurrency（命名车道并发） | ⏳ 待实现 |

## 整合后的完整架构

```
+------------------- openai-agent-harness -------------------+
|                                                           |
| s10: Concurrency (named lanes, generation track)         |
| s09: Resilience (auth rotation, overflow compact)        |
| s08: Delivery (write-ahead queue, backoff)               |
| s07: Heartbeat (lane lock, cron scheduler)               |
| s06: Intelligence (8-layer prompt, hybrid memory)        |
| s05: Gateway (WebSocket, 5-tier routing)                 |
| s04: Channels (Telegram pipeline, Feishu hook)           |
| s03: Sessions (JSONL persistence, 3-stage retry)         |
| s02: Tools (dispatch table, 4 tools)                     |
| s01: Agent Loop (while True + stop_reason)               |
|                                                           |
+-----------------------------------------------------------+
```

## 实现顺序

1. **c03 Sessions** - 会话持久化（JSONL 格式）
2. **c04 Channels** - 多通道支持
3. **c05 Gateway** - 网关路由
4. **c06 Intelligence** - 智能系统
5. **c07 Heartbeat** - 心跳机制
6. **c08 Delivery** - 消息投递
7. **c09 Resilience** - 弹性重试
8. **c10 Concurrency** - 并发控制