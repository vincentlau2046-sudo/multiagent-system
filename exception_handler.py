#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理模块 - 实现异常策略矩阵
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ExceptionType(Enum):
    """异常类型枚举"""
    CONFIGURATION = "configuration"
    NETWORK = "network" 
    LOGIC = "logic"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    RESOURCE = "resource"

@dataclass
class ExceptionInfo:
    """异常信息结构"""
    error_code: str
    error_type: ExceptionType
    message: str
    details: Dict[str, Any]
    solution: str
    impact: str
    next_steps: list

class ExceptionHandler:
    """异常处理器 - 实现策略矩阵"""
    
    def __init__(self):
        self.retry_counts: Dict[str, int] = {}  # task_id -> retry_count
        self.max_retries = {
            ExceptionType.NETWORK: 3,
            ExceptionType.TIMEOUT: 2, 
            ExceptionType.RESOURCE: 1,
            ExceptionType.CONFIGURATION: 0,
            ExceptionType.LOGIC: 0,
            ExceptionType.PERMISSION: 0
        }
        
    def handle_exception(self, task_id: str, exception: Exception, 
                        exception_type: ExceptionType) -> Dict[str, Any]:
        """
        处理异常的统一入口
        返回处理结果和下一步行动
        """
        current_retry = self.retry_counts.get(task_id, 0)
        max_retry = self.max_retries.get(exception_type, 0)
        
        if current_retry < max_retry:
            # 执行重试
            self.retry_counts[task_id] = current_retry + 1
            wait_time = self._calculate_wait_time(exception_type, current_retry)
            
            logger.info(f"Retrying task {task_id} after {wait_time}s (attempt {current_retry + 1}/{max_retry})")
            
            return {
                "action": "retry",
                "wait_time": wait_time,
                "retry_count": current_retry + 1,
                "max_retries": max_retry
            }
        else:
            # 重试次数用完，执行降级或人工介入
            return self._execute_fallback_strategy(task_id, exception, exception_type)
            
    def _calculate_wait_time(self, exception_type: ExceptionType, retry_count: int) -> float:
        """计算等待时间（指数退避）"""
        if exception_type == ExceptionType.NETWORK:
            # 网络异常：指数退避 + 随机抖动
            base_delay = 2 ** retry_count
            import random
            jitter = random.uniform(0, 1)
            return base_delay + jitter
        elif exception_type == ExceptionType.TIMEOUT:
            return 5.0  # 固定5秒重试
        else:
            return 1.0  # 其他情况立即重试
            
    def _execute_fallback_strategy(self, task_id: str, exception: Exception, 
                                 exception_type: ExceptionType) -> Dict[str, Any]:
        """执行降级策略"""
        if exception_type == ExceptionType.NETWORK:
            # 网络异常：尝试使用缓存数据
            cached_data = self._get_cached_data(task_id)
            if cached_data:
                logger.info(f"Using cached data for task {task_id}")
                return {
                    "action": "use_cache",
                    "data": cached_data
                }
            else:
                # 无缓存，触发人工介入
                return self._trigger_human_intervention(task_id, exception, exception_type)
                
        elif exception_type in [ExceptionType.CONFIGURATION, ExceptionType.PERMISSION, ExceptionType.LOGIC]:
            # 配置、权限、逻辑异常：直接人工介入
            return self._trigger_human_intervention(task_id, exception, exception_type)
            
        elif exception_type == ExceptionType.RESOURCE:
            # 资源异常：尝试降级到简化模式
            return {
                "action": "degrade",
                "mode": "simplified"
            }
            
        else:
            # 默认人工介入
            return self._trigger_human_intervention(task_id, exception, exception_type)
            
    def _get_cached_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存数据"""
        # 这里应该实现实际的缓存逻辑
        # 例如从文件系统、数据库或内存缓存中读取
        try:
            cache_file = f"/home/Vincent/.openclaw/workspace/cache/{task_id}.json"
            import os
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache for task {task_id}: {e}")
        return None
        
    def _trigger_human_intervention(self, task_id: str, exception: Exception, 
                                   exception_type: ExceptionType) -> Dict[str, Any]:
        """触发人工介入"""
        exception_info = self._create_exception_info(task_id, exception, exception_type)
        
        logger.error(f"Human intervention required for task {task_id}: {exception_info}")
        
        # 这里应该实现实际的人工介入通知逻辑
        # 例如发送飞书消息、邮件通知等
        self._send_human_intervention_notification(exception_info)
        
        return {
            "action": "human_intervention",
            "exception_info": exception_info
        }
        
    def _create_exception_info(self, task_id: str, exception: Exception, 
                              exception_type: ExceptionType) -> ExceptionInfo:
        """创建标准化的异常信息"""
        # 这里应该根据具体的异常类型和上下文生成详细信息
        # 目前提供一个通用模板
        return ExceptionInfo(
            error_code=f"{exception_type.value.upper()}_001",
            error_type=exception_type,
            message=str(exception),
            details={"task_id": task_id, "timestamp": time.time()},
            solution="请联系技术支持或检查相关配置",
            impact="任务执行失败，需要人工干预",
            next_steps=["检查配置", "联系技术支持", "重试任务"]
        )
        
    def _send_human_intervention_notification(self, exception_info: ExceptionInfo):
        """发送人工介入通知"""
        # 这里应该集成实际的通知渠道（飞书、邮件等）
        notification_message = f"""
【人工介入请求】
错误代码: {exception_info.error_code}
错误类型: {exception_info.error_type.value}
错误信息: {exception_info.message}
影响说明: {exception_info.impact}
解决方案: {exception_info.solution}
后续步骤: {', '.join(exception_info.next_steps)}
        """
        logger.info(f"Sending human intervention notification:\n{notification_message}")
        
        # 实际实现应该调用飞书API或其他通知服务
        # from feishu_client import send_message
        # send_message(notification_message)

# 全局异常处理器实例
exception_handler = ExceptionHandler()