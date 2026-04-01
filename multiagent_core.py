#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Agent 核心引擎 - 支持热插拔的可维护架构
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running" 
    SUCCESS = "success"
    FAILED = "failed"

class AgentRole(Enum):
    """Agent角色枚举"""
    PRIMARY = "primary"
    SECONDARY = "secondary"

@dataclass
class QualityMetrics:
    """质量评估指标"""
    completeness: float = 0.0    # 完整性 (0-100)
    accuracy: float = 0.0        # 准确性 (0-100)  
    depth: float = 0.0           # 深度 (0-100)
    practicality: float = 0.0     # 实用性 (0-100)
    
    def calculate_confidence(self, task_type: str = "default") -> float:
        """计算置信度分数"""
        # 基础权重
        weights = {
            "default": {"completeness": 0.3, "accuracy": 0.35, "depth": 0.2, "practicality": 0.15},
            "intelligence_collection": {"completeness": 0.3, "accuracy": 0.45, "depth": 0.1, "practicality": 0.15},
            "technical_analysis": {"completeness": 0.3, "accuracy": 0.35, "depth": 0.3, "practicality": 0.05},
            "content_creation": {"completeness": 0.3, "accuracy": 0.35, "depth": 0.2, "practicality": 0.25},
            "complex_research": {"completeness": 0.3, "accuracy": 0.35, "depth": 0.25, "practicality": 0.1}
        }
        
        task_weights = weights.get(task_type, weights["default"])
        confidence = (
            self.completeness * task_weights["completeness"] +
            self.accuracy * task_weights["accuracy"] +
            self.depth * task_weights["depth"] +
            self.practicality * task_weights["practicality"]
        )
        return min(100.0, max(0.0, confidence))

@dataclass
class AgentStatus:
    """Agent状态信息"""
    agent_id: str
    role: AgentRole
    status: TaskStatus
    progress: float = 0.0
    quality_metrics: Optional[QualityMetrics] = None
    confidence: float = 0.0
    last_update: float = 0.0
    message: str = ""
    retry_count: int = 0
    max_retries: int = 3

@dataclass 
class TaskInfo:
    """任务基本信息"""
    task_id: str
    task_name: str
    task_type: str
    primary_agent: str
    secondary_agents: List[str]
    status: TaskStatus = TaskStatus.PENDING
    confidence: float = 0.0
    review_round: int = 0
    created_time: str = ""
    updated_time: str = ""
    notes: str = ""

