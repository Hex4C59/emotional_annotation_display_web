/**
 * 管理员管理模块
 * 负责管理员账户相关的所有操作
 */
class AdminManager {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    /**
     * 绑定管理员管理相关事件
     */
    bindEvents() {
        // 创建管理员按钮
        document.getElementById('create-admin-btn')?.addEventListener('click', () => {
            this.showCreateAdminModal();
        });

        // 创建管理员表单提交
        document.getElementById('create-admin-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createAdmin();
        });

        // 修改管理员表单提交
        document.getElementById('modify-admin-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.modifyAdmin();
        });
    }

    /**
     * 加载管理员数据
     */
    async loadAdmins() {
        try {
            const response = await fetch('/admin/api/admins');
            const data = await response.json();

            if (response.ok) {
                this.updateAdminsTable(data);
            } else {
                this.dashboard.showError('加载管理员数据失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 更新管理员表格
     * @param {Array} admins - 管理员数据数组
     */
    updateAdminsTable(admins) {
        const tbody = document.querySelector('#admins-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';

        admins.forEach(admin => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${admin.username}</td>
                <td><span class="status-badge ${admin.is_active ? 'active' : 'inactive'}">
                    ${admin.is_active ? '活跃' : '禁用'}
                </span></td>
                <td>${admin.created_at}</td>
                <td>${admin.last_login || '从未登录'}</td>
                <td>
                    <button class="btn btn-primary action-btn" onclick="adminDashboard.modules.adminManager.showModifyAdminModal('${admin.username}', ${admin.is_active})">修改</button>
                    <button class="btn ${admin.is_active ? 'btn-warning' : 'btn-success'} action-btn" 
                            onclick="adminDashboard.modules.adminManager.toggleAdminStatus('${admin.username}', ${admin.is_active})">
                        ${admin.is_active ? '禁用' : '启用'}
                    </button>
                    <button class="btn btn-danger action-btn" onclick="adminDashboard.modules.adminManager.confirmDeleteAdmin('${admin.username}')">删除</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    /**
     * 显示创建管理员模态框
     */
    showCreateAdminModal() {
        document.getElementById('create-admin-form').reset();
        document.getElementById('create-admin-modal').style.display = 'block';
    }

    /**
     * 创建管理员
     */
    async createAdmin() {
        try {
            const formData = new FormData(document.getElementById('create-admin-form'));
            const adminData = {
                username: formData.get('username'),
                password: formData.get('password'),
                confirm_password: formData.get('confirm_password')
            };

            // 验证密码
            if (adminData.password !== adminData.confirm_password) {
                this.dashboard.showError('两次输入的密码不一致');
                return;
            }

            if (adminData.password.length < 6) {
                this.dashboard.showError('密码长度至少6位');
                return;
            }

            const response = await fetch('/admin/api/admins', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: adminData.username,
                    password: adminData.password
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.dashboard.showSuccess('管理员创建成功');
                document.getElementById('create-admin-modal').style.display = 'none';
                this.loadAdmins(); // 刷新管理员列表
            } else {
                this.dashboard.showError('创建失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 显示修改管理员模态框
     * @param {string} username - 管理员用户名
     * @param {boolean} isActive - 是否活跃
     */
    showModifyAdminModal(username, isActive) {
        document.getElementById('modify-username').value = username;
        document.getElementById('modify-username').readOnly = true;
        document.getElementById('new-password').value = '';
        document.getElementById('confirm-new-password').value = '';
        document.getElementById('modify-admin-modal').style.display = 'block';
    }

    /**
     * 修改管理员
     */
    async modifyAdmin() {
        try {
            const formData = new FormData(document.getElementById('modify-admin-form'));
            const username = formData.get('username');
            const newPassword = formData.get('new_password');
            const confirmPassword = formData.get('confirm_new_password');

            // 验证密码
            if (newPassword !== confirmPassword) {
                this.dashboard.showError('两次输入的密码不一致');
                return;
            }

            if (newPassword && newPassword.length < 6) {
                this.dashboard.showError('密码长度至少6位');
                return;
            }

            const updateData = {};
            if (newPassword) {
                updateData.password = newPassword;
            }

            const response = await fetch(`/admin/api/admins/${username}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });

            const data = await response.json();

            if (response.ok) {
                this.dashboard.showSuccess('管理员信息修改成功');
                document.getElementById('modify-admin-modal').style.display = 'none';
                this.loadAdmins(); // 刷新管理员列表
            } else {
                this.dashboard.showError('修改失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }

    /**
     * 切换管理员状态
     * @param {string} username - 管理员用户名
     * @param {boolean} currentStatus - 当前状态
     */
    async toggleAdminStatus(username, currentStatus) {
        const action = currentStatus ? '禁用' : '启用';
        
        this.dashboard.showConfirm(
            `确定要${action}管理员 "${username}" 吗？`,
            async () => {
                try {
                    const response = await fetch(`/admin/api/admins/${username}/status`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            is_active: !currentStatus
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        this.dashboard.showSuccess(`管理员${action}成功`);
                        this.loadAdmins(); // 刷新管理员列表
                    } else {
                        this.dashboard.showError(`${action}失败: ` + data.error);
                    }
                } catch (error) {
                    this.dashboard.showError('网络错误: ' + error.message);
                }
            }
        );
    }

    /**
     * 确认删除管理员
     * @param {string} username - 管理员用户名
     */
    confirmDeleteAdmin(username) {
        this.dashboard.showConfirm(
            `确定要删除管理员 "${username}" 吗？此操作不可恢复！`,
            () => this.deleteAdmin(username)
        );
    }

    /**
     * 删除管理员
     * @param {string} username - 管理员用户名
     */
    async deleteAdmin(username) {
        try {
            const response = await fetch(`/admin/api/admins/${username}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok) {
                this.dashboard.showSuccess('管理员删除成功');
                this.loadAdmins(); // 刷新管理员列表
            } else {
                this.dashboard.showError('删除失败: ' + data.error);
            }
        } catch (error) {
            this.dashboard.showError('网络错误: ' + error.message);
        }
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminManager;
}