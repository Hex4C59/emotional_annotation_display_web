/**
 * 管理员仪表板主类
 * 负责整体的导航和模块协调
 */
class AdminDashboard {
    /**
     * 初始化管理员仪表板
     */
    constructor() {
        this.currentSection = 'users';
        this.charts = {};
        this.modules = {};
        // 异步初始化
        this.init().catch(error => {
            console.error('AdminDashboard初始化失败:', error);
        });
    }

    /**
     * 初始化仪表板
     */
    async init() {
        this.initModules();
        this.setupNavigation();
        this.bindGlobalEvents();
        
        // 延迟加载用户数据，确保DOM完全加载
        setTimeout(() => {
            this.loadSectionData('users'); // 默认加载用户管理
        }, 100);
    }



    /**
     * 初始化各个功能模块
     */
    initModules() {
        try {
            this.modules.userManager = new UserManager(this);
            this.modules.adminManager = new AdminManager(this);
            this.modules.dataAnalysis = new DataAnalysis(this);
            this.modules.consistencyAnalysis = new ConsistencyAnalysis(this);
            this.modules.testSettings = new TestSettings(this);
            this.modules.exportManager = new ExportManager(this);
            this.modules.systemStatus = new SystemStatus(this);
            this.modules.utils = new AdminUtils(this);
            
            console.log('所有模块初始化完成');
        } catch (error) {
            console.error('模块初始化失败:', error);
            this.showError('模块初始化失败: ' + error.message);
        }
    }

    /**
     * 设置导航
     */
    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                this.switchSection(section);
            });
        });
    }

    /**
     * 绑定全局事件
     */
    bindGlobalEvents() {
        // 模态框关闭
        document.querySelectorAll('.close').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                e.target.closest('.modal').style.display = 'none';
            });
        });

        // 点击模态框外部关闭
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });
    }

    /**
     * 切换页面部分
     * @param {string} section - 要切换到的部分
     */
    switchSection(section) {
        // 更新导航状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`)?.classList.add('active');

        // 更新内容区域
        document.querySelectorAll('.content-section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}-section`)?.classList.add('active');

        this.currentSection = section;

        // 加载对应数据
        this.loadSectionData(section);
    }

    /**
     * 加载指定部分的数据
     * @param {string} section - 部分名称
     */
    loadSectionData(section) {
        try {
            switch (section) {
                case 'users':
                    if (this.modules.userManager?.loadUsersData) {
                        this.modules.userManager.loadUsersData();
                    } else {
                        console.error('UserManager.loadUsersData方法不存在');
                    }
                    break;
                case 'admins':
                    if (this.modules.adminManager?.loadAdminsData) {
                        this.modules.adminManager.loadAdminsData();
                    } else {
                        console.error('AdminManager.loadAdminsData方法不存在');
                    }
                    break;
                case 'test-settings':
                    if (this.modules.testSettings?.loadTestSettingsData) {
                        this.modules.testSettings.loadTestSettingsData();
                    } else {
                        console.error('TestSettings.loadTestSettingsData方法不存在');
                    }
                    break;
                case 'quality':
                    if (this.modules.dataAnalysis?.loadQualityData) {
                        this.modules.dataAnalysis.loadQualityData();
                    } else {
                        console.error('DataAnalysis.loadQualityData方法不存在');
                    }
                    break;
                case 'consistency':
                    if (this.modules.consistencyAnalysis?.loadConsistencyData) {
                        this.modules.consistencyAnalysis.loadConsistencyData();
                    } else {
                        console.error('ConsistencyAnalysis.loadConsistencyData方法不存在');
                    }
                    break;
                case 'system':
                    if (this.modules.systemStatus?.loadSystemStatus) {
                        this.modules.systemStatus.loadSystemStatus();
                    } else {
                        console.error('SystemStatus.loadSystemStatus方法不存在');
                    }
                    break;
                case 'export':
                    // 数据导出部分不需要加载数据，只需要初始化事件绑定
                    console.log('数据导出模块已初始化');
                    // 重新绑定导出事件，确保按钮事件正确绑定
                    if (this.modules.exportManager?.bindEvents) {
                        this.modules.exportManager.bindEvents();
                    }
                    break;
                default:
                    console.warn('未知的部分:', section);
            }
        } catch (error) {
            console.error('加载部分数据失败:', error);
            this.showError('加载数据失败: ' + error.message);
        }
    }

    /**
     * 显示成功消息
     * @param {string} message - 消息内容
     */
    showSuccess(message) {
        if (this.modules.utils?.showSuccess) {
            this.modules.utils.showSuccess(message);
        } else {
            // 备用显示方法
            alert('成功: ' + message);
        }
    }

    /**
     * 显示错误消息
     * @param {string} message - 消息内容
     */
    showError(message) {
        if (this.modules.utils?.showError) {
            this.modules.utils.showError(message);
        } else {
            // 备用显示方法
            console.error(message);
            alert('错误: ' + message);
        }
    }

    /**
     * 显示加载状态
     * @param {string} message - 加载消息
     */
    showLoading(message = '加载中...') {
        // 创建或获取加载提示元素
        let loadingElement = document.getElementById('global-loading');
        if (!loadingElement) {
            loadingElement = document.createElement('div');
            loadingElement.id = 'global-loading';
            loadingElement.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                color: white;
                font-size: 16px;
            `;
            document.body.appendChild(loadingElement);
        }
        
        loadingElement.innerHTML = `
            <div style="text-align: center;">
                <div style="border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 10px;"></div>
                <div>${message}</div>
            </div>
        `;
        loadingElement.style.display = 'flex';
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        const loadingElement = document.getElementById('global-loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    /**
     * 获取当前模块
     * @param {string} moduleName - 模块名称
     * @returns {Object} 模块实例
     */
    getModule(moduleName) {
        return this.modules[moduleName];
    }
}

// 全局实例
let adminDashboard;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    try {
        adminDashboard = new AdminDashboard();
        console.log('AdminDashboard初始化成功');
    } catch (error) {
        console.error('AdminDashboard初始化失败:', error);
        // 显示错误信息给用户
        alert('管理员后台初始化失败，请刷新页面重试。错误信息: ' + error.message);
    }
});