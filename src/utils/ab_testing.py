"""
A/B测试框架
支持话术、人格模板、功能开关的多变量测试
"""

import logging
import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import random

logger = logging.getLogger(__name__)


class ExperimentType(Enum):
    """实验类型"""
    PERSONALITY = "personality"          # 人格模板测试
    SCRIPT = "script"                    # 话术测试
    FEATURE = "feature"                  # 功能开关测试
    MODEL = "model"                      # 模型参数测试


class ExperimentStatus(Enum):
    """实验状态"""
    DRAFT = "draft"                      # 草稿
    RUNNING = "running"                  # 运行中
    PAUSED = "paused"                    # 已暂停
    COMPLETED = "completed"              # 已完成


class Variant:
    """实验变体"""
    
    def __init__(
        self,
        variant_id: str,
        name: str,
        config: Dict[str, Any],
        weight: float = 0.5
    ):
        """
        参数:
            variant_id: 变体ID
            name: 变体名称
            config: 配置参数
            weight: 流量权重 (0-1)
        """
        self.variant_id = variant_id
        self.name = name
        self.config = config
        self.weight = weight
        
        # 统计数据
        self.metrics = {
            "exposure_count": 0,         # 曝光次数
            "response_count": 0,         # 回复次数
            "positive_count": 0,         # 正向反馈次数
            "negative_count": 0,         # 负向反馈次数
            "takeover_count": 0,         # 人工接管次数
            "avg_response_time": 0.0,    # 平均响应时间
            "total_response_time": 0.0   # 总响应时间
        }


class Experiment:
    """实验"""
    
    def __init__(
        self,
        experiment_id: str,
        name: str,
        description: str,
        experiment_type: ExperimentType,
        variants: List[Variant],
        status: ExperimentStatus = ExperimentStatus.DRAFT,
        start_time: datetime = None,
        end_time: datetime = None
    ):
        """
        参数:
            experiment_id: 实验ID
            name: 实验名称
            description: 实验描述
            experiment_type: 实验类型
            variants: 变体列表
            status: 实验状态
            start_time: 开始时间
            end_time: 结束时间
        """
        self.experiment_id = experiment_id
        self.name = name
        self.description = description
        self.experiment_type = experiment_type
        self.variants = variants
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        
        # 用户分组缓存
        self.user_variant_map: Dict[str, str] = {}
    
    def assign_variant(self, user_id: str) -> Variant:
        """
        为用户分配变体
        
        使用一致性哈希确保同一用户始终分配到同一变体
        
        参数:
            user_id: 用户ID
        
        返回:
            变体实例
        """
        # 检查缓存
        if user_id in self.user_variant_map:
            variant_id = self.user_variant_map[user_id]
            for variant in self.variants:
                if variant.variant_id == variant_id:
                    return variant
        
        # 一致性哈希分配
        hash_value = int(
            hashlib.md5(
                f"{self.experiment_id}:{user_id}".encode()
            ).hexdigest(),
            16
        )
        
        # 根据权重分配
        cumulative = 0.0
        for variant in self.variants:
            cumulative += variant.weight
            if hash_value % 10000 < cumulative * 10000:
                # 缓存分配结果
                self.user_variant_map[user_id] = variant.variant_id
                return variant
        
        # 默认返回第一个变体
        return self.variants[0]
    
    def record_exposure(self, variant_id: str):
        """记录曝光"""
        for variant in self.variants:
            if variant.variant_id == variant_id:
                variant.metrics["exposure_count"] += 1
                break
    
    def record_response(
        self,
        variant_id: str,
        response_time: float,
        is_positive: bool = None
    ):
        """
        记录回复
        
        参数:
            variant_id: 变体ID
            response_time: 响应时间(秒)
            is_positive: 是否正向反馈 (None表示未知)
        """
        for variant in self.variants:
            if variant.variant_id == variant_id:
                variant.metrics["response_count"] += 1
                variant.metrics["total_response_time"] += response_time
                variant.metrics["avg_response_time"] = (
                    variant.metrics["total_response_time"] / 
                    variant.metrics["response_count"]
                )
                
                if is_positive is True:
                    variant.metrics["positive_count"] += 1
                elif is_positive is False:
                    variant.metrics["negative_count"] += 1
                
                break
    
    def record_takeover(self, variant_id: str):
        """记录人工接管"""
        for variant in self.variants:
            if variant.variant_id == variant_id:
                variant.metrics["takeover_count"] += 1
                break
    
    def get_results(self) -> Dict[str, Any]:
        """
        获取实验结果
        
        返回:
            实验统计数据
        """
        results = {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "type": self.experiment_type.value,
            "status": self.status.value,
            "variants": []
        }
        
        for variant in self.variants:
            metrics = variant.metrics.copy()
            
            # 计算转化率
            if metrics["exposure_count"] > 0:
                metrics["response_rate"] = (
                    metrics["response_count"] / metrics["exposure_count"]
                )
            
            # 计算好评率
            if metrics["response_count"] > 0:
                metrics["positive_rate"] = (
                    metrics["positive_count"] / metrics["response_count"]
                )
                metrics["takeover_rate"] = (
                    metrics["takeover_count"] / metrics["response_count"]
                )
            
            results["variants"].append({
                "variant_id": variant.variant_id,
                "name": variant.name,
                "weight": variant.weight,
                "metrics": metrics
            })
        
        return results