class AgentInterface(ABC):
    """Agent接口定义 - 支持热插拔的关键"""
    
    @abstractmethod
    def get_agent_id(self) -> str:
        """获取Agent ID"""
        pass
        
    @abstractmethod
    def execute_task(self, task_info: TaskInfo, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        pass
        
    @abstractmethod
    def self_review(self, result: Dict[str, Any]) -> QualityMetrics:
        """自审"""
        pass
        
    @abstractmethod
    def can_handle_task_type(self, task_type: str) -> bool:
        """判断是否能处理指定任务类型"""
        pass

class AgentRegistry:
    """Agent注册中心 - 热插拔核心"""
    
    def __init__(self):
        self._agents: Dict[str, AgentInterface] = {}
        self._task_type_mapping: Dict[str, List[str]] = {}
        
    def register_agent(self, agent: AgentInterface):
        """注册Agent"""
        agent_id = agent.get_agent_id()
        self._agents[agent_id] = agent
        logger.info(f"Agent {agent_id} registered")
        
        # 更新任务类型映射
        self._update_task_type_mapping()
        
    def unregister_agent(self, agent_id: str):
        """注销Agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Agent {agent_id} unregistered")
            self._update_task_type_mapping()
            
    def get_agent(self, agent_id: str) -> Optional[AgentInterface]:
        """获取Agent"""
        return self._agents.get(agent_id)
        
    def get_available_agents(self) -> List[str]:
        """获取所有可用Agent"""
        return list(self._agents.keys())
        
    def get_agents_for_task_type(self, task_type: str) -> List[str]:
        """根据任务类型获取合适的Agent列表"""
        return self._task_type_mapping.get(task_type, [])
        
    def _update_task_type_mapping(self):
        """更新任务类型到Agent的映射"""
        self._task_type_mapping = {}
        for agent_id, agent in self._agents.items():
            # 这里可以根据实际需求扩展任务类型判断逻辑
            # 目前简化处理，后续可以从配置文件读取
            pass

class TaskRouter:
    """任务路由器 - 从YAML配置加载路由规则"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.routing_rules = self._load_routing_rules()
        
    def _load_routing_rules(self) -> Dict[str, Any]:
        """加载路由规则"""
        import yaml
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load routing rules: {e}")
            return {"task_classification": []}
            
    def route_task(self, task_description: str) -> Optional[Dict[str, Any]]:
        """根据任务描述路由到合适的Agent组合"""
        for rule in self.routing_rules.get("task_classification", []):
            keywords = rule.get("keywords", [])
            if any(keyword in task_description for keyword in keywords):
                return {
                    "task_type": rule["type"],
                    "primary_agent": rule["primary_agent"],
                    "secondary_agents": rule.get("secondary_agents", [])
                }
        return None

class StateManager:
    """状态管理器 - 实时状态同步"""
    
    def __init__(self):
        self._task_states: Dict[str, TaskInfo] = {}
        self._agent_states: Dict[str, Dict[str, AgentStatus]] = {}  # task_id -> {agent_id -> status}
        self._event_listeners: List[Callable] = []
        
    def update_agent_status(self, task_id: str, agent_status: AgentStatus):
        """更新Agent状态并触发事件"""
        if task_id not in self._agent_states:
            self._agent_states[task_id] = {}
        self._agent_states[task_id][agent_status.agent_id] = agent_status
        
        # 触发状态变更事件
        self._notify_listeners({
            "event_type": "agent.status.update",
            "task_id": task_id,
            "agent_status": asdict(agent_status),
            "timestamp": time.time()
        })
        
    def get_task_state(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务状态"""
        return self._task_states.get(task_id)
        
    def update_task_state(self, task_info: TaskInfo):
        """更新任务状态"""
        self._task_states[task_info.task_id] = task_info
        
    def add_event_listener(self, listener: Callable):
        """添加事件监听器"""
        self._event_listeners.append(listener)
        
    def _notify_listeners(self, event: Dict[str, Any]):
        """通知所有监听器"""
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Event listener error: {e}")

class ReactMechanism:
    """React机制处理器"""
    
    def __init__(self, state_manager: StateManager, agent_registry: AgentRegistry):
        self.state_manager = state_manager
        self.agent_registry = agent_registry
        
    def handle_low_confidence(self, task_id: str, agent_id: str, confidence: float) -> bool:
        """处理低置信度情况"""
        if confidence >= 90:
            return True  # 自动通过
            
        elif confidence >= 70:
            # 需要主审，这里可以触发主审流程
            logger.info(f"Task {task_id} requires main review (confidence: {confidence})")
            return False
            
        else:
            # 置信度 < 70，触发React机制
            return self._trigger_react_mechanism(task_id, agent_id)
            
    def _trigger_react_mechanism(self, task_id: str, agent_id: str) -> bool:
        """触发React机制"""
        task_state = self.state_manager.get_task_state(task_id)
        if not task_state:
            return False
            
        agent_status = self.state_manager._agent_states.get(task_id, {}).get(agent_id)
        if not agent_status:
            return False
            
        # 检查重试次数
        if agent_status.retry_count < agent_status.max_retries:
            logger.info(f"Retrying agent {agent_id} for task {task_id} (attempt {agent_status.retry_count + 1})")
            # 这里应该触发重试逻辑
            return True
        else:
            logger.warning(f"Max retries exceeded for agent {agent_id} in task {task_id}")
            # 触发人工介入或其他降级策略
            return False

# 全局实例
agent_registry = AgentRegistry()
state_manager = StateManager()
react_mechanism = ReactMechanism(state_manager, agent_registry)

def initialize_core_engine():
    """初始化核心引擎"""
    logger.info("Initializing Multi-Agent Core Engine...")
    
    # 加载路由配置
    router = TaskRouter("/home/Vincent/.openclaw/workspace/shared/task_routing_rules.yaml")
    
    # 注册事件监听器（用于实时状态更新）
    state_manager.add_event_listener(lambda event: _handle_state_event(event))
    
    logger.info("Core engine initialized successfully!")
    return router

def _handle_state_event(event: Dict[str, Any]):
    """处理状态事件"""
    # 这里可以实现飞书通知、WebUI更新等逻辑
    event_type = event.get("event_type")
    if event_type == "agent.status.update":
        task_id = event["task_id"]
        agent_status = event["agent_status"]
        confidence = agent_status["confidence"]
        
        # 自动处理低置信度情况
        if confidence > 0 and confidence < 90:
            react_mechanism.handle_low_confidence(task_id, agent_status["agent_id"], confidence)

if __name__ == "__main__":
    # 初始化引擎
    router = initialize_core_engine()
    print("Multi-Agent Core Engine is ready!")