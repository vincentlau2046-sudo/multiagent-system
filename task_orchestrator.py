#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主Agent任务调度器 - 动态调度核心逻辑
"""

import yaml
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class TaskOrchestrator:
    def __init__(self):
        self.routing_rules_path = "/home/Vincent/.openclaw/workspace/shared/task_routing_rules.yaml"
        self.capabilities_path = "/home/Vincent/.openclaw/workspace/shared/agent_capabilities.yaml"
        self.status_table_path = "/home/Vincent/.openclaw/workspace/shared/task_status.md"
        
    def parse_task(self, task_content: str) -> Dict:
        """解析任务内容，提取关键词和任务类型"""
        # 加载路由规则
        with open(self.routing_rules_path, 'r', encoding='utf-8') as f:
            routing_rules = yaml.safe_load(f)
            
        # 提取关键词并匹配任务类型
        matched_task_type = None
        for rule in routing_rules['task_classification']:
            for keyword in rule['keywords']:
                if keyword in task_content:
                    matched_task_type = rule
                    break
            if matched_task_type:
                break
                
        if not matched_task_type:
            # 默认使用主Agent处理
            matched_task_type = {
                'type': 'default',
                'primary_agent': 'main',
                'secondary_agents': []
            }
            
        return matched_task_type
        
    def select_agents(self, task_type: Dict) -> Tuple[str, List[str]]:
        """根据任务类型选择主Agent和辅助Agent"""
        primary_agent = task_type['primary_agent']
        secondary_agents = task_type.get('secondary_agents', [])
        return primary_agent, secondary_agents
        
    def generate_task_id(self) -> str:
        """生成全局唯一任务ID"""
        now = datetime.now().strftime("%Y%m%d")
        # 简单实现：读取状态表最后一行获取序号
        try:
            with open(self.status_table_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_task_line = lines[-1] if len(lines) > 6 else ""
                if last_task_line and last_task_line.startswith('|'):
                    last_id = last_task_line.split('|')[1].strip()
                    if last_id.startswith(now):
                        seq = int(last_id[-3:]) + 1
                    else:
                        seq = 1
                else:
                    seq = 1
        except:
            seq = 1
            
        return f"{now}{seq:03d}"
        
    def update_task_status(self, task_id: str, task_name: str, 
                         primary_agent: str, secondary_agents: List[str],
                         status: str = "pending", confidence: int = 0,
                         review_round: int = 1, notes: str = ""):
        """更新任务状态表"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 读取现有状态表
        with open(self.status_table_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 找到执行记录部分
        lines = content.split('\n')
        record_start = -1
        for i, line in enumerate(lines):
            if line.startswith('| 任务ID | 任务名称 |'):
                record_start = i + 2
                break
                
        if record_start == -1:
            record_start = len(lines)
            
        # 添加新记录
        secondary_str = ','.join(secondary_agents) if secondary_agents else ""
        new_record = f"| {task_id} | {task_name} | {primary_agent} | {secondary_str} | {status} | {confidence} | {review_round} | {now} | {now} | {notes} |"
        
        lines.insert(record_start, new_record)
        
        # 写回文件
        with open(self.status_table_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            
    def execute_agent_task(self, agent_id: str, task_content: str, is_primary: bool = True) -> str:
        """执行单个Agent任务"""
        if agent_id == "main":
            # 主Agent直接返回任务内容
            return task_content
            
        # 构建OpenClaw命令
        cmd = [
            "openclaw", "sessions", "spawn",
            "--runtime", "subagent",
            "--agent-id", agent_id,
            "--task", task_content,
            "--mode", "run"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if result.returncode == 0:
                return f"Agent {agent_id} completed successfully"
            else:
                return f"Agent {agent_id} failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            return f"Agent {agent_id} timeout"
        except Exception as e:
            return f"Agent {agent_id} error: {str(e)}"
            
    def execute_multi_agent_task(self, task_content: str, task_name: str = "") -> Dict:
        """执行多Agent任务调度"""
        # 1. 解析任务
        task_type = self.parse_task(task_content)
        
        # 2. 选择Agent
        primary_agent, secondary_agents = self.select_agents(task_type)
        
        # 3. 生成任务ID
        task_id = self.generate_task_id()
        if not task_name:
            task_name = task_content[:50] + "..." if len(task_content) > 50 else task_content
            
        # 4. 更新任务状态
        self.update_task_status(
            task_id=task_id,
            task_name=task_name,
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            status="running",
            notes="多Agent协作启动"
        )
        
        # 5. 执行主Agent任务
        primary_result = self.execute_agent_task(primary_agent, task_content, is_primary=True)
        
        # 6. 并行执行辅助Agent任务
        secondary_results = {}
        for agent in secondary_agents:
            # 为辅助Agent提供上下文
            aux_task = f"作为{agent}，请为以下任务提供支持：{task_content}"
            secondary_results[agent] = self.execute_agent_task(agent, aux_task, is_primary=False)
            
        # 7. 更新最终状态
        final_status = "success" if "failed" not in primary_result and all("failed" not in r for r in secondary_results.values()) else "failed"
        self.update_task_status(
            task_id=task_id,
            task_name=task_name,
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            status=final_status,
            confidence=95 if final_status == "success" else 0,
            review_round=3,
            notes="多Agent协作完成"
        )
        
        return {
            "task_id": task_id,
            "task_name": task_name,
            "primary_agent": primary_agent,
            "secondary_agents": secondary_agents,
            "task_type": task_type['type'],
            "primary_result": primary_result,
            "secondary_results": secondary_results,
            "status": final_status
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 task_orchestrator.py <task_content> [task_name]")
        sys.exit(1)
        
    task_content = sys.argv[1]
    task_name = sys.argv[2] if len(sys.argv) > 2 else ""
    
    orchestrator = TaskOrchestrator()
    result = orchestrator.execute_multi_agent_task(task_content, task_name)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()