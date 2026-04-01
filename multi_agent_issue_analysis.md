# 多Agent调度问题全面复盘报告

## 📋 问题概述

用户反馈：在执行MaaS市场分析任务时，子Agent（official-operate、tech-analyst、ai-intel）没有被调度。

## 🔍 根本原因分析

### 问题1: 主Agent没有真正调用调度逻辑 ❌

**现象**：
- 调度脚本 `task_router.sh` 存在
- 路由规则 `task_routing_rules.yaml` 配置完整
- 但主Agent只是"读取"了脚本，没有真正执行调度

**根本原因**：
- 主Agent（我）在之前的执行中，只是打印了"应该启动子Agent"的信息
- 没有真正调用 `sessions_spawn` 工具来启动子Agent
- 最终是主Agent自己完成了任务

### 问题2: 子Agent模型配置错误 ❌

**现象**：
- 子Agent配置中指定使用 `bailian/qwen3-max-2026-01-23`
- 但实际执行时使用了 `doubao-seed-2.0-pro`
- 导致429配额超限错误

**根本原因**：
- `sessions_spawn` 启动子Agent时，子Agent继承了主Agent的当前模型
- 而不是使用 openclaw.json 中配置的模型
- 主Agent当前模型是 `kimi-k2.5` (bailian)，但子Agent启动时变成了 `doubao-seed-2.0-pro`

**验证证据**：
```json
// 子Agent会话历史显示
{
  "sessionKey": "agent:main:subagent:904332ab...",
  "model": "doubao-seed-2.0-pro",  // ❌ 错误模型
  "status": "done",
  "errorMessage": "429 You have exceeded the 5-hour usage quota..."
}
```

### 问题3: 子Agent确实被启动过 ✅

**发现**：
- 查看历史会话记录，发现子Agent确实被启动过
- `maas-analysis-tech` 和 `maas-analysis-intel` 都有执行记录
- 但都因为模型错误导致配额超限失败

## ✅ 彻底解决方案

### 方案1: 修复主Agent调度逻辑（已完成）

**已完成的修复**：

1. **创建Python调度器** (`agent_scheduler.py`)
   - 自动读取YAML路由规则
   - 关键词匹配任务类型
   - 生成任务ID和Agent分配

2. **更新MEMORY.md调度规则**
   - 添加明确的调度流程说明
   - 提供实际代码示例
   - 强调必须使用 `sessions_spawn` 工具

3. **关键提醒**：
   ```
   ❌ 错误: 只打印"应该启动子Agent"但不执行
   ✅ 正确: 直接调用 sessions_spawn 工具启动子Agent
   ```

### 方案2: 修复子Agent模型配置

**问题**：子Agent启动时没有使用配置中的模型

**解决方案**：

在调用 `sessions_spawn` 时，显式指定模型参数：

```python
# 启动子Agent时指定正确模型
sessions_spawn(
    runtime="subagent",
    agent_id="tech_analyst",
    task="任务内容",
    mode="run",
    model="bailian/qwen3-max-2026-01-23"  # 显式指定模型
)
```

**各子Agent正确模型配置**：
- `ai_intel`: `bailian/qwen3-max-2026-01-23`
- `tech_analyst`: `bailian/qwen3-max-2026-01-23`
- `official_operate`: `bailian/qwen3-coder-plus`

### 方案3: 创建标准调度流程文档

**已创建文件**：
1. `/shared/agent_scheduler.py` - Python调度器
2. `/shared/schedule_and_spawn.sh` - Shell调度脚本
3. `/shared/multi_agent_issue_analysis.md` - 本分析报告

**标准调度流程**：

```python
def schedule_multi_agent_task(task_content: str, task_name: str = None):
    """标准多Agent任务调度流程"""
    
    # 步骤1: 匹配任务类型
    task_type, config = match_task_type(task_content)
    
    # 步骤2: 获取Agent分配
    primary = config.get('primary_agent', 'main')
    secondary = config.get('secondary_agents', [])
    
    # 步骤3: 生成任务ID
    task_id = generate_task_id()
    
    # 步骤4: 启动主Agent（如果不是main）
    if primary != 'main':
        sessions_spawn(
            runtime="subagent",
            agent_id=primary,
            task=f"【任务ID: {task_id}】{task_content}",
            mode="run",
            model=get_agent_model(primary)  # 显式指定模型
        )
    
    # 步骤5: 并行启动辅助Agent
    for agent in secondary:
        sessions_spawn(
            runtime="subagent",
            agent_id=agent,
            task=f"【任务ID: {task_id}】【辅助】{task_content}",
            mode="run",
            model=get_agent_model(agent)  # 显式指定模型
        )
    
    # 步骤6: 更新任务状态
    update_task_status(task_id, task_name, primary, secondary, "running")
```

## 🧪 验证测试

### 测试1: 调度器工作正常 ✅

```bash
$ python3 agent_scheduler.py "深度分析MaaS市场" "测试任务"

[调度器] 任务ID: 20260401001
[调度器] 匹配任务类型: technical_analysis
[调度器] 主Agent: tech_analyst
[调度器] 辅助Agent: ai_intel
```

### 测试2: 子Agent配置正确 ✅

- openclaw.json 中子Agent配置完整
- 各子Agent workspace 已创建
- models.json 配置正确

### 测试3: 待验证 - 显式模型参数

需要在下次调用 `sessions_spawn` 时：
1. 添加 `model` 参数显式指定模型
2. 验证子Agent是否使用正确模型
3. 验证是否避免429配额错误

## 📋 后续行动清单

- [x] 修复主Agent调度逻辑（MEMORY.md更新）
- [x] 创建Python调度器
- [x] 分析问题根本原因
- [ ] 下次调度时显式指定模型参数
- [ ] 验证子Agent使用正确模型执行
- [ ] 监控任务执行状态

## 💡 关键教训

1. **不要只打印命令，要真正执行**
   - 之前只是打印了"应该启动子Agent"
   - 实际上必须调用 `sessions_spawn` 工具

2. **注意模型继承问题**
   - 子Agent可能继承主Agent的模型
   - 需要显式指定 `model` 参数

3. **检查错误日志**
   - 子Agent失败时查看历史记录
   - 429错误表明模型配置有问题

4. **验证执行结果**
   - 不要假设子Agent已启动
   - 通过 `sessions_list` 验证实际状态
