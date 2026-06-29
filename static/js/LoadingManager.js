/**
 * 加载状态管理器
 * 负责管理页面加载状态、进度显示和用户体验优化
 */
class LoadingManager {
    constructor() {
        this.loadingStates = new Map();
        this.loadingElements = new Map();
        this.progressBars = new Map();
        this.init();
    }

    /**
     * 初始化加载管理器
     */
    init() {
        this.createGlobalLoadingOverlay();
        this.createProgressBar();
        this.bindEvents();
    }

    /**
     * 创建全局加载遮罩
     */
    createGlobalLoadingOverlay() {
        if (document.getElementById('global-loading-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'global-loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <div class="loading-text">加载中...</div>
                <div class="loading-progress">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">0%</div>
                </div>
            </div>
        `;
        
        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.9);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                backdrop-filter: blur(2px);
            }
            
            .loading-overlay.show {
                display: flex;
            }
            
            .loading-content {
                text-align: center;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                min-width: 300px;
            }
            
            .loading-spinner {
                width: 40px;
                height: 40px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .loading-text {
                font-size: 16px;
                color: #333;
                margin-bottom: 20px;
            }
            
            .loading-progress {
                width: 100%;
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #f0f0f0;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 10px;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #3498db, #2ecc71);
                width: 0%;
                transition: width 0.3s ease;
            }
            
            .progress-text {
                font-size: 14px;
                color: #666;
            }
            
            .loading-skeleton {
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
            }
            
            @keyframes loading {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }
            
            .section-loading {
                position: relative;
                min-height: 100px;
            }
            
            .section-loading::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10;
            }
            
            .section-loading::after {
                content: '加载中...';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 11;
                color: #666;
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(overlay);
    }

    /**
     * 创建进度条
     */
    createProgressBar() {
        if (document.getElementById('top-progress-bar')) return;

        const progressBar = document.createElement('div');
        progressBar.id = 'top-progress-bar';
        progressBar.innerHTML = '<div class="progress-fill"></div>';
        
        const style = document.createElement('style');
        style.textContent = `
            #top-progress-bar {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 3px;
                background: rgba(255, 255, 255, 0.2);
                z-index: 10000;
                display: none;
            }
            
            #top-progress-bar .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #3498db, #2ecc71);
                width: 0%;
                transition: width 0.3s ease;
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(progressBar);
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 监听页面切换
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('[data-section]');
            if (navLink) {
                const section = navLink.dataset.section;
                this.showSectionLoading(section);
            }
        });
    }

    /**
     * 显示全局加载状态
     * @param {string} text - 加载文本
     * @param {Object} options - 选项
     */
    showGlobalLoading(text = '加载中...', options = {}) {
        const overlay = document.getElementById('global-loading-overlay');
        const textElement = overlay.querySelector('.loading-text');
        const progressElement = overlay.querySelector('.loading-progress');
        
        textElement.textContent = text;
        
        if (options.hideProgress) {
            progressElement.style.display = 'none';
        } else {
            progressElement.style.display = 'block';
            this.updateProgress('global', 0);
        }
        
        overlay.classList.add('show');
        this.loadingStates.set('global', { active: true, startTime: Date.now() });
    }

    /**
     * 隐藏全局加载状态
     */
    hideGlobalLoading() {
        const overlay = document.getElementById('global-loading-overlay');
        overlay.classList.remove('show');
        this.loadingStates.delete('global');
    }

    /**
     * 显示顶部进度条
     */
    showTopProgress() {
        const progressBar = document.getElementById('top-progress-bar');
        progressBar.style.display = 'block';
        this.updateProgress('top', 0);
    }

    /**
     * 隐藏顶部进度条
     */
    hideTopProgress() {
        const progressBar = document.getElementById('top-progress-bar');
        setTimeout(() => {
            progressBar.style.display = 'none';
        }, 300);
    }

    /**
     * 更新进度
     * @param {string} type - 进度条类型 ('global' | 'top')
     * @param {number} progress - 进度百分比 (0-100)
     */
    updateProgress(type, progress) {
        progress = Math.max(0, Math.min(100, progress));
        
        if (type === 'global') {
            const overlay = document.getElementById('global-loading-overlay');
            const progressFill = overlay.querySelector('.progress-fill');
            const progressText = overlay.querySelector('.progress-text');
            
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `${Math.round(progress)}%`;
        } else if (type === 'top') {
            const progressBar = document.getElementById('top-progress-bar');
            const progressFill = progressBar.querySelector('.progress-fill');
            
            progressFill.style.width = `${progress}%`;
        }
    }

    /**
     * 显示区域加载状态
     * @param {string} sectionId - 区域ID
     * @param {string} text - 加载文本
     */
    showSectionLoading(sectionId, text = '加载中...') {
        const section = document.getElementById(sectionId);
        if (!section) return;
        
        section.classList.add('section-loading');
        this.loadingStates.set(sectionId, { active: true, startTime: Date.now() });
    }

    /**
     * 隐藏区域加载状态
     * @param {string} sectionId - 区域ID
     */
    hideSectionLoading(sectionId) {
        const section = document.getElementById(sectionId);
        if (!section) return;
        
        section.classList.remove('section-loading');
        this.loadingStates.delete(sectionId);
    }

    /**
     * 创建骨架屏
     * @param {HTMLElement} container - 容器元素
     * @param {Object} config - 配置
     */
    createSkeleton(container, config = {}) {
        // 检查容器是否存在
        if (!container) {
            console.warn('createSkeleton: container is null or undefined');
            return null;
        }
        
        const {
            rows = 3,
            height = '20px',
            spacing = '10px',
            borderRadius = '4px'
        } = config;
        
        const skeleton = document.createElement('div');
        skeleton.className = 'loading-skeleton-container';
        
        for (let i = 0; i < rows; i++) {
            const row = document.createElement('div');
            row.className = 'loading-skeleton';
            row.style.cssText = `
                height: ${height};
                margin-bottom: ${spacing};
                border-radius: ${borderRadius};
                width: ${i === rows - 1 ? '60%' : '100%'};
            `;
            skeleton.appendChild(row);
        }
        
        container.innerHTML = '';
        container.appendChild(skeleton);
        
        return skeleton;
    }

    /**
     * 移除骨架屏
     * @param {HTMLElement} container - 容器元素
     */
    removeSkeleton(container) {
        // 检查容器是否存在
        if (!container) {
            console.warn('removeSkeleton: container is null or undefined');
            return;
        }
        
        const skeleton = container.querySelector('.loading-skeleton-container');
        if (skeleton) {
            skeleton.remove();
        }
    }

    /**
     * 智能加载管理
     * @param {Promise} promise - 要管理的Promise
     * @param {Object} options - 选项
     */
    async manageLoading(promise, options = {}) {
        const {
            type = 'global',
            text = '加载中...',
            minDuration = 500,
            showProgress = true,
            sectionId = null
        } = options;
        
        const startTime = Date.now();
        
        try {
            // 显示加载状态
            if (type === 'global') {
                this.showGlobalLoading(text, { hideProgress: !showProgress });
            } else if (type === 'top') {
                this.showTopProgress();
            } else if (type === 'section' && sectionId) {
                this.showSectionLoading(sectionId, text);
            }
            
            // 模拟进度更新
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 30;
                if (progress > 90) progress = 90;
                
                if (showProgress) {
                    this.updateProgress(type, progress);
                }
            }, 200);
            
            // 等待Promise完成
            const result = await promise;
            
            // 完成进度
            clearInterval(progressInterval);
            if (showProgress) {
                this.updateProgress(type, 100);
            }
            
            // 确保最小显示时间
            const elapsed = Date.now() - startTime;
            if (elapsed < minDuration) {
                await new Promise(resolve => setTimeout(resolve, minDuration - elapsed));
            }
            
            return result;
            
        } finally {
            // 隐藏加载状态
            if (type === 'global') {
                this.hideGlobalLoading();
            } else if (type === 'top') {
                this.hideTopProgress();
            } else if (type === 'section' && sectionId) {
                this.hideSectionLoading(sectionId);
            }
        }
    }

    /**
     * 批量加载管理
     * @param {Array} promises - Promise数组
     * @param {Object} options - 选项
     */
    async manageBatchLoading(promises, options = {}) {
        const {
            type = 'global',
            text = '批量加载中...',
            showProgress = true
        } = options;
        
        if (type === 'global') {
            this.showGlobalLoading(text, { hideProgress: !showProgress });
        } else if (type === 'top') {
            this.showTopProgress();
        }
        
        try {
            const results = [];
            let completed = 0;
            
            for (const promise of promises) {
                const result = await promise;
                results.push(result);
                completed++;
                
                if (showProgress) {
                    const progress = (completed / promises.length) * 100;
                    this.updateProgress(type, progress);
                }
            }
            
            return results;
            
        } finally {
            if (type === 'global') {
                this.hideGlobalLoading();
            } else if (type === 'top') {
                this.hideTopProgress();
            }
        }
    }

    /**
     * 获取加载状态
     * @param {string} id - 加载ID
     */
    getLoadingState(id) {
        return this.loadingStates.get(id);
    }

    /**
     * 检查是否正在加载
     * @param {string} id - 加载ID
     */
    isLoading(id) {
        return this.loadingStates.has(id);
    }

    /**
     * 清除所有加载状态
     */
    clearAllLoading() {
        this.hideGlobalLoading();
        this.hideTopProgress();
        
        // 清除所有区域加载状态
        for (const [sectionId] of this.loadingStates) {
            if (sectionId !== 'global' && sectionId !== 'top') {
                this.hideSectionLoading(sectionId);
            }
        }
        
        this.loadingStates.clear();
    }
}

// 创建全局加载管理器实例
window.loadingManager = new LoadingManager();