class ABTestingFramework:
    """
    A/B测试框架
    
    管理多个实验和变体分配
    """
    
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
    
    def create_experiment(
        self,
        name: str,
        description: str,
        experiment_type: ExperimentType,
        variants: List[Dict[str, Any]],
        experiment_id: str = None
    ) -> Experiment:
        """
        创建实验
        
        参数:
            name: 实验名称
            description: 实验描述
            experiment_type: 实验类型
            variants: 变体配置列表
            experiment_id: 实验ID (可选)
        
        返回:
            实验实例
        """
        # 生成实验ID
        if not experiment_id:
            experiment_id = f"exp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 创建变体
        variant_objects = []
        for v in variants:
            variant = Variant(
                variant_id=v["variant_id"],
                name=v["name"],
                config=v.get("config", {}),
                weight=v.get("weight", 1.0 / len(variants))
            )
            variant_objects.append(variant)
        
        # 创建实验
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            experiment_type=experiment_type,
            variants=variant_objects
        )
        
        self.experiments[experiment_id] = experiment
        
        logger.info(f"✅ 创建实验: {name} ({experiment_id})")
        
        return experiment
    
    def start_experiment(self, experiment_id: str):
        """启动实验"""
        if experiment_id not in self.experiments:
            raise ValueError(f"实验不存在: {experiment_id}")
        
        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.RUNNING
        experiment.start_time = datetime.now()
        
        logger.info(f"✅ 启动实验: {experiment.name}")
    
    def pause_experiment(self, experiment_id: str):
        """暂停实验"""
        if experiment_id not in self.experiments:
            raise ValueError(f"实验不存在: {experiment_id}")
        
        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.PAUSED
        
        logger.info(f"⏸️ 暂停实验: {experiment.name}")
    
    def complete_experiment(self, experiment_id: str):
        """结束实验"""
        if experiment_id not in self.experiments:
            raise ValueError(f"实验不存在: {experiment_id}")
        
        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_time = datetime.now()
        
        logger.info(f"✅ 结束实验: {experiment.name}")
    
    def get_variant(
        self,
        experiment_id: str,
        user_id: str
    ) -> Optional[Variant]:
        """
        获取用户的实验变体
        
        参数:
            experiment_id: 实验ID
            user_id: 用户ID
        
        返回:
            变体实例
        """
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.RUNNING:
            return None
        
        return experiment.assign_variant(user_id)
    
    def record_exposure(self, experiment_id: str, variant_id: str):
        """记录曝光"""
        if experiment_id in self.experiments:
            self.experiments[experiment_id].record_exposure(variant_id)
    
    def record_response(
        self,
        experiment_id: str,
        variant_id: str,
        response_time: float,
        is_positive: bool = None
    ):
        """记录回复"""
        if experiment_id in self.experiments:
            self.experiments[experiment_id].record_response(
                variant_id,
                response_time,
                is_positive
            )
    
    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """获取实验结果"""
        if experiment_id not in self.experiments:
            return {}
        
        return self.experiments[experiment_id].get_results()
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """列出所有实验"""
        return [
            {
                "experiment_id": exp.experiment_id,
                "name": exp.name,
                "type": exp.experiment_type.value,
                "status": exp.status.value,
                "variant_count": len(exp.variants)
            }
            for exp in self.experiments.values()
        ]


# 全局实例
ab_testing = ABTestingFramework()


def init_sample_experiments():
    """
    初始化示例实验
    
    包含人格模板、话术风格、功能开关的测试
    """
    # 实验1: 人格模板测试
    ab_testing.create_experiment(
        name="人格模板效果对比",
        description="对比专业型和热情型人格模板的回复效果",
        experiment_type=ExperimentType.PERSONALITY,
        variants=[
            {
                "variant_id": "professional",
                "name": "专业型",
                "config": {
                    "personality": "professional",
                    "tone": "formal",
                    "emoji_frequency": "low"
                },
                "weight": 0.5
            },
            {
                "variant_id": "enthusiastic",
                "name": "热情型",
                "config": {
                    "personality": "enthusiastic",
                    "tone": "casual",
                    "emoji_frequency": "high"
                },
                "weight": 0.5
            }
        ]
    )
    
    # 实验2: 话术风格测试
    ab_testing.create_experiment(
        name="话术风格测试",
        description="对比简洁型和详细型话术的用户体验",
        experiment_type=ExperimentType.SCRIPT,
        variants=[
            {
                "variant_id": "concise",
                "name": "简洁型",
                "config": {
                    "max_length": 100,
                    "include_details": False,
                    "use_bullets": True
                },
                "weight": 0.5
            },
            {
                "variant_id": "detailed",
                "name": "详细型",
                "config": {
                    "max_length": 300,
                    "include_details": True,
                    "use_bullets": False
                },
                "weight": 0.5
            }
        ]
    )
    
    # 实验3: 功能开关测试
    ab_testing.create_experiment(
        name="视觉识别功能测试",
        description="测试启用/禁用视觉识别功能对用户体验的影响",
        experiment_type=ExperimentType.FEATURE,
        variants=[
            {
                "variant_id": "with_visual",
                "name": "启用视觉识别",
                "config": {
                    "enable_visual": True,
                    "visual_features": ["ocr", "product_detection", "scene_analysis"]
                },
                "weight": 0.5
            },
            {
                "variant_id": "without_visual",
                "name": "禁用视觉识别",
                "config": {
                    "enable_visual": False,
                    "visual_features": []
                },
                "weight": 0.5
            }
        ]
    )
    
    logger.info("✅ 示例实验初始化完成")
    
    # 启动所有实验
    for exp_id in ab_testing.experiments.keys():
        ab_testing.start_experiment(exp_id)


# API端点示例
"""
# 创建实验
POST /api/ab/experiments
{
    "name": "人格模板测试",
    "description": "对比不同人格模板的效果",
    "type": "personality",
    "variants": [...]
}

# 获取变体
GET /api/ab/experiments/{experiment_id}/variant?user_id={user_id}

# 记录指标
POST /api/ab/experiments/{experiment_id}/metrics
{
    "variant_id": "variant_a",
    "metric_type": "response",
    "value": {
        "response_time": 1.5,
        "is_positive": true
    }
}

# 获取结果
GET /api/ab/experiments/{experiment_id}/results
"""
