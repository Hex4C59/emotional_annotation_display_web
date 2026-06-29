/**
 * 测试设置管理模块
 * 负责用户测试设置的加载、显示和更新
 */
class TestSettings {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    /**
     * 绑定测试设置相关事件
     */
    bindEvents() {
        // 刷新测试设置按钮
        document.getElementById('refresh-test-settings')?.addEventListener('click', () => {
            this.loadTestSettingsData();
        });

        // 绑定测试设置表格中的操作按钮事件
        this.bindTableEvents();
    }

    /**
     * 绑定表格中的事件
     */
    bindTableEvents() {
        const tbody = document.getElementById('test-settings-tbody');
        if (!tbody) return;

        // 使用事件委托处理动态生成的按钮
        tbody.addEventListener('click', (e) => {
            if (e.target.classList.contains('toggle-test-btn')) {
                const username = e.target.dataset.username;
                const currentSkipTest = e.target.dataset.skipTest === 'true';
                this.updateTestSetting(username, 'skip_test', !currentSkipTest);
            } else if (e.target.classList.contains('toggle-consistency-btn')) {
                const username = e.target.dataset.username;
                const currentSkipConsistency = e.target.dataset.skipConsistency === 'true';
                this.updateTestSetting(username, 'skip_consistency_test', !currentSkipConsistency);
            }
        });

        // 绑定量表顺序选择变化事件
        tbody.addEventListener('change', (e) => {
            if (e.target.classList.contains('scale-order-select')) {
                const username = e.target.dataset.username;
                const scaleOrder = e.target.value;
                this.updateScaleOrder(username, scaleOrder);
            }
        });
    }

    /**
     * 加载测试设置数据
     */
    async loadTestSettingsData() {
        try {
            const response = await fetch('/admin/api/users/test-settings');
            const data = await response.json();

            if (response.ok && data.success) {
                this.updateTestSettingsTable(data.users || []);
            } else {
                this.dashboard.showError('加载测试设置失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新测试设置表格
     * @param {Array} users - 用户列表
     */
    updateTestSettingsTable(users) {
        const tbody = document.getElementById('test-settings-tbody');
        if (!tbody) return;

        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无用户数据</td></tr>';
            return;
        }

        tbody.innerHTML = users.map(user => {
            const skipTest = user.skip_test || false;
            const skipConsistency = user.skip_consistency_test || false;
            const scaleOrder = user.scale_order || '5_point_first';
            const registrationTime = user.created_at ? 
                new Date(user.created_at).toLocaleString('zh-CN') : '未知';

            return `
                <tr>
                    <td>${this.escapeHtml(user.wechat_name || user.username || '未知')}</td>
                    <td>${this.escapeHtml(user.phone_number || '未设置')}</td>
                    <td>${registrationTime}</td>
                    <td>
                        <button class="btn ${skipTest ? 'btn-success' : 'btn-secondary'} btn-sm toggle-test-btn"
                                data-username="${this.escapeHtml(user.wechat_name || user.username)}"
                                data-skip-test="${skipTest}">
                            ${skipTest ? '已跳过' : '需测试'}
                        </button>
                    </td>
                    <td>
                        <button class="btn ${skipConsistency ? 'btn-success' : 'btn-secondary'} btn-sm toggle-consistency-btn"
                                data-username="${this.escapeHtml(user.wechat_name || user.username)}"
                                data-skip-consistency="${skipConsistency}">
                            ${skipConsistency ? '已跳过' : '需测试'}
                        </button>
                    </td>
                    <td>
                        <select class="form-control form-control-sm scale-order-select"
                                data-username="${this.escapeHtml(user.wechat_name || user.username)}">
                            <option value="9_point_first" ${scaleOrder === '9_point_first' ? 'selected' : ''}>9点量表优先</option>
                            <option value="5_point_first" ${scaleOrder === '5_point_first' ? 'selected' : ''}>5点量表优先</option>
                        </select>
                    </td>
                    <td>
                        <button class="btn btn-info btn-sm" onclick="adminDashboard.getModule('userManager').showUserDetails('${this.escapeHtml(user.wechat_name || user.username)}')">
                            查看详情
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    /**
     * 更新用户测试设置
     * @param {string} username - 用户名
     * @param {string} settingType - 设置类型 ('skip_test' 或 'skip_consistency_test')
     * @param {boolean} value - 设置值
     */
    async updateTestSetting(username, settingType, value) {
        try {
            const requestData = {
                username: username
            };
            requestData[settingType] = value;

            const response = await fetch('/admin/api/users/test-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.dashboard.showSuccess(`用户 ${username} 的${settingType === 'skip_test' ? '测试' : '一致性测试'}设置已更新`);
                // 重新加载数据以更新显示
                this.loadTestSettingsData();
            } else {
                this.dashboard.showError('更新设置失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新用户量表顺序
     * @param {string} username - 用户名
     * @param {string} scaleOrder - 量表顺序
     */
    async updateScaleOrder(username, scaleOrder) {
        try {
            const response = await fetch('/admin/api/users/scale-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    scale_order: scaleOrder
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.dashboard.showSuccess(`用户 ${username} 的量表顺序已更新为 ${scaleOrder === '9_point_first' ? '9点量表优先' : '5点量表优先'}`);
            } else {
                this.dashboard.showError('更新量表顺序失败: ' + (data.error || '未知错误'));
                // 重新加载数据以恢复原始状态
                this.loadTestSettingsData();
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
            // 重新加载数据以恢复原始状态
            this.loadTestSettingsData();
        }
    }

    /**
     * HTML转义
     * @param {string} text - 要转义的文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}