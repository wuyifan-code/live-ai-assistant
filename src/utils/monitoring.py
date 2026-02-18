"""
性能监控面板
提供实时监控API和可视化界面
"""

import asyncio
import logging
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import deque
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.start_time = time.time()
        
        # 当前指标
        self.current = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "danmaku_per_second": 0.0,
            "avg_response_time": 0.0,
            "cache_hit_rate": 0.0,
            "db_query_time": 0.0,
            "llm_response_time": 0.0,
            "websocket_latency": 0.0,
            "active_connections": 0,
            "total_danmaku": 0,
            "total_errors": 0
        }
        
        # 统计数据
        self.stats = {
            "total_danmaku_processed": 0,
            "total_errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time_sum": 0.0,
            "response_count": 0
        }
    
    def record_metric(self, metric_name: str, value: float):
        """记录指标"""
        self.current[metric_name] = value
        
        # 记录到历史
        self.metrics_history.append({
            "timestamp": datetime.now().isoformat(),
            "metric": metric_name,
            "value": value
        })
    
    def record_danmaku(self, response_time: float):
        """记录弹幕处理"""
        self.stats["total_danmaku_processed"] += 1
        self.stats["avg_response_time_sum"] += response_time
        self.stats["response_count"] += 1
        
        self.current["total_danmaku"] = self.stats["total_danmaku_processed"]
        self.current["avg_response_time"] = (
            self.stats["avg_response_time_sum"] / self.stats["response_count"]
        )
    
    def record_cache_hit(self, hit: bool):
        """记录缓存命中"""
        if hit:
            self.stats["cache_hits"] += 1
        else:
            self.stats["cache_misses"] += 1
        
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total > 0:
            self.current["cache_hit_rate"] = self.stats["cache_hits"] / total
    
    def record_error(self):
        """记录错误"""
        self.stats["total_errors"] += 1
        self.current["total_errors"] = self.stats["total_errors"]
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        return {
            **self.current,
            "uptime": time.time() - self.start_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        return {
            **self.stats,
            "uptime": time.time() - self.start_time,
            "cache_hit_rate": self.current["cache_hit_rate"],
            "avg_response_time": self.current["avg_response_time"]
        }
    
    def get_metrics_history(
        self,
        metric_name: str,
        minutes: int = 10
    ) -> List[Dict[str, Any]]:
        """获取指标历史"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        return [
            m for m in self.metrics_history
            if m["metric"] == metric_name
            and datetime.fromisoformat(m["timestamp"]) >= cutoff
        ]


# 全局性能指标收集器
performance_metrics = PerformanceMetrics()


class MonitoringAPI:
    """监控API"""
    
    def __init__(self):
        self.app = FastAPI(title="Live AI Assistant - Monitoring API")
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/")
        async def dashboard():
            """监控仪表板"""
            html_content = self._generate_dashboard_html()
            return HTMLResponse(content=html_content)
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """获取当前指标"""
            return JSONResponse(content=performance_metrics.get_current_metrics())
        
        @self.app.get("/api/stats")
        async def get_stats():
            """获取统计数据"""
            return JSONResponse(content=performance_metrics.get_stats())
        
        @self.app.get("/api/history/{metric_name}")
        async def get_metric_history(metric_name: str, minutes: int = 10):
            """获取指标历史"""
            history = performance_metrics.get_metrics_history(metric_name, minutes)
            return JSONResponse(content=history)
        
        @self.app.get("/api/health")
        async def health_check():
            """健康检查"""
            from .websocket_monitor import websocket_pool
            from .error_handler import error_handler
            
            pool_stats = websocket_pool.get_all_stats()
            error_stats = error_handler.get_error_stats()
            
            health_status = "healthy"
            if pool_stats["failed"] > 0:
                health_status = "degraded"
            if pool_stats["failed"] > 2 or error_stats["unresolved_errors"] > 5:
                health_status = "unhealthy"
            
            return JSONResponse(content={
                "status": health_status,
                "websocket": pool_stats,
                "errors": error_stats,
                "timestamp": datetime.now().isoformat()
            })
    
    def _generate_dashboard_html(self) -> str:
        """生成仪表板HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Live AI Assistant - 监控面板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: #333;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }
        
        .status-healthy { background: #4caf50; color: white; }
        .status-degraded { background: #ff9800; color: white; }
        .status-unhealthy { background: #f44336; color: white; }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .metric-title {
            color: #666;
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }
        
        .metric-unit {
            font-size: 14px;
            color: #999;
            margin-left: 4px;
        }
        
        .metric-change {
            font-size: 12px;
            margin-top: 8px;
        }
        
        .change-positive { color: #4caf50; }
        .change-negative { color: #f44336; }
        
        .section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .table th,
        .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .table th {
            background: #fafafa;
            font-weight: bold;
            color: #666;
        }
        
        .table tbody tr:hover {
            background: #f9f9f9;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        .progress-green { background: #4caf50; }
        .progress-yellow { background: #ff9800; }
        .progress-red { background: #f44336; }
        
        .refresh-btn {
            padding: 10px 20px;
            background: #2196f3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .refresh-btn:hover {
            background: #1976d2;
        }
        
        .footer {
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>
            🎥 Live AI Assistant - 监控面板
            <span id="status-badge" class="status-badge status-healthy">健康</span>
        </h1>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">弹幕处理数</div>
                <div class="metric-value" id="total-danmaku">0</div>
                <div class="metric-unit">条</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">平均响应时间</div>
                <div class="metric-value" id="avg-response-time">0.0</div>
                <div class="metric-unit">秒</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">缓存命中率</div>
                <div class="metric-value" id="cache-hit-rate">0.0</div>
                <div class="metric-unit">%</div>
                <div class="progress-bar">
                    <div class="progress-fill progress-green" id="cache-progress" style="width: 0%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">错误数</div>
                <div class="metric-value" id="total-errors">0</div>
                <div class="metric-unit">个</div>
                <div class="metric-change change-negative">↑ 检测到错误</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">活跃连接</div>
                <div class="metric-value" id="active-connections">0</div>
                <div class="metric-unit">个</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">运行时间</div>
                <div class="metric-value" id="uptime">0</div>
                <div class="metric-unit">秒</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">WebSocket连接状态</div>
            <table class="table">
                <thead>
                    <tr>
                        <th>连接名称</th>
                        <th>状态</th>
                        <th>重连次数</th>
                        <th>延迟</th>
                        <th>消息接收/发送</th>
                    </tr>
                </thead>
                <tbody id="websocket-table">
                    <tr><td colspan="5">加载中...</td></tr>
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <div class="section-title">错误统计</div>
            <table class="table">
                <thead>
                    <tr>
                        <th>错误类型</th>
                        <th>级别</th>
                        <th>数量</th>
                        <th>最近发生</th>
                    </tr>
                </thead>
                <tbody id="error-table">
                    <tr><td colspan="4">加载中...</td></tr>
                </tbody>
            </table>
        </div>
        
        <button class="refresh-btn" onclick="loadData()">🔄 刷新数据</button>
        
        <div class="footer">
            Live AI Assistant v2.0 | 监控面板 | 自动刷新: 5秒
        </div>
    </div>
    
    <script>
        // 自动刷新
        setInterval(loadData, 5000);
        
        // 页面加载时首次刷新
        window.onload = loadData;
        
        async function loadData() {
            try {
                // 加载指标
                const metricsRes = await fetch('/api/metrics');
                const metrics = await metricsRes.json();
                
                // 更新指标卡片
                document.getElementById('total-danmaku').textContent = metrics.total_danmaku;
                document.getElementById('avg-response-time').textContent = metrics.avg_response_time.toFixed(2);
                document.getElementById('cache-hit-rate').textContent = (metrics.cache_hit_rate * 100).toFixed(1);
                document.getElementById('cache-progress').style.width = (metrics.cache_hit_rate * 100) + '%';
                document.getElementById('total-errors').textContent = metrics.total_errors;
                document.getElementById('active-connections').textContent = metrics.active_connections;
                document.getElementById('uptime').textContent = Math.floor(metrics.uptime);
                
                // 加载健康状态
                const healthRes = await fetch('/api/health');
                const health = await healthRes.json();
                
                const statusBadge = document.getElementById('status-badge');
                statusBadge.textContent = health.status === 'healthy' ? '健康' : 
                                        health.status === 'degraded' ? '降级' : '异常';
                statusBadge.className = 'status-badge status-' + health.status;
                
                // 更新WebSocket表格
                const wsTable = document.getElementById('websocket-table');
                if (Object.keys(health.websocket.connections).length > 0) {
                    wsTable.innerHTML = '';
                    for (const [name, conn] of Object.entries(health.websocket.connections)) {
                        const stateColor = conn.state === 'connected' ? 'green' : 
                                         conn.state === 'reconnecting' ? 'orange' : 'red';
                        wsTable.innerHTML += `
                            <tr>
                                <td>${name}</td>
                                <td style="color: ${stateColor}">${conn.state}</td>
                                <td>${conn.reconnect_count}</td>
                                <td>${conn.latency ? conn.latency.toFixed(3) + 's' : '-'}</td>
                                <td>${conn.messages_received} / ${conn.messages_sent}</td>
                            </tr>
                        `;
                    }
                } else {
                    wsTable.innerHTML = '<tr><td colspan="5">暂无连接</td></tr>';
                }
                
                // 更新错误表格
                const errorTable = document.getElementById('error-table');
                if (Object.keys(health.errors.error_counts).length > 0) {
                    errorTable.innerHTML = '';
                    for (const [error_type, count] of Object.entries(health.errors.error_counts)) {
                        const parts = error_type.split(':');
                        errorTable.innerHTML += `
                            <tr>
                                <td>${parts[0]}</td>
                                <td>${parts[1]}</td>
                                <td>${count}</td>
                                <td>-</td>
                            </tr>
                        `;
                    }
                } else {
                    errorTable.innerHTML = '<tr><td colspan="4">暂无错误</td></tr>';
                }
                
            } catch (error) {
                console.error('加载数据失败:', error);
            }
        }
    </script>
</body>
</html>
        """
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """启动监控服务"""
        logger.info(f"🚀 启动监控API服务: http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# 全局监控API实例
monitoring_api = MonitoringAPI()


def record_danmaku(response_time: float):
    """记录弹幕处理"""
    performance_metrics.record_danmaku(response_time)


def record_cache_hit(hit: bool):
    """记录缓存命中"""
    performance_metrics.record_cache_hit(hit)


def record_error():
    """记录错误"""
    performance_metrics.record_error()
