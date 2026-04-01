#!/usr/bin/env python3
"""
Agent调度器 - 主Agent内建调度模块
直接集成到主Agent工作流中，无需外部脚本
"""

import yaml
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class AgentScheduler:
    """Agent任务调度器"""
    
    def __init__(self, workspace_root: str = "/home/Vincent/.openclaw/workspace"):
        self.workspace_root = workspace_root
        self.shared_dir = os.path.join(workspace_root, "shared")
        self.routing_rules_path = os.path.join(self.shared_dir, "task_routing_rules.yaml")
        self.status_table_path = os.path.join(self.shared_dir, "task_status.md")
        self.capabilities_path = os.path.join(self.shared_dir, "agent_capabilities.yaml")
        
        # 加载配置
        self.routing_rules = self._load_yaml(self.routing_rules_path)
        self.agent_capabilities = self._load_yaml(self.capabilities_path)
        
    def _load_yaml(self, path: str) -> Dict:
        """加载YAML文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[调度器] 加载YAML失败 {path}: {e}")
            return {}
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        today = datetime.now().strftime("%Y%m%d")
        
        # 读取当前最大序号
        max_seq = 0
        if os.path.exists(self.status_table_path):
            with open(self.status_table_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 查找今天的任务
                pattern = rf"{today}(\d{{3}})"
                matches = re.findall(pattern, content)
                if matches:
                    max_seq = max(int(m) for m in matches)
        
        new_seq = max_seq + 1
        return f"{today}{new_seq:03d}"
    
    def match_task_type(self, task_content: str) -> Tuple[str, Dict]:
        """
        匹配任务类型
        返回: (task_type, task_config)
        """
        task_content_lower = task_content.lower()
        best_match = None
        best_score = 0
        
        classifications = self.routing_rules.get('task_classification', [])
        
        for task_config in classifications:
            task_type = task_config.get('type', 'unknown')
            keywords = task_config.get('keywords', [])
            
            # 计算匹配分数
            score = 0
            for keyword in keywords:
                if keyword.lower() in task_content_lower:
                    score += 1
                    # 精确匹配加分
                    if keyword.lower() in task_content_lower.split():
                        score += 1
            
            if score > best_score:
                best_score = score
                best_match = task_config
        
        if best_match:
            return best_match.get('type', 'default'), best_match
        return 'default', {}
    
    def get_agent_assignment(self, task_type: str, task_config: Dict) -> Dict:
        """
        获取Agent分配
        返回: {primary_agent, secondary_agents, task_type}
        """
        if task_type == 'default' or not task_config:
            return {
                'primary_agent': 'main',
                'secondary_agents': [],
                'task_type': 'default'
            }
        
        return {
            'primary_agent': task_config.get('primary_agent', 'main'),
            'secondary_agents': task_config.get('secondary_agents', []),
            'task_type': task_type
        }
    
    def update_task_status(self, task_id: str, task_name: str, 
                          primary_agent: str, secondary_agents: List[str],
                          status: str, notes: str = ""):
        """更新任务状态表"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        secondary_str = ','.join(secondary_agents) if secondary_agents else ""
        
        # 确保状态表存在
        if not os.path.exists(self.status_table_path):
            header = """# 📋 全局任务状态跟踪表（动态调度版）
## 字段说明
| 字段 | 说明 |
|------|------|
| 任务ID | 全局唯一任务标识（格式：YYYYMMDD+3位序号） |
| 任务名称 | 任务的简短描述 |
| 主Agent | 主要负责执行的Agent ID |
| 辅助Agent | 协助执行的Agent ID列表（逗号分隔） |
| 状态 | pending（待执行）/running（执行中）/success（成功）/failed（失败） |
| 置信度 | 内容质量置信度评分（0-100），≥90自动通过 |
| 审核轮次 | 当前审核轮次（自审→交叉审→主审） |
| 创建时间 | YYYY-MM-DD HH:MM:SS |
| 更新时间 | YYYY-MM-DD HH:MM:SS |
| 备注 | 失败原因/进度说明/审核意见等 |

## 执行记录
| 任务ID | 任务名称 | 主Agent | 辅助Agent | 状态 | 置信度 | 审核轮次 | 创建时间 | 更新时间 | 备注 |
|--------|----------|---------|-----------|------|--------|----------|----------|----------|------|
"""
            with open(self.status_table_path, 'w', encoding='utf-8') as f:
                f.write(header)
        
        # 添加新记录
        record = f"| {task_id} | {task_name} | {primary_agent} | {secondary_str} | {status} | - | 1 | {now} | {now} | {notes} |\n"
        
        with open(self.status_table_path, 'a', encoding='utf-8') as f:
            f.write(record)
    
    def schedule_task(self, task_content: str, task_name: Optional[str] = None) -> Dict:
        """
        调度任务 - 主入口
        返回调度结果，包含所有需要启动的Agent信息
        """
        print(f"\n{'='*60}")
        print(f"[Agent调度器] 开始调度任务")
        print(f"{'='*60}")
        
        # 生成任务信息
        task_id = self._generate_task_id()
        if not task_name:
            task_name = task_content[:50] + "..." if len(task_content) > 50 else task_content
        
        print(f"[调度器] 任务ID: {task_id}")
        print(f"[调度器] 任务名称: {task_name}")
        
        # 匹配任务类型
        task_type, task_config = self.match_task_type(task_content)
        print(f"[调度器] 匹配任务类型: {task_type}")
        
        # 获取Agent分配
        assignment = self.get_agent_assignment(task_type, task_config)
        primary_agent = assignment['primary_agent']
        secondary_agents = assignment['secondary_agents']
        
        print(f"[调度器] 主Agent: {primary_agent}")
        print(f"[调度器] 辅助Agent: {', '.join(secondary_agents) if secondary_agents else '无'}")
        
        # 更新状态为running
        self.update_task_status(
            task_id, task_name, 
            primary_agent, secondary_agents,
            "running", 
            f"任务类型: {task_type}"
        )
        
        # 构建调度结果
        result = {
            'task_id': task_id,
            'task_name': task_name,
            'task_type': task_type,
            'primary_agent': primary_agent,
            'secondary_agents': secondary_agents,
            'task_content': task_content,
            'status': 'scheduled'
        }
        
        print(f"[调度器] 调度完成，准备执行...")
        print(f"{'='*60}\n")
        
        return result
    
    def get_spawn_commands(self, schedule_result: Dict) -> List[Dict]:
        """
        生成启动命令列表
        返回: [{agent_id, task, mode, is_primary}]
        """
        commands = []
        task_content = schedule_result['task_content']
        task_id = schedule_result['task_id']
        
        # 主Agent任务
        primary = schedule_result['primary_agent']
        if primary != 'main':
            commands.append({
                'agent_id': primary,
                'task': f"【任务ID: {task_id}】{task_content}",
                'mode': 'run',
                'is_primary': True,
                'workspace': f"/home/Vincent/.openclaw/workspace-{primary.upper().replace('_', '-')}"
            })
        
        # 辅助Agent任务
        for secondary in schedule_result['secondary_agents']:
            commands.append({
                'agent_id': secondary,
                'task': f"【任务ID: {task_id}】【辅助任务】作为{secondary}，请为以下任务提供支持：{task_content}",
                'mode': 'run',
                'is_primary': False,
                'workspace': f"/home/Vincent/.openclaw/workspace-{secondary.upper().replace('_', '-')}"
            })
        
        return commands


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python agent_scheduler.py '任务内容' [任务名称]")
        sys.exit(1)
    
    task_content = sys.argv[1]
    task_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    scheduler = AgentScheduler()
    result = scheduler.schedule_task(task_content, task_name)
    
    # 输出JSON格式结果，供主Agent解析
    print("\n[调度结果JSON]")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 输出生成的启动命令
    commands = scheduler.get_spawn_commands(result)
    print("\n[启动命令列表]")
    for cmd in commands:
        print(f"  Agent: {cmd['agent_id']}")
        print(f"  任务: {cmd['task'][:100]}...")
        print(f"  模式: {cmd['mode']}")
        print(f"  主任务: {'是' if cmd['is_primary'] else '否'}")
        print()


if __name__ == "__main__":
    main()