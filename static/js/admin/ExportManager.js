/**
 * 导出管理模块
 * 负责数据导出、备份等功能
 */
class ExportManager {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    /**
     * 绑定导出相关事件
     */
    bindEvents() {
        // 导出按钮
        document.getElementById('export-btn')?.addEventListener('click', () => {
            this.exportData();
        });

        // 直接下载按钮
        document.getElementById('download-btn')?.addEventListener('click', () => {
            this.downloadData();
        });

        // 备份按钮
        document.getElementById('backup-btn')?.addEventListener('click', () => {
            this.backupDatabase();
        });

        // 导出用户数据按钮
        document.getElementById('export-users-btn')?.addEventListener('click', () => {
            this.exportUsersData();
        });

        // 导出管理员数据按钮
        document.getElementById('export-admins-btn')?.addEventListener('click', () => {
            this.exportAdminsData();
        });


    }

    /**
     * 导出标注数据
     * @param {string} format - 导出格式 (json/csv)
     * @param {boolean} includeMetadata - 是否包含元数据
     */
    async exportData(format = 'json', includeMetadata = true) {
        try {
            this.dashboard.showLoading('正在导出数据...');
            
            const response = await fetch('/admin/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    format: format,
                    include_metadata: includeMetadata
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `emotion_labels_${new Date().toISOString().slice(0, 10)}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                this.dashboard.showSuccess('数据导出成功');
            } else {
                const errorData = await response.json();
                this.dashboard.showError('导出失败: ' + (errorData.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
        }
    }

    /**
     * 直接下载CSV格式数据
     */
    async downloadData() {
        await this.exportData('csv', false);
    }

    /**
     * 导出用户数据
     */
    async exportUsersData() {
        try {
            this.dashboard.showLoading('正在导出用户数据...');
            
            const response = await fetch('/admin/api/export/users', {
                method: 'GET'
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `users_data_${new Date().toISOString().slice(0, 10)}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                this.dashboard.showSuccess('用户数据导出成功');
            } else {
                const errorData = await response.json();
                this.dashboard.showError('导出失败: ' + (errorData.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
        }
    }

    /**
     * 导出管理员数据
     */
    async exportAdminsData() {
        try {
            this.dashboard.showLoading('正在导出管理员数据...');
            
            const response = await fetch('/admin/api/export/admins', {
                method: 'GET'
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `admins_data_${new Date().toISOString().slice(0, 10)}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                this.dashboard.showSuccess('管理员数据导出成功');
            } else {
                const errorData = await response.json();
                this.dashboard.showError('导出失败: ' + (errorData.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
        }
    }



    /**
     * 备份数据库
     */
    async backupDatabase() {
        try {
            this.dashboard.showLoading('正在备份数据库...');
            
            const response = await fetch('/admin/api/backup', {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                this.dashboard.showSuccess('数据库备份成功: ' + data.backup_file);
            } else {
                const errorData = await response.json();
                this.dashboard.showError('备份失败: ' + (errorData.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
        }
    }

    /**
     * 导出分组数据
     * @param {string} groupId - 分组ID
     */
    async exportGroupData(groupId) {
        try {
            this.dashboard.showLoading('正在导出分组数据...');
            
            const response = await fetch(`/admin/api/export/group/${groupId}`, {
                method: 'GET'
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `group_${groupId}_data_${new Date().toISOString().slice(0, 10)}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                this.dashboard.showSuccess('分组数据导出成功');
            } else {
                const errorData = await response.json();
                this.dashboard.showError('导出失败: ' + (errorData.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
        }
    }

    /**
     * 导出用户标注数据
     * @param {string} userId - 用户ID
     */
    async exportUserAnnotations(userId) {
        try {
            this.dashboard.showLoading('正在导出用户标注数据...');
            
            const response = await fetch(`/admin/api/export/user/${userId}/annotations`, {
                method: 'GET'
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `user_${userId}_annotations_${new Date().toISOString().slice(0, 10)}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                this.dashboard.showSuccess('用户标注数据导出成功');
            } else {
                const errorData = await response.json();
                this.dashboard.showError('导出失败: ' + (errorData.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
        }
    }

    /**
     * 批量导出数据
     * @param {Array} exportItems - 导出项目列表
     */
    async batchExport(exportItems) {
        try {
            this.dashboard.showLoading('正在批量导出数据...');
            
            const response = await fetch('/admin/api/export/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    items: exportItems
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `batch_export_${new Date().toISOString().slice(0, 10)}.zip`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                this.dashboard.showSuccess('批量导出成功');
            } else {
                const errorData = await response.json();
                this.dashboard.showError('批量导出失败: ' + (errorData.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        } finally {
            this.dashboard.hideLoading();
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
                return data.history || [];
            } else {
                this.dashboard.showError('获取导出历史失败: ' + data.error);
                return [];
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
            return [];
        }
    }

    /**
     * 清理过期的导出文件
     */
    async cleanupExpiredExports() {
        try {
            const response = await fetch('/admin/api/export/cleanup', {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                this.dashboard.showSuccess(`清理完成，删除了 ${data.deleted_count} 个过期文件`);
            } else {
                const errorData = await response.json();
                this.dashboard.showError('清理失败: ' + (errorData.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }
}