/**
 * 保存优化器
 * 提供防抖、批量保存等性能优化功能
 */
class SaveOptimizer {
    constructor() {
        this.saveQueue = new Map(); // 保存队列
        this.debounceTimers = new Map(); // 防抖定时器
        this.isProcessing = false; // 是否正在处理保存
        
        // 配置参数
        this.debounceDelay = 150; // 减少防抖延迟，提高响应速度
        this.batchSize = 5; // 批量保存大小
        this.maxRetries = 1; // 减少重试次数，提高速度
    }
    
    /**
     * 优化的保存方法
     * @param {string} key - 保存键（用于去重）
     * @param {Object} labelData - 标注数据
     * @param {Function} callback - 回调函数
     */
    optimizedSave(key, labelData, callback = null) {
        // 清除之前的定时器
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }
        
        // 更新队列中的数据
        this.saveQueue.set(key, {
            data: labelData,
            callback: callback,
            retries: 0,
            timestamp: Date.now()
        });
        
        // 设置防抖定时器
        const timer = setTimeout(() => {
            this.processSave(key);
            this.debounceTimers.delete(key);
        }, this.debounceDelay);
        
        this.debounceTimers.set(key, timer);
    }
    
    /**
     * 处理单个保存请求
     * @param {string} key - 保存键
     */
    async processSave(key) {
        if (!this.saveQueue.has(key)) {
            return;
        }
        
        const saveItem = this.saveQueue.get(key);
        this.saveQueue.delete(key);
        
        try {
            // 显示保存状态
            this.updateSaveStatus('saving');
            
            // 执行保存
            const result = await window.optimizedDataService.saveLabel(saveItem.data);
            
            if (result.success) {
                this.updateSaveStatus('saved');
                if (saveItem.callback) {
                    saveItem.callback(true, result);
                }
            } else {
                throw new Error(result.message || '保存失败');
            }
            
        } catch (error) {
            console.error('保存失败:', error);
            
            // 重试机制
            if (saveItem.retries < this.maxRetries) {
                saveItem.retries++;
                this.saveQueue.set(key, saveItem);
                
                // 延迟重试（减少延迟时间）
                setTimeout(() => {
                    this.processSave(key);
                }, 300 * saveItem.retries);
                
                this.updateSaveStatus('retrying');
            } else {
                this.updateSaveStatus('error');
                if (saveItem.callback) {
                    saveItem.callback(false, error);
                }
            }
        }
    }
    
    /**
     * 批量处理保存队列
     */
    async processBatch() {
        if (this.isProcessing || this.saveQueue.size === 0) {
            return;
        }
        
        this.isProcessing = true;
        
        try {
            const keys = Array.from(this.saveQueue.keys()).slice(0, this.batchSize);
            const promises = keys.map(key => this.processSave(key));
            
            await Promise.allSettled(promises);
        } finally {
            this.isProcessing = false;
        }
    }
    
    /**
     * 强制保存所有待保存的数据
     */
    async forceFlush() {
        // 清除所有防抖定时器
        for (const timer of this.debounceTimers.values()) {
            clearTimeout(timer);
        }
        this.debounceTimers.clear();
        
        // 处理所有待保存的数据
        const keys = Array.from(this.saveQueue.keys());
        const promises = keys.map(key => this.processSave(key));
        
        await Promise.allSettled(promises);
    }
    
    /**
     * 更新保存状态显示
     * @param {string} status - 状态：saving, saved, error, retrying
     */
    updateSaveStatus(status) {
        const statusElement = document.getElementById('save-status');
        if (!statusElement) return;
        
        // 移除所有状态类
        statusElement.classList.remove('saving', 'saved', 'error', 'retrying');
        
        // 添加当前状态类
        statusElement.classList.add(status);
        
        // 更新状态文本
        const statusTexts = {
            saving: '保存中...',
            saved: '已保存',
            error: '保存失败',
            retrying: '重试中...'
        };
        
        statusElement.textContent = statusTexts[status] || '';
        
        // 自动隐藏成功状态
        if (status === 'saved') {
            setTimeout(() => {
                statusElement.textContent = '';
                statusElement.classList.remove('saved');
            }, 2000);
        }
    }
    
    /**
     * 获取队列状态
     */
    getQueueStatus() {
        return {
            queueSize: this.saveQueue.size,
            pendingTimers: this.debounceTimers.size,
            isProcessing: this.isProcessing
        };
    }
    
    /**
     * 清空队列
     */
    clearQueue() {
        // 清除所有定时器
        for (const timer of this.debounceTimers.values()) {
            clearTimeout(timer);
        }
        
        this.debounceTimers.clear();
        this.saveQueue.clear();
        this.isProcessing = false;
    }
}

// 创建全局保存优化器实例
window.saveOptimizer = new SaveOptimizer();

// 页面卸载时强制保存所有数据
window.addEventListener('beforeunload', async (event) => {
    if (window.saveOptimizer.getQueueStatus().queueSize > 0) {
        event.preventDefault();
        await window.saveOptimizer.forceFlush();
    }
});

// 定期处理批量保存
setInterval(() => {
    if (window.saveOptimizer) {
        window.saveOptimizer.processBatch();
    }
}, 1000);