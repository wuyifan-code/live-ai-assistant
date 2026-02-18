"""
增强版性能监控面板
提供实时监控API、可视化界面和丰富的图表
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


class EnhancedPerformanceMetrics:
    """增强版性能指标收集器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.start_time = time.time()
        
        # 时间序列数据（用于图表）
        self.time_series = {
            "danmaku_rate": deque(maxlen=100),
            "response_time": deque(maxlen=100),
            "cache_hit_rate": deque(maxlen=100),
            "error_rate": deque(maxlen=100),
            "websocket_latency": deque(maxlen=100)
        }
        
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
            "total_errors": 0,
            "tts_outputs": 0,
            "ocr_operations": 0,
            "visual_analyses": 0
        }
        
        # 统计数据
        self.stats = {
            "total_danmaku_processed": 0,
            "total_errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time_sum": 0.0,
            "response_count": 0,
            "takeovers": 0,
            "audits": 0
        }
        
        # 时间窗口统计
        self.window_stats = {
            "1min": {"danmaku": 0, "errors": 0},
            "5min": {"danmaku": 0, "errors": 0},
            "15min": {"danmaku": 0, "errors": 0}
        }
    
    def record_metric(self, metric_name: str, value: float):
        """记录指标"""
        self.current[metric_name] = value
        
        # 记录到历史
        timestamp = datetime.now()
        self.metrics_history.append({
            "timestamp": timestamp.isoformat(),
            "metric": metric_name,
            "value": value
        })
        
        # 记录到时间序列
        if metric_name in self.time_series:
            self.time_series[metric_name].append({
                "timestamp": timestamp.isoformat(),
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
        
        # 更新时间序列
        self.time_series["response_time"].append({
            "timestamp": datetime.now().isoformat(),
            "value": response_time
        })
    
    def record_cache_hit(self, hit: bool):
        """记录缓存命中"""
        if hit:
            self.stats["cache_hits"] += 1
        else:
            self.stats["cache_misses"] += 1
        
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total > 0:
            self.current["cache_hit_rate"] = self.stats["cache_hits"] / total
            
            # 更新时间序列
            self.time_series["cache_hit_rate"].append({
                "timestamp": datetime.now().isoformat(),
                "value": self.current["cache_hit_rate"]
            })
    
    def record_error(self):
        """记录错误"""
        self.stats["total_errors"] += 1
        self.current["total_errors"] = self.stats["total_errors"]
        
        # 更新时间序列
        self.time_series["error_rate"].append({
            "timestamp": datetime.now().isoformat(),
            "value": self.stats["total_errors"]
        })
    
    def record_tts_output(self):
        """记录TTS输出"""
        self.current["tts_outputs"] += 1
    
    def record_ocr_operation(self):
        """记录OCR操作"""
        self.current["ocr_operations"] += 1
    
    def record_visual_analysis(self):
        """记录视觉分析"""
        self.current["visual_analyses"] += 1
    
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
    
    def get_time_series(self, metric_name: str = None) -> Dict[str, List]:
        """获取时间序列数据"""
        if metric_name:
            if metric_name in self.time_series:
                return {
                    "metric": metric_name,
                    "data": list(self.time_series[metric_name])
                }
            return {}
        
        # 返回所有时间序列
        return {
            name: list(data)
            for name, data in self.time_series.items()
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


# 全局增强版性能指标收集器
enhanced_performance_metrics = EnhancedPerformanceMetrics()


class EnhancedMonitoringAPI:
    """增强版监控API"""
    
    def __init__(self):
        self.app = FastAPI(title="Live AI Assistant - Enhanced Monitoring API")
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/")
        async def dashboard():
            """监控仪表板"""
            html_content = self._generate_enhanced_dashboard_html()
            return HTMLResponse(content=html_content)
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """获取当前指标"""
            return JSONResponse(content=enhanced_performance_metrics.get_current_metrics())
        
        @self.app.get("/api/stats")
        async def get_stats():
            """获取统计数据"""
            return JSONResponse(content=enhanced_performance_metrics.get_stats())
        
        @self.app.get("/api/timeseries/{metric_name}")
        async def get_time_series(metric_name: str):
            """获取时间序列数据"""
            data = enhanced_performance_metrics.get_time_series(metric_name)
            return JSONResponse(content=data)
        
        @self.app.get("/api/timeseries")
        async def get_all_time_series():
            """获取所有时间序列数据"""
            data = enhanced_performance_metrics.get_time_series()
            return JSONResponse(content=data)
        
        @self.app.get("/api/history/{metric_name}")
        async def get_metric_history(metric_name: str, minutes: int = 10):
            """获取指标历史"""
            history = enhanced_performance_metrics.get_metrics_history(metric_name, minutes)
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
        
        @self.app.get("/api/collaboration")
        async def get_collaboration_stats():
            """获取人机协作统计"""
            try:
                from .human_collaboration import takeover_trigger, audit_queue
                
                return JSONResponse(content={
                    "takeover": takeover_trigger.get_statistics(),
                    "audit": audit_queue.get_statistics()
                })
            except ImportError:
                return JSONResponse(content={
                    "takeover": {},
                    "audit": {}
                })
    
    def _generate_enhanced_dashboard_html(self) -> str:
        """生成增强版仪表板HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Live AI Assistant - 增强版监控面板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .status-badge {
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        
        .status-healthy { background: #4caf50; color: white; }
        .status-degraded { background: #ff9800; color: white; }
        .status-unhealthy { background: #f44336; color: white; }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }
        
        .metric-title {
            color: #666;
            font-size: 13px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-value {
            font-size: 36px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
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
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .chart-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .chart-title {
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
        }
        
        .section {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin-bottom: 20px;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
            display: flex;
            align-items: center;
            gap: 8px;
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
        
        .progress-green { background: linear-gradient(90deg, #4caf50, #81c784); }
        .progress-yellow { background: linear-gradient(90deg, #ff9800, #ffb74d); }
        .progress-red { background: linear-gradient(90deg, #f44336, #e57373); }
        
        .refresh-btn {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            transition: transform 0.2s ease;
        }
        
        .refresh-btn:hover {
            transform: scale(1.05);
        }
        
        .footer {
            text-align: center;
            color: white;
            font-size: 12px;
            margin-top: 20px;
            opacity: 0.8;
        }
        
        .alert-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        
        .alert-high { background: #ffebee; color: #c62828; }
        .alert-medium { background: #fff3e0; color: #e65100; }
        .alert-low { background: #e8f5e9; color: #2e7d32; }
    </style>
</head>
<body>
    <div class="container">
        <h1>
            🎥 Live AI Assistant - 增强版监控面板
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
            </div>
            
            <div class="metric-card">
                <div class="metric-title">TTS输出</div>
                <div class="metric-value" id="tts-outputs">0</div>
                <div class="metric-unit">次</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">视觉分析</div>
                <div class="metric-value" id="visual-analyses">0</div>
                <div class="metric-unit">次</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-title">📈 响应时间趋势</div>
                <canvas id="responseTimeChart" height="200"></canvas>
            </div>
            
            <div class="chart-card">
                <div class="chart-title">📊 缓存命中率趋势</div>
                <canvas id="cacheHitChart" height="200"></canvas>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🔌 WebSocket连接状态</div>
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
            <div class="section-title">👥 人机协作统计</div>
            <table class="table">
                <thead>
                    <tr>
                        <th>类型</th>
                        <th>总数</th>
                        <th>已处理</th>
                        <th>待处理</th>
                        <th>处理率</th>
                    </tr>
                </thead>
                <tbody id="collaboration-table">
                    <tr><td colspan="5">加载中...</td></tr>
                </tbody>
            </table>
        </div>
        
        <button class="refresh-btn" onclick="loadData()">🔄 刷新数据</button>
        
        <div class="footer">
            Live AI Assistant v2.1 | 增强版监控面板 | 自动刷新: 3秒
        </div>
    </div>
    
    <script>
        let responseTimeChart, cacheHitChart;
        
        // 初始化图表
        function initCharts() {
            const ctx1 = document.getElementById('responseTimeChart').getContext('2d');
            const ctx2 = document.getElementById('cacheHitChart').getContext('2d');
            
            responseTimeChart = new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '响应时间(秒)',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
            
            cacheHitChart = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '缓存命中率(%)',
                        data: [],
                        borderColor: '#4caf50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true, max: 100 }
                    }
                }
            });
        }
        
        // 自动刷新
        setInterval(loadData, 3000);
        
        // 页面加载时初始化
        window.onload = function() {
            initCharts();
            loadData();
        };
        
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
                document.getElementById('tts-outputs').textContent = metrics.tts_outputs || 0;
                document.getElementById('visual-analyses').textContent = metrics.visual_analyses || 0;
                
                // 更新图表
                if (responseTimeChart && cacheHitChart) {
                    const now = new Date();
                    const timeLabel = now.getHours() + ':' + now.getMinutes() + ':' + now.getSeconds();
                    
                    responseTimeChart.data.labels.push(timeLabel);
                    responseTimeChart.data.datasets[0].data.push(metrics.avg_response_time);
                    
                    cacheHitChart.data.labels.push(timeLabel);
                    cacheHitChart.data.datasets[0].data.push(metrics.cache_hit_rate * 100);
                    
                    // 保持最近20个数据点
                    if (responseTimeChart.data.labels.length > 20) {
                        responseTimeChart.data.labels.shift();
                        responseTimeChart.data.datasets[0].data.shift();
                    }
                    
                    if (cacheHitChart.data.labels.length > 20) {
                        cacheHitChart.data.labels.shift();
                        cacheHitChart.data.datasets[0].data.shift();
                    }
                    
                    responseTimeChart.update('none');
                    cacheHitChart.update('none');
                }
                
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
                        const stateColor = conn.state === 'connected' ? '#4caf50' : 
                                         conn.state === 'reconnecting' ? '#ff9800' : '#f44336';
                        wsTable.innerHTML += `
                            <tr>
                                <td>${name}</td>
                                <td style="color: ${stateColor}; font-weight: bold;">${conn.state}</td>
                                <td>${conn.reconnect_count}</td>
                                <td>${conn.latency ? conn.latency.toFixed(3) + 's' : '-'}</td>
                                <td>${conn.messages_received} / ${conn.messages_sent}</td>
                            </tr>
                        `;
                    }
                } else {
                    wsTable.innerHTML = '<tr><td colspan="5">暂无连接</td></tr>';
                }
                
                // 加载人机协作统计
                try {
                    const collabRes = await fetch('/api/collaboration');
                    const collab = await collabRes.json();
                    
                    const collabTable = document.getElementById('collaboration-table');
                    collabTable.innerHTML = '';
                    
                    if (collab.takeover && Object.keys(collab.takeover).length > 0) {
                        collabTable.innerHTML += `
                            <tr>
                                <td>人工接管</td>
                                <td>${collab.takeover.total_takeovers || 0}</td>
                                <td>${collab.takeover.resolved_takeovers || 0}</td>
                                <td>${collab.takeover.pending_takeovers || 0}</td>
                                <td>${((collab.takeover.resolution_rate || 0) * 100).toFixed(1)}%</td>
                            </tr>
                        `;
                    }
                    
                    if (collab.audit && Object.keys(collab.audit).length > 0) {
                        collabTable.innerHTML += `
                            <tr>
                                <td>话术审核</td>
                                <td>${collab.audit.total_submitted || 0}</td>
                                <td>${collab.audit.total_approved || 0}</td>
                                <td>${collab.audit.pending_items || 0}</td>
                                <td>${((collab.audit.approval_rate || 0) * 100).toFixed(1)}%</td>
                            </tr>
                        `;
                    }
                    
                    if (!collabTable.innerHTML) {
                        collabTable.innerHTML = '<tr><td colspan="5">暂无数据</td></tr>';
                    }
                } catch (e) {
                    console.log('人机协作数据加载失败:', e);
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
        logger.info(f"🚀 启动增强版监控API服务: http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# 全局增强版监控API实例
enhanced_monitoring_api = EnhancedMonitoringAPI()


def record_danmaku(response_time: float):
    """记录弹幕处理"""
    enhanced_performance_metrics.record_danmaku(response_time)


def record_cache_hit(hit: bool):
    """记录缓存命中"""
    enhanced_performance_metrics.record_cache_hit(hit)


def record_error():
    """记录错误"""
    enhanced_performance_metrics.record_error()


def record_tts_output():
    """记录TTS输出"""
    enhanced_performance_metrics.record_tts_output()


def record_ocr_operation():
    """记录OCR操作"""
    enhanced_performance_metrics.record_ocr_operation()


def record_visual_analysis():
    """记录视觉分析"""
    enhanced_performance_metrics.record_visual_analysis()
