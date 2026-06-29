/**
 * 系统状态模块
 * 负责显示和管理系统状态信息
 */
class SystemStatus {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    /**
     * 绑定系统状态相关事件
     */
    bindEvents() {
        // 刷新系统状态按钮
        const refreshBtn = document.getElementById('refresh-system-status');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadSystemStatusData());
        }
    }

    /**
     * 加载系统状态数据
     */
    async loadSystemStatusData() {
        return this.loadSystemStatus();
    }

    /**
     * 加载系统状态（兼容AdminDashboard调用）
     */
    async loadSystemStatus() {
        try {
            const response = await fetch('/admin/api/system/status');
            const data = await response.json();

            if (response.ok) {
                this.updateSystemStatusDisplay(data);
            } else {
                this.dashboard.showError('加载系统状态失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新系统状态显示
     */
    updateSystemStatusDisplay(statusData) {
        const container = document.getElementById('system-status');
        if (!container) return;

        container.innerHTML = `
            <div class="system-info">
                <h4>系统信息</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="status-label">数据库大小:</span>
                        <span class="status-value">${statusData.database_size || '未知'}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">音频文件数:</span>
                        <span class="status-value">${statusData.audio_files_count || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">总用户数:</span>
                        <span class="status-value">${statusData.total_users || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">活跃用户数:</span>
                        <span class="status-value">${statusData.active_users || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">总标注数:</span>
                        <span class="status-value">${statusData.total_annotations || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">今日标注数:</span>
                        <span class="status-value">${statusData.today_annotations || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">服务器时间:</span>
                        <span class="status-value">${this.formatDate(new Date())}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">系统版本:</span>
                        <span class="status-value">${statusData.version || '1.0.0'}</span>
                    </div>
                </div>
            </div>
            <div class="database-info">
                <h4>数据库状态</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="status-label">用户数据库:</span>
                        <span class="status-value status-${statusData.users_db_status === 'ok' ? 'success' : 'danger'}">
                            ${statusData.users_db_status === 'ok' ? '正常' : '异常'}
                        </span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">标注数据库:</span>
                        <span class="status-value status-${statusData.annotations_db_status === 'ok' ? 'success' : 'danger'}">
                            ${statusData.annotations_db_status === 'ok' ? '正常' : '异常'}
                        </span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">磁盘使用率:</span>
                        <span class="status-value">${statusData.disk_usage || '未知'}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">内存使用率:</span>
                        <span class="status-value">${statusData.memory_usage || '未知'}</span>
                    </div>
                </div>
            </div>
            <div class="performance-info">
                <h4>性能指标</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="status-label">平均响应时间:</span>
                        <span class="status-value">${statusData.avg_response_time || '未知'}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">今日请求数:</span>
                        <span class="status-value">${statusData.today_requests || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">错误率:</span>
                        <span class="status-value">${statusData.error_rate || '0%'}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">在线用户:</span>
                        <span class="status-value">${statusData.online_users || 0}</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 格式化日期
     */
    formatDate(date) {
        if (!date) return '未知';
        
        const options = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        };
        
        return date.toLocaleString('zh-CN', options);
    }

    /**
     * 获取系统健康状态
     */
    getSystemHealth(statusData) {
        const issues = [];
        
        if (statusData.users_db_status !== 'ok') {
            issues.push('用户数据库异常');
        }
        
        if (statusData.annotations_db_status !== 'ok') {
            issues.push('标注数据库异常');
        }
        
        if (statusData.disk_usage && parseFloat(statusData.disk_usage) > 90) {
            issues.push('磁盘空间不足');
        }
        
        if (statusData.memory_usage && parseFloat(statusData.memory_usage) > 90) {
            issues.push('内存使用率过高');
        }
        
        return {
            status: issues.length === 0 ? 'healthy' : 'warning',
            issues: issues
        };
    }
}

// 确保类在全局作用域中可用
window.SystemStatus = SystemStatus;