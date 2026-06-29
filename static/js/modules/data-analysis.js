/**
 * 数据分析模块
 * 负责数据统计、图表生成和质量分析
 */
class DataAnalysis {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.charts = {}; // 存储图表实例
        this.init();
    }

    init() {
        this.bindEvents();
    }

    /**
     * 绑定数据分析相关事件
     */
    bindEvents() {
        // 一致性计算按钮
        document.getElementById('calculate-consistency-btn')?.addEventListener('click', () => {
            this.calculateConsistency();
        });

        // 生成一致性报告按钮
        document.getElementById('generate-consistency-report-btn')?.addEventListener('click', () => {
            this.generateConsistencyReport();
        });

        // 导出一致性报告按钮
        document.getElementById('export-consistency-report-btn')?.addEventListener('click', () => {
            this.exportConsistencyReport();
        });

        // 图表导出按钮事件委托
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('export-chart-btn')) {
                const chartType = e.target.dataset.chart;
                this.exportChart(chartType);
            }
        });
    }


    /**
     * 加载分组列表（用于说话人页面）
     */
    async loadGroupsList() {
        try {
            const data = await window.loadingManager.manageLoading(
                window.optimizedDataService.getGroups(),
                {
                    type: 'section',
                    sectionId: 'speakers-section',
                    text: '加载分组列表...',
                    minDuration: 300
                }
            );

            if (data && data.success) {
                this.updateGroupsFilter(data.groups || []);
            } else {
                this.dashboard.showError('加载分组列表失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新分组筛选器
     * @param {Array} groups - 分组数据
     */
    updateGroupsFilter(groups) {
        const groupFilter = document.getElementById('group-filter');
        if (!groupFilter) return;

        groupFilter.innerHTML = '<option value="">所有分组</option>';
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.id;
            option.textContent = group.name;
            groupFilter.appendChild(option);
        });
    }



    /**
     * 加载质量分析分组列表
     */
    async loadQualityGroupsList() {
        try {
            const data = await window.optimizedDataService.getGroups();

            if (data && data.success) {
                this.updateQualityGroupsFilter(data.groups || []);
            } else {
                this.dashboard.showError('加载质量分析分组列表失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新质量分析分组筛选器
     * @param {Array} groups - 分组数据
     */
    updateQualityGroupsFilter(groups) {
        const qualityGroupFilter = document.getElementById('quality-group-filter');
        if (!qualityGroupFilter) return;

        qualityGroupFilter.innerHTML = '<option value="">所有分组</option>';
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.id;
            option.textContent = group.name;
            qualityGroupFilter.appendChild(option);
        });
    }

    /**
     * 加载质量分析数据
     */
    async loadQualityData() {
        try {
            const qualitySection = document.getElementById('quality-section');
            if (qualitySection) {
                window.loadingManager.createSkeleton(qualitySection, {
                    rows: 5,
                    height: '60px',
                    spacing: '15px'
                });
            }

            const data = await window.loadingManager.manageLoading(
                window.optimizedDataService.getQualityData(),
                {
                    type: 'top',
                    showProgress: true,
                    minDuration: 500
                }
            );

            if (qualitySection) {
                window.loadingManager.removeSkeleton(qualitySection);
            }

            if (data && data.success) {
                this.updateQualityDisplay(data.data);
                this.generateCharts(data.data);
            } else {
                this.dashboard.showError('加载质量数据失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            const qualitySection = document.getElementById('quality-section');
            if (qualitySection) {
                window.loadingManager.removeSkeleton(qualitySection);
            }
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 加载质量分析数据（兼容旧方法名）
     */
    async loadQuality() {
        return this.loadQualityData();
    }

    /**
     * 更新质量显示
     * @param {Object} qualityData - 质量数据
     */
    updateQualityDisplay(qualityData) {
        // 更新统计信息
        const statsContainer = document.getElementById('quality-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="status-label">总标注数:</span>
                        <span class="status-value">${qualityData.total_annotations}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">完成标注数:</span>
                        <span class="status-value">${qualityData.completed_annotations}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">完成率:</span>
                        <span class="status-value">${qualityData.completion_rate}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">平均播放次数:</span>
                        <span class="status-value">${qualityData.avg_play_count}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">平均标注时长:</span>
                        <span class="status-value">${qualityData.avg_annotation_time}秒</span>
                    </div>
                </div>
            `;
        }
    }

    /**
     * 生成图表
     * @param {Object} data - 数据
     */
    generateCharts(data) {
        this.generateValenceChart(data.valence_distribution);
        this.generateArousalChart(data.arousal_distribution);
        this.generateDiscreteEmotionChart(data.discrete_emotion_distribution);
    }

    /**
     * 生成效价分布图表
     * @param {Array} data - 效价分布数据
     */
    generateValenceChart(data) {
        const ctx = document.getElementById('valence-chart');
        if (!ctx || !data) return;

        // 销毁现有图表
        if (this.charts.valence) {
            this.charts.valence.destroy();
        }

        this.charts.valence = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => `${item.range_start}-${item.range_end}`),
                datasets: [{
                    label: '效价分布',
                    data: data.map(item => item.count),
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '效价(Valence)分布'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * 生成唤醒度分布图表
     * @param {Array} data - 唤醒度分布数据
     */
    generateArousalChart(data) {
        const ctx = document.getElementById('arousal-chart');
        if (!ctx || !data) return;

        // 销毁现有图表
        if (this.charts.arousal) {
            this.charts.arousal.destroy();
        }

        this.charts.arousal = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => `${item.range_start}-${item.range_end}`),
                datasets: [{
                    label: '唤醒度分布',
                    data: data.map(item => item.count),
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '唤醒度(Arousal)分布'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * 生成离散情感分布图表
     * @param {Array} data - 离散情感分布数据
     */
    generateDiscreteEmotionChart(data) {
        const ctx = document.getElementById('discrete-emotion-chart');
        if (!ctx || !data) return;

        // 销毁现有图表
        if (this.charts.discreteEmotion) {
            this.charts.discreteEmotion.destroy();
        }

        const colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
        ];

        this.charts.discreteEmotion = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(item => item.emotion),
                datasets: [{
                    data: data.map(item => item.count),
                    backgroundColor: colors.slice(0, data.length),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '离散情感分布'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    /**
     * 导出图表
     * @param {string} chartType - 图表类型
     */
    exportChart(chartType) {
        const chart = this.charts[chartType];
        if (!chart) {
            this.dashboard.showError('图表不存在');
            return;
        }

        const canvas = chart.canvas;
        const link = document.createElement('a');
        link.download = `${chartType}_chart_${new Date().toISOString().slice(0, 10)}.png`;
        link.href = canvas.toDataURL();
        link.click();

        this.dashboard.showSuccess('图表已导出');
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
                this.loadConsistency(); // 刷新一致性数据
            } else {
                this.dashboard.showError('一致性计算失败: ' + data.error);
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
     * 加载一致性数据
     */
    async loadConsistency() {
        try {
            const consistencySection = document.getElementById('consistency-section');
            if (consistencySection) {
                window.loadingManager.createSkeleton(consistencySection, {
                    rows: 4,
                    height: '50px',
                    spacing: '12px'
                });
            }

            const data = await window.loadingManager.manageLoading(
                window.optimizedDataService.getConsistencyData(),
                {
                    type: 'section',
                    sectionId: 'consistency-section',
                    text: '加载一致性数据...',
                    minDuration: 400
                }
            );

            if (consistencySection) {
                window.loadingManager.removeSkeleton(consistencySection);
            }

            if (data) {
                this.updateConsistencyDisplay(data);
            } else {
                this.dashboard.showError('加载一致性数据失败: ' + (data?.error || '未知错误'));
            }
        } catch (error) {
            const consistencySection = document.getElementById('consistency-section');
            if (consistencySection) {
                window.loadingManager.removeSkeleton(consistencySection);
            }
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新一致性显示
     * @param {Object} consistencyData - 一致性数据
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
                        <span class="status-value">${consistencyData.total_comparisons}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">平均一致性:</span>
                        <span class="status-value">${consistencyData.avg_consistency}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">VA一致性:</span>
                        <span class="status-value">${consistencyData.va_consistency}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">离散情感一致性:</span>
                        <span class="status-value">${consistencyData.discrete_consistency}%</span>
                    </div>
                </div>
            </div>
            
            <div class="consistency-details">
                <h4>详细结果</h4>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>用户对</th>
                            <th>对比数</th>
                            <th>VA一致性</th>
                            <th>离散一致性</th>
                            <th>总体一致性</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${consistencyData.details.map(detail => `
                            <tr>
                                <td>${detail.user_pair}</td>
                                <td>${detail.comparison_count}</td>
                                <td>${detail.va_consistency}%</td>
                                <td>${detail.discrete_consistency}%</td>
                                <td>${detail.overall_consistency}%</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    /**
     * 生成一致性报告
     */
    async generateConsistencyReport() {
        try {
            const button = document.getElementById('generate-consistency-report-btn');
            const originalText = button.textContent;
            button.textContent = '生成中...';
            button.disabled = true;

            const response = await fetch('/admin/api/consistency/report', {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                this.dashboard.showSuccess('一致性报告生成完成');
                // 可以在这里显示报告内容或提供下载链接
            } else {
                this.dashboard.showError('报告生成失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            const button = document.getElementById('generate-consistency-report-btn');
            if (button) {
                button.textContent = '生成报告';
                button.disabled = false;
            }
        }
    }

    /**
     * 导出一致性报告
     */
    async exportConsistencyReport() {
        try {
            const response = await fetch('/admin/api/consistency/export');
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `consistency_report_${new Date().toISOString().slice(0, 10)}.csv`;
                link.click();
                window.URL.revokeObjectURL(url);
                
                this.dashboard.showSuccess('一致性报告已导出');
            } else {
                const data = await response.json();
                this.dashboard.showError('导出失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 加载系统状态
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
     * @param {Object} statusData - 系统状态数据
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
                        <span class="status-value">${statusData.database_size}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">音频文件数:</span>
                        <span class="status-value">${statusData.audio_files_count}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">总用户数:</span>
                        <span class="status-value">${statusData.total_users}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">活跃用户数:</span>
                        <span class="status-value">${statusData.active_users}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">系统运行时间:</span>
                        <span class="status-value">${statusData.uptime}</span>
                    </div>
                    <div class="stat-item">
                        <span class="status-label">最后备份时间:</span>
                        <span class="status-value">${statusData.last_backup || '从未备份'}</span>
                    </div>
                </div>
            </div>
        `;
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataAnalysis;
}