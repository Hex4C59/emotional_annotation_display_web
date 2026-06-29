/**
 * 数据分析模块
 * 负责说话人数据、质量分析、图表生成等功能
 */
class DataAnalysis {
    constructor(dashboard) {
        this.dashboard = dashboard;

        this.init();
    }

    init() {
        this.bindEvents();
    }

    /**
     * 绑定数据分析相关事件
     */
    bindEvents() {


        // 绑定分组选择事件
        document.getElementById('group-filter')?.addEventListener('change', (e) => {
            this.onGroupFilterChange(e.target.value);
        });

        // 质量分析分组选择事件
        document.getElementById('quality-group-filter')?.addEventListener('change', (e) => {
            this.onQualityGroupFilterChange(e.target.value);
        });

        // 质量分析刷新按钮
        document.getElementById('refresh-quality')?.addEventListener('click', () => {
            const groupId = document.getElementById('quality-group-filter')?.value;
            this.loadQualityData(groupId || null);
        });

        // 导出按钮
        document.getElementById('export-btn')?.addEventListener('click', () => {
            this.exportData();
        });

        // 直接下载按钮
        document.getElementById('download-btn')?.addEventListener('click', () => {
            this.downloadData();
        });

        document.getElementById('backup-btn')?.addEventListener('click', () => {
            this.backupDatabase();
        });

        // 图表导出按钮事件监听器 - 使用事件委托处理所有导出按钮
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('export-chart-btn')) {
                const chartId = e.target.getAttribute('data-chart');
                let filename = '';
                
                // 根据图表ID确定文件名
                switch(chartId) {
                    case 'a-value-chart':
                        filename = '分组A值分布图';
                        break;
                    case 'v-value-chart':
                        filename = '分组V值分布图';
                        break;
                    case 'discrete-emotion-user-chart':
                        filename = '分组离散情感分布图';
                        break;
                    case 'global-a-value-chart':
                        filename = '全局A值分布图';
                        break;
                    case 'global-v-value-chart':
                        filename = '全局V值分布图';
                        break;
                    case 'discrete-emotion-chart':
                        filename = '全局离散情感分布图';
                        break;
                    default:
                        filename = '图表';
                }
                
                this.exportChartAsImage(chartId, filename);
            }
        });
    }



    /**
     * 加载分组列表
     */
    async loadGroupsList() {
        try {
            const response = await fetch('/admin/api/groups');
            const data = await response.json();

            if (response.ok) {
                this.updateGroupsSelect(data.groups || []);
            } else {
                this.dashboard.showError('加载分组列表失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新分组选择下拉框
     * @param {Array} groups - 分组数据数组
     */
    updateGroupsSelect(groups) {
        const select = document.getElementById('group-filter');
        if (!select) return;
        
        // 清空现有选项（保留第一个"全部分组"选项）
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }

        // 添加分组选项
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.group_id;
            option.textContent = group.group_name;
            select.appendChild(option);
        });
    }

    /**
     * 分组筛选变化处理
     * @param {string} groupId - 分组ID
     */
    async onGroupFilterChange(groupId) {
        console.log('分组筛选变化:', groupId);
        
        if (groupId) {
            // 加载分组详细统计
            await this.loadGroupDetailedStatistics(groupId);
        }
        

    }

    /**
     * 加载分组详细统计
     * @param {string} groupId - 分组ID
     */
    async loadGroupDetailedStatistics(groupId) {
        try {
            const response = await fetch(`/admin/api/groups/${groupId}/statistics`);
            const data = await response.json();

            if (response.ok) {
                this.updateGroupSummary(data);
            } else {
                this.dashboard.showError('加载分组统计失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新分组摘要信息
     * @param {Object} groupStats - 分组统计数据
     */
    updateGroupSummary(groupStats) {
        // 更新基本信息
        const basicInfo = document.getElementById('group-basic-info');
        if (basicInfo) {
            basicInfo.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">分组名称:</span>
                    <span class="stat-value">${groupStats.group_name}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">总音频数:</span>
                    <span class="stat-value">${groupStats.total_segments}</span>
                </div>
            `;
        }

        // 更新用户信息
        const userInfo = document.getElementById('group-user-info');
        if (userInfo) {
            userInfo.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">用户数:</span>
                    <span class="stat-value">${groupStats.user_count}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">活跃用户:</span>
                    <span class="stat-value">${groupStats.active_users}</span>
                </div>
            `;
        }

        // 更新进度信息
        const progressInfo = document.getElementById('group-progress-info');
        if (progressInfo) {
            progressInfo.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">总标注数:</span>
                    <span class="stat-value">${groupStats.total_annotations}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">完成数:</span>
                    <span class="stat-value">${groupStats.completed_annotations}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">完成率:</span>
                    <span class="stat-value">${groupStats.completion_rate}%</span>
                </div>
            `;
        }


    }



    /**
     * 加载质量分析数据
     * @param {string|null} groupId - 分组ID
     */
    async loadQualityData(groupId = null) {
        try {
            let url = '/admin/api/quality-analysis';
            if (groupId) {
                url += `?group_id=${groupId}`;
            }
            
            const response = await fetch(url);
            const data = await response.json();

            if (response.ok) {
                this.updateQualityCharts(data, groupId);
            } else {
                this.dashboard.showError('加载质量分析数据失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新质量分析图表
     * @param {Object} data - 质量分析数据
     * @param {string|null} groupId - 分组ID
     */
    updateQualityCharts(data, groupId = null) {
        if (groupId) {
            this.updateGroupQualityCharts(data);
        } else {
            this.updateGlobalQualityCharts(data);
        }
    }

    /**
     * 更新分组质量图表
     * @param {Object} data - 质量分析数据
     */
    updateGroupQualityCharts(data) {
        // A值分布图表
        if (data.a_value_distribution) {
            const ctx = document.getElementById('a-value-chart');
            if (this.dashboard.charts.aValue) {
                this.dashboard.charts.aValue.destroy();
            }
            
            const aValueData = this.processValueDistribution(data.a_value_distribution, [
                '[-1.0, -0.6)', '[-0.6, -0.2)', '[-0.2, 0.2)', '[0.2, 0.6)', '[0.6, 1.0]'
            ]);
            
            this.dashboard.charts.aValue = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: aValueData.labels,
                    datasets: [{
                        label: 'A值分布',
                        data: aValueData.values,
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
                            text: '分组A值分布'
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

        // V值分布图表
        if (data.v_value_distribution) {
            const ctx = document.getElementById('v-value-chart');
            if (this.dashboard.charts.vValue) {
                this.dashboard.charts.vValue.destroy();
            }
            
            const vValueData = this.processValueDistribution(data.v_value_distribution, [
                '[-1.0, -0.6)', '[-0.6, -0.2)', '[-0.2, 0.2)', '[0.2, 0.6)', '[0.6, 1.0]'
            ]);
            
            this.dashboard.charts.vValue = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: vValueData.labels,
                    datasets: [{
                        label: 'V值分布',
                        data: vValueData.values,
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
                            text: '分组V值分布'
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

        // 离散情感分布图表
        if (data.discrete_emotion_distribution) {
            const ctx = document.getElementById('discrete-emotion-user-chart');
            if (this.dashboard.charts.discreteEmotionUser) {
                this.dashboard.charts.discreteEmotionUser.destroy();
            }
            
            const emotionData = this.processDiscreteEmotionDistribution(data.discrete_emotion_distribution);
            
            this.dashboard.charts.discreteEmotionUser = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: emotionData.labels,
                    datasets: [{
                        data: emotionData.values,
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: '分组离散情感分布'
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    /**
     * 更新全局质量图表
     * @param {Object} data - 质量分析数据
     */
    updateGlobalQualityCharts(data) {
        // 全局A值分布图表
        if (data.a_value_distribution) {
            const ctx = document.getElementById('global-a-value-chart');
            if (this.dashboard.charts.globalAValue) {
                this.dashboard.charts.globalAValue.destroy();
            }
            
            const aValueData = this.processValueDistribution(data.a_value_distribution, [
                '[-1.0, -0.6)', '[-0.6, -0.2)', '[-0.2, 0.2)', '[0.2, 0.6)', '[0.6, 1.0]'
            ]);
            
            this.dashboard.charts.globalAValue = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: aValueData.labels,
                    datasets: [{
                        label: 'A值分布',
                        data: aValueData.values,
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
                            text: '全局A值分布'
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

        // 全局V值分布图表
        if (data.v_value_distribution) {
            const ctx = document.getElementById('global-v-value-chart');
            if (this.dashboard.charts.globalVValue) {
                this.dashboard.charts.globalVValue.destroy();
            }
            
            const vValueData = this.processValueDistribution(data.v_value_distribution, [
                '[-1.0, -0.6)', '[-0.6, -0.2)', '[-0.2, 0.2)', '[0.2, 0.6)', '[0.6, 1.0]'
            ]);
            
            this.dashboard.charts.globalVValue = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: vValueData.labels,
                    datasets: [{
                        label: 'V值分布',
                        data: vValueData.values,
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
                            text: '全局V值分布'
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

        // 全局离散情感分布图表
        if (data.discrete_emotion_distribution) {
            const ctx = document.getElementById('discrete-emotion-chart');
            if (this.dashboard.charts.discreteEmotion) {
                this.dashboard.charts.discreteEmotion.destroy();
            }
            
            const emotionData = this.processDiscreteEmotionDistribution(data.discrete_emotion_distribution);
            
            this.dashboard.charts.discreteEmotion = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: emotionData.labels,
                    datasets: [{
                        data: emotionData.values,
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: '全局离散情感分布'
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    /**
     * 加载质量分析分组列表
     */
    async loadQualityGroupsList() {
        try {
            const response = await fetch('/admin/api/groups');
            const data = await response.json();

            if (response.ok) {
                this.updateQualityGroupFilter(data.groups || []);
            } else {
                this.dashboard.showError('加载分组列表失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新质量分析分组筛选器
     * @param {Array} groups - 分组数据数组
     */
    updateQualityGroupFilter(groups) {
        const select = document.getElementById('quality-group-filter');
        if (!select) return;
        
        // 清空现有选项（保留第一个"全部分组"选项）
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }

        // 添加分组选项
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.group_id;
            option.textContent = group.group_name;
            select.appendChild(option);
        });
    }

    /**
     * 质量分析分组筛选变化处理
     * @param {string} groupId - 分组ID
     */
    onQualityGroupFilterChange(groupId) {
        console.log('质量分析分组筛选变化:', groupId);
        this.loadQualityData(groupId || null);
    }

    /**
     * 导出数据
     */
    async exportData() {
        try {
            const response = await fetch('/admin/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    format: 'json',
                    include_metadata: true
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `emotion_labels_${new Date().toISOString().slice(0, 10)}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                this.dashboard.showSuccess('数据导出成功');
            } else {
                this.dashboard.showError('导出失败');
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 直接下载数据
     */
    async downloadData() {
        try {
            const response = await fetch('/admin/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    format: 'csv',
                    include_metadata: false
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                
                // 尝试从响应头获取文件名
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = `emotion_labels_${new Date().toISOString().slice(0, 10)}.csv`;
                
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                    if (filenameMatch && filenameMatch[1]) {
                        filename = filenameMatch[1];
                    }
                }
                
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                this.dashboard.showSuccess('数据下载成功');
            } else {
                this.dashboard.showError('下载失败');
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 备份数据库
     */
    async backupDatabase() {
        try {
            const response = await fetch('/admin/api/backup', {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                this.dashboard.showSuccess('数据库备份成功: ' + data.backup_file);
            } else {
                this.dashboard.showError('备份失败');
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 处理值分布数据
     * @param {Object} distributionData - 分布数据
     * @param {Array} ranges - 范围数组
     * @returns {Object} 处理后的数据
     */
    processValueDistribution(distributionData, ranges) {
        const labels = [];
        const values = [];
        
        ranges.forEach(range => {
            labels.push(range);
            values.push(distributionData[range] || 0);
        });
        
        return { labels, values };
    }

    /**
     * 处理离散情感分布数据
     * @param {Object} distributionData - 分布数据
     * @returns {Object} 处理后的数据
     */
    processDiscreteEmotionDistribution(distributionData) {
        const emotions = {
            'anger': '愤怒',
            'disgust': '厌恶', 
            'fear': '恐惧',
            'happiness': '快乐',
            'sadness': '悲伤',
            'surprise': '惊讶',
            'contempt': '蔑视',
            'neutral': '中性'
        };
        
        const labels = [];
        const values = [];
        
        Object.entries(distributionData).forEach(([emotion, count]) => {
            labels.push(emotions[emotion] || emotion);
            values.push(count);
        });
        
        return { labels, values };
    }

    /**
     * 导出图表为图片
     * @param {string} canvasId - 画布ID
     * @param {string} filename - 文件名
     */
    exportChartAsImage(canvasId, filename) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            this.dashboard.showError('找不到图表');
            return;
        }

        // 创建下载链接
        const link = document.createElement('a');
        link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.png`;
        link.href = canvas.toDataURL();
        link.click();
        
        this.dashboard.showSuccess('图表导出成功');
    }
}