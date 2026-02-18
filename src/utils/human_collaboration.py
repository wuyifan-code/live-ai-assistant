"""
人机协作系统
人工接管触发器、话术审核机制
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import json

logger = logging.getLogger(__name__)


class TakeoverReason(Enum):
    """接管原因"""
    SEVERE_COMPLAINT = "severe_complaint"      # 严重投诉
    LOW_CONFIDENCE = "low_confidence"           # AI置信度低
    ESCALATION_REQUEST = "escalation_request"   # 用户要求转人工
    COMPLEX_ISSUE = "complex_issue"             # 复杂问题
    BRAND_RISK = "brand_risk"                   # 品牌风险
    TECHNICAL_ERROR = "technical_error"         # 技术错误


class AuditStatus(Enum):
    """审核状态"""
    PENDING = "pending"          # 待审核
    APPROVED = "approved"        # 已通过
    REJECTED = "rejected"        # 已拒绝
    MODIFIED = "modified"        # 已修改


class UrgencyLevel(Enum):
    """紧急程度"""
    LOW = 1       # 低：可以等待
    MEDIUM = 2    # 中：尽快处理
    HIGH = 3      # 高：立即处理
    CRITICAL = 4  # 严重：必须人工介入


@dataclass
class TakeoverRequest:
    """人工接管请求"""
    request_id: str
    reason: TakeoverReason
    urgency: UrgencyLevel
    user_id: str
    username: str
    content: str
    ai_suggestion: Optional[str] = None
    confidence: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None


@dataclass
class AuditItem:
    """话术审核项"""
    item_id: str
    user_id: str
    username: str
    original_question: str
    ai_response: str
    confidence: float
    risk_level: str
    created_at: datetime = field(default_factory=datetime.now)
    status: AuditStatus = AuditStatus.PENDING
    reviewer: Optional[str] = None
    modified_response: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None


class HumanTakeoverTrigger:
    """人工接管触发器"""
    
    def __init__(
        self,
        low_confidence_threshold: float = 0.6,
        complaint_keywords: List[str] = None,
        escalation_keywords: List[str] = None
    ):
        """
        参数:
            low_confidence_threshold: 低置信度阈值
            complaint_keywords: 投诉关键词
            escalation_keywords: 转人工关键词
        """
        self.low_confidence_threshold = low_confidence_threshold
        
        # 默认投诉关键词
        self.complaint_keywords = complaint_keywords or [
            "投诉", "举报", "维权", "退款", "假货",
            "诈骗", "欺诈", "赔偿", "律师", "消费者协会",
            "差评", "曝光", "维权", "工商", "315"
        ]
        
        # 默认转人工关键词
        self.escalation_keywords = escalation_keywords or [
            "人工客服", "转人工", "人工服务", "真人",
            "客服人员", "人工接听", "不要机器人"
        ]
        
        # 待处理接管请求队列
        self.pending_requests: deque = deque(maxlen=100)
        self.total_takeovers = 0
        self.resolved_takeovers = 0
    
    def check_takeover_needed(
        self,
        user_id: str,
        username: str,
        content: str,
        ai_response: str = "",
        confidence: float = 1.0,
        context: Dict[str, Any] = None
    ) -> Optional[TakeoverRequest]:
        """
        检查是否需要人工接管
        
        参数:
            user_id: 用户ID
            username: 用户名
            content: 用户消息
            ai_response: AI回复
            confidence: AI置信度
            context: 上下文信息
        
        返回:
            TakeoverRequest if needed, None otherwise
        """
        # 1. 检查投诉关键词
        for keyword in self.complaint_keywords:
            if keyword in content:
                return self._create_takeover_request(
                    user_id=user_id,
                    username=username,
                    content=content,
                    reason=TakeoverReason.SEVERE_COMPLAINT,
                    urgency=UrgencyLevel.HIGH,
                    ai_suggestion=ai_response,
                    confidence=confidence,
                    context=context
                )
        
        # 2. 检查转人工请求
        for keyword in self.escalation_keywords:
            if keyword in content:
                return self._create_takeover_request(
                    user_id=user_id,
                    username=username,
                    content=content,
                    reason=TakeoverReason.ESCALATION_REQUEST,
                    urgency=UrgencyLevel.MEDIUM,
                    ai_suggestion=ai_response,
                    confidence=confidence,
                    context=context
                )
        
        # 3. 检查低置信度
        if confidence < self.low_confidence_threshold:
            return self._create_takeover_request(
                user_id=user_id,
                username=username,
                content=content,
                reason=TakeoverReason.LOW_CONFIDENCE,
                urgency=UrgencyLevel.MEDIUM,
                ai_suggestion=ai_response,
                confidence=confidence,
                context=context
            )
        
        # 4. 检查品牌风险关键词
        risk_keywords = ["虚假宣传", "价格欺诈", "质量问题", "安全隐患"]
        for keyword in risk_keywords:
            if keyword in content:
                return self._create_takeover_request(
                    user_id=user_id,
                    username=username,
                    content=content,
                    reason=TakeoverReason.BRAND_RISK,
                    urgency=UrgencyLevel.HIGH,
                    ai_suggestion=ai_response,
                    confidence=confidence,
                    context=context
                )
        
        return None
    
    def _create_takeover_request(
        self,
        user_id: str,
        username: str,
        content: str,
        reason: TakeoverReason,
        urgency: UrgencyLevel,
        ai_suggestion: str = "",
        confidence: float = 1.0,
        context: Dict[str, Any] = None
    ) -> TakeoverRequest:
        """创建接管请求"""
        import uuid
        
        request = TakeoverRequest(
            request_id=f"TK{int(time.time() * 1000)}",
            reason=reason,
            urgency=urgency,
            user_id=user_id,
            username=username,
            content=content,
            ai_suggestion=ai_suggestion,
            confidence=confidence,
            context=context or {}
        )
        
        self.pending_requests.append(request)
        self.total_takeovers += 1
        
        # 记录日志
        logger.warning(
            f"⚠️ 触发人工接管: 原因={reason.value}, "
            f"紧急度={urgency.name}, 用户={username}"
        )
        
        return request
    
    def get_pending_requests(self, urgency: UrgencyLevel = None) -> List[TakeoverRequest]:
        """
        获取待处理的接管请求
        
        参数:
            urgency: 紧急程度过滤（可选）
        
        返回:
            待处理请求列表
        """
        requests = list(self.pending_requests)
        
        if urgency:
            requests = [r for r in requests if r.urgency == urgency]
        
        # 按紧急程度排序
        requests.sort(key=lambda r: r.urgency.value, reverse=True)
        
        return requests
    
    def resolve_request(self, request_id: str, resolution: str) -> bool:
        """
        解决接管请求
        
        参数:
            request_id: 请求ID
            resolution: 解决方案
        
        返回:
            是否成功
        """
        for request in self.pending_requests:
            if request.request_id == request_id:
                request.status = "resolved"
                request.resolved_at = datetime.now()
                self.resolved_takeovers += 1
                
                logger.info(f"✅ 接管请求已解决: {request_id}")
                return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取接管统计"""
        return {
            "total_takeovers": self.total_takeovers,
            "resolved_takeovers": self.resolved_takeovers,
            "pending_takeovers": len(self.pending_requests),
            "resolution_rate": (
                self.resolved_takeovers / self.total_takeovers 
                if self.total_takeovers > 0 else 0
            )
        }


class ResponseAuditQueue:
    """话术审核队列"""
    
    def __init__(
        self,
        audit_keywords: List[str] = None,
        confidence_threshold: float = 0.75
    ):
        """
        参数:
            audit_keywords: 需要审核的关键词
            confidence_threshold: 审核置信度阈值
        """
        # 默认审核关键词
        self.audit_keywords = audit_keywords or [
            "退款", "赔偿", "投诉", "维权",
            "质量问题", "假货", "欺诈"
        ]
        
        self.confidence_threshold = confidence_threshold
        
        # 审核队列
        self.audit_queue: deque = deque(maxlen=100)
        
        # 统计
        self.total_submitted = 0
        self.total_approved = 0
        self.total_rejected = 0
        self.total_modified = 0
    
    def submit_for_audit(
        self,
        user_id: str,
        username: str,
        original_question: str,
        ai_response: str,
        confidence: float,
        risk_level: str = "medium"
    ) -> Optional[AuditItem]:
        """
        提交话术审核
        
        参数:
            user_id: 用户ID
            username: 用户名
            original_question: 原始问题
            ai_response: AI回复
            confidence: 置信度
            risk_level: 风险等级
        
        返回:
            AuditItem if needs audit, None otherwise
        """
        # 检查是否需要审核
        needs_audit = False
        
        # 1. 低置信度需要审核
        if confidence < self.confidence_threshold:
            needs_audit = True
        
        # 2. 包含审核关键词需要审核
        for keyword in self.audit_keywords:
            if keyword in original_question or keyword in ai_response:
                needs_audit = True
                risk_level = "high"
                break
        
        # 3. 高风险等级需要审核
        if risk_level == "high":
            needs_audit = True
        
        if not needs_audit:
            return None
        
        # 创建审核项
        import uuid
        
        item = AuditItem(
            item_id=f"AU{int(time.time() * 1000)}",
            user_id=user_id,
            username=username,
            original_question=original_question,
            ai_response=ai_response,
            confidence=confidence,
            risk_level=risk_level
        )
        
        self.audit_queue.append(item)
        self.total_submitted += 1
        
        logger.info(
            f"📝 提交话术审核: 用户={username}, "
            f"风险={risk_level}, 置信度={confidence:.2f}"
        )
        
        return item
    
    def get_pending_items(self, risk_level: str = None) -> List[AuditItem]:
        """
        获取待审核项
        
        参数:
            risk_level: 风险等级过滤（可选）
        
        返回:
            待审核项列表
        """
        items = [item for item in self.audit_queue if item.status == AuditStatus.PENDING]
        
        if risk_level:
            items = [item for item in items if item.risk_level == risk_level]
        
        # 按风险等级排序
        risk_order = {"high": 3, "medium": 2, "low": 1}
        items.sort(key=lambda i: risk_order.get(i.risk_level, 0), reverse=True)
        
        return items
    
    def approve_item(self, item_id: str, reviewer: str) -> bool:
        """
        批准审核项
        
        参数:
            item_id: 审核项ID
            reviewer: 审核人
        
        返回:
            是否成功
        """
        for item in self.audit_queue:
            if item.item_id == item_id:
                item.status = AuditStatus.APPROVED
                item.reviewer = reviewer
                item.reviewed_at = datetime.now()
                
                self.total_approved += 1
                
                logger.info(f"✅ 话术审核通过: {item_id}")
                return True
        
        return False
    
    def reject_item(self, item_id: str, reviewer: str, notes: str = "") -> bool:
        """
        拒绝审核项
        
        参数:
            item_id: 审核项ID
            reviewer: 审核人
            notes: 拒绝原因
        
        返回:
            是否成功
        """
        for item in self.audit_queue:
            if item.item_id == item_id:
                item.status = AuditStatus.REJECTED
                item.reviewer = reviewer
                item.reviewed_at = datetime.now()
                item.review_notes = notes
                
                self.total_rejected += 1
                
                logger.info(f"❌ 话术审核拒绝: {item_id}")
                return True
        
        return False
    
    def modify_item(
        self,
        item_id: str,
        reviewer: str,
        modified_response: str,
        notes: str = ""
    ) -> bool:
        """
        修改审核项
        
        参数:
            item_id: 审核项ID
            reviewer: 审核人
            modified_response: 修改后的回复
            notes: 修改说明
        
        返回:
            是否成功
        """
        for item in self.audit_queue:
            if item.item_id == item_id:
                item.status = AuditStatus.MODIFIED
                item.reviewer = reviewer
                item.modified_response = modified_response
                item.reviewed_at = datetime.now()
                item.review_notes = notes
                
                self.total_modified += 1
                
                logger.info(f"✏️ 话术已修改: {item_id}")
                return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取审核统计"""
        return {
            "total_submitted": self.total_submitted,
            "total_approved": self.total_approved,
            "total_rejected": self.total_rejected,
            "total_modified": self.total_modified,
            "pending_items": len([i for i in self.audit_queue if i.status == AuditStatus.PENDING]),
            "approval_rate": (
                self.total_approved / self.total_submitted 
                if self.total_submitted > 0 else 0
            )
        }


# 全局实例
takeover_trigger = HumanTakeoverTrigger()
audit_queue = ResponseAuditQueue()


# 需要导入time
import time


class HumanCollaborationAPI:
    """
    人机协作API
    
    提供REST API接口供运营后台调用
    """
    
    @staticmethod
    def get_takeover_requests(urgency: str = None) -> List[Dict]:
        """获取接管请求列表"""
        from fastapi import HTTPException
        
        urgency_enum = UrgencyLevel[urgency] if urgency else None
        requests = takeover_trigger.get_pending_requests(urgency_enum)
        
        return [
            {
                "request_id": r.request_id,
                "reason": r.reason.value,
                "urgency": r.urgency.name,
                "user_id": r.user_id,
                "username": r.username,
                "content": r.content,
                "ai_suggestion": r.ai_suggestion,
                "confidence": r.confidence,
                "created_at": r.created_at.isoformat(),
                "status": r.status
            }
            for r in requests
        ]
    
    @staticmethod
    def get_audit_items(risk_level: str = None) -> List[Dict]:
        """获取审核项列表"""
        items = audit_queue.get_pending_items(risk_level)
        
        return [
            {
                "item_id": i.item_id,
                "user_id": i.user_id,
                "username": i.username,
                "original_question": i.original_question,
                "ai_response": i.ai_response,
                "confidence": i.confidence,
                "risk_level": i.risk_level,
                "created_at": i.created_at.isoformat(),
                "status": i.status.value
            }
            for i in items
        ]
    
    @staticmethod
    def approve_audit_item(item_id: str, reviewer: str) -> Dict:
        """批准审核项"""
        success = audit_queue.approve_item(item_id, reviewer)
        
        if not success:
            raise ValueError(f"审核项不存在: {item_id}")
        
        return {"success": True, "message": "审核通过"}
    
    @staticmethod
    def reject_audit_item(item_id: str, reviewer: str, notes: str) -> Dict:
        """拒绝审核项"""
        success = audit_queue.reject_item(item_id, reviewer, notes)
        
        if not success:
            raise ValueError(f"审核项不存在: {item_id}")
        
        return {"success": True, "message": "已拒绝"}
    
    @staticmethod
    def modify_audit_item(
        item_id: str,
        reviewer: str,
        modified_response: str,
        notes: str = ""
    ) -> Dict:
        """修改审核项"""
        success = audit_queue.modify_item(item_id, reviewer, modified_response, notes)
        
        if not success:
            raise ValueError(f"审核项不存在: {item_id}")
        
        return {"success": True, "message": "已修改", "modified_response": modified_response}
