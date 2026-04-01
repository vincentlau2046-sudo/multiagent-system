# 实时状态管理与可视化

## 1. 状态同步机制

### 基于事件的状态更新
- **事件驱动架构**: 每个Agent状态变化触发事件
- **统一状态总线**: 所有状态事件发布到中央状态总线
- **实时订阅**: 主Agent和其他组件可订阅相关状态变化

### 状态事件类型
```json
{
  "eventType": "agent.status.update",
  "timestamp": "2026-04-01T14:05:00Z",
  "taskId": "20260401003",
  "agentId": "tech_analyst", 
  "status": "running|success|failed",
  "progress": 75,
  "qualityScores": {
    "completeness": 80,
    "accuracy": 85, 
    "depth": 70,
    "practicality": 60
  },
  "confidence": 76,
  "message": "技术分析完成，等待主审"
}
```

### 状态持久化
- 实时更新 `task_status.md` 表格
- 自动备份状态历史到 `memory/task_states/`
- 支持状态回滚和历史查询

## 2. 可视化进度跟踪

### 控制台实时显示
```
📋 任务: 中国MaaS市场深度分析 (20260401003)
├── 🤖 tech_analyst [██████████░░░░] 75% | 置信度: 76 | running
├── 🕵️ ai_intel     [██████████████] 100% | 置信度: 92 | success  
├── ✍️ content_creator [░░░░░░░░░░░░░░] 0%   | 置信度: -  | pending
└── 👑 主审状态: 等待tech_analyst完成
```

### Web界面集成
- OpenClaw控制UI实时显示任务进度
- 支持点击查看详情和手动干预
- 颜色编码状态：绿色(成功)、黄色(进行中)、红色(失败)

### 飞书通知集成
- 关键状态变更自动推送飞书消息
- 支持一键确认降级输出或人工介入
- 提供快速操作按钮（重试、终止、查看详情）

## 3. 任务依赖管理

### 依赖图构建
- 自动分析任务间的依赖关系
- 构建有向无环图(DAG)表示执行顺序
- 支持并行和串行混合依赖

### 依赖状态跟踪
```json
{
  "taskId": "20260401003",
  "dependencies": {
    "tech_analyst": ["ai_intel"],
    "content_creator": ["tech_analyst", "ai_intel"], 
    "main_review": ["tech_analyst", "content_creator"]
  },
  "executionGraph": {
    "nodes": ["ai_intel", "tech_analyst", "content_creator", "main_review"],
    "edges": [["ai_intel", "tech_analyst"], ["tech_analyst", "content_creator"], ["content_creator", "main_review"]]
  }
}
```

### 智能调度优化
- 根据依赖关系自动优化执行顺序
- 动态调整资源分配优先级
- 预测完成时间和潜在瓶颈

## 4. 监控与调试

### 实时日志
- 统一日志格式，包含任务ID、AgentID、时间戳
- 支持按任务ID过滤查看完整执行链路
- 自动标记异常和警告信息

### 性能指标
- Token消耗统计（按Agent和任务维度）
- 执行时间分析（各阶段耗时分布）
- 资源利用率监控（CPU、内存、网络）

### 调试工具
- 状态快照导出功能
- 任务重放和模拟执行
- 异常场景注入测试