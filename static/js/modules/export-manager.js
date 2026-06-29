/**
 * 导出管理模块
 * 负责数据导出和数据库备份功能
 */
class ExportManager {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.init();
    }

    init() {
        // 延迟绑定事件，确保DOM元素存在
        setTimeout(() => {
            this.bindEvents();
        }, 100);
    }

    /**
     * 绑定导出管理相关事件
     */
    bindEvents() {
        console.log('ExportManager: 开始绑定事件');
        
        // 导出标注数据按钮
        const exportAnnotationsBtn = document.getElementById('export-annotations-btn');
        if (exportAnnotationsBtn) {
            console.log('ExportManager: 找到导出标注数据按钮');
            exportAnnotationsBtn.addEventListener('click', () => {
                console.log('ExportManager: 点击导出标注数据按钮');
                this.exportAnnotations();
            });
        } else {
            console.warn('ExportManager: 未找到导出标注数据按钮');
        }

        // 导出用户数据按钮
        const exportUsersBtn = document.getElementById('export-users-btn');
        if (exportUsersBtn) {
            console.log('ExportManager: 找到导出用户数据按钮');
            exportUsersBtn.addEventListener('click', () => {
                console.log('ExportManager: 点击导出用户数据按钮');
                this.exportUsers();
            });
        } else {
            console.warn('ExportManager: 未找到导出用户数据按钮');
        }

        // 导出管理员数据按钮
        const exportAdminsBtn = document.getElementById('export-admins-btn');
        if (exportAdminsBtn) {
            console.log('ExportManager: 找到导出管理员数据按钮');
            exportAdminsBtn.addEventListener('click', () => {
                console.log('ExportManager: 点击导出管理员数据按钮');
                this.exportAdmins();
            });
        } else {
            console.warn('ExportManager: 未找到导出管理员数据按钮');
        }

        // 导出分组数据按钮
        const exportGroupsBtn = document.getElementById('export-groups-btn');
        if (exportGroupsBtn) {
            console.log('ExportManager: 找到导出分组数据按钮');
            exportGroupsBtn.addEventListener('click', () => {
                console.log('ExportManager: 点击导出分组数据按钮');
                this.exportGroups();
            });
        } else {
            console.warn('ExportManager: 未找到导出分组数据按钮');
        }

        // 导出用户标注数据按钮
        const exportUserAnnotationsBtn = document.getElementById('export-user-annotations-btn');
        if (exportUserAnnotationsBtn) {
            console.log('ExportManager: 找到导出用户标注数据按钮');
            exportUserAnnotationsBtn.addEventListener('click', () => {
                console.log('ExportManager: 点击导出用户标注数据按钮');
                this.exportUserAnnotations();
            });
        } else {
            console.warn('ExportManager: 未找到导出用户标注数据按钮');
        }

        // 批量导出按钮
        const batchExportBtn = document.getElementById('batch-export-btn');
        if (batchExportBtn) {
            console.log('ExportManager: 找到批量导出按钮');
            batchExportBtn.addEventListener('click', () => {
                console.log('ExportManager: 点击批量导出按钮');
                this.batchExport();
            });
        } else {
            console.warn('ExportManager: 未找到批量导出按钮');
        }

        // 备份数据库按钮
        const backupDatabaseBtn = document.getElementById('backup-database-btn');
        if (backupDatabaseBtn) {
            console.log('ExportManager: 找到备份数据库按钮');
            backupDatabaseBtn.addEventListener('click', () => {
                console.log('ExportManager: 点击备份数据库按钮');
                this.backupDatabase();
            });
        } else {
            console.warn('ExportManager: 未找到备份数据库按钮');
        }

        // 获取导出历史按钮
        const exportHistoryBtn = document.getElementById('export-history-btn');
        if (exportHistoryBtn) {
            console.log('ExportManager: 找到导出历史按钮');
            exportHistoryBtn.addEventListener('click', () => {
                console.log('ExportManager: 点击导出历史按钮');
                this.getExportHistory();
            });
        } else {
            console.warn('ExportManager: 未找到导出历史按钮');
        }
        
        console.log('ExportManager: 事件绑定完成');
    }

    /**
     * 导出标注数据
     */
    async exportAnnotations() {
        console.log('ExportManager: 开始导出标注数据');
        try {
            this.dashboard.showLoading('正在导出标注数据...');
            const button = document.getElementById('export-annotations-btn');
            this.setButtonLoading(button, '导出中...');

            console.log('ExportManager: 发送请求到 /admin/api/export/annotations');
            const response = await fetch('/admin/api/export/annotations');
            console.log('ExportManager: 收到响应', response.status, response.ok);
            
            if (response.ok) {
                console.log('ExportManager: 导出成功，开始下载文件');
                await this.downloadFile(response, 'annotations');
                this.dashboard.showSuccess('标注数据导出成功');
            } else {
                const data = await response.json();
                console.error('ExportManager: 导出失败', data);
                this.dashboard.showError('导出失败: ' + data.error);
            }
        } catch (error) {
            console.error('ExportManager: 导出标注数据时出错', error);
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
            this.resetButton(document.getElementById('export-annotations-btn'), '导出标注数据');
        }
    }

    /**
     * 导出用户数据
     */
    async exportUsers() {
        try {
            this.dashboard.showLoading('正在导出用户数据...');
            const button = document.getElementById('export-users-btn');
            this.setButtonLoading(button, '导出中...');

            const response = await fetch('/admin/api/export/users');
            
            if (response.ok) {
                await this.downloadFile(response, 'users');
                this.dashboard.showSuccess('用户数据导出成功');
            } else {
                const data = await response.json();
                this.dashboard.showError('导出失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
            this.resetButton(document.getElementById('export-users-btn'), '导出用户数据');
        }
    }

    /**
     * 导出管理员数据
     */
    async exportAdmins() {
        try {
            this.dashboard.showLoading('正在导出管理员数据...');
            const button = document.getElementById('export-admins-btn');
            this.setButtonLoading(button, '导出中...');

            const response = await fetch('/admin/api/export/admins');
            
            if (response.ok) {
                await this.downloadFile(response, 'admins');
                this.dashboard.showSuccess('管理员数据导出成功');
            } else {
                const data = await response.json();
                this.dashboard.showError('导出失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
            this.resetButton(document.getElementById('export-admins-btn'), '导出管理员数据');
        }
    }



    /**
     * 导出分组数据
     */
    async exportGroups() {
        try {
            this.dashboard.showLoading('正在导出分组数据...');
            const button = document.getElementById('export-groups-btn');
            this.setButtonLoading(button, '导出中...');

            const response = await fetch('/admin/api/export/groups');
            
            if (response.ok) {
                await this.downloadFile(response, 'groups');
                this.dashboard.showSuccess('分组数据导出成功');
            } else {
                const data = await response.json();
                this.dashboard.showError('导出失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
            this.resetButton(document.getElementById('export-groups-btn'), '导出分组数据');
        }
    }

    /**
     * 导出用户标注数据
     */
    async exportUserAnnotations() {
        console.log('ExportManager: 开始导出用户标注数据');
        try {
            this.dashboard.showLoading('正在导出用户标注数据...');
            const button = document.getElementById('export-user-annotations-btn');
            this.setButtonLoading(button, '导出中...');

            console.log('ExportManager: 发送请求到 /admin/api/export/user-annotations');
            const response = await fetch('/admin/api/export/user-annotations');
            console.log('ExportManager: 收到响应', response.status, response.ok);
            
            if (response.ok) {
                console.log('ExportManager: 导出成功，开始下载文件');
                await this.downloadFile(response, 'user_annotations');
                this.dashboard.showSuccess('用户5点量表和9点量表标注数据导出成功');
            } else {
                const data = await response.json();
                console.error('ExportManager: 导出失败', data);
                this.dashboard.showError('导出失败: ' + data.error);
            }
        } catch (error) {
            console.error('ExportManager: 导出用户标注数据时出错', error);
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
            this.resetButton(document.getElementById('export-user-annotations-btn'), '导出用户标注数据');
        }
    }

    /**
     * 批量导出所有数据
     */
    async batchExport() {
        try {
            this.dashboard.showLoading('正在批量导出数据...');
            const button = document.getElementById('batch-export-btn');
            this.setButtonLoading(button, '批量导出中...');

            const response = await fetch('/admin/api/export/batch');
            
            if (response.ok) {
                await this.downloadFile(response, 'batch_export');
                this.dashboard.showSuccess('批量导出成功');
            } else {
                const data = await response.json();
                this.dashboard.showError('批量导出失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
            this.resetButton(document.getElementById('batch-export-btn'), '批量导出');
        }
    }

    /**
     * 备份数据库
     */
    async backupDatabase() {
        try {
            this.dashboard.showLoading('正在备份数据库...');
            const button = document.getElementById('backup-database-btn');
            this.setButtonLoading(button, '备份中...');

            const response = await fetch('/admin/api/backup', {
                method: 'POST'
            });
            
            if (response.ok) {
                await this.downloadFile(response, 'database_backup');
                this.dashboard.showSuccess('数据库备份成功');
            } else {
                const data = await response.json();
                this.dashboard.showError('备份失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
            this.resetButton(document.getElementById('backup-database-btn'), '备份数据库');
        }
    }

    /**
     * 获取导出历史
     */
    async getExportHistory() {
        try {
            const response = await fetch('/admin/api/export/history');
            const data = await response.json();

            if (response.ok) {
                this.displayExportHistory(data);
            } else {
                this.dashboard.showError('获取导出历史失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 显示导出历史
     * @param {Array} history - 导出历史数据
     */
    displayExportHistory(history) {
        const container = document.getElementById('export-history');
        if (!container) return;

        if (history.length === 0) {
            container.innerHTML = '<p>暂无导出历史</p>';
            return;
        }

        container.innerHTML = `
            <h4>导出历史</h4>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>导出类型</th>
                        <th>文件名</th>
                        <th>文件大小</th>
                        <th>导出时间</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${history.map(item => `
                        <tr>
                            <td>${item.export_type}</td>
                            <td>${item.filename}</td>
                            <td>${item.file_size}</td>
                            <td>${item.created_at}</td>
                            <td><span class="status-badge ${item.status}">${item.status}</span></td>
                            <td>
                                ${item.status === 'completed' ? 
                                    `<button class="btn btn-primary action-btn" onclick="adminDashboard.modules.exportManager.downloadHistoryFile('${item.id}')">下载</button>` : 
                                    ''
                                }
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    /**
     * 下载历史文件
     * @param {string} fileId - 文件ID
     */
    async downloadHistoryFile(fileId) {
        try {
            const response = await fetch(`/admin/api/export/download/${fileId}`);
            
            if (response.ok) {
                await this.downloadFile(response, 'history_file');
                this.dashboard.showSuccess('文件下载成功');
            } else {
                const data = await response.json();
                this.dashboard.showError('下载失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 下载文件
     * @param {Response} response - 响应对象
     * @param {string} defaultName - 默认文件名
     */
    async downloadFile(response, defaultName) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        // 尝试从响应头获取文件名
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = defaultName;
        
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        // 如果没有扩展名，根据内容类型添加
        if (!filename.includes('.')) {
            const contentType = response.headers.get('Content-Type');
            if (contentType?.includes('csv')) {
                filename += '.csv';
            } else if (contentType?.includes('json')) {
                filename += '.json';
            } else if (contentType?.includes('zip')) {
                filename += '.zip';
            } else {
                filename += `_${new Date().toISOString().slice(0, 10)}.csv`;
            }
        }
        
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
    }

    /**
     * 设置按钮加载状态
     * @param {HTMLElement} button - 按钮元素
     * @param {string} loadingText - 加载文本
     */
    setButtonLoading(button, loadingText) {
        if (button) {
            button.dataset.originalText = button.textContent;
            button.textContent = loadingText;
            button.disabled = true;
        }
    }

    /**
     * 重置按钮状态
     * @param {HTMLElement} button - 按钮元素
     * @param {string} originalText - 原始文本
     */
    resetButton(button, originalText) {
        if (button) {
            button.textContent = originalText || button.dataset.originalText || '导出';
            button.disabled = false;
            delete button.dataset.originalText;
        }
    }

    /**
     * 获取导出进度
     * @param {string} taskId - 任务ID
     */
    async getExportProgress(taskId) {
        try {
            const response = await fetch(`/admin/api/export/progress/${taskId}`);
            const data = await response.json();

            if (response.ok) {
                return data;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('获取导出进度失败:', error);
            return null;
        }
    }

    /**
     * 显示导出进度
     * @param {string} taskId - 任务ID
     * @param {HTMLElement} progressContainer - 进度容器
     */
    async showExportProgress(taskId, progressContainer) {
        const checkProgress = async () => {
            const progress = await this.getExportProgress(taskId);
            
            if (progress) {
                progressContainer.innerHTML = `
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progress.percentage}%"></div>
                    </div>
                    <div class="progress-text">${progress.message} (${progress.percentage}%)</div>
                `;

                if (progress.status === 'completed') {
                    progressContainer.innerHTML += '<div class="progress-success">导出完成！</div>';
                    return;
                } else if (progress.status === 'failed') {
                    progressContainer.innerHTML += '<div class="progress-error">导出失败！</div>';
                    return;
                }

                // 继续检查进度
                setTimeout(checkProgress, 1000);
            }
        };

        checkProgress();
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ExportManager;
}