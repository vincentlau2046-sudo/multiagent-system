#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent动态加载器 - 支持热插拔的关键组件
"""

import os
import sys
import importlib
import logging
from typing import Dict, List, Optional
from pathlib import Path

from .multiagent_core import agent_registry, AgentInterface
from .agent_base import BaseAgent

logger = logging.getLogger(__name__)

class AgentLoader:
    """Agent动态加载器"""
    
    def __init__(self, agents_dir: str = "/home/Vincent/.openclaw/workspace/agents"):
        self.agents_dir = Path(agents_dir)
        self.loaded_agents: Dict[str, AgentInterface] = {}
        
    def discover_agents(self) -> List[str]:
        """发现可用的Agent模块"""
        agent_modules = []
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            return agent_modules
            
        # 查找所有agent目录下的__init__.py文件
        for agent_dir in self.agents_dir.iterdir():
            if agent_dir.is_dir() and (agent_dir / "__init__.py").exists():
                agent_modules.append(agent_dir.name)
                
        logger.info(f"Discovered agents: {agent_modules}")
        return agent_modules
        
    def load_agent(self, agent_name: str) -> Optional[AgentInterface]:
        """动态加载单个Agent"""
        if agent_name in self.loaded_agents:
            logger.info(f"Agent {agent_name} already loaded")
            return self.loaded_agents[agent_name]
            
        agent_module_path = self.agents_dir / agent_name
        if not agent_module_path.exists():
            logger.error(f"Agent module not found: {agent_name}")
            return None
            
        try:
            # 动态导入Agent模块
            sys.path.insert(0, str(self.agents_dir))
            agent_module = importlib.import_module(agent_name)
            sys.path.pop(0)
            
            # 查找Agent类（约定：类名以Agent结尾）
            agent_class = None
            for attr_name in dir(agent_module):
                attr = getattr(agent_module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseAgent) and 
                    attr != BaseAgent):
                    agent_class = attr
                    break
                    
            if not agent_class:
                logger.error(f"No valid Agent class found in {agent_name}")
                return None
                
            # 实例化Agent
            agent_instance = agent_class()
            if not isinstance(agent_instance, AgentInterface):
                logger.error(f"Agent {agent_name} does not implement AgentInterface")
                return None
                
            # 注册到全局注册中心
            agent_registry.register_agent(agent_instance)
            self.loaded_agents[agent_name] = agent_instance
            
            logger.info(f"Successfully loaded agent: {agent_name}")
            return agent_instance
            
        except Exception as e:
            logger.error(f"Failed to load agent {agent_name}: {e}")
            return None
            
    def load_all_agents(self) -> Dict[str, AgentInterface]:
        """加载所有可用Agent"""
        agent_names = self.discover_agents()
        for agent_name in agent_names:
            self.load_agent(agent_name)
        return self.loaded_agents
        
    def unload_agent(self, agent_name: str) -> bool:
        """卸载Agent（热插拔支持）"""
        if agent_name in self.loaded_agents:
            agent_registry.unregister_agent(agent_name)
            del self.loaded_agents[agent_name]
            logger.info(f"Agent {agent_name} unloaded successfully")
            return True
        return False
        
    def reload_agent(self, agent_name: str) -> Optional[AgentInterface]:
        """重新加载Agent（热更新支持）"""
        self.unload_agent(agent_name)
        return self.load_agent(agent_name)

# 全局Agent加载器实例
agent_loader = AgentLoader()

def initialize_agents():
    """初始化所有Agent"""
    logger.info("Initializing all agents...")
    agents = agent_loader.load_all_agents()
    logger.info(f"Initialized {len(agents)} agents: {list(agents.keys())}")
    return agents

if __name__ == "__main__":
    # 测试Agent加载
    initialize_agents()