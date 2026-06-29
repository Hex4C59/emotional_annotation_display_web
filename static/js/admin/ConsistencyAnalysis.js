/**
 * 一致性分析模块
 * 负责处理用户标注一致性的计算和显示
 */
class ConsistencyAnalysis {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    /**
     * 绑定一致性分析相关事件
     */
    bindEvents() {
        // 计算一致性按钮
        const calculateBtn = document.getElementById('calculate-consistency-btn');
        if (calculateBtn) {
            calculateBtn.addEventListener('click', () => this.calculateConsistency());
        }

        // 刷新一致性数据按钮
        const refreshBtn = document.getElementById('refresh-consistency');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadConsistencyData());
        }
    }

    /**
     * 加载一致性数据
     */
    async loadConsistencyData() {
        try {
            const response = await fetch('/admin/api/consistency');
            const data = await response.json();

            if (response.ok) {
                this.updateConsistencyDisplay(data);
            } else {
                this.dashboard.showError('加载一致性数据失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 计算一致性
     */
    async calculateConsistency() {
        try {
            const button = document.getElementById('calculate-consistency-btn');
            const originalText = button.textContent;
            button.textContent = '计算中...';
            button.disabled = true;

            const response = await fetch('/admin/api/consistency/calculate', {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                this.dashboard.showSuccess('一致性计算完成');
                this.loadConsistencyData(); // 刷新一致性数据
            } else {
                this.dashboard.showError('计算一致性失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            const button = document.getElementById('calculate-consistency-btn');
            if (button) {
                button.textContent = '计算一致性';
                button.disabled = false;
            }
        }
    }

    /**
     * 更新一致性显示
     */
    updateConsistencyDisplay(consistencyData) {
        const container = document.getElementById('consistency-results');
        if (!container) return;

        container.innerHTML = `
            <div class="consistency-summary">
                <h4>一致性统计</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="status-label">总对比数:</span>
                        <span class="status-value">${consistencyData.total_comparisons || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">平均一致性:</span>
                        <span class="status-value">${consistencyData.avg_consistency || 0}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">高一致性用户:</span>
                        <span class="status-value">${consistencyData.high_consistency_users || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">低一致性用户:</span>
                        <span class="status-value">${consistencyData.low_consistency_users || 0}</span>
                    </div>
                </div>
            </div>
            <div class="consistency-details">
                <h4>用户一致性详情</h4>
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>用户名</th>
                                <th>一致性百分比</th>
                                <th>对比次数</th>
                                <th>状态</th>
                            </tr>
                        </thead>
                        <tbody id="consistency-table-body">
                            ${this.renderConsistencyTable(consistencyData.user_details || [])}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    /**
     * 渲染一致性表格
     */
    renderConsistencyTable(userDetails) {
        if (!userDetails || userDetails.length === 0) {
            return '<tr><td colspan="4" class="text-center">暂无数据</td></tr>';
        }

        return userDetails.map(user => {
            const statusClass = user.consistency >= 80 ? 'success' : user.consistency >= 60 ? 'warning' : 'danger';
            const statusText = user.consistency >= 80 ? '良好' : user.consistency >= 60 ? '一般' : '较差';
            
            return `
                <tr>
                    <td>${this.escapeHtml(user.username)}</td>
                    <td><span class="badge badge-${statusClass}">${user.consistency}%</span></td>
                    <td>${user.comparison_count}</td>
                    <td><span class="status-${statusClass}">${statusText}</span></td>
                </tr>
            `;
        }).join('');
    }

    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 确保类在全局作用域中可用
window.ConsistencyAnalysis = ConsistencyAnalysis;