#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent基类 - 热插拔架构的基础
所有具体Agent都应该继承此类
"""

import json
import logging
from typing import Dict, Any, List
from abc import abstractmethod
from .multiagent_core import AgentInterface, QualityMetrics, TaskInfo

logger = logging.getLogger(__name__)

class BaseAgent(AgentInterface):
    """
    Agent基类，提供通用功能和接口实现
    子类只需要实现具体的业务逻辑方法
    """
    
    def __init__(self, agent_id: str, supported_task_types: List[str] = None):
        self.agent_id = agent_id
        self.supported_task_types = supported_task_types or []
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
    def get_agent_id(self) -> str:
        """获取Agent ID"""
        return self.agent_id
        
    def can_handle_task_type(self, task_type: str) -> bool:
        """判断是否能处理指定任务类型"""
        if not self.supported_task_types:
            # 如果没有指定支持的任务类型，默认支持所有
            return True
        return task_type in self.supported_task_types
        
    def execute_task(self, task_info: TaskInfo, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务的统一入口
        子类应该重写 _execute_business_logic 方法
        """
        try:
            self.logger.info(f"Starting task execution: {task_info.task_id}")
            
            # 执行具体的业务逻辑
            result = self._execute_business_logic(task_info, context)
            
            # 添加元数据
            result.update({
                "agent_id": self.agent_id,
                "task_id": task_info.task_id,
                "execution_time": time.time(),
                "status": "success"
            })
            
            self.logger.info(f"Task completed successfully: {task_info.task_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {
                "agent_id": self.agent_id,
                "task_id": task_info.task_id,
                "status": "failed",
                "error": str(e),
                "execution_time": time.time()
            }
    
    def self_review(self, result: Dict[str, Any]) -> QualityMetrics:
        """
        自审的统一入口
        子类应该重写 _perform_self_review 方法
        """
        try:
            if result.get("status") == "failed":
                # 执行失败的情况，返回最低质量分数
                return QualityMetrics(0.0, 0.0, 0.0, 0.0)
                
            quality_metrics = self._perform_self_review(result)
            self.logger.info(f"Self-review completed for task {result.get('task_id')}: {quality_metrics}")
            return quality_metrics
            
        except Exception as e:
            self.logger.error(f"Self-review failed: {e}")
            # 自审失败时返回保守分数
            return QualityMetrics(50.0, 50.0, 50.0, 50.0)
    
    @abstractmethod
    def _execute_business_logic(self, task_info: TaskInfo, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        子类必须实现的具体业务逻辑
        返回任务执行结果
        """
        pass
        
    @abstractmethod  
    def _perform_self_review(self, result: Dict[str, Any]) -> QualityMetrics:
        """
        子类必须实现的自审逻辑
        返回质量评估指标
        """
        pass

# 示例：如何创建具体的Agent
"""
class TechAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="tech_analyst", 
            supported_task_types=["technical_analysis", "complex_research"]
        )
    
    def _execute_business_logic(self, task_info: TaskInfo, context: Dict[str, Any]) -> Dict[str, Any]:
        # 具体的技术分析逻辑
        pass
        
    def _perform_self_review(self, result: Dict[str, Any]) -> QualityMetrics:
        # 具体的自审逻辑
        pass

# 注册Agent到全局注册中心
from .multiagent_core import agent_registry
agent_registry.register_agent(TechAnalystAgent())
"""