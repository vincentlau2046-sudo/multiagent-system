# Multi-Agent System

## 概述
这是一个支持热插拔架构的多智能体协作系统，专为OpenClaw Agent生态设计。

## 核心特性

### 🔥 热插拔架构
- **Agent注册中心**: 支持动态注册/注销Agent
- **接口标准化**: 通过`AgentInterface`定义统一接口
- **配置驱动**: 任务路由规则通过YAML配置文件管理

### 🧠 智能调度
- **关键词匹配**: 基于任务描述自动匹配最佳Agent组合
- **工作流模式**: 支持并行(parallel)、串行(sequential)、混合(hybrid)三种执行模式
- **动态分配**: 自动识别主Agent和辅助Agent角色

### 📊 质量保障
- **置信度评估**: 基于完整性、准确性、深度、实用性四个维度评分
- **React机制**: 自动处理低置信度情况（重试/人工介入）
- **状态跟踪**: 实时监控任务执行状态和进度

### 🔄 状态同步
- **全局状态管理**: 统一的任务状态跟踪表
- **事件驱动**: 支持状态变更事件监听
- **飞书集成**: 自动同步到飞书文档

## 目录结构

```
multiagent-system/
├── __init__.py
├── agent_base.py          # Agent基类定义
├── agent_loader.py        # Agent动态加载器
├── agent_scheduler.py     # 任务调度器（主Agent内建）
├── multiagent_core.py     # 核心引擎
├── task_orchestrator.py   # 任务编排器
├── state_management.md    # 状态管理规范
├── react_mechanism.md     # React机制说明
├── quality_metrics.md     # 质量评估指标
├── exception_handling.md  # 异常处理策略
└── audit_react_log.md     # 审计日志规范
```

## 使用方式

### 主Agent调度流程
1. **接收任务**: 主Agent接收到用户任务请求
2. **路由匹配**: 调用`AgentScheduler`匹配任务类型
3. **生成命令**: 获取需要启动的Agent列表和任务内容
4. **执行调度**: 使用`sessions_spawn`工具启动子Agent
5. **状态跟踪**: 更新全局任务状态表

### 任务类型映射
```yaml
task_classification:
  - type: intelligence_collection    # 情报采集
    keywords: ["情报", "动态", "论文"]
    primary_agent: ai_intel
    
  - type: technical_analysis         # 技术分析  
    keywords: ["架构", "技术评估", "竞品分析"]
    primary_agent: tech_analyst
    secondary_agents: [ai_intel]
    
  - type: content_creation           # 内容创作
    keywords: ["公众号", "文章", "视频"]
    primary_agent: content_creator
    secondary_agents: [tech_analyst, ai_intel]
    
  - type: complex_research           # 深度研究
    keywords: ["深度研究", "综合分析", "战略报告"]
    primary_agent: tech_analyst
    secondary_agents: [ai_intel, official_operate]
    
  - type: math_tutoring              # 数学辅导
    keywords: ["数学", "小瑜", "辅导"]
    primary_agent: main
```

## Agent能力映射

| Agent ID | 名称 | 工作区 | 主要能力 |
|----------|------|--------|----------|
| `ai_intel` | AI情报官 | `workspace-AI-INTEL` | 情报采集、市场监控、趋势分析 |
| `tech_analyst` | 技术分析师 | `workspace-TECH-ANALYST` | 技术分析、架构拆解、战略规划 |
| `content_creator` | 内容创作官 | `workspace-CONTENT-CREATOR` | 公众号文章、视频脚本、内容策划 |
| `official_operate` | 官方运营官 | `workspace-OFFICIAL-OPERATE` | 运营策略、传播优化、用户增长 |
| `work-present-output` | 演示输出代理 | `workspace-WORK-PRESENT-OUTPUT` | PPT/HTML幻灯片、汇报视频 |

## 质量评估标准

### 置信度计算公式
```
置信度 = 完整性×权重 + 准确性×权重 + 深度×权重 + 实用性×权重
```

不同任务类型的权重分配：
- **情报采集**: 准确性(45%) > 完整性(30%) > 实用性(15%) > 深度(10%)
- **技术分析**: 准确性(35%) = 完整性(30%) > 深度(30%) > 实用性(5%)
- **内容创作**: 准确性(35%) = 完整性(30%) > 实用性(25%) > 深度(10%)
- **深度研究**: 准确性(35%) = 完整性(30%) > 深度(25%) > 实用性(10%)

### 自动审核流程
1. **自审**: Agent完成任务后自我评估
2. **交叉审**: 相关Agent互相审核（如适用）
3. **主审**: 置信度<90时触发主Agent审核
4. **React**: 置信度<70时触发重试或人工介入

## 部署要求

- **Python版本**: >= 3.8
- **依赖库**: pyyaml, dataclasses (Python < 3.7)
- **OpenClaw版本**: >= 2.0
- **工作区配置**: 各Agent对应的工作区目录需预先创建

## 开发指南

### 添加新Agent
1. 实现`AgentInterface`接口
2. 在`shared/agent_capabilities.yaml`中注册能力
3. 更新`shared/task_routing_rules.yaml`添加路由规则

### 扩展任务类型
1. 在路由规则中添加新的`task_classification`条目
2. 配置对应的关键词和Agent分配
3. 如需特殊质量评估权重，在`QualityMetrics.calculate_confidence()`中添加

## 版本历史

### v1.0.0 (2026-04-01)
- 初始版本发布
- 实现热插拔架构核心功能
- 支持四种任务类型调度
- 集成质量评估和React机制
- 提供完整的状态跟踪能力

## 许可证
MIT